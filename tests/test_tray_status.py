from windows_screen_agent.tray import create_tray_icon, read_status_label


def test_read_status_label_defaults_to_idle_when_file_is_missing(tmp_path):
    assert read_status_label(tmp_path / "status.txt") == "Status: Idle"


def test_read_status_label_formats_working_steps(tmp_path):
    status_file = tmp_path / "status.txt"
    status_file.write_text("step 3: plan (fast)", encoding="utf-8")

    assert read_status_label(status_file) == "Status: Working - step 3: plan (fast)"


def test_read_status_label_formats_terminal_states(tmp_path):
    status_file = tmp_path / "status.txt"
    status_file.write_text("timeout", encoding="utf-8")

    assert read_status_label(status_file) == "Status: Timeout"


def test_tray_menu_starts_with_disabled_status_item():
    labels = iter(["Status: Running", "Status: Stopped"])
    icon = create_tray_icon(
        on_run=lambda: None,
        on_stop=lambda: None,
        on_quit=lambda: None,
        get_status_label=lambda: next(labels),
    )

    first_item = tuple(icon.menu)[0]

    assert first_item.text == "Status: Running"
    assert first_item.text == "Status: Stopped"
    assert first_item.enabled is False
