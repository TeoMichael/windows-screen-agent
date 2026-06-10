# Tray Answer Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add tray model selection, a one-shot answer-only hotkey, clipboard output, and short answer cycling on the tray icon.

**Architecture:** Keep the existing action runner unchanged for `Ctrl+Alt+Enter`. Add a separate answer-only planner path that captures one screenshot, asks the selected backend for text answers only, copies that text to the clipboard, stores it in runtime files, and updates tray icon state. Persist tray-selected backend in a small runtime settings file.

**Tech Stack:** Python, pystray, pynput, PIL, pytest, Windows clipboard via tkinter fallback.

---

### Task 1: Runtime Settings And Model Menu

**Files:**
- Create: `src/windows_screen_agent/settings.py`
- Modify: `src/windows_screen_agent/tray.py`
- Modify: `src/windows_screen_agent/app.py`
- Test: `tests/test_settings.py`
- Test: `tests/test_tray_status.py`

- [x] Write failing tests for reading default settings and saving selected planner.
- [x] Write failing tests for tray `Model` submenu entries: Auto, Codex, OpenAI, Ollama.
- [x] Implement JSON settings in the runtime directory.
- [x] Wire tray model selection to update settings.

### Task 2: Answer-Only Planner

**Files:**
- Create: `src/windows_screen_agent/answer_mode.py`
- Modify: `src/windows_screen_agent/prompt.py`
- Test: `tests/test_answer_mode.py`

- [x] Write failing tests for parsing short multiple-choice answers into `1A`, `2B`, `3C`.
- [x] Write failing tests for preserving long free-text answers.
- [x] Write failing tests for copying answer text and writing runtime `answer.txt`.
- [x] Implement answer-only prompt, parser helpers, clipboard writer, and one-shot service.

### Task 3: Hotkey And Dynamic Tray Icon

**Files:**
- Modify: `src/windows_screen_agent/hotkey.py`
- Modify: `src/windows_screen_agent/tray.py`
- Modify: `src/windows_screen_agent/app.py`
- Test: `tests/test_hotkey.py`
- Test: `tests/test_tray_hotkeys.py`
- Test: `tests/test_tray_status.py`

- [x] Write failing tests for answer-only hotkey registration.
- [x] Write failing tests for icon label cycling: `1A -> 2B -> 3C -> 1A`.
- [x] Add status-icon rendering helpers for idle, watching, thinking, acting, answer, error.
- [x] Wire answer hotkey to run one-shot answer mode in a background thread.

### Task 4: Documentation And Verification

**Files:**
- Modify: `README.md`
- Modify: `samples/README.md`

- [x] Document answer-only mode and clipboard behavior.
- [x] Run targeted tests, full pytest, ruff, and doctor.
- [x] Commit and push to `main`.
