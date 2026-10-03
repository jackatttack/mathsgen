"""Exercise Ivory UI state, shared browser, counts and footer on the main thread."""
import builtins
import json
import sys
import tempfile
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
PROGRESS = PROJECT_ROOT / "dev" / "smoke_ivory_ui_progress.txt"
PROGRESS.parent.mkdir(parents=True, exist_ok=True)


def step(message):
    with PROGRESS.open("a", encoding="utf-8") as stream:
        stream.write(message + "\n")
        stream.flush()
    print(message)


def main():
    for name in list(sys.modules):
        if name == "mathsgen" or name.startswith("mathsgen."):
            del sys.modules[name]
    from mathsgen.catalogue import build_registry
    from mathsgen.worksheet_ui import WorksheetBuilder
    from mathsgen.build_workspace import SkillBoard
    from mathsgen.build_model import maximum_count
    from mathsgen.drill import MAXIMUM_ITEMS_PER_STAGE

    step("01 construct maker")
    registry = build_registry()
    root = Path(tempfile.mkdtemp(prefix="mathsgen_ivory_ui_"))
    host = WorksheetBuilder(registry, root)
    if not hasattr(builtins, "_mathsgen_ui_smoke_views"):
        builtins._mathsgen_ui_smoke_views = []
    builtins._mathsgen_ui_smoke_views.append(host)
    host.frame = (0, 0, 390, 760)
    host.layout()

    def switch(index):
        host.mode_control.selected_index = index
        host.change_mode(host.mode_control)
        host.layout()

    step("02 Build footer and retained browser")
    switch(1)
    workspace = host.workspace
    workspace.layout()
    board = workspace.board
    board.layout()
    assert isinstance(board, SkillBoard)
    assert workspace.y + workspace.height <= host.footer.y + 1
    assert not host.generate_button.hidden
    board.toggle_fold(board.fold_button)
    assert board.rows
    row = board.rows[0]
    key = row.entry["generator_id"]
    board.row_tapped(row)
    assert row.added == 1
    assert host.generate_button.enabled
    assert "questions" in host.total_label.text
    board.fill_grid()
    assert next(r for r in board.rows if r.entry["generator_id"] == key) is row
    board.toggle_filters(board.filters_button)
    assert not board.topic_strip.hidden
    board.toggle_filters(board.filters_button)
    assert board.topic_strip.hidden

    step("03 block slider, typed counts and Actions")
    workspace.show_sheet(True)
    sheet = workspace.sheet
    sheet.layout()
    assert sheet.style_control.hidden and sheet.generate_button.hidden
    card = sheet.cards[0]
    sheet.toggle_card(card)
    assert card.up_button.hidden
    card.toggle_actions(card.actions_button)
    assert not card.up_button.hidden
    card.toggle_actions(card.actions_button)
    cards = list(sheet.cards)
    card.count_slider.value = 1
    card.slide_count(card.count_slider)
    assert card.block["count"] == maximum_count(card.block["kind"])
    card.count_value.text = "7"
    card.textfield_did_end_editing(card.count_value)
    assert card.block["count"] == 7
    card.count_value.text = "invalid"
    card.textfield_did_end_editing(card.count_value)
    assert card.count_value.text == "7"
    for _ in range(20):
        card.change_count(card.plus)
        card.change_count(card.minus)
    assert sheet.cards == cards and card.block["count"] == 7
    sheet.duplicate_card(card)
    assert sheet.cards[0] is card
    duplicate = sheet.cards[1]
    sheet.remove_card(duplicate)
    assert duplicate.hidden and duplicate.superview is sheet.scroll
    assert sheet.cards[0] is card
    sheet.toggle_settings(sheet.settings_button)
    assert not sheet.title_field.hidden
    sheet.title_field.text = "Ivory UI smoke"
    sheet.textfield_did_end_editing(sheet.title_field)
    assert host.title_field.text == "Ivory UI smoke"
    sheet.toggle_settings(sheet.settings_button)

    step("04 Drill shares browser and preserves independent selection")
    switch(3)
    drill = host.drill_browser
    assert type(drill) is type(board)
    assert not host.settings_open
    assert host.count_slider.hidden and host.count_field.hidden
    assert host.difficulty_label.hidden
    assert all(control.hidden for control in host.level_buttons)
    assert host.subtitle.hidden
    collapsed_browser_height = drill.height
    host.toggle_settings(host.settings_button)
    assert not host.count_slider.hidden and not host.count_field.hidden
    assert not host.difficulty_label.hidden
    assert drill.height < collapsed_browser_height
    host.toggle_settings(host.settings_button)
    assert drill.height == collapsed_browser_height
    drill.toggle_fold(drill.fold_button)
    assert drill.rows
    drill_row = drill.rows[0]
    drill.row_tapped(drill_row)
    drill_key = drill_row.entry["generator_id"]
    assert drill_key in host.drill_selected
    assert host.generate_button.enabled
    retained = list(drill.rows)
    host.count_slider.value = 1
    host.slide_count(host.count_slider)
    assert host.drill_count == MAXIMUM_ITEMS_PER_STAGE
    assert drill.rows == retained
    host.count_slider.value = 0
    host.slide_count(host.count_slider)
    assert host.drill_count == 1
    host.count_field.text = "8"
    host.textfield_did_end_editing(host.count_field)
    assert host.drill_count == 8
    for _ in range(10):
        drill.row_tapped(drill_row)
        drill.row_tapped(drill_row)
    assert drill_key in host.drill_selected
    host.toggle_settings(host.settings_button)
    assert not host.title_field.hidden and not host.apply_switch.hidden
    host.toggle_settings(host.settings_button)

    step("05 all modes and preview footer geometry")
    for size in ((320, 640), (390, 760), (768, 960)):
        host.frame = (0, 0, *size)
        for index in (0, 1, 2, 3):
            switch(index)
            assert not host.generate_button.hidden
            assert host.generate_button.width > 0
            assert host.footer.y + host.footer.height <= host.height + 1
            assert host.theme_control.hidden
            if index == 3:
                assert host.drill_browser.y + host.drill_browser.height <= host.footer.y + 1
    host.report = {"pdfs": [{"mode": "questions"}, {"mode": "answers"}],
                   "question_count": 8}
    host.status.text = "Preview ready."
    host.refresh()
    assert not host.open_questions.hidden and host.open_questions.enabled
    assert not host.open_answers.hidden and host.open_answers.enabled
    assert host.save_button.y + host.save_button.height <= host.footer.height
    host.busy = True
    host.refresh()
    assert not host.generate_button.enabled and not host.open_questions.enabled
    host.busy = False
    host.report = None
    host.status.text = ""
    host.refresh()

    step("06 save and restore")
    host.save()
    state = json.loads(host.state_path.read_text(encoding="utf-8"))
    assert state["theme"] == "ivory"
    assert state["drill_count"] == 8
    restored = WorksheetBuilder(registry, root)
    builtins._mathsgen_ui_smoke_views.append(restored)
    restored.frame = (0, 0, 390, 760)
    restored.layout()
    assert restored.drill_selected == host.drill_selected
    assert len(restored.build_blocks) == len(host.build_blocks)
    for before, after in zip(host.build_blocks, restored.build_blocks):
        for key in ("generator_id", "kind", "levels", "count"):
            assert after[key] == before[key], "Restored setting changed: " + key
        assert after["title"] == registry.get(after["generator_id"]).info.title
        if before["kind"] == "drill":
            assert after["apply"] == before.get("apply", True)
        else:
            assert after["apply"] is False
    assert restored.title_field.text == "Ivory UI smoke"
    step("PASS: shared browser, retained views, counts, four modes, footer and restore")
    step("Device appearance and rapid-touch acceptance remain pending.")


def run():
    from objc_util import on_main_thread
    PROGRESS.write_text("", encoding="utf-8")
    result = []

    @on_main_thread
    def execute():
        try:
            main()
        except Exception:
            step(traceback.format_exc())
            result.append(1)
        else:
            result.append(0)

    execute()
    return result[0] if result else 1


if __name__ == "__main__":
    sys.exit(run())