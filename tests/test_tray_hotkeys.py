from windows_screen_agent.app import _run_tray
from windows_screen_agent.logs import runtime_paths
from windows_screen_agent.settings import load_settings


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


class FakeStopEvent:
    def set(self):
        pass


def test_tray_registers_global_hotkeys_and_stops_listener_on_quit(monkeypatch, tmp_path):
    calls = []
    callbacks = {}

    def fake_create_tray_icon(
        *,
        on_run,
        on_stop,
        on_quit,
        get_status_label,
        get_answer_label,
        get_current_planner,
        on_select_planner,
    ):
        callbacks["on_run"] = on_run
        callbacks["on_stop"] = on_stop
        callbacks["on_quit"] = on_quit
        callbacks["get_status_label"] = get_status_label
        callbacks["get_answer_label"] = get_answer_label
        callbacks["get_current_planner"] = get_current_planner
        callbacks["on_select_planner"] = on_select_planner
        return FakeIcon(calls, callbacks)

    def fake_start_hotkey_listener(*, on_run, on_stop, on_answer):
        callbacks["hotkey_on_run"] = on_run
        callbacks["hotkey_on_stop"] = on_stop
        callbacks["hotkey_on_answer"] = on_answer
        return FakeListener(calls)

    monkeypatch.setattr("windows_screen_agent.tray.create_tray_icon", fake_create_tray_icon)
    monkeypatch.setattr("windows_screen_agent.hotkey.start_hotkey_listener", fake_start_hotkey_listener)

    assert _run_tray(tmp_path) == 0

    assert callbacks["hotkey_on_run"] is callbacks["on_run"]
    assert callbacks["hotkey_on_stop"] is callbacks["on_stop"]
    assert callbacks["hotkey_on_answer"] is not None
    assert runtime_paths(tmp_path).stop_file.exists()
    assert runtime_paths(tmp_path).status_file.read_text(encoding="utf-8") == "stopping"
    assert calls == ["icon.run", "listener.stop", "icon.stop"]


def test_tray_hotkey_start_clears_stale_stop_and_prints_feedback(
    monkeypatch, tmp_path, capsys
):
    calls = []
    callbacks = {}
    paths = runtime_paths(tmp_path)
    paths.stop_file.write_text("stop", encoding="utf-8")

    class FakeThread:
        def __init__(self, *, target, daemon):
            self.target = target
            self.daemon = daemon
            self.alive = False

        def start(self):
            self.alive = True
            self.target()
            self.alive = False

        def is_alive(self):
            return self.alive

    def fake_create_tray_icon(
        *,
        on_run,
        on_stop,
        on_quit,
        get_status_label,
        get_answer_label,
        get_current_planner,
        on_select_planner,
    ):
        callbacks["on_run"] = on_run
        callbacks["on_stop"] = on_stop
        callbacks["on_quit"] = on_quit
        callbacks["get_status_label"] = get_status_label
        callbacks["get_answer_label"] = get_answer_label
        callbacks["get_current_planner"] = get_current_planner
        callbacks["on_select_planner"] = on_select_planner
        return FakeIcon(calls, callbacks)

    def fake_start_hotkey_listener(*, on_run, on_stop, on_answer):
        callbacks["hotkey_on_run"] = on_run
        callbacks["hotkey_on_stop"] = on_stop
        callbacks["hotkey_on_answer"] = on_answer
        return FakeListener(calls)

    def fake_main(argv):
        assert argv == ["run"]
        assert not paths.stop_file.exists()
        assert paths.status_file.read_text(encoding="utf-8") == "starting"
        calls.append("main.run")
        return 0

    def fake_icon_run(self):
        callbacks["hotkey_on_run"]()

    monkeypatch.setattr(FakeIcon, "run", fake_icon_run)
    monkeypatch.setattr(
        "windows_screen_agent.tray.start_icon_refresher",
        lambda *args, **kwargs: FakeStopEvent(),
    )
    monkeypatch.setattr("windows_screen_agent.app.threading.Thread", FakeThread)
    monkeypatch.setattr("windows_screen_agent.app.main", fake_main)
    monkeypatch.setattr("windows_screen_agent.tray.create_tray_icon", fake_create_tray_icon)
    monkeypatch.setattr("windows_screen_agent.hotkey.start_hotkey_listener", fake_start_hotkey_listener)

    assert _run_tray(tmp_path) == 0

    output = capsys.readouterr().out
    assert "agent start requested" in output
    assert calls == ["main.run", "listener.stop"]


