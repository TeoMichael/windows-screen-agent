from windows_screen_agent.config import load_config
from windows_screen_agent.logs import redact_secrets, runtime_paths


def test_load_config_defaults_to_codex_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("WSA_PLANNER", raising=False)

    cfg = load_config()

    assert cfg.planner_backend == "codex"
    assert cfg.openai_api_key == ""
    assert cfg.max_runtime_seconds == 900.0
    assert cfg.action_delay_seconds == 0.2


def test_load_config_reads_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("WSA_PLANNER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.2")
    monkeypatch.setenv("WSA_MAX_STEPS", "7")
    monkeypatch.setenv("WSA_RUNTIME_DIR", str(tmp_path))

    cfg = load_config()

    assert cfg.openai_api_key == "sk-test"
    assert cfg.planner_backend == "openai"
    assert cfg.model == "gpt-5.2"
    assert cfg.max_steps == 7
    assert cfg.runtime_dir == tmp_path


def test_load_config_reads_mode_and_model_profiles(monkeypatch, tmp_path):
    monkeypatch.setenv("WSA_PLANNER", "codex")
    monkeypatch.setenv("WSA_MODE", "careful")
    monkeypatch.setenv("CODEX_MODEL_FAST", "codex-fast")
    monkeypatch.setenv("CODEX_MODEL_CAREFUL", "codex-careful")
    monkeypatch.setenv("OPENAI_MODEL_FAST", "openai-fast")
    monkeypatch.setenv("OPENAI_MODEL_CAREFUL", "openai-careful")
    monkeypatch.setenv("WSA_RUNTIME_DIR", str(tmp_path))

    cfg = load_config()

    assert cfg.planner_mode == "careful"
    assert cfg.codex_model_fast == "codex-fast"
    assert cfg.codex_model_careful == "codex-careful"
    assert cfg.openai_model_fast == "openai-fast"
    assert cfg.openai_model_careful == "openai-careful"


def test_load_config_rejects_unknown_mode(monkeypatch):
    monkeypatch.setenv("WSA_PLANNER", "codex")
    monkeypatch.setenv("WSA_MODE", "slowish")

    try:
        load_config()
    except ValueError as exc:
        assert "WSA_MODE" in str(exc)
    else:
        raise AssertionError("unknown WSA_MODE must be rejected")


def test_openai_backend_requires_api_key(monkeypatch):
    monkeypatch.setenv("WSA_PLANNER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    try:
        load_config()
    except ValueError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:
        raise AssertionError("openai planner must require OPENAI_API_KEY")


def test_load_config_reads_codex_binary(monkeypatch):
    monkeypatch.setenv("WSA_PLANNER", "codex")
    monkeypatch.setenv("CODEX_BIN", "C:/tools/codex.exe")

    cfg = load_config()

    assert cfg.planner_backend == "codex"
    assert cfg.codex_bin == "C:/tools/codex.exe"


def test_load_config_discovers_local_codex_binary(monkeypatch, tmp_path):
    monkeypatch.setenv("WSA_PLANNER", "codex")
    monkeypatch.delenv("CODEX_BIN", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    codex_bin = tmp_path / "OpenAI" / "Codex" / "bin" / "abc" / "codex.exe"
    codex_bin.parent.mkdir(parents=True)
    codex_bin.write_text("fake", encoding="utf-8")

    cfg = load_config()

    assert cfg.codex_bin == str(codex_bin)


def test_runtime_paths_creates_directories(tmp_path):
    paths = runtime_paths(tmp_path)

    assert paths.base_dir == tmp_path
    assert paths.screens_dir.exists()
    assert paths.logs_dir.exists()
    assert paths.status_file == tmp_path / "status.txt"


def test_redact_secrets_masks_keys_and_bearer_tokens():
    text = "OPENAI_API_KEY=sk-secret Authorization: Bearer abc123"

    redacted = redact_secrets(text)

    assert "sk-secret" not in redacted
    assert "abc123" not in redacted
    assert "[REDACTED]" in redacted
