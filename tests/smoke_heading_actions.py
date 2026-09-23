"""Verify question-heading links and export a real layout specimen."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))


from dataclasses import replace
from pathlib import Path

from launch_mathsgen import load_engine


def main():
    from mathsgen.question_actions import (
        action_links_markup,
        available_actions,
        link_flowable,
    )
    from mathsgen.worksheets import build_worksheet
    from mathsgen.export import export_worksheet
    from mathsgen.pdf import render_pdf

    registry = load_engine()

    spec = {
        "title": "Integrated question heading layout",
        "shuffle": False,
        "show_difficulty": True,
        "sections": [{
            "generator_ids": ["geometry.circles.sectors"],
            "count": 2,
            "difficulties": [3],
        }],
    }

    worksheet = build_worksheet(spec, 20260921, registry)
    assert len(worksheet.questions) == 2

    expected_links = 0

    for number, question in enumerate(worksheet.questions, 1):
        actions = available_actions(question)
        markup = action_links_markup(question)

        assert actions
        assert markup.count("<link ") == len(actions)
        # The "another" action has been labelled "+ New" since the heading
        # layout was integrated; this test still expected the older label.
        assert "+ New" in markup
        assert "pythonista3://" in markup

        # The previous standalone API must remain usable by other
        # parts of MathsGen.
        standalone = link_flowable(question)
        assert standalone.text == markup

        expected_links += len(actions)

        print(
            "PASS: question {} has {} reusable action links".format(
                number, len(actions)
            )
        )

    output_root = Path(__file__).resolve().parent.parent / "exports"

    report = export_worksheet(
        worksheet,
        output_root,
        answers=True,
    )

    for pdf in report["pdfs"]:
        path = Path(pdf["path"])

        assert path.exists()
        assert path.read_bytes()[:5] == b"%PDF-"
        assert path.stat().st_size > 1000

        print(
            "PASS: exported {} ({} bytes)".format(
                path.name, path.stat().st_size
            )
        )
        print("PDF: " + str(path))

    question_pdf = Path(report["pdfs"][0]["path"])
    answer_pdf = Path(report["pdfs"][1]["path"])

    # ReportLab writes PDF hyperlink annotations as /URI entries.
    # Check the finished document, not merely the source markup.
    question_bytes = question_pdf.read_bytes()
    answer_bytes = answer_pdf.read_bytes()

    assert question_bytes.count(b"/URI") == expected_links, (
        "Question PDF did not preserve all clickable action links"
    )
    assert b"/URI" not in answer_bytes, (
        "Answer PDF unexpectedly contains question action links"
    )

    print(
        "PASS: {} clickable links retained in question PDF".format(
            expected_links
        )
    )
    print("PASS: answer PDF contains no question action links")

    # Disabling interactive links should still produce a valid PDF
    # without any action annotations.
    no_links_spec = dict(
        worksheet.specification,
        interactive_links=False,
    )
    no_links_worksheet = replace(
        worksheet,
        specification=no_links_spec,
    )

    no_links_path = output_root / "heading_links_disabled_specimen.pdf"

    render_pdf(
        no_links_worksheet,
        no_links_path,
        mode="questions",
    )

    assert no_links_path.read_bytes()[:5] == b"%PDF-"
    assert b"/URI" not in no_links_path.read_bytes()

    print("PASS: disabling interactive links still works")
    print("PASS: integrated heading layout export complete")
    print("VISUAL REVIEW: pending device inspection")


if __name__ == "__main__":
    main()