# Tray Status Menu Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the current Windows Screen Agent status directly in the tray menu.

**Architecture:** Add a small status reader that converts `status.txt` values into user-facing labels, then pass that reader into the tray menu as a disabled status row. The tray run/stop callbacks update status immediately while the runner continues to own final persisted status.

**Tech Stack:** Python, pystray, pytest.

---

### Task 1: Tray Status Reader

**Files:**
- Modify: `src/windows_screen_agent/tray.py`
- Test: `tests/test_tray_status.py`

- [x] Write a failing test that formats missing status as `Status: Idle`.
- [x] Write a failing test that formats `step 3: plan (fast)` as `Status: Working - step 3: plan (fast)`.
- [x] Implement the reader and formatter with no tray side effects.
- [x] Run the targeted status tests.

### Task 2: Tray Menu Integration

**Files:**
- Modify: `src/windows_screen_agent/tray.py`
- Modify: `src/windows_screen_agent/app.py`
- Test: `tests/test_tray_status.py`
- Test: `tests/test_tray_hotkeys.py`

- [x] Write a failing test that the menu starts with a disabled status item.
- [x] Pass the runtime status file reader into `create_tray_icon`.
- [x] Set status to `starting` when Run is requested and `stopping` when Stop is requested.
- [x] Run tray tests, full pytest, ruff, and doctor.
