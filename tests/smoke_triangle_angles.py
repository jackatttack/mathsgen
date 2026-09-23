"""geometry.angles.triangle v2: forms, render checks, orientation variety, specimen."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

import tempfile
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from launch_mathsgen import load_engine

SEEDS = 40
EXPECTED = {1: {"missing"}, 2: {"isosceles_base", "isosceles_apex"},
            3: {"exterior", "isosceles_exterior"}, 4: {"algebra", "algebra_isosceles"}}


def rejects(generator, question, reason):
    try:
        generator.validate(question)
    except ValueError:
        return
    raise AssertionError("Accepted " + reason)


def main():
    registry = load_engine()
    from mathsgen.visuals import drawing_for
    from mathsgen.pdf import render_pdf
    from mathsgen import figures
    generator = registry.get("geometry.angles.triangle")
    specimen = []
    for level in (1, 2, 3, 4):
        forms, orientations, independent = {}, set(), {}
        for seed in range(SEEDS):
            q = generator.generate(seed, level)
            p = q.parameters
            forms.setdefault(p["form"], q)
            orientations.add(tuple(p["orientation"]))
            if independent.get(p["form"], 0) < 8:
                generator.validate_independently(q)
                independent[p["form"]] = independent.get(p["form"], 0) + 1
            for width in (360, 250):
                drawing_for(q.question_visuals[0], width)
            wrong = dict(q.answer, value=q.answer["value"] + 1)
            rejects(generator, replace(q, answer=wrong), "a wrong answer")
            other = [list(o) for o in figures.ORIENTATIONS if list(o) != p["orientation"]][0]
            rejects(generator, replace(q, parameters=dict(p, orientation=other)),
                    "a changed orientation")
        missing = EXPECTED[level] - set(forms)
        if missing:
            raise AssertionError("Level {} never produced {}".format(level, sorted(missing)))
        print("L{}: forms {}, {} orientations in {} seeds".format(
            level, sorted(independent.items()), len(orientations), SEEDS))
        for form in sorted(forms):
            print("  [{}] {} -> {}".format(form, forms[form].prompt.text,
                                            forms[form].answer_display.text))
        specimen += [generator.generate(seed, level) for seed in range(3)]

    export_root = Path(__file__).resolve().parent.parent / "exports"
    directory = Path(tempfile.mkdtemp(prefix="triangle_angles_v2_", dir=str(export_root)))
    worksheet = SimpleNamespace(title="Triangle angles v2", id="triangle-angles-v2",
                                specification={}, questions=specimen)
    print(render_pdf(worksheet, directory / "questions.pdf", "questions"))
    print("PASS: forms, independence, rendering at 360/250, orientation rejection, specimen.")


if __name__ == "__main__":
    main()