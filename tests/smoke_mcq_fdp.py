"""All six FDP directions: target notation, exact semantics and reproduction."""
from fractions import Fraction
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
for name in list(sys.modules):
    if name == "mathsgen" or name.startswith("mathsgen."):
        del sys.modules[name]

from mathsgen.catalogue import build_registry
from mathsgen.core import require
from mathsgen.multiple_choice import (
    make_multiple_choice, validate_multiple_choice, numeric_answer,
)
from mathsgen.mcq_fdp import conversion
from mathsgen.fdp_conversions import DIRECTIONS
from mathsgen.question_actions import encode_question, source_question
from mathsgen.blocks import build_block_sheet
from mathsgen.export import export_worksheet


def main():
    registry = build_registry()
    generator = registry.get("number.fdp.fraction_to_decimal")
    total = skipped = 0
    for level in (1, 2):
        seen = set()
        for seed in range(180):
            original = generator.generate(seed, level)
            question = make_multiple_choice(original)
            if question is None:
                require(original.parameters["source"] == "fraction_decimal"
                        and original.parameters["inner"]["form"] == "order",
                        "Unexpectedly rejected a single conversion")
                skipped += 1
                continue
            source, target, expected = conversion(original)
            key = (original.parameters["source"], source + "_to_" + target)
            validate_multiple_choice(question, generator, independent=key not in seen)
            require(numeric_answer(original) == expected, "Answer normalisation wrong")
            values = []
            for choice, item in zip(
                    question.choices, question.answer["multiple_choice"]["options"]):
                text = choice.content.text
                if target == "percentage":
                    require(text.endswith("%"), "Missing percent sign")
                    value = Fraction(text[:-1]) / 100
                else:
                    require("%" not in text, "Unexpected percent sign")
                    if target == "decimal":
                        require("/" not in text, "Decimal option displayed as a fraction")
                    value = Fraction(text)
                require(value == Fraction(item["value"]), "Displayed option has wrong value")
                values.append(value)
            require(len(set(values)) == len(values) and values.count(expected) == 1,
                    "Equivalent or ambiguous conversion options")
            if key not in seen:
                require(source_question(encode_question(question), registry) == question,
                        "Conversion link failed")
                print("L{} {}".format(level, key), original.prompt.text)
                print(" | ".join(chr(65 + i) + ": " + choice.content.text
                                 for i, choice in enumerate(question.choices)))
                print("Answer:", question.answer_display.text)
            seen.add(key)
            total += 1
        expected_routes = {("conversions", direction) for direction in DIRECTIONS}
        expected_routes.add(("fraction_decimal", "fraction_to_decimal"))
        if level == 1:
            expected_routes.add(("fraction_decimal", "decimal_to_fraction"))
        require(seen == expected_routes, "Missing conversion route: " + str(expected_routes - seen))
    sheet = build_block_sheet(registry, [{
        "generator_id": generator.info.id, "kind": "questions",
        "levels": [1, 2], "count": 12, "multiple_choice": True,
    }], "Fractions, decimals and percentages — choose one answer", seed=10349)
    result = export_worksheet(sheet, ROOT / "exports" / "specimens", answers=True)
    print("Validated conversion MCQs:", total, "| excluded ordering questions:", skipped)
    print("Specimen:", result["directory"])
    print("MCQ FDP PASS — visual review pending")


if __name__ == "__main__":
    main()