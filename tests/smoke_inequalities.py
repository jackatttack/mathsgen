"""Known inequalities and corrupt-answer rejection for both new families.

Corruption perturbs the real answer rather than substituting a fixed value,
because a constant can coincide with the true answer and make a rejection
test pass without testing anything.
"""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from fractions import Fraction
from launch_mathsgen import load_engine


def reject(generator, question, answer, message):
    """Require that a deliberately wrong answer fails validation."""
    try:
        generator.validate(replace(question, answer=answer))
    except ValueError:
        return
    raise AssertionError(message)


def check_inequalities(registry, require):
    generator = registry.get("algebra.inequalities.linear")

    for level in range(1, 5):
        for seed in (5, 66, 777):
            question = generator.generate(seed, level)
            generator.validate_independently(question)
        seed = 777
        while "context" in question.parameters:
            seed += 1
            question = generator.generate(seed, level)

        if level == 4:
            values = question.answer["values"]
            reject(generator, question,
                   dict(question.answer, values=values[:-1]),
                   "Truncated integer list accepted")
            reject(generator, question,
                   dict(question.answer, values=values + [values[-1] + 1]),
                   "Extended integer list accepted")
        else:
            boundary = Fraction(question.answer["boundary"])
            reject(generator, question,
                   dict(question.answer, boundary=str(boundary + 1)),
                   "Shifted boundary accepted")
            # The reversal at level 3 is the whole point of that level, so
            # a flipped direction must be rejected at every level.
            flipped = {"<": ">", "<=": ">=", ">": "<", ">=": "<="}
            reject(generator, question,
                   dict(question.answer, operator=flipped[question.answer["operator"]]),
                   "Reversed direction accepted")

        print("Level {}: {}".format(level, question.prompt.text))
        print("Answer: " + question.answer_display.text)

    # Level 3 must reverse the displayed relation; the others must not.
    for level in range(1, 4):
        seed = 31
        question = generator.generate(seed, level)
        while "context" in question.parameters:
            seed += 1
            question = generator.generate(seed, level)
        reversed_direction = (
            question.answer["operator"] != question.parameters["operator"]
        )
        require(reversed_direction == (level == 3),
                "Direction change does not match level {}".format(level))
    print(generator.info.title)


def check_index_rules(registry, require):
    generator = registry.get("number.indices.rules")
    from mathsgen.index_rules import exact_value

    require(exact_value(7, Fraction(0)) == 1, "Zero index failed")
    require(exact_value(5, Fraction(-2)) == Fraction(1, 25), "Negative index failed")
    require(exact_value(64, Fraction(1, 3)) == 4, "Cube root failed")
    require(exact_value(81, Fraction(3, 2)) == 729, "Fractional index failed")
    require(exact_value(8, Fraction(-2, 3)) == Fraction(1, 4),
            "Negative fractional index failed")

    for base, exponent in ((10, Fraction(1, 2)), (7, Fraction(1, 3))):
        try:
            exact_value(base, exponent)
        except ValueError:
            continue
        raise AssertionError("Irrational root accepted for {}".format(base))

    for level in range(1, 5):
        for seed in (5, 66, 777):
            question = generator.generate(seed, level)
            generator.validate_independently(question)
        for seed in range(60):
            question = generator.generate(seed, level)
            if "form" not in question.parameters:
                break
        else:
            raise AssertionError("Bare index form was not generated")
        value = Fraction(question.answer["value"])
        reject(generator, question,
               dict(question.answer, value=str(value + 1)),
               "Perturbed value accepted")
        reject(generator, question,
               dict(question.answer, value=str(1 / value)) if value != 1
               else dict(question.answer, value="2"),
               "Reciprocal value accepted")
        print("Level {}: {}".format(level, question.prompt.text))
        print("Answer: " + question.answer_display.text)
    print(generator.info.title)


def main():
    registry = load_engine()
    from mathsgen.core import require

    check_inequalities(registry, require)
    check_index_rules(registry, require)
    print("PASS: known values, level structure and corrupt-answer rejection.")


if __name__ == "__main__":
    main()