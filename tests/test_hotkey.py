from windows_screen_agent.hotkey import (
    DEFAULT_ANSWER_HOTKEY,
    DEFAULT_RUN_HOTKEY,
    DEFAULT_STOP_HOTKEY,
    start_hotkey_listener,
)


class FakeGlobalHotKeys:
    def __init__(self, bindings):
        self.bindings = bindings
        self.started = False

    def start(self):
        self.started = True


def test_start_hotkey_listener_registers_run_and_stop_callbacks():
    events = []

    listener = start_hotkey_listener(
        on_run=lambda: events.append("run"),
        on_stop=lambda: events.append("stop"),
        on_answer=lambda: events.append("answer"),
        listener_factory=FakeGlobalHotKeys,
    )

    assert listener.started is True
    assert set(listener.bindings) == {
        DEFAULT_RUN_HOTKEY,
        DEFAULT_STOP_HOTKEY,
        DEFAULT_ANSWER_HOTKEY,
    }

    listener.bindings[DEFAULT_RUN_HOTKEY]()
    listener.bindings[DEFAULT_STOP_HOTKEY]()
    listener.bindings[DEFAULT_ANSWER_HOTKEY]()

    assert events == ["run", "stop", "answer"]


def test_answer_hotkey_defaults_to_ctrl_alt_backslash():
    assert DEFAULT_ANSWER_HOTKEY == "<ctrl>+<alt>+\\"
