"""Check both solutions, rearrangement, known roots and display integrity."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from launch_mathsgen import load_engine


def reject(check, question):
    try:
        check(question)
    except ValueError:
        return
    raise AssertionError("Incorrect quadratic accepted")


def main():
    registry = load_engine()
    generator = registry.get("algebra.quadratic.factorisable_monic")
    for level in range(1, 5):
        question = generator.generate(12345, level)
        generator.validate_independently(question)
        print("Level {}: {}".format(level, question.prompt.text))
        print("Answer: " + question.answer_display.text)
        roots = question.answer["values"]
        for incorrect in (
            roots[:1],
            [roots[0], roots[0]],
            [str(int(roots[0]) - 1), roots[1]],
        ):
            bad = replace(question, answer=dict(question.answer, values=incorrect))
            reject(generator.validate, bad)
            reject(generator.validate_independently, bad)
        reject(generator.validate, replace(
            question, answer_display=replace(question.answer_display, text="x = 99")
        ))

    from mathsgen.quadratic_monic import prompt_for, display_for
    base = generator.generate(0, 4)
    left, right = [1, 4, -7], [0, 5, -1]
    # Rearranges to x^2 - x - 6 = 0.
    known = replace(
        base, parameters={"left": left, "right": right},
        prompt=prompt_for(left, right),
        answer={"kind": "roots", "variable": "x", "values": ["-2", "3"]},
        answer_display=display_for(["-2", "3"]),
    )
    generator.validate(known)
    generator.validate_independently(known)
    print("PASS: four levels, missing/duplicate/wrong roots and rearrangement case.")


if __name__ == "__main__":
    main()