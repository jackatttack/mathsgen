"""Portable question links, source reconstruction and compact PDF cards."""
import base64
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import secrets
from urllib.parse import urlencode
from xml.sax.saxutils import quoteattr

from .core import canonical_json, require

SCRIPT = "mathsgen/tools/mathsgen_action.py"
# Keep legacy actions available for previously exported worksheets.
ACTIONS = ("another", "facts", "hint", "tools", "answer", "flag")


def content_digest(question, unordered_choices=False):
    choices = [asdict(choice.content) for choice in question.choices]
    if unordered_choices:
        if "multiple_choice" in question.answer:
            # Different distractors must not disguise a repeated question.
            choices = []
        else:
            choices.sort(key=canonical_json)
    visible = {
        "prompt": asdict(question.prompt),
        "visuals": question.visual_assets("questions"),
        "choices": choices,
    }
    return hashlib.sha256(
        canonical_json(visible).encode("utf-8")
    ).hexdigest()


def encode_question(question):
    payload = {
        "schema": 1,
        "generator": question.generator_id,
        "version": question.generator_version,
        "seed": question.seed,
        "difficulty": question.difficulty,
        "settings": question.settings,
        "display": content_digest(question),
    }
    if "multiple_choice" in question.answer:
        payload["schema"] = 2
        payload["multiple_choice_version"] = question.answer["multiple_choice"]["engine_version"]
    return base64.urlsafe_b64encode(
        canonical_json(payload).encode("utf-8")
    ).decode("ascii")


def decode_question(token):
    require(isinstance(token, str) and 0 < len(token) <= 16384,
            "Invalid question link size")
    try:
        raw = base64.b64decode(token.encode("ascii"), altchars=b"-_", validate=True)
        data = json.loads(raw.decode("utf-8"))
    except Exception as error:
        raise ValueError("Unreadable question link") from error
    require(isinstance(data, dict), "Invalid question link")
    require(type(data.get("schema")) is int and data["schema"] in (1, 2),
            "Unsupported question link version")
    expected_fields = {
        "schema", "generator", "version", "seed",
        "difficulty", "settings", "display",
    }
    if data["schema"] == 2:
        from .multiple_choice import ENGINE_VERSION
        expected_fields.add("multiple_choice_version")
        require(type(data.get("multiple_choice_version")) is int
                and data["multiple_choice_version"] == ENGINE_VERSION,
                "Multiple-choice rules have changed. Generate a new worksheet.")
    require(set(data) == expected_fields, "Unexpected question link fields")
    require(isinstance(data["generator"], str), "Invalid generator ID")
    for field in ("version", "seed", "difficulty"):
        require(type(data[field]) is int, "Invalid " + field)
    require(isinstance(data["settings"], dict), "Invalid settings")
    require(isinstance(data["display"], str) and len(data["display"]) == 64,
            "Invalid question checksum")
    return data


def source_question(token, registry):
    data = decode_question(token)
    generator = registry.get(data["generator"])
    require(generator.info.version == data["version"],
            "This generator has changed. Generate a new worksheet to refresh its links.")
    question = generator.generate(
        seed=data["seed"], difficulty=data["difficulty"],
        settings=data["settings"],
    )
    generator.validate(question)
    if data["schema"] == 2:
        from .multiple_choice import make_multiple_choice, validate_multiple_choice
        question = make_multiple_choice(question)
        require(question is not None,
                "This multiple-choice form is no longer supported.")
        validate_multiple_choice(question, generator)
    require(content_digest(question) == data["display"],
            "The original question no longer reproduces exactly. Generate a new worksheet.")
    return question


def action_url(question, action):
    """Build a link for a built-in action or a supported quick-copy tool."""
    if action.startswith("tool:"):
        from .teacher_tools import get_tool
        get_tool(question, action[len("tool:"):])
    else:
        require(action in ACTIONS, "Unknown question action")

    return "pythonista3://" + SCRIPT + "?" + urlencode([
        ("action", "run"), ("root", "local"),
        ("argv", action), ("argv", encode_question(question)),
    ])


def available_actions(question):
    """Expose every applicable quick-copy tool in the question heading.

    The optional toolbox remains accessible through Options. New retains
    its existing direct-to-clipboard implementation.
    """
    from .teacher_tools import available_tools

    resource_tools = [
        tool for tool in available_tools(question)
        if tool.kind in ("formula", "diagram")
    ]

    formula_count = sum(
        tool.kind == "formula" for tool in resource_tools
    )

    actions = [
        ("another", "+ New"),
        ("answer", "Answer"),
        ("flag", "Flag"),
    ]

    for tool in resource_tools:
        label = tool.label

        if tool.kind == "formula" and formula_count == 1:
            label = "Formula"
        elif tool.kind == "diagram" and tool.id.endswith(".graph"):
            label = "Graph"

        actions.append(("tool:" + tool.id, label))

    actions.append(("tools", "Options"))
    return actions


