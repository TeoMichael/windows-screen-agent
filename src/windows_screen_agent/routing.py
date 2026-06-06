from windows_screen_agent.config import Config


CAREFUL_NOTE_KEYWORDS = {
    "careful",
    "complex",
    "essay",
    "security",
    "portswigger",
    "web security",
    "lab",
    "exploit",
    "vulnerability",
    "tự luận",
    "dien vao",
    "điền vào",
    "lỗ hổng",
    "thâm nhập",
}


def choose_planning_profile(
    config: Config,
    *,
    note: str,
    history: list[dict],
) -> str:
    if config.planner_mode in {"fast", "careful"}:
        return config.planner_mode

    lower_note = note.lower()
    if any(keyword in lower_note for keyword in CAREFUL_NOTE_KEYWORDS):
        return "careful"

    if len(history) >= 2:
        last_two = history[-2:]
        repeated_action = last_two[0].get("action")
        if repeated_action == last_two[1].get("action") and repeated_action in {
            "scroll",
            "wait",
            "fail",
        }:
            return "careful"

    return "fast"


def codex_model_for_profile(config: Config, profile: str) -> str:
    if profile == "fast":
        return config.codex_model_fast
    return config.codex_model_careful


def openai_model_for_profile(config: Config, profile: str) -> str:
    if profile == "fast":
        return config.openai_model_fast
    return config.openai_model_careful
