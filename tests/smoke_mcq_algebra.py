"""Polynomial MCQs: like terms L1-4, and one- and two-bracket expansion via expanding L1.

The engine compares options by exact collected form. This smoke checks every
emitted option independently with SymPy: exactly one option equals the
expanded question, and no two options are equivalent. It also checks that
worded forms and expanding level 2 are refused, and that a tampered answer
key is rejected. One example is printed per bracket form (source level).
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
from mathsgen.algebra_basics import sympy_terms
from mathsgen import worded
from mathsgen.blocks import build_block_sheet
from mathsgen.export import export_worksheet


SEEDS = 120
CASES = (
    ("algebra.expressions.like_terms", (1, 2, 3, 4)),
    ("algebra.expanding.double_brackets", (1,)),
)


def original_expression(question):
    """The written question rebuilt independently in SymPy."""
    import sympy
    p = question.parameters
    if "inner" in p:  # dispatch family: the source's own parameters
        p = p["inner"]
    if "terms" in p:
        return sympy_terms(p["terms"])
    total = sympy.Integer(0)
    for multiplier, inner in p["brackets"]:
        total += sympy_terms([multiplier]) * sympy_terms(inner)
    return sympy.expand(total)


def check_options_independently(original, question):
    import sympy
    target = original_expression(original)
    options = [sympy_terms(item["terms"])
               for item in question.answer["multiple_choice"]["options"]]
    matches = sum(sympy.expand(option - target) == 0 for option in options)
    require(matches == 1, "SymPy finds {} correct options".format(matches))
    for i in range(len(options)):
        for j in range(i + 1, len(options)):
            require(sympy.expand(options[i] - options[j]) != 0,
                    "SymPy finds equivalent options")


def must_reject(question, generator):
    try:
        validate_multiple_choice(question, generator)
    except Exception:
        return
    raise AssertionError("Tampered MCQ accepted")


def main():
    registry = build_registry()
    checked = 0
    for generator_id, levels in CASES:
        generator = registry.get(generator_id)
        for level in levels:
            adapted, worded_count, mistakes, shown = 0, 0, {}, set()
            for seed in range(SEEDS):
                original = generator.generate(seed, level)
                question = make_multiple_choice(original)
                if worded.is_worded(original):
                    require(question is None, "Worded form silently adapted")
                    worded_count += 1
                    continue
                if question is None:
                    continue
                validate_multiple_choice(question, generator, independent=adapted == 0)
                check_options_independently(original, question)
                require(make_multiple_choice(original) == question, "Non-reproducible options")
                for item in question.answer["multiple_choice"]["options"]:
                    if item["mistake"]:
                        mistakes[item["mistake"]] = mistakes.get(item["mistake"], 0) + 1
                form = original.parameters.get("source_level")
                if form not in shown:
                    shown.add(form)
                    print("{} L{}".format(generator_id, level), original.prompt.text)
                    print(" | ".join(chr(65 + i) + ": " + choice.content.text
                                     for i, choice in enumerate(question.choices)))
                    print("Answer:", question.answer_display.text)
                    wrong = next(c.id for c in question.choices
                                 if c.id != question.answer["choice_id"])
                    must_reject(replace(question, answer=dict(question.answer, choice_id=wrong)),
                                generator)
                adapted += 1
            require(adapted > 0, "No MCQs at {} L{}".format(generator_id, level))
            print("  L{}: {} adapted / {} bare ({} worded refused); mistakes {}".format(
                level, adapted, SEEDS - worded_count, worded_count,
                ", ".join("{} {}".format(k, v) for k, v in sorted(mistakes.items()))))
            checked += adapted
    expanding = registry.get("algebra.expanding.double_brackets")
    require(make_multiple_choice(expanding.generate(1, 2)) is None,
            "Unsupported expanding level silently adapted")
    sheet = build_block_sheet(registry, [
        {"generator_id": "algebra.expressions.like_terms", "kind": "questions",
         "levels": [1, 2, 3, 4], "count": 8, "multiple_choice": True},
        {"generator_id": "algebra.expanding.double_brackets", "kind": "questions",
         "levels": [1], "count": 6, "multiple_choice": True},
    ], "Simplifying and expanding — choose one answer", seed=20261003)
    report = export_worksheet(sheet, ROOT / "exports" / "specimens", answers=True)
    print("Validated MCQs:", checked)
    print("Specimen:", report["directory"])
    print("MCQ ALGEBRA PASS — visual review pending")


if __name__ == "__main__":
    main()