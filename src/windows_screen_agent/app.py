import argparse
from dataclasses import replace
import os
from pathlib import Path
import threading
import traceback

from windows_screen_agent.actions import ActionExecutor
from windows_screen_agent.answer_mode import run_answer_once
from windows_screen_agent.autostart import install_autostart, start_tray_background, uninstall_autostart
from windows_screen_agent.config import Config, load_config
from windows_screen_agent.doctor import collect_diagnostics, format_diagnostics
from windows_screen_agent.logs import runtime_paths, write_status
from windows_screen_agent.planners import build_planner
from windows_screen_agent.runner import Runner
from windows_screen_agent.screen import capture_screen
from windows_screen_agent.settings import RuntimeSettings, load_settings, save_settings


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
    answer_once = sub.add_parser("answer-once")
    answer_once.add_argument("--note", default="")
    sub.add_parser("status")
    sub.add_parser("stop")
    sub.add_parser("doctor")
    sub.add_parser("tray")
    sub.add_parser("start-tray")
    install = sub.add_parser("install-autostart")
    install.add_argument("--no-start", action="store_true")
    sub.add_parser("uninstall-autostart")
    return parser


def _runtime_dir_without_api_key() -> Path:
    return Path(os.environ.get("WSA_RUNTIME_DIR", str(Path.home() / ".windows-screen-agent")))


def _settings_file(runtime_dir: Path) -> Path:
    return runtime_dir / "settings.json"


def _load_config_with_runtime_settings(runtime_dir: Path) -> Config:
    cfg = load_config()
    settings = load_settings(_settings_file(runtime_dir))
    if settings.planner_backend:
        cfg = replace(cfg, planner_backend=settings.planner_backend)
        if cfg.planner_backend == "openai" and not cfg.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when selected planner is openai")
    return cfg


def _request_stop(runtime_dir: Path) -> None:
    paths = runtime_paths(runtime_dir)
    paths.stop_file.write_text("stop", encoding="utf-8")


def _clear_stop(runtime_dir: Path) -> None:
    paths = runtime_paths(runtime_dir)
    if paths.stop_file.exists():
        paths.stop_file.unlink()


def _diagnostic_config() -> Config:
    try:
        cfg = load_config()
    except ValueError:
        runtime_dir = _runtime_dir_without_api_key()
        cfg = Config(
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            model=os.environ.get("OPENAI_MODEL", "gpt-5.2"),
            runtime_dir=runtime_dir,
            max_steps=20,
            max_runtime_seconds=900.0,
            action_delay_seconds=0.2,
            max_type_chars=1000,
            confirm_before_submit=False,
            planner_backend=os.environ.get("WSA_PLANNER", "codex").strip().lower(),
            codex_bin=os.environ.get("CODEX_BIN", "codex"),
            planner_mode=os.environ.get("WSA_MODE", "auto").strip().lower(),
            codex_model_fast=os.environ.get("CODEX_MODEL_FAST", os.environ.get("CODEX_MODEL", "")),
            codex_model_careful=os.environ.get(
                "CODEX_MODEL_CAREFUL",
                os.environ.get("CODEX_MODEL", ""),
            ),
            openai_model_fast=os.environ.get(
                "OPENAI_MODEL_FAST",
                os.environ.get("OPENAI_MODEL", "gpt-5.2"),
            ),
            openai_model_careful=os.environ.get(
                "OPENAI_MODEL_CAREFUL",
                os.environ.get("OPENAI_MODEL", "gpt-5.2"),
            ),
            ollama_base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
            .strip()
            .rstrip("/"),
            ollama_model_fast=os.environ.get(
                "OLLAMA_MODEL_FAST",
                os.environ.get("OLLAMA_MODEL", "qwen2.5vl:7b"),
            ).strip(),
            ollama_model_careful=os.environ.get(
                "OLLAMA_MODEL_CAREFUL",
                os.environ.get("OLLAMA_MODEL", "qwen2.5vl:7b"),
            ).strip(),
        )
    settings = load_settings(_settings_file(cfg.runtime_dir))
    if settings.planner_backend:
        cfg = replace(cfg, planner_backend=settings.planner_backend)
    return cfg


