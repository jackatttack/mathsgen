"""Exercise the new teacher-tool image pipeline on the Pythonista host.

The smoke renders actual PNGs but deliberately does not overwrite the
clipboard. Manual clipboard and touch-interface testing comes next.
"""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))


from pathlib import Path
import tempfile

from launch_mathsgen import load_engine


def main():
    from mathsgen.teacher_tools import available_tools
    from mathsgen.teacher_tool_output import render_tool_image

    registry = load_engine()

    cases = (
        ("algebra.quadratic.factorisable_monic", "quadratic.formula"),
        ("geometry.trigonometry.right_angled", "trigonometry.sohcahtoa"),
        ("algebra.linear.two_sided", "question.answer"),
    )

    with tempfile.TemporaryDirectory() as folder:

        for generator_id, tool_id in cases:
            generator = registry.get(generator_id)

            question = generator.generate(
                20260921,
                difficulty=2,
            )

            generator.validate(question)

            assert tool_id in [
                tool.id
                for tool in available_tools(question)
            ], "Expected tool is not available"

            resource, path, size = render_tool_image(
                question,
                tool_id,
                folder,
            )

            assert path.exists()
            assert path.read_bytes()[:8] == (
                b"\x89PNG\r\n\x1a\n"
            )

            assert size[0] > 0
            assert size[1] > 0

            print(
                "PASS: {} — {} PNG {} x {}".format(
                    generator_id,
                    resource.title,
                    size[0],
                    size[1],
                )
            )

    # Import the Pythonista UI without presenting a modal interface
    # during Forge execution.
    from mathsgen.teacher_tools_ui import (
        TeacherToolbox,
        present_toolbox,
    )

    assert callable(present_toolbox)

    print("PASS: teacher toolbox UI imports")
    print("PASS: teacher-tool image pipeline complete")
    print("DEVICE UI AND CLIPBOARD: manual verification pending")


if __name__ == "__main__":
    main()