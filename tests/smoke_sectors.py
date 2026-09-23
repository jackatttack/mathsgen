"""Sectors v3: forms, decoy angles, independent proportions, tampering, labels, PDF."""
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
    from mathsgen.sectors import FORMS, UNKNOWN_ANGLE, truth
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    generator = registry.get("geometry.circles.sectors")
    require(generator.info.version == 3, "Expected sectors v3")
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
            if p["form"] in UNKNOWN_ANGLE:
                r, t = truth(p)
                require(abs(p["drawn"] - t) >= 20, "Decoy too close to the answer")
            if p["form"] not in shown:
                shown.add(p["form"])
                specimens.append(q)
                print("L{} [{}] {}".format(level, p["form"], q.prompt.text))
                print("  Answer:", q.answer_display.text)
            if seed < 5:
                tampered = [dict(p, orientation=[999, False]), dict(p, form="banana")]
                if "radius" in p:
                    tampered.append(dict(p, radius=p["radius"] + 1))
                if "angle" in p:
                    tampered.append(dict(p, angle=7))
                if "drawn" in p:
                    tampered.append(dict(p, drawn=int(truth(p)[1])))
                for bad in tampered:
                    require(rejects(generator.validate, replace(q, parameters=bad)),
                            "Tampered parameters accepted: " + str(bad))
            wrong = dict(q.answer)
            key = "value" if wrong["kind"] == "angle" else (
                "constant" if p["form"] == "radius" else "pi_coefficient")
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
        print("Level {}: forms {}, {} orientations".format(
            level, sorted(forms), len(orientations)))

    report = export_worksheet(
        Worksheet(id="sectors-v3-specimens", title="Arcs and sectors",
                  seed=20260923, specification={"specimens": True},
                  questions=tuple(specimens)),
        _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
    )
    print("Specimen:", report["directory"])
    print("PASS:", checked, "questions; proportions, decoys, tampering, "
          "label clearance, three widths and PDF")


if __name__ == "__main__":
    main()