"""Tangents v2: forms vs hand formulas, variety, tampering, labels, PDF."""
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
    if form in ("triangle_at_p", "triangle_at_o"):
        given = p["AOP"] if form == "triangle_at_p" else p["APO"]
        return 90 - given[1]
    if form == "kite":
        return 180 - p["APB"][1]
    if form == "kite_reverse":
        return 180 - p["AOB"][1]
    if form == "isosceles":
        return (180 - p["APB"][1]) // 2
    if form == "radius_chord":
        return p["APB"][1] // 2
    if form == "algebra":
        (k1, b1), (k2, b2) = p["APB"], p["AOB"]
        return (180 - b1 - b2) // (k1 + k2)
    (k, b), (_, c) = p["APB"], p["PAB"]
    return (180 - b - 2 * c) // (k + 2)


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
    from mathsgen.tangent_theorems import FORMS, FORM_ROLES
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    generator = registry.get("geometry.circle_theorems.tangents")
    require(generator.info.version == 2, "Expected tangents v2")
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
                first = FORM_ROLES[p["form"]][0]
                bumped = [p[first][0], p[first][1] + 2]
                for bad in (dict(p, orientation=[999, False]), dict(p, form="banana"),
                            dict(p, names="ZZZ"), dict(p, **{first: bumped})):
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
            id="tangents-v2-specimens", title="Circle theorem: tangents and radii",
            seed=20260923, specification={"specimens": True},
            questions=tuple(specimens),
        ),
        _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
    )
    print("Specimen:", report["directory"])
    print("PASS:", checked, "questions; hand formulas, measured kites, "
          "tampering, label clearance, three widths and PDF")


if __name__ == "__main__":
    main()