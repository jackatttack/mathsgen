"""Multi-step circles v2: chains vs hand formulas, steps, variety, tampering, PDF."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from fractions import Fraction
from launch_mathsgen import load_engine


SEEDS = 50


def hand_answer(p):
    chain = p["chain"]
    if chain == "algebra_centre_cyclic":
        (k, b), (_, c) = p["u"], p["v"]
        return Fraction(360 - b - 2 * c, k + 2)
    s = p["start"]
    return {
        "centre_then_cyclic": 180 - Fraction(s, 2),
        "semicircle_then_triangle": 90 - s,
        "tangent_then_isosceles": 2 * s,
        "kite_then_circumference": 90 - Fraction(s, 2),
        "semicircle_then_same_segment": 90 - s,
        "alternate_then_centre": 90 - s,
        "kite_then_reflex": 90 + Fraction(s, 2),
    }[chain]


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
    from mathsgen.multi_step_circles import FORMS, REASONING
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    generator = registry.get("geometry.circle_theorems.multi_step")
    require(generator.info.version == 2, "Expected multi-step circles v2")
    specimens, checked = [], 0
    for level in range(1, 5):
        chains, orientations, names, shown = set(), set(), set(), set()
        for seed in range(SEEDS):
            q = generator.generate(seed, level)
            generator.validate(q)
            generator.validate_independently(q)
            p = q.parameters
            require(q.answer["value"] == hand_answer(p),
                    "Hand formula disagrees for " + p["chain"])
            require(len(q.answer["steps"]) == len(REASONING[p["chain"]]),
                    "Every reason needs a step")
            chains.add(p["chain"])
            orientations.add(tuple(p["orientation"]))
            names.add(p["names"])
            if p["chain"] not in shown:
                shown.add(p["chain"])
                specimens.append(q)
                print("L{} [{}] {}".format(level, p["chain"], q.prompt.text))
                print("  Steps:", q.answer["steps"], "->", q.answer_display.text)
            if seed < 5:
                tampered = [dict(p, orientation=[999, False]), dict(p, chain="banana"),
                            dict(p, names="ZZZZZZZ")]
                if "start" in p:
                    tampered.append(dict(p, start=p["start"] + 2))
                else:
                    tampered.append(dict(p, u=[p["u"][0], p["u"][1] + 2]))
                if p["free"]:
                    tampered.append(dict(p, free=[p["free"][0] + 5] + p["free"][1:]))
                for bad in tampered:
                    require(rejects(generator.validate, replace(q, parameters=bad)),
                            "Tampered parameters accepted: " + str(bad))
                wrong_steps = dict(q.answer, steps=q.answer["steps"][:-1] + ["1"])
                require(rejects(generator.validate, replace(q, answer=wrong_steps)),
                        "Wrong steps accepted")
            value = q.answer["value"]
            for wrong in (value + 1, value - 2):
                bad = replace(q, answer=dict(q.answer, value=wrong))
                for checker in (generator.validate, generator.validate_independently):
                    require(rejects(checker, bad), "Wrong angle accepted")
            require(rejects(generator.validate, replace(q, prompt=Content("Wrong"))),
                    "Wrong prompt accepted")
            asset = q.visual_assets("questions")[0]
            require(labels_clear(asset), "Label touches a line")
            for width in CHECK_WIDTHS:
                drawing_for(asset, width)
            checked += 1
        require(chains == set(FORMS[level]),
                "Level {} chains: saw {}".format(level, sorted(chains)))
        require(len(orientations) >= 3, "Orientations lack variety")
        require(len(names) >= 3, "Letter sets lack variety")
        print("Level {}: chains {}, {} orientations, {} letter sets".format(
            level, sorted(chains), len(orientations), len(names)))

    report = export_worksheet(
        Worksheet(
            id="multi-step-circles-v2-specimens", title="Circle theorems: multi-step",
            seed=20260923, specification={"specimens": True},
            questions=tuple(specimens),
        ),
        _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
    )
    print("Specimen:", report["directory"])
    print("PASS:", checked, "questions; hand formulas, steps, measured figures, "
          "tampering, label clearance, three widths and PDF")


if __name__ == "__main__":
    main()