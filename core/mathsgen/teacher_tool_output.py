"""Shared rendering and clipboard pipeline for teacher tools.

Quick actions and interactive previews use the same resource builder.
Only an explicit copy operation modifies the iOS clipboard.

The resource registry and PDF rendering remain portable. Pythonista-specific
image conversion and clipboard access are imported only when needed.
"""

from pathlib import Path

from .core import require
from .teacher_tools import build_resource


def render_tool_image(question, tool_id, output_root, options=None):
    """Render one teaching resource to a PNG without changing the clipboard.

    Return the resource, image path and image dimensions. Output paths are
    scoped to the question and tool so different resources do not overwrite
    one another.

    The returned PNG uses the same proven renderer as existing question cards.
    """

    from .question_actions import render_support_card
    from .pythonista_card_image import pdf_to_image

    resource = build_resource(question, tool_id, options)

    directory = (
        Path(output_root)
        / question.id
        / tool_id.replace(".", "_")
    )
    directory.mkdir(parents=True, exist_ok=True)

    pdf_path = directory / "resource.pdf"
    png_path = directory / "resource.png"

    size = render_support_card(resource, pdf_path)

    require(
        pdf_path.exists(),
        "Teacher resource PDF was not created",
    )

    image = pdf_to_image(pdf_path, size)
    image.save(str(png_path), "PNG")

    require(
        png_path.exists() and png_path.stat().st_size > 0,
        "Teacher resource image was not created",
    )

    return resource, png_path, image.size


def copy_tool_image(question, tool_id, output_root, options=None):
    """Render a resource and copy its PNG directly to the iOS clipboard.

    A successful return means the existing clipboard adapter confirmed
    that UIPasteboard retained the image.
    """

    from .pythonista_card_image import copy_png

    resource, png_path, size = render_tool_image(
        question,
        tool_id,
        output_root,
        options,
    )

    copy_png(png_path)

    return resource, png_path, size