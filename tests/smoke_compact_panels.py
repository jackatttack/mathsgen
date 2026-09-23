"""Test tightly fitted diagram and action panels with a real PDF export."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))


from pathlib import Path

from launch_mathsgen import load_engine


def main():
    from mathsgen.visuals import VisualFlowable
    from mathsgen.pdf import (
        compact_action_panel,
        scene_working_row,
    )
    from mathsgen.worksheets import build_worksheet
    from mathsgen.export import export_worksheet

    registry = load_engine()

    spec = {
        "title": "Compact panels layout specimen",
        "shuffle": False,
        "sections": [{
            "generator_ids": ["geometry.circles.sectors"],
            "count": 2,
            "difficulties": [3],
        }],
    }

    worksheet = build_worksheet(spec, 20260921, registry)

    assert len(worksheet.questions) == 2

    for number, question in enumerate(worksheet.questions, 1):
        asset = question.visual_assets("questions")[0]

        # Ensure a nested wrap does not redraw at the cropped width.
        visual = VisualFlowable(asset, preferred_width=238)

        drawing_width, drawing_height = visual.wrap(238, 10000)
        original_drawing = visual.drawing

        repeated_width, repeated_height = visual.wrap(
            drawing_width, 10000
        )

        assert visual.drawing is original_drawing, (
            "Nested wrap unexpectedly recreated the diagram"
        )
        assert repeated_width == drawing_width
        assert repeated_height == drawing_height

        # The white diagram panel must fit the actual drawing.
        row = scene_working_row(question, 470)

        diagram_panel = row._cellvalues[0][0]
        panel_width = diagram_panel._argW[0]

        assert abs(panel_width - (drawing_width + 12)) < 0.1
        assert panel_width < 250, (
            "Diagram retained its original fixed-width panel"
        )

        # The action panel must no longer occupy the full question width.
        action_panel = compact_action_panel(question, 470)
        action_width = action_panel._argW[0]

        assert action_width < 250, (
            "Action panel is unnecessarily wide"
        )

        print(
            "PASS: question {} diagram panel {:.1f} pt; "
            "action panel {:.1f} pt".format(
                number, panel_width, action_width
            )
        )

    # Verify that both layouts survive the complete PDF rendering path.
    output_root = Path(__file__).resolve().parent.parent / "exports"

    report = export_worksheet(
        worksheet,
        output_root,
        answers=True,
    )

    for pdf in report["pdfs"]:
        path = Path(pdf["path"])

        assert path.exists()
        assert path.read_bytes()[:5] == b"%PDF-"
        assert path.stat().st_size > 1000

        print(
            "PASS: exported {} ({} bytes)".format(
                path.name, path.stat().st_size
            )
        )
        print("PDF: " + str(path))

    print("PASS: compact panel PDF export complete")
    print("VISUAL REVIEW: pending device inspection")


if __name__ == "__main__":
    main()