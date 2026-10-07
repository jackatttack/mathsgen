"""Main-thread checks for Build's MCQ filter and shared Drill browser."""
import builtins
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
for name in list(sys.modules):
    if name == "mathsgen" or name.startswith("mathsgen."):
        del sys.modules[name]

from objc_util import on_main_thread

PROGRESS = ROOT / "dev" / "smoke_mcq_filter_progress.txt"
ERRORS = []


def step(message):
    with PROGRESS.open("a", encoding="utf-8") as output:
        output.write(message + "\n")
        output.flush()


@on_main_thread
def check_filter():
    try:
        from mathsgen.catalogue import build_registry
        from mathsgen.build_workspace import Workspace, SkillBoard
        from mathsgen.drill_browser import DrillBrowserModel
        from mathsgen.core import require

        registry = build_registry()
        changes = []
        workspace = Workspace(
            registry, [], "Filter smoke",
            lambda *args: changes.append(args),
            log_path=Path(tempfile.gettempdir()) / "mcq_filter_actions.log")
        retained = getattr(builtins, "_mathsgen_mcq_filter_views", [])
        retained.append(workspace)
        builtins._mathsgen_mcq_filter_views = retained
        workspace.frame = (0, 0, 390, 760)
        workspace.layout()
        board = workspace.board
        board.layout()
        chip = next(c for c in board.topic_chips if c.name == "mcq")

        step("MCQ filter")
        board.pick_topic(chip)
        shown = {row.entry["generator_id"] for row in board.rows}
        require(shown == board.mcq_ids, "MCQ filter omitted or added skills")
        require("number.indices.meaning_mcq" in shown, "Native MCQ missing")
        require("MCQ" in board.filters_button.title, "Collapsed summary missing")

        step("topic intersection")
        algebra = next(c for c in board.topic_chips if c.name == "algebra")
        board.pick_topic(algebra)
        require(board.rows and all(
            registry.get(row.entry["generator_id"]).info.topic == "algebra"
            for row in board.rows), "Topic filter did not intersect MCQ")
        board.search.text = "substitution"
        board.textfield_did_change(board.search)
        require({row.entry["generator_id"] for row in board.rows}
                == {"algebra.substitution.values"}, "Search intersection failed")
        board.search.text = "no_matching_skill_here"
        board.textfield_did_change(board.search)
        require(not board.rows and not board._empty.hidden, "Empty state missing")
        board.search.text = ""
        board.pick_topic(next(c for c in board.topic_chips if c.name == "all"))

        step("grade intersection")
        grade_chip = next(c for c in board.grade_chips if c.name != "any")
        board.pick_grades(grade_chip)
        low, high = board.grades
        require(all(
            row.entry["generator_id"] in board.mcq_ids
            and any(low <= grade <= high for grade in row.entry["grades"])
            for row in board.rows), "Grade intersection failed")
        board.pick_grades(next(c for c in board.grade_chips if c.name == "any"))

        step("rapid filter toggles preserve selection")
        before = list(workspace.blocks)
        for _ in range(20):
            board.pick_topic(chip)
        require(board.mcq_only, "Even toggle count changed filter state")
        require(workspace.blocks == before and not changes,
                "Filtering changed or saved sheet selection")

        step("Drill browser unaffected")
        host = SimpleNamespace(
            registry=registry, infos=registry.list(), drill_selected=set())
        drill = SkillBoard(DrillBrowserModel(host))
        retained.append(drill)
        drill.frame = (0, 0, 390, 650)
        drill.layout()
        require(not any(c.name == "mcq" for c in drill.topic_chips),
                "Build filter leaked into Drill")
        require(not drill.mcq_only, "Drill is unexpectedly filtered")
        step("PASS")
    except Exception:
        import traceback
        ERRORS.append(traceback.format_exc())
        step(ERRORS[-1])


if __name__ == "__main__":
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.write_text("", encoding="utf-8")
    check_filter()
    if ERRORS:
        raise AssertionError("\n".join(ERRORS))
    print("MCQ FILTER PASS — topic, grade, search, empty state and Drill isolation")