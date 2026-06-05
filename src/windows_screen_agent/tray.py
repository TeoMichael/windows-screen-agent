from collections.abc import Callable

from PIL import Image, ImageDraw
import pystray


def _icon_image() -> Image.Image:
    image = Image.new("RGB", (64, 64), color=(35, 35, 35))
    draw = ImageDraw.Draw(image)
    draw.rectangle((14, 18, 50, 44), outline=(230, 230, 230), width=3)
    draw.rectangle((26, 48, 38, 52), fill=(230, 230, 230))
    return image


def create_tray_icon(
    *,
    on_run: Callable[[], None],
    on_stop: Callable[[], None],
    on_quit: Callable[[], None],
) -> pystray.Icon:
    return pystray.Icon(
        "windows-screen-agent",
        _icon_image(),
        "Windows Screen Agent",
        menu=pystray.Menu(
            pystray.MenuItem("Run", lambda icon, item: on_run()),
            pystray.MenuItem("Stop", lambda icon, item: on_stop()),
            pystray.MenuItem("Quit", lambda icon, item: on_quit()),
        ),
    )
