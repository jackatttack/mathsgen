"""Check visual audiences and export an integrated worksheet on Pythonista."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import tempfile

from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import Content, LayoutHint, canonical_json, require
    from mathsgen.worksheets import build_worksheet
    from mathsgen.export import export_worksheet
    from mathsgen.pdf import visual_blocks

    def rejects(action, fragment):
        try:
            action()
        except ValueError as error:
            require(fragment in str(error), "Unexpected rejection: " + str(error))
        else:
            raise AssertionError("Expected rejection: " + fragment)

    spec = {
        "title": "Visual layout integration",
        "shuffle": False,
        "sections": [{
            "generator_ids": ["algebra.linear.two_sided"],
            "count": 3,
            "difficulties": [1],
        }],
    }
    original = build_worksheet(spec, 20260919, registry)
    base = original.questions[0]

    grid = {
        "kind": "plot", "version": 1,
        "x_range": [-3, 3], "y_range": [-5, 7],
        "x_step": 1, "y_step": 2,
        "minor_divisions": 2, "equal_units": False,
        "x_label": "x", "y_label": "y",
    }
    completed = deepcopy(grid)
    completed["curves"] = [{"segments": [[[-3, -5], [3, 7]]]}]
    table = {
        "kind": "table", "version": 1,
        "headers": ["x", "-2", "-1", "0", "1", "2"],
        "rows": [["y", "-3", "-1", "1", "3", "5"]],
    }
    graph_question = replace(
        base,
        id="visual-layout-graph-v1",
        generator_id="specimen.visual_layout.graph",
        prompt=Content(
            "Draw the graph of y = 2x + 1 using the table and grid below. "
            "The table gives x = -2, -1, 0, 1, 2 and y = -3, -1, 1, 3, 5."
        ),
        answer={"kind": "line", "gradient": "2", "intercept": "1"},
        answer_display=Content("The straight line y = 2x + 1.", "y = 2x + 1"),
        parameters={"gradient": "2", "intercept": "1"},
        worked_solution=(),
        layout_hint=LayoutHint(working_lines=0),
        question_visuals=(table, grid),
        answer_visuals=(completed,),
    )
    triangle = {
        "kind": "scene", "version": 1, "width": 360, "height": 180,
        "caption": "Not drawn accurately",
        "nodes": [
            {"type": "polygon", "points": [[70, 40], [280, 40], [70, 150]]},
            {"type": "right_angle", "vertex": [70, 40],
             "first": [280, 40], "second": [70, 150]},
            {"type": "label", "point": [175, 20], "text": "4 cm"},
            {"type": "label", "point": [40, 95], "text": "3 cm"},
            {"type": "label", "point": [195, 115], "text": "x"},
        ],
    }
    triangle_question = replace(
        base,
        id="visual-layout-triangle-v1",
        generator_id="specimen.visual_layout.triangle",
        prompt=Content(
            "A right-angled triangle has perpendicular sides of 3 cm and "
            "4 cm. Find the hypotenuse x."
        ),
        answer={"kind": "length", "value": "5", "unit": "cm"},
        answer_display=Content("x = 5 cm"),
        parameters={"legs": [3, 4], "hypotenuse": 5},
        worked_solution=(),
        layout_hint=LayoutHint(working_lines=3),
        diagram=triangle,
    )

    require(graph_question.visual_assets("questions") == (table, grid),
            "Question asset order changed")
    require(graph_question.visual_assets("answers") == (completed,),
            "Answer routing failed")
    require(triangle_question.visual_assets("questions") == (triangle,),
            "Legacy diagram was lost")
    require(not triangle_question.visual_assets("answers"),
            "Legacy diagram unexpectedly appeared on answer sheet")
    require(not base.visual_assets(), "Old text question gained an asset")

    student_specs = [
        block.spec for block in visual_blocks(graph_question, "questions")
        if hasattr(block, "spec")
    ]
    answer_specs = [
        block.spec for block in visual_blocks(graph_question, "answers")
        if hasattr(block, "spec")
    ]
    require(student_specs == [table, grid], "PDF student routing failed")
    require(answer_specs == [completed], "PDF answer routing failed")
    require("curves" not in student_specs[1], "Answer curve leaked into student grid")

    # Invalid answer graphics must not be rendered in a student PDF.
    hidden = replace(graph_question, answer_visuals=({"kind": "invalid", "version": 1},))
    require(
        [b.spec for b in visual_blocks(hidden, "questions") if hasattr(b, "spec")]
        == [table, grid],
        "Student route depends on answer graphics",
    )
    rejects(
        lambda: replace(graph_question, diagram=triangle).visual_assets(),
        "Use diagram or question_visuals",
    )
    rejects(
        lambda: replace(graph_question, question_visuals=("bad",)).visual_assets(),
        "must contain visual specifications",
    )

    # Use a temporary registry wrapper to exercise duplicate detection.
    class FixtureGenerator:
        info = registry.get("algebra.linear.two_sided").info

        def __init__(self, answer_only=False):
            self.calls = 0
            self.answer_only = answer_only

        def generate(self, seed, difficulty=1, settings=None):
            self.calls += 1
            varied = deepcopy(grid)
            varied["x_label"] = "x " + str(self.calls)
            return replace(
                graph_question, id="fixture-" + str(self.calls),
                question_visuals=(grid,) if self.answer_only else (varied,),
                answer_visuals=(varied,) if self.answer_only else (),
            )

        def validate(self, question):
            return True

    class FixtureRegistry:
        def __init__(self, generator):
            self.generator = generator

        def get(self, generator_id):
            return self.generator

    pair_spec = deepcopy(spec)
    pair_spec["sections"][0]["count"] = 2
    varied = build_worksheet(pair_spec, 7, FixtureRegistry(FixtureGenerator()))
    require(len(varied.questions) == 2, "Different visual prompts collapsed")
    rejects(
        lambda: build_worksheet(pair_spec, 7, FixtureRegistry(FixtureGenerator(True))),
        "Could not find a unique question",
    )

    payload = graph_question.to_dict()
    require(canonical_json(payload) == canonical_json(json.loads(canonical_json(payload))),
            "JSON round trip changed visual data")
    require(payload["schema_version"] == 4, "Schema version was not updated")

    with tempfile.TemporaryDirectory() as folder:
        # Student export succeeds despite an intentionally unsupported answer asset.
        export_worksheet(replace(original, questions=(hidden,)), folder)
        oversized = replace(
            triangle_question, diagram=None,
            question_visuals=(triangle,) * 5,
        )
        rejects(
            lambda: export_worksheet(replace(original, questions=(oversized,)), folder),
            "too tall for one page",
        )

    worksheet = replace(
        original,
        id="visual-layout-integration-v1-" + original.id,
        questions=(original.questions[0], graph_question, triangle_question),
    )
    report = export_worksheet(
        worksheet, Path(__file__).resolve().parent.parent / "exports", answers=True,
    )
    manifest = json.loads(Path(report["teacher_manifest"]).read_text(encoding="utf-8"))
    require(
        manifest["questions"][1]["answer_visuals"] == [completed],
        "Teacher manifest lost answer visuals",
    )
    print("PASS: audience routing, ordered assets and legacy diagrams.")
    print("PASS: visual duplicate detection and JSON preservation.")
    print("PASS: student export excludes answer assets; oversized questions rejected.")
    print("Specimens only: no new production generators registered.")
    print(json.dumps(report, indent=2))
    print("Open questions.pdf and answers.pdf for visual review.")


if __name__ == "__main__":
    main()