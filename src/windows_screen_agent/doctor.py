import json
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


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


def check_ollama_service(
    base_url: str,
    model: str,
    *,
    opener: Any = urlopen,
    timeout: float = 2.0,
) -> tuple[bool, str]:
    base_url = base_url.rstrip("/")
    request = Request(f"{base_url}/api/tags", method="GET")
    try:
        with opener(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, OSError, TimeoutError) as exc:
        return False, f"{base_url} unavailable: {exc}"
    except json.JSONDecodeError:
        return False, f"{base_url} returned invalid JSON"

    models = payload.get("models", [])
    names = {
        str(item.get("name") or item.get("model"))
        for item in models
        if isinstance(item, dict) and (item.get("name") or item.get("model"))
    }
    if model in names:
        return True, f"{model} available at {base_url}"
    return False, f"{model} not found; run: ollama pull {model}"


def collect_diagnostics(
    *,
    runtime_dir: Path,
    planner_backend: str,
    codex_bin: str,
    openai_api_key: str | None,
    ollama_base_url: str = "http://localhost:11434",
    ollama_model: str = "qwen2.5vl:7b",
    opener: Any = urlopen,
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
            planner_backend in {"codex", "openai", "ollama", "auto"},
            planner_backend,
        ),
        Diagnostic("Runtime directory", can_write, str(runtime_dir)),
    ]
    if planner_backend in {"codex", "auto"}:
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
    if planner_backend == "auto" and openai_api_key:
        diagnostics.append(Diagnostic("OPENAI_API_KEY", True, "set"))
    if planner_backend in {"ollama", "auto"}:
        ok, detail = check_ollama_service(
            ollama_base_url,
            ollama_model,
            opener=opener,
        )
        diagnostics.append(Diagnostic("Ollama", ok, detail))
    return diagnostics


def format_diagnostics(diagnostics: list[Diagnostic]) -> str:
    lines = []
    for diagnostic in diagnostics:
        marker = "ok" if diagnostic.ok else "warn"
        lines.append(f"{diagnostic.name}: {diagnostic.detail} [{marker}]")
    return "\n".join(lines)
