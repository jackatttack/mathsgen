"""Smoke: drive the Build workspace without presenting it.

Board: starts folded to topic headers; Expand all shows every skill; topic
and group headers fold; topic chips, grade chips and search filter (and
unfold); rows fit their full titles; tapping a row toggles the skill and
headers count what is on the sheet. Sheet: cards open and close, collapse
the drill row when there is none, switch to drill, change count, move by
press-and-hold and by grip; title, settings, Generate and preview actions
reach the host.

Each step is written to dev/smoke_build_workspace_progress.txt (flushed to
disk) before it runs, so if Pythonista itself crashes, the last line names
the step that crashed it.
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_PROGRESS_DIR = PROJECT_ROOT / "dev"
if not _PROGRESS_DIR.is_dir():   # the public release has no dev/ folder
    import tempfile
    _PROGRESS_DIR = Path(tempfile.gettempdir())
PROGRESS = _PROGRESS_DIR / "smoke_build_workspace_progress.txt"
failures = []
# Views built by the test stay referenced after it finishes, so they are not
# torn down while Forge is still wrapping up the run.
KEEP_ALIVE = []


def step(name):
    """Record the step about to run, surviving a hard crash."""
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
        self.phase = "moved"
        self.timestamp = 0


def tap(view, x=5, y=5):
    view.touch_began(FakeTouch(x, y))
    view.touch_ended(FakeTouch(x, y))


def row_for(board, generator_id):
    return next(r for r in board.rows if r.entry["generator_id"] == generator_id)


def main():
    PROGRESS.write_text("", encoding="utf-8")
    step("01 import engine and workspace")
    from launch_mathsgen import load_engine
    from mathsgen.blocks import build_block_sheet
    from mathsgen.build_workspace import CARD_ROW, ROW_TITLE_SIZE, Workspace, text_height
    registry = load_engine()

    step("02 construct workspace")
    received, settings, generated, actions = [], [], [], []
    workspace = Workspace(
        registry, [], "Starter",
        lambda blocks, title: received.append((blocks, title)),
        on_settings=lambda answers, theme: settings.append((answers, theme)),
        on_generate=lambda: generated.append(True),
        on_action=actions.append)

    step("03 first layout (folded board)")
    workspace.frame = (0, 0, 390, 760)
    workspace.layout()
    workspace.board.layout()
    workspace.sheet.layout()
    board, sheet = workspace.board, workspace.sheet
    check(not board.rows and len(board.headers) == len(workspace.topics),
          "board should start folded to topic headers")

    step("04 expand all")
    board.toggle_fold(board.fold_button)
    check(len(board.rows) == len(workspace.infos), "Expand all should show every skill")
    check(any(h.kind == "group" for h in board.headers), "subheadings should appear")

    step("05 measure the longest row")
    longest = max(board.rows, key=lambda r: len(r.entry["title"]))
    longest.layout()
    needed = text_height(longest.entry["title"], longest.title_width(longest.width),
                         ROW_TITLE_SIZE, True)
    check(longest.title.height >= needed - 1, "longest row should fit its whole title")

    step("06 tap rows on")
    drills = workspace.drill_levels
    drill_row = next(r for r in board.rows if r.entry["generator_id"] in drills)
    plain = [r for r in board.rows if r.entry["generator_id"] not in drills][:2]
    for row in plain + [drill_row]:
        tap(row)
    check(len(workspace.blocks) == 3, "three row taps should add three blocks")

    step("07 header counts and toggling off")
    first_id = plain[0].entry["generator_id"]
    topic = workspace.infos[first_id].topic
    topic_header = next(h for h in board.headers if h.kind == "topic" and h.key == topic)
    check("on sheet" in topic_header.detail.text, "topic header should count skills on the sheet")
    tap(row_for(board, first_id))
    check(len(workspace.blocks) == 2, "tapping a green row should take the skill off")
    tap(row_for(board, first_id))

    step("08 duplicate and remove every copy")
    sheet.layout()
    sheet.duplicate_card(sheet.cards[-1])
    check(row_for(board, first_id).added == 2, "duplicate should show ×2")
    tap(row_for(board, first_id))
    check(first_id not in workspace.counts(), "tapping should remove every copy")
    tap(row_for(board, first_id))
    sheet.layout()

    step("09 open and close cards")
    plain_card = next(c for c in sheet.cards if not c.has_drill)
    closed = plain_card.height_needed()
    tap(plain_card, 60, 50)
    check(plain_card.height_needed() == closed + 3 * CARD_ROW + 8,
          "a card without drill should skip the drill row")
    tap(plain_card, 60, 50)

    step("10 drill switch and count")
    drill_card = next(c for c in sheet.cards if c.has_drill)
    tap(drill_card, 60, 50)
    drill_card.layout()
    drill_card.drill_switch.value = True
    drill_card.change_drill(drill_card.drill_switch)
    check(drill_card.block["kind"] == "drill", "drill switch should make a drill block")
    drill_card.change_count(drill_card.plus)
    tap(drill_card, 60, 50)

    step("11 hold and drag")
    last = sheet.cards[-1]
    held = last.block
    last.touch_began(FakeTouch(60, 50))
    last.lift_if_held(last.press_token)
    for _ in range(12):
        last.touch_moved(FakeTouch(60, -40))
    last.touch_ended(FakeTouch(60, -40))
    check(workspace.blocks[0] is held, "hold-and-drag should move the card to the top")

    step("12 grip drag")
    grip_card = sheet.cards[-1]
    gripped = grip_card.block
    grip_card.grip.touch_began(FakeTouch(40, 10))
    for _ in range(12):
        grip_card.grip.touch_moved(FakeTouch(40, -40))
    grip_card.grip.touch_ended(FakeTouch(40, -40))
    check(workspace.blocks[0] is gripped, "grip drag should move the card to the top")

    step("13 fold all, open one topic")
    board.toggle_fold(board.fold_button)
    check(not board.rows, "Fold all should hide the rows")
    first_topic = next(h for h in board.headers if h.kind == "topic")
    first_topic.touch_ended(FakeTouch(10, 10))

    step("14 topic chip")
    algebra_chip = next(chip for chip in board.topic_chips if chip.name == "algebra")
    board.pick_topic(algebra_chip)
    board.toggle_fold(board.fold_button)
    board.toggle_fold(board.fold_button)
    check(board.rows and all(workspace.infos[r.entry["generator_id"]].topic == "algebra"
                             for r in board.rows), "Algebra chip should show Algebra only")
    board.pick_topic(board.topic_chips[0])

    step("15 grade chip")
    board.pick_grades(next(chip for chip in board.grade_chips if chip.name == "Grades 8-9"))
    check(board.rows and all(max(r.entry["grades"]) >= 8 for r in board.rows),
          "Grades 8-9 should show only skills reaching grade 8")
    board.pick_grades(board.grade_chips[0])

    step("16 search")
    board.search.text = "fractions"
    board.textfield_did_change(board.search)
    check(board.rows and board.placeholder.hidden, "search should unfold matches")

    step("17a edge handle tap (sheet slide animation)")
    sheet.handle.touch_began(FakeTouch(10, 300))
    sheet.handle.touch_ended(FakeTouch(10, 300))
    step("17b title")
    sheet.title_field.text = "Y9 starter"
    sheet.textfield_did_end_editing(sheet.title_field)
    check(received[-1][1] == "Y9 starter", "host should hear the new title")
    step("17c settings")
    sheet.answers_switch.value = False
    sheet.style_control.selected_index = 1
    sheet.change_settings(sheet.answers_switch)
    step("17d generate")
    check(settings and settings[-1] == (False, 1), "host should hear the settings")
    sheet.generate(None)
    check(generated, "Generate should reach the host")
    step("17e preview actions")
    workspace.sync_results({"busy": False, "status": "Preview ready.",
                            "ready": True, "answers": False, "saved": False})
    sheet.run_action(sheet.open_button)
    check(actions == ["open_questions"], "Open should reach the host")

    step("18 build the sheet")
    blocks, title = received[-1]
    built = build_block_sheet(registry, blocks, title, seed=4)
    print("Built questions:", len(built.questions))

    step("19 finished")
    for failure in failures:
        print("FAIL", failure)
        step("FAIL " + failure)
    result = "FAIL" if failures else "PASS"
    step("RESULT: " + result)
    KEEP_ALIVE.append(workspace)
    print("RESULT:", result)
    return 1 if failures else 0


def main_on_ui_thread():
    """UIKit views must only be touched on the main thread. Forge runs scripts
    on a background thread, so run the whole smoke on the main thread, as real
    taps are, instead of racing UIKit's own animations."""
    from objc_util import on_main_thread
    result = []
    on_main_thread(lambda: result.append(main()))()
    return result[0] if result else 1


if __name__ == "__main__":
    sys.exit(main_on_ui_thread())