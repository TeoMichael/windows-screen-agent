from dataclasses import dataclass

from windows_screen_agent.config import Config
from windows_screen_agent.openai_agent import OpenAIPlanner
from windows_screen_agent.screen import ScreenSnapshot


@dataclass
class FakeResponse:
    output_text: str


class FakeResponses:
    def __init__(self, output_text=None):
        self.calls = []
        self.output_text = output_text or (
            '{"actions":[{"action":"click","x":4,"y":5,"button":"left",'
            '"text":"","keys":[],"amount":0,"seconds":0,"reason":"press visible button"}]}'
        )

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse(self.output_text)


class FakeClient:
    def __init__(self, output_text=None):
        self.responses = FakeResponses(output_text=output_text)


def test_planner_calls_responses_api_and_parses_action(tmp_path):
    cfg = Config(
        openai_api_key="sk-test",
        model="gpt-5.2",
        runtime_dir=tmp_path,
        max_steps=3,
        max_runtime_seconds=10,
        action_delay_seconds=0.1,
        max_type_chars=100,
        confirm_before_submit=False,
    )
    client = FakeClient()
    planner = OpenAIPlanner(config=cfg, client=client)
    screen = ScreenSnapshot(
        path=tmp_path / "screen.png",
        width=100,
        height=80,
        data_url="data:image/png;base64,abc",
    )

    actions = planner.plan(screen=screen, note="fill the form", history=[])

    assert [action.action for action in actions] == ["click"]
    assert client.responses.calls[0]["model"] == "gpt-5.2"
    assert client.responses.calls[0]["input"][1]["content"][1]["type"] == "input_image"
    assert client.responses.calls[0]["text"]["format"]["name"] == "screen_action_plan"


def test_openai_planner_uses_profile_model(tmp_path):
    cfg = Config(
        openai_api_key="sk-test",
        model="gpt-5.2",
        openai_model_fast="gpt-fast",
        openai_model_careful="gpt-careful",
        runtime_dir=tmp_path,
        max_steps=3,
        max_runtime_seconds=10,
        action_delay_seconds=0.1,
        max_type_chars=100,
        confirm_before_submit=False,
    )
    client = FakeClient()
    planner = OpenAIPlanner(config=cfg, client=client)
    screen = ScreenSnapshot(
        path=tmp_path / "screen.png",
        width=100,
        height=80,
        data_url="data:image/png;base64,abc",
    )

    planner.plan(screen=screen, note="quiz", history=[], profile="fast")

    assert client.responses.calls[0]["model"] == "gpt-fast"


def test_openai_planner_answer_uses_answer_schema(tmp_path):
    cfg = Config(
        openai_api_key="sk-test",
        model="gpt-5.2",
        runtime_dir=tmp_path,
        max_steps=3,
        max_runtime_seconds=10,
        action_delay_seconds=0.1,
        max_type_chars=100,
        confirm_before_submit=False,
    )
    client = FakeClient(
        output_text='{"text":"1A","kind":"multiple_choice","reason":"visible"}'
    )
    planner = OpenAIPlanner(config=cfg, client=client)
    screen = ScreenSnapshot(
        path=tmp_path / "screen.png",
        width=100,
        height=80,
        data_url="data:image/png;base64,abc",
    )

    answer = planner.answer(screen=screen, note="answer only", history=[], profile="fast")

    assert answer.text == "1A"
    assert client.responses.calls[0]["text"]["format"]["name"] == "screen_answer"
