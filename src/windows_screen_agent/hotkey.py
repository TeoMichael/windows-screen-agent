from collections.abc import Callable

from pynput import keyboard


DEFAULT_RUN_HOTKEY = "<ctrl>+<alt>+<enter>"
DEFAULT_STOP_HOTKEY = "<ctrl>+<alt>+<backspace>"
DEFAULT_ANSWER_HOTKEY = "<ctrl>+<shift>+\\"


def start_hotkey_listener(
    *,
    on_run: Callable[[], None],
    on_stop: Callable[[], None],
    on_answer: Callable[[], None] | None = None,
    run_hotkey: str = DEFAULT_RUN_HOTKEY,
    stop_hotkey: str = DEFAULT_STOP_HOTKEY,
    answer_hotkey: str = DEFAULT_ANSWER_HOTKEY,
    listener_factory=keyboard.GlobalHotKeys,
):
    bindings = {
        run_hotkey: on_run,
        stop_hotkey: on_stop,
    }
    if on_answer is not None:
        bindings[answer_hotkey] = on_answer
    listener = listener_factory(bindings)
    listener.start()
    return listener
