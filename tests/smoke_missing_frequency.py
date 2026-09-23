"""Exercise unique solutions, underdetermined tables and display corruption."""
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
    from mathsgen.core import Content, require
    from mathsgen.missing_frequency import presentation
    generator = registry.get("data.mean.missing_frequency")

    def reject(check, question):
        try:
            check(question)
        except ValueError:
            return
        raise AssertionError("Corrupt or underdetermined question accepted")

    for level in range(1, 5):
        q = generator.generate(12345, level)
        generator.validate_independently(q)
        print("Level {}: {}".format(level, q.prompt.text))
        print("Answer:", q.answer_display.text)
        wrong = replace(q, answer={"kind": "integer", "value": q.answer["value"] + 1})
        reject(generator.validate, wrong)
        reject(generator.validate_independently, wrong)
        table = deepcopy(q.question_visuals[0])
        table["rows"][0][0] = "999"
        reject(generator.validate, replace(q, question_visuals=(table,)))

    q = generator.generate(0, 1)
    values, frequencies = list(map(Fraction, (1, 3, 5))), [2, 3, None]
    prompt, table = presentation(values, frequencies, Fraction(3))
    known = replace(
        q, prompt=prompt, question_visuals=(table,),
        parameters={"values": ["1", "3", "5"], "frequencies": frequencies, "mean": "3"},
        answer={"kind": "integer", "value": 2},
        answer_display=Content("f = 2", "f = 2"),
    )
    generator.validate(known)
    generator.validate_independently(known)

    # Mean stays 3 for EVERY frequency in the middle row.
    frequencies = [2, None, 2]
    prompt, table = presentation(values, frequencies, Fraction(3))
    ambiguous = replace(
        known, prompt=prompt, question_visuals=(table,),
        parameters={"values": ["1", "3", "5"], "frequencies": frequencies, "mean": "3"},
    )
    reject(generator.validate, ambiguous)
    reject(generator.validate_independently, ambiguous)
    try:
        generator.generate(0, settings={"ignored": True})
    except ValueError:
        pass
    else:
        raise AssertionError("Unsupported settings accepted")
    print("PASS: four levels, known solution, non-unique case and corruption rejection.")


if __name__ == "__main__":
    main()