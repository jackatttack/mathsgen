"""Focused negative-number MCQs: every advertised bare template and corruption."""
from dataclasses import replace
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
from mathsgen.number_operations import NEGATIVE_TEMPLATES
from mathsgen.blocks import build_block_sheet
from mathsgen.export import export_worksheet


def main():
    registry = build_registry()
    generator = registry.get("number.integers.negatives")
    checked = 0
    for level in (1, 2):
        seen = set()
        for seed in range(160):
            original = generator.generate(seed, level)
            question = make_multiple_choice(original)
            if question is None:
                continue
            template = original.parameters["template"]
            validate_multiple_choice(question, generator, independent=template not in seen)
            values = [Fraction(item["value"])
                      for item in question.answer["multiple_choice"]["options"]]
            require(len(values) == len(set(values)), "Equivalent sign errors")
            require(values.count(Fraction(original.answer["value"])) == 1,
                    "Ambiguous negative-number answer")
            require(make_multiple_choice(original) == question, "Non-reproducible options")
            if template not in seen:
                print("L{} {}".format(level, template), original.prompt.text)
                print(" | ".join(chr(65 + i) + ": " + choice.content.text
                                 for i, choice in enumerate(question.choices)))
                print("Answer:", question.answer_display.text)
            seen.add(template)
            checked += 1
        require(seen == set(NEGATIVE_TEMPLATES[level]),
                "Not every bare template produced MCQs: " + str(seen))
    require(make_multiple_choice(generator.generate(1, 3)) is None,
            "Unsupported level silently adapted")
    sheet = build_block_sheet(registry, [{
        "generator_id": generator.info.id, "kind": "questions",
        "levels": [1, 2], "count": 8, "multiple_choice": True,
    }], "Negative numbers — choose one answer", seed=10337)
    report = export_worksheet(sheet, ROOT / "exports" / "specimens", answers=True)
    print("Validated MCQs:", checked)
    print("Specimen:", report["directory"])
    print("MCQ NEGATIVES PASS — visual review pending")


if __name__ == "__main__":
    main()