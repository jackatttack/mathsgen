"""Check registry-driven PDF quick actions and actual PDF annotations."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))


from pathlib import Path
from urllib.parse import parse_qs, urlparse

from launch_mathsgen import load_engine


def linked_action(url):
    arguments = parse_qs(urlparse(url).query).get("argv", [])
    assert len(arguments) == 2
    return arguments[0]


def pdf_actions(path):
    from pypdf import PdfReader

    actions = []

    for page in PdfReader(str(path)).pages:
        for reference in page.get("/Annots", []):
            annotation = reference.get_object()

            if annotation.get("/Subtype") != "/Link":
                continue

            action = annotation.get("/A")

            if action is None or action.get("/URI") is None:
                continue

            actions.append(linked_action(str(action["/URI"])))

    return actions


def main():
    from mathsgen.question_actions import (
        ACTIONS,
        action_url,
        available_actions,
    )
    from mathsgen.teacher_tools import available_tools
    from mathsgen.worksheets import build_worksheet
    from mathsgen.export import export_worksheet

    registry = load_engine()

    cases = (
        (
            "algebra.quadratic.factorisable_monic",
            "tool:quadratic.formula",
        ),
        (
            "geometry.trigonometry.right_angled",
            "tool:trigonometry.sohcahtoa",
        ),
        (
            "algebra.linear.two_sided",
            None,
        ),
    )

    for generator_id, expected_tool_action in cases:
        question = registry.get(generator_id).generate(
            20260921,
            difficulty=2,
        )

        actions = available_actions(question)
        action_ids = [action for action, label in actions]

        assert action_ids[0] == "another"
        assert "answer" in action_ids
        assert action_ids[-1] == "tools"

        discovered = {
            "tool:" + tool.id
            for tool in available_tools(question)
            if tool.kind in ("formula", "diagram")
        }

        linked = {
            action for action in action_ids
            if action.startswith("tool:")
        }

        assert linked == discovered

        if expected_tool_action is not None:
            assert expected_tool_action in linked
        else:
            assert not linked

        for action, label in actions:
            assert linked_action(
                action_url(question, action)
            ) == action

        print(
            "PASS: {} quick actions: {}".format(
                generator_id,
                ", ".join(label for action, label in actions),
            )
        )

    assert "facts" in ACTIONS and "hint" in ACTIONS
    print("PASS: older Facts and Hint actions remain recognised")

    spec = {
        "title": "Direct teacher-tool action specimen",
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

    report = export_worksheet(
        worksheet,
        Path(__file__).resolve().parent.parent / "exports",
        answers=True,
    )

    question_pdf = Path(report["pdfs"][0]["path"])
    answer_pdf = Path(report["pdfs"][1]["path"])

    actual_actions = pdf_actions(question_pdf)
    expected_actions = [
        action
        for question in worksheet.questions
        for action, label in available_actions(question)
    ]

    assert sorted(actual_actions) == sorted(expected_actions), (
        "PDF quick-action annotations do not match the registry"
    )
    assert not pdf_actions(answer_pdf)

    print(
        "PASS: {} clickable PDF quick actions".format(
            len(actual_actions)
        )
    )
    print("PASS: answer sheet contains no quick-action links")
    print("PDF:", question_pdf)
    print("PASS: dynamic question-heading integration")
    print("DEVICE QUICK COPY: manual verification pending")


if __name__ == "__main__":
    main()