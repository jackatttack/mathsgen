"""Exercise short/long headings, large numbering and clickable question links."""
import sys
from io import BytesIO
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
for name in list(sys.modules):
    if name == "mathsgen" or name.startswith("mathsgen."):
        del sys.modules[name]

from reportlab.pdfgen.canvas import Canvas
from mathsgen.pdf_headings import SectionHeading, LevelBadge
from mathsgen.theme import THEMES


def main():
    theme = THEMES["ivory"]
    stream = BytesIO()
    canvas = Canvas(stream)
    for width in (230, 458):
        for number in (1, 12, 123):
            for title in (
                "Algebra",
                "Prime factors, HCF and LCM",
                "Equations, inequalities and algebraic manipulation with fractions",
            ):
                heading = SectionHeading(number, title, theme)
                measured_width, height = heading.wrap(width, 800)
                assert measured_width == width
                assert heading.title_x + heading.title_width <= width + 0.01
                assert height >= heading.title_height
                heading.drawOn(canvas, 20, 700 - height)
                canvas.showPage()
        question = SectionHeading(12, "Question", theme, compact=True, badge="Level 4")
        question.wrap(width, 800)
        question.drawOn(canvas, 20, 700)
        canvas.showPage()
    badge = LevelBadge("Apply it", theme)
    badge.wrap(230, 800)
    badge.drawOn(canvas, 20, 700)
    canvas.save()
    assert len(stream.getvalue()) > 1000
    print("PASS: headings draw at two widths with wrapped titles, 1-3 digit numbers and badges.")
    print("Visual acceptance remains a device check.")


if __name__ == "__main__":
    main()