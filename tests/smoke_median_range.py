"""Known median and range cases, including the midpoint of an even data set."""
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
    from mathsgen.core import require
    from mathsgen.median_range import decimal_text, median_value

    require(median_value([Fraction(n) for n in (3, 1, 2)]) == 2, "Odd median failed")
    require(median_value([Fraction(n) for n in (1, 2, 3, 8)]) == Fraction(5, 2),
            "Even midpoint failed")
    require(median_value([Fraction(n) for n in (-5, 5)]) == 0, "Signed midpoint failed")
    require(decimal_text(Fraction(5, 2)) == "2.5", "Half formatting failed")
    require(decimal_text(Fraction(-13, 4)) == "-3.25", "Quarter formatting failed")
    require(decimal_text(Fraction(7)) == "7", "Integer formatting failed")

    generator = registry.get("data.averages.median_range")
    for level in range(1, 5):
        question = generator.generate(12345, level)
        generator.validate_independently(question)
        wrong = dict(question.answer, median="1000")
        try:
            generator.validate(replace(question, answer=wrong))
        except ValueError:
            pass
        else:
            raise AssertionError("Corrupted median accepted")
        print("Level {}: {}".format(level, question.prompt.text))
        print("Answer: " + question.answer_display.text)
    print("PASS: known medians and corrupt-answer rejection for all levels.")


if __name__ == "__main__":
    main()