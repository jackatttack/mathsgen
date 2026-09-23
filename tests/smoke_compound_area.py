"""Check direct/reverse areas, a known polygon and diagram corruption."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from random import Random
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.compound_area import presentation, answer_content
    from mathsgen import figures
    from mathsgen.visuals import drawing_for
    from mathsgen.worksheets import build_worksheet
    from mathsgen.export import export_worksheet
    generator = registry.get("geometry.area.compound_rectangles")

    def reject(check, q):
        try:
            check(q)
        except ValueError:
            return
        raise AssertionError("Invalid compound-area question accepted")

    seen_tasks = set()
    for level in range(1, 5):
        orientations = set()
        for seed in range(40):
            q = generator.generate(seed, level)
            if seed < 8:
                generator.validate_independently(q)
            orientations.add(tuple(q.parameters["orientation"]))
            if level == 4:
                seen_tasks.add(q.parameters["task"])
            for width in (360, 250):
                drawing_for(q.question_visuals[0], width)
            if seed == 0:
                print("Level {}: {}".format(level, q.prompt.text))
                print("Answer:", q.answer_display.text)
                wrong = replace(q, answer=dict(q.answer, value=q.answer["value"] + 1))
                reject(generator.validate, wrong)
                reject(generator.validate_independently, wrong)
                visual = deepcopy(q.question_visuals[0])
                visual["nodes"][-1]["text"] = "99 cm"
                reject(generator.validate, replace(q, question_visuals=(visual,)))
                altered = deepcopy(q.parameters)
                altered["orientation"] = [999, False]
                reject(generator.validate, replace(q, parameters=altered))
        assert len(orientations) >= 3, "Diagrams do not vary at level {}".format(level)
        print("Level {}: {} orientations in 40 seeds".format(level, len(orientations)))
    assert seen_tasks == {"missing", "inner_trim"}, "Both reverse tasks must appear"

    # 10 by 12 outer rectangle minus a 4 by 5 cut-out: 100 square cm.
    known_questions = []
    for index, (level, given, task, result) in enumerate((
        (2, {"W": 10, "H": 12, "w": 4, "h": 5}, "area", 100),
        (4, {"W": 10, "H": 12, "w": 4, "area": 100}, "missing", 5),
        (4, {"W": 10, "H": 12, "w": 4, "area": 100}, "inner_trim", 9),
    )):
        q = generator.generate(index, level)
        orientation = figures.choose_orientation(
            Random(20260922 + index),
            lambda choice: presentation(given, level, choice, task)[1])
        prompt, visual = presentation(given, level, orientation, task)
        parameters = {"given": given, "orientation": orientation}
        if level == 4:
            parameters["task"] = task
        known = replace(
            q, parameters=parameters, prompt=prompt,
            question_visuals=(visual,), answer=dict(q.answer, value=result),
            answer_display=answer_content(result, level, task),
            marks=5 if task == "inner_trim" else 4 if level == 4 else 3,
        )
        generator.validate(known)
        generator.validate_independently(known)
        known_questions.append(known)

    from mathsgen.worksheets import Worksheet
    known_report = export_worksheet(
        Worksheet(
            id="compound-area-v2-known-specimens",
            title="Compound area: direct and both reverse forms",
            seed=20260922, specification={"specimens": True},
            questions=tuple(known_questions),
        ),
        Path(__file__).resolve().parent.parent / "exports", answers=True,
    )
    print("Known forms specimen:", known_report["directory"])

    try:
        generator.generate(0, settings={"unknown": True})
    except ValueError:
        pass
    else:
        raise AssertionError("Unsupported settings ignored")

    worksheet = build_worksheet({
        "title": "Compound area: rectangles", "shuffle": False,
        "sections": [{
            "generator_ids": [generator.info.id], "count": 1,
            "difficulties": [level],
        } for level in range(1, 5)],
    }, 20260919, registry)
    report = export_worksheet(
        worksheet, Path(__file__).resolve().parent.parent / "exports", answers=True,
    )
    print("PASS: four structures, known direct/reverse cases and corruption rejection.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()