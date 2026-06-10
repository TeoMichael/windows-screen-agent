import json
from dataclasses import dataclass

from windows_screen_agent.actions import Action
from windows_screen_agent.config import Config
from windows_screen_agent.planners import AutoPlanner, build_planner
from windows_screen_agent.screen import ScreenSnapshot


def _config(tmp_path, backend="ollama"):
    return Config(
        openai_api_key="",
        model="gpt-5.2",
        planner_backend=backend,
        runtime_dir=tmp_path,
        max_steps=3,
        max_runtime_seconds=10,
        action_delay_seconds=0.1,
        max_type_chars=100,
        confirm_before_submit=False,
        ollama_base_url="http://localhost:11434",
        ollama_model_fast="qwen2.5vl:3b",
        ollama_model_careful="qwen2.5vl:7b",
    )


class FakeHTTPResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class FakeOpener:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def __call__(self, request, timeout):
        self.calls.append((request, timeout))
        return FakeHTTPResponse(self.payload)


def test_ollama_planner_posts_image_schema_and_parses_actions(tmp_path):
    from windows_screen_agent.ollama_agent import OllamaPlanner
    from windows_screen_agent.prompt import ACTION_PLAN_JSON_SCHEMA

    opener = FakeOpener(
        {
            "message": {
                "content": (
                    '{"actions":[{"action":"click","x":4,"y":5,"button":"left",'
                    '"text":"","keys":[],"amount":0,"seconds":0,"reason":"press"}]}'
                )
            }
        }
    )
    planner = OllamaPlanner(config=_config(tmp_path), opener=opener)
    screen = ScreenSnapshot(
        path=tmp_path / "screen.png",
        width=100,
        height=80,
        data_url="data:image/png;base64,abc123",
    )

    actions = planner.plan(screen=screen, note="local sample", history=[], profile="fast")

    request, timeout = opener.calls[0]
    payload = json.loads(request.data.decode("utf-8"))
    assert request.full_url == "http://localhost:11434/api/chat"
    assert timeout == 10
    assert payload["model"] == "qwen2.5vl:3b"
    assert payload["format"] == ACTION_PLAN_JSON_SCHEMA
    assert payload["stream"] is False
    assert payload["messages"][1]["images"] == ["abc123"]
    assert "Screen size: 100x80" in payload["messages"][1]["content"]
    assert [action.action for action in actions] == ["click"]


def test_ollama_planner_uses_careful_model(tmp_path):
    from windows_screen_agent.ollama_agent import OllamaPlanner

    opener = FakeOpener(
        {
            "message": {
                "content": (
                    '{"actions":[{"action":"done","x":0,"y":0,"button":"left",'
                    '"text":"","keys":[],"amount":0,"seconds":0,"reason":"ok"}]}'
                )
            }
        }
    )
    planner = OllamaPlanner(config=_config(tmp_path), opener=opener)
    screen = ScreenSnapshot(
        path=tmp_path / "screen.png",
        width=100,
        height=80,
        data_url="data:image/png;base64,abc123",
    )

    planner.plan(screen=screen, note="complex", history=[], profile="careful")

    payload = json.loads(opener.calls[0][0].data.decode("utf-8"))
    assert payload["model"] == "qwen2.5vl:7b"


def test_ollama_planner_answer_uses_answer_schema(tmp_path):
    from windows_screen_agent.ollama_agent import OllamaPlanner
    from windows_screen_agent.prompt import ANSWER_JSON_SCHEMA

    opener = FakeOpener(
        {
            "message": {
                "content": '{"text":"1A","kind":"multiple_choice","reason":"visible"}'
            }
        }
    )
    planner = OllamaPlanner(config=_config(tmp_path), opener=opener)
    screen = ScreenSnapshot(
        path=tmp_path / "screen.png",
        width=100,
        height=80,
        data_url="data:image/png;base64,abc123",
    )

    answer = planner.answer(screen=screen, note="answer only", history=[], profile="fast")

    payload = json.loads(opener.calls[0][0].data.decode("utf-8"))
    assert answer.text == "1A"
    assert payload["format"] == ANSWER_JSON_SCHEMA
    assert payload["messages"][1]["images"] == ["abc123"]


def test_planner_factory_selects_ollama_backend(tmp_path):
    from windows_screen_agent.ollama_agent import OllamaPlanner

    planner = build_planner(_config(tmp_path, backend="ollama"))

    assert isinstance(planner, OllamaPlanner)


def test_planner_factory_selects_auto_backend(tmp_path):
    planner = build_planner(_config(tmp_path, backend="auto"))

    assert isinstance(planner, AutoPlanner)


@dataclass
class FailingPlanner:
    calls: list[str]

    def plan(self, **kwargs):
        self.calls.append("fail")
        raise RuntimeError("backend unavailable")


@dataclass
class SuccessfulPlanner:
    calls: list[str]

    def plan(self, **kwargs):
        self.calls.append("success")
        return (Action(action="done", reason="ok"),)


def test_auto_planner_falls_back_to_next_backend():
    calls = []
    planner = AutoPlanner(
        [
            ("bad", FailingPlanner(calls)),
            ("good", SuccessfulPlanner(calls)),
        ]
    )

    actions = planner.plan(screen=None, note="", history=[], profile="fast")

    assert [action.action for action in actions] == ["done"]
    assert calls == ["fail", "success"]