def action_links_markup(question, link_colour="#24658A"):
    """Build reusable ReportLab markup for this question's clickable actions.

    The same links can appear inside a question heading or in a
    standalone paragraph without duplicating their URL construction.
    link_colour comes from the worksheet theme when called by the PDF.
    """
    items = [
        '<link href={} color="{}"><u>{}</u></link>'.format(
            quoteattr(action_url(question, action)), link_colour, label
        )
        for action, label in available_actions(question)
    ]
    return " &nbsp; | &nbsp; ".join(items)


def link_flowable(question):
    """Standalone action paragraph for callers that need one."""
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph

    return Paragraph(
        action_links_markup(question),
        ParagraphStyle(
            "QuestionActions", fontName="Helvetica",
            fontSize=9, leading=14, spaceBefore=2, spaceAfter=2,
        ),
    )


def new_question(source, registry, previous=None, seed_source=None):
    generator = registry.get(source.generator_id)
    require(generator.info.version == source.generator_version,
            "Generator version changed")
    multiple_choice = "multiple_choice" in source.answer
    if multiple_choice:
        from .multiple_choice import (
            make_multiple_choice, supported_levels, validate_multiple_choice,
        )
        require(source.difficulty in supported_levels(source.generator_id),
                "This difficulty has no multiple-choice support.")
    seed_source = seed_source or (lambda: secrets.randbits(53))
    excluded = {content_digest(source, True), previous}
    for attempt in range(100):
        question = generator.generate(
            seed=seed_source(), difficulty=source.difficulty,
            settings=source.settings,
        )
        generator.validate(question)
        if multiple_choice:
            question = make_multiple_choice(question)
            if question is None:
                continue
            validate_multiple_choice(question, generator)
        if content_digest(question, True) not in excluded:
            return question
    raise ValueError("Could not find a different question after 100 attempts.")


def choice_flowables(question):
    from .pdf import CONTENT_WIDTH, styles
    from .pdf_choices import ChoiceGrid
    if not question.choices:
        return []
    return [ChoiceGrid(question, styles(), CONTENT_WIDTH - 24)]


def write_card(blocks, destination):
    """Measure and draw flowables on one content-sized white PDF page."""
    from reportlab.pdfgen.canvas import Canvas
    from .pdf import CONTENT_WIDTH

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    available = CONTENT_WIDTH - 24
    padding = 16.0
    width = available + 2 * padding
    canvas = Canvas(str(destination), pagesize=(width, 1000))
    measured = []
    for block in blocks:
        w, h = block.wrapOn(canvas, available, 10000)
        require(w <= available + 0.1 and 0 <= h <= 4000,
                "Card content exceeds rendering bounds")
        before = max(0.0, float(block.getSpaceBefore()))
        after = max(0.0, float(block.getSpaceAfter()))
        measured.append((block, h, before, after))
    require(bool(measured), "Cannot render an empty card")
    height = 2 * padding + sum(h + b + a for _, h, b, a in measured)
    require(height <= 4000, "Card is too tall")
    canvas.setPageSize((width, height))
    canvas.setFillColorRGB(1, 1, 1)
    canvas.rect(0, 0, width, height, stroke=0, fill=1)
    y = height - padding
    for block, h, before, after in measured:
        y -= before + h
        block.drawOn(canvas, padding, y)
        y -= after
    canvas.showPage()
    canvas.save()
    return width, height


def render_question_card(question, destination):
    from .pdf import question_prompt, visual_blocks, styles
    blocks = question_prompt(question, styles()["body"])
    blocks += visual_blocks(question, "questions")
    blocks += choice_flowables(question)
    return write_card(blocks, destination)


def render_support_card(card, destination):
    """Render rich and legacy Content using the worksheet's display rules."""
    from .content_rendering import content_flowables
    from .pdf import MathLine, paragraph, styles
    from .visuals import VisualFlowable

    style = styles()
    blocks = [paragraph(card.title, style["label"])]

    if card.content.blocks:
        blocks.extend(content_flowables(
            card.content, style["body"], card.title
        ))
    elif card.content.math_tex:
        if card.content.display_text:
            blocks.append(paragraph(
                card.content.display_text, style["body"]
            ))
        blocks.append(MathLine(card.content.math_tex))
    elif card.content.text.strip():
        blocks.append(paragraph(card.content.text, style["body"]))

    blocks.extend(VisualFlowable(asset) for asset in card.visuals)
    require(len(blocks) > 1, "Support card has no content")
    return write_card(blocks, destination)