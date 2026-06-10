from dataclasses import dataclass
import json
from pathlib import Path


SUPPORTED_PLANNERS = {"auto", "codex", "openai", "ollama"}


@dataclass(frozen=True)
class RuntimeSettings:
    planner_backend: str | None = None


def load_settings(path: Path) -> RuntimeSettings:
    if not path.exists():
        return RuntimeSettings()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return RuntimeSettings()
    planner_backend = payload.get("planner_backend")
    if planner_backend not in SUPPORTED_PLANNERS:
        planner_backend = None
    return RuntimeSettings(planner_backend=planner_backend)


def save_settings(path: Path, settings: RuntimeSettings) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"planner_backend": settings.planner_backend}, ensure_ascii=False),
        encoding="utf-8",
    )
