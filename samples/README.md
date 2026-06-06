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

## 3. Try a visible sample form

Open `sample_form.html` in a browser or Notepad. Focus the sample form window, then run:

```powershell
windows-screen-agent run-once --note "This is the local sample form. Fill the name field with Sample User."
```

Use only local or sandbox pages while testing.
