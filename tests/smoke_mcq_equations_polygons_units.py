"""Linear equations (bare L1-2), polygon angles (L1-3 regular) and unit
conversion (L1-4) MCQs.

Checks: every expected form adapts; forms meant to stay written never do;
equations and units show the correct option exactly as the original answer;
no two options look the same; a tampered answer key is rejected.
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
from mathsgen.unit_conversion import CAPACITY_CASES
from mathsgen.blocks import build_block_sheet
from mathsgen.export import export_worksheet


SEEDS = 120
LINEAR = "algebra.linear.two_sided"
POLYGONS = "geometry.angles.polygons"
UNITS = "number.units.area_volume"
CASES = (
    (LINEAR, (1, 2), True),
    (POLYGONS, (1, 2, 3), False),
    (UNITS, (1, 2, 3, 4), True),
)
EXPECTED_FORMS = {
    (LINEAR, 1): {"bare"}, (LINEAR, 2): {"bare"},
    (POLYGONS, 2): {"interior", "exterior"}, (POLYGONS, 3): {"interior", "exterior"},
    (UNITS, 3): {"to_smaller", "to_larger"}, (UNITS, 4): set(CAPACITY_CASES),
}
STAYS_WRITTEN = {"quadrilateral_exterior"}


def form_key(question):
    p = question.parameters
    if question.generator_id == LINEAR:
        return "bare" if set(p) == {"a", "b", "c", "d"} else "other"
    for key in ("case", "direction", "angle_kind"):
        if key in p:
            return p[key]
    return p.get("form", "sum")


def must_reject(question, generator):
    try:
        validate_multiple_choice(question, generator)
    except Exception:
        return
    raise AssertionError("Tampered MCQ accepted")


def main():
    registry = build_registry()
    checked = 0
    for generator_id, levels, exact_display in CASES:
        generator = registry.get(generator_id)
        for level in levels:
            adapted, refused, mistakes, shown = 0, 0, {}, set()
            for seed in range(SEEDS):
                original = generator.generate(seed, level)
                form = form_key(original)
                question = make_multiple_choice(original)
                if form in STAYS_WRITTEN:
                    require(question is None, "Written-only form adapted: " + form)
                    continue
                if question is None:
                    refused += 1
                    continue
                validate_multiple_choice(question, generator, independent=form not in shown)
                require(make_multiple_choice(original) == question, "Non-reproducible options")
                correct = next(c for c in question.choices
                               if c.id == question.answer["choice_id"])
                if exact_display:
                    require(correct.content.text == original.answer_display.text,
                            "Correct option {!r}, original {!r}".format(
                                correct.content.text, original.answer_display.text))
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
            require(adapted > 0, "No MCQs at {} L{}".format(generator_id, level))
            missing = EXPECTED_FORMS.get((generator_id, level), set()) - shown
            require(not missing, "Forms without MCQs at {} L{}: {}".format(
                generator_id, level, sorted(missing)))
            print("  L{}: {} adapted, {} refused; mistakes {}".format(
                level, adapted, refused,
                ", ".join("{} {}".format(k, v) for k, v in sorted(mistakes.items()))))
            checked += adapted
    require(make_multiple_choice(registry.get(LINEAR).generate(1, 3)) is None,
            "Linear L3 silently adapted")
    require(make_multiple_choice(registry.get(POLYGONS).generate(1, 4)) is None,
            "Polygons L4 silently adapted")
    sheet = build_block_sheet(registry, [
        {"generator_id": LINEAR, "kind": "questions", "levels": [1, 2],
         "count": 4, "multiple_choice": True},
        {"generator_id": POLYGONS, "kind": "questions", "levels": [1, 2, 3],
         "count": 4, "multiple_choice": True},
        {"generator_id": UNITS, "kind": "questions", "levels": [1, 2, 3, 4],
         "count": 6, "multiple_choice": True},
    ], "Equations, polygons and units — choose one answer", seed=20261006)
    report = export_worksheet(sheet, ROOT / "exports" / "specimens", answers=True)
    print("Validated MCQs:", checked)
    print("Specimen:", report["directory"])
    print("MCQ EQUATIONS POLYGONS UNITS PASS — visual review pending")


if __name__ == "__main__":
    main()