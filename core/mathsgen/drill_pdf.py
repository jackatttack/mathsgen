"""Compact PDF layout for drill sheets: a progression per exercise.

Each exercise prints its heading, then its stages in order:
- drill stages, one per level: a grid of labelled items (a), (b), (c)
  with no source lines or per-item working space;
- an apply stage: worded and diagram problems in one or two columns with
  room to work.

Shared instruction: within a drill stage, when most items share a lead-in
followed by a display equation or a diagram ("Factorise fully." then an
expression; "Find the length x." then a triangle), the lead-in prints once
and those items show only the expression or the drawing.

Items with a diagram are stacked: the label sits above the drawing so the
drawing gets the whole column width. Drawings never exceed
DRILL_DIAGRAM_WIDTH and need at least VISUAL_MINIMUM_WIDTH.

Columns: each stage tries its column choices widest first and keeps the
first in which every item fits.
"""
from collections import Counter, namedtuple
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import CondPageBreak, SimpleDocTemplate, Spacer, Table, TableStyle

from .core import Content, canonical_json, require
from .drill import DRILL_DIAGRAM_WIDTH, drill_stages
from .pdf import (
    MARGIN, PAGE_HEIGHT, PAGE_WIDTH, MathLine, difficulty_stars, paragraph,
    question_prompt, styles,
)
from .squared_page import content_panel, draw_page_background
from .theme import theme_for
from .topic_browser import topic_style


# ------------------------------------------------------------ editable layout

DRILL_COLUMN_CHOICES = (3, 2, 1)  # tried in order; the first that fits wins
APPLY_COLUMN_CHOICES = (2, 1)
ITEM_LABEL_WIDTH = 26             # points reserved for "(a)" beside an item
COLUMN_GUTTER = 12                # clear space before the next column's label
DRILL_ROW_SPACE = 22              # space under each drill item
DIAGRAM_ROW_SPACE = 48            # space under a row of diagram items
APPLY_ROW_SPACE = 80              # working room under each applied problem
ANSWER_ROW_SPACE = 2              # answer sheets stay tight
EQUATION_SIZE = 13                # display maths size in the grid
DRILL_WRAP_LINES = 2              # drill prose may wrap onto this many lines
APPLY_WRAP_LINES = 8
VISUAL_MINIMUM_WIDTH = 220        # visuals.drawing_for refuses anything narrower
BLOCK_GAP = 16
STAGE_GAP = 8
BLOCK_START_SPACE = 160           # start an exercise on a new page if less remains
STAGE_START_SPACE = 110
BODY_FONT_SIZE = 11               # must match styles()["body"]
# A lead-in prints once when at least this share of a stage uses it.
SHARED_INSTRUCTION_MINIMUM_SHARE = 0.5

PAGE_LABELS = {"questions": "Practice drill", "answers": "Drill answers"}
APPLY_TITLE = "Apply it"

# flowables: what goes in the cell; rigid: widest display maths; prose:
# unwrapped prose width; stacked: label above (diagram cells).
Cell = namedtuple("Cell", "flowables rigid prose stacked")


# ------------------------------------------------------- shared instructions

def paragraph_block_text(block):
    if "text" in block:
        return block["text"]
    return "".join(run["text"] for run in block["runs"])


def split_prompt(question):
    """(lead key, lead, body) when a prompt is a lead-in plus one display part.

    body is ("tex", display tex) or ("visual", None). Returns None for any
    other shape, so the item keeps its full prompt.
    """
    prompt = question.prompt
    has_visual = bool(question.visual_assets("questions"))
    if prompt.blocks:
        blocks = list(prompt.blocks)
        leading_prose = all(block.get("kind") == "paragraph" for block in blocks[:-1])
        if len(blocks) >= 2 and blocks[-1].get("kind") == "equation" and leading_prose:
            lead = tuple(blocks[:-1])
            return canonical_json(lead), ("blocks", lead), ("tex", blocks[-1]["tex"])
        if has_visual and all(block.get("kind") == "paragraph" for block in blocks):
            lead = tuple(blocks)
            return canonical_json(lead), ("blocks", lead), ("visual", None)
        return None
    if prompt.math_tex:
        if prompt.display_text:
            return prompt.display_text, ("text", prompt.display_text), ("tex", prompt.math_tex)
        return None
    if has_visual and prompt.display_text:
        return prompt.display_text, ("text", prompt.display_text), ("visual", None)
    return None


