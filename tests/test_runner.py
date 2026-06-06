from dataclasses import dataclass
from pathlib import Path

from windows_screen_agent.actions import Action
from windows_screen_agent.config import Config
from windows_screen_agent.runner import Runner
from windows_screen_agent.screen import ScreenSnapshot


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
    def __init__(self, actions):
        self.actions = list(actions)
        self.profiles = []

    def plan(self, *, screen, note, history, profile):
        self.profiles.append(profile)
        return self.actions.pop(0)


class FakeExecutor:
    def __init__(self):
        self.actions = []

    def execute(self, action):
        self.actions.append(action.action)


def _config(tmp_path):
    return Config(
        openai_api_key="sk-test",
        model="gpt-5.2",
        runtime_dir=tmp_path,
        max_steps=3,
        max_runtime_seconds=10,
        action_delay_seconds=0.0,
        max_type_chars=100,
        confirm_before_submit=False,
    )


def test_runner_stops_on_done(tmp_path):
    executor = FakeExecutor()
    planner = FakePlanner([Action(action="done", reason="finished")])
    runner = Runner(
        config=_config(tmp_path),
        screen=FakeScreen(tmp_path / "screen.png"),
        planner=planner,
        executor=executor,
    )

    result = runner.run(note="")

    assert result.reason == "done"
    assert executor.actions == []
    assert planner.profiles == ["fast"]


def test_runner_executes_action_then_done(tmp_path):
    executor = FakeExecutor()
    runner = Runner(
        config=_config(tmp_path),
        screen=FakeScreen(tmp_path / "screen.png"),
        planner=FakePlanner(
            [
                Action(action="click", x=1, y=2, button="left", reason="click"),
                Action(action="done", reason="finished"),
            ]
        ),
        executor=executor,
    )

    result = runner.run(note="")

    assert result.reason == "done"
    assert executor.actions == ["click"]


def test_runner_executes_action_batch_from_one_plan_call(tmp_path):
    executor = FakeExecutor()
    planner = FakePlanner(
        [
            [
                Action(action="click", x=1, y=2, button="left", reason="answer"),
                Action(action="click", x=80, y=70, button="left", reason="next"),
            ],
            Action(action="done", reason="finished"),
        ]
    )
    runner = Runner(
        config=_config(tmp_path),
        screen=FakeScreen(tmp_path / "screen.png"),
        planner=planner,
        executor=executor,
    )

    result = runner.run(note="")

    assert result.reason == "done"
    assert executor.actions == ["click", "click"]
    assert len(planner.profiles) == 2


def test_runner_rejects_empty_action_batch(tmp_path):
    executor = FakeExecutor()
    runner = Runner(
        config=_config(tmp_path),
        screen=FakeScreen(tmp_path / "screen.png"),
        planner=FakePlanner([[]]),
        executor=executor,
    )

    result = runner.run(note="")

    assert result.reason == "validation failed"
    assert executor.actions == []
