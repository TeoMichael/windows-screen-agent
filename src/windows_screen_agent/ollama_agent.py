import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from windows_screen_agent.actions import Action, parse_action_plan
from windows_screen_agent.config import Config
from windows_screen_agent.prompt import ACTION_PLAN_JSON_SCHEMA, build_developer_prompt, build_user_text
from windows_screen_agent.routing import ollama_model_for_profile
from windows_screen_agent.screen import ScreenSnapshot


def _screen_image_base64(screen: ScreenSnapshot) -> str:
    prefix = "base64,"
    if prefix in screen.data_url:
        return screen.data_url.split(prefix, 1)[1]
    return screen.data_url


class OllamaPlanner:
    def __init__(self, config: Config, opener: Any = urlopen):
        self.config = config
        self.opener = opener

    def plan(
        self,
        *,
        screen: ScreenSnapshot,
        note: str,
        history: list[dict],
        profile: str = "careful",
    ) -> tuple[Action, ...]:
        payload = {
            "model": ollama_model_for_profile(self.config, profile),
            "messages": [
                {"role": "system", "content": build_developer_prompt()},
                {
                    "role": "user",
                    "content": build_user_text(
                        note,
                        screen.width,
                        screen.height,
                        history,
                        profile=profile,
                    ),
                    "images": [_screen_image_base64(screen)],
                },
            ],
            "stream": False,
            "format": ACTION_PLAN_JSON_SCHEMA,
            "options": {"temperature": 0},
        }
        request = Request(
            f"{self.config.ollama_base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self.opener(request, timeout=_request_timeout(self.config)) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, OSError, TimeoutError) as exc:
            raise RuntimeError(f"ollama request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError("ollama returned invalid JSON") from exc

        content = response_payload.get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("ollama response did not contain message.content")
        return parse_action_plan(content)


def _request_timeout(config: Config) -> float:
    return min(30.0, max(2.0, float(config.max_runtime_seconds)))
