import subprocess
import sys

import windows_screen_agent
from windows_screen_agent.app import build_parser
from windows_screen_agent.hotkey import DEFAULT_RUN_HOTKEY, DEFAULT_STOP_HOTKEY
from windows_screen_agent.tray import create_tray_icon


def test_version_is_present():
    assert windows_screen_agent.__version__ == "0.1.0"


def test_parser_has_core_commands():
    parser = build_parser()
    commands = parser._subparsers._group_actions[0].choices

    assert {
        "run",
        "run-once",
        "answer-once",
        "status",
        "stop",
        "doctor",
        "tray",
        "start-tray",
        "install-autostart",
        "uninstall-autostart",
    } <= set(commands)
    assert "demo" not in commands


def test_default_hotkeys_start_and_stop_exam_mode():
    assert DEFAULT_RUN_HOTKEY == "<ctrl>+<alt>+<enter>"
    assert DEFAULT_STOP_HOTKEY == "<ctrl>+<alt>+<backspace>"


def test_tray_icon_can_be_created():
    icon = create_tray_icon(on_run=lambda: None, on_stop=lambda: None, on_quit=lambda: None)

    assert icon.name == "windows-screen-agent"


def test_module_help_lists_core_commands():
    result = subprocess.run(
        [sys.executable, "-m", "windows_screen_agent.app", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "run-once" in result.stdout
    assert "status" in result.stdout
    assert "doctor" in result.stdout
    assert "demo" not in result.stdout
