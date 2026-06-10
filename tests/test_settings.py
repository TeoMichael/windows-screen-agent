from windows_screen_agent.settings import RuntimeSettings, load_settings, save_settings


def test_load_settings_defaults_when_file_is_missing(tmp_path):
    settings = load_settings(tmp_path / "settings.json")

    assert settings == RuntimeSettings(planner_backend=None)


def test_save_settings_round_trips_selected_planner(tmp_path):
    settings_file = tmp_path / "settings.json"

    save_settings(settings_file, RuntimeSettings(planner_backend="ollama"))

    assert load_settings(settings_file) == RuntimeSettings(planner_backend="ollama")


def test_load_settings_ignores_unknown_planner(tmp_path):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text('{"planner_backend":"unknown"}', encoding="utf-8")

    assert load_settings(settings_file) == RuntimeSettings(planner_backend=None)


def test_runtime_settings_override_loaded_config(monkeypatch, tmp_path):
    from windows_screen_agent.app import _load_config_with_runtime_settings

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("WSA_PLANNER", raising=False)
    save_settings(tmp_path / "settings.json", RuntimeSettings(planner_backend="ollama"))

    cfg = _load_config_with_runtime_settings(tmp_path)

    assert cfg.planner_backend == "ollama"


def test_diagnostic_config_uses_runtime_settings(monkeypatch, tmp_path):
    from windows_screen_agent.app import _diagnostic_config

    monkeypatch.setenv("WSA_RUNTIME_DIR", str(tmp_path))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("WSA_PLANNER", raising=False)
    save_settings(tmp_path / "settings.json", RuntimeSettings(planner_backend="ollama"))

    cfg = _diagnostic_config()

    assert cfg.planner_backend == "ollama"
