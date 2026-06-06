from windows_screen_agent.codex_agent import CodexPlanner
from windows_screen_agent.config import Config
from windows_screen_agent.openai_agent import OpenAIPlanner


def build_planner(config: Config):
    if config.planner_backend == "codex":
        return CodexPlanner(config=config)
    if config.planner_backend == "openai":
        return OpenAIPlanner(config=config)
    raise ValueError(f"Unsupported planner backend: {config.planner_backend}")
