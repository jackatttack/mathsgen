"""Test and export a two-stage probability-tree rendering prototype."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from pathlib import Path

from launch_mathsgen import load_engine


def main():
    load_engine()

    from reportlab.graphics import renderPDF
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen.canvas import Canvas

    from mathsgen.core import require
    from mathsgen.probability_tree_diagrams import (
        branch_probabilities,
        check_label_clearance,
        tree_scene,
    )
    from mathsgen.visuals import drawing_for

    for replacement in (False, True):
        probabilities = branch_probabilities(3, 2, replacement)
        for offset in (0, 2, 4):
            require(
                probabilities[offset] + probabilities[offset + 1] == 1,
                "Sibling probabilities must sum to one",
            )

        for student in (False, True):
            specimen = tree_scene(
                red=3, blue=2,
                replacement=replacement,
                student=student,
            )

            for width in (250, 360):
                check_label_clearance(specimen, width)
                drawing = drawing_for(specimen, width)
                require(
                    drawing.width == width and drawing.height > 0,
                    "Tree drawing has incorrect dimensions",
                )

    output = Path(__file__).resolve().parent.parent
    output = output / "exports" / "probability_tree_layout_probe.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)

    canvas = Canvas(str(output), pagesize=A4)
    page_width, page_height = A4

    for replacement in (False, True):
        heading = (
            "With replacement" if replacement
            else "Without replacement"
        )

        canvas.setFont("Helvetica-Bold", 15)
        canvas.drawString(42, page_height - 43, heading)

        complete = tree_scene(3, 2, replacement, student=False)
        drawing = drawing_for(complete, 360)
        renderPDF.draw(drawing, canvas, 100, 415)

        canvas.setFont("Helvetica", 11)
        canvas.drawString(42, 365, "Student version: fill in the missing probabilities.")

        student = tree_scene(3, 2, replacement, student=True)
        drawing = drawing_for(student, 250)
        renderPDF.draw(drawing, canvas, 145, 100)

        canvas.showPage()

    canvas.save()

    print("PASS: 16 diagram checks, sibling probabilities and label clearance")
    print("PDF:", output)


if __name__ == "__main__":
    main()