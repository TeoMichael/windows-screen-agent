from collections.abc import Callable
from pathlib import Path
from threading import Event, Thread

from PIL import Image, ImageDraw
import pystray


def _icon_image(label: str = "") -> Image.Image:
    image = Image.new("RGB", (64, 64), color=(35, 35, 35))
    draw = ImageDraw.Draw(image)
    if label:
        text = label[:3].upper()
        bbox = draw.textbbox((0, 0), text)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        draw.text(((64 - width) / 2, (64 - height) / 2 - 2), text, fill=(245, 245, 245))
    else:
        draw.rectangle((14, 18, 50, 44), outline=(230, 230, 230), width=3)
        draw.rectangle((26, 48, 38, 52), fill=(230, 230, 230))
    return image


STATUS_LABELS = {
    "starting": "Status: Starting",
    "stopping": "Status: Stopping...",
    "stopped": "Status: Stopped",
    "timeout": "Status: Timeout",
    "done": "Status: Done",
    "failed": "Status: Failed",
    "validation failed": "Status: Validation failed",
    "max steps reached": "Status: Max steps reached",
}


def read_status_label(status_file: Path) -> str:
    if not status_file.exists():
        return "Status: Idle"
    status = status_file.read_text(encoding="utf-8").strip()
    if not status:
        return "Status: Idle"
    if status.startswith("step "):
        return f"Status: Working - {status}"
    return STATUS_LABELS.get(status, f"Status: {status}")


def read_answer_label(answer_file: Path, max_chars: int = 60) -> str:
    if not answer_file.exists():
        return "Last answer: (none)"
    answer = answer_file.read_text(encoding="utf-8").strip()
    if not answer:
        return "Last answer: (none)"
    if len(answer) > max_chars:
        answer = answer[: max_chars - 3].rstrip() + "..."
    return f"Last answer: {answer}"


def cycle_answer_label(tokens: list[str], tick: int) -> str:
    if not tokens:
        return "A"
    return tokens[tick % len(tokens)]


def icon_label_for_status(status: str, answer_tokens: list[str], tick: int) -> str:
    normalized = status.strip().lower()
    if normalized == "answer ready":
        return cycle_answer_label(answer_tokens, tick)
    if normalized.startswith("answer: capture") or normalized.endswith(": capture"):
        return "EYE"
    if normalized.startswith("answer: plan") or ": plan" in normalized:
        return "THK"
    if any(action in normalized for action in (": click", ": type", ": scroll", ": hotkey")):
        return "ACT"
    if normalized in {"failed", "validation failed"} or normalized.startswith(
        ("failed:", "answer failed")
    ):
        return "!"
    if normalized == "timeout":
        return "TO"
    if normalized in {"stopped", "stopping"}:
        return "STP"
    return ""


def _read_status(status_file: Path) -> str:
    if not status_file.exists():
        return ""
    return status_file.read_text(encoding="utf-8").strip()


def _read_answer_tokens(tokens_file: Path) -> list[str]:
    if not tokens_file.exists():
        return []
    return [line.strip() for line in tokens_file.read_text(encoding="utf-8").splitlines() if line.strip()]


def start_icon_refresher(icon, status_file: Path, answer_tokens_file: Path, interval: float = 1.0):
    stop_event = Event()

    def refresh_loop():
        tick = 0
        previous_signature = None
        while not stop_event.is_set():
            status = _read_status(status_file)
            tokens = _read_answer_tokens(answer_tokens_file)
            label = icon_label_for_status(status, tokens, tick)
            signature = (status, tuple(tokens), label)
            icon.icon = _icon_image(label)
            if signature != previous_signature and hasattr(icon, "update_menu"):
                icon.update_menu()
                previous_signature = signature
            tick += 1
            stop_event.wait(interval)

    thread = Thread(target=refresh_loop, daemon=True)
    thread.start()
    return stop_event


def create_tray_icon(
    *,
    on_run: Callable[[], None],
    on_stop: Callable[[], None],
    on_quit: Callable[[], None],
    get_status_label: Callable[[], str] = lambda: "Status: Idle",
    get_answer_label: Callable[[], str] = lambda: "Last answer: (none)",
    get_current_planner: Callable[[], str] = lambda: "codex",
    on_select_planner: Callable[[str], None] = lambda planner: None,
) -> pystray.Icon:
    def select_planner(planner: str):
        return lambda icon, item: on_select_planner(planner)

    def checked(planner: str):
        return lambda item: get_current_planner() == planner

    return pystray.Icon(
        "windows-screen-agent",
        _icon_image(),
        "Windows Screen Agent",
        menu=pystray.Menu(
            pystray.MenuItem(lambda item: get_status_label(), lambda icon, item: None, enabled=False),
            pystray.MenuItem(lambda item: get_answer_label(), lambda icon, item: None, enabled=False),
            pystray.MenuItem(
                "Model",
                pystray.Menu(
                    pystray.MenuItem("Auto", select_planner("auto"), checked=checked("auto")),
                    pystray.MenuItem("Codex", select_planner("codex"), checked=checked("codex")),
                    pystray.MenuItem("OpenAI", select_planner("openai"), checked=checked("openai")),
                    pystray.MenuItem("Ollama", select_planner("ollama"), checked=checked("ollama")),
                ),
            ),
            pystray.MenuItem("Run", lambda icon, item: on_run()),
            pystray.MenuItem("Stop", lambda icon, item: on_stop()),
            pystray.MenuItem("Quit", lambda icon, item: on_quit()),
        ),
    )
