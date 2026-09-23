"""Check option semantics, display consistency and answer-key corruption."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import Content, require
    from mathsgen.index_meaning import candidate_descriptors, equivalent_options
    from fractions import Fraction

    # Exercise every mathematical case in the current option banks.
    cases = {
        1: [Fraction(1, n) for n in (2, 3, 4, 5)],
        2: [Fraction(2, 3), Fraction(3, 2), Fraction(3, 4), Fraction(2, 5)],
        3: [Fraction(-n) for n in (2, 3, 4, 5)],
        4: [Fraction(-1, 2), Fraction(-1, 3), Fraction(-2, 3), Fraction(-3, 2)],
    }
    for level, exponents in cases.items():
        for exponent in exponents:
            descriptors = tuple(
                (kind, str(value)) for kind, value in candidate_descriptors(exponent, level)
            )
            require(equivalent_options(str(exponent), descriptors) == (
                True, False, False, False, False
            ), "Option bank has an incorrect or ambiguous key")

    generator = registry.get("number.indices.meaning_mcq")
    for level in range(1, 5):
        question = generator.generate(12345, level)
        generator.validate_independently(question)
        wrong_id = next(choice.id for choice in question.choices
                        if choice.id != question.answer["choice_id"])
        corruptions = [
            replace(question, answer={"kind": "choice", "choice_id": wrong_id}),
            replace(question, choices=(
                replace(question.choices[0], content=Content("incorrect", "999")),
            ) + question.choices[1:]),
        ]
        for corrupted in corruptions:
            try:
                generator.validate(corrupted)
            except ValueError:
                pass
            else:
                raise AssertionError("Corrupted question accepted")
        print("Level {}: {}".format(level, question.prompt.text))
        for index, choice in enumerate(question.choices):
            print("  {}. {}".format(chr(65 + index), choice.content.text))
        print("Answer: " + question.answer_display.text)
    print("PASS: all 16 mathematical cases and answer/display corruption checks.")


if __name__ == "__main__":
    main()