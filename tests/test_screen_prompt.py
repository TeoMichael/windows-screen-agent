from PIL import Image

from windows_screen_agent.prompt import ACTION_JSON_SCHEMA, ACTION_PLAN_JSON_SCHEMA, build_developer_prompt
from windows_screen_agent.screen import capture_screen


class FakeScreenshotBackend:
    def screenshot(self):
        return Image.new("RGB", (32, 24), color="white")


def test_capture_screen_saves_png_and_data_url(tmp_path):
    snapshot = capture_screen(tmp_path, backend=FakeScreenshotBackend())

    assert snapshot.path.exists()
    assert snapshot.width == 32
    assert snapshot.height == 24
    assert snapshot.data_url.startswith("data:image/png;base64,")


def test_prompt_mentions_allowed_actions_and_schema():
    prompt = build_developer_prompt()

    assert "coordinate-first" in prompt
    assert "actions" in prompt
    assert "up to 3" in prompt
    assert "Next" in prompt
    assert "Do not use this for graded" in prompt
    assert "already answered" in prompt
    assert "scroll action" in prompt
    assert "PageDown" in prompt
    assert "blank" in prompt
    assert ACTION_JSON_SCHEMA["type"] == "object"
    assert "action" in ACTION_JSON_SCHEMA["required"]


def test_structured_output_schema_requires_every_property():
    assert set(ACTION_JSON_SCHEMA["required"]) == set(ACTION_JSON_SCHEMA["properties"])


def test_plan_schema_wraps_actions_array():
    assert ACTION_PLAN_JSON_SCHEMA["type"] == "object"
    assert ACTION_PLAN_JSON_SCHEMA["required"] == ["actions"]
    assert ACTION_PLAN_JSON_SCHEMA["properties"]["actions"]["items"] == ACTION_JSON_SCHEMA
