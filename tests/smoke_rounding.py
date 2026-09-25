"""Known rounding cases, halfway boundaries and carries, for both modes."""
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
    from mathsgen.catalogue import source_registry
    registry = source_registry(registry)
    from mathsgen.core import require
    from mathsgen.rounding import (
        fixed_text, round_half_up, round_significant, significant_text,
    )

    require(round_half_up(Fraction("3.14159"), 2) == Fraction("3.14"), "Round down failed")
    require(round_half_up(Fraction("3.15"), 1) == Fraction("3.2"), "Halfway up failed")
    require(round_half_up(Fraction("2.999"), 2) == Fraction(3), "Carry failed")
    require(round_half_up(Fraction("-3.15"), 1) == Fraction("-3.2"), "Negative halfway failed")
    require(round_significant(Fraction("0.004567"), 2) == Fraction("0.0046"),
            "Leading-zero significant figures failed")
    require(round_significant(Fraction("3985"), 2) == Fraction(4000), "Whole-number carry failed")
    require(round_significant(Fraction("0.0999"), 2) == Fraction("0.1"),
            "Significant carry failed")
    require(fixed_text(Fraction(3), 2) == "3.00", "Zero padding failed")
    require(fixed_text(Fraction("3.2"), 3) == "3.200", "Decimal padding failed")
    require(significant_text(Fraction("0.0046"), 2) == "0.0046", "Significant text failed")
    require(significant_text(Fraction(4000), 2) == "4000", "Whole significant text failed")

    for generator_id in (
        "number.rounding.decimal_places", "number.rounding.significant_figures"
    ):
        generator = registry.get(generator_id)
        for level in range(1, 5):
            for seed in (11, 222, 3333):
                question = generator.generate(seed, level)
                generator.validate_independently(question)
            wrong = dict(question.answer, value="1")
            try:
                generator.validate(replace(question, answer=wrong))
            except ValueError:
                pass
            else:
                raise AssertionError("Corrupted rounding accepted")
            print("Level {}: {}".format(level, question.prompt.text))
            print("Answer: " + question.answer_display.text)
        print(generator.info.title)
    print("PASS: known rounding, boundaries and corrupt-answer rejection.")


if __name__ == "__main__":
    main()