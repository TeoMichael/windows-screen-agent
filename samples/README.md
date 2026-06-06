# Samples

These samples are safe local checks for a fresh clone.

## 1. Run the automated test suite

```powershell
python -m pytest -q
```

## 2. Select a planner backend

```powershell
$env:WSA_PLANNER = "codex"
windows-screen-agent doctor
```

The default `codex` backend uses your local Codex CLI. To use OpenAI instead:

```powershell
$env:WSA_PLANNER = "openai"
$env:OPENAI_API_KEY = "your-api-key"
windows-screen-agent doctor
```

For quiz pages, start with fast mode and a larger step budget:

```powershell
$env:WSA_MODE = "fast"
$env:WSA_MAX_STEPS = "80"
$env:WSA_MAX_RUNTIME_SECONDS = "900"
```

## 3. Try a visible sample form

Open `sample_form.html` in a browser or Notepad. Focus the sample form window, then run:

```powershell
windows-screen-agent run-once --note "This is the local sample form. Fill the name field with Sample User."
```

Use only local or sandbox pages while testing.

## 4. Try tray hotkeys

Start the tray process in the background:

```powershell
windows-screen-agent start-tray
```

Then focus the sample form window and use:

- `Ctrl+Alt+Enter` to start a background run.
- `Ctrl+Alt+Backspace` to stop it.

Install auto-start after login:

```powershell
windows-screen-agent install-autostart
```
