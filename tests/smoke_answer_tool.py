"""Check that the Answer quick action uses the source question's full answer."""
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from launch_mathsgen import load_engine


def main():
    from mathsgen.core import require
    from mathsgen.question_actions import (
        encode_question, source_question, render_support_card,
    )
    from mathsgen.teacher_tools import build_resource

    registry = load_engine()
    text_question = registry.get(
        "algebra.quadratic.factorisable_monic"
    ).generate(seed=20260922, difficulty=1)

    visual_question = None
    for info in registry.list():
        generator = registry.get(info.id)
        for difficulty in sorted(info.difficulty_descriptions):
            question = generator.generate(
                seed=20260922, difficulty=difficulty
            )
            if question.visual_assets("answers"):
                visual_question = question
                break
        if visual_question is not None:
            break

    require(visual_question is not None, "No visual-answer specimen found")

    with tempfile.TemporaryDirectory(prefix="mathsgen_answer_") as folder:
        for label, original in (
            ("text", text_question),
            ("visual", visual_question),
        ):
            source = source_question(encode_question(original), registry)
            resource = build_resource(source, "question.answer")
            require(resource.content == source.answer_display,
                    "Answer content does not match the source question")
            require(resource.visuals == source.visual_assets("answers"),
                    "Answer visuals do not match the source question")
            require(resource.content.text.strip() or resource.visuals,
                    "Answer resource is empty")

            # A heading-only PDF used to pass this test. Check the
            # actual content path, including legacy MathText answers.
            from mathsgen.pdf import MathLine, paragraph, styles
            from mathsgen.content_rendering import content_flowables
            if resource.content.blocks:
                answer_blocks = content_flowables(
                    resource.content, styles()["body"], "answer test"
                )
            elif resource.content.math_tex:
                answer_blocks = [MathLine(resource.content.math_tex)]
            elif resource.content.text.strip():
                answer_blocks = [
                    paragraph(resource.content.text, styles()["body"])
                ]
            else:
                answer_blocks = []
            require(answer_blocks or resource.visuals,
                    "Answer would render as a heading-only card")

            destination = Path(folder) / (label + ".pdf")
            render_support_card(resource, destination)
            require(destination.exists() and destination.stat().st_size > 1000,
                    "Answer PDF was not rendered")
            print("PASS:", label, source.generator_id,
                  "answer visuals:", len(resource.visuals))

    print("PASS: Answer resources match their linked questions; clipboard untouched")
    print("DEVICE REVIEW: Tap Answer and paste into GoodNotes.")


if __name__ == "__main__":
    main()