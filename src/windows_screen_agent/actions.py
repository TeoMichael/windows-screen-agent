from dataclasses import dataclass
from dataclasses import replace
import json
import math
from typing import Any


SUPPORTED_ACTIONS = {"click", "type", "hotkey", "scroll", "wait", "done", "fail"}
SUPPORTED_BUTTONS = {"left", "right", "middle"}
MIN_SCROLL_UNITS = 15
SUPPORTED_HOTKEYS = {
    "enter",
    "tab",
    "esc",
    "escape",
    "ctrl",
    "shift",
    "alt",
    "win",
    "pagedown",
    "pageup",
    "a",
    "c",
    "v",
    "x",
    "z",
}


class ActionValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Action:
    action: str
    x: int | None = None
    y: int | None = None
    button: str = "left"
    text: str = ""
    keys: tuple[str, ...] = ()
    amount: int = 0
    seconds: float = 0.0
    reason: str = ""


def parse_action(raw: str | dict[str, Any]) -> Action:
    payload = json.loads(raw) if isinstance(raw, str) else raw
    if not isinstance(payload, dict):
        raise ActionValidationError("Action payload must be an object")

    name = str(payload.get("action", "")).strip().lower()
    if name not in SUPPORTED_ACTIONS:
        raise ActionValidationError(f"Unsupported action: {name}")

    keys = payload.get("keys") or ()
    if isinstance(keys, str):
        keys = (keys,)
    return Action(
        action=name,
        x=payload.get("x"),
        y=payload.get("y"),
        button=str(payload.get("button", "left")).lower(),
        text=str(payload.get("text", "")),
        keys=tuple(str(key).lower() for key in keys),
        amount=int(payload.get("amount", 0) or 0),
        seconds=float(payload.get("seconds", 0.0) or 0.0),
        reason=str(payload.get("reason", "")),
    )


def parse_action_plan(raw: str | dict[str, Any] | list[Any]) -> tuple[Action, ...]:
    payload = json.loads(raw) if isinstance(raw, str) else raw
    if isinstance(payload, dict) and "actions" not in payload:
        return (parse_action(payload),)
    if isinstance(payload, dict):
        payload = payload.get("actions")
    if not isinstance(payload, list) or not payload:
        raise ActionValidationError("Action plan must contain a non-empty actions list")
    return tuple(parse_action(item) for item in payload)


def validate_action(
    action: Action,
    *,
    screen_width: int,
    screen_height: int,
    max_type_chars: int,
) -> None:
    if action.action == "click":
        if action.x is None or action.y is None:
            raise ActionValidationError("Click action requires x and y")
        if not (0 <= int(action.x) < screen_width and 0 <= int(action.y) < screen_height):
            raise ActionValidationError("Click coordinates are off screen")
        if action.button not in SUPPORTED_BUTTONS:
            raise ActionValidationError(f"Unsupported button: {action.button}")

    if action.action == "type" and len(action.text) > max_type_chars:
        raise ActionValidationError("Type text is too long")

    if action.action == "hotkey":
        if not action.keys:
            raise ActionValidationError("Hotkey action requires keys")
        unsupported = [key for key in action.keys if key not in SUPPORTED_HOTKEYS]
        if unsupported:
            raise ActionValidationError(f"Unsupported hotkey: {unsupported[0]}")

    if action.action == "wait" and action.seconds < 0:
        raise ActionValidationError("Wait seconds cannot be negative")


class ActionExecutor:
    def __init__(self, backend: Any):
        self.backend = backend

    def execute(self, action: Action) -> None:
        if action.action == "click":
            self.backend.click(int(action.x), int(action.y), button=action.button)
        elif action.action == "type":
            self.backend.write(action.text, interval=0.01)
        elif action.action == "scroll":
            _execute_page_scroll(self.backend, action.amount)
        elif action.action == "hotkey":
            self.backend.hotkey(*action.keys)
        elif action.action in {"wait", "done", "fail"}:
            return


def _normalize_scroll_amount(amount: int) -> int:
    if amount == 0:
        return 0
    direction = 1 if amount > 0 else -1
    return direction * max(abs(amount), MIN_SCROLL_UNITS)


def _execute_page_scroll(backend: Any, amount: int) -> None:
    if amount == 0:
        return
    key = "pagedown" if amount < 0 else "pageup"
    repeats = max(1, min(3, math.ceil(abs(_normalize_scroll_amount(amount)) / MIN_SCROLL_UNITS)))
    for _ in range(repeats):
        if hasattr(backend, "press"):
            backend.press(key)
        elif hasattr(backend, "hotkey"):
            backend.hotkey(key)
        else:
            backend.scroll(_normalize_scroll_amount(amount))


def amplify_repeated_scroll(action: Action, history: list[dict]) -> Action:
    if action.action != "scroll" or action.amount == 0:
        return action
    direction = 1 if action.amount > 0 else -1
    trailing_same_direction = 0
    for previous in reversed(history):
        if previous.get("action") != "scroll":
            break
        previous_amount = int(previous.get("amount", 0) or 0)
        if previous_amount == 0 or (1 if previous_amount > 0 else -1) != direction:
            break
        trailing_same_direction += 1
    if trailing_same_direction == 0:
        return action
    units = min(3, trailing_same_direction + 1) * MIN_SCROLL_UNITS
    return replace(action, amount=direction * max(abs(action.amount), units))
