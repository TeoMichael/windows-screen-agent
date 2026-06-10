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


ACTION_PLAN_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "actions": {
            "type": "array",
            "minItems": 1,
            "maxItems": 3,
            "items": ACTION_JSON_SCHEMA,
        }
    },
    "required": ["actions"],
}


ANSWER_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "text": {"type": "string"},
        "kind": {"type": "string", "enum": ["multiple_choice", "free_text"]},
        "reason": {"type": "string"},
    },
    "required": ["text", "kind", "reason"],
}


def build_developer_prompt() -> str:
    return (
        "You are Windows Screen Agent, a coordinate-first Windows automation planner. "
        "Read the screenshot and return exactly one JSON object with an actions array "
        "matching the schema. Return up to 3 actions when they are all safe from the "
        "same screenshot. "
        "Allowed actions are click, type, hotkey, scroll, wait, done, and fail. "
        "Return every schema field for every action; use neutral values like x=0, y=0, "
        "button='left', text='', keys=[], amount=0, and seconds=0 when a field is not "
        "relevant to the chosen action. "
        "For simple multiple-choice practice quizzes, work top-to-bottom and prefer the "
        "fast path: click each visible unanswered answer that you can identify with high "
        "confidence. If a single-question page has a visible Next or Next Question button, "
        "you may include the answer click followed by the Next click in the same actions "
        "array. Do not batch a final submit, finish, purchase, login, or destructive action. "
        "Do not click choices that are "
        "already answered, marked correct, marked wrong, disabled, or showing result "
        "percentages. If all currently visible questions are already answered or the "
        "next unanswered question is partly below the bottom of the screen, return a "
        "scroll action; the app will perform full-page PageDown/PageUp movement and "
        "then capture the updated screen. Use negative amounts to move down and "
        "positive amounts only to move back up. For fill-in-the-blank, short-answer, "
        "or text field questions, click "
        "the visible blank/input first, then use type with the concise answer when the "
        "field is focused. "
        "Do not use this for graded, proctored, honor-code-bound exams, credential "
        "harvesting, payment flows, destructive operations, or production administration. "
        "Prefer small reversible actions. If the task is complete, return done. "
        "If the visible task is unsafe or unclear, return fail."
    )


def build_answer_developer_prompt() -> str:
    return (
        "You are Windows Screen Agent answer-only mode. Read the screenshot and return "
        "only the answer text in JSON. Do not choose coordinates and do not request any "
        "local action. For visible multiple-choice questions, return compact tokens like "
        "'1A 2B 3C' when question numbers and option letters are visible or inferable. "
        "If there is one multiple-choice question, return a single token like '1A'. "
        "For fill-in-the-blank or free-response prompts, return the concise answer text. "
        "Set kind to multiple_choice only when the text is a sequence of numbered option "
        "tokens; otherwise set kind to free_text. If the task is unsafe, graded, "
        "proctored, honor-code-bound, or unclear, return a short refusal in text with "
        "kind free_text."
    )


def build_user_text(note: str, width: int, height: int, history: list[dict], profile: str = "fast") -> str:
    return (
        f"Screen size: {width}x{height}. "
        f"User note: {note.strip() if note.strip() else '(none)'}. "
        f"Planner profile: {profile}. "
        f"Recent actions: {history[-5:]}. "
        "Choose the next action plan. In fast profile, keep reasoning short and batch "
        "obvious quiz answer clicks or answer-plus-next clicks when the coordinates remain stable. "
        "In careful profile, return fewer actions when the page may change after a click."
    )


def build_answer_user_text(note: str, width: int, height: int, profile: str = "fast") -> str:
    return (
        f"Screen size: {width}x{height}. "
        f"User note: {note.strip() if note.strip() else '(none)'}. "
        f"Planner profile: {profile}. "
        "Return one answer JSON object for the current screenshot."
    )
