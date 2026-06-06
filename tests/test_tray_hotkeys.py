from windows_screen_agent.app import _run_tray
from windows_screen_agent.logs import runtime_paths


class FakeListener:
    def __init__(self, calls):
        self.calls = calls

    def stop(self):
        self.calls.append("listener.stop")


class FakeIcon:
    def __init__(self, calls, callbacks):
        self.calls = calls
        self.callbacks = callbacks

    def run(self):
        self.calls.append("icon.run")
        self.callbacks["on_stop"]()
        self.callbacks["on_quit"]()

    def stop(self):
        self.calls.append("icon.stop")


def test_tray_registers_global_hotkeys_and_stops_listener_on_quit(monkeypatch, tmp_path):
    calls = []
    callbacks = {}

    def fake_create_tray_icon(*, on_run, on_stop, on_quit):
        callbacks["on_run"] = on_run
        callbacks["on_stop"] = on_stop
        callbacks["on_quit"] = on_quit
        return FakeIcon(calls, callbacks)

    def fake_start_hotkey_listener(*, on_run, on_stop):
        callbacks["hotkey_on_run"] = on_run
        callbacks["hotkey_on_stop"] = on_stop
        return FakeListener(calls)

    monkeypatch.setattr("windows_screen_agent.tray.create_tray_icon", fake_create_tray_icon)
    monkeypatch.setattr("windows_screen_agent.hotkey.start_hotkey_listener", fake_start_hotkey_listener)

    assert _run_tray(tmp_path) == 0

    assert callbacks["hotkey_on_run"] is callbacks["on_run"]
    assert callbacks["hotkey_on_stop"] is callbacks["on_stop"]
    assert runtime_paths(tmp_path).stop_file.exists()
    assert calls == ["icon.run", "listener.stop", "icon.stop"]
