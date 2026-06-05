import pytest

from windows_screen_agent.actions import (
    Action,
    ActionExecutor,
    ActionValidationError,
    parse_action,
    validate_action,
)


def test_parse_click_action():
    action = parse_action('{"action":"click","x":10,"y":20,"button":"left","reason":"select"}')

    assert action.action == "click"
    assert action.x == 10
    assert action.y == 20


def test_parse_rejects_unknown_action():
    with pytest.raises(ActionValidationError, match="Unsupported action"):
        parse_action('{"action":"drag","x":1,"y":1}')


def test_validate_rejects_offscreen_click():
    action = Action(action="click", x=9999, y=20, button="left", reason="bad")

    with pytest.raises(ActionValidationError, match="off screen"):
        validate_action(action, screen_width=100, screen_height=100, max_type_chars=100)


def test_validate_rejects_excessive_type_text():
    action = Action(action="type", text="x" * 101, reason="too much")

    with pytest.raises(ActionValidationError, match="too long"):
        validate_action(action, screen_width=100, screen_height=100, max_type_chars=100)


def test_executor_dispatches_click_to_backend():
    calls = []
    backend = type(
        "Backend",
        (),
        {
            "click": lambda self, x, y, button: calls.append(("click", x, y, button)),
            "write": lambda self, text, interval: calls.append(("write", text, interval)),
            "scroll": lambda self, amount: calls.append(("scroll", amount)),
            "hotkey": lambda self, *keys: calls.append(("hotkey", keys)),
        },
    )()

    ActionExecutor(backend=backend).execute(Action(action="click", x=5, y=6, button="left"))

    assert calls == [("click", 5, 6, "left")]
