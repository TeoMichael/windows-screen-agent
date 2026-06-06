import subprocess

from windows_screen_agent.codex_agent import CodexPlanner, extract_json_object
from windows_screen_agent.config import Config
from windows_screen_agent.planners import build_planner
from windows_screen_agent.screen import ScreenSnapshot


def _config(tmp_path, backend="codex"):
    return Config(
        openai_api_key="sk-test",
        model="gpt-5.2",
        codex_bin="codex",
        planner_backend=backend,
        runtime_dir=tmp_path,
        max_steps=3,
        max_runtime_seconds=10,
        action_delay_seconds=0.1,
        max_type_chars=100,
        confirm_before_submit=False,
    )


def test_extract_json_object_from_markdown_fenced_output():
    text = 'Here is the next action:\n```json\n{"action":"done","reason":"complete"}\n```'

    assert extract_json_object(text) == '{"action":"done","reason":"complete"}'


def test_codex_planner_invokes_codex_exec_and_parses_action(tmp_path):
    calls = []

    def fake_runner(argv, **kwargs):
        calls.append((argv, kwargs))

        class Result:
            returncode = 0
            stdout = (
                '{"actions":[{"action":"click","x":4,"y":5,"button":"left",'
                '"text":"","keys":[],"amount":0,"seconds":0,"reason":"press"}]}'
            )
            stderr = ""

        return Result()

    planner = CodexPlanner(config=_config(tmp_path), command_runner=fake_runner)
    screen = ScreenSnapshot(
        path=tmp_path / "screen.png",
        width=100,
        height=80,
        data_url="data:image/png;base64,abc",
    )

    actions = planner.plan(screen=screen, note="fill the form", history=[])

    assert [action.action for action in actions] == ["click"]
    assert calls[0][0][0:2] == ["codex", "exec"]
    assert "--image" in calls[0][0]
    assert str(screen.path) in calls[0][0]
    assert "--output-schema" in calls[0][0]
    assert str(screen.path) in calls[0][0][-1]


def test_codex_planner_passes_profile_model(tmp_path):
    calls = []
    cfg = _config(tmp_path)
    cfg = Config(
        **{
            **cfg.__dict__,
            "codex_model_fast": "codex-fast",
            "codex_model_careful": "codex-careful",
        }
    )

    def fake_runner(argv, **kwargs):
        calls.append((argv, kwargs))

        class Result:
            returncode = 0
            stdout = (
                '{"actions":[{"action":"done","x":0,"y":0,"button":"left",'
                '"text":"","keys":[],"amount":0,"seconds":0,"reason":"ok"}]}'
            )
            stderr = ""

        return Result()

    planner = CodexPlanner(config=cfg, command_runner=fake_runner)
    screen = ScreenSnapshot(
        path=tmp_path / "screen.png",
        width=100,
        height=80,
        data_url="data:image/png;base64,abc",
    )

    planner.plan(screen=screen, note="quiz", history=[], profile="fast")

    assert "--model" in calls[0][0]
    assert calls[0][0][calls[0][0].index("--model") + 1] == "codex-fast"


def test_codex_planner_hides_codex_console_window(tmp_path):
    calls = []

    def fake_runner(argv, **kwargs):
        calls.append((argv, kwargs))

        class Result:
            returncode = 0
            stdout = (
                '{"actions":[{"action":"done","x":0,"y":0,"button":"left",'
                '"text":"","keys":[],"amount":0,"seconds":0,"reason":"ok"}]}'
            )
            stderr = ""

        return Result()

    planner = CodexPlanner(config=_config(tmp_path), command_runner=fake_runner)
    screen = ScreenSnapshot(
        path=tmp_path / "screen.png",
        width=100,
        height=80,
        data_url="data:image/png;base64,abc",
    )

    planner.plan(screen=screen, note="quiz", history=[], profile="fast")

    assert calls[0][1]["creationflags"] & subprocess.CREATE_NO_WINDOW


def test_planner_factory_selects_codex_by_default(tmp_path):
    planner = build_planner(_config(tmp_path, backend="codex"))

    assert isinstance(planner, CodexPlanner)
