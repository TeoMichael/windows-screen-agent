from dataclasses import dataclass
import json
from pathlib import Path
import re
import time
from typing import Any


SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]+"),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]+", re.IGNORECASE),
    re.compile(r"(OPENAI_API_KEY=)[^\s]+", re.IGNORECASE),
]


@dataclass(frozen=True)
class RuntimePaths:
    base_dir: Path
    screens_dir: Path
    logs_dir: Path
    status_file: Path
    stop_file: Path
    actions_log: Path


def runtime_paths(base_dir: Path) -> RuntimePaths:
    base_dir.mkdir(parents=True, exist_ok=True)
    screens_dir = base_dir / "screens"
    logs_dir = base_dir / "logs"
    screens_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    return RuntimePaths(
        base_dir=base_dir,
        screens_dir=screens_dir,
        logs_dir=logs_dir,
        status_file=base_dir / "status.txt",
        stop_file=base_dir / "stop",
        actions_log=logs_dir / "actions.jsonl",
    )


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def write_status(paths: RuntimePaths, status: str) -> None:
    paths.status_file.write_text(status, encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    safe = json.loads(redact_secrets(json.dumps(payload, ensure_ascii=False)))
    safe["ts"] = time.time()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(safe, ensure_ascii=False) + "\n")
