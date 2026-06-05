from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Config:
    openai_api_key: str
    model: str
    runtime_dir: Path
    max_steps: int
    max_runtime_seconds: float
    action_delay_seconds: float
    max_type_chars: int
    confirm_before_submit: bool


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return default if raw in (None, "") else int(raw)


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    return default if raw in (None, "") else float(raw)


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw in (None, ""):
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_config() -> Config:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required")

    runtime_dir = Path(
        os.environ.get("WSA_RUNTIME_DIR", str(Path.home() / ".windows-screen-agent"))
    ).expanduser()

    return Config(
        openai_api_key=api_key,
        model=os.environ.get("OPENAI_MODEL", "gpt-5.2"),
        runtime_dir=runtime_dir,
        max_steps=_int_env("WSA_MAX_STEPS", 20),
        max_runtime_seconds=_float_env("WSA_MAX_RUNTIME_SECONDS", 180.0),
        action_delay_seconds=_float_env("WSA_ACTION_DELAY_SECONDS", 0.5),
        max_type_chars=_int_env("WSA_MAX_TYPE_CHARS", 1000),
        confirm_before_submit=_bool_env("WSA_CONFIRM_BEFORE_SUBMIT", False),
    )
