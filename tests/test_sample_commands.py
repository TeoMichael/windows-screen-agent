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
