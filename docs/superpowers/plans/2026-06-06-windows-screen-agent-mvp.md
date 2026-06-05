# Windows Screen Agent MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first Windows Screen Agent MVP: a Windows CLI/tray-capable app that captures the screen, sends it to the OpenAI Responses API, receives one structured action, validates it, executes it, and repeats until stopped.

**Architecture:** Use a coordinate-first loop with clear module boundaries. The runner captures the screen, the OpenAI planner returns one JSON action, the validator rejects unsafe actions, and the executor performs allowed PyAutoGUI actions. Tray and hotkey support wrap the runner without owning its core logic.

**Tech Stack:** Python 3.11+, OpenAI Python SDK, PyAutoGUI, Pillow, pynput, pystray, pytest, dataclasses, argparse.

---

## File Structure

Create these files:

- `pyproject.toml`: package metadata, runtime dependencies, dev dependencies, console script.
- `README.md`: setup, safe-use scope, commands, environment variables.
- `src/windows_screen_agent/__init__.py`: package version.
- `src/windows_screen_agent/config.py`: environment/config loading.
- `src/windows_screen_agent/logs.py`: runtime directories, JSONL action logs, secret redaction.
- `src/windows_screen_agent/actions.py`: action schema, parsing, validation, and PyAutoGUI execution.
- `src/windows_screen_agent/screen.py`: screenshot capture, dimensions, base64 data URL.
- `src/windows_screen_agent/prompt.py`: developer prompt and JSON schema for action output.
- `src/windows_screen_agent/openai_agent.py`: Responses API client wrapper.
- `src/windows_screen_agent/runner.py`: step loop and stop handling.
- `src/windows_screen_agent/app.py`: CLI entrypoint.
- `src/windows_screen_agent/hotkey.py`: conservative global hotkey wrapper.
- `src/windows_screen_agent/tray.py`: system tray wrapper.
- `tests/test_config_logs.py`: config and redaction coverage.
- `tests/test_actions.py`: parsing and validation coverage.
- `tests/test_screen_prompt.py`: screenshot metadata and prompt coverage.
- `tests/test_openai_agent.py`: mocked OpenAI response parsing.
- `tests/test_runner.py`: runner stop and loop behavior.

---

