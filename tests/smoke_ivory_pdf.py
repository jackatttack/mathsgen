"""Check transparent paper panels and export all three Ivory worksheet layouts."""
import sys
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
for module_name in list(sys.modules):
    if module_name == "mathsgen" or module_name.startswith("mathsgen."):
        del sys.modules[module_name]

from reportlab.lib import colors
from reportlab.platypus import Paragraph
from mathsgen.catalogue import build_registry
from mathsgen.blocks import build_block_sheet
from mathsgen.drill import build_drill
from mathsgen.export import export_worksheet
from mathsgen.pdf import styles
from mathsgen.squared_page import content_panel, draw_page_background
from mathsgen.theme import THEMES
from mathsgen.worksheets import build_worksheet


class PaperRecorder:
    """Record paper and grid painting without requiring a native UI."""
    def __init__(self):
        self.events = []

    def saveState(self):
        pass

    def restoreState(self):
        pass

    def setFillColor(self, colour):
        self.events.append(("fill", colour))

    def setStrokeColor(self, colour):
        pass

    def setLineWidth(self, width):
        pass

    def rect(self, *args, **kwargs):
        self.events.append(("paper", args))

    def line(self, *args):
        self.events.append(("grid", args))


def main():
    ivory = THEMES["ivory"]
    sizes = []
    for name in ("calm", "classic", "contrast", "ivory"):
        theme = THEMES[name]
        panel = content_panel(
            [Paragraph("Measured question content", styles(THEMES["calm"])["body"])],
            300, theme,
        )
        sizes.append(panel.wrap(300, 800))
        assert bool(panel._bkgrndcmds) == theme.opaque_panels
    assert len(set(sizes)) == 1, "Backing changed panel measurement"

    recorder = PaperRecorder()
    draw_page_background(recorder, 300, 500, ivory)
    assert recorder.events[0] == ("fill", colors.HexColor(ivory.paper_ink))
    assert recorder.events[1][0] == "paper"
    assert all(event[0] == "grid" for event in recorder.events[2:])
    assert len(recorder.events) > 4
    recorder = PaperRecorder()
    draw_page_background(recorder, 300, 500, ivory, squared=False)
    assert len(recorder.events) == 2, "Answer paper gained a grid"

    registry = build_registry()
    normal = build_worksheet({
        "title": "Ivory - algebra and geometry", "shuffle": False,
        "sections": [
            {"generator_ids": ["algebra.linear.two_sided"], "count": 2,
             "difficulties": [1, 2]},
            {"generator_ids": ["geometry.angles.triangle"], "count": 2,
             "difficulties": [1, 2]},
        ],
    }, 103, registry)
    drill_blocks = [
        {"generator_id": "algebra.expressions.like_terms",
         "levels": [1, 2], "count": 6},
        {"generator_id": "geometry.trigonometry.right_angled",
         "levels": [1], "count": 4},
    ]
    drill = build_drill(registry, drill_blocks, "Ivory - fluency practice", seed=103)
    mixed = build_block_sheet(registry, [
        dict(drill_blocks[0], kind="drill"),
        {"generator_id": "geometry.angles.triangle", "kind": "questions",
         "levels": [1, 2], "count": 2},
    ], "Ivory - mixed practice", seed=103)
    destination = PROJECT_ROOT / "exports" / "specimens"
    destination.mkdir(parents=True, exist_ok=True)
    for worksheet in (normal, drill, mixed):
        worksheet = replace(worksheet, specification=dict(
            worksheet.specification, theme="ivory",
        ))
        result = export_worksheet(worksheet, destination, answers=True)
        assert len(result["pdfs"]) == 2
        assert all(pdf["pages"] > 0 and pdf["bytes"] > 0 for pdf in result["pdfs"])
        print(worksheet.title)
        print("Specimen:", result["directory"])
        for pdf in result["pdfs"]:
            print("  {}: {} pages".format(pdf["mode"], pdf["pages"]))
    print("PASS: backing preserves measurement; paper precedes grid; three layouts export.")
    print("Device review pending: paper colour, grid readability and diagram backgrounds.")


if __name__ == "__main__":
    main()