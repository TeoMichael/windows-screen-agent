from windows_screen_agent.tray import (
    cycle_answer_label,
    create_tray_icon,
    icon_label_for_status,
    read_status_label,
)


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


def test_tray_menu_has_model_submenu_and_selection_callback():
    selected = []
    icon = create_tray_icon(
        on_run=lambda: None,
        on_stop=lambda: None,
        on_quit=lambda: None,
        get_status_label=lambda: "Status: Idle",
        get_current_planner=lambda: "codex",
        on_select_planner=selected.append,
    )

    items = tuple(icon.menu)
    model_item = next(item for item in items if item.text == "Model")
    model_options = tuple(model_item.submenu)

    assert [item.text for item in model_options] == ["Auto", "Codex", "OpenAI", "Ollama"]

    model_options[-1](None)

    assert selected == ["ollama"]


def test_tray_menu_shows_last_answer_without_copy_command():
    icon = create_tray_icon(
        on_run=lambda: None,
        on_stop=lambda: None,
        on_quit=lambda: None,
        get_status_label=lambda: "Status: Idle",
        get_answer_label=lambda: "Last answer: 1A 2B",
    )

    items = tuple(icon.menu)

    assert items[1].text == "Last answer: 1A 2B"
    assert items[1].enabled is False
    assert "Copy Last Answer" not in [item.text for item in items]


def test_cycle_answer_label_repeats_short_tokens():
    assert cycle_answer_label(["1A", "2B", "3C"], 0) == "1A"
    assert cycle_answer_label(["1A", "2B", "3C"], 1) == "2B"
    assert cycle_answer_label(["1A", "2B", "3C"], 3) == "1A"
    assert cycle_answer_label([], 0) == "A"


def test_icon_label_for_status_maps_runtime_states():
    assert icon_label_for_status("answer ready", ["1A", "2B"], 1) == "2B"
    assert icon_label_for_status("answer: capture", [], 0) == "EYE"
    assert icon_label_for_status("answer: plan (fast)", [], 0) == "THK"
    assert icon_label_for_status("step 1: click", [], 0) == "ACT"
    assert icon_label_for_status("failed", [], 0) == "!"
