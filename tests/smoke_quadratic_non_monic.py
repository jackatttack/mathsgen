"""Check rational solutions, missing roots and scalar-multiple rejection."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from fractions import Fraction
from launch_mathsgen import load_engine


def reject(check, question):
    try:
        check(question)
    except ValueError:
        return
    raise AssertionError("Invalid quadratic accepted")


def main():
    registry = load_engine()
    generator = registry.get("algebra.quadratic.factorisable_non_monic")
    for level in range(1, 5):
        seed = 12345
        question = generator.generate(seed, level)
        while "context" in question.parameters:  # worded: smoke_algebra_contexts_2.py
            seed += 1
            question = generator.generate(seed, level)
        generator.validate_independently(question)
        print("Level {}: {}".format(level, question.prompt.text))
        print("Answer: " + question.answer_display.text)
        roots = question.answer["values"]
        for values in (roots[:1], [roots[0], roots[0]],
                       [str(Fraction(roots[0]) - 1), roots[1]]):
            bad = replace(question, answer=dict(question.answer, values=values))
            reject(generator.validate, bad)
            reject(generator.validate_independently, bad)
        scaled = {
            key: [2 * value for value in row]
            for key, row in question.parameters.items()
        }
        reject(generator.validate, replace(question, parameters=scaled))

    from mathsgen.quadratic_monic import prompt_for
    from mathsgen.quadratic_non_monic import display_for
    # (2x - 1)(3x + 2) = 6x^2 + x - 2.
    base = generator.generate(0, 3)
    roots = [Fraction(-2, 3), Fraction(1, 2)]
    known = replace(
        base, parameters={"left": [6, 1, -2], "right": [0, 0, 0]},
        prompt=prompt_for([6, 1, -2], [0, 0, 0]),
        answer={"kind": "roots", "variable": "x", "values": ["-2/3", "1/2"]},
        answer_display=display_for(roots),
    )
    generator.validate(known)
    generator.validate_independently(known)
    print("PASS: four structures, known rational roots and corruption rejection.")


if __name__ == "__main__":
    main()