# Samples

These samples are safe local checks for a fresh clone.

## 1. Run the automated test suite

```powershell
python -m pytest -q
```

## 2. Run the built-in demo without an API key

```powershell
windows-screen-agent demo
```

The demo uses an in-memory sample screen, a deterministic demo planner, and a recording backend. It does not call OpenAI and does not move the mouse.

## 3. Try a visible sample form

Open `sample_form.html` in a browser or Notepad. For live automation, set `OPENAI_API_KEY`, focus the sample form window, and run:

```powershell
windows-screen-agent run-once --note "This is the local sample form. Fill the name field with Sample User."
```

Use only local or sandbox pages while testing.
