"""Smoke: the stable Build workspace, driven without presenting it.

Board: folded topics, Expand all, row toggling and header counts, topic and
grade chips, search. Switch: the sheet rebuilds only when shown after a
change. Sheet: cards open and close, 50 rapid + taps on one card (count
caps, nothing rebuilt), drill switch, Up / Down / To top, duplicate and
remove, title, settings, Generate and preview actions. The action log
records taps. The returned blocks build a real sheet.

Runs on the main thread (UIKit requires it), keeps its views alive after
finishing, and writes each step to a progress file so that a hard crash
names its step.
"""
import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_PROGRESS_DIR = PROJECT_ROOT / "dev"
if not _PROGRESS_DIR.is_dir():   # the public release has no dev/ folder
    _PROGRESS_DIR = Path(tempfile.gettempdir())
PROGRESS = _PROGRESS_DIR / "smoke_build_workspace_progress.txt"
LOG = Path(tempfile.gettempdir()) / "smoke_build_actions.log"
failures = []
KEEP_ALIVE = []


def step(name):
    with open(str(PROGRESS), "a", encoding="utf-8") as output:
        output.write(name + "\n")
        output.flush()
        os.fsync(output.fileno())


def check(condition, message):
    if not condition:
        failures.append(message)


class FakeTouch:
    def __init__(self, x, y):
        self.location = (x, y)
        self.prev_location = (x, y)
        self.touch_id = 1
        self.phase = "ended"
        self.timestamp = 0


def tap(view, x=5, y=5):
    began = getattr(view, "touch_began", None)
    if began is not None:
        began(FakeTouch(x, y))
    view.touch_ended(FakeTouch(x, y))


def row_for(board, generator_id):
    return next(r for r in board.rows if r.entry["generator_id"] == generator_id)


