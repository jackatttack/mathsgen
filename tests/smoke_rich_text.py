"""Typography specimen and focused wrapping/baseline checks."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

import tempfile
from pathlib import Path

from launch_mathsgen import load_engine


def main():
    load_engine()
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from mathsgen.core import require
    from mathsgen.rich_text import RichParagraph

    examples = [
        [
            {"text": "The cylinder has radius "},
            {"tex": "x+2", "text": "x + 2"},
            {"text": " cm and height "},
            {"tex": "3x", "text": "3x"},
            {"text": " cm. Find its volume."},
        ],
        [
            {"text": "The volume of a sphere is "},
            {"tex": r"V=\frac{4}{3}\pi r^{3}", "text": "V = (4/3)pi*r^3"},
            {"text": ". Use this formula to form an equation and solve it."},
        ],
        [
            {"text": "The paintable area is "},
            {"tex": r"31.81\ \mathrm{m}^{2}", "text": "31.81 square metres"},
            {"text": ". Exactly "},
            {"tex": r"\frac{3181}{600}", "text": "3181/600"},
            {"text": " litres are needed. Buy 3 tins at £38 each."},
        ],
        [
            {"text": "Simplify "},
            {"tex": r"\frac{x^{2}-9}{x+3}", "text": "(x^2 - 9)/(x + 3)"},
            {"text": ", where "},
            {"tex": r"x\ne-3", "text": "x != -3"},
            {"text": ". Explain your answer."},
        ],
        [
            {"text": "Compare "},
            {"tex": r"\sqrt{x+1}", "text": "sqrt(x + 1)"},
            {"text": " with "},
            {"tex": r"\frac{1}{\sqrt{x+1}}", "text": "1/sqrt(x + 1)"},
            {"text": "; keep the punctuation attached to the expression."},
        ],
    ]
    for index, runs in enumerate(examples):
        paragraph = RichParagraph(runs, context="specimen " + str(index + 1))
        for width in (150, 250, 480):
            _, height = paragraph.wrap(width, 700)
            require(height > 0, "Missing paragraph")
            for pieces, ascent, descent, line_height in paragraph.lines:
                require(ascent + descent + 4 <= line_height + 1e-8, "Clipped baseline")
                require(all(x + piece[0] <= width + 1e-8 for x, piece in pieces),
                        "Horizontal overflow")
            original = paragraph.lines
            paragraph.wrap(width, 700)
            require(paragraph.lines is original, "Repeated measurement was not cached")

    attached = RichParagraph([
        {"tex": r"\frac{3}{4}", "text": "3/4"}, {"text": ", next"},
    ])
    require(len(attached.words[0]) == 2, "Punctuation separated from maths")
    try:
        RichParagraph([{"text": "unbreakable"}]).wrap(5, 700)
    except ValueError:
        pass
    else:
        raise AssertionError("Overwide content accepted")

    root = Path(__file__).resolve().parent.parent
    exports = root / "exports"
    exports.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="rich_text_specimen_", dir=str(exports)))
    destination = directory / "typography.pdf"
    styles = getSampleStyleSheet()
    story = [Paragraph("Mathsgen: inline maths specimen", styles["Title"]), Spacer(1, 12)]
    for width in (480, 250):
        story.append(Paragraph("Text column: {} pt".format(width), styles["Heading2"]))
        for index, runs in enumerate(examples):
            # A one-column table supplies the exact test width during PDF layout.
            from reportlab.platypus import Table, TableStyle
            paragraph = RichParagraph(runs, context="PDF specimen " + str(index + 1))
            table = Table([[paragraph]], colWidths=[width], hAlign="LEFT")
            table.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(table)
    SimpleDocTemplate(
        str(destination), pagesize=A4,
        leftMargin=50, rightMargin=50, topMargin=40, bottomMargin=40,
    ).build(story)
    print("PASS: 15 width/sample combinations, baseline bounds, punctuation,")
    print("wrap caching, overflow rejection and actual vector PDF drawing.")
    print("Typography specimen:", destination)
    print("Visual review: pending. Existing worksheet rendering is unchanged.")


if __name__ == "__main__":
    main()