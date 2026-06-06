from dataclasses import asdict, dataclass
import time
from typing import Any

from windows_screen_agent.actions import (
    Action,
    ActionValidationError,
    amplify_repeated_scroll,
    parse_action_plan,
    validate_action,
)
from windows_screen_agent.config import Config
from windows_screen_agent.logs import append_jsonl, runtime_paths, write_status
from windows_screen_agent.routing import choose_planning_profile


@dataclass(frozen=True)
class RunResult:
    reason: str
    steps: int


class Runner:
    def __init__(self, *, config: Config, screen: Any, planner: Any, executor: Any):
        self.config = config
        self.screen = screen
        self.planner = planner
        self.executor = executor
        self.paths = runtime_paths(config.runtime_dir)

    def stop_requested(self) -> bool:
        return self.paths.stop_file.exists()

    def run(self, note: str = "") -> RunResult:
        history: list[dict] = []
        started = time.monotonic()
        actions_completed = 0
        write_status(self.paths, "starting")

        while actions_completed < self.config.max_steps:
            if self.stop_requested():
                write_status(self.paths, "stopped")
                return RunResult(reason="stopped", steps=actions_completed)
            if time.monotonic() - started > self.config.max_runtime_seconds:
                write_status(self.paths, "timeout")
                return RunResult(reason="timeout", steps=actions_completed)

            step = actions_completed + 1
            write_status(self.paths, f"step {step}: capture")
            snapshot = self.screen.capture()
            profile = choose_planning_profile(self.config, note=note, history=history)
            write_status(self.paths, f"step {step}: plan ({profile})")
            planned = self.planner.plan(
                screen=snapshot,
                note=note,
                history=history,
                profile=profile,
            )

            try:
                planned_actions = _coerce_action_plan(planned)
                planned_actions = planned_actions[: self.config.max_steps - actions_completed]
                planned_history = list(history)
                actions = []
                for action in planned_actions:
                    action = amplify_repeated_scroll(action, planned_history)
                    planned_history.append(asdict(action))
                    actions.append(action)
                actions = tuple(actions)

                for action in actions:
                    validate_action(
                        action,
                        screen_width=snapshot.width,
                        screen_height=snapshot.height,
                        max_type_chars=self.config.max_type_chars,
                    )
            except ActionValidationError as exc:
                append_jsonl(
                    self.paths.actions_log,
                    {"step": actions_completed + 1, "error": str(exc)},
                )
                write_status(self.paths, "validation failed")
                return RunResult(reason="validation failed", steps=actions_completed)

            for action in actions:
                step = actions_completed + 1
                append_jsonl(
                    self.paths.actions_log,
                    {"step": step, "profile": profile, "action": asdict(action)},
                )
                history.append(asdict(action))

                if action.action == "done":
                    write_status(self.paths, "done")
                    return RunResult(reason="done", steps=actions_completed)
                if action.action == "fail":
                    write_status(self.paths, "failed")
                    return RunResult(reason="failed", steps=actions_completed)

                write_status(self.paths, f"step {step}: {action.action}")
                self.executor.execute(action)
                actions_completed += 1
                time.sleep(self.config.action_delay_seconds)

                if self.stop_requested():
                    write_status(self.paths, "stopped")
                    return RunResult(reason="stopped", steps=actions_completed)
                if time.monotonic() - started > self.config.max_runtime_seconds:
                    write_status(self.paths, "timeout")
                    return RunResult(reason="timeout", steps=actions_completed)

        write_status(self.paths, "max steps reached")
        return RunResult(reason="max steps reached", steps=actions_completed)


def _coerce_action_plan(planned: Any) -> tuple[Action, ...]:
    if isinstance(planned, Action):
        return (planned,)
    if isinstance(planned, (list, tuple)) and all(isinstance(action, Action) for action in planned):
        if not planned:
            raise ActionValidationError("Action plan must contain a non-empty actions list")
        return tuple(planned)
    return parse_action_plan(planned)
