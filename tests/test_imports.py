import windows_screen_agent
from windows_screen_agent.app import build_parser


def test_version_is_present():
    assert windows_screen_agent.__version__ == "0.1.0"


def test_parser_has_core_commands():
    parser = build_parser()
    commands = parser._subparsers._group_actions[0].choices

    assert {"run", "run-once", "status", "stop"} <= set(commands)