### Task 1: Bootstrap Package And Documentation

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/windows_screen_agent/__init__.py`
- Create: `tests/test_imports.py`

- [ ] **Step 1: Create packaging metadata**

Create `pyproject.toml` with this content:

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "windows-screen-agent"
version = "0.1.0"
description = "Windows screen automation assistant using the OpenAI API"
requires-python = ">=3.11"
dependencies = [
  "openai>=2.0.0",
  "pyautogui>=0.9.54",
  "pillow>=10.0.0",
  "pynput>=1.7.7",
  "pystray>=0.19.5"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
  "ruff>=0.8.0"
]

[project.scripts]
windows-screen-agent = "windows_screen_agent.app:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

- [ ] **Step 2: Create package marker**

Create `src/windows_screen_agent/__init__.py`:

```python
"""Windows Screen Agent."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create README**

Create `README.md`:

```markdown
# Windows Screen Agent

Windows Screen Agent is a Windows-first screen automation assistant. It captures the current screen, sends the screenshot to the OpenAI Responses API, receives one structured action, validates that action, executes it locally, and repeats until the task is complete or the user stops it.

This project is for personal practice, sandbox labs, forms, and repetitive local tasks. Do not use it for graded, proctored, honor-code-bound exams, credential harvesting, payment flows, production administration, or automation that violates a site's terms.

## Requirements

- Windows 10 or 11
- Python 3.11+
- An OpenAI API key in `OPENAI_API_KEY`

## Setup

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
$env:OPENAI_API_KEY = "your-api-key"
```

## Commands

```powershell
windows-screen-agent run-once
windows-screen-agent run
windows-screen-agent status
windows-screen-agent stop
```

## Configuration

- `OPENAI_API_KEY`: required for live API calls.
- `OPENAI_MODEL`: model used for planning actions. Defaults to `gpt-5.2`.
- `WSA_MAX_STEPS`: maximum actions per run. Defaults to `20`.
- `WSA_MAX_RUNTIME_SECONDS`: maximum runtime per run. Defaults to `180`.
- `WSA_RUNTIME_DIR`: runtime data directory. Defaults to `%USERPROFILE%\.windows-screen-agent`.

## Safety Controls

- Stop file and emergency stop hotkey.
- Coordinate bounds checks.
- Action allowlist.
- Maximum step and runtime limits.
- Logs redact API keys and bearer tokens.
```

- [ ] **Step 4: Add smoke import test**

Create `tests/test_imports.py`:

```python
import windows_screen_agent


def test_version_is_present():
    assert windows_screen_agent.__version__ == "0.1.0"
```

- [ ] **Step 5: Run smoke test**

Run:

```powershell
python -m pytest tests/test_imports.py -q
```

Expected: `1 passed`.

- [ ] **Step 6: Commit**

```powershell
git add pyproject.toml README.md src/windows_screen_agent/__init__.py tests/test_imports.py
git commit -m "chore: bootstrap windows screen agent"
```

---

### Task 2: Config And Logging

**Files:**
- Create: `src/windows_screen_agent/config.py`
- Create: `src/windows_screen_agent/logs.py`
- Create: `tests/test_config_logs.py`

- [ ] **Step 1: Write config and log tests**

Create `tests/test_config_logs.py`:

```python
from pathlib import Path

import pytest

from windows_screen_agent.config import load_config
from windows_screen_agent.logs import redact_secrets, runtime_paths


def test_load_config_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        load_config()


def test_load_config_reads_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.2")
    monkeypatch.setenv("WSA_MAX_STEPS", "7")
    monkeypatch.setenv("WSA_RUNTIME_DIR", str(tmp_path))

    cfg = load_config()

    assert cfg.openai_api_key == "sk-test"
    assert cfg.model == "gpt-5.2"
    assert cfg.max_steps == 7
    assert cfg.runtime_dir == tmp_path


def test_runtime_paths_creates_directories(tmp_path):
    paths = runtime_paths(tmp_path)

    assert paths.base_dir == tmp_path
    assert paths.screens_dir.exists()
    assert paths.logs_dir.exists()
    assert paths.status_file == tmp_path / "status.txt"


def test_redact_secrets_masks_keys_and_bearer_tokens():
    text = "OPENAI_API_KEY=sk-secret Authorization: Bearer abc123"

    redacted = redact_secrets(text)

    assert "sk-secret" not in redacted
    assert "abc123" not in redacted
    assert "[REDACTED]" in redacted
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_config_logs.py -q
```

Expected: FAIL because `config.py` and `logs.py` do not exist.

- [ ] **Step 3: Implement config**

Create `src/windows_screen_agent/config.py`:

```python
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
```

- [ ] **Step 4: Implement logs**

Create `src/windows_screen_agent/logs.py`:

```python
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
```

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m pytest tests/test_config_logs.py -q
```

Expected: `4 passed`.

- [ ] **Step 6: Commit**

```powershell
git add src/windows_screen_agent/config.py src/windows_screen_agent/logs.py tests/test_config_logs.py
git commit -m "feat: add config and runtime logs"
```

---

### Task 3: Action Parsing, Validation, And Execution

**Files:**
- Create: `src/windows_screen_agent/actions.py`
- Create: `tests/test_actions.py`

- [ ] **Step 1: Write action tests**

Create `tests/test_actions.py`:

```python
import pytest

from windows_screen_agent.actions import (
    Action,
    ActionExecutor,
    ActionValidationError,
    parse_action,
    validate_action,
)


def test_parse_click_action():
    action = parse_action('{"action":"click","x":10,"y":20,"button":"left","reason":"select"}')

    assert action.action == "click"
    assert action.x == 10
    assert action.y == 20


def test_parse_rejects_unknown_action():
    with pytest.raises(ActionValidationError, match="Unsupported action"):
        parse_action('{"action":"drag","x":1,"y":1}')


def test_validate_rejects_offscreen_click():
    action = Action(action="click", x=9999, y=20, button="left", reason="bad")

    with pytest.raises(ActionValidationError, match="off screen"):
        validate_action(action, screen_width=100, screen_height=100, max_type_chars=100)


def test_validate_rejects_excessive_type_text():
    action = Action(action="type", text="x" * 101, reason="too much")

    with pytest.raises(ActionValidationError, match="too long"):
        validate_action(action, screen_width=100, screen_height=100, max_type_chars=100)


def test_executor_dispatches_click_to_backend():
    calls = []
    backend = type(
        "Backend",
        (),
        {
            "click": lambda self, x, y, button: calls.append(("click", x, y, button)),
            "write": lambda self, text, interval: calls.append(("write", text, interval)),
            "scroll": lambda self, amount: calls.append(("scroll", amount)),
            "hotkey": lambda self, *keys: calls.append(("hotkey", keys)),
        },
    )()

    ActionExecutor(backend=backend).execute(Action(action="click", x=5, y=6, button="left"))

    assert calls == [("click", 5, 6, "left")]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_actions.py -q
```

Expected: FAIL because `actions.py` does not exist.

- [ ] **Step 3: Implement actions**

Create `src/windows_screen_agent/actions.py`:

```python
from dataclasses import dataclass
import json
from typing import Any


SUPPORTED_ACTIONS = {"click", "type", "hotkey", "scroll", "wait", "done", "fail"}
SUPPORTED_BUTTONS = {"left", "right", "middle"}
SUPPORTED_HOTKEYS = {
    "enter",
    "tab",
    "esc",
    "escape",
    "ctrl",
    "shift",
    "alt",
    "win",
    "a",
    "c",
    "v",
    "x",
    "z",
}


class ActionValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Action:
    action: str
    x: int | None = None
    y: int | None = None
    button: str = "left"
    text: str = ""
    keys: tuple[str, ...] = ()
    amount: int = 0
    seconds: float = 0.0
    reason: str = ""


def parse_action(raw: str | dict[str, Any]) -> Action:
    payload = json.loads(raw) if isinstance(raw, str) else raw
    if not isinstance(payload, dict):
        raise ActionValidationError("Action payload must be an object")

    name = str(payload.get("action", "")).strip().lower()
    if name not in SUPPORTED_ACTIONS:
        raise ActionValidationError(f"Unsupported action: {name}")

    keys = payload.get("keys") or ()
    if isinstance(keys, str):
        keys = (keys,)
    return Action(
        action=name,
        x=payload.get("x"),
        y=payload.get("y"),
        button=str(payload.get("button", "left")).lower(),
        text=str(payload.get("text", "")),
        keys=tuple(str(key).lower() for key in keys),
        amount=int(payload.get("amount", 0) or 0),
        seconds=float(payload.get("seconds", 0.0) or 0.0),
        reason=str(payload.get("reason", "")),
    )


def validate_action(
    action: Action,
    *,
    screen_width: int,
    screen_height: int,
    max_type_chars: int,
) -> None:
    if action.action == "click":
        if action.x is None or action.y is None:
            raise ActionValidationError("Click action requires x and y")
        if not (0 <= int(action.x) < screen_width and 0 <= int(action.y) < screen_height):
            raise ActionValidationError("Click coordinates are off screen")
        if action.button not in SUPPORTED_BUTTONS:
            raise ActionValidationError(f"Unsupported button: {action.button}")

    if action.action == "type" and len(action.text) > max_type_chars:
        raise ActionValidationError("Type text is too long")

    if action.action == "hotkey":
        if not action.keys:
            raise ActionValidationError("Hotkey action requires keys")
        unsupported = [key for key in action.keys if key not in SUPPORTED_HOTKEYS]
        if unsupported:
            raise ActionValidationError(f"Unsupported hotkey: {unsupported[0]}")

    if action.action == "wait" and action.seconds < 0:
        raise ActionValidationError("Wait seconds cannot be negative")


class ActionExecutor:
    def __init__(self, backend: Any):
        self.backend = backend

    def execute(self, action: Action) -> None:
        if action.action == "click":
            self.backend.click(int(action.x), int(action.y), button=action.button)
        elif action.action == "type":
            self.backend.write(action.text, interval=0.01)
        elif action.action == "scroll":
            self.backend.scroll(action.amount)
        elif action.action == "hotkey":
            self.backend.hotkey(*action.keys)
        elif action.action in {"wait", "done", "fail"}:
            return
```

- [ ] **Step 4: Run action tests**

Run:

```powershell
python -m pytest tests/test_actions.py -q
```

Expected: `5 passed`.

- [ ] **Step 5: Commit**

```powershell
git add src/windows_screen_agent/actions.py tests/test_actions.py
git commit -m "feat: add action validation and execution"
```

---

### Task 4: Screenshot Capture And Prompt Schema

**Files:**
- Create: `src/windows_screen_agent/screen.py`
- Create: `src/windows_screen_agent/prompt.py`
- Create: `tests/test_screen_prompt.py`

- [ ] **Step 1: Write screen and prompt tests**

Create `tests/test_screen_prompt.py`:

```python
from pathlib import Path

from PIL import Image

from windows_screen_agent.prompt import ACTION_JSON_SCHEMA, build_developer_prompt
from windows_screen_agent.screen import capture_screen


class FakeScreenshotBackend:
    def screenshot(self):
        return Image.new("RGB", (32, 24), color="white")


def test_capture_screen_saves_png_and_data_url(tmp_path):
    snapshot = capture_screen(tmp_path, backend=FakeScreenshotBackend())

    assert snapshot.path.exists()
    assert snapshot.width == 32
    assert snapshot.height == 24
    assert snapshot.data_url.startswith("data:image/png;base64,")


def test_prompt_mentions_allowed_actions_and_schema():
    prompt = build_developer_prompt()

    assert "coordinate-first" in prompt
    assert "Do not use this for graded" in prompt
    assert ACTION_JSON_SCHEMA["type"] == "object"
    assert "action" in ACTION_JSON_SCHEMA["required"]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_screen_prompt.py -q
```

Expected: FAIL because `screen.py` and `prompt.py` do not exist.

- [ ] **Step 3: Implement screenshot capture**

Create `src/windows_screen_agent/screen.py`:

```python
from dataclasses import dataclass
import base64
from io import BytesIO
from pathlib import Path
import time
from typing import Any


@dataclass(frozen=True)
class ScreenSnapshot:
    path: Path
    width: int
    height: int
    data_url: str


def capture_screen(screens_dir: Path, backend: Any) -> ScreenSnapshot:
    screens_dir.mkdir(parents=True, exist_ok=True)
    image = backend.screenshot()
    path = screens_dir / f"screen-{int(time.time() * 1000)}.png"
    image.save(path, format="PNG")

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

    return ScreenSnapshot(
        path=path,
        width=image.width,
        height=image.height,
        data_url=f"data:image/png;base64,{encoded}",
    )
```

- [ ] **Step 4: Implement prompt schema**

Create `src/windows_screen_agent/prompt.py`:

```python
ACTION_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "action": {
            "type": "string",
            "enum": ["click", "type", "hotkey", "scroll", "wait", "done", "fail"],
        },
        "x": {"type": ["integer", "null"]},
        "y": {"type": ["integer", "null"]},
        "button": {"type": "string", "enum": ["left", "right", "middle"]},
        "text": {"type": "string"},
        "keys": {"type": "array", "items": {"type": "string"}},
        "amount": {"type": "integer"},
        "seconds": {"type": "number"},
        "reason": {"type": "string"},
    },
    "required": ["action", "reason"],
}


def build_developer_prompt() -> str:
    return (
        "You are Windows Screen Agent, a coordinate-first Windows automation planner. "
        "Read the screenshot and return exactly one JSON action matching the schema. "
        "Allowed actions are click, type, hotkey, scroll, wait, done, and fail. "
        "Do not use this for graded, proctored, honor-code-bound exams, credential "
        "harvesting, payment flows, destructive operations, or production administration. "
        "Prefer small reversible actions. If the task is complete, return done. "
        "If the visible task is unsafe or unclear, return fail."
    )


def build_user_text(note: str, width: int, height: int, history: list[dict]) -> str:
    return (
        f"Screen size: {width}x{height}. "
        f"User note: {note.strip() if note.strip() else '(none)'}. "
        f"Recent actions: {history[-5:]}. "
        "Choose the next single action."
    )
```

- [ ] **Step 5: Run tests**

Run:

```powershell
python -m pytest tests/test_screen_prompt.py -q
```

Expected: `2 passed`.

- [ ] **Step 6: Commit**

```powershell
git add src/windows_screen_agent/screen.py src/windows_screen_agent/prompt.py tests/test_screen_prompt.py
git commit -m "feat: add screenshot capture and prompt schema"
```

---

### Task 5: OpenAI Responses API Planner

**Files:**
- Create: `src/windows_screen_agent/openai_agent.py`
- Create: `tests/test_openai_agent.py`

- [ ] **Step 1: Write mocked OpenAI planner tests**

Create `tests/test_openai_agent.py`:

```python
from dataclasses import dataclass

from windows_screen_agent.config import Config
from windows_screen_agent.openai_agent import OpenAIPlanner
from windows_screen_agent.screen import ScreenSnapshot


@dataclass
class FakeResponse:
    output_text: str


class FakeResponses:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse(
            '{"action":"click","x":4,"y":5,"button":"left","reason":"press visible button"}'
        )


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()


def test_planner_calls_responses_api_and_parses_action(tmp_path):
    cfg = Config(
        openai_api_key="sk-test",
        model="gpt-5.2",
        runtime_dir=tmp_path,
        max_steps=3,
        max_runtime_seconds=10,
        action_delay_seconds=0.1,
        max_type_chars=100,
        confirm_before_submit=False,
    )
    client = FakeClient()
    planner = OpenAIPlanner(config=cfg, client=client)
    screen = ScreenSnapshot(
        path=tmp_path / "screen.png",
        width=100,
        height=80,
        data_url="data:image/png;base64,abc",
    )

    action = planner.plan(screen=screen, note="fill the form", history=[])

    assert action.action == "click"
    assert client.responses.calls[0]["model"] == "gpt-5.2"
    assert client.responses.calls[0]["input"][1]["content"][1]["type"] == "input_image"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_openai_agent.py -q
```

Expected: FAIL because `openai_agent.py` does not exist.

- [ ] **Step 3: Implement OpenAI planner**

Create `src/windows_screen_agent/openai_agent.py`:

```python
from typing import Any

from openai import OpenAI

from windows_screen_agent.actions import Action, parse_action
from windows_screen_agent.config import Config
from windows_screen_agent.prompt import ACTION_JSON_SCHEMA, build_developer_prompt, build_user_text
from windows_screen_agent.screen import ScreenSnapshot


class OpenAIPlanner:
    def __init__(self, config: Config, client: Any | None = None):
        self.config = config
        self.client = client or OpenAI(api_key=config.openai_api_key)

    def plan(self, *, screen: ScreenSnapshot, note: str, history: list[dict]) -> Action:
        response = self.client.responses.create(
            model=self.config.model,
            input=[
                {
                    "role": "developer",
                    "content": [{"type": "input_text", "text": build_developer_prompt()}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": build_user_text(note, screen.width, screen.height, history),
                        },
                        {"type": "input_image", "image_url": screen.data_url},
                    ],
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "screen_action",
                    "schema": ACTION_JSON_SCHEMA,
                    "strict": True,
                }
            },
            reasoning={"effort": "low"},
        )
        return parse_action(response.output_text)
```

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest tests/test_openai_agent.py -q
```

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```powershell
git add src/windows_screen_agent/openai_agent.py tests/test_openai_agent.py
git commit -m "feat: add openai action planner"
```

---

### Task 6: Runner Loop And Stop Handling

**Files:**
- Create: `src/windows_screen_agent/runner.py`
- Create: `tests/test_runner.py`

- [ ] **Step 1: Write runner tests**

Create `tests/test_runner.py`:

```python
from dataclasses import dataclass
from pathlib import Path

from windows_screen_agent.actions import Action
from windows_screen_agent.config import Config
from windows_screen_agent.runner import Runner
from windows_screen_agent.screen import ScreenSnapshot


@dataclass
class FakeScreen:
    path: Path

    def capture(self):
        return ScreenSnapshot(
            path=self.path,
            width=100,
            height=80,
            data_url="data:image/png;base64,abc",
        )


class FakePlanner:
    def __init__(self, actions):
        self.actions = list(actions)

    def plan(self, *, screen, note, history):
        return self.actions.pop(0)


class FakeExecutor:
    def __init__(self):
        self.actions = []

    def execute(self, action):
        self.actions.append(action.action)


def _config(tmp_path):
    return Config(
        openai_api_key="sk-test",
        model="gpt-5.2",
        runtime_dir=tmp_path,
        max_steps=3,
        max_runtime_seconds=10,
        action_delay_seconds=0.0,
        max_type_chars=100,
        confirm_before_submit=False,
    )


def test_runner_stops_on_done(tmp_path):
    executor = FakeExecutor()
    runner = Runner(
        config=_config(tmp_path),
        screen=FakeScreen(tmp_path / "screen.png"),
        planner=FakePlanner([Action(action="done", reason="finished")]),
        executor=executor,
    )

    result = runner.run(note="")

    assert result.reason == "done"
    assert executor.actions == []


def test_runner_executes_action_then_done(tmp_path):
    executor = FakeExecutor()
    runner = Runner(
        config=_config(tmp_path),
        screen=FakeScreen(tmp_path / "screen.png"),
        planner=FakePlanner(
            [
                Action(action="click", x=1, y=2, button="left", reason="click"),
                Action(action="done", reason="finished"),
            ]
        ),
        executor=executor,
    )

    result = runner.run(note="")

    assert result.reason == "done"
    assert executor.actions == ["click"]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_runner.py -q
```

Expected: FAIL because `runner.py` does not exist.

- [ ] **Step 3: Implement runner**

Create `src/windows_screen_agent/runner.py`:

```python
from dataclasses import asdict, dataclass
import time
from typing import Any

from windows_screen_agent.actions import ActionValidationError, validate_action
from windows_screen_agent.config import Config
from windows_screen_agent.logs import append_jsonl, runtime_paths, write_status


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
            action = self.planner.plan(screen=snapshot, note=note, history=history)

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

            append_jsonl(self.paths.actions_log, {"step": step, "action": asdict(action)})
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
```

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest tests/test_runner.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit**

```powershell
git add src/windows_screen_agent/runner.py tests/test_runner.py
git commit -m "feat: add runner loop"
```

---

### Task 7: CLI Entry Point

**Files:**
- Create: `src/windows_screen_agent/app.py`
- Modify: `tests/test_imports.py`

- [ ] **Step 1: Extend import test for CLI**

Modify `tests/test_imports.py`:

```python
import windows_screen_agent
from windows_screen_agent.app import build_parser


def test_version_is_present():
    assert windows_screen_agent.__version__ == "0.1.0"


def test_parser_has_core_commands():
    parser = build_parser()
    commands = parser._subparsers._group_actions[0].choices

    assert {"run", "run-once", "status", "stop"} <= set(commands)
```

- [ ] **Step 2: Run test to verify failure**

Run:

```powershell
python -m pytest tests/test_imports.py -q
```

Expected: FAIL because `app.py` does not exist.

- [ ] **Step 3: Implement CLI**

Create `src/windows_screen_agent/app.py`:

```python
import argparse

import pyautogui

from windows_screen_agent.actions import ActionExecutor
from windows_screen_agent.config import load_config
from windows_screen_agent.logs import runtime_paths
from windows_screen_agent.openai_agent import OpenAIPlanner
from windows_screen_agent.runner import Runner
from windows_screen_agent.screen import capture_screen


class PyAutoGuiScreen:
    def __init__(self, screens_dir):
        self.screens_dir = screens_dir

    def capture(self):
        return capture_screen(self.screens_dir, backend=pyautogui)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="windows-screen-agent")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run")
    sub.add_parser("run-once")
    sub.add_parser("status")
    sub.add_parser("stop")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = load_config()
    paths = runtime_paths(cfg.runtime_dir)

    if args.command == "stop":
        paths.stop_file.write_text("stop", encoding="utf-8")
        print("stop requested")
        return 0

    if args.command == "status":
        if paths.status_file.exists():
            print(paths.status_file.read_text(encoding="utf-8"))
        else:
            print("idle")
        return 0

    if paths.stop_file.exists():
        paths.stop_file.unlink()

    screen = PyAutoGuiScreen(paths.screens_dir)
    planner = OpenAIPlanner(config=cfg)
    executor = ActionExecutor(backend=pyautogui)
    runner = Runner(config=cfg, screen=screen, planner=planner, executor=executor)

    if args.command == "run-once":
        cfg = cfg.__class__(**{**cfg.__dict__, "max_steps": 1})
        runner = Runner(config=cfg, screen=screen, planner=planner, executor=executor)

    result = runner.run()
    print(f"{result.reason} after {result.steps} steps")
    return 0
```

- [ ] **Step 4: Run import tests**

Run:

```powershell
python -m pytest tests/test_imports.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Run full pure test suite**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```powershell
git add src/windows_screen_agent/app.py tests/test_imports.py
git commit -m "feat: add cli entrypoint"
```

---

### Task 8: Hotkey And Tray Wrappers

**Files:**
- Create: `src/windows_screen_agent/hotkey.py`
- Create: `src/windows_screen_agent/tray.py`
- Modify: `README.md`

- [ ] **Step 1: Create hotkey wrapper**

Create `src/windows_screen_agent/hotkey.py`:

```python
from collections.abc import Callable

from pynput import keyboard


DEFAULT_HOTKEY = "<ctrl>+<alt>+<shift>+s"


def start_hotkey_listener(on_toggle: Callable[[], None], hotkey: str = DEFAULT_HOTKEY):
    listener = keyboard.GlobalHotKeys({hotkey: on_toggle})
    listener.start()
    return listener
```

- [ ] **Step 2: Create tray wrapper**

Create `src/windows_screen_agent/tray.py`:

```python
from collections.abc import Callable

from PIL import Image, ImageDraw
import pystray


def _icon_image() -> Image.Image:
    image = Image.new("RGB", (64, 64), color=(35, 35, 35))
    draw = ImageDraw.Draw(image)
    draw.rectangle((14, 18, 50, 44), outline=(230, 230, 230), width=3)
    draw.rectangle((26, 48, 38, 52), fill=(230, 230, 230))
    return image


def create_tray_icon(
    *,
    on_run: Callable[[], None],
    on_stop: Callable[[], None],
    on_quit: Callable[[], None],
) -> pystray.Icon:
    return pystray.Icon(
        "windows-screen-agent",
        _icon_image(),
        "Windows Screen Agent",
        menu=pystray.Menu(
            pystray.MenuItem("Run", lambda: on_run()),
            pystray.MenuItem("Stop", lambda: on_stop()),
            pystray.MenuItem("Quit", lambda: on_quit()),
        ),
    )
```

- [ ] **Step 3: Update README commands**

Add this section to `README.md` after the command list:

```markdown
## Tray And Hotkey

The planned tray wrapper exposes Run, Stop, and Quit actions. The default global hotkey is `Ctrl+Alt+Shift+S`. Keep this conservative default so it does not collide with common typing or browser shortcuts.
```

- [ ] **Step 4: Run import tests**

Run:

```powershell
python -m pytest tests/test_imports.py -q
```

Expected: `2 passed`.

- [ ] **Step 5: Commit**

```powershell
git add src/windows_screen_agent/hotkey.py src/windows_screen_agent/tray.py README.md
git commit -m "feat: add tray and hotkey wrappers"
```

---

### Task 9: Final Verification And Push

**Files:**
- Modify: no source files unless verification finds a real defect.

- [ ] **Step 1: Run full tests**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Run lint**

Run:

```powershell
python -m ruff check .
```

Expected: `All checks passed!`

- [ ] **Step 3: Verify CLI help**

Run:

```powershell
python -m windows_screen_agent.app --help
```

Expected: output includes `run`, `run-once`, `status`, and `stop`.

- [ ] **Step 4: Verify git status**

Run:

```powershell
git status --short --branch
```

Expected: branch is `main...origin/main` with no unstaged source changes after commits.

- [ ] **Step 5: Push**

Run:

```powershell
git push
```

Expected: all local commits are pushed to `origin/main`.

---

## Self-Review

- Spec coverage: package, config, logs, screenshot capture, OpenAI Responses API planner, JSON action parsing, coordinate validation, runner loop, CLI, hotkey/tray wrappers, README safety statement, and tests are covered by Tasks 1-9.
- Placeholder scan: no placeholder markers are present.
- Type consistency: `Config`, `Action`, `ScreenSnapshot`, `OpenAIPlanner.plan`, `ActionExecutor.execute`, and `Runner.run` are introduced before use and keep consistent names across tasks.
