"""Stable URL entry point for worksheet actions. Run through a worksheet link."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = Path(tempfile.gettempdir()) / "mathsgen_question_actions"


def action_workspace():
    """Local scratch space, capped at the 10 most recent action sessions."""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    current = Path(tempfile.mkdtemp(prefix="action_", dir=str(SCRATCH)))

    sessions = sorted(
        (
            path for path in SCRATCH.iterdir()
            if path.is_dir() and path.name.startswith("action_")
        ),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    for old in sessions[10:]:
        shutil.rmtree(old)

    return current


def main():
    import console
    if len(sys.argv) != 3:
        raise ValueError("Open a MathsGen action from a generated worksheet.")
    action, token = sys.argv[1:]
    core_path = str(ROOT / "core")
    if core_path not in sys.path:
        sys.path.insert(0, core_path)
    for name in list(sys.modules):
        if name == "mathsgen" or name.startswith("mathsgen."):
            del sys.modules[name]

    from mathsgen.catalogue import build_registry
    from mathsgen.question_actions import (
        ACTIONS, source_question, new_question, content_digest,
        render_question_card, render_support_card,
    )
    from mathsgen.question_support import card_for
    from mathsgen.pythonista_card_image import pdf_to_image, copy_png

    if action not in ACTIONS and not action.startswith("tool:"):
        raise ValueError("Unknown worksheet action.")
    registry = build_registry()
    source = source_question(token, registry)

    # One-tap feedback: persist the exact question without creating scratch
    # files, rendering resources or changing the clipboard.
    if action == "flag":
        from mathsgen.question_feedback import (
            feedback_database, flag_question,
        )
        is_new, count = flag_question(source, feedback_database(ROOT))
        print("FLAGGED:", source.generator_id, source.id)
        print("FLAG COUNT:", count)
        console.hud_alert(
            "Question flagged" if is_new else "Flag recorded ({})".format(count),
            "success",
            1.0,
        )
        return

    OUT = action_workspace()

    # Registry-backed quick actions render and copy immediately.
    # The registry validates both the tool ID and question support.
    if action.startswith("tool:"):
        from mathsgen.teacher_tools import get_tool
        from mathsgen.teacher_tool_output import copy_tool_image

        tool_id = action[len("tool:"):]
        tool = get_tool(source, tool_id)
        resource, png_path, size = copy_tool_image(
            source,
            tool.id,
            OUT / "teacher_tools",
        )

        print("COPIED:", resource.title)
        print("IMAGE:", size, str(png_path))
        console.hud_alert(
            "{} copied".format(resource.title),
            "success",
            1.0,
        )
        return

    # The toolbox is optional: opening it does not overwrite the clipboard.
    if action == "tools":
        from mathsgen.teacher_tools_ui import present_toolbox

        present_toolbox(
            source,
            OUT / "teacher_tools",
        )
        return

    # Answer is a universal quick action. Reuse the same verified
    # rendering and clipboard pipeline as every other teacher tool.
    if action == "answer":
        from mathsgen.teacher_tool_output import copy_tool_image

        resource, png_path, size = copy_tool_image(
            source,
            "question.answer",
            OUT / "teacher_tools",
        )

        print("COPIED:", resource.title)
        print("IMAGE:", size, str(png_path))
        console.hud_alert("Answer copied", "success", 1.0)
        return

    if action == "another":
        from mathsgen.new_question_ui import present_new_question
        present_new_question(source, registry, token, OUT)
        return

    # Legacy Facts and Hint URLs remain functional on older worksheets.
    pdf_path = OUT / ("latest_" + action + ".pdf")
    png_path = OUT / ("latest_" + action + ".png")
    card = card_for(source, action)
    size = render_support_card(card, pdf_path)
    image = pdf_to_image(pdf_path, size)
    image.save(str(png_path), "PNG")
    copy_png(png_path)

    print("COPIED:", card.title)
    print("IMAGE:", image.size, str(png_path))
    console.hud_alert({
        "facts": "Facts copied",
        "hint": "Hint copied",
    }[action], "success", 1.0)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        import console
        console.alert("Mathsgen action failed", str(error),
                      "OK", hide_cancel_button=True)
        raise