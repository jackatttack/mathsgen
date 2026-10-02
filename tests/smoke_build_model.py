"""Smoke: the Build library, default blocks and the editor views.

Data: the library lists all skills once, in strand order; every skill's
default block builds, as does every drill skill's drill block; search,
summaries and saved-block restore behave.

Views (constructed, never presented): add two skills from the library,
switch a block to drill and raise its count, drag it to the top, duplicate
it, press Done, and build the resulting sheet.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from launch_mathsgen import load_engine
from mathsgen import build_model as model
from mathsgen.blocks import build_block_sheet
from mathsgen.curriculum import load_level_tags

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def check_data(registry):
    level_tags = load_level_tags(registry)
    drills = model.drill_levels_by_skill(registry)
    sections = model.library_sections(registry, level_tags, drills)
    listed = [entry["generator_id"] for _, entries in sections for entry in entries]
    ids = {info.id for info in registry.list()}
    check(sorted(listed) == sorted(ids), "library does not list every skill exactly once")
    titles = [title for title, _ in sections]
    order = [title for _, title in model.STRANDS]
    check(titles == [title for title in order if title in titles], "strands out of order")
    check(model.filter_sections(sections, "fractions"), "search 'fractions' found nothing")
    check(not model.filter_sections(sections, "zzzz"), "search 'zzzz' found something")
    check(model.filter_sections(sections, "a18"), "search by spec code found nothing")

    infos = registry.list()
    defaults = [dict(model.default_block(info), count=1) for info in infos]
    sheet = build_block_sheet(registry, defaults, "Every default", seed=2)
    check(len(sheet.questions) == len(infos), "default blocks did not all build")
    drill_blocks = [{"generator_id": gid, "kind": "drill", "levels": list(levels),
                     "count": 1, "apply": False} for gid, levels in sorted(drills.items())]
    sheet = build_block_sheet(registry, drill_blocks, "Every drill", seed=2)
    check(len(sheet.specification["segments"]) == len(drills), "drill blocks did not all build")

    check(model.level_text([1, 2, 3, 4]) == "L1–4", "level run text")
    check(model.level_text([1, 3]) == "L1, 3", "level gap text")
    restored = model.usable_blocks(defaults[:2] + [{"generator_id": "gone"}, "junk"], registry)
    check(len(restored) == 2, "restore should keep two valid blocks")
    first = sections[0][1][0]
    print("Library:", ", ".join("{} {}".format(t, len(e)) for t, e in sections))
    print("First entry:", first["title"], "|", first["detail"])
    return drills


def check_views(registry, drills):
    from mathsgen.build_ui import BuildEditor
    received = []
    editor = BuildEditor(registry, [], received.append)
    editor.frame = (0, 0, 390, 844)
    editor.layout()
    editor.library.open()
    editor.library.layout()
    check(bool(editor.library.sections), "library panel is empty")
    editor.library.tableview_did_select(editor.library.table, 0, 0)
    editor.library.tableview_did_select(editor.library.table, 1, 0)
    check(len(editor.blocks) == 2, "library taps did not add two blocks")

    drill_id = sorted(drills)[0]
    editor.add_block(drill_id)
    panel = editor.panel
    panel.open(2)
    panel.layout()
    panel.kind_control.selected_index = 1
    panel.change_kind(panel.kind_control)
    block = editor.blocks[2]
    check(block["kind"] == "drill", "kind did not switch to drill")
    check(set(block["levels"]) <= set(drills[drill_id]), "drill levels not limited")
    before = block["count"]
    panel.change_count(panel.plus)
    check(block["count"] == before + 1, "count did not go up")
    panel.close()

    editor.tableview_move_row(editor.table, 0, 2, 0, 0)
    check(editor.blocks[0]["kind"] == "drill", "drag to top did not move the block")
    panel.open(0)
    panel.duplicate(None)
    check(len(editor.blocks) == 4, "duplicate did not add a block")
    editor.finish(None)
    check(len(received) == 1 and len(received[0]) == 4, "Done did not hand back four blocks")
    sheet = build_block_sheet(registry, received[0], "Editor smoke", seed=3)
    print("Editor sheet:", [model.block_summary(b) for b in received[0]])
    print("Editor sheet questions:", len(sheet.questions))


def main():
    registry = load_engine()
    drills = check_data(registry)
    check_views(registry, drills)
    for failure in failures:
        print("FAIL", failure)
    print("RESULT:", "FAIL" if failures else "PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())