def test_tray_answer_hotkey_runs_answer_once(monkeypatch, tmp_path, capsys):
    calls = []
    callbacks = {}

    class FakeThread:
        def __init__(self, *, target, daemon):
            self.target = target
            self.daemon = daemon
            self.alive = False

        def start(self):
            self.alive = True
            self.target()
            self.alive = False

        def is_alive(self):
            return self.alive

    def fake_create_tray_icon(
        *,
        on_run,
        on_stop,
        on_quit,
        get_status_label,
        get_answer_label,
        get_current_planner,
        on_select_planner,
    ):
        callbacks["on_answer"] = None
        return FakeIcon(calls, callbacks)

    def fake_start_hotkey_listener(*, on_run, on_stop, on_answer):
        callbacks["hotkey_on_answer"] = on_answer
        return FakeListener(calls)

    def fake_main(argv):
        assert argv == ["answer-once"]
        calls.append("main.answer")
        return 0

    def fake_icon_run(self):
        callbacks["hotkey_on_answer"]()

    monkeypatch.setattr(FakeIcon, "run", fake_icon_run)
    monkeypatch.setattr(
        "windows_screen_agent.tray.start_icon_refresher",
        lambda *args, **kwargs: FakeStopEvent(),
    )
    monkeypatch.setattr("windows_screen_agent.app.threading.Thread", FakeThread)
    monkeypatch.setattr("windows_screen_agent.app.main", fake_main)
    monkeypatch.setattr("windows_screen_agent.tray.create_tray_icon", fake_create_tray_icon)
    monkeypatch.setattr("windows_screen_agent.hotkey.start_hotkey_listener", fake_start_hotkey_listener)

    assert _run_tray(tmp_path) == 0

    output = capsys.readouterr().out
    assert "answer start requested" in output
    assert calls == ["main.answer", "listener.stop"]


def test_tray_model_selection_persists_runtime_setting(monkeypatch, tmp_path):
    calls = []
    callbacks = {}

    def fake_create_tray_icon(
        *,
        on_run,
        on_stop,
        on_quit,
        get_status_label,
        get_answer_label,
        get_current_planner,
        on_select_planner,
    ):
        callbacks["on_select_planner"] = on_select_planner
        callbacks["get_current_planner"] = get_current_planner
        return FakeIcon(calls, callbacks)

    def fake_start_hotkey_listener(*, on_run, on_stop, on_answer):
        return FakeListener(calls)

    def fake_icon_run(self):
        callbacks["on_select_planner"]("ollama")
        calls.append(callbacks["get_current_planner"]())

    monkeypatch.setattr(FakeIcon, "run", fake_icon_run)
    monkeypatch.setattr("windows_screen_agent.tray.create_tray_icon", fake_create_tray_icon)
    monkeypatch.setattr("windows_screen_agent.hotkey.start_hotkey_listener", fake_start_hotkey_listener)

    assert _run_tray(tmp_path) == 0

    assert load_settings(tmp_path / "settings.json").planner_backend == "ollama"
    assert calls == ["ollama", "listener.stop"]


def test_tray_status_label_reads_runtime_status(monkeypatch, tmp_path):
    calls = []
    callbacks = {}
    paths = runtime_paths(tmp_path)
    paths.status_file.write_text("stopped", encoding="utf-8")

    def fake_create_tray_icon(
        *,
        on_run,
        on_stop,
        on_quit,
        get_status_label,
        get_answer_label,
        get_current_planner,
        on_select_planner,
    ):
        callbacks["get_status_label"] = get_status_label
        return FakeIcon(calls, callbacks)

    def fake_start_hotkey_listener(*, on_run, on_stop, on_answer):
        return FakeListener(calls)

    def fake_icon_run(self):
        calls.append(callbacks["get_status_label"]())

    monkeypatch.setattr(FakeIcon, "run", fake_icon_run)
    monkeypatch.setattr("windows_screen_agent.tray.create_tray_icon", fake_create_tray_icon)
    monkeypatch.setattr("windows_screen_agent.hotkey.start_hotkey_listener", fake_start_hotkey_listener)

    assert _run_tray(tmp_path) == 0

    assert calls == ["Status: Stopped", "listener.stop"]
