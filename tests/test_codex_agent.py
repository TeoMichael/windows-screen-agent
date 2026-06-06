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

    def fake_runner(argv, *, capture_output, text, timeout, check):
        calls.append(argv)

        class Result:
            returncode = 0
            stdout = '{"action":"click","x":4,"y":5,"button":"left","reason":"press"}'
            stderr = ""

        return Result()

    planner = CodexPlanner(config=_config(tmp_path), command_runner=fake_runner)
    screen = ScreenSnapshot(
        path=tmp_path / "screen.png",
        width=100,
        height=80,
        data_url="data:image/png;base64,abc",
    )

    action = planner.plan(screen=screen, note="fill the form", history=[])

    assert action.action == "click"
    assert calls[0][0:2] == ["codex", "exec"]
    assert "--image" in calls[0]
    assert str(screen.path) in calls[0]
    assert "--output-schema" in calls[0]
    assert str(screen.path) in calls[0][-1]


def test_planner_factory_selects_codex_by_default(tmp_path):
    planner = build_planner(_config(tmp_path, backend="codex"))

    assert isinstance(planner, CodexPlanner)
