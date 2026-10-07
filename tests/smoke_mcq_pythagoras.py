"""Pythagoras MCQs, levels 1-3.

Checks: every level adapts, including both shorter sides at level 2; level 4
stays written; the correct option shows the original value and unit; no two
options look the same; a tampered answer key is rejected.
"""
from dataclasses import replace
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
from mathsgen.blocks import build_block_sheet
from mathsgen.export import export_worksheet


SEEDS = 160
GENERATOR = "geometry.pythagoras.lengths"
EXPECTED_MISSING = {1: {2}, 2: {0, 1}, 3: {2}}


def must_reject(question, generator):
    try:
        validate_multiple_choice(question, generator)
    except Exception:
        return
    raise AssertionError("Tampered MCQ accepted")


def main():
    registry = build_registry()
    generator = registry.get(GENERATOR)
    checked = 0
    for level in (1, 2, 3):
        adapted, refused, mistakes, shown = 0, 0, {}, set()
        for seed in range(SEEDS):
            original = generator.generate(seed, level)
            question = make_multiple_choice(original)
            if question is None:
                refused += 1
                continue
            missing = original.parameters["missing"]
            validate_multiple_choice(question, generator, independent=missing not in shown)
            require(make_multiple_choice(original) == question, "Non-reproducible options")
            correct = next(c for c in question.choices if c.id == question.answer["choice_id"])
            want = original.answer_display.text.split(" = ", 1)[1]
            require(correct.content.text == want,
                    "Correct option {!r}, original {!r}".format(correct.content.text, want))
            texts = [choice.content.text for choice in question.choices]
            require(len(set(texts)) == len(texts), "Two options look the same: " + str(texts))
            for item in question.answer["multiple_choice"]["options"]:
                if item["mistake"]:
                    mistakes[item["mistake"]] = mistakes.get(item["mistake"], 0) + 1
            if missing not in shown:
                shown.add(missing)
                print("L{} missing side {}".format(level, missing), original.prompt.text)
                print(" | ".join(chr(65 + i) + ": " + text for i, text in enumerate(texts)))
                print("Answer:", question.answer_display.text)
                wrong = next(c.id for c in question.choices
                             if c.id != question.answer["choice_id"])
                must_reject(replace(question, answer=dict(question.answer, choice_id=wrong)),
                            generator)
            adapted += 1
        missing_forms = EXPECTED_MISSING[level] - shown
        require(not missing_forms, "Missing sides without MCQs at L{}: {}".format(
            level, sorted(missing_forms)))
        print("  L{}: {} adapted, {} refused; mistakes {}".format(
            level, adapted, refused,
            ", ".join("{} {}".format(k, v) for k, v in sorted(mistakes.items()))))
        checked += adapted
    require(make_multiple_choice(generator.generate(1, 4)) is None,
            "Pythagoras L4 silently adapted")
    sheet = build_block_sheet(registry, [
        {"generator_id": GENERATOR, "kind": "questions", "levels": [1, 2, 3],
         "count": 9, "multiple_choice": True},
    ], "Pythagoras — choose one answer", seed=20261007)
    report = export_worksheet(sheet, ROOT / "exports" / "specimens", answers=True)
    print("Validated MCQs:", checked)
    print("Specimen:", report["directory"])
    print("MCQ PYTHAGORAS PASS — visual review pending")


if __name__ == "__main__":
    main()