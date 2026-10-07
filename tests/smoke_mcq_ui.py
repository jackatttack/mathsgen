"""Main-thread MCQ switch smoke; retained views and flushed crash breadcrumbs."""
import builtins
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
for name in list(sys.modules):
    if name == "mathsgen" or name.startswith("mathsgen."):
        del sys.modules[name]

from objc_util import on_main_thread

PROGRESS = ROOT / "dev" / "smoke_mcq_ui_progress.txt"
STATE = Path(tempfile.gettempdir()) / "mathsgen_mcq_ui_smoke.json"
ERRORS = []


def step(message):
    with PROGRESS.open("a", encoding="utf-8") as output:
        output.write(message + "\n")
        output.flush()


@on_main_thread
def check_ui():
    try:
        from mathsgen.catalogue import build_registry
        from mathsgen.build_workspace import Workspace
        from mathsgen.build_model import default_block, usable_blocks
        from mathsgen.core import require
        registry = build_registry()
        identifiers = [
            "number.percentages.of_amount",
            "number.fractions.addition",
            "algebra.substitution.values",
            "geometry.angles.basic_facts",
        ]
        blocks = [default_block(registry.get(gid).info) for gid in identifiers]
        saved = []

        def save(changed, title):
            STATE.write_text(json.dumps(changed), encoding="utf-8")
            saved.append(True)

        step("construct")
        workspace = Workspace(
            registry, blocks, "MCQ switch smoke", save,
            log_path=Path(tempfile.gettempdir()) / "mathsgen_mcq_actions.log")
        retained = getattr(builtins, "_mathsgen_mcq_smoke_views", [])
        retained.append(workspace)
        builtins._mathsgen_mcq_smoke_views = retained
        workspace.frame = (0, 0, 390, 760)
        workspace.layout()
        workspace.switch.selected_index = 1
        workspace.switch_view(workspace.switch)
        sheet = workspace.sheet
        sheet.layout()
        cards = list(sheet.cards)
        percent = next(c for c in cards if c.info.id == identifiers[0])
        percent.opened = True
        sheet.place_cards()
        step("enable and restrict levels")
        percent.mcq_switch.value = True
        percent.change_multiple_choice(percent.mcq_switch)
        require(percent.block["levels"] == [1, 2], "MCQ levels not restricted")
        require(not percent.level_pills[2].enabled, "Unsupported level enabled")
        require("Multiple choice" in percent.summary.text, "MCQ summary absent")
        height = percent.height_needed()
        step("forty rapid switches with synchronous saving")
        before = len(saved)
        for index in range(40):
            percent.mcq_switch.value = bool(index % 2)
            percent.change_multiple_choice(percent.mcq_switch)
        require(len(saved) == before + 40, "Switch did not save once per action")
        require(sheet.cards == cards, "Switch rebuilt cards")
        require(percent.height_needed() == height, "Switch changed card height")
        restored = usable_blocks(json.loads(STATE.read_text(encoding="utf-8")), registry)
        require(restored[0]["multiple_choice"], "Saved MCQ switch lost")

        step("drill interaction")
        fraction = next(c for c in cards if c.info.id == identifiers[1])
        fraction.opened = True
        sheet.place_cards()
        fraction.mcq_switch.value = True
        fraction.change_multiple_choice(fraction.mcq_switch)
        require(fraction.has_drill, "Expected fraction drill support")
        fraction.drill_switch.value = True
        fraction.change_drill(fraction.drill_switch)
        require(not fraction.block["multiple_choice"], "Drill retained MCQ")
        require(not fraction.mcq_switch.enabled, "MCQ switch enabled during drill")

        unsupported = next(c for c in cards if c.info.id == identifiers[3])
        require("mcq" not in unsupported.rows(), "Unsupported skill offers MCQ")
        step("PASS")
    except Exception as error:
        import traceback
        ERRORS.append(traceback.format_exc())
        step("FAIL " + str(error))


if __name__ == "__main__":
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.write_text("", encoding="utf-8")
    check_ui()
    if ERRORS:
        raise AssertionError("\n".join(ERRORS))
    print("MCQ UI PASS — automated actions; physical rapid-tap check pending")