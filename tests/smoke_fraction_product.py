"""Known products, quotients and cancellation structure for both operations."""
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
    from mathsgen.fraction_product import cancels, effective_right, expression_text

    require(effective_right(Fraction(3, 4), "divide") == Fraction(4, 3), "Reciprocal failed")
    require(effective_right(Fraction(3, 4), "multiply") == Fraction(3, 4), "Identity failed")
    require(cancels(Fraction(2, 3), Fraction(3, 4), "multiply"), "Missed cancellation")
    require(not cancels(Fraction(1, 3), Fraction(2, 5), "multiply"), "False cancellation")
    require(cancels(Fraction(2, 3), Fraction(2, 5), "divide"), "Missed divide cancellation")
    require(expression_text(Fraction(2, 3), Fraction(4, 5), "multiply") == "2/3 × 4/5",
            "Product text failed")
    require(expression_text(Fraction(2, 3), Fraction(-4, 5), "divide") == "2/3 ÷ (-4/5)",
            "Quotient text failed")

    for generator_id in ("number.fractions.multiplication", "number.fractions.division"):
        generator = registry.get(generator_id)
        for level in range(1, 5):
            question = generator.generate(12345, level)
            generator.validate_independently(question)
            try:
                generator.validate(
                    replace(question, answer={"kind": "rational", "value": "0"})
                )
            except ValueError:
                pass
            else:
                raise AssertionError("Corrupted answer accepted")
            print("Level {}: {}".format(level, question.prompt.text))
            print("Answer: " + question.answer_display.text)
        print(generator.info.title)
    print("PASS: known cases and corrupt-answer rejection for all levels.")


if __name__ == "__main__":
    main()