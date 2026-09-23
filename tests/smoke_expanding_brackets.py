"""Known expansions, bracket wording and corrupt-answer rejection."""
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
    from mathsgen.expanding_brackets import expand, linear_text, polynomial

    require(expand((1, 3), (1, 5)) == [1, 8, 15], "Positive expansion failed")
    require(expand((1, -3), (1, 5)) == [1, 2, -15], "Signed expansion failed")
    require(expand((1, -4), (1, -4)) == [1, -8, 16], "Squared expansion failed")
    require(expand((3, 2), (1, -5)) == [3, -13, -10], "Non-monic expansion failed")
    require(linear_text(1, -4) == "(x - 4)", "Monic bracket text failed")
    require(linear_text(3, 2) == "(3x + 2)", "Non-monic bracket text failed")
    require(polynomial([1, -8, 16]) == "x^2 - 8x + 16", "Quadratic text failed")

    generator = registry.get("algebra.expanding.double_brackets")
    for level in range(1, 5):
        question = generator.generate(12345, level)
        generator.validate_independently(question)
        wrong = {"kind": "polynomial", "coefficients": [1, 1, 1]}
        try:
            generator.validate(replace(question, answer=wrong))
        except ValueError:
            pass
        else:
            raise AssertionError("Corrupted expansion accepted")
        print("Level {}: {}".format(level, question.prompt.text))
        print("Answer: " + question.answer_display.text)
    print("PASS: known expansions and corrupt-answer rejection for all levels.")


if __name__ == "__main__":
    main()