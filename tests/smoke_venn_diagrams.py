"""Validate and export the first two-set Venn rendering prototype."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from itertools import combinations
from pathlib import Path

from launch_mathsgen import load_engine


def main():
    load_engine()

    from reportlab.graphics import renderPDF
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen.canvas import Canvas

    from mathsgen.core import require
    from mathsgen.visuals import drawing_for
    from mathsgen.venn_diagrams import venn_asset

    checks = 0

    # All 16 distinct subsets of the four Venn regions.
    for count in range(5):
        for regions in combinations(range(4), count):
            asset = venn_asset(shaded=regions)

            for width in (250, 360):
                drawing = drawing_for(asset, width)

                require(
                    drawing.width == width
                    and drawing.height > 0,
                    "Incorrect Venn drawing size",
                )
                checks += 1

    examples = [
        ("Shade A", venn_asset(shaded=(0, 1))),
        ("Shade A complement", venn_asset(shaded=(2, 3))),
        ("Shade A intersection B", venn_asset(shaded=(1,))),
        ("Shade A intersection B complement", venn_asset(shaded=(0,))),
        ("Shade neither A nor B", venn_asset(shaded=(3,))),
        ("Shade A complement union B", venn_asset(shaded=(1, 2, 3))),
        (
            "Completed frequency diagram",
            venn_asset(values=(12, 8, 7, 3)),
        ),
        (
            "Student diagram with missing values",
            venn_asset(values=(12, 8, 7, 3), missing=(0, 1, 3)),
        ),
    ]

    output = (
        Path(__file__).resolve().parent.parent
        / "exports"
        / "venn_layout_probe.pdf"
    )

    output.parent.mkdir(parents=True, exist_ok=True)

    canvas = Canvas(str(output), pagesize=A4)
    page_width, page_height = A4

    for index, (heading, asset) in enumerate(examples):
        if index % 2 == 0:
            canvas.setFont("Helvetica-Bold", 16)
            canvas.drawString(
                45, page_height - 43,
                "Mathsgen - Venn diagram prototype",
            )

        y = 415 if index % 2 == 0 else 95

        canvas.setFont("Helvetica", 12)
        canvas.drawString(70, y + 280, heading)

        drawing = drawing_for(asset, 360)
        renderPDF.draw(drawing, canvas, 110, y)

        if index % 2 == 1:
            canvas.showPage()

    canvas.save()

    print("PASS:", checks, "region-mask rendering checks")
    print("PASS:", len(examples), "specimen diagrams exported")
    print("PDF:", output)


if __name__ == "__main__":
    main()