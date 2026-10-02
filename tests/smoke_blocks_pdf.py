"""Smoke: normal worksheets still render, and block sheets export.

1. Renders a small normal worksheet (questions and answers) to a temporary
   folder, proving pdf.render_pdf still works after question_story was
   extracted.
2. Exports the example block sheet (fractions drill, level-3 simultaneous
   equations, level 1-4 percentages) with answers to exports/specimens/ for
   device review, in the classic theme.
"""
import shutil
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from launch_mathsgen import load_engine
from mathsgen.blocks import build_block_sheet
from mathsgen.drill import drill_skills
from mathsgen.export import export_worksheet
from mathsgen.worksheets import build_worksheet

SPECIMENS = PROJECT_ROOT / "exports" / "specimens"
failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def main():
    registry = load_engine()

    normal = build_worksheet({
        "title": "Normal render smoke", "shuffle": False,
        "sections": [{"generator_ids": ["number.percentages.of_amount"],
                      "count": 4, "difficulties": [1, 2]}],
    }, 5, registry)
    scratch = tempfile.mkdtemp(prefix="normal_render_")
    try:
        result = export_worksheet(normal, scratch, answers=True)
        check(len(result["pdfs"]) == 2, "normal sheet: expected two PDFs")
        check(all(pdf["pages"] >= 1 and pdf["bytes"] > 0 for pdf in result["pdfs"]),
              "normal sheet: empty PDF")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    drills = {info.id: levels for info, levels in drill_skills(registry)}
    drill_id = ("number.fractions.addition" if "number.fractions.addition" in drills
                else sorted(drills)[0])
    blocks = [
        {"generator_id": drill_id, "kind": "drill",
         "levels": sorted(drills[drill_id])[:2], "count": 4, "apply": True},
        {"generator_id": "algebra.simultaneous.linear", "kind": "questions",
         "levels": [3], "count": 6},
        {"generator_id": "number.percentages.of_amount", "kind": "questions",
         "levels": [1, 2, 3, 4], "count": 8},
    ]
    sheet = build_block_sheet(registry, blocks, "Block sheet specimen", seed=11)
    sheet = replace(sheet, specification=dict(sheet.specification, theme="classic"))
    SPECIMENS.mkdir(parents=True, exist_ok=True)
    result = export_worksheet(sheet, SPECIMENS, answers=True)
    questions_pdf = result["pdfs"][0]
    check(len(result["pdfs"]) == 2, "block sheet: expected two PDFs")
    check(len(questions_pdf["blocks"]) == 1, "block sheet: expected one drill exercise")
    check(questions_pdf["questions_numbered"] == 14,
          "block sheet: expected 14 numbered questions, got {}".format(
              questions_pdf["questions_numbered"]))

    print("Normal sheet rendered: questions and answers")
    for pdf in result["pdfs"]:
        print("Block sheet {}: {} pages".format(pdf["mode"], pdf["pages"]))
    print("Specimen folder:", result["directory"])
    for failure in failures:
        print("FAIL", failure)
    print("RESULT:", "FAIL" if failures else "PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())