from collections.abc import Callable

from pynput import keyboard


DEFAULT_RUN_HOTKEY = "<ctrl>+<alt>+<enter>"
DEFAULT_STOP_HOTKEY = "<ctrl>+<alt>+<backspace>"


def start_hotkey_listener(
    *,
    on_run: Callable[[], None],
    on_stop: Callable[[], None],
    run_hotkey: str = DEFAULT_RUN_HOTKEY,
    stop_hotkey: str = DEFAULT_STOP_HOTKEY,
    listener_factory=keyboard.GlobalHotKeys,
):
    listener = listener_factory(
        {
            run_hotkey: on_run,
            stop_hotkey: on_stop,
        }
    )
    listener.start()
    return listener