def shared_instruction(questions):
    """(lead, body or None per item, items sharing) or None.

    The most common lead-in becomes the stage instruction when enough items
    use it. Items with that lead-in show only their body; any other item
    keeps its full prompt (body None).
    """
    splits = [split_prompt(question) for question in questions]
    counts = Counter(split[0] for split in splits if split is not None)
    if not counts:
        return None
    key, sharing = counts.most_common(1)[0]
    if sharing < SHARED_INSTRUCTION_MINIMUM_SHARE * len(questions):
        return None
    lead = next(split[1] for split in splits if split is not None and split[0] == key)
    bodies = [
        split[2] if split is not None and split[0] == key else None
        for split in splits
    ]
    return lead, bodies, sharing


def terse_instruction(text, questions):
    """A curated stage instruction: items with a diagram show only the diagram.

    Same shape as shared_instruction(). An item without a diagram keeps its
    full prompt, so nothing a student needs can disappear.
    """
    bodies = [
        ("visual", None) if question.visual_assets("questions") else None
        for question in questions
    ]
    return ("text", text), bodies, sum(body is not None for body in bodies)


def instruction_flowables(lead, style):
    kind, value = lead
    if kind == "text":
        return [paragraph(value, style)]
    from .content_rendering import content_flowables
    text = " ".join(paragraph_block_text(block) for block in value)
    return content_flowables(Content(text, blocks=value), style, "drill instruction")


# --------------------------------------------------------------------- cells

def prompt_text(question):
    """The prose actually printed, for width estimates."""
    prompt = question.prompt
    if not prompt.blocks and prompt.display_text is not None:
        return prompt.display_text
    return prompt.text


def visual_flowables(question, audience, inner_width):
    assets = question.visual_assets(audience)
    if not assets:
        return []
    width = min(inner_width, DRILL_DIAGRAM_WIDTH)
    if width < VISUAL_MINIMUM_WIDTH:
        raise ValueError("Column too narrow for a diagram")
    from .visuals import VisualFlowable
    return [VisualFlowable(asset, preferred_width=width) for asset in assets]


def make_cell(flowables, text, font, stacked):
    rigid = max([item.width for item in flowables if isinstance(item, MathLine)] or [0])
    has_prose = bool(text) and any(
        not isinstance(item, MathLine) for item in flowables
    )
    prose = stringWidth(text, font, BODY_FONT_SIZE) if has_prose else 0
    return Cell(flowables, rigid, prose, stacked)


def inner_width(column_width, stacked):
    """Width an item's content may use.

    Text items sit beside their "(a)" label and stop COLUMN_GUTTER short of
    the next column's label. Stacked (diagram) items have the label above,
    so nothing can collide and they keep the full column width.
    """
    if stacked:
        return column_width
    return column_width - ITEM_LABEL_WIDTH - COLUMN_GUTTER


def question_cell(question, body, style, theme, column_width):
    stacked = bool(question.visual_assets("questions"))
    inner = inner_width(column_width, stacked)
    if body is None:
        flowables = list(question_prompt(question, style["body"]))
        text = prompt_text(question)
    elif body[0] == "tex":
        flowables = [MathLine(body[1], size=EQUATION_SIZE)]
        text = ""
    else:
        flowables = []
        text = ""
    flowables.extend(visual_flowables(question, "questions", inner))
    return make_cell(flowables, text, theme.body_font, stacked)


def answer_cell(question, style, theme, column_width):
    stacked = bool(question.visual_assets("answers"))
    inner = inner_width(column_width, stacked)
    answer = question.answer_display
    if answer.blocks:
        from .content_rendering import content_flowables
        flowables = list(content_flowables(
            answer, style["body"], question.generator_id + " answer"))
    elif answer.math_tex:
        flowables = [MathLine(answer.math_tex, size=EQUATION_SIZE)]
    else:
        flowables = [paragraph(answer.text, style["body"])]
    flowables.extend(visual_flowables(question, "answers", inner))
    return make_cell(flowables, answer.text, theme.body_font, stacked)


# ---------------------------------------------------------------------- grid

def item_label(index):
    """(a) ... (z), then (aa), (ab) ..."""
    letters = ""
    number = index
    while True:
        letters = chr(97 + number % 26) + letters
        number = number // 26 - 1
        if number < 0:
            return "(" + letters + ")"


