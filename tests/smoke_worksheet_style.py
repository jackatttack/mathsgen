"""Check square geometry, compact footer and export all six subject colours."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from pathlib import Path
import json
import tempfile

from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import require
    from mathsgen.pdf import WorkingSpace
    from mathsgen.worksheet_ui import WorksheetBuilder
    from mathsgen.worksheets import build_worksheet
    from mathsgen.export import export_worksheet

    class CanvasRecorder:
        def __init__(self):
            self.segments = []

        def saveState(self):
            pass

        def restoreState(self):
            pass

        def setStrokeColor(self, colour):
            pass

        def setLineWidth(self, width):
            pass

        def line(self, x1, y1, x2, y2):
            self.segments.append((x1, y1, x2, y2))

    for available in (230, 470):
        space = WorkingSpace(4)
        width, height = space.wrap(available, 800)
        require(height == 80, "Working-space height changed")
        recorder = CanvasRecorder()
        space.canv = recorder
        space.draw()
        vertical = sorted({x1 for x1, y1, x2, y2 in recorder.segments if x1 == x2})
        horizontal = sorted({y1 for x1, y1, x2, y2 in recorder.segments if y1 == y2})
        require(len(vertical) > 2 and len(horizontal) > 2, "Missing grid lines")
        dx, dy = vertical[1] - vertical[0], horizontal[1] - horizontal[0]
        require(abs(dx - dy) < 1e-8 and abs(dx * 25.4 / 72 - 5) < 1e-8,
                "Cells are not five-millimetre squares")
        require(all(0 <= x <= width and 0 <= y <= height
                    for segment in recorder.segments
                    for x, y in ((segment[0], segment[1]), (segment[2], segment[3]))),
                "Grid exceeds its allocated space")
    empty = WorkingSpace(0)
    empty.canv = CanvasRecorder()
    empty.draw()
    require(not empty.canv.segments, "Zero working-space request gained a grid")

    with tempfile.TemporaryDirectory() as folder:
        view = WorksheetBuilder(registry, Path(folder))
        view.frame = (0, 0, 390, 844)
        view.layout()
        require(view.footer.height == 96, "Unused footer not compact")
        require(view.open_questions.hidden and view.open_answers.hidden
                and view.save_button.hidden, "Unused PDF controls visible")
        view.status.text = "Choose at least one skill."
        view.layout()
        require(view.footer.height == 132 and not view.status.hidden,
                "Status message is hidden")
        view.report = {"pdfs": [{"mode": "questions"}, {"mode": "answers"}]}
        view.refresh()
        require(view.footer.height == 214 and not view.open_questions.hidden
                and not view.save_button.hidden, "Preview controls did not return")
        view.busy = True
        view.refresh()
        require(not view.open_questions.enabled and not view.save_button.enabled,
                "Busy preview controls enabled")

    ids = [
        "number.percentages.of_amount",
        "algebra.linear.two_sided",
        "ratio.simplifying",
        "geometry.angles.triangle",
        "probability.selection.colours",
        "data.mean.frequency_table",
    ]
    worksheet = build_worksheet({
        "title": "Squared working space and subject colours",
        "shuffle": False,
        "sections": [{
            "generator_ids": [generator_id], "count": 1, "difficulties": [1],
        } for generator_id in ids],
    }, 20260919, registry)
    report = export_worksheet(
        worksheet, Path(__file__).resolve().parent.parent / "exports", answers=True,
    )
    print("PASS: 5 mm square cells, preserved height and zero-space behaviour.")
    print("PASS: compact footer, visible status and restored preview controls.")
    print(json.dumps(report, indent=2))
    print("Visual check: grid contrast and coloured question headings in the PDFs.")


if __name__ == "__main__":
    main()