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
