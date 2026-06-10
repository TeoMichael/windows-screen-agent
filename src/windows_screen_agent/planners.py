from typing import Any

from windows_screen_agent.actions import Action
from windows_screen_agent.codex_agent import CodexPlanner
from windows_screen_agent.config import Config
from windows_screen_agent.ollama_agent import OllamaPlanner
from windows_screen_agent.openai_agent import OpenAIPlanner


class AutoPlanner:
    def __init__(self, planners: list[tuple[str, Any]]):
        if not planners:
            raise ValueError("AutoPlanner requires at least one planner")
        self.planners = planners

    def plan(
        self,
        *,
        screen: Any,
        note: str,
        history: list[dict],
        profile: str = "careful",
    ) -> tuple[Action, ...]:
        errors = []
        for name, planner in self.planners:
            try:
                return planner.plan(
                    screen=screen,
                    note=note,
                    history=history,
                    profile=profile,
                )
            except Exception as exc:
                errors.append(f"{name}: {exc}")
        raise RuntimeError("all planner backends failed: " + "; ".join(errors))


def build_planner(config: Config):
    if config.planner_backend == "codex":
        return CodexPlanner(config=config)
    if config.planner_backend == "openai":
        return OpenAIPlanner(config=config)
    if config.planner_backend == "ollama":
        return OllamaPlanner(config=config)
    if config.planner_backend == "auto":
        planners = [("ollama", OllamaPlanner(config=config)), ("codex", CodexPlanner(config=config))]
        if config.openai_api_key:
            planners.append(("openai", OpenAIPlanner(config=config)))
        return AutoPlanner(planners)
    raise ValueError(f"Unsupported planner backend: {config.planner_backend}")
