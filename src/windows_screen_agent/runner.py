from dataclasses import asdict, dataclass
import time
from typing import Any

from windows_screen_agent.actions import ActionValidationError, validate_action
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
        write_status(self.paths, "starting")

        for step in range(1, self.config.max_steps + 1):
            if self.stop_requested():
                write_status(self.paths, "stopped")
                return RunResult(reason="stopped", steps=step - 1)
            if time.monotonic() - started > self.config.max_runtime_seconds:
                write_status(self.paths, "timeout")
                return RunResult(reason="timeout", steps=step - 1)

            write_status(self.paths, f"step {step}: capture")
            snapshot = self.screen.capture()
            profile = choose_planning_profile(self.config, note=note, history=history)
            write_status(self.paths, f"step {step}: plan ({profile})")
            action = self.planner.plan(
                screen=snapshot,
                note=note,
                history=history,
                profile=profile,
            )

            try:
                validate_action(
                    action,
                    screen_width=snapshot.width,
                    screen_height=snapshot.height,
                    max_type_chars=self.config.max_type_chars,
                )
            except ActionValidationError as exc:
                append_jsonl(self.paths.actions_log, {"step": step, "error": str(exc)})
                write_status(self.paths, "validation failed")
                return RunResult(reason="validation failed", steps=step - 1)

            append_jsonl(
                self.paths.actions_log,
                {"step": step, "profile": profile, "action": asdict(action)},
            )
            history.append(asdict(action))

            if action.action == "done":
                write_status(self.paths, "done")
                return RunResult(reason="done", steps=step - 1)
            if action.action == "fail":
                write_status(self.paths, "failed")
                return RunResult(reason="failed", steps=step - 1)

            write_status(self.paths, f"step {step}: {action.action}")
            self.executor.execute(action)
            time.sleep(self.config.action_delay_seconds)

        write_status(self.paths, "max steps reached")
        return RunResult(reason="max steps reached", steps=self.config.max_steps)
