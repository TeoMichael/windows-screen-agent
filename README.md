# Windows Screen Agent

Windows Screen Agent is a Windows-first screen automation assistant. It captures the current screen, asks a planner backend for one structured action, validates that action, executes it locally, and repeats until the task is complete or the user stops it.

This project is for personal practice, sandbox labs, forms, and repetitive local tasks. Do not use it for graded, proctored, honor-code-bound exams, credential harvesting, payment flows, production administration, or automation that violates a site's terms.

## Current Status

This repository is runnable as a developer preview:

- `WSA_PLANNER=codex` is the default and uses your local Codex CLI as the planner backend.
- `WSA_PLANNER=openai` uses the OpenAI Responses API instead.
- `python -m pytest -q` runs the sample test suite.
- `windows-screen-agent run` and `run-once` can move/click/type on the active Windows desktop.
- `windows-screen-agent tray` runs in the background and exposes global start/stop hotkeys.
- `windows-screen-agent install-autostart` installs a per-user Windows Startup shortcut so the tray listener starts after login.

## Requirements

- Windows 10 or 11
- Python 3.11+
- Codex CLI installed and logged in for the default `codex` backend, or an OpenAI API key in `OPENAI_API_KEY` for the `openai` backend

Use a normal Windows Python installation from python.org or the Microsoft Store. Avoid MSYS/Cygwin Python for this project because some Windows wheels may not install cleanly there.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
```

The default backend is Codex:

```powershell
$env:WSA_PLANNER = "codex"
$env:CODEX_BIN = "codex"
$env:WSA_MODE = "auto"
```

Use OpenAI API instead:

```powershell
$env:WSA_PLANNER = "openai"
$env:OPENAI_API_KEY = "your-api-key"
```

## Commands

```powershell
windows-screen-agent run-once
windows-screen-agent run
windows-screen-agent status
windows-screen-agent stop
windows-screen-agent doctor
windows-screen-agent tray
windows-screen-agent start-tray
windows-screen-agent install-autostart
windows-screen-agent uninstall-autostart
python -m pytest -q
```

## Safe First Run

Run these commands after installing:

```powershell
windows-screen-agent doctor
python -m pytest -q
```

`doctor` checks whether your selected planner backend is ready. Tests validate the parser, runner, config, sample form, and planner wrappers without moving the mouse.

For a visible local sample, open `samples/sample_form.html`, select a backend, focus the browser window, and run:

```powershell
windows-screen-agent run-once --note "This is the local sample form. Fill the name field with Sample User."
```

## Tray, Background Mode, And Hotkeys

The tray wrapper exposes Run, Stop, and Quit actions. For the current session, start it hidden in the background:

```powershell
windows-screen-agent start-tray
```

To start the tray automatically after Windows login, install the per-user Startup shortcut:

```powershell
windows-screen-agent install-autostart
```

Remove it with:

```powershell
windows-screen-agent uninstall-autostart
```

For debugging, you can still run the tray in the foreground:

```powershell
windows-screen-agent tray
```

Default global hotkeys:

- `Ctrl+Alt+Enter`: start a background `run`.
- `Ctrl+Alt+Backspace`: request an emergency stop.

Keep the tray process running while using hotkeys. The hotkeys use the selected planner backend, so `WSA_PLANNER=codex` uses local Codex and `WSA_PLANNER=openai` uses the OpenAI API.

## Configuration

- `WSA_PLANNER`: `codex` or `openai`. Defaults to `codex`.
- `WSA_MODE`: `auto`, `fast`, or `careful`. Defaults to `auto`; simple quiz/form runs use `fast`, complex/security/lab notes use `careful`.
- `CODEX_BIN`: Codex executable used when `WSA_PLANNER=codex`. Defaults to `codex`.
- `CODEX_MODEL`: optional default Codex model passed to `codex exec --model`.
- `CODEX_MODEL_FAST`: optional Codex model for `fast` profile.
- `CODEX_MODEL_CAREFUL`: optional Codex model for `careful` profile.
- `OPENAI_API_KEY`: required only when `WSA_PLANNER=openai`.
- `OPENAI_MODEL`: model used for planning actions. Defaults to `gpt-5.2`.
- `OPENAI_MODEL_FAST`: optional OpenAI model for `fast` profile. Defaults to `OPENAI_MODEL`.
- `OPENAI_MODEL_CAREFUL`: optional OpenAI model for `careful` profile. Defaults to `OPENAI_MODEL`.
- `WSA_MAX_STEPS`: maximum actions per run. Defaults to `20`.
- `WSA_MAX_RUNTIME_SECONDS`: maximum runtime per run. Defaults to `180`.
- `WSA_RUNTIME_DIR`: runtime data directory. Defaults to `%USERPROFILE%\.windows-screen-agent`.

For long quiz pages, raise the limits and keep the fast profile:

```powershell
$env:WSA_MODE = "fast"
$env:WSA_MAX_STEPS = "80"
$env:WSA_MAX_RUNTIME_SECONDS = "900"
windows-screen-agent tray
```

Scroll actions use full-page `PageDown`/`PageUp` movement instead of tiny mouse-wheel steps. Repeated scroll actions are amplified to move farther before the next screenshot.

## Safety Controls

- Stop file and emergency stop hotkey.
- Coordinate bounds checks.
- Action allowlist.
- Maximum step and runtime limits.
- Logs redact API keys and bearer tokens.
