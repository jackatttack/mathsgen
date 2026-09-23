"""Test the teacher-tool registry and real mathematical resource rendering.

This test is portable and deliberately does not replace the iOS clipboard.
The actual clipboard and optional Pythonista UI are tested separately.
"""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))


from dataclasses import replace
from pathlib import Path
import tempfile

from launch_mathsgen import load_engine


def main():
    from mathsgen.core import require
    from mathsgen.teacher_tools import (
        TeacherTool,
        ToolOption,
        available_tools,
        build_resource,
        default_options,
        register_tool,
        resolve_options,
    )
    from mathsgen.question_actions import render_support_card

    registry = load_engine()

    quadratic = registry.get(
        "algebra.quadratic.factorisable_monic"
    )

    trigonometry = registry.get(
        "geometry.trigonometry.right_angled"
    )

    linear = registry.get(
        "algebra.linear.two_sided"
    )

    cases = (
        (quadratic, "quadratic.formula"),
        (trigonometry, "trigonometry.sohcahtoa"),
        (linear, None),
    )

    with tempfile.TemporaryDirectory() as temporary:
        output_root = Path(temporary)
        rendered = 0

        for generator, expected_formula in cases:
            for difficulty in (1, 2, 3, 4):
                question = generator.generate(
                    seed=20260921 + difficulty,
                    difficulty=difficulty,
                )

                generator.validate(question)

                tools = available_tools(question)
                tool_ids = [tool.id for tool in tools]

                require(
                    "question.answer" in tool_ids,
                    "Universal answer tool is missing",
                )

                if expected_formula is not None:
                    require(
                        expected_formula in tool_ids,
                        "Expected formula tool is missing",
                    )

                # Every resource goes through the existing renderer,
                # not a separate untested formula drawing implementation.
                for tool in tools:
                    resource = build_resource(question, tool.id)

                    require(
                        bool(resource.title),
                        "Teaching resource has no title",
                    )

                    filename = "{}_level_{}_{}.pdf".format(
                        generator.info.id.replace(".", "_"),
                        difficulty,
                        tool.id.replace(".", "_"),
                    )

                    destination = output_root / filename

                    size = render_support_card(resource, destination)

                    require(
                        destination.exists(),
                        "Teaching resource PDF was not created",
                    )
                    require(
                        destination.read_bytes()[:5] == b"%PDF-",
                        "Teaching resource did not render as a PDF",
                    )
                    require(
                        size[0] > 0 and size[1] > 0,
                        "Teaching resource has invalid dimensions",
                    )

                    rendered += 1

                print(
                    "PASS: {} level {} — {}".format(
                        generator.info.id,
                        difficulty,
                        ", ".join(tool_ids),
                    )
                )

        # A new generator version must not inherit support accidentally.
        original = quadratic.generate(98765, difficulty=2)
        changed = replace(original, generator_version=999)

        changed_ids = [
            tool.id for tool in available_tools(changed)
        ]

        require(
            "quadratic.formula" not in changed_ids,
            "Unreviewed generator version inherited formula support",
        )
        require(
            "question.answer" in changed_ids,
            "Universal answer should remain available",
        )

        print("PASS: version-restricted tools do not attach to new versions")

        # Verify the shared configuration contract independently of UI.
        sample_tool = TeacherTool(
            id="test.configurable",
            label="Configurable test resource",
            kind="diagram",
            supports=lambda question: True,
            build=lambda question, options: build_resource(
                question, "question.answer"
            ),
            options=(
                ToolOption(
                    name="show_labels",
                    label="Show labels",
                    choices=(False, True),
                    default=False,
                ),
            ),
        )

        defaults = default_options(sample_tool)
        require(
            defaults == {"show_labels": False},
            "Incorrect tool defaults",
        )
        require(
            resolve_options(
                sample_tool,
                {"show_labels": True},
            ) == {"show_labels": True},
            "Tool option override failed",
        )

        try:
            resolve_options(sample_tool, {"unknown": True})
        except ValueError:
            pass
        else:
            raise AssertionError("Unknown tool option was accepted")

        try:
            resolve_options(sample_tool, {"show_labels": "yes"})
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid tool option value was accepted")

        register_tool(sample_tool)

        try:
            register_tool(sample_tool)
        except ValueError:
            pass
        else:
            raise AssertionError("Duplicate teacher tool was accepted")

        print("PASS: defaults, overrides and invalid-option rejection")
        print("PASS: duplicate tool registration rejected")
        print("PASS: {} teaching resources rendered".format(rendered))

    print("PASS: teacher-tools foundation complete")
    print("DEVICE CLIPBOARD AND UI: not yet tested")


if __name__ == "__main__":
    main()