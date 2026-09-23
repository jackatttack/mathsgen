"""Known index results and corrupt-answer rejection for both laws."""
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
    from mathsgen.index_laws import IndexPower, IndexQuotient

    require(IndexQuotient.combine([Fraction(7), Fraction(3)]) == 4, "Quotient failed")
    require(IndexQuotient.combine([Fraction(3), Fraction(7)]) == -4, "Negative quotient failed")
    require(IndexQuotient.combine([Fraction(1, 2), Fraction(1, 3)]) == Fraction(1, 6),
            "Fractional quotient failed")
    require(IndexPower.combine([Fraction(3), Fraction(2)]) == 6, "Power failed")
    require(IndexPower.combine([Fraction(3), Fraction(-2)]) == -6, "Negative power failed")
    require(IndexPower.combine([Fraction(1, 2), Fraction(4)]) == 2, "Fractional power failed")

    for generator_id in ("number.indices.quotient", "number.indices.power_of_power"):
        generator = registry.get(generator_id)
        for level in range(1, 5):
            question = generator.generate(12345, level)
            generator.validate_independently(question)
            wrong = dict(question.answer, exponent="99")
            try:
                generator.validate(replace(question, answer=wrong))
            except ValueError:
                pass
            else:
                raise AssertionError("Corrupted index accepted")
            print("Level {}: {}".format(level, question.prompt.text))
            print("Answer: " + question.answer_display.text)
        print(generator.info.title)
    print("PASS: known index results and corrupt-answer rejection for all levels.")


if __name__ == "__main__":
    main()