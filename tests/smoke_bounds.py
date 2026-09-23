"""Known bounds, including the compound-measure quotient at level 4."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from fractions import Fraction
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.bounds import lower_bound, upper_bound
    from mathsgen.core import require
    from mathsgen.rounding import round_significant

    require(lower_bound(24, Fraction(1)) == Fraction("23.5"), "Whole lower bound failed")
    require(upper_bound(24, Fraction(1)) == Fraction("24.5"), "Whole upper bound failed")
    require(lower_bound(300, Fraction(100)) == 250, "Nearest hundred lower failed")
    require(upper_bound(Fraction("4.6"), Fraction(1, 10)) == Fraction("4.65"),
            "Decimal upper bound failed")

    # A distance of 100 m to the nearest metre, over a time of 20 s to the
    # nearest second, has greatest speed 100.5 / 19.5, which recurs and is
    # therefore stored exactly and displayed rounded.
    fastest = upper_bound(100, Fraction(1)) / lower_bound(20, Fraction(1))
    require(fastest == Fraction(201, 39), "Compound upper bound failed")
    require(round_significant(fastest, 3) == Fraction("5.15"), "Compound rounding failed")

    generator = registry.get("number.bounds.measurement")
    for level in range(1, 5):
        for seed in (7, 88, 999):
            question = generator.generate(seed, level)
            generator.validate_independently(question)
        wrong = dict(question.answer, upper="1")
        try:
            generator.validate(replace(question, answer=wrong))
        except ValueError:
            pass
        else:
            raise AssertionError("Corrupted bound accepted")
        print("Level {}: {}".format(level, question.prompt.text))
        print("Answer: " + question.answer_display.text)
    print("PASS: known bounds and corrupt-answer rejection for all levels.")


if __name__ == "__main__":
    main()