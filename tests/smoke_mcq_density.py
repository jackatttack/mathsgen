"""Regression for horizontal options and the reported 25-page fraction sheet."""
from dataclasses import replace
from io import BytesIO
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
for name in list(sys.modules):
    if name == "mathsgen" or name.startswith("mathsgen."):
        del sys.modules[name]

from reportlab.pdfgen.canvas import Canvas
from mathsgen.blocks import build_block_sheet
from mathsgen.catalogue import build_registry
from mathsgen.core import Choice, Content, require
from mathsgen.export import export_worksheet
from mathsgen.pdf import CONTENT_WIDTH, styles
from mathsgen.pdf_choices import ChoiceGrid
from mathsgen.question_actions import render_question_card
from mathsgen.worksheets import Worksheet


def main():
    registry = build_registry()
    sheet = build_block_sheet(registry, [{
        "generator_id": "number.fractions.addition",
        "kind": "questions", "levels": [1], "count": 25,
        "multiple_choice": True,
    }], "Fraction addition — choose one answer", seed=10325)
    canvas = Canvas(BytesIO())
    for question in sheet.questions:
        grid = ChoiceGrid(question, styles(), CONTENT_WIDTH - 24)
        width, height = grid.wrapOn(canvas, CONTENT_WIDTH - 24, 10000)
        require(grid.columns == len(question.choices),
                "Short fraction options did not fit on one row")
        require(height < 60, "Fraction options unexpectedly tall")

    # A wider expression must wrap to fewer columns at readable type size.
    question = sheet.questions[0]
    wide = replace(question, choices=tuple(
        Choice("option_" + str(index), Content(
            "x + y + z + a + b + c + " + str(index),
            "x+y+z+a+b+c+" + str(index)))
        for index in range(4)))
    grid = ChoiceGrid(wide, styles(), CONTENT_WIDTH - 24)
    grid.wrapOn(canvas, CONTENT_WIDTH - 24, 10000)
    require(grid.columns < 4, "Wide options did not fall back safely")
    print("Wide-option columns:", grid.columns)

    result = export_worksheet(sheet, ROOT / "exports" / "specimens", answers=True)
    question_report = next(item for item in result["pdfs"] if item["mode"] == "questions")
    print("25 MCQs, block renderer:", question_report["pages"], "pages")
    print("Specimen:", question_report["path"])
    require(question_report["pages"] <= 9,
            "Pagination still wastes space: more than nine pages for 25 short MCQs")

    ordinary = Worksheet(
        sheet.id, sheet.title, sheet.seed, {"title": sheet.title}, sheet.questions)
    normal_result = export_worksheet(ordinary, ROOT / "exports" / "specimens")
    normal_report = normal_result["pdfs"][0]
    print("25 MCQs, normal renderer:", normal_report["pages"], "pages")
    require(normal_report["pages"] <= 9, "Normal worksheet pagination regression")
    card = Path(result["directory"]) / "horizontal_choice_card.pdf"
    print("Copied card size:", render_question_card(question, card))
    print("MCQ DENSITY PASS — device visual review pending")


if __name__ == "__main__":
    main()