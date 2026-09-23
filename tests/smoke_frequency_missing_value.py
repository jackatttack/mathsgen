"""Known solution, zero-frequency ambiguity and displayed-table corruption."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import Content, rational_text
    from mathsgen.frequency_missing_value import presentation
    generator = registry.get("data.mean.frequency_missing_value")

    def reject(check, question):
        try:
            check(question)
        except ValueError:
            return
        raise AssertionError("Invalid question accepted")

    for level in range(1, 5):
        q = generator.generate(12345, level)
        generator.validate_independently(q)
        print("Level {}: {}".format(level, q.prompt.text))
        print("Answer:", q.answer_display.text)
        wrong = replace(q, answer={
            "kind": "rational",
            "value": rational_text(Fraction(q.answer["value"]) + 1),
        })
        reject(generator.validate, wrong)
        reject(generator.validate_independently, wrong)
        table = deepcopy(q.question_visuals[0])
        table["rows"][0][1] = "99"
        reject(generator.validate, replace(q, question_visuals=(table,)))

    q = generator.generate(0, 1)
    values, frequencies = ["0", "1", None, "3"], [1, 2, 3, 4]
    prompt, table = presentation(values, frequencies, Fraction(2))
    known = replace(
        q, prompt=prompt, question_visuals=(table,),
        parameters={"values": values, "frequencies": frequencies, "mean": "2"},
        answer={"kind": "rational", "value": "2"},
        answer_display=Content("x = 2", "x = 2"),
    )
    generator.validate(known)
    generator.validate_independently(known)

    ambiguous = replace(known, parameters={
        "values": values, "frequencies": [1, 2, 0, 4], "mean": "2",
    })
    reject(generator.validate, ambiguous)
    reject(generator.validate_independently, ambiguous)
    try:
        generator.generate(0, settings={"unknown": True})
    except ValueError:
        pass
    else:
        raise AssertionError("Unsupported settings accepted")
    print("PASS: four levels, known answer, zero-frequency ambiguity and corruption.")


if __name__ == "__main__":
    main()