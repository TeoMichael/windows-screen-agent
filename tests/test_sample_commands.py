import os
import subprocess
import sys


def _env_without_api_key(tmp_path):
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)
    env["WSA_RUNTIME_DIR"] = str(tmp_path)
    return env


def test_doctor_runs_without_api_key(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "windows_screen_agent.app", "doctor"],
        capture_output=True,
        text=True,
        check=False,
        env=_env_without_api_key(tmp_path),
    )

    assert result.returncode == 0
    assert "Python:" in result.stdout
    assert "Planner backend: codex" in result.stdout


def test_doctor_reports_unusable_codex_binary(tmp_path):
    env = _env_without_api_key(tmp_path)
    env["CODEX_BIN"] = str(tmp_path / "missing-codex.exe")

    result = subprocess.run(
        [sys.executable, "-m", "windows_screen_agent.app", "doctor"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0
    assert "CODEX_BIN:" in result.stdout
    assert "[warn]" in result.stdout


def test_demo_command_is_removed(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "windows_screen_agent.app", "demo"],
        capture_output=True,
        text=True,
        check=False,
        env=_env_without_api_key(tmp_path),
    )

    assert result.returncode == 2


def test_autostart_commands_are_dispatchable(monkeypatch, tmp_path, capsys):
    from windows_screen_agent import app

    monkeypatch.setenv("WSA_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setattr(app, "install_autostart", lambda **kwargs: tmp_path / "agent.lnk")
    monkeypatch.setattr(app, "uninstall_autostart", lambda: tmp_path / "agent.lnk")

    assert app.main(["install-autostart", "--no-start"]) == 0
    assert "autostart installed" in capsys.readouterr().out

    assert app.main(["uninstall-autostart"]) == 0
    assert "autostart removed" in capsys.readouterr().out


def test_start_tray_command_dispatches_background_launcher(monkeypatch, tmp_path, capsys):
    from windows_screen_agent import app

    monkeypatch.setenv("WSA_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setattr(app, "start_tray_background", lambda **kwargs: 4321)

    assert app.main(["start-tray"]) == 0

    assert "tray started pid 4321" in capsys.readouterr().out