def fits(cell, column_width, wrap_lines):
    """Trial-wrap an item at its real width inside the column."""
    inner = inner_width(column_width, cell.stacked)
    if cell.rigid > inner or cell.prose > wrap_lines * inner:
        return False
    try:
        for flowable in cell.flowables:
            width, _ = flowable.wrap(inner, 10000)
            if width > inner + 0.5:
                return False
    except ValueError:
        return False
    return True


def choose_layout(build_cells, choices, available_width, wrap_lines):
    """(columns, cells) for the widest choice in which every item fits."""
    for columns in choices:
        column_width = available_width / columns
        try:
            cells = build_cells(column_width)
        except ValueError:
            continue
        if all(fits(cell, column_width, wrap_lines) for cell in cells):
            return columns, cells
    columns = choices[-1]
    return columns, build_cells(available_width / columns)


TIGHT = [
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ("TOPPADDING", (0, 0), (-1, -1), 0),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
]


def grid_item(index, cell, column_width, label_style):
    label = paragraph(item_label(index), label_style)
    if cell.stacked:
        item = Table([[label], [cell.flowables]], colWidths=[column_width], hAlign="LEFT")
    else:
        item = Table(
            [[label, cell.flowables]],
            colWidths=[ITEM_LABEL_WIDTH, column_width - ITEM_LABEL_WIDTH],
            hAlign="LEFT",
        )
    # Text wraps short of the column edge, matching inner_width.
    style = TIGHT if cell.stacked else TIGHT + [
        ("RIGHTPADDING", (-1, 0), (-1, -1), COLUMN_GUTTER),
    ]
    item.setStyle(TableStyle(style))
    return item


