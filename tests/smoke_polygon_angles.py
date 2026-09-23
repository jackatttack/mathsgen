"""Known polygon cases, reverse uniqueness, corruption and sample export."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
import json
from pathlib import Path
from random import Random
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import require
    from mathsgen import figures
    from mathsgen.polygon_angles import presentation, answer_display, diagram_for
    from mathsgen.visuals import drawing_for
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    generator = registry.get("geometry.angles.polygons")
    cases = (
        (1, {"sides": 7}, 900),
        (2, {"sides": 8, "angle_kind": "interior"}, 135),
        (2, {"sides": 12, "angle_kind": "exterior"}, 30),
        (3, {"angle_kind": "interior", "angle": 144}, 10),
        (3, {"angle_kind": "exterior", "angle": 40}, 9),
        (3, {"form": "quadrilateral_exterior",
             "angles": [80, 95, 110]}, 105),
        (4, {"known_sides": 4, "gap": 150}, 6),
        (4, {"form": "vertex_fit",
             "first_sides": 4, "second_sides": 6}, 12),
    )
    questions = []
    for index, (level, parameters, value) in enumerate(cases):
        parameters = dict(parameters)
        parameters["orientation"] = figures.choose_orientation(
            Random(20260922 + index),
            lambda orientation: diagram_for(
                dict(parameters, orientation=orientation), level))
        q = replace(
            generator.generate(index, level),
            id="polygon-known-{}".format(index),
            parameters=parameters, prompt=presentation(parameters, level),
            answer={"kind": "integer", "value": value},
            answer_display=answer_display(value, level, parameters.get("form")),
            question_visuals=(diagram_for(parameters, level),),
        )
        generator.validate(q)
        generator.validate_independently(q)
        for width in (250, 360):
            drawing_for(q.question_visuals[0], width)
        if level >= 3 and parameters.get("form") != "quadrilateral_exterior":
            require(not any(node["type"] == "polygon"
                            for node in q.question_visuals[0]["nodes"]),
                    "A complete outline reveals the unknown side count")
        try:
            generator.validate(replace(q, question_visuals=()))
        except ValueError:
            pass
        else:
            raise AssertionError("Missing diagram accepted")
        print("Level {}: {}".format(level, q.prompt.text))
        print("Answer:", q.answer_display.text)
        bad = replace(q, answer={"kind": "integer", "value": value + 1})
        for check in (generator.validate, generator.validate_independently):
            try:
                check(bad)
            except ValueError:
                pass
            else:
                raise AssertionError("Wrong answer accepted")
        try:
            generator.validate(replace(q, prompt=questions[0].prompt if questions
                                       else presentation({"sides": 8}, 1)))
        except ValueError:
            pass
        else:
            raise AssertionError("Wrong prompt accepted")
        questions.append(q)

    base = generator.generate(0, 3)
    invalid = replace(
        base, parameters={"angle_kind": "interior", "angle": 131},
        answer={"kind": "integer", "value": 7},
    )
    for check in (generator.validate, generator.validate_independently):
        try:
            check(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Non-integer side count accepted")

    for level in range(1, 5):
        orientations = set()
        forms = set()
        for seed in range(60):
            sample = generator.generate(seed, level)
            forms.add(sample.parameters.get("form", "original"))
            orientations.add(tuple(sample.parameters["orientation"]))
            generator.validate_independently(sample)
            for width in (250, 360):
                drawing_for(sample.question_visuals[0], width)
        require(len(orientations) >= 3, "Insufficient polygon orientations")
        if level == 3:
            require(forms == {"original", "quadrilateral_exterior"},
                    "Missing level 3 form")
        if level == 4:
            require(forms == {"original", "vertex_fit"},
                    "Missing level 4 form")
        print("Level {}: {} orientations; forms {}".format(
            level, len(orientations), sorted(forms)))

    worksheet = Worksheet(
        id="polygon-angles-v4-specimens", title="Angles in polygons",
        seed=0, specification={"specimens": True},
        questions=tuple(questions),
    )
    report = export_worksheet(
        worksheet, Path(__file__).resolve().parent.parent / "exports", answers=True,
    )
    print("PASS: known forward/reverse cases and corruption rejection.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()