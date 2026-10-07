"""MCQ assembly: mixed blocks, saved settings, exclusions and exact recovery."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
for name in list(sys.modules):
    if name == "mathsgen" or name.startswith("mathsgen."):
        del sys.modules[name]

from mathsgen.blocks import build_block_sheet
from mathsgen.build_model import usable_blocks
from mathsgen.catalogue import build_registry
from mathsgen.core import canonical_json, require
from mathsgen.multiple_choice import validate_multiple_choice
from mathsgen.worksheets import build_worksheet


def must_reject(action, fragment):
    try:
        action()
    except ValueError as error:
        require(fragment in str(error), "Unexpected error: " + str(error))
        return
    raise AssertionError("Expected rejection: " + fragment)


def main():
    registry = build_registry()
    blocks = [
        {"generator_id": "number.fractions.addition", "kind": "questions",
         "levels": [1, 2], "count": 6, "multiple_choice": True},
        {"generator_id": "number.percentages.of_amount", "kind": "questions",
         "levels": [1, 2], "count": 6, "multiple_choice": True},
        {"generator_id": "algebra.substitution.values", "kind": "questions",
         "levels": [1, 2], "count": 6, "multiple_choice": True},
        {"generator_id": "number.fractions.multiplication", "kind": "questions",
         "levels": [1], "count": 3},
        {"generator_id": "number.fractions.addition", "kind": "drill",
         "levels": [1], "count": 3, "apply": False},
    ]
    sheet = build_block_sheet(registry, blocks, "MCQ integration", seed=103)
    again = build_block_sheet(registry, blocks, "MCQ integration", seed=103)
    require(canonical_json(sheet.to_dict()) == canonical_json(again.to_dict()),
            "Sheet not reproducible")
    require(all(q.choices for q in sheet.questions[:18]), "Missing MCQ options")
    require(all(not q.choices for q in sheet.questions[18:]),
            "Ordinary questions or drills changed to MCQ")
    for question in sheet.questions[:18]:
        validate_multiple_choice(question, registry.get(question.generator_id))
    saved = usable_blocks(sheet.specification["blocks"], registry)
    require(saved == sheet.specification["blocks"], "Saved MCQ state lost")

    base = {"generator_id": "number.percentages.of_amount",
            "kind": "questions", "levels": [3], "count": 2,
            "multiple_choice": True}
    must_reject(lambda: build_block_sheet(registry, [base]),
                "supports multiple choice")
    must_reject(lambda: build_block_sheet(registry, [
        dict(blocks[0], kind="drill")]), "not drills")
    must_reject(lambda: build_block_sheet(registry, [
        dict(blocks[0], multiple_choice="yes")]), "true or false")

    section = {"generator_ids": ["algebra.substitution.values"],
               "difficulties": [1, 2], "count": 8, "multiple_choice": True}
    ordinary = build_worksheet({
        "title": "CLI MCQ spec", "sections": [section]}, seed=31, registry=registry)
    require(all(q.choices for q in ordinary.questions), "Section MCQ setting lost")
    must_reject(lambda: build_worksheet({
        "sections": [dict(section, difficulties=[4])]}, registry=registry),
        "no multiple-choice support")
    print("Mixed sheet:", len(sheet.questions), "questions; 18 MCQs")
    print("Section specifications, saved blocks, exclusions and recovery PASS")
    print("MCQ WORKSHEETS PASS")


if __name__ == "__main__":
    main()