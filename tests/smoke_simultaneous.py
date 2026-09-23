"""Check simultaneous-equation structures and reject incorrect or singular data."""
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
    raise AssertionError("Invalid question was accepted")


def main():
    registry = load_engine()
    generator = registry.get("algebra.simultaneous.linear")
    for level in range(1, 5):
        seed = 12345
        question = generator.generate(seed, level)
        while "context" in question.parameters:  # worded: smoke_simultaneous_contexts.py
            seed += 1
            question = generator.generate(seed, level)
        generator.validate_independently(question)
        print("Level {}: {}".format(level, question.prompt.text))
        print("Answer: " + question.answer_display.text)

        values = dict(question.answer["values"])
        values["x"] = str(Fraction(values["x"]) + 1)
        bad = replace(question, answer={"kind": "variable_values", "values": values})
        reject(generator.validate, bad)
        reject(generator.validate_independently, bad)

        row = list(question.parameters["rows"][0])
        singular = replace(question, parameters={"rows": [row, list(row)]})
        reject(generator.validate, singular)
        reject(generator.validate_independently, singular)

        bad_prompt = replace(
            question, prompt=replace(question.prompt, text="Unrelated question")
        )
        reject(generator.validate, bad_prompt)

    question = generator.generate(12, 1)
    known = replace(
        question,
        parameters={"rows": [[2, 1, 7], [1, 1, 5]]},
        answer={"kind": "variable_values", "values": {"x": "2", "y": "3"}},
    )
    generator.validate_independently(known)
    for level, settings in ((0, None), (5, None), (1, {"unused": True})):
        try:
            generator.generate(0, level, settings)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid request accepted")
    print("PASS: four levels, known solution, singular systems and corruption checks.")


if __name__ == "__main__":
    main()