import windows_screen_agent
from windows_screen_agent.app import build_parser
from windows_screen_agent.hotkey import DEFAULT_HOTKEY
from windows_screen_agent.tray import create_tray_icon


def test_version_is_present():
    assert windows_screen_agent.__version__ == "0.1.0"


def test_parser_has_core_commands():
    parser = build_parser()
    commands = parser._subparsers._group_actions[0].choices

    assert {"run", "run-once", "status", "stop"} <= set(commands)


def test_default_hotkey_is_conservative():
    assert DEFAULT_HOTKEY == "<ctrl>+<alt>+<shift>+s"


def test_tray_icon_can_be_created():
    icon = create_tray_icon(on_run=lambda: None, on_stop=lambda: None, on_quit=lambda: None)

    assert icon.name == "windows-screen-agent"
