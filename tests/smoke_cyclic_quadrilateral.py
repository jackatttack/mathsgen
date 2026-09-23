"""Cyclic quadrilateral v3: forms vs hand formulas, variety, tampering, labels, PDF."""
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
    if form == "opposite":
        return 180 - p["int0"][1]
    if form == "exterior":
        return p["ext2"][1]
    if form == "exterior_reverse":
        return p["int0"][1]
    if form == "triangle_diagonal":
        return p["d01"][1] + p["d21"][1]
    if form == "diagonal_split":
        return 180 - p["d01"][1] - p["d03"][1]
    if form == "algebra":
        (k1, b1), (k2, b2) = p["int0"], p["int2"]
        return (180 - b1 - b2) // (k1 + k2)
    (k, b), (_, c) = p["ext2"], p["int0"]
    return (c - b) // (k - 1)


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
    from mathsgen.cyclic_quadrilateral import FORMS
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    generator = registry.get("geometry.circle_theorems.cyclic_quadrilateral")
    require(generator.info.version == 3, "Expected cyclic quadrilateral v3")
    specimens, checked = [], 0
    for level in range(1, 5):
        forms, orientations, names, starts, shown = set(), set(), set(), set(), set()
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
            starts.add(p["start"])
            if p["form"] not in shown:
                shown.add(p["form"])
                specimens.append(q)
                print("L{} [{}] {}".format(level, p["form"], q.prompt.text))
                print("  Answer:", q.answer_display.text)
            if seed < 5:
                a, b, c, d = p["arcs"]
                for bad in (dict(p, orientation=[999, False]), dict(p, form="banana"),
                            dict(p, names="ZZZZ"), dict(p, start=(p["start"] + 1) % 4),
                            dict(p, arcs=[a + 2, b - 2, c, d]),
                            dict(p, arcs=[a, b + 1, c - 1, d])):
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
        require(len(names) >= 3 and len(starts) == 4, "Lettering lacks variety")
        print("Level {}: forms {}, {} orientations, {} letter sets, {} starts".format(
            level, sorted(forms), len(orientations), len(names), len(starts)))

    multi = registry.get("geometry.circle_theorems.multi_step")
    for level in range(1, 5):
        for seed in range(3):
            multi.validate(multi.generate(seed, level))
    print("Multi-step circles still generate and validate.")

    report = export_worksheet(
        Worksheet(
            id="cyclic-quadrilateral-v3-specimens",
            title="Circle theorem: cyclic quadrilaterals",
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