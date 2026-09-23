"""Check known reverse-percentage cases, misconceptions and exact money."""
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
    raise AssertionError("Incorrect question accepted")


def main():
    registry = load_engine()
    generator = registry.get("number.percentages.reverse")
    from mathsgen.reverse_percentage import prompt_for
    from fractions import Fraction

    for level in range(1, 5):
        question = generator.generate(12345, level)
        generator.validate_independently(question)
        print("Level {}: {}".format(level, question.prompt.text))
        print("Answer: " + question.answer_display.text)
        bad = replace(question, answer=dict(
            question.answer, pence=question.answer["pence"] + 100
        ))
        reject(generator.validate, bad)
        reject(generator.validate_independently, bad)
        reject(generator.validate, replace(
            question, prompt=replace(question.prompt, text="Incorrect prompt")
        ))

    # A 20% discount on £100 gives £80, not an original of £96.
    base = generator.generate(1, 1)
    parameters = {
        "percentage": "20", "direction": -1,
        "given_pence": 8000, "change_only": False,
    }
    from mathsgen.core import Content
    known = replace(
        base, parameters=parameters,
        prompt=prompt_for(Fraction(20), -1, 8000, False),
        answer={"kind": "money", "currency": "GBP", "pence": 10000},
        answer_display=Content("£100.00"),
    )
    generator.validate(known)
    generator.validate_independently(known)
    mistaken = replace(known, answer=dict(known.answer, pence=9600))
    reject(generator.validate, mistaken)
    reject(generator.validate_independently, mistaken)

    try:
        generator.generate(0, 1, {"round": True})
    except ValueError:
        pass
    else:
        raise AssertionError("Unsupported setting accepted")
    print("PASS: four structures, known discount and reverse-percent misconception.")
    print("PASS: corrupted answers/displays and unsupported settings rejected.")


if __name__ == "__main__":
    main()