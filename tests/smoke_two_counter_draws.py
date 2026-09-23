"""Known cases distinguish replacement, order and complement reasoning."""
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
    from mathsgen.two_counter_draws import probability

    counts = {"red": 2, "blue": 3, "green": 1}
    cases = [
        ("same", ["red"], Fraction(1, 9), Fraction(1, 15)),
        ("ordered", ["red", "blue"], Fraction(1, 6), Fraction(1, 5)),
        ("either_order", ["red", "blue"], Fraction(1, 3), Fraction(2, 5)),
        ("at_least_one", ["red"], Fraction(5, 9), Fraction(3, 5)),
    ]
    for event, targets, with_answer, without_answer in cases:
        require(probability(counts, targets, event, True) == with_answer, "Replacement case failed")
        require(probability(counts, targets, event, False) == without_answer, "No-replacement case failed")

    for suffix in ("with_replacement", "without_replacement"):
        generator = registry.get("probability.two_draws." + suffix)
        for level in range(1, 5):
            question = generator.generate(12345, level)
            generator.validate_independently(question)
            try:
                generator.validate(replace(
                    question, answer={"kind": "rational", "value": "1"}
                ))
            except ValueError:
                pass
            else:
                raise AssertionError("Corrupt answer accepted")
        sample = generator.generate(12345, 3)
        print(sample.prompt.text)
        print("Answer: " + sample.answer_display.text)
    print("PASS: known replacement/order/complement cases and corrupt-answer rejection.")


if __name__ == "__main__":
    main()