def grid_table(cells, columns, available_width, label_style, row_space, white,
               background="#FFFFFF"):
    column_width = available_width / columns
    rows = []
    row = []
    for index, cell in enumerate(cells):
        row.append(grid_item(index, cell, column_width, label_style))
        if len(row) == columns:
            rows.append(row)
            row = []
    if row:
        rows.append(row + [""] * (columns - len(row)))
    grid = Table(rows, colWidths=[column_width] * columns, hAlign="LEFT")
    grid_style = TIGHT + [
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), row_space),
    ]
    if white:
        grid_style.append(("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(background)))
    grid.setStyle(TableStyle(grid_style))
    return grid


# -------------------------------------------------------------------- stages

def stage_title(stage):
    if stage["kind"] == "apply":
        return APPLY_TITLE
    return "Level {}{}   {}".format(
        stage["level"], stage.get("part", ""), difficulty_stars(stage["level"]))


def stage_story(stage, questions, style, theme, width, on_paper):
    """Flowables and a report entry for one stage."""
    applied = stage["kind"] == "apply"
    if theme.name == "ivory":
        from .pdf_headings import LevelBadge

        label = APPLY_TITLE if applied else "Level {}{}".format(
            stage["level"], stage.get("part", ""),
        )
        heading = [LevelBadge(label, theme)]
    else:
        heading = [paragraph(stage_title(stage), style["label"])]
    shared = None
    if on_paper:
        if stage.get("instruction"):
            # Diagram-only stage: one line of instruction, then just the drawings.
            shared = terse_instruction(stage["instruction"], questions)
        else:
            shared = None if applied else shared_instruction(questions)
        if shared:
            heading.extend(instruction_flowables(shared[0], style["body"]))
        bodies = shared[1] if shared else [None] * len(questions)

        def build_cells(column_width):
            return [
                question_cell(question, body, style, theme, column_width)
                for question, body in zip(questions, bodies)
            ]
        choices = APPLY_COLUMN_CHOICES if applied else DRILL_COLUMN_CHOICES
    else:
        def build_cells(column_width):
            return [answer_cell(question, style, theme, column_width) for question in questions]
        choices = DRILL_COLUMN_CHOICES

    wrap_lines = APPLY_WRAP_LINES if applied or not on_paper else DRILL_WRAP_LINES
    columns, cells = choose_layout(build_cells, choices, width, wrap_lines)
    diagrams = sum(cell.stacked for cell in cells)
    if not on_paper:
        row_space = ANSWER_ROW_SPACE
    elif applied:
        row_space = APPLY_ROW_SPACE
    else:
        row_space = DIAGRAM_ROW_SPACE if diagrams else DRILL_ROW_SPACE

    story = [CondPageBreak(STAGE_START_SPACE)]
    stage_heading = content_panel(heading, width, theme) if on_paper else heading[0]
    stage_heading.keepWithNext = True
    story.append(stage_heading)
    story.append(Spacer(1, 4))
    story.append(grid_table(
        cells, columns, width, style["label"], row_space,
        on_paper and theme.opaque_panels, theme.paper_ink,
    ))
    story.append(Spacer(1, STAGE_GAP))
    report = {
        "kind": stage["kind"], "part": stage.get("part", ""),
        "items": len(questions), "columns": columns,
        "shared": shared[2] if shared else 0, "diagrams": diagrams,
    }
    return story, report


# -------------------------------------------------------------------- render

def exercise_story(number, block, stages, style, theme, width, on_paper):
    """One drill exercise: its heading, then every stage.

    Returns (flowables, report). Shared by drill sheets and block sheets, so
    an exercise looks the same in both.
    """
    topic = stages[0][1][0].topic
    heading_style = ParagraphStyle(
        "DrillHeading_" + topic, parent=style["label"], fontSize=13, leading=17,
        textColor=colors.HexColor(
            topic_style(topic)[1] if theme.topic_colours else theme.accent
        ),
    )
    if theme.name == "ivory":
        from .pdf_headings import SectionHeading

        heading = SectionHeading(number, block["title"], theme)
    else:
        heading = paragraph("Exercise {}   {}".format(number, block["title"]), heading_style)
    exercise_heading = content_panel([heading], width, theme) if on_paper else heading
    exercise_heading.keepWithNext = True
    story = [
        CondPageBreak(BLOCK_START_SPACE),
        exercise_heading,
        Spacer(1, 6),
    ]
    stage_reports = []
    for stage, questions in stages:
        flowables, stage_report = stage_story(
            stage, questions, style, theme, width, on_paper)
        story.extend(flowables)
        stage_reports.append(stage_report)
    story.append(Spacer(1, BLOCK_GAP))
    return story, {"title": block["title"], "stages": stage_reports}


def render_drill_pdf(worksheet, destination, mode="questions"):
    """Write the question or answer variant of a drill sheet."""
    require(mode in PAGE_LABELS, "Drill sheets support question and answer PDFs only.")
    require(worksheet.specification.get("mode") == "drill", "Not a drill worksheet.")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    theme = theme_for(worksheet.specification)
    style = styles(theme)
    document = SimpleDocTemplate(
        str(destination), pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=19 * mm, bottomMargin=19 * mm,
        title=worksheet.title + " - " + PAGE_LABELS[mode],
        author="Mathsgen", pageCompression=1,
    )
    width = document.width - 12   # the frame pads each edge by six points
    on_paper = mode == "questions"

    header = [
        paragraph(worksheet.title, style["title"]),
        paragraph(PAGE_LABELS[mode], style["subtitle"]),
    ]
    if on_paper:
        header.append(paragraph(
            "Name: ________________________    Date: ______________", style["body"]
        ))
        story = [content_panel(header, width, theme), Spacer(1, 10)]
    else:
        story = header

    report = []
    for number, (block, stages) in enumerate(drill_stages(worksheet), 1):
        flowables, block_report = exercise_story(
            number, block, stages, style, theme, width, on_paper)
        story.extend(flowables)
        report.append(block_report)

    def footer(canvas, doc):
        draw_page_background(canvas, PAGE_WIDTH, PAGE_HEIGHT, theme, squared=on_paper)
        canvas.saveState()
        if on_paper and theme.opaque_panels:
            canvas.setFillColor(colors.HexColor(theme.paper_ink))
            canvas.rect(MARGIN - 4, 11 * mm - 3, PAGE_WIDTH - 2 * MARGIN + 8, 13, stroke=0, fill=1)
        canvas.setFont(theme.body_font, 8)
        canvas.setFillColor(colors.HexColor(theme.muted_ink))
        canvas.drawString(MARGIN, 11 * mm, PAGE_LABELS[mode])
        canvas.drawCentredString(PAGE_WIDTH / 2, 11 * mm, "Set " + worksheet.id[:10])
        canvas.drawRightString(PAGE_WIDTH - MARGIN, 11 * mm, str(doc.page))
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return {
        "mode": mode,
        "path": str(destination),
        "pages": document.page,
        "page_size_points": [PAGE_WIDTH, PAGE_HEIGHT],
        "bytes": destination.stat().st_size,
        "blocks": report,
    }