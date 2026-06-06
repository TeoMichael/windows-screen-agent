from windows_screen_agent.config import Config
from windows_screen_agent.routing import choose_planning_profile


def _config(tmp_path, mode="auto"):
    return Config(
        openai_api_key="",
        model="gpt-5.2",
        runtime_dir=tmp_path,
        max_steps=3,
        max_runtime_seconds=10,
        action_delay_seconds=0.1,
        max_type_chars=100,
        confirm_before_submit=False,
        planner_mode=mode,
    )


def test_choose_profile_respects_explicit_mode(tmp_path):
    assert choose_planning_profile(_config(tmp_path, mode="fast"), note="", history=[]) == "fast"
    assert (
        choose_planning_profile(_config(tmp_path, mode="careful"), note="", history=[])
        == "careful"
    )


def test_auto_profile_defaults_to_fast_for_simple_quiz(tmp_path):
    assert choose_planning_profile(_config(tmp_path), note="answer the quiz", history=[]) == "fast"


def test_auto_profile_uses_careful_for_security_or_complex_tasks(tmp_path):
    assert (
        choose_planning_profile(_config(tmp_path), note="PortSwigger web security lab", history=[])
        == "careful"
    )


def test_auto_profile_uses_careful_after_repeated_actions(tmp_path):
    history = [
        {"action": "scroll", "amount": -5},
        {"action": "scroll", "amount": -5},
    ]

    assert choose_planning_profile(_config(tmp_path), note="", history=history) == "careful"
