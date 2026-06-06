from pathlib import Path
import subprocess
import sys

from windows_screen_agent.logs import runtime_paths


SHORTCUT_NAME = "Windows Screen Agent.lnk"


def default_startup_dir() -> Path:
    return (
        Path.home()
        / "AppData"
        / "Roaming"
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "Startup"
    )


def autostart_link_path(startup_dir: Path | None = None) -> Path:
    return (startup_dir or default_startup_dir()) / SHORTCUT_NAME


def pythonw_executable(python_executable: str | Path | None = None) -> Path:
    python_path = Path(python_executable or sys.executable)
    candidate = python_path.with_name("pythonw.exe")
    return candidate if candidate.exists() else python_path


def _ps_single_quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def install_autostart(
    *,
    startup_dir: Path | None = None,
    python_executable: str | Path | None = None,
    working_dir: Path | None = None,
    command_runner=subprocess.run,
) -> Path:
    link_path = autostart_link_path(startup_dir)
    link_path.parent.mkdir(parents=True, exist_ok=True)
    target = pythonw_executable(python_executable)
    shortcut_args = "-m windows_screen_agent.app tray"
    cwd = Path(working_dir or Path.cwd())
    script = "\n".join(
        [
            "$shell = New-Object -ComObject WScript.Shell",
            f"$shortcut = $shell.CreateShortcut({_ps_single_quote(str(link_path))})",
            f"$shortcut.TargetPath = {_ps_single_quote(str(target))}",
            f"$shortcut.Arguments = {_ps_single_quote(shortcut_args)}",
            f"$shortcut.WorkingDirectory = {_ps_single_quote(str(cwd))}",
            "$shortcut.WindowStyle = 7",
            "$shortcut.Description = 'Windows Screen Agent tray'",
            "$shortcut.Save()",
        ]
    )
    command_runner(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return link_path


def uninstall_autostart(*, startup_dir: Path | None = None) -> Path:
    link_path = autostart_link_path(startup_dir)
    if link_path.exists():
        link_path.unlink()
    return link_path


def start_tray_background(
    *,
    runtime_dir: Path,
    python_executable: str | Path | None = None,
    popen=subprocess.Popen,
) -> int:
    paths = runtime_paths(runtime_dir)
    log_path = paths.logs_dir / "tray.log"
    target = pythonw_executable(python_executable)
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    with log_path.open("ab") as log_handle:
        proc = popen(
            [str(target), "-m", "windows_screen_agent.app", "tray"],
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            cwd=str(Path.cwd()),
            creationflags=creationflags,
        )
    return int(proc.pid)
