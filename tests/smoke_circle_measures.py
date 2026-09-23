"""Circle measures v4: forms, identities, tampering, labels, PDF; sectors still work."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from fractions import Fraction
from launch_mathsgen import load_engine


SEEDS = 50


def rejects(checker, question):
    try:
        checker(question)
    except ValueError:
        return True
    return False


def main():
    registry = load_engine()
    from mathsgen.core import Content, require, rational_text
    from mathsgen.visuals import drawing_for
    from mathsgen.circle_figures import labels_clear, CHECK_WIDTHS
    from mathsgen.circle_measures import FORMS
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    generator = registry.get("geometry.circles.measures")
    require(generator.info.version == 4, "Expected circle measures v4")
    specimens, checked = [], 0
    for level in range(1, 5):
        forms, orientations, shown = set(), set(), set()
        for seed in range(SEEDS):
            q = generator.generate(seed, level)
            generator.validate(q)
            generator.validate_independently(q)
            p = q.parameters
            forms.add(p["form"])
            orientations.add(tuple(p["orientation"]))
            if p["form"] not in shown:
                shown.add(p["form"])
                specimens.append(q)
                print("L{} [{}] {}".format(level, p["form"], q.prompt.text))
                print("  Answer:", q.answer_display.text)
            if seed < 5:
                numeric = next(k for k in ("value", "outer", "side") if k in p)
                for bad in (dict(p, orientation=[999, False]), dict(p, form="banana"),
                            dict(p, **{numeric: p[numeric] + 2})):
                    require(rejects(generator.validate, replace(q, parameters=bad)),
                            "Tampered parameters accepted: " + str(bad))
            wrong = dict(q.answer)
            key = "constant" if Fraction(wrong["pi_coefficient"]) == 0 else "pi_coefficient"
            wrong[key] = rational_text(Fraction(wrong[key]) + 1)
            for checker in (generator.validate, generator.validate_independently):
                require(rejects(checker, replace(q, answer=wrong)), "Wrong answer accepted")
            require(rejects(generator.validate, replace(q, prompt=Content("Wrong"))),
                    "Wrong prompt accepted")
            asset = q.visual_assets("questions")[0]
            require(labels_clear(asset), "Label touches a line")
            for width in CHECK_WIDTHS:
                drawing_for(asset, width)
            checked += 1
        require(forms == set(FORMS[level]),
                "Level {} forms: saw {}".format(level, sorted(forms)))
        require(len(orientations) >= 3, "Orientations lack variety")
        print("Level {}: forms {}, {} orientations".format(level, sorted(forms), len(orientations)))

    sectors = registry.get("geometry.circles.sectors")
    for level in range(1, 5):
        for seed in range(3):
            sectors.validate(sectors.generate(seed, level))
    print("Sectors still generate and validate with the shared helpers.")

    report = export_worksheet(
        Worksheet(id="circle-measures-v4-specimens",
                  title="Circles and circular regions", seed=20260923,
                  specification={"specimens": True}, questions=tuple(specimens)),
        _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
    )
    print("Specimen:", report["directory"])
    print("PASS:", checked, "questions; identities, tampering, label clearance, "
          "three widths and PDF")


if __name__ == "__main__":
    main()