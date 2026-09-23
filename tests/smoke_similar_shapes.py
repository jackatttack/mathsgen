"""Similarity v2: forms, variety, independent invariants, tampering, labels, PDF."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
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
    from mathsgen.core import Content, require
    from mathsgen.visuals import drawing_for
    from mathsgen.circle_figures import labels_clear, CHECK_WIDTHS
    from mathsgen.similar_shapes import FORMS, FAMILY
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    generator = registry.get("geometry.similarity.scale_factors")
    require(generator.info.version == 2, "Expected similarity v2")
    specimens, checked = [], 0
    for level in range(1, 5):
        forms, shapes, names, shown = set(), set(), set(), set()
        for seed in range(SEEDS):
            q = generator.generate(seed, level)
            generator.validate(q)
            generator.validate_independently(q)
            p = q.parameters
            forms.add(p["form"])
            names.add(p["names"])
            shapes.add(str({k: v for k, v in p.items() if k not in ("names", "form")}))
            if p["form"] not in shown:
                shown.add(p["form"])
                specimens.append(q)
                print("L{} [{}] {}".format(level, p["form"], q.prompt.text))
                print("  Answer:", q.answer_display.text)
            if seed < 5:
                family = FAMILY[p["form"]]
                bumpers = {
                    "pair": lambda: dict(p, sides=[p["sides"][0] + p["scale"][1]] + p["sides"][1:]),
                    "nested": lambda: dict(p, de=p["de"] + 1),
                    "area": lambda: dict(p, height=p["height"] + 1),
                    "solid": lambda: dict(p, dims=[p["dims"][0] + p["scale"][1]] + p["dims"][1:]),
                }
                tampered = [dict(p, form="banana"), dict(p, names="ZZZ"), bumpers[family]()]
                if "orientations" in p:
                    tampered.append(dict(p, orientations=[[999, False], [0, False]]))
                if "orientation" in p:
                    tampered.append(dict(p, orientation=[999, False]))
                for bad in tampered:
                    require(rejects(generator.validate, replace(q, parameters=bad)),
                            "Tampered parameters accepted: " + str(bad))
            value = q.answer["value"]
            for wrong in (value + 1, value * 2):
                bad = replace(q, answer=dict(q.answer, value=wrong))
                for checker in (generator.validate, generator.validate_independently):
                    require(rejects(checker, bad), "Wrong answer accepted")
            require(rejects(generator.validate, replace(q, prompt=Content("Wrong"))),
                    "Wrong prompt accepted")
            asset = q.visual_assets("questions")[0]
            require(labels_clear(asset), "Label touches a line")
            for width in CHECK_WIDTHS:
                drawing_for(asset, width)
            checked += 1
        require(forms == set(FORMS[level]),
                "Level {} forms: saw {}".format(level, sorted(forms)))
        require(len(shapes) >= 30, "Figures lack variety")
        print("Level {}: forms {}, {} distinct figures, {} letter sets".format(
            level, sorted(forms), len(shapes), len(names)))

    report = export_worksheet(
        Worksheet(
            id="similar-shapes-v2-specimens",
            title="Similar shapes: lengths, areas and volumes",
            seed=20260923, specification={"specimens": True},
            questions=tuple(specimens),
        ),
        _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
    )
    print("Specimen:", report["directory"])
    print("PASS:", checked, "questions; invariants, tampering, label clearance, "
          "three widths and PDF")


if __name__ == "__main__":
    main()