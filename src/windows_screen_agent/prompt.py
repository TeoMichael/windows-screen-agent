ACTION_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "action": {
            "type": "string",
            "enum": ["click", "type", "hotkey", "scroll", "wait", "done", "fail"],
        },
        "x": {"type": ["integer", "null"]},
        "y": {"type": ["integer", "null"]},
        "button": {"type": "string", "enum": ["left", "right", "middle"]},
        "text": {"type": "string"},
        "keys": {"type": "array", "items": {"type": "string"}},
        "amount": {"type": "integer"},
        "seconds": {"type": "number"},
        "reason": {"type": "string"},
    },
    "required": ["action", "x", "y", "button", "text", "keys", "amount", "seconds", "reason"],
}


def build_developer_prompt() -> str:
    return (
        "You are Windows Screen Agent, a coordinate-first Windows automation planner. "
        "Read the screenshot and return exactly one JSON action matching the schema. "
        "Allowed actions are click, type, hotkey, scroll, wait, done, and fail. "
        "Return every schema field for every action; use neutral values like x=0, y=0, "
        "button='left', text='', keys=[], amount=0, and seconds=0 when a field is not "
        "relevant to the chosen action. "
        "For quiz or form pages, work top-to-bottom. Do not click choices that are "
        "already answered, marked correct, marked wrong, disabled, or showing result "
        "percentages. If all currently visible questions are already answered or the "
        "next unanswered question is partly below the bottom of the screen, scroll down "
        "with a negative amount such as -5. Use positive scroll amounts only to move "
        "back up. For fill-in-the-blank, short-answer, or text field questions, click "
        "the visible blank/input first, then use type with the concise answer when the "
        "field is focused. "
        "Do not use this for graded, proctored, honor-code-bound exams, credential "
        "harvesting, payment flows, destructive operations, or production administration. "
        "Prefer small reversible actions. If the task is complete, return done. "
        "If the visible task is unsafe or unclear, return fail."
    )


def build_user_text(note: str, width: int, height: int, history: list[dict]) -> str:
    return (
        f"Screen size: {width}x{height}. "
        f"User note: {note.strip() if note.strip() else '(none)'}. "
        f"Recent actions: {history[-5:]}. "
        "Choose the next single action."
    )
