"""Known factorisations, including the two-letter and common-factor cases."""
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
    from mathsgen.difference_of_squares import expression_text, factorised_text

    require(expression_text(1, 1, 3, ("x", None)) == "x^2 - 9", "Plain expression failed")
    require(factorised_text(1, 1, 3, ("x", None)) == "(x + 3)(x - 3)", "Plain factors failed")
    require(expression_text(1, 2, 3, ("x", None)) == "4x^2 - 9", "Coefficient expression failed")
    require(factorised_text(1, 2, 3, ("x", None)) == "(2x + 3)(2x - 3)",
            "Coefficient factors failed")
    require(expression_text(1, 1, 1, ("x", "y")) == "x^2 - y^2", "Two-letter expression failed")
    require(expression_text(2, 1, 5, ("x", None)) == "2x^2 - 50", "Common-factor expression failed")
    require(factorised_text(2, 1, 5, ("x", None)) == "2(x + 5)(x - 5)",
            "Common-factor factors failed")

    generator = registry.get("algebra.factorising.difference_of_squares")
    for level in range(1, 5):
        question = generator.generate(12345, level)
        generator.validate_independently(question)
        wrong = dict(question.answer, second=question.answer["second"] + 1)
        try:
            generator.validate(replace(question, answer=wrong))
        except ValueError:
            pass
        else:
            raise AssertionError("Corrupted factorisation accepted")
        print("Level {}: {}".format(level, question.prompt.text))
        print("Answer: " + question.answer_display.text)
    print("PASS: known factorisations and corrupt-answer rejection for all levels.")


if __name__ == "__main__":
    main()