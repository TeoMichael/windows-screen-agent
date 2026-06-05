from collections.abc import Callable

from pynput import keyboard


DEFAULT_HOTKEY = "<ctrl>+<alt>+<shift>+s"


def start_hotkey_listener(on_toggle: Callable[[], None], hotkey: str = DEFAULT_HOTKEY):
    listener = keyboard.GlobalHotKeys({hotkey: on_toggle})
    listener.start()
    return listener
