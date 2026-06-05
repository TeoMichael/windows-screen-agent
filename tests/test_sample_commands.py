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
    assert "OPENAI_API_KEY: missing" in result.stdout


def test_demo_runs_without_api_key_and_writes_logs(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "windows_screen_agent.app", "demo"],
        capture_output=True,
        text=True,
        check=False,
        env=_env_without_api_key(tmp_path),
    )

    assert result.returncode == 0
    assert "demo completed after 2 steps" in result.stdout
    assert (tmp_path / "logs" / "actions.jsonl").exists()
    assert (tmp_path / "screens").exists()
