"""Centre-angle v2: every form against hand formulas, variety, tampering, labels, PDF."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from launch_mathsgen import load_engine


SEEDS = 50


def hand_answer(p):
    """Each form's textbook route, written out separately from the generator."""
    form = p["form"]
    c, g, base = p.get("central"), p.get("circumference"), p.get("base")
    if form == "central":
        return 2 * g[1]
    if form == "circumference":
        return c[1] // 2
    if form == "base_angle":
        return 90 - g[1]
    if form == "reflex":
        return (360 - c[1]) // 2
    if form == "base_to_reflex":
        return 90 + base[1]
    if form == "algebra":
        return 2 * g[1] - c[1]
    return (90 - g[1] - base[1]) // 2


def rejects(checker, question):
    try:
        checker(question)
    except ValueError:
        return True
    return False


def main():
    registry = load_engine()
    from mathsgen.core import Content, require
    from mathsgen.visuals import drawing_for
    from mathsgen.circle_figures import labels_clear
    from mathsgen.circle_centre_angles import FORMS
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    generator = registry.get("geometry.circle_theorems.centre_angle")
    require(generator.info.version == 2, "Expected centre angle v2")
    specimens, checked = [], 0
    for level in range(1, 5):
        forms, orientations, names, shifts = set(), set(), set(), set()
        shown = set()
        for seed in range(SEEDS):
            q = generator.generate(seed, level)
            generator.validate(q)
            generator.validate_independently(q)
            p = q.parameters
            require(q.answer["value"] == hand_answer(p),
                    "Hand formula disagrees for " + p["form"])
            forms.add(p["form"])
            orientations.add(tuple(p["orientation"]))
            names.add(p["names"])
            shifts.add(p["c_shift"])
            if p["form"] not in shown:
                shown.add(p["form"])
                specimens.append(q)
                print("L{} [{}] {}".format(level, p["form"], q.prompt.text))
                print("  Answer:", q.answer_display.text)
            if seed < 5:
                for bad in (dict(p, orientation=[999, False]), dict(p, form="banana"),
                            dict(p, c_shift=p["c_shift"] + 3),
                            dict(p, names="XYZ")):
                    require(rejects(generator.validate, replace(q, parameters=bad)),
                            "Tampered parameters accepted: " + str(bad))
            value = q.answer["value"]
            for wrong in (value + 1, value - 2):
                bad = replace(q, answer={"kind": "integer", "value": wrong})
                for checker in (generator.validate, generator.validate_independently):
                    require(rejects(checker, bad), "Wrong angle accepted")
            require(rejects(generator.validate, replace(q, prompt=Content("Wrong"))),
                    "Wrong prompt accepted")
            asset = q.visual_assets("questions")[0]
            require(labels_clear(asset), "Label touches a line")
            for width in (250, 360):
                drawing_for(asset, width)
            checked += 1
        require(forms == set(FORMS[level]),
                "Level {} forms: saw {}".format(level, sorted(forms)))
        require(len(orientations) >= 3, "Orientations lack variety")
        require(len(names) >= 3, "Letter sets lack variety")
        print("Level {}: forms {}, {} orientations, {} letter sets, {} C positions".format(
            level, sorted(forms), len(orientations), len(names), len(shifts)))
    report = export_worksheet(
        Worksheet(
            id="circle-centre-v2-specimens", title="Circle theorem: angle at the centre",
            seed=20260923, specification={"specimens": True},
            questions=tuple(specimens),
        ),
        _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
    )
    print("Specimen:", report["directory"])
    print("PASS:", checked, "questions; hand formulas, measured drawings, "
          "tampering, label clearance and two widths")


if __name__ == "__main__":
    main()