"""Cosine rule v4: forms, lettering, orientations, independent maths, tampering, PDF."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from fractions import Fraction
from launch_mathsgen import load_engine


EXPECTED_FORMS = {
    1: {"side"},
    2: {"angle"},
    3: {"angle_area", "side_angle"},
    4: {"linked_side", "linked_angle"},
}
SEEDS = 60


def rejects(checker, question):
    try:
        checker(question)
    except ValueError:
        return True
    return False


def main():
    registry = load_engine()
    from mathsgen.core import Content, require, rational_text
    from mathsgen.visuals import VisualFlowable
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet
    from smoke_geometry_layout import crossings

    generator = registry.get("geometry.trigonometry.cosine_rule")
    require(generator.info.version == 4, "Expected cosine rule v4")
    checked = 0
    specimens = []
    for level in range(1, 5):
        forms, orientations, namings = set(), set(), set()
        for seed in range(SEEDS):
            q = generator.generate(seed, level)
            generator.validate(q)
            generator.validate_independently(q)
            p = q.parameters
            forms.add(p["form"])
            orientations.add(tuple(p["orientation"]))
            namings.add(p.get("names"))
            if seed < 3:
                specimens.append(q)
            if seed < 5:
                bad = replace(q, parameters=dict(p, orientation=[999, False]))
                require(rejects(generator.validate, bad), "Invalid orientation accepted")
                bad = replace(q, parameters=dict(p, form="banana"))
                require(rejects(generator.validate, bad), "Invalid form accepted")
                if level < 4:
                    bad = replace(q, parameters=dict(p, names=p["names"][::-1]))
                    require(rejects(generator.validate, bad), "Relettered triangle accepted")
            for asset in q.visual_assets("questions"):
                require(not crossings(asset), "Label centre lies on an edge")
                for width in (250, 360):
                    VisualFlowable(asset).wrap(width, 420)
            for key in q.answer:
                if key in ("kind", "unit"):
                    continue
                wrong = dict(q.answer)
                wrong[key] = rational_text(Fraction(wrong[key]) + 1)
                for checker in (generator.validate, generator.validate_independently):
                    require(rejects(checker, replace(q, answer=wrong)),
                            "Wrong {} accepted".format(key))
            require(rejects(generator.validate, replace(q, prompt=Content("Wrong givens"))),
                    "Wrong prompt accepted")
            checked += 1
        require(forms == EXPECTED_FORMS[level],
                "Level {} forms: saw {}".format(level, sorted(forms)))
        require(len(orientations) >= 3, "Diagram orientations lack variety")
        if level < 4:
            require(len(namings) >= 4, "Vertex lettering lacks variety")
        print("Level {}: forms {}, {} orientations, {} letterings in {} seeds".format(
            level, sorted(forms), len(orientations),
            len(namings - {None}), SEEDS))
        for seed in (12345, 12346):
            sample = generator.generate(seed, level)
            print("  [{}] {}".format(sample.parameters["form"], sample.prompt.text))
            print("  Answer:", sample.answer_display.text)
    report = export_worksheet(
        Worksheet(
            id="cosine-rule-v4-varied-specimens",
            title="Cosine rule: varied forms and diagrams",
            seed=20260923, specification={"specimens": True},
            questions=tuple(specimens),
        ),
        _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
    )
    print("Specimen:", report["directory"])
    print("PASS:", checked, "questions; forms, lettering, orientation, "
          "independent maths, tampering and two widths")


if __name__ == "__main__":
    main()