def main():
    PROGRESS.write_text("", encoding="utf-8")
    step("01 import")
    from launch_mathsgen import load_engine
    from mathsgen.blocks import build_block_sheet
    from mathsgen.build_model import maximum_count
    from mathsgen.build_workspace import CARD_ROW, Workspace
    registry = load_engine()
    if LOG.exists():
        LOG.unlink()

    step("02 construct and lay out")
    received, settings, generated, actions = [], [], [], []
    workspace = Workspace(
        registry, [], "Starter",
        lambda blocks, title: received.append((blocks, title)),
        on_settings=lambda answers, theme: settings.append((answers, theme)),
        on_generate=lambda: generated.append(True),
        on_action=actions.append, log_path=LOG)
    KEEP_ALIVE.append(workspace)
    workspace.frame = (0, 0, 390, 760)
    workspace.layout()
    workspace.board.layout()
    workspace.sheet.layout()
    board, sheet = workspace.board, workspace.sheet
    check(not workspace.showing_sheet and sheet.hidden, "empty sheet: Skills shows first")
    check(not board.rows and len(board.headers) == len(workspace.topics), "board starts folded")

    step("03 expand all and add skills")
    board.toggle_fold(board.fold_button)
    check(len(board.rows) == len(workspace.infos), "Expand all shows every skill")
    drills = workspace.drill_levels
    drill_row = next(r for r in board.rows if r.entry["generator_id"] in drills)
    plain = [r for r in board.rows if r.entry["generator_id"] not in drills][:3]
    for row in plain + [drill_row]:
        tap(row)
    check(len(workspace.blocks) == 4, "four row taps add four blocks")
    check(workspace.switch.segments[1] == "Sheet (4)", "switch shows the block count")
    check(workspace.sheet_dirty and not sheet.cards, "sheet waits until it is shown")
    first_id = plain[0].entry["generator_id"]
    tap(row_for(board, first_id))
    check(len(workspace.blocks) == 3 and row_for(board, first_id).added == 0,
          "tapping a green row removes the skill")
    tap(row_for(board, first_id))

    step("03b twenty rapid taps, saving to disk on each")
    import json
    saved = []
    store = Path(tempfile.gettempdir()) / "smoke_build_state.json"

    def saving_host(blocks, title):
        store.write_text(json.dumps({"blocks": blocks, "title": title}), encoding="utf-8")
        saved.append(len(blocks))

    real_host = workspace.on_change
    workspace.on_change = saving_host
    before = len(workspace.blocks)
    rapid = [r for r in board.rows if r.entry["generator_id"] not in workspace.counts()][:10]
    for row in rapid + rapid:
        tap(row)
    check(len(workspace.blocks) == before, "ten skills on then off should net to no change")
    check(len(saved) == 20, "every tap should save exactly once")
    workspace.on_change = real_host

    step("04 show the sheet")
    workspace.switch.selected_index = 1
    workspace.switch_view(workspace.switch)
    check(workspace.showing_sheet and board.hidden and not sheet.hidden, "sheet shows")
    check(len(sheet.cards) == 4 and not workspace.sheet_dirty, "sheet built its cards")

    step("05 open cards")
    plain_card = next(c for c in sheet.cards if not c.has_drill)
    closed = plain_card.height_needed()
    tap(plain_card, 60, 20)
    check(plain_card.opened, "tap opens a card")
    check(plain_card.height_needed() == closed + 4 * CARD_ROW + 8,
          "card without drill: count, levels, move, buttons")

    step("06 fifty rapid plus taps")
    cards_before = list(sheet.cards)
    for _ in range(50):
        plain_card.change_count(plain_card.plus)
    check(plain_card.block["count"] == maximum_count("questions"), "count caps at the maximum")
    check(sheet.cards == cards_before, "plus taps must not rebuild the cards")
    check(plain_card.count_value.text == str(plain_card.block["count"]), "count label updates")
    for _ in range(60):
        plain_card.change_count(plain_card.minus)
    check(plain_card.block["count"] == 1, "count floors at 1")
    tap(plain_card, 60, 20)

    step("07 drill switch")
    drill_card = next(c for c in sheet.cards if c.has_drill)
    tap(drill_card, 60, 20)
    drill_card.drill_switch.value = True
    drill_card.change_drill(drill_card.drill_switch)
    check(drill_card.block["kind"] == "drill", "drill switch makes a drill block")
    check(set(drill_card.block["levels"]) <= set(drills[drill_card.info.id]), "drill levels limited")

    step("08 move up, down, to top")
    last = sheet.cards[-1]
    sheet.move_card(last, "top")
    check(workspace.blocks[0] is last.block and sheet.cards[0] is last, "To top moves first")
    sheet.move_card(last, "up")
    check(sheet.cards[0] is last, "Up at the top does nothing")
    sheet.move_card(last, "down")
    check(sheet.cards[1] is last and workspace.blocks[1] is last.block, "Down moves one place")
    check([c.number for c in sheet.cards] == [1, 2, 3, 4], "cards renumber")

    step("09 duplicate and remove")
    sheet.duplicate_card(sheet.cards[0])
    check(len(workspace.blocks) == 5 and len(sheet.cards) == 5, "duplicate adds a card")
    sheet.remove_card(sheet.cards[0])
    check(len(workspace.blocks) == 4, "remove deletes a card")

    step("10 back to skills: filters")
    workspace.switch.selected_index = 0
    workspace.switch_view(workspace.switch)
    algebra = next(chip for chip in board.topic_chips if chip.name == "algebra")
    board.pick_topic(algebra)
    board.toggle_fold(board.fold_button)
    board.toggle_fold(board.fold_button)
    check(board.rows and all(workspace.infos[r.entry["generator_id"]].topic == "algebra"
                             for r in board.rows), "Algebra chip shows Algebra only")
    board.pick_topic(board.topic_chips[0])
    board.pick_grades(next(chip for chip in board.grade_chips if chip.name == "Grades 8-9"))
    check(board.rows and all(max(r.entry["grades"]) >= 8 for r in board.rows), "grade chip filters")
    board.pick_grades(board.grade_chips[0])
    board.search.text = "fractions"
    board.textfield_did_change(board.search)
    check(board.rows and board.placeholder.hidden, "search unfolds matches")

    step("11 header tools")
    workspace.show_sheet(True)
    sheet.title_field.text = "Y9 starter"
    sheet.textfield_did_end_editing(sheet.title_field)
    check(received[-1][1] == "Y9 starter", "host hears the title")
    sheet.answers_switch.value = False
    sheet.style_control.selected_index = 1
    sheet.change_settings(sheet.answers_switch)
    check(settings and settings[-1] == (False, 1), "host hears the settings")
    sheet.generate(None)
    check(generated, "Generate reaches the host")
    workspace.sync_results({"busy": False, "status": "Preview ready.",
                            "ready": True, "answers": False, "saved": False})
    sheet.run_action(sheet.open_button)
    check(actions == ["open_questions"], "Open reaches the host")

    step("12 action log and build")
    logged = LOG.read_text(encoding="utf-8").splitlines() if LOG.exists() else []
    check(logged and any("count" in line for line in logged), "action log records taps")
    check(len(logged) <= 50, "action log keeps at most 50 lines")
    blocks, title = received[-1]
    built = build_block_sheet(registry, blocks, title, seed=4)
    print("Built questions:", len(built.questions), "| log lines:", len(logged))

    step("13 finished")
    for failure in failures:
        print("FAIL", failure)
        step("FAIL " + failure)
    result = "FAIL" if failures else "PASS"
    step("RESULT: " + result)
    print("RESULT:", result)
    return 1 if failures else 0


def main_on_ui_thread():
    """UIKit views must only be touched on the main thread; run there."""
    from objc_util import on_main_thread
    result = []
    on_main_thread(lambda: result.append(main()))()
    return result[0] if result else 1


if __name__ == "__main__":
    sys.exit(main_on_ui_thread())