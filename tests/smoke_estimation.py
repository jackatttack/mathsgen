"""Known estimates, rounding each value to one significant figure first."""
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
    from mathsgen.estimation import estimate_for, rounded_values

    require(rounded_values([Fraction(312), Fraction(48)]) == [300, 50],
            "Whole rounding failed")
    require(estimate_for([Fraction(312), Fraction(48)], "product") == 15000,
            "Product estimate failed")
    require(estimate_for([Fraction(612), Fraction(29)], "quotient") == 20,
            "Quotient estimate failed")
    require(rounded_values([Fraction("0.038")]) == [Fraction("0.04")],
            "Small rounding failed")
    require(estimate_for([Fraction(41), Fraction("0.19")], "quotient") == 200,
            "Small divisor estimate failed")

    for generator_id in ("number.estimation.product", "number.estimation.quotient"):
        generator = registry.get(generator_id)
        for level in range(1, 5):
            for seed in (6, 77, 888):
                question = generator.generate(seed, level)
                generator.validate_independently(question)
            wrong = dict(
                question.answer,
                value=str(Fraction(question.answer["value"]) + 1),
            )
            try:
                generator.validate(replace(question, answer=wrong))
            except ValueError:
                pass
            else:
                raise AssertionError("Corrupted estimate accepted")
            print("Level {}: {}".format(level, question.prompt.text))
            print("Answer: " + question.answer_display.text)
        print(generator.info.title)
    print("PASS: known estimates and corrupt-answer rejection for all levels.")


if __name__ == "__main__":
    main()