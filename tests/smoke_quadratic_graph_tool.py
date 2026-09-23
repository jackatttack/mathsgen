"""Validate question-specific quadratic graphs and render real specimens."""

from pathlib import Path
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from launch_mathsgen import load_engine


def main():
    from mathsgen.core import require
    from mathsgen.teacher_tools import (
        available_tools,
        build_resource,
    )
    from mathsgen.question_actions import render_support_card
    from mathsgen.worksheets import build_worksheet
    from mathsgen.export import export_worksheet

    registry = load_engine()
    generator = registry.get(
        "algebra.quadratic.factorisable_monic"
    )

    checked = 0

    with tempfile.TemporaryDirectory() as folder:
        destination = Path(folder)

        for difficulty in (1, 2, 3, 4):
            for seed in range(50):
                question = generator.generate(seed, difficulty=difficulty)
                generator.validate(question)

                tool_ids = [
                    tool.id for tool in available_tools(question)
                ]
                require(
                    "quadratic.graph" in tool_ids,
                    "Graph tool missing from a supported question",
                )

                default = build_resource(question, "quadratic.graph")
                plot = default.visuals[0]

                require(plot["kind"] == "plot", "Expected a plot")
                require(
                    not plot["points"],
                    "Default graph unexpectedly reveals the roots",
                )

                left = question.parameters["left"]
                right = question.parameters["right"]
                a, b, c = [
                    l - r for l, r in zip(left, right)
                ]

                require(a == 1, "Unexpected non-monic quadratic")

                x_low, x_high = plot["x_range"]
                y_low, y_high = plot["y_range"]

                require(
                    x_low <= 0 <= x_high,
                    "Graph does not include the y-axis",
                )
                require(
                    y_low < 0 < y_high,
                    "Graph does not include the x-axis",
                )

                curve = plot["curves"][0]["segments"][0]
                require(
                    len(curve) == 241,
                    "Graph has the wrong number of samples",
                )

                for x, y in curve:
                    require(
                        abs(y - (a * x * x + b * x + c)) < 1e-8,
                        "Graph does not match the question coefficients",
                    )

                marked = build_resource(
                    question,
                    "quadratic.graph",
                    {"show_roots": True},
                )
                points = marked.visuals[0]["points"]

                require(len(points) == 2, "Expected two marked roots")

                for x, y in points:
                    require(y == 0, "Root marker is not on the x-axis")
                    require(
                        a * x * x + b * x + c == 0,
                        "Root marker does not solve the equation",
                    )
                    require(
                        x_low <= x <= x_high,
                        "Root marker is outside the graph",
                    )

                # Render every difficulty and a range of curve shapes.
                # This exercises the existing plot renderer's bounds checks.
                if seed < 10:
                    pdf = destination / "graph_{}_{}.pdf".format(
                        difficulty, seed
                    )
                    size = render_support_card(default, pdf)
                    require(
                        pdf.read_bytes()[:5] == b"%PDF-",
                        "Graph specimen is not a PDF",
                    )
                    require(
                        size[0] > 0 and size[1] > 0,
                        "Invalid graph specimen dimensions",
                    )

                checked += 1

            print(
                "PASS: level {} — 50 coefficient and root checks".format(
                    difficulty
                )
            )

        # Rebuild the worksheet action bar using the registry.
        spec = {
            "title": "Quadratic graph quick-action specimen",
            "shuffle": False,
            "sections": [{
                "generator_ids": [generator.info.id],
                "count": 2,
                "difficulties": [2],
            }],
        }
        worksheet = build_worksheet(spec, 20260921, registry)

        from mathsgen.question_actions import available_actions

        for question in worksheet.questions:
            action_ids = [
                action for action, label in available_actions(question)
            ]
            require(
                "tool:quadratic.graph" in action_ids,
                "Graph quick action missing from PDF heading",
            )

        report = export_worksheet(
            worksheet,
            PROJECT_ROOT / "exports",
            answers=True,
        )

        questions_pdf = Path(report["pdfs"][0]["path"])
        require(
            questions_pdf.read_bytes()[:5] == b"%PDF-",
            "Question worksheet PDF failed to export",
        )

        print("PASS: {} quadratic graph cases".format(checked))
        print("PASS: 40 graph PDFs rendered")
        print("PASS: Graph included in registry-driven PDF heading")
        print("PDF:", questions_pdf)
        print("DEVICE GRAPH CLIPBOARD AND VISUAL REVIEW: pending")


if __name__ == "__main__":
    main()