"""Exercise old and applied surd forms, exact answers and rotated diagrams."""
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dataclasses import replace
from fractions import Fraction
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import require, rational_text
    from mathsgen.surds import answer_for, presentation, right_triangle_scene
    from mathsgen.visuals import drawing_for
    from mathsgen.pdf import render_pdf

    generator = registry.get("number.surds.manipulation")
    expected = {
        1: {"simplify", "collect"},
        2: {"multiply", "divide"},
        3: {"expand", "right_triangle"},
        4: {"rationalise", "rectangle_perimeter"},
    }
    specimen_samples = {}
    for level in range(1, 5):
        seen = set()
        orientations = set()
        independent = {}
        for seed in range(60):
            q = generator.generate(seed, level)
            form = q.parameters["form"]
            seen.add(form)
            variant = (form + "_" + str(len(q.parameters["denominator"]))
                       if form == "rationalise" else form)
            specimen_samples.setdefault((level, variant), q)
            if form == "right_triangle":
                orientations.add(tuple(q.parameters["orientation"]))
                for width in (360, 250):
                    drawing_for(q.question_visuals[0], width)
            if independent.get(form, 0) < 8:
                generator.validate_independently(q)
                independent[form] = independent.get(form, 0) + 1
            wrong = dict(q.answer)
            wrong["terms"] = [list(term) for term in wrong["terms"]]
            wrong["terms"][0][0] = rational_text(
                Fraction(wrong["terms"][0][0]) + 1
            )
            try:
                generator.validate(replace(q, answer=wrong))
            except ValueError:
                pass
            else:
                raise AssertionError("Wrong surd answer accepted")
        require(seen == expected[level], "Missing surd form at level {}".format(level))
        if level == 3:
            require(len(orientations) >= 3, "Triangle diagrams do not vary")
        print("L{}: {}; {} triangle orientations".format(
            level, sorted(seen), len(orientations)
        ))

    for level, parameters, terms in (
        (3, {"form": "right_triangle", "leg": 6,
             "orientation": [0, False]}, [["12", 1], ["6", 2]]),
        (4, {"form": "rectangle_perimeter", "width_rational": 4,
             "width_radicand": 7, "area": 18}, [["24", 1], ["-2", 7]]),
    ):
        q = generator.generate(12345, level)
        answer, display = answer_for(parameters)
        require(answer["terms"] == terms, "Known surd example changed")
        known = replace(
            q, parameters=parameters, answer=answer, answer_display=display,
            prompt=presentation(parameters),
            question_visuals=((right_triangle_scene(parameters),)
                              if level == 3 else ()),
        )
        generator.validate(known)
        generator.validate_independently(known)

    export_root = ROOT / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(
        prefix="surds_progression_", dir=str(export_root)
    ))
    worksheet = SimpleNamespace(
        title="Surds progression", id="surds-progression",
        specification={},
        questions=[specimen_samples[key] for key in sorted(specimen_samples)],
    )
    for mode in ("questions", "answers"):
        print("Progression specimen:",
              render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    print("PASS: surd forms, exact examples, diagram rendering and rejection.")


if __name__ == "__main__":
    main()