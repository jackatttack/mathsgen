"""Angle facts and triangle angle MCQs: every supported form at every level.

Checks: every form the provider supports produces MCQs; two-part forms never
do; the correct option shows the original value (55° or x = 12); no two
options look the same; a tampered answer key is rejected.
"""
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
from mathsgen.multiple_choice import (
    make_multiple_choice, numeric_answer, validate_multiple_choice,
)
from mathsgen.mcq_angles import SOLVE_FOR_X
from mathsgen.triangle_angles import FORMS as TRIANGLE_FORMS
from mathsgen.angle_facts import FORMS as FACT_FORMS
from mathsgen.blocks import build_block_sheet
from mathsgen.export import export_worksheet


SEEDS = 120
TWO_PART = {"vertically_opposite", "algebraic_quad_largest"}
CASES = (
    ("geometry.angles.triangle", TRIANGLE_FORMS),
    ("geometry.angles.basic_facts", FACT_FORMS),
)


def expected_text(form, value):
    value = int(value)
    return "x = {}".format(value) if form in SOLVE_FOR_X else "{}°".format(value)


def must_reject(question, generator):
    try:
        validate_multiple_choice(question, generator)
    except Exception:
        return
    raise AssertionError("Tampered MCQ accepted")


def main():
    registry = build_registry()
    checked = 0
    for generator_id, forms in CASES:
        generator = registry.get(generator_id)
        for level in (1, 2, 3, 4):
            adapted, refused, mistakes, shown = 0, 0, {}, set()
            for seed in range(SEEDS):
                original = generator.generate(seed, level)
                form = original.parameters["form"]
                question = make_multiple_choice(original)
                if form in TWO_PART:
                    require(question is None, "Two-part form silently adapted: " + form)
                    continue
                if question is None:
                    refused += 1
                    continue
                validate_multiple_choice(question, generator, independent=form not in shown)
                require(make_multiple_choice(original) == question, "Non-reproducible options")
                correct = next(c for c in question.choices
                               if c.id == question.answer["choice_id"])
                want = expected_text(form, numeric_answer(original))
                require(correct.content.text == want,
                        "Correct option {!r}, expected {!r}".format(correct.content.text, want))
                texts = [choice.content.text for choice in question.choices]
                require(len(set(texts)) == len(texts), "Two options look the same: " + str(texts))
                for item in question.answer["multiple_choice"]["options"]:
                    if item["mistake"]:
                        mistakes[item["mistake"]] = mistakes.get(item["mistake"], 0) + 1
                if form not in shown:
                    shown.add(form)
                    print("{} L{} {}".format(generator_id, level, form), original.prompt.text)
                    print(" | ".join(chr(65 + i) + ": " + text for i, text in enumerate(texts)))
                    print("Answer:", question.answer_display.text)
                    wrong = next(c.id for c in question.choices
                                 if c.id != question.answer["choice_id"])
                    must_reject(replace(question, answer=dict(question.answer, choice_id=wrong)),
                                generator)
                adapted += 1
            missing = set(forms[level]) - TWO_PART - shown
            require(not missing, "Forms without MCQs at {} L{}: {}".format(
                generator_id, level, sorted(missing)))
            print("  L{}: {} adapted, {} refused; mistakes {}".format(
                level, adapted, refused,
                ", ".join("{} {}".format(k, v) for k, v in sorted(mistakes.items()))))
            checked += adapted
    sheet = build_block_sheet(registry, [
        {"generator_id": "geometry.angles.basic_facts", "kind": "questions",
         "levels": [1, 2], "count": 4, "multiple_choice": True},
        {"generator_id": "geometry.angles.triangle", "kind": "questions",
         "levels": [1, 2, 3], "count": 6, "multiple_choice": True},
    ], "Angles — choose one answer", seed=20261005)
    report = export_worksheet(sheet, ROOT / "exports" / "specimens", answers=True)
    print("Validated MCQs:", checked)
    print("Specimen:", report["directory"])
    print("MCQ ANGLES PASS — visual review pending")


if __name__ == "__main__":
    main()