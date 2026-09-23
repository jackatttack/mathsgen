"""Surface area v4: forms, net sums, tampering, labels, PDF."""
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
    from mathsgen.prism_surface_area import FORMS
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    generator = registry.get("geometry.surface_area.prisms")
    require(generator.info.version == 4, "Expected surface area v4")
    specimens, checked = [], 0
    for level in range(1, 5):
        forms, seen, shown = set(), set(), set()
        for seed in range(SEEDS):
            q = generator.generate(seed, level)
            generator.validate(q)
            generator.validate_independently(q)
            p = q.parameters
            forms.add(p["form"])
            if p["shape"] in ("cylinder", "open_cylinder"):
                require("pi" in q.prompt.text, "Cylinder prompt lost its pi: " + q.prompt.text)
            seen.add(str(sorted(p["dims"].items())) + str(p["style"]) + str(p["mirror"])
                     + str(p.get("area")))
            if p["form"] not in shown:
                shown.add(p["form"])
                specimens.append(q)
                print("L{} [{}/{}] {}".format(level, p["form"], p["shape"], q.prompt.text))
                print("  Answer:", q.answer_display.text)
            if seed < 5:
                tampered = [dict(p, form="banana"), dict(p, mirror="yes")]
                if p["dims"]:
                    key = sorted(p["dims"])[-1]
                    tampered.append(dict(p, dims=dict(p["dims"], **{key: p["dims"][key] + 1})))
                if "area" in p:
                    tampered.append(dict(p, area=str(Fraction(p["area"]) + 1)))
                for bad in tampered:
                    require(rejects(generator.validate, replace(q, parameters=bad)),
                            "Tampered parameters accepted: " + str(bad))
            wrong = dict(q.answer, value=rational_text(Fraction(q.answer["value"]) + 1))
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
        print("Level {}: forms {}, {} distinct questions".format(level, sorted(forms), len(seen)))

    report = export_worksheet(
        Worksheet(id="surface-area-v4-specimens", title="Surface area of prisms and cylinders",
                  seed=20260923, specification={"specimens": True},
                  questions=tuple(specimens)),
        _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
    )
    print("Specimen:", report["directory"])
    print("PASS:", checked, "questions; net sums, tampering, label clearance, "
          "three widths and PDF")


if __name__ == "__main__":
    main()