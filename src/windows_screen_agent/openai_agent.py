from typing import Any

from openai import OpenAI

from windows_screen_agent.actions import Action, parse_action
from windows_screen_agent.config import Config
from windows_screen_agent.prompt import ACTION_JSON_SCHEMA, build_developer_prompt, build_user_text
from windows_screen_agent.routing import openai_model_for_profile
from windows_screen_agent.screen import ScreenSnapshot


class OpenAIPlanner:
    def __init__(self, config: Config, client: Any | None = None):
        self.config = config
        self.client = client or OpenAI(api_key=config.openai_api_key)

    def plan(
        self,
        *,
        screen: ScreenSnapshot,
        note: str,
        history: list[dict],
        profile: str = "careful",
    ) -> Action:
        response = self.client.responses.create(
            model=openai_model_for_profile(self.config, profile),
            input=[
                {
                    "role": "developer",
                    "content": [{"type": "input_text", "text": build_developer_prompt()}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": build_user_text(note, screen.width, screen.height, history),
                        },
                        {"type": "input_image", "image_url": screen.data_url},
                    ],
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "screen_action",
                    "schema": ACTION_JSON_SCHEMA,
                    "strict": True,
                }
            },
            reasoning={"effort": "low"},
        )
        return parse_action(response.output_text)
