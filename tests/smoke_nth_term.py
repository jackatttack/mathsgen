"""Check sample structures and rejection of a shifted starting-index answer."""
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
    from mathsgen.core import rational_text

    for generator_id in ("algebra.sequences.linear_nth", "algebra.sequences.quadratic_nth"):
        generator = registry.get(generator_id)
        for level in range(1, 5):
            # Keep the original formula-recovery test on a bare question.
            question = next(
                q for seed in range(12345, 12445)
                for q in (generator.generate(seed, level),)
                if "context" not in q.parameters
            )
            generator.validate_independently(question)
            print(question.prompt.text)
            print("Answer: " + question.answer_display.text)
            # A common mistake is reporting the formula for n starting at 0.
            a, b, c = map(Fraction, question.answer["coefficients_descending"])
            wrong = dict(question.answer)
            wrong["coefficients_descending"] = [
                rational_text(a), rational_text(2 * a + b), rational_text(a + b + c)
            ]
            try:
                generator.validate(replace(question, answer=wrong))
            except ValueError:
                pass
            else:
                raise AssertionError("Wrong starting-index answer accepted")
    print("PASS: all eight structures and starting-index error rejection.")


if __name__ == "__main__":
    main()