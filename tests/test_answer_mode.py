from dataclasses import dataclass
from pathlib import Path

from windows_screen_agent.answer_mode import (
    AnswerResult,
    answer_icon_tokens,
    copy_to_clipboard,
    format_answer_text,
    parse_answer_result,
    run_answer_once,
)
from windows_screen_agent.config import Config
from windows_screen_agent.screen import ScreenSnapshot


def test_format_answer_text_keeps_short_multiple_choice_sequence():
    result = AnswerResult(text="1A 2B 3C", kind="multiple_choice")

    assert format_answer_text(result) == "1A 2B 3C"
    assert answer_icon_tokens(result) == ["1A", "2B", "3C"]


def test_format_answer_text_normalizes_multiple_choice_variants():
    result = AnswerResult(text="1. A\n2) b\n3: C", kind="multiple_choice")

    assert format_answer_text(result) == "1A 2B 3C"
    assert answer_icon_tokens(result) == ["1A", "2B", "3C"]


def test_answer_icon_tokens_use_txt_for_free_text():
    result = AnswerResult(text="The answer is a longer explanation.", kind="free_text")

    assert answer_icon_tokens(result) == ["TXT"]


def test_parse_answer_result_from_json():
    result = parse_answer_result('{"text":"1A 2B","kind":"multiple_choice","reason":"visible"}')

    assert result == AnswerResult(text="1A 2B", kind="multiple_choice")


def test_copy_to_clipboard_prefers_text_clipboard_backend(monkeypatch):
    copied = []
    fallback_calls = []

    monkeypatch.setattr(
        "windows_screen_agent.answer_mode.pyperclip.copy",
        lambda text: copied.append(text),
    )

    copy_to_clipboard("1A 2B", fallback_writer=lambda text: fallback_calls.append(text))

    assert copied == ["1A 2B"]
    assert fallback_calls == []


@dataclass
class FakeScreen:
    path: Path

    def capture(self):
        return ScreenSnapshot(
            path=self.path,
            width=100,
            height=80,
            data_url="data:image/png;base64,abc",
        )


class FakePlanner:
    def __init__(self):
        self.calls = []

    def answer(self, *, screen, note, history, profile):
        self.calls.append((screen, note, history, profile))
        return AnswerResult(text="1A 2B", kind="multiple_choice")


def _config(tmp_path):
    return Config(
        openai_api_key="",
        model="gpt-5.2",
        runtime_dir=tmp_path,
        max_steps=3,
        max_runtime_seconds=10,
        action_delay_seconds=0.1,
        max_type_chars=100,
        confirm_before_submit=False,
    )


def test_run_answer_once_copies_and_persists_answer(tmp_path):
    copied = []
    planner = FakePlanner()

    result = run_answer_once(
        config=_config(tmp_path),
        screen=FakeScreen(tmp_path / "screen.png"),
        planner=planner,
        clipboard_writer=copied.append,
        note="visible quiz",
    )

    assert result.text == "1A 2B"
    assert copied == ["1A 2B"]
    assert (tmp_path / "answer.txt").read_text(encoding="utf-8") == "1A 2B"
    assert (tmp_path / "answer_tokens.txt").read_text(encoding="utf-8") == "1A\n2B"
    assert planner.calls[0][3] == "fast"
