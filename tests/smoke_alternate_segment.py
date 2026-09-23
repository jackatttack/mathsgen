"""Alternate segment v4: forms vs hand formulas, variety, tampering, labels, PDF."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from launch_mathsgen import load_engine


SEEDS = 50


def hand_answer(p):
    form = p["form"]
    if form in ("forward", "backward", "other_chord", "other_chord_reverse"):
        first = {"forward": "BAT", "backward": "ACB", "other_chord": "CAS",
                 "other_chord_reverse": "ABC"}[form]
        return p[first][1]
    if form == "triangle":
        return 180 - p["BAT"][1] - p["ABC"][1]
    if form == "centre":
        return 2 * p["BAT"][1]
    if form == "algebra":
        (k, b), (_, c) = p["BAT"], p["ACB"]
        return (c - b) // (k - 1)
    (k, b), (_, a), (_, c) = p["BAT"], p["ABC"], p["BAC"]
    return (180 - b - a - c) // (k + 1)


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
    from mathsgen.circle_figures import labels_clear, CHECK_WIDTHS
    from mathsgen.alternate_segment import FORMS
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    generator = registry.get("geometry.circle_theorems.alternate_segment")
    require(generator.info.version == 4, "Expected alternate segment v4")
    specimens, checked = [], 0
    for level in range(1, 5):
        forms, orientations, names, shown = set(), set(), set(), set()
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
            if p["form"] not in shown:
                shown.add(p["form"])
                specimens.append(q)
                print("L{} [{}] {}".format(level, p["form"], q.prompt.text))
                print("  Answer:", q.answer_display.text)
            if seed < 5:
                ab, bc, ca = p["arcs"]
                for bad in (dict(p, orientation=[999, False]), dict(p, form="banana"),
                            dict(p, names="ZZZZZ"), dict(p, arcs=[ab + 2, bc - 2, ca]),
                            dict(p, arcs=[ab, bc + 2, ca - 2])):
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
            for width in CHECK_WIDTHS:
                drawing_for(asset, width)
            checked += 1
        require(forms == set(FORMS[level]),
                "Level {} forms: saw {}".format(level, sorted(forms)))
        require(len(orientations) >= 3, "Orientations lack variety")
        require(len(names) >= 3, "Letter sets lack variety")
        print("Level {}: forms {}, {} orientations, {} letter sets".format(
            level, sorted(forms), len(orientations), len(names)))

    multi = registry.get("geometry.circle_theorems.multi_step")
    for level in range(1, 5):
        for seed in range(3):
            multi.validate(multi.generate(seed, level))
    print("Multi-step circles still generate and validate.")

    report = export_worksheet(
        Worksheet(
            id="alternate-segment-v4-specimens", title="Circle theorem: alternate segment",
            seed=20260923, specification={"specimens": True},
            questions=tuple(specimens),
        ),
        _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
    )
    print("Specimen:", report["directory"])
    print("PASS:", checked, "questions; hand formulas, measured drawings, "
          "tampering, label clearance, three widths and PDF")


if __name__ == "__main__":
    main()