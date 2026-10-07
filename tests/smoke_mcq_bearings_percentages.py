"""Back bearings (L1) and percentage-multiplier (L1-4) MCQs.

Every form at every supported level must produce MCQs. The correct option
must display exactly as the original answer (054°, £243.00, 1.025), no two
options may look the same on paper, a tampered answer key must be rejected,
and bearings L2 must stay a written question.
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
from mathsgen.percentage_multiplier import FIND_FORMS
from mathsgen.blocks import build_block_sheet
from mathsgen.export import export_worksheet


SEEDS = 160
CASES = (
    ("geometry.bearings.bearings", (1,), {1: ("back",)}),
    ("number.percentages.multiplier", (1, 2, 3, 4), FIND_FORMS),
)


def correct_choice(question):
    return next(c for c in question.choices if c.id == question.answer["choice_id"])


def must_reject(question, generator):
    try:
        validate_multiple_choice(question, generator)
    except Exception:
        return
    raise AssertionError("Tampered MCQ accepted")


def main():
    registry = build_registry()
    checked = 0
    for generator_id, levels, forms in CASES:
        generator = registry.get(generator_id)
        for level in levels:
            adapted, refused, mistakes, shown = 0, 0, {}, set()
            for seed in range(SEEDS):
                original = generator.generate(seed, level)
                question = make_multiple_choice(original)
                if question is None:
                    refused += 1
                    continue
                form = original.parameters["form"]
                validate_multiple_choice(question, generator, independent=form not in shown)
                require(make_multiple_choice(original) == question, "Non-reproducible options")
                shown_answer = correct_choice(question).content.text
                require(shown_answer == original.answer_display.text,
                        "Correct option {!r} differs from the original answer {!r}".format(
                            shown_answer, original.answer_display.text))
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
            missing = set(forms[level]) - shown
            require(not missing, "Forms without MCQs at {} L{}: {}".format(
                generator_id, level, sorted(missing)))
            print("  L{}: {} adapted, {} refused; mistakes {}".format(
                level, adapted, refused,
                ", ".join("{} {}".format(k, v) for k, v in sorted(mistakes.items()))))
            checked += adapted
    bearings = registry.get("geometry.bearings.bearings")
    require(make_multiple_choice(bearings.generate(1, 2)) is None,
            "Bearings L2 silently adapted")
    sheet = build_block_sheet(registry, [
        {"generator_id": "geometry.bearings.bearings", "kind": "questions",
         "levels": [1], "count": 4, "multiple_choice": True},
        {"generator_id": "number.percentages.multiplier", "kind": "questions",
         "levels": [1, 2, 3, 4], "count": 8, "multiple_choice": True},
    ], "Bearings and percentage change — choose one answer", seed=20261004)
    report = export_worksheet(sheet, ROOT / "exports" / "specimens", answers=True)
    print("Validated MCQs:", checked)
    print("Specimen:", report["directory"])
    print("MCQ BEARINGS AND PERCENTAGES PASS — visual review pending")


if __name__ == "__main__":
    main()