def _run_tray(runtime_dir: Path) -> int:
    from windows_screen_agent import hotkey
    from windows_screen_agent.tray import (
        create_tray_icon,
        read_answer_label,
        read_status_label,
        start_icon_refresher,
    )

    paths = runtime_paths(runtime_dir)
    icon_holder = {}
    listener_holder = {}
    icon_refresh_stop = {}
    active_run = {}
    active_answer = {}
    listener_stopped = False

    def run_worker(argv: list[str], failure_status: str) -> None:
        try:
            main(argv)
        except Exception as exc:
            message = str(exc).strip() or exc.__class__.__name__
            write_status(paths, f"{failure_status}: {message}")
            print(f"{failure_status}: {message}", flush=True)
            traceback.print_exc()

    def run_background():
        thread = active_run.get("thread")
        if thread and thread.is_alive():
            print("agent already running", flush=True)
            return
        _clear_stop(runtime_dir)
        write_status(paths, "starting")
        print("agent start requested", flush=True)
        thread = threading.Thread(target=lambda: run_worker(["run"], "failed"), daemon=True)
        active_run["thread"] = thread
        thread.start()

    def answer_background():
        thread = active_answer.get("thread")
        if thread and thread.is_alive():
            print("answer already running", flush=True)
            return
        write_status(paths, "answer: starting")
        print("answer start requested", flush=True)
        thread = threading.Thread(
            target=lambda: run_worker(["answer-once"], "answer failed"),
            daemon=True,
        )
        active_answer["thread"] = thread
        thread.start()

    def stop_run():
        print("agent stop requested", flush=True)
        write_status(paths, "stopping")
        _request_stop(runtime_dir)

    def stop_hotkey_listener():
        nonlocal listener_stopped
        if listener_stopped:
            return
        listener = listener_holder.get("listener")
        if listener is not None:
            listener.stop()
        listener_stopped = True

    def quit_tray():
        stop_run()
        stop_hotkey_listener()
        icon_holder["icon"].stop()

    def current_planner() -> str:
        return load_settings(_settings_file(runtime_dir)).planner_backend or os.environ.get(
            "WSA_PLANNER",
            "codex",
        ).strip().lower()

    def select_planner(planner: str) -> None:
        save_settings(_settings_file(runtime_dir), RuntimeSettings(planner_backend=planner))
        icon = icon_holder.get("icon")
        if icon is not None and hasattr(icon, "update_menu"):
            icon.update_menu()

    icon = create_tray_icon(
        on_run=run_background,
        on_stop=stop_run,
        on_quit=quit_tray,
        get_status_label=lambda: read_status_label(paths.status_file),
        get_answer_label=lambda: read_answer_label(paths.base_dir / "answer.txt"),
        get_current_planner=current_planner,
        on_select_planner=select_planner,
    )
    icon_holder["icon"] = icon
    icon_refresh_stop["event"] = start_icon_refresher(
        icon,
        paths.status_file,
        paths.base_dir / "answer_tokens.txt",
    )
    listener_holder["listener"] = hotkey.start_hotkey_listener(
        on_run=run_background,
        on_stop=stop_run,
        on_answer=answer_background,
    )
    print("tray running")
    try:
        icon.run()
    finally:
        stop_event = icon_refresh_stop.get("event")
        if stop_event is not None:
            stop_event.set()
        stop_hotkey_listener()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runtime_dir = _runtime_dir_without_api_key()

    if args.command in {
        "stop",
        "status",
        "doctor",
        "tray",
        "start-tray",
        "install-autostart",
        "uninstall-autostart",
    }:
        paths = runtime_paths(runtime_dir)
        if args.command == "stop":
            _request_stop(runtime_dir)
            print("stop requested")
            return 0
        if args.command == "doctor":
            cfg = _diagnostic_config()
            diagnostics = collect_diagnostics(
                runtime_dir=cfg.runtime_dir,
                planner_backend=cfg.planner_backend,
                codex_bin=cfg.codex_bin,
                openai_api_key=os.environ.get("OPENAI_API_KEY"),
                ollama_base_url=cfg.ollama_base_url,
                ollama_model=cfg.ollama_model_fast,
            )
            print(format_diagnostics(diagnostics))
            return 0
        if args.command == "tray":
            return _run_tray(runtime_dir)
        if args.command == "start-tray":
            pid = start_tray_background(runtime_dir=runtime_dir)
            print(f"tray started pid {pid}")
            return 0
        if args.command == "install-autostart":
            link_path = install_autostart(working_dir=Path.cwd())
            print(f"autostart installed: {link_path}")
            if not args.no_start:
                pid = start_tray_background(runtime_dir=runtime_dir)
                print(f"tray started pid {pid}")
            return 0
        if args.command == "uninstall-autostart":
            link_path = uninstall_autostart()
            print(f"autostart removed: {link_path}")
            return 0
        if paths.status_file.exists():
            print(paths.status_file.read_text(encoding="utf-8"))
        else:
            print("idle")
        return 0

    import pyautogui

    cfg = _load_config_with_runtime_settings(runtime_dir)
    paths = runtime_paths(cfg.runtime_dir)
    if paths.stop_file.exists():
        paths.stop_file.unlink()

    screen = PyAutoGuiScreen(paths.screens_dir, backend=pyautogui)
    planner = build_planner(cfg)
    executor = ActionExecutor(backend=pyautogui)

    if args.command == "run-once":
        cfg = replace(cfg, max_steps=1)
    if args.command == "answer-once":
        result = run_answer_once(
            config=cfg,
            screen=screen,
            planner=planner,
            note=args.note,
        )
        print(f"answer ready: {result.text}")
        return 0

    runner = Runner(config=cfg, screen=screen, planner=planner, executor=executor)
    result = runner.run(note=args.note)
    print(f"{result.reason} after {result.steps} steps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
