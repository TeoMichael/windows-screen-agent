import platform
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Diagnostic:
    name: str
    ok: bool
    detail: str


def collect_diagnostics(*, runtime_dir: Path, openai_api_key: str | None) -> list[Diagnostic]:
    runtime_dir.mkdir(parents=True, exist_ok=True)
    can_write = runtime_dir.exists() and runtime_dir.is_dir()
    return [
        Diagnostic(
            "Python",
            sys.version_info >= (3, 11),
            f"{platform.python_version()} on {platform.system()}",
        ),
        Diagnostic(
            "OPENAI_API_KEY",
            bool(openai_api_key),
            "set" if openai_api_key else "missing (live runs disabled)",
        ),
        Diagnostic("Runtime directory", can_write, str(runtime_dir)),
    ]


def format_diagnostics(diagnostics: list[Diagnostic]) -> str:
    lines = []
    for diagnostic in diagnostics:
        marker = "ok" if diagnostic.ok else "warn"
        lines.append(f"{diagnostic.name}: {diagnostic.detail} [{marker}]")
    return "\n".join(lines)
