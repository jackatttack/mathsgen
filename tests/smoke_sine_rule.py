"""Check sine-rule mathematics, corrupted answers and diagram rendering."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from fractions import Fraction
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import Content, require, rational_text
    from mathsgen.visuals import VisualFlowable
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet
    from smoke_geometry_layout import crossings

    generator = registry.get("geometry.trigonometry.sine_rule")
    checked = 0
    specimens = []
    for level in range(1, 5):
        orientations = set()
        for seed in range(50):
            q = generator.generate(seed, level)
            generator.validate_independently(q)
            orientations.add(tuple(q.parameters["orientation"]))
            if seed in (0, 1):
                specimens.append(q)
            if seed == 0:
                altered = dict(q.parameters, orientation=[999, False])
                try:
                    generator.validate(replace(q, parameters=altered))
                except ValueError:
                    pass
                else:
                    raise AssertionError("Invalid orientation accepted")
            for asset in q.visual_assets("questions"):
                require(not crossings(asset), "Label centre lies on an edge")
                for width in (250, 360):
                    VisualFlowable(asset).wrap(width, 420)
            wrong = dict(q.answer)
            wrong["value"] = rational_text(Fraction(wrong["value"]) + 1)
            for checker in (generator.validate, generator.validate_independently):
                try:
                    checker(replace(q, answer=wrong))
                except ValueError:
                    pass
                else:
                    raise AssertionError("Wrong answer accepted")
            try:
                generator.validate(replace(q, prompt=Content("Wrong givens")))
            except ValueError:
                pass
            else:
                raise AssertionError("Wrong prompt accepted")
            checked += 1
        require(len(orientations) >= 3,
                "Sine-rule diagram orientations lack variety")
        sample = generator.generate(12345, level)
        print("Level {}: {} orientations in 50 seeds".format(
            level, len(orientations)))
        print("Level", level, sample.prompt.text)
        print("Answer:", sample.answer_display.text)
    report = export_worksheet(
        Worksheet(
            id="sine-rule-v3-varied-specimens",
            title="Sine rule: varied diagrams",
            seed=20260923, specification={"specimens": True},
            questions=tuple(specimens),
        ),
        _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
    )
    print("Specimen:", report["directory"])
    print("PASS:", checked, "questions; independent checks, corruption and two widths")


if __name__ == "__main__":
    main()