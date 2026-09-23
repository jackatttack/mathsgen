"""Check graph isolation, point membership and rearranged gradient answers."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import require, rational_text
    from mathsgen.visuals import drawing_for
    from mathsgen.worksheets import build_worksheet
    from mathsgen.export import export_worksheet
    from mathsgen.pdf import render_pdf
    generator = registry.get("algebra.graphs.straight_lines")

    def reject(check, q):
        try:
            check(q)
        except ValueError:
            return
        raise AssertionError("Corrupted line question accepted")

    for level in range(1, 5):
        q = generator.generate(12345, level)
        generator.validate_independently(q)
        print("Level {}: {}".format(level, q.prompt.text))
        print("Answer:", q.answer_display.text)
        for asset in q.visual_assets("worked"):
            for width in (360, 250):
                drawing_for(asset, width)
        bad = dict(q.answer)
        if "on_line" in bad:
            bad["on_line"] = not bad["on_line"]
        elif "m" in bad:
            bad["m"] = rational_text(Fraction(bad["m"]) + 1)
        else:
            bad["x"] += 1
        for check in (generator.validate, generator.validate_independently):
            reject(check, replace(q, answer=bad))
        if level == 1:
            require("curves" not in q.question_visuals[0], "Student grid contains answer")
            require("curves" in q.answer_visuals[0], "Completed graph missing")
            altered = deepcopy(q.answer_visuals[0])
            altered["curves"][0]["segments"][0][0][1] += 1
            reject(generator.validate, replace(q, answer_visuals=(altered,)))

    forms = {3: set(), 4: set()}
    samples = {}
    outcomes = set()
    for level in (3, 4):
        independent = {}
        for seed in range(60):
            q = generator.generate(seed, level)
            form = q.parameters.get("form", "membership" if level == 3 else "implicit")
            forms[level].add(form)
            samples.setdefault((level, form), q)
            if form == "two_points":
                require(q.question_visuals[0]["points"] == q.parameters["points"],
                        "Given points are not plotted")
                require("curves" not in q.question_visuals[0],
                        "Student graph already contains the answer line")
                require("curves" in q.answer_visuals[0],
                        "Answer line missing")
            if form == "intersection":
                require("points" not in q.question_visuals[0],
                        "Student graph reveals the intersection")
                require(q.answer_visuals[0]["points"] ==
                        [[q.answer["x"], q.answer["y"]]],
                        "Answer intersection marker is misplaced")
            if independent.get(form, 0) < 8:
                generator.validate_independently(q)
                independent[form] = independent.get(form, 0) + 1
            for asset in q.visual_assets("worked"):
                for width in (360, 250):
                    drawing_for(asset, width)
            if form == "membership":
                outcomes.add(q.answer["on_line"])
            wrong = dict(q.answer)
            if form == "intersection":
                wrong["x"] += 1
            elif form == "membership":
                wrong["on_line"] = not wrong["on_line"]
            else:
                wrong["m"] = rational_text(Fraction(wrong["m"]) + 1)
            for check in (generator.validate, generator.validate_independently):
                reject(check, replace(q, answer=wrong))
    require(forms[3] == {"membership", "two_points"}, "Missing L3 graph form")
    require(forms[4] == {"implicit", "intersection"}, "Missing L4 graph form")
    require(outcomes == {True, False}, "Membership examples need both outcomes")
    print("Later-level forms:", {level: sorted(names) for level, names in forms.items()})
    export_root = Path(__file__).resolve().parent.parent / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(
        prefix="straight_progression_", dir=str(export_root)
    ))
    specimen = SimpleNamespace(
        title="Straight-line progression", id="straight-progression",
        specification={},
        questions=[generator.generate(12345, 1), generator.generate(12345, 2)]
        + [samples[key] for key in sorted(samples)],
    )
    for mode in ("questions", "answers"):
        print("Progression specimen:",
              render_pdf(specimen, directory / (mode + ".pdf"), mode))
    worksheet = build_worksheet({
        "title": "Straight-line graphs and equations", "shuffle": False,
        "sections": [{
            "generator_ids": [generator.info.id], "count": 1,
            "difficulties": [level],
        } for level in range(1, 5)],
    }, 20260919, registry)
    report = export_worksheet(
        worksheet, Path(__file__).resolve().parent.parent / "exports", answers=True,
    )
    print("PASS: four tasks, graph isolation, both point outcomes and corruption checks.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()