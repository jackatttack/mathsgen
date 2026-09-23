"""Exercise white panels, diagrams, plots, choices and page breaks."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

import tempfile
from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace

from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import Content, Choice, LayoutHint, require
    from mathsgen.pdf import render_pdf, WorkingSpace
    from mathsgen.squared_page import white_panel
    from mathsgen.content_rendering import content_flowables
    from mathsgen.pdf import styles

    ids = [
        "problem_solving.liquid_flow.tanks",
        "problem_solving.related_solids.volume",
        "problem_solving.painting.budget",
        "geometry.transformations.reflection",
    ]
    questions = [
        registry.get(generator_id).generate(12345, 4)
        for generator_id in ids
    ]
    base = questions[0]
    legacy = replace(
        base,
        prompt=Content("Find f(5), where f(x) = 6x + 6.", "f(x)=6x+6", "Find f(5), where"),
        answer_display=Content("36", "36"),
        question_visuals=(),
        layout_hint=LayoutHint(working_lines=3),
    )
    choice = replace(
        legacy, prompt=Content("Choose the correct expression."),
        choices=(
            Choice("a", Content("x + 2", "x+2")),
            Choice("b", Content("x squared", blocks=(
                {"kind": "equation", "tex": "x^{2}", "text": "x squared"},
            ))),
        ),
    )
    questions = [legacy, choice] + questions

    paragraphs = content_flowables(questions[2].prompt, styles()["body"])
    panel = white_panel(paragraphs, 460)
    width, height = panel.wrap(460, 700)
    require(width == 460 and height > 12, "Panel measurement failed")
    require(WorkingSpace(7).wrap(460, 700)[1] == 134,
            "Working-space allocation changed")

    root = Path(__file__).resolve().parent.parent / "exports"
    root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="squared_page_specimen_", dir=str(root)))
    worksheet = SimpleNamespace(
        title="Squared-page layout specimen",
        id="squared-page-layout",
        specification={},
        questions=questions,
    )
    for mode in ("questions", "answers"):
        report = render_pdf(worksheet, directory / (mode + ".pdf"), mode)
        print(report)
        require(report["pages"] >= 1 and report["bytes"] > 0, "Empty export")
    print("PASS: measured panels, retained working space and actual PDF export")
    print("covering legacy maths, rich content, choices, scenes and square plots.")
    print("Review question.pdf backgrounds, page breaks and white panel coverage.")
    print("Specimen directory:", directory)


if __name__ == "__main__":
    main()