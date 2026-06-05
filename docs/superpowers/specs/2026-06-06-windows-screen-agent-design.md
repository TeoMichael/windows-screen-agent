# Windows Screen Agent MVP Design

## Goal

Build a Windows-first screen automation assistant inspired by `exam-computer`, using the OpenAI API instead of Claude Code. The MVP should run on Windows 10/11, capture the current screen, ask OpenAI what to do next, execute simple coordinate-based actions, and repeat until the task is complete or the user stops it.

The intended use is personal practice, sandbox labs, forms, and repetitive local tasks. It is not designed for graded, proctored, honor-code-bound exams, production credentials, payments, destructive changes, or other high-risk workflows.

## MVP Scope

The first version is coordinate-first:

- Capture the active desktop screenshot.
- Send the screenshot plus task instructions to the OpenAI Responses API.
- Receive one structured action at a time.
- Execute actions with Windows automation primitives.
- Re-capture the screen and continue.
- Provide a tray/status indicator, logs, and an emergency stop.

The MVP supports both web pages and desktop apps at a basic level because it acts on visible pixels. More precise Windows UI Automation and Playwright integrations are prepared as interfaces but are not required to be complete in v1.

## Non-Goals

- No exam-cheating workflow or stealth behavior.
- No credential harvesting, bypassing access control, or automation against production systems.
- No installer in v1.
- No full browser DOM automation in v1.
- No full Windows UI Automation control tree in v1.
- No persistent memory beyond local config, note text, screenshots, and logs.

## OpenAI API Approach

Use the Responses API as the primary API surface because it supports text and image inputs and agent-style workflows. The MVP uses a vision-capable model to inspect a screenshot and return a strict JSON action. A later version can add the official Computer Use tool path if availability, cost, and safety requirements fit the project.

The agent request includes:

- A developer instruction describing allowed behavior, safety limits, and output schema.
- The current screenshot as a base64 data URL.
- Optional user note text.
- A compact action history from the current run.
- Display dimensions and DPI metadata when available.

The model must return exactly one action:

```json
{
  "action": "click",
  "x": 640,
  "y": 420,
  "button": "left",
  "reason": "Select the visible submit button"
}
```

Supported MVP actions:

- `click`
- `type`
- `hotkey`
- `scroll`
- `wait`
- `done`
- `fail`

## Architecture

```text
Hotkey / tray
  -> runner loop
     -> screenshot capture
     -> OpenAI action planner
     -> action validator
     -> PyAutoGUI executor
     -> status and logs
     -> repeat or stop
```

Planned project layout:

```text
windows-screen-agent/
  pyproject.toml
  README.md
  src/windows_screen_agent/
    app.py
    config.py
    hotkey.py
    tray.py
    screen.py
    openai_agent.py
    actions.py
    runner.py
    prompt.py
    logs.py
  tests/
```

## Components

`app.py` exposes the CLI entrypoint: start, stop, status, run-once, and optional debug commands.

`config.py` reads environment variables and local config. `OPENAI_API_KEY` is required. Model, max steps, action delay, screenshot detail, and log directory are configurable.

`hotkey.py` handles the global start/stop hotkey. The default should be conservative and easy to disable.

`tray.py` shows the system tray status and menu actions: start, stop, edit note, open logs, quit.

`screen.py` captures screenshots, reads display size, handles DPI awareness, and saves the latest image.

`openai_agent.py` calls the OpenAI Responses API, sends screenshot input, and parses the returned action.

`actions.py` validates and executes actions. In v1 this primarily uses PyAutoGUI. It rejects off-screen coordinates, unsupported keys, excessive text length, and unsafe repeated actions.

`runner.py` owns the loop: check stop flag, capture, plan, validate, execute, log, and repeat.

`prompt.py` defines the system/developer prompt and JSON schema instructions.

`logs.py` writes run logs, action history, model output summaries, and error reports.

## Data Flow

1. User presses the hotkey or starts from tray/CLI.
2. Runner creates a run directory and writes status `starting`.
3. Runner captures the full screen.
4. OpenAI agent receives screenshot, instructions, optional note, and recent actions.
5. Model returns one structured action.
6. Validator checks action safety and bounds.
7. Executor performs the action.
8. Runner waits briefly, captures the next screenshot, and repeats.
9. Runner stops on `done`, max steps, timeout, explicit stop, or validation failure.

## Safety

The MVP must include:

- Emergency stop hotkey.
- Max step count per run.
- Max runtime per run.
- Coordinate bounds checks.
- Action allowlist.
- Optional confirm-before-submit mode for destructive-looking actions.
- Local logs that do not include API keys.
- A clear README statement that the tool is for practice, sandbox, form, and personal automation only.

The MVP should not store the OpenAI API key in project files. It should read the key from environment variables or a user-managed secret store.

## Error Handling

If screenshot capture fails, the run stops and writes a visible error status.

If the OpenAI request fails, the run retries a small fixed number of times, then stops.

If the model returns invalid JSON or an unsupported action, the runner logs the raw output and stops.

If an action is unsafe or out of bounds, the runner rejects it and stops rather than guessing.

If the user triggers stop, the runner exits promptly and leaves a final status.

## Testing

Unit tests cover:

- Config loading.
- Prompt construction.
- Action JSON parsing.
- Coordinate validation.
- Action allowlist enforcement.
- Runner stop conditions.
- Log redaction.

Integration tests can use mocked screenshots and mocked OpenAI responses. Live UI automation tests are manual for v1 because they depend on the active Windows desktop.

## Future Enhancements

- Add `UIAEngine` using Windows UI Automation or pywinauto for native app reliability.
- Add `BrowserEngine` using Playwright for DOM-aware web automation.
- Add a packaged `.exe` with PyInstaller.
- Add a richer tray note editor.
- Add per-domain or per-app allowlists.
- Add screenshot diffing to detect whether actions changed the screen.
- Add a dry-run mode that shows intended actions without executing them.

## Acceptance Criteria

- A user can start and stop a run from CLI and tray/hotkey.
- The app captures the current Windows screen.
- The app sends screenshot context to OpenAI through the Responses API.
- The app parses a structured action response.
- The app executes basic click, type, scroll, wait, and done actions.
- The app logs each step and stops cleanly.
- Tests pass for pure logic and safety validation.
