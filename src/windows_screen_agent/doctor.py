import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Diagnostic:
    name: str
    ok: bool
    detail: str


def _check_codex_binary(codex_bin: str) -> tuple[bool, str]:
    resolved = shutil.which(codex_bin)
    if not resolved:
        return False, f"{codex_bin} not found on PATH"
    try:
        result = subprocess.run(
            [resolved, "--help"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except OSError as exc:
        return False, f"{resolved} is not executable: {exc}"
    except subprocess.TimeoutExpired:
        return False, f"{resolved} timed out while checking --help"
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        return False, f"{resolved} returned {result.returncode}: {detail}"
    return True, resolved


def collect_diagnostics(
    *,
    runtime_dir: Path,
    planner_backend: str,
    codex_bin: str,
    openai_api_key: str | None,
) -> list[Diagnostic]:
    runtime_dir.mkdir(parents=True, exist_ok=True)
    can_write = runtime_dir.exists() and runtime_dir.is_dir()
    diagnostics = [
        Diagnostic(
            "Python",
            sys.version_info >= (3, 11),
            f"{platform.python_version()} on {platform.system()}",
        ),
        Diagnostic(
            "Planner backend",
            planner_backend in {"codex", "openai"},
            planner_backend,
        ),
        Diagnostic("Runtime directory", can_write, str(runtime_dir)),
    ]
    if planner_backend == "codex":
        ok, detail = _check_codex_binary(codex_bin)
        diagnostics.append(Diagnostic("CODEX_BIN", ok, detail))
    if planner_backend == "openai":
        diagnostics.append(
            Diagnostic(
                "OPENAI_API_KEY",
                bool(openai_api_key),
                "set" if openai_api_key else "missing (live runs disabled)",
            )
        )
    return diagnostics


def format_diagnostics(diagnostics: list[Diagnostic]) -> str:
    lines = []
    for diagnostic in diagnostics:
        marker = "ok" if diagnostic.ok else "warn"
        lines.append(f"{diagnostic.name}: {diagnostic.detail} [{marker}]")
    return "\n".join(lines)
