"""Area MCQs: exact values, all shapes, units, links and diagram layout."""
from fractions import Fraction
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
from mathsgen.catalogue import build_registry
from mathsgen.core import require
from mathsgen.multiple_choice import (
    make_multiple_choice, validate_multiple_choice, candidates_for,
    choose_candidates, MINIMUM_OPTIONS,
)
from mathsgen.question_actions import encode_question, source_question
from mathsgen.blocks import build_block_sheet
from mathsgen.export import export_worksheet
from mathsgen.pdf import CONTENT_WIDTH, styles
from mathsgen.pdf_choices import ChoiceGrid


def main():
    registry = build_registry()
    generator = registry.get("geometry.area.basic_shapes")
    checked = 0
    rejected_collisions = 0
    canvas = Canvas(BytesIO())
    for level in (1, 2):
        seen = set()
        for seed in range(40):
            original = generator.generate(seed, level)
            question = make_multiple_choice(original)
            if question is None:
                candidates = candidates_for(original)
                require(candidates is not None, "Area provider failed to recognise its form")
                target = Fraction(original.answer["value"])
                distinct_wrong = {Fraction(item.value) for item in candidates} - {target}
                require(len(distinct_wrong) < MINIMUM_OPTIONS - 1,
                        "Rejected a question with enough distinct wrong answers")
                require(len(choose_candidates(target, candidates)) == len(distinct_wrong),
                        "Candidate filtering disagrees with independent set comparison")
                generator.validate_independently(original)
                rejected_collisions += 1
                print("Correctly skipped collision:", original.prompt.text)
                continue
            shape = original.parameters["shape"]
            validate_multiple_choice(question, generator, independent=seed < 8)
            values = []
            for choice, data in zip(
                    question.choices, question.answer["multiple_choice"]["options"]):
                require(choice.content.text.endswith(" cm²"), "Missing area unit")
                shown = Fraction(choice.content.text[:-4])
                require(shown == Fraction(data["value"]), "Display/value mismatch")
                values.append(shown)
            require(len(set(values)) == len(values), "Equivalent area options")
            require(values.count(Fraction(original.answer["value"])) == 1,
                    "Incorrect or ambiguous area options")
            require(question.question_visuals == original.question_visuals,
                    "MCQ altered the question diagram")
            grid = ChoiceGrid(question, styles(), CONTENT_WIDTH - 24)
            grid.wrapOn(canvas, CONTENT_WIDTH - 24, 10000)
            require(grid.columns == len(question.choices), "Area options do not fit across")
            if shape not in seen:
                require(source_question(encode_question(question), registry) == question,
                        "Area link failed to reproduce")
                print("L{} {}".format(level, shape), original.prompt.text)
                print(" | ".join(chr(65 + i) + ": " + choice.content.text
                                 for i, choice in enumerate(question.choices)))
                print("Answer:", question.answer_display.text)
            seen.add(shape)
            checked += 1
        expected = {"triangle", "parallelogram"} if level == 1 else {"trapezium"}
        require(seen == expected, "Missing shape coverage")
    sheet = build_block_sheet(registry, [{
        "generator_id": generator.info.id, "kind": "questions",
        "levels": [1, 2], "count": 6, "multiple_choice": True,
    }], "Areas — choose one answer", seed=10345)
    result = export_worksheet(sheet, ROOT / "exports" / "specimens", answers=True)
    print("Validated area MCQs:", checked)
    print("Correctly rejected candidate collisions:", rejected_collisions)
    print("Specimen:", result["directory"])
    print("MCQ AREA PASS — diagram layout needs device review")


if __name__ == "__main__":
    main()