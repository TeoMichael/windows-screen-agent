# Windows Screen Agent

Windows Screen Agent is a Windows-first screen automation assistant. It captures the current screen, sends the screenshot to the OpenAI Responses API, receives one structured action, validates that action, executes it locally, and repeats until the task is complete or the user stops it.

This project is for personal practice, sandbox labs, forms, and repetitive local tasks. Do not use it for graded, proctored, honor-code-bound exams, credential harvesting, payment flows, production administration, or automation that violates a site's terms.

## Current Status

This repository is runnable as a developer preview:

- `windows-screen-agent demo` runs without an API key and does not move the mouse.
- `python -m pytest -q` runs the sample test suite.
- `windows-screen-agent run` and `run-once` call the OpenAI API and can move/click/type on the active Windows desktop.

## Requirements

- Windows 10 or 11
- Python 3.11+
- An OpenAI API key in `OPENAI_API_KEY`

Use a normal Windows Python installation from python.org or the Microsoft Store. Avoid MSYS/Cygwin Python for this project because some Windows wheels may not install cleanly there.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
```

Set an API key only for live OpenAI runs:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
```

## Commands

```powershell
windows-screen-agent run-once
windows-screen-agent run
windows-screen-agent status
windows-screen-agent stop
windows-screen-agent doctor
windows-screen-agent demo
windows-screen-agent tray
python -m pytest -q
```

## Safe First Run

Run these commands after installing:

```powershell
windows-screen-agent doctor
windows-screen-agent demo
python -m pytest -q
```

`demo` is deterministic and offline. It creates a fake screenshot, runs a sample click/type/done sequence, and records the actions without controlling your desktop.

For a visible local sample, open `samples/sample_form.html`, set `OPENAI_API_KEY`, focus the browser window, and run:

```powershell
windows-screen-agent run-once --note "This is the local sample form. Fill the name field with Sample User."
```

## Tray And Hotkey

The planned tray wrapper exposes Run, Stop, and Quit actions. The default global hotkey is `Ctrl+Alt+Shift+S`. Keep this conservative default so it does not collide with common typing or browser shortcuts.

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
