import json
import subprocess
from typing import Any

from windows_screen_agent.actions import Action, parse_action
from windows_screen_agent.config import Config
from windows_screen_agent.prompt import ACTION_JSON_SCHEMA, build_developer_prompt, build_user_text
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


def _build_codex_prompt(screen: ScreenSnapshot, note: str, history: list[dict]) -> str:
    return (
        build_developer_prompt()
        + "\n\n"
        + "You are acting as the planner backend for Windows Screen Agent. "
        + "Return only one JSON object and no prose. The local app will execute the action. "
        + f"The current screenshot is saved at: {screen.path}\n"
        + f"Action schema: {json.dumps(ACTION_JSON_SCHEMA, ensure_ascii=False)}\n"
        + build_user_text(note, screen.width, screen.height, history)
    )


class CodexPlanner:
    def __init__(self, config: Config, command_runner: Any = subprocess.run):
        self.config = config
        self.command_runner = command_runner

    def plan(self, *, screen: ScreenSnapshot, note: str, history: list[dict]) -> Action:
        prompt = _build_codex_prompt(screen, note, history)
        self.config.runtime_dir.mkdir(parents=True, exist_ok=True)
        schema_path = self.config.runtime_dir / "action-schema.json"
        schema_path.write_text(json.dumps(ACTION_JSON_SCHEMA, ensure_ascii=False), encoding="utf-8")
        result = self.command_runner(
            [
                self.config.codex_bin,
                "exec",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "--image",
                str(screen.path),
                "--output-schema",
                str(schema_path),
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=max(30, int(self.config.max_runtime_seconds)),
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"codex exec failed: {result.stderr.strip()}")
        return parse_action(extract_json_object(result.stdout))
