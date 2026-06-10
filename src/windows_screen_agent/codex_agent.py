import json
import subprocess
from typing import Any

from windows_screen_agent.actions import Action, parse_action_plan
from windows_screen_agent.answer_mode import AnswerResult, parse_answer_result
from windows_screen_agent.config import Config
from windows_screen_agent.prompt import (
    ACTION_PLAN_JSON_SCHEMA,
    ANSWER_JSON_SCHEMA,
    build_answer_developer_prompt,
    build_answer_user_text,
    build_developer_prompt,
    build_user_text,
)
from windows_screen_agent.routing import codex_model_for_profile
from windows_screen_agent.screen import ScreenSnapshot


def extract_json_object(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    if stripped.startswith("{"):
        return stripped

    start = stripped.find("{")
    if start == -1:
        raise ValueError("Codex output did not contain a JSON object")

    depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(stripped[start:], start=start):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return stripped[start : index + 1]
    raise ValueError("Codex output contained an incomplete JSON object")


def _build_codex_prompt(screen: ScreenSnapshot, note: str, history: list[dict], profile: str) -> str:
    return (
        build_developer_prompt()
        + "\n\n"
        + "You are acting as the planner backend for Windows Screen Agent. "
        + "Return only one JSON object and no prose. The local app will execute the actions. "
        + f"The current screenshot is saved at: {screen.path}\n"
        + f"Action plan schema: {json.dumps(ACTION_PLAN_JSON_SCHEMA, ensure_ascii=False)}\n"
        + build_user_text(note, screen.width, screen.height, history, profile=profile)
    )


def _build_codex_answer_prompt(screen: ScreenSnapshot, note: str, profile: str) -> str:
    return (
        build_answer_developer_prompt()
        + "\n\n"
        + "You are acting as the answer-only backend for Windows Screen Agent. "
        + "Return only one JSON object and no prose. The local app will copy the answer text. "
        + f"The current screenshot is saved at: {screen.path}\n"
        + f"Answer result schema: {json.dumps(ANSWER_JSON_SCHEMA, ensure_ascii=False)}\n"
        + build_answer_user_text(note, screen.width, screen.height, profile=profile)
    )


def _hidden_subprocess_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    creation_no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if creation_no_window:
        kwargs["creationflags"] = creation_no_window

    startupinfo_type = getattr(subprocess, "STARTUPINFO", None)
    startf_use_show_window = getattr(subprocess, "STARTF_USESHOWWINDOW", 0)
    sw_hide = getattr(subprocess, "SW_HIDE", 0)
    if startupinfo_type is not None and startf_use_show_window:
        startupinfo = startupinfo_type()
        startupinfo.dwFlags |= startf_use_show_window
        startupinfo.wShowWindow = sw_hide
        kwargs["startupinfo"] = startupinfo
    return kwargs


class CodexPlanner:
    def __init__(self, config: Config, command_runner: Any = subprocess.run):
        self.config = config
        self.command_runner = command_runner

    def plan(
        self,
        *,
        screen: ScreenSnapshot,
        note: str,
        history: list[dict],
        profile: str = "careful",
    ) -> tuple[Action, ...]:
        prompt = _build_codex_prompt(screen, note, history, profile)
        self.config.runtime_dir.mkdir(parents=True, exist_ok=True)
        schema_path = self.config.runtime_dir / "action-schema.json"
        schema_path.write_text(json.dumps(ACTION_PLAN_JSON_SCHEMA, ensure_ascii=False), encoding="utf-8")
        argv = [
            self.config.codex_bin,
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
        ]
        model = codex_model_for_profile(self.config, profile)
        if model:
            argv.extend(["--model", model])
        argv.extend(
            [
                "--image",
                str(screen.path),
                "--output-schema",
                str(schema_path),
                prompt,
            ]
        )
        result = self.command_runner(
            argv,
            capture_output=True,
            text=True,
            timeout=max(30, int(self.config.max_runtime_seconds)),
            check=False,
            **_hidden_subprocess_kwargs(),
        )
        if result.returncode != 0:
            raise RuntimeError(f"codex exec failed: {result.stderr.strip()}")
        return parse_action_plan(extract_json_object(result.stdout))

    def answer(
        self,
        *,
        screen: ScreenSnapshot,
        note: str,
        history: list[dict],
        profile: str = "careful",
    ) -> AnswerResult:
        prompt = _build_codex_answer_prompt(screen, note, profile)
        self.config.runtime_dir.mkdir(parents=True, exist_ok=True)
        schema_path = self.config.runtime_dir / "answer-schema.json"
        schema_path.write_text(json.dumps(ANSWER_JSON_SCHEMA, ensure_ascii=False), encoding="utf-8")
        argv = [
            self.config.codex_bin,
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
        ]
        model = codex_model_for_profile(self.config, profile)
        if model:
            argv.extend(["--model", model])
        argv.extend(
            [
                "--image",
                str(screen.path),
                "--output-schema",
                str(schema_path),
                prompt,
            ]
        )
        result = self.command_runner(
            argv,
            capture_output=True,
            text=True,
            timeout=max(30, int(self.config.max_runtime_seconds)),
            check=False,
            **_hidden_subprocess_kwargs(),
        )
        if result.returncode != 0:
            raise RuntimeError(f"codex exec failed: {result.stderr.strip()}")
        return parse_answer_result(extract_json_object(result.stdout))
