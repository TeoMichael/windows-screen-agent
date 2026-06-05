import argparse
from dataclasses import replace
from pathlib import Path
import os

from windows_screen_agent.actions import ActionExecutor
from windows_screen_agent.config import load_config
from windows_screen_agent.logs import runtime_paths
from windows_screen_agent.openai_agent import OpenAIPlanner
from windows_screen_agent.runner import Runner
from windows_screen_agent.screen import capture_screen


class PyAutoGuiScreen:
    def __init__(self, screens_dir: Path, backend):
        self.screens_dir = screens_dir
        self.backend = backend

    def capture(self):
        return capture_screen(self.screens_dir, backend=self.backend)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="windows-screen-agent")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run")
    sub.add_parser("run-once")
    sub.add_parser("status")
    sub.add_parser("stop")
    return parser


def _runtime_dir_without_api_key() -> Path:
    return Path(os.environ.get("WSA_RUNTIME_DIR", str(Path.home() / ".windows-screen-agent")))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command in {"stop", "status"}:
        paths = runtime_paths(_runtime_dir_without_api_key())
        if args.command == "stop":
            paths.stop_file.write_text("stop", encoding="utf-8")
            print("stop requested")
            return 0
        if paths.status_file.exists():
            print(paths.status_file.read_text(encoding="utf-8"))
        else:
            print("idle")
        return 0

    import pyautogui

    cfg = load_config()
    paths = runtime_paths(cfg.runtime_dir)
    if paths.stop_file.exists():
        paths.stop_file.unlink()

    screen = PyAutoGuiScreen(paths.screens_dir, backend=pyautogui)
    planner = OpenAIPlanner(config=cfg)
    executor = ActionExecutor(backend=pyautogui)

    if args.command == "run-once":
        cfg = replace(cfg, max_steps=1)

    runner = Runner(config=cfg, screen=screen, planner=planner, executor=executor)
    result = runner.run()
    print(f"{result.reason} after {result.steps} steps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
