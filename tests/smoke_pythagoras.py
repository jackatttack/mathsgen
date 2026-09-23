"""Check reverse calculations, diagrams and export all four levels."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import rational_text
    from mathsgen.visuals import drawing_for
    from mathsgen.worksheets import build_worksheet
    from mathsgen.export import export_worksheet
    generator = registry.get("geometry.pythagoras.lengths")

    seen_missing = set()
    for seed in range(80):
        question = generator.generate(seed, 2)
        missing = question.parameters["missing"]
        sides = question.parameters["sides"]
        known_side = sides[1 - missing]
        expected = "other perpendicular side: {} cm".format(known_side)
        assert expected in question.prompt.text, (
            "L2 wording must state the known leg, not the missing leg"
        )
        seen_missing.add(missing)
    assert seen_missing == {0, 1}, "Both missing-leg forms must appear"

    for level in range(1, 5):
        q = generator.generate(12345, level)
        generator.validate_independently(q)
        print("Level {}: {}".format(level, q.prompt.text))
        print("Answer:", q.answer_display.text)
        for width in (360, 250):
            drawing_for(q.question_visuals[0], width)
        wrong = replace(q, answer=dict(
            q.answer, value=rational_text(Fraction(q.answer["value"]) + 1)
        ))
        for check in (generator.validate, generator.validate_independently):
            try:
                check(wrong)
            except ValueError:
                pass
            else:
                raise AssertionError("Wrong length accepted")

    worksheet = build_worksheet({
        "title": "Pythagoras: missing lengths", "shuffle": False,
        "sections": [{
            "generator_ids": [generator.info.id], "count": 1,
            "difficulties": [level],
        } for level in range(1, 5)],
    }, 20260919, registry)
    report = export_worksheet(
        worksheet, Path(__file__).resolve().parent.parent / "exports", answers=True,
    )
    print("PASS: four structures, independent rejection and two drawing widths.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()