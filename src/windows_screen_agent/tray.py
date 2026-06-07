from collections.abc import Callable
from pathlib import Path

from PIL import Image, ImageDraw
import pystray


def _icon_image() -> Image.Image:
    image = Image.new("RGB", (64, 64), color=(35, 35, 35))
    draw = ImageDraw.Draw(image)
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


def create_tray_icon(
    *,
    on_run: Callable[[], None],
    on_stop: Callable[[], None],
    on_quit: Callable[[], None],
    get_status_label: Callable[[], str] = lambda: "Status: Idle",
) -> pystray.Icon:
    return pystray.Icon(
        "windows-screen-agent",
        _icon_image(),
        "Windows Screen Agent",
        menu=pystray.Menu(
            pystray.MenuItem(lambda item: get_status_label(), lambda icon, item: None, enabled=False),
            pystray.MenuItem("Run", lambda icon, item: on_run()),
            pystray.MenuItem("Stop", lambda icon, item: on_stop()),
            pystray.MenuItem("Quit", lambda icon, item: on_quit()),
        ),
    )
