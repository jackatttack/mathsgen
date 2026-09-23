"""Render explicitly authored content blocks; never infer maths from prose."""
from .rich_text import RichParagraph


def content_flowables(content, style, context="content"):
    content.validate_blocks()
    result = []
    for index, block in enumerate(content.blocks):
        location = "{} block {}".format(context, index + 1)
        if block["kind"] == "equation":
            result.append(RichParagraph(
                [{"tex": block["tex"], "text": block["text"]}],
                size=14, leading=20, context=location,
            ))
        else:
            runs = block.get("runs")
            if runs is None:
                runs = [{"text": block["text"]}]
            result.append(RichParagraph(
                runs, size=style.fontSize, leading=style.leading,
                context=location,
            ))
    return result