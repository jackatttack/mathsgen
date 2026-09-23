"""Check signed transformations, answer isolation and stacked grid exports."""
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
    from mathsgen.core import require, rational_text
    from mathsgen.enlargements import FACTORS, transform
    from mathsgen.visuals import drawing_for
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    generator = registry.get("geometry.transformations.enlargement")
    require(transform([[3, 2], [4, 2], [3, 3]], [1, 1], Fraction(-2))
            == [[-3, -1], [-5, -1], [-3, -3]], "Known negative case failed")
    require(transform([[5, 3], [7, 3], [5, 5]], [1, 1], Fraction(1, 2))
            == [[3, 2], [4, 2], [3, 3]], "Known reduction failed")

    specimens = []
    for level in range(1, 5):
        seen = set()
        chosen = None
        for seed in range(120):
            q = generator.generate(seed, level)
            generator.validate_independently(q)
            seen.add(q.parameters["factor"])
            for asset in q.visual_assets("worked"):
                require(asset["equal_units"]
                        and asset["x_step"] / asset["minor_divisions"] == 1
                        and asset["y_step"] / asset["minor_divisions"] == 1,
                        "Grid must have square one-unit cells")
                for width in (280, 360):
                    drawing_for(asset, width)
            if chosen is None and q.parameters["centre"] != [0, 0]:
                chosen = q
        require(seen == set(FACTORS[level]), "Missing scale-factor case")
        q = chosen
        require(len(q.question_visuals[0]["curves"]) == (2 if level == 4 else 1),
                "Student image routing failed")
        require(len(q.answer_visuals[0]["curves"]) == 2, "Completed image missing")

        wrong = deepcopy(q.answer)
        if level == 4:
            wrong["value"] = rational_text(-Fraction(wrong["value"]))
        else:
            wrong["vertices"][0][0] += 1
        for check in (generator.validate, generator.validate_independently):
            try:
                check(replace(q, answer=wrong))
            except ValueError:
                pass
            else:
                raise AssertionError("Wrong transformation accepted")
        if level != 4:
            try:
                generator.validate(replace(q, question_visuals=q.answer_visuals))
            except ValueError:
                pass
            else:
                raise AssertionError("Answer leaked into student grid")

        print("Level {}: {}".format(level, q.prompt.text))
        print("Answer:", q.answer_display.text)
        specimens.append(q)

    worksheet = Worksheet(
        id="enlargements-v1-specimens", title="Enlargements",
        seed=0, specification={"specimens": True}, questions=tuple(specimens),
    )
    report = export_worksheet(
        worksheet, Path(__file__).resolve().parent.parent / "exports", answers=True,
    )
    question_pdf = next(item for item in report["pdfs"] if item["mode"] == "questions")
    require(question_pdf["pages"] == 2,
            "Four enlargement specimens should fit on two question pages")
    print("PASS: four questions on two pages; square one-unit grid cells.")
    print("PASS: all signed factors, off-origin centres and two widths.")
    print("PASS: known cases, corruption rejection and answer isolation.")
    print(json.dumps(report, indent=2))
    print("Review square cells, drawing room and page stacking on device.")


if __name__ == "__main__":
    main()