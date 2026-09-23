"""Check dependent calculations, all four tasks and their printed diagrams."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

import copy
from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path
from random import Random

from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import Content, canonical_json, rational_text, require
    from mathsgen import figures
    from mathsgen.pythagoras import LINKED, LINKED_TASKS, presentation, answer_name
    from mathsgen.visuals import drawing_for
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    generator = registry.get("geometry.pythagoras.lengths")
    base = generator.generate(20260919, 4)

    # Two known triangles: 5,12,13 and 9,12,15.
    # AB=5 and AC=13 reveal CB=12; the second triangle then becomes solvable.
    known = [12, 5, 9, 13, 15]
    require(tuple(known) in LINKED, "Known configuration is unavailable")
    expected = {
        "second_hypotenuse": 15,
        "second_base": 9,
        "total_base": 14,
        "perimeter": 42,
    }
    specimens = []
    for index, task in enumerate(LINKED_TASKS):
        parameters = {"linked": list(known), "task": task}
        parameters["orientation"] = figures.choose_orientation(
            Random(20260919 + index),
            lambda orientation: presentation(
                dict(parameters, orientation=orientation), 4)[1],
        )
        prompt, diagram = presentation(parameters, 4)
        value = expected[task]
        q = replace(
            base, id="linked-pythagoras-v3-" + task,
            parameters=parameters, prompt=prompt,
            question_visuals=(diagram,),
            answer={"kind": "length", "value": str(value), "unit": "cm"},
            answer_display=Content("{} = {} cm".format(
                answer_name(parameters, 4), value
            )),
            marks=5 if task in ("total_base", "perimeter") else 4,
        )
        generator.validate(q)
        generator.validate_independently(q)
        for width in (250, 360):
            drawing_for(diagram, width)
        require("CB =" not in prompt.text, "Shared height leaked into wording")
        require(not any(
            node.get("text") == "12 cm" for node in diagram["nodes"]
        ), "Shared height leaked into diagram")
        require(json.loads(canonical_json(q.to_dict()))["parameters"] == parameters,
                "Parameters changed in JSON")

        wrong = replace(q, answer=dict(
            q.answer, value=rational_text(Fraction(value) + 1)
        ))
        for check in (generator.validate, generator.validate_independently):
            try:
                check(wrong)
            except ValueError:
                pass
            else:
                raise AssertionError("Incorrect answer accepted")

        # The independent checker must not read hidden construction answers.
        altered = copy.deepcopy(parameters)
        altered["linked"][0] = 999
        altered["linked"][4 if task == "second_hypotenuse" else 2] = 888
        generator.validate_independently(replace(q, parameters=altered))

        damaged = copy.deepcopy(diagram)
        damaged["nodes"].append({
            "type": "label", "point": [210, 85], "text": "12 cm"
        })
        try:
            generator.validate(replace(q, question_visuals=(damaged,)))
        except ValueError:
            pass
        else:
            raise AssertionError("Leaked shared height accepted")

        print(task + ": " + q.prompt.text)
        print("Answer:", q.answer_display.text)
        specimens.append(q)

    seen = set()
    for seed in range(200):
        q = generator.generate(seed, 4)
        seen.add(q.parameters["task"])
    require(seen == set(LINKED_TASKS), "A linked task was not generated")

    worksheet = Worksheet(
        id="linked-pythagoras-v3-specimens",
        title="Pythagoras: linked triangles",
        seed=20260919,
        specification={"specimens": True},
        questions=tuple(specimens),
    )
    report = export_worksheet(
        worksheet, Path(__file__).resolve().parent.parent / "exports", answers=True,
    )
    print("PASS: four dependent tasks, known answers and two drawing widths.")
    print("PASS: hidden values unused by independent checker; corruption rejected.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()