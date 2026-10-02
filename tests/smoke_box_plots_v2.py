"""Box plots v2: every form appears, checks agree, corruption is rejected."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from fractions import Fraction
from pathlib import Path
import tempfile
from types import SimpleNamespace

from launch_mathsgen import load_engine


def reject(check, question):
    try:
        check(question)
    except (ValueError, KeyError, TypeError):
        return
    raise AssertionError("Corrupted question accepted")


def main():
    registry = load_engine()
    from mathsgen.box_plot_questions import (
        BoxPlots, FORMS, estimate_percent, percent_text,
    )
    from mathsgen.pdf import render_pdf
    from mathsgen.project_paths import EXPORTS_ROOT

    registered = registry.get("data.spread.box_plots")
    assert registered.info.version == 2, registered.info.version

    # Known values: halfway into the third section is 62.5% below.
    assert estimate_percent(2, "below") == Fraction(125, 2)
    assert percent_text(estimate_percent(2, "below")) == "62.5"
    assert percent_text(estimate_percent(0, "above")) == "87.5"

    generator = BoxPlots()
    seen = {}
    specimen = []
    for level in sorted(FORMS):
        for seed in range(200):
            question = generator.generate(seed, level)
            generator.validate_independently(question)
            form = question.parameters["form"]
            seen[form] = seen.get(form, 0) + 1
            if seen[form] == 1:
                specimen.append(question)
                print("L{} {}: {}".format(level, form, question.prompt.text[:220]))
                print("   -> " + question.answer_display.text)
                reject(generator.validate, replace(
                    question, answer=dict(question.answer, kind="wrong")))
                reject(generator.validate, replace(
                    question, parameters=dict(question.parameters, context=99)))
    missing = [form for forms in FORMS.values() for form in forms if form not in seen]
    assert not missing, "Forms never generated: {}".format(missing)
    print("Form counts:", seen)

    worksheet = SimpleNamespace(
        title="Box plots v2 specimen", id="box-plots-v2",
        specification={}, questions=specimen,
    )
    directory = Path(tempfile.mkdtemp(prefix="box_plots_v2_", dir=str(EXPORTS_ROOT)))
    print(render_pdf(worksheet, directory / "questions.pdf", "questions"))
    print(render_pdf(worksheet, directory / "answers.pdf", "answers"))
    print("PASS: box plots v2, nine forms, independent checks, rejection, specimen.")


if __name__ == "__main__":
    main()