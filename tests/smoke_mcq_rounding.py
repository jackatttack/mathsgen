"""Rounding options: exact decimal displays, source routes, links and PDF."""
from decimal import Decimal, ROUND_HALF_UP
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
from mathsgen.multiple_choice import make_multiple_choice, validate_multiple_choice
from mathsgen.question_actions import encode_question, source_question
from mathsgen.blocks import build_block_sheet
from mathsgen.export import export_worksheet


def main():
    registry = build_registry()
    generator = registry.get("number.rounding.decimal_places")
    total = 0
    for level in (1, 2):
        seen = set()
        for seed in range(100):
            original = generator.generate(seed, level)
            question = make_multiple_choice(original)
            if question is None:
                continue
            p = original.parameters["inner"]
            source = original.parameters["source"]
            key = (source, p["form"])
            validate_multiple_choice(question, generator, independent=key not in seen)
            number = Decimal(p["digits"]).scaleb(p["exponent"])
            places = (p["amount"] if source == "places"
                      else p["amount"] - 1 - number.copy_abs().adjusted())
            expected = number.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
            require(Fraction(expected) == Fraction(original.answer["value"]),
                    "Independent Decimal rounding disagrees")
            for choice, data in zip(
                    question.choices, question.answer["multiple_choice"]["options"]):
                require(Fraction(choice.content.text) == Fraction(data["value"]),
                        "Displayed decimal disagrees with option value")
                require("/" not in choice.content.text, "Rounding option is a fraction")
            require(source_question(encode_question(question), registry) == question,
                    "Rounding MCQ link does not reproduce")
            if key not in seen:
                print("L{} {} {}".format(level, source, p["form"]), original.prompt.text)
                print(" | ".join(chr(65 + i) + ": " + choice.content.text
                                 for i, choice in enumerate(question.choices)))
                print("Answer:", question.answer_display.text)
            seen.add(key)
            total += 1
        expected_forms = {"round", "context"} if level == 1 else {"round"}
        require(seen == {(source, form) for source in ("places", "figures")
                         for form in expected_forms}, "Missing rounding route/form")

    percentage = registry.get("number.percentages.of_amount")
    checked_percentage = False
    for seed in range(40):
        question = make_multiple_choice(percentage.generate(seed, 1))
        if question is None:
            continue
        require(all("/" not in choice.content.text for choice in question.choices),
                "Percentage option still displayed as a fraction")
        validate_multiple_choice(question, percentage)
        checked_percentage = True
    require(checked_percentage, "No percentage formatting checked")
    sheet = build_block_sheet(registry, [{
        "generator_id": generator.info.id, "kind": "questions",
        "levels": [1, 2], "count": 8, "multiple_choice": True,
    }], "Rounding — choose one answer", seed=10341)
    result = export_worksheet(sheet, ROOT / "exports" / "specimens", answers=True)
    print("Validated rounding MCQs:", total)
    print("Specimen:", result["directory"])
    print("MCQ ROUNDING PASS — visual review pending")


if __name__ == "__main__":
    main()