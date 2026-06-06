import pytest

from windows_screen_agent.actions import (
    Action,
    ActionExecutor,
    ActionValidationError,
    parse_action,
    parse_action_plan,
    validate_action,
)


def test_parse_click_action():
    action = parse_action('{"action":"click","x":10,"y":20,"button":"left","reason":"select"}')

    assert action.action == "click"
    assert action.x == 10
    assert action.y == 20


def test_parse_action_plan_accepts_multiple_actions():
    actions = parse_action_plan(
        {
            "actions": [
                {"action": "click", "x": 10, "y": 20, "button": "left", "reason": "answer"},
                {
                    "action": "click",
                    "x": 80,
                    "y": 70,
                    "button": "left",
                    "reason": "next",
                },
            ]
        }
    )

    assert [action.action for action in actions] == ["click", "click"]
    assert actions[0].x == 10
    assert actions[1].x == 80


def test_parse_action_plan_keeps_single_action_compatibility():
    actions = parse_action_plan(
        '{"action":"click","x":10,"y":20,"button":"left","reason":"select"}'
    )

    assert len(actions) == 1
    assert actions[0].action == "click"


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


def test_executor_expands_tiny_scroll_steps():
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

    ActionExecutor(backend=backend).execute(Action(action="scroll", amount=-5))

    assert calls == [("hotkey", ("pagedown",))]


def test_executor_repeats_page_down_for_larger_scroll():
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

    ActionExecutor(backend=backend).execute(Action(action="scroll", amount=-30))

    assert calls == [("hotkey", ("pagedown",)), ("hotkey", ("pagedown",))]


def test_repeated_scroll_actions_are_amplified():
    from windows_screen_agent.actions import amplify_repeated_scroll

    action = amplify_repeated_scroll(
        Action(action="scroll", amount=-5),
        history=[{"action": "scroll", "amount": -15}],
    )

    assert action.amount == -30
