"""All frequency-mean forms, exact reverse cases and student/answer specimen."""
import sys
import tempfile
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from launch_mathsgen import load_engine


def reject(checker, q):
    try:
        checker(q)
    except ValueError:
        return
    raise AssertionError("Corrupt frequency-mean answer accepted")


def main():
    registry = load_engine()
    from mathsgen.core import require, rational_text
    from mathsgen.frequency_mean_forms import parts
    from mathsgen.visuals import drawing_for
    from mathsgen.pdf import render_pdf

    generator = registry.get("data.mean.frequency_table")
    samples = {}
    for level in range(1, 5):
        seen, independent = set(), {}
        for seed in range(60):
            q = generator.generate(seed, level)
            form = q.parameters.get("form", "mean")
            seen.add(form)
            samples.setdefault((level, form), q)
            if independent.get(form, 0) < 8:
                generator.validate_independently(q)
                independent[form] = independent.get(form, 0) + 1
            for width in (360, 250):
                drawing_for(q.question_visuals[0], width)
            wrong = dict(q.answer, value=rational_text(
                Fraction(q.answer["value"]) + 1
            ))
            reject(generator.validate, replace(q, answer=wrong))
            reject(generator.validate_independently, replace(q, answer=wrong))
        expected = {
            1: {"mean"}, 2: {"mean"},
            3: {"mean", "missing_frequency"},
            4: {"mean", "target_observation", "combined_mean"},
        }[level]
        require(seen == expected, "Missing frequency form at L{}".format(level))
        print("L{} forms: {}".format(level, sorted(seen)))

    for level, p, answer in (
        (3, {"form": "missing_frequency", "values": ["1", "2", "4", "7"],
             "frequencies": [2, None, 3, 1], "mean": "29/10"}, "4"),
        (4, {"form": "target_observation",
             "values": ["-3/2", "-1", "1", "5/2"],
             "frequencies": [3, 4, 6, 6], "mean": "7/10"}, "3/2"),
        (4, {"form": "combined_mean",
             "values": ["-3/2", "-1/2", "1", "5/2"],
             "first": [1, 2, 3, 2], "second": [2, 2, 4, 4]}, "31/40"),
    ):
        prompt, table, calculated, display = parts(p)
        require(calculated["value"] == answer, "Known frequency result changed")
        q = generator.generate(12345, level)
        known = replace(q, parameters=p, prompt=prompt, answer=calculated,
                        answer_display=display, question_visuals=(table,),
                        marks=4, layout_hint=replace(
                            q.layout_hint, working_lines=5 if level == 3 else 6
                        ))
        generator.validate(known)
        generator.validate_independently(known)

    export_root = ROOT / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="frequency_progression_",
                                      dir=str(export_root)))
    worksheet = SimpleNamespace(
        title="Frequency-table mean progression", id="frequency-progression",
        specification={}, questions=[samples[key] for key in sorted(samples)],
    )
    for mode in ("questions", "answers"):
        print(render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    print("PASS: frequency forms, reverse examples, render widths and rejection.")


if __name__ == "__main__":
    main()