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
    planner_backend: str = "codex"
    codex_bin: str = "codex"
    planner_mode: str = "auto"
    codex_model_fast: str = ""
    codex_model_careful: str = ""
    openai_model_fast: str = "gpt-5.2"
    openai_model_careful: str = "gpt-5.2"


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


def _default_codex_bin() -> str:
    configured = os.environ.get("CODEX_BIN", "").strip()
    if configured:
        return configured
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        root = Path(local_app_data) / "OpenAI" / "Codex" / "bin"
        candidates = sorted(root.glob("*/codex.exe"), key=lambda path: path.stat().st_mtime, reverse=True)
        if candidates:
            return str(candidates[0])
    return "codex"


def load_config() -> Config:
    planner_backend = os.environ.get("WSA_PLANNER", "codex").strip().lower()
    if planner_backend not in {"codex", "openai"}:
        raise ValueError("WSA_PLANNER must be either 'codex' or 'openai'")

    planner_mode = os.environ.get("WSA_MODE", "auto").strip().lower()
    if planner_mode not in {"auto", "fast", "careful"}:
        raise ValueError("WSA_MODE must be one of 'auto', 'fast', or 'careful'")

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if planner_backend == "openai" and not api_key:
        raise ValueError("OPENAI_API_KEY is required when WSA_PLANNER=openai")

    runtime_dir = Path(
        os.environ.get("WSA_RUNTIME_DIR", str(Path.home() / ".windows-screen-agent"))
    ).expanduser()
    openai_model = os.environ.get("OPENAI_MODEL", "gpt-5.2")
    codex_model = os.environ.get("CODEX_MODEL", "").strip()

    return Config(
        openai_api_key=api_key,
        model=openai_model,
        runtime_dir=runtime_dir,
        max_steps=_int_env("WSA_MAX_STEPS", 20),
        max_runtime_seconds=_float_env("WSA_MAX_RUNTIME_SECONDS", 900.0),
        action_delay_seconds=_float_env("WSA_ACTION_DELAY_SECONDS", 0.2),
        max_type_chars=_int_env("WSA_MAX_TYPE_CHARS", 1000),
        confirm_before_submit=_bool_env("WSA_CONFIRM_BEFORE_SUBMIT", False),
        planner_backend=planner_backend,
        codex_bin=_default_codex_bin(),
        planner_mode=planner_mode,
        codex_model_fast=os.environ.get("CODEX_MODEL_FAST", codex_model).strip(),
        codex_model_careful=os.environ.get("CODEX_MODEL_CAREFUL", codex_model).strip(),
        openai_model_fast=os.environ.get("OPENAI_MODEL_FAST", openai_model),
        openai_model_careful=os.environ.get("OPENAI_MODEL_CAREFUL", openai_model),
    )
