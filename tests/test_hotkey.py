from windows_screen_agent.hotkey import DEFAULT_RUN_HOTKEY, DEFAULT_STOP_HOTKEY, start_hotkey_listener


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
        listener_factory=FakeGlobalHotKeys,
    )

    assert listener.started is True
    assert set(listener.bindings) == {DEFAULT_RUN_HOTKEY, DEFAULT_STOP_HOTKEY}

    listener.bindings[DEFAULT_RUN_HOTKEY]()
    listener.bindings[DEFAULT_STOP_HOTKEY]()

    assert events == ["run", "stop"]
