"""Check index structures, common misconceptions and corrupted displays."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from fractions import Fraction
from launch_mathsgen import load_engine


def expect_rejection(check, question):
    try:
        check(question)
    except ValueError:
        return
    raise AssertionError("Corrupted question accepted")


def main():
    registry = load_engine()
    generator = registry.get("number.indices.product")
    for level in range(1, 5):
        question = generator.generate(12345, level)
        generator.validate_independently(question)
        print("Level {}: {}".format(level, question.prompt.text))
        print("Answer: " + question.answer_display.text)

        exponents = [
            Fraction(value) for value in question.parameters["exponents"]
        ]
        mistaken = Fraction(1)
        for exponent in exponents:
            mistaken *= exponent
        correct = Fraction(question.answer["exponent"])
        if mistaken == correct:
            mistaken = correct + 1
        corrupted = replace(
            question,
            answer=dict(question.answer, exponent=str(mistaken)),
        )
        expect_rejection(generator.validate, corrupted)
        expect_rejection(generator.validate_independently, corrupted)

        expect_rejection(
            generator.validate,
            replace(question, prompt=replace(
                question.prompt, text="Incorrect displayed question"
            )),
        )
        expect_rejection(
            generator.validate,
            replace(question, answer_display=replace(
                question.answer_display, math_tex="x^{999}"
            )),
        )

    for difficulty, settings in (
        (0, None), (5, None), (1, {"unexpected": True}),
    ):
        try:
            generator.generate(0, difficulty, settings)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid request accepted")

    print("PASS: four structures and independent wrong-answer rejection.")
    print("PASS: display corruption and invalid requests rejected.")


if __name__ == "__main__":
    main()