from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from windows_screen_agent.actions import Action, ActionExecutor
from windows_screen_agent.config import Config
from windows_screen_agent.runner import Runner
from windows_screen_agent.screen import capture_screen


class DemoScreenshotBackend:
    def screenshot(self) -> Image.Image:
        image = Image.new("RGB", (640, 360), color="white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((40, 40, 600, 310), outline=(40, 40, 40), width=2)
        draw.text((60, 70), "Windows Screen Agent demo form", fill=(0, 0, 0))
        draw.rectangle((60, 125, 410, 155), outline=(80, 80, 80), width=2)
        draw.text((70, 132), "Name", fill=(80, 80, 80))
        draw.rectangle((60, 190, 180, 230), outline=(30, 90, 160), width=2)
        draw.text((92, 202), "Submit", fill=(30, 90, 160))
        return image


class DemoScreen:
    def __init__(self, screens_dir: Path):
        self.screens_dir = screens_dir
        self.backend = DemoScreenshotBackend()

    def capture(self):
        return capture_screen(self.screens_dir, backend=self.backend)


class DemoPlanner:
    def __init__(self):
        self.actions = [
            Action(
                action="click",
                x=90,
                y=140,
                button="left",
                reason="Focus the sample name field",
            ),
            Action(
                action="type",
                text="Sample User",
                reason="Fill the sample name field",
            ),
            Action(action="done", reason="Demo sequence completed"),
        ]

    def plan(self, *, screen, note, history):
        return self.actions.pop(0)


class RecordingBackend:
    def __init__(self):
        self.calls: list[tuple] = []

    def click(self, x: int, y: int, button: str):
        self.calls.append(("click", x, y, button))

    def write(self, text: str, interval: float):
        self.calls.append(("write", text, interval))

    def scroll(self, amount: int):
        self.calls.append(("scroll", amount))

    def hotkey(self, *keys: str):
        self.calls.append(("hotkey", keys))


@dataclass(frozen=True)
class DemoResult:
    reason: str
    steps: int
    calls: list[tuple]


def run_demo(runtime_dir: Path) -> DemoResult:
    cfg = Config(
        openai_api_key="demo",
        model="demo",
        runtime_dir=runtime_dir,
        max_steps=5,
        max_runtime_seconds=30.0,
        action_delay_seconds=0.0,
        max_type_chars=1000,
        confirm_before_submit=False,
    )
    backend = RecordingBackend()
    runner = Runner(
        config=cfg,
        screen=DemoScreen((runtime_dir / "screens")),
        planner=DemoPlanner(),
        executor=ActionExecutor(backend=backend),
    )
    if runner.paths.stop_file.exists():
        runner.paths.stop_file.unlink()
    result = runner.run(note="demo")
    return DemoResult(reason=result.reason, steps=result.steps, calls=backend.calls)
