"""Check line relationships, incidence, progression and common misconceptions."""
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
    from mathsgen.catalogue import source_registry
    registry = source_registry(registry)
    from mathsgen.core import Content, rational_text, require
    from mathsgen.related_lines import presentation
    from mathsgen.straight_lines import linear_text
    from mathsgen.worksheets import build_worksheet
    from mathsgen.export import export_worksheet
    generator = registry.get("algebra.graphs.related_lines")

    def reject(check, q):
        try:
            check(q)
        except ValueError:
            return
        raise AssertionError("Incorrect line accepted")

    def with_answer(q, m, c):
        m, c = Fraction(m), Fraction(c)
        return replace(
            q, answer={"kind": "linear_equation", "m": rational_text(m), "c": rational_text(c)},
            answer_display=Content(linear_text(m, c), linear_text(m, c, True)),
        )

    for level in range(1, 5):
        q = generator.generate(12345, level)
        generator.validate_independently(q)
        print("Level {}: {}".format(level, q.prompt.text))
        print("Answer:", q.answer_display.text)
        m, c = Fraction(q.answer["m"]), Fraction(q.answer["c"])
        # Correct relationship but wrong intercept.
        wrong = with_answer(q, m, c + 1)
        for check in (generator.validate, generator.validate_independently):
            reject(check, wrong)
        # A wrong slope adjusted to STILL pass through the given point.
        x, y = q.parameters["point"]
        wrong = with_answer(q, m + 1, y - (m + 1) * x)
        reject(generator.validate_independently, wrong)

    # Known parallel case: A y=3x-7, B through (2,5), so B y=3x-1.
    p = {"line_a": [-3, 1, -7], "relation": "parallel", "point": [2, 5]}
    q = generator.generate(0, 2)
    known = with_answer(replace(q, parameters=p, prompt=presentation(p, 2)), 3, -1)
    generator.validate(known)
    generator.validate_independently(known)

    # Known perpendicular case: A 2x+3y=12, B through (4,1).
    p = {"line_a": [2, 3, 12], "relation": "perpendicular", "point": [4, 1]}
    q = generator.generate(0, 4)
    known = with_answer(replace(q, parameters=p, prompt=presentation(p, 4)), Fraction(3, 2), -5)
    generator.validate(known)
    generator.validate_independently(known)
    # Reciprocal without the sign change, adjusted through the same point.
    wrong_m = Fraction(-3, 2)
    reject(generator.validate_independently, with_answer(known, wrong_m, 1 - 4 * wrong_m))

    # Coincident lines are not a valid parallel-question construction.
    p = {"line_a": [-3, 1, -7], "relation": "parallel", "point": [2, -1]}
    q = generator.generate(0, 2)
    same = with_answer(replace(q, parameters=p, prompt=presentation(p, 2)), 3, -7)
    reject(generator.validate, same)
    reject(generator.validate_independently, same)

    relations = {generator.generate(seed, 4).parameters["relation"] for seed in range(40)}
    require(relations == {"parallel", "perpendicular"}, "Level 4 lacks relationship variety")
    try:
        generator.generate(0, settings={"unknown": True})
    except ValueError:
        pass
    else:
        raise AssertionError("Unsupported settings accepted")

    worksheet = build_worksheet({
        "title": "Parallel and perpendicular lines", "shuffle": False,
        "sections": [{
            "generator_ids": [generator.info.id], "count": 2,
            "difficulties": [level],
        } for level in range(1, 5)],
    }, 20260919, registry)
    report = export_worksheet(
        worksheet, Path(__file__).resolve().parent.parent / "exports", answers=True,
    )
    print("PASS: four stages, known cases, relationship and incidence errors rejected.")
    print("PASS: distinct parallel lines, both level-4 relationships and settings rejection.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()