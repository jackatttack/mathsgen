"""Verify the new worksheet action bar without modifying the clipboard.

Exercises real question reconstruction, action URLs, PDF rendering and
hyperlink annotations. The Pythonista toolbox is opened manually afterwards.
"""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))


from pathlib import Path

from launch_mathsgen import load_engine


def main():
    from pypdf import PdfReader

    from mathsgen.question_actions import (
        ACTIONS,
        action_url,
        available_actions,
        decode_question,
        encode_question,
        source_question,
    )
    from mathsgen.teacher_tools import available_tools
    from mathsgen.worksheets import build_worksheet
    from mathsgen.export import export_worksheet

    registry = load_engine()

    spec = {
        "title": "Teacher toolbox action-bar specimen",
        "shuffle": False,
        "show_difficulty": True,
        "sections": [{
            "generator_ids": [
                "algebra.quadratic.factorisable_monic",
            ],
            "count": 2,
            "difficulties": [2],
        }],
    }

    worksheet = build_worksheet(spec, 20260921, registry)

    assert len(worksheet.questions) == 2

    for question in worksheet.questions:
        labels = available_actions(question)

        assert labels == [
            ("another", "Another like this"),
            ("tools", "Tools"),
            ("answer", "Answer"),
        ]

        token = encode_question(question)
        restored = source_question(token, registry)

        assert restored.id == question.id
        assert decode_question(token)["generator"] == question.generator_id

        for action, label in labels:
            url = action_url(question, action)

            assert url.startswith("pythonista3://")
            assert "argv=" + action in url

        assert "facts" in ACTIONS
        assert "hint" in ACTIONS

        tool_ids = [
            tool.id for tool in available_tools(question)
        ]

        assert "quadratic.formula" in tool_ids
        assert "question.answer" in tool_ids

    print("PASS: current heading has New, Tools and Answer")
    print("PASS: original question reconstructs from its URL token")
    print("PASS: legacy Facts and Hint URL actions remain available")
    print("PASS: quadratic and answer tools are registered")

    report = export_worksheet(
        worksheet,
        Path(__file__).resolve().parent.parent / "exports",
        answers=True,
    )

    question_pdf = Path(report["pdfs"][0]["path"])
    answer_pdf = Path(report["pdfs"][1]["path"])

    assert question_pdf.exists()
    assert answer_pdf.exists()

    def pdf_links(path):
        reader = PdfReader(str(path))
        urls = []

        for page in reader.pages:
            for reference in page.get("/Annots", []):
                annotation = reference.get_object()

                if annotation.get("/Subtype") != "/Link":
                    continue

                action = annotation.get("/A")

                if action is None:
                    continue

                uri = action.get("/URI")

                if uri is not None:
                    urls.append(str(uri))

        return urls

    question_urls = pdf_links(question_pdf)
    answer_urls = pdf_links(answer_pdf)

    # Three actions per question, counted from actual PDF annotations.
    # Raw /URI byte counts are unreliable because PDF strings and
    # annotation dictionaries can each contain that marker.
    assert len(question_urls) == len(worksheet.questions) * 3, (
        "Question PDF does not contain the expected action annotations"
    )

    for action in ("another", "tools", "answer"):
        matching = [
            url for url in question_urls
            if "argv=" + action in url
        ]

        assert len(matching) == len(worksheet.questions), (
            "Missing or duplicated PDF action: " + action
        )

    assert not answer_urls, (
        "Answer sheet unexpectedly contains question action links"
    )

    print("PASS: all six PDF hyperlink annotations are present")
    print("PASS: answer sheet has no question action links")
    print("PASS: questions.pdf exported successfully")
    print("PDF:", question_pdf)
    print("PASS: teacher action-bar integration smoke complete")
    print("DEVICE TOOLBOX AND CLIPBOARD: manual verification pending")


if __name__ == "__main__":
    main()