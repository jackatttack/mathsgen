"""Rich content contract, legacy compatibility and actual PDF integration."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

import json
import tempfile
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import Content, Choice, LayoutHint, require
    from mathsgen.pdf import question_prompt, render_pdf, styles
    from mathsgen.content_rendering import content_flowables

    legacy = Content("Full text", "x+1", "Find")
    require(not legacy.blocks, "Legacy positional fields changed")
    rich = Content("The answer is x = 2.", blocks=(
        {"kind": "paragraph", "text": "The answer is"},
        {"kind": "equation", "tex": "x=2", "text": "x = 2"},
        {"kind": "paragraph", "text": "This explanation must remain visible."},
    ))
    rebuilt = Content(**json.loads(json.dumps(asdict(rich))))
    require(asdict(rebuilt)["text"] == rich.text, "Fallback lost")
    require(len(rebuilt.blocks) == 3, "JSON blocks lost")
    invalid = [
        {"text": "fallback", "math_tex": "x", "blocks": rich.blocks},
        {"text": "fallback", "blocks": ({"kind": "unknown"},)},
        {"text": "fallback", "blocks": (
            {"kind": "paragraph", "text": "both", "runs": [{"text": "invalid"}]},
        )},
    ]
    for data in invalid:
        try:
            Content(**data)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid rich content accepted")

    generator = registry.get("problem_solving.related_solids.volume")
    questions = []
    for level in range(1, 5):
        q = generator.generate(12345, level)
        generator.validate_independently(q)
        require(q.schema_version == 5, "Wrong schema version")
        require(q.prompt.blocks and q.answer_display.blocks, "Rich presentation missing")
        require("Form an equation" in q.prompt.text, "CLI fallback lost")
        for content in (q.prompt, q.answer_display):
            for flowable in content_flowables(content, styles()["body"]):
                flowable.wrap(460, 700)
        questions.append(q)

    base = questions[0]
    old_question = replace(
        base, prompt=legacy, answer_display=Content("x = 2", "x=2"),
        question_visuals=(), layout_hint=LayoutHint(working_lines=1),
    )
    require(len(question_prompt(old_question, styles()["body"])) == 2,
            "Legacy display equation path changed")
    choice_question = replace(
        old_question,
        prompt=Content("Choose the correct value."),
        choices=(
            Choice("a", Content("2", blocks=({"kind": "equation", "tex": "2", "text": "2"},))),
            Choice("b", Content("3")),
        ),
        answer_display=rich,
    )
    export_root = Path(__file__).resolve().parent.parent / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="rich_content_check_", dir=str(export_root)))
    worksheet = SimpleNamespace(
        title="Rich content integration check", id="rich-content-check",
        specification={}, questions=[old_question, choice_question],
    )
    for mode in ("questions", "answers"):
        print(render_pdf(worksheet, directory / (mode + ".pdf"), mode))
    worked = replace(
        old_question, worked_solution=(rich,),
    )
    worksheet.questions = [worked]
    print(render_pdf(worksheet, directory / "worked.pdf", "worked"))
    print("PASS: schema/fallback validation, JSON reconstruction, four solid levels,")
    print("legacy question/answer paths, rich choices and worked-step PDF export.")


if __name__ == "__main__":
    main()