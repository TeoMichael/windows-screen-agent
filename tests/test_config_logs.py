import pytest

from windows_screen_agent.config import load_config
from windows_screen_agent.logs import redact_secrets, runtime_paths


def test_load_config_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        load_config()


def test_load_config_reads_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.2")
    monkeypatch.setenv("WSA_MAX_STEPS", "7")
    monkeypatch.setenv("WSA_RUNTIME_DIR", str(tmp_path))

    cfg = load_config()

    assert cfg.openai_api_key == "sk-test"
    assert cfg.model == "gpt-5.2"
    assert cfg.max_steps == 7
    assert cfg.runtime_dir == tmp_path


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
