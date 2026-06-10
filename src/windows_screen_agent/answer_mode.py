from dataclasses import dataclass
import json
import re
import tkinter as tk
from typing import Any

import pyperclip

from windows_screen_agent.config import Config
from windows_screen_agent.logs import runtime_paths, write_status
from windows_screen_agent.routing import choose_planning_profile


@dataclass(frozen=True)
class AnswerResult:
    text: str
    kind: str = "free_text"


def normalize_multiple_choice_text(text: str) -> str:
    tokens = re.findall(r"\b(\d{1,2})\s*[\.\)\-:]?\s*([A-Za-z])\b", text)
    if not tokens:
        return text.strip()
    return " ".join(f"{number}{letter.upper()}" for number, letter in tokens)


def format_answer_text(result: AnswerResult) -> str:
    if result.kind == "multiple_choice":
        return normalize_multiple_choice_text(result.text)
    return result.text.strip()


def parse_answer_result(raw: str | dict[str, Any]) -> AnswerResult:
    payload = json.loads(raw) if isinstance(raw, str) else raw
    if not isinstance(payload, dict):
        raise ValueError("Answer payload must be an object")
    text = str(payload.get("text", "")).strip()
    kind = str(payload.get("kind", "free_text")).strip() or "free_text"
    if kind not in {"multiple_choice", "free_text"}:
        kind = "free_text"
    return AnswerResult(text=text, kind=kind)


def answer_icon_tokens(result: AnswerResult) -> list[str]:
    text = format_answer_text(result)
    if result.kind == "multiple_choice":
        tokens = re.findall(r"\b\d{1,2}[A-Za-z]\b", text)
        if tokens:
            return [token.upper() for token in tokens]
    return ["TXT"]


def _copy_to_clipboard_with_tk(text: str) -> None:
    root = tk.Tk()
    root.withdraw()
    try:
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
    finally:
        root.destroy()


def copy_to_clipboard(text: str, fallback_writer=_copy_to_clipboard_with_tk) -> None:
    try:
        pyperclip.copy(text)
    except pyperclip.PyperclipException:
        fallback_writer(text)


def run_answer_once(
    *,
    config: Config,
    screen: Any,
    planner: Any,
    clipboard_writer=copy_to_clipboard,
    note: str = "",
) -> AnswerResult:
    paths = runtime_paths(config.runtime_dir)
    write_status(paths, "answer: capture")
    snapshot = screen.capture()
    profile = choose_planning_profile(config, note=note, history=[])
    write_status(paths, f"answer: plan ({profile})")
    result = planner.answer(screen=snapshot, note=note, history=[], profile=profile)
    text = format_answer_text(result)
    clipboard_writer(text)
    paths.base_dir.joinpath("answer.txt").write_text(text, encoding="utf-8")
    paths.base_dir.joinpath("answer_tokens.txt").write_text(
        "\n".join(answer_icon_tokens(result)),
        encoding="utf-8",
    )
    write_status(paths, "answer ready")
    return result
