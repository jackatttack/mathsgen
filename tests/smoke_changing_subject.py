"""Known rearrangements, including the factorising case, plus rejection checks."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import require
    from mathsgen.changing_subject import (
        answer_text, combine, make_term, rearranged, side_text,
    )

    # y = 3x + 7 rearranges to x = (y - 7)/3.
    left = [make_term(1, ["y"])]
    right = [make_term(3, [], True), make_term(7)]
    numerator, denominator = rearranged(left, right)
    require(answer_text(numerator, denominator) == "x = (y - 7)/3", "Two-step failed")

    # p = 12 - 5x rearranges to x = (12 - p)/5.
    left = [make_term(1, ["p"])]
    right = [make_term(12), make_term(-5, [], True)]
    numerator, denominator = rearranged(left, right)
    require(answer_text(numerator, denominator) == "x = (12 - p)/5", "Negative case failed")

    # ax + 12 = bx + 5 rearranges to x = -7/(a - b), collecting and factorising.
    left = [make_term(1, ["a"], True), make_term(12)]
    right = [make_term(1, ["b"], True), make_term(5)]
    numerator, denominator = rearranged(left, right)
    require(side_text(denominator) == "a - b", "Factorised denominator failed")
    require(answer_text(numerator, denominator) == "x = -7/(a - b)", "Factorising failed")

    # t = 4sx - 11m rearranges to x = (11m + t)/(4s): the denominator must be
    # bracketed, or the plain text reads as a division followed by a product.
    left = [make_term(1, ["t"])]
    right = [make_term(4, ["s"], True), make_term(-11, ["m"])]
    numerator, denominator = rearranged(left, right)
    require(answer_text(numerator, denominator) == "x = (11m + t)/(4s)",
            "Coefficient denominator bracketing failed")

    # A bare letter or a bare number needs no brackets.
    left = [make_term(1, ["y"])]
    right = [make_term(1, ["a"], True), make_term(2)]
    numerator, denominator = rearranged(left, right)
    require(answer_text(numerator, denominator) == "x = (y - 2)/a",
            "Single-letter denominator should not be bracketed")

    require(len(combine([make_term(12), make_term(-5)])) == 1, "Numeric merge failed")
    require(combine([make_term(4), make_term(-4)]) == [], "Cancellation failed")

    generator = registry.get("algebra.rearranging.changing_subject")
    for level in range(1, 5):
        question = generator.generate(12345, level)
        generator.validate_independently(question)
        wrong = dict(question.answer, numerator=[make_term(99)])
        try:
            generator.validate(replace(question, answer=wrong))
        except ValueError:
            pass
        else:
            raise AssertionError("Corrupted rearrangement accepted")
        print("Level {}: {}".format(level, question.prompt.text))
        print("Answer: " + question.answer_display.text)
    print("PASS: known rearrangements and corrupt-answer rejection for all levels.")


if __name__ == "__main__":
    main()