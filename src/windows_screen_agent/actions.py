from dataclasses import dataclass
import json
from typing import Any


SUPPORTED_ACTIONS = {"click", "type", "hotkey", "scroll", "wait", "done", "fail"}
SUPPORTED_BUTTONS = {"left", "right", "middle"}
SUPPORTED_HOTKEYS = {
    "enter",
    "tab",
    "esc",
    "escape",
    "ctrl",
    "shift",
    "alt",
    "win",
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
            self.backend.scroll(action.amount)
        elif action.action == "hotkey":
            self.backend.hotkey(*action.keys)
        elif action.action in {"wait", "done", "fail"}:
            return
