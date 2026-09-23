"""Exercise every parallel-angle structure and its PDF layout."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

import copy
from dataclasses import replace
import json
from pathlib import Path

from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import require
    from mathsgen.visuals import drawing_for
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    generator = registry.get("geometry.angles.parallel_lines")
    representatives = {}
    for level in range(1, 5):
        orientations = set()
        for seed in range(40):
            q = generator.generate(seed, level)
            generator.validate_independently(q)
            assert "horizontal" not in q.prompt.text
            assert "above the upper" not in q.prompt.text
            orientations.add(tuple(q.parameters["orientation"]))
            key = (level, q.parameters["relation"])
            representatives.setdefault(key, q)
            for width in (250, 360):
                drawing_for(q.question_visuals[0], width)
        require(len(orientations) >= 3,
                "Insufficient diagram variety at level {}".format(level))
        print("Level {}: {} orientations in 40 seeds".format(
            level, len(orientations)))

    require(len(representatives) == 6, "Missing question structure")
    for key, q in sorted(representatives.items()):
        print("Level {} / {}: {}".format(*key, q.prompt.text))
        print("Answer:", q.answer_display.text)
        wrong = replace(q, answer={"kind": "integer", "value": q.answer["value"] + 1})
        for check in (generator.validate, generator.validate_independently):
            try:
                check(wrong)
            except ValueError:
                pass
            else:
                raise AssertionError("Wrong answer accepted")

        altered = copy.deepcopy(q.parameters)
        altered["orientation"] = [999, False]
        try:
            generator.validate(replace(q, parameters=altered))
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid orientation accepted")

        diagram = copy.deepcopy(q.question_visuals[0])
        diagram["nodes"] = [
            n for n in diagram["nodes"] if n["type"] != "parallel"
        ]
        try:
            generator.validate(replace(q, question_visuals=(diagram,)))
        except ValueError:
            pass
        else:
            raise AssertionError("Missing parallel markings accepted")

    try:
        generator.generate(0, 1, {"unexpected": True})
    except ValueError:
        pass
    else:
        raise AssertionError("Unsupported settings accepted")

    worksheet = Worksheet(
        id="parallel-angles-v2-specimens",
        title="Angles in parallel lines", seed=0,
        specification={"specimens": True},
        questions=tuple(q for key, q in sorted(representatives.items())),
    )
    report = export_worksheet(
        worksheet, Path(__file__).resolve().parent.parent / "exports", answers=True,
    )
    print("PASS: six structures, two drawing widths and corruption rejection.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()