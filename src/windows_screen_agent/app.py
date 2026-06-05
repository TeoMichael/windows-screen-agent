import argparse
from dataclasses import replace
import os
from pathlib import Path
import threading

from windows_screen_agent.actions import ActionExecutor
from windows_screen_agent.config import load_config
from windows_screen_agent.demo import run_demo
from windows_screen_agent.doctor import collect_diagnostics, format_diagnostics
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
    run = sub.add_parser("run")
    run.add_argument("--note", default="")
    run_once = sub.add_parser("run-once")
    run_once.add_argument("--note", default="")
    sub.add_parser("status")
    sub.add_parser("stop")
    sub.add_parser("demo")
    sub.add_parser("doctor")
    sub.add_parser("tray")
    return parser


def _runtime_dir_without_api_key() -> Path:
    return Path(os.environ.get("WSA_RUNTIME_DIR", str(Path.home() / ".windows-screen-agent")))


def _request_stop(runtime_dir: Path) -> None:
    paths = runtime_paths(runtime_dir)
    paths.stop_file.write_text("stop", encoding="utf-8")


def _run_tray(runtime_dir: Path) -> int:
    from windows_screen_agent.tray import create_tray_icon

    icon_holder = {}

    def run_background():
        thread = threading.Thread(target=lambda: main(["run"]), daemon=True)
        thread.start()

    def stop_run():
        _request_stop(runtime_dir)

    def quit_tray():
        stop_run()
        icon_holder["icon"].stop()

    icon = create_tray_icon(on_run=run_background, on_stop=stop_run, on_quit=quit_tray)
    icon_holder["icon"] = icon
    print("tray running")
    icon.run()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runtime_dir = _runtime_dir_without_api_key()

    if args.command in {"stop", "status", "demo", "doctor", "tray"}:
        paths = runtime_paths(runtime_dir)
        if args.command == "stop":
            _request_stop(runtime_dir)
            print("stop requested")
            return 0
        if args.command == "demo":
            result = run_demo(runtime_dir)
            calls = ", ".join(call[0] for call in result.calls)
            print(f"demo completed after {result.steps} steps: {calls}")
            return 0
        if args.command == "doctor":
            diagnostics = collect_diagnostics(
                runtime_dir=runtime_dir,
                openai_api_key=os.environ.get("OPENAI_API_KEY"),
            )
            print(format_diagnostics(diagnostics))
            return 0
        if args.command == "tray":
            return _run_tray(runtime_dir)
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
    result = runner.run(note=args.note)
    print(f"{result.reason} after {result.steps} steps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
