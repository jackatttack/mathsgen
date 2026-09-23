"""Targeted frequency-mean checks and a four-level PDF worksheet."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path

from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import Content, require, rational_text
    from mathsgen.frequency_mean import presentation
    from mathsgen.worksheets import build_worksheet
    from mathsgen.export import export_worksheet

    generator = registry.get("data.mean.frequency_table")

    def rejected(check, question):
        try:
            check(question)
        except ValueError:
            return
        raise AssertionError("Corrupted question accepted")

    for level in range(1, 5):
        question = generator.generate(12345, level)
        generator.validate_independently(question)
        print("Level {}: {}".format(level, question.prompt.text))
        print("Answer:", question.answer_display.text)
        wrong = dict(question.answer, value=rational_text(
            Fraction(question.answer["value"]) + 1
        ))
        for check in (generator.validate, generator.validate_independently):
            rejected(check, replace(question, answer=wrong))
        table = deepcopy(question.question_visuals[0])
        table["rows"][0][1] = "99"
        rejected(generator.validate, replace(question, question_visuals=(table,)))
        rejected(generator.validate, replace(question, answer_display=Content("wrong")))

    # Known example: 0 occurs once, 1 twice, 2 three times, 3 four times.
    known = generator.generate(1, 1)
    values, frequencies = list(map(Fraction, (0, 1, 2, 3))), [1, 2, 3, 4]
    prompt, table = presentation(values, frequencies)
    known = replace(
        known, prompt=prompt, question_visuals=(table,),
        parameters={"values": ["0", "1", "2", "3"], "frequencies": frequencies},
        answer={"kind": "rational", "value": "2"},
        answer_display=Content("2", "2"),
    )
    generator.validate(known)
    generator.validate_independently(known)
    for settings in ({"unknown": True},):
        try:
            generator.generate(0, settings=settings)
        except ValueError:
            pass
        else:
            raise AssertionError("Settings were ignored")

    worksheet = build_worksheet({
        "title": "Mean from frequency tables",
        "shuffle": False,
        "sections": [{
            "generator_ids": [generator.info.id],
            "count": 4, "difficulties": [1, 2, 3, 4],
        }],
    }, 20260919, registry)
    report = export_worksheet(
        worksheet, Path(__file__).resolve().parent.parent / "exports", answers=True,
    )
    print("PASS: all four levels, known mean, wrong answers and visual corruption.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()