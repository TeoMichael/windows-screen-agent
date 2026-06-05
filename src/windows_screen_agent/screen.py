from dataclasses import dataclass
import base64
from io import BytesIO
from pathlib import Path
import time
from typing import Any


@dataclass(frozen=True)
class ScreenSnapshot:
    path: Path
    width: int
    height: int
    data_url: str


def capture_screen(screens_dir: Path, backend: Any) -> ScreenSnapshot:
    screens_dir.mkdir(parents=True, exist_ok=True)
    image = backend.screenshot()
    path = screens_dir / f"screen-{int(time.time() * 1000)}.png"
    image.save(path, format="PNG")

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

    return ScreenSnapshot(
        path=path,
        width=image.width,
        height=image.height,
        data_url=f"data:image/png;base64,{encoded}",
    )
