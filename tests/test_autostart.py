from pathlib import Path

from windows_screen_agent.autostart import (
    autostart_link_path,
    install_autostart,
    pythonw_executable,
    start_tray_background,
    uninstall_autostart,
)


def test_pythonw_executable_prefers_pythonw_next_to_python(tmp_path):
    scripts = tmp_path / "Scripts"
    scripts.mkdir()
    python = scripts / "python.exe"
    pythonw = scripts / "pythonw.exe"
    python.write_text("", encoding="utf-8")
    pythonw.write_text("", encoding="utf-8")

    assert pythonw_executable(python) == pythonw


def test_autostart_link_path_uses_startup_folder(tmp_path):
    assert autostart_link_path(tmp_path) == tmp_path / "Windows Screen Agent.lnk"


def test_install_autostart_creates_startup_shortcut_with_pythonw(tmp_path):
    calls = []
    pythonw = tmp_path / "pythonw.exe"

    def fake_runner(argv, *, check, capture_output, text):
        calls.append(argv)

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return Result()

    link = install_autostart(
        startup_dir=tmp_path,
        python_executable=pythonw,
        command_runner=fake_runner,
        working_dir=Path("C:/project"),
    )

    assert link == tmp_path / "Windows Screen Agent.lnk"
    script = calls[0][-1]
    assert "CreateShortcut" in script
    assert str(link) in script
    assert str(pythonw) in script
    assert "-m windows_screen_agent.app tray" in script


def test_uninstall_autostart_removes_shortcut(tmp_path):
    link = autostart_link_path(tmp_path)
    link.write_text("shortcut", encoding="utf-8")

    removed = uninstall_autostart(startup_dir=tmp_path)

    assert removed == link
    assert not link.exists()


def test_start_tray_background_uses_pythonw_and_returns_pid(tmp_path):
    calls = []
    pythonw = tmp_path / "pythonw.exe"

    class FakeProc:
        pid = 1234

    def fake_popen(argv, **kwargs):
        calls.append((argv, kwargs))
        return FakeProc()

    pid = start_tray_background(
        runtime_dir=tmp_path / "runtime",
        python_executable=pythonw,
        popen=fake_popen,
    )

    assert pid == 1234
    assert calls[0][0] == [str(pythonw), "-m", "windows_screen_agent.app", "tray"]
    assert calls[0][1]["stdin"] is not None
