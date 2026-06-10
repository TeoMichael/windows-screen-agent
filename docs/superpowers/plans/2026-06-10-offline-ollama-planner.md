# Offline Ollama Planner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an offline-capable local planner backend using Ollama while keeping Codex and OpenAI behavior unchanged.

**Architecture:** Introduce `OllamaPlanner` as a third planner implementation that sends the existing screenshot prompt and `ACTION_PLAN_JSON_SCHEMA` to a local Ollama HTTP API. Extend config and planner factory to support `WSA_PLANNER=ollama` and `WSA_PLANNER=auto`; `auto` wraps concrete planners and falls back when a backend fails.

**Tech Stack:** Python stdlib HTTP (`urllib.request`), pytest, existing action schema and screen snapshots.

---

### Task 1: Config And Factory

**Files:**
- Modify: `src/windows_screen_agent/config.py`
- Modify: `src/windows_screen_agent/planners.py`
- Test: `tests/test_config_logs.py`
- Test: `tests/test_ollama_agent.py`

- [x] Write failing tests for `WSA_PLANNER=ollama`, Ollama model/base URL env vars, and `WSA_PLANNER=auto`.
- [x] Add `ollama_base_url`, `ollama_model_fast`, and `ollama_model_careful` to `Config`.
- [x] Update validation so `codex`, `openai`, `ollama`, and `auto` are accepted.
- [x] Update planner factory to select the new planner classes.

### Task 2: Ollama Planner

**Files:**
- Create: `src/windows_screen_agent/ollama_agent.py`
- Test: `tests/test_ollama_agent.py`

- [x] Write a failing test that `OllamaPlanner.plan()` sends screenshot base64, prompt text, and `ACTION_PLAN_JSON_SCHEMA`.
- [x] Implement a small JSON POST client with timeout and no new dependency.
- [x] Parse Ollama response content via `parse_action_plan`.
- [x] Add useful errors for unreachable Ollama and invalid responses.

### Task 3: Auto Fallback And Doctor

**Files:**
- Modify: `src/windows_screen_agent/planners.py`
- Modify: `src/windows_screen_agent/doctor.py`
- Modify: `src/windows_screen_agent/app.py`
- Test: `tests/test_ollama_agent.py`
- Test: `tests/test_sample_commands.py`

- [x] Write a failing test that auto fallback tries a failed planner then a successful planner.
- [x] Add a simple `AutoPlanner` wrapper.
- [x] Extend doctor output to show Ollama service/model readiness.
- [x] Keep existing doctor behavior for Codex/OpenAI.

### Task 4: Documentation And Verification

**Files:**
- Modify: `README.md`

- [x] Document installing Ollama, pulling `qwen2.5vl:7b`, and setting `WSA_PLANNER=ollama`.
- [x] Run targeted tests, full pytest, ruff, and doctor.
- [x] Commit and push to `main`.
