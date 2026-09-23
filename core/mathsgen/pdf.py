"""A4 PDF backend. Exact mathematics stays in the question generators."""
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from .core import require
from .topic_browser import topic_style
from .squared_page import draw_page_grid, white_panel
from .theme import DEFAULT_THEME, THEMES, theme_for


PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 20 * mm
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN


@lru_cache(maxsize=512)
def math_outline(tex, size):
    """MathText creates vector paths without LaTeX or a raster image."""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties

    return TextPath(
        (0, 0), "$" + tex + "$", size=size,
        prop=FontProperties(family="DejaVu Sans"), usetex=False,
    )


class MathLine(Flowable):
    """Render the limited TeX supported by Matplotlib MathText as vectors."""

    def __init__(self, tex, size=14):
        Flowable.__init__(self)
        self.outline = math_outline(tex, size)
        self.bounds = self.outline.get_extents()
        self.width = float(self.bounds.width)
        self.height = float(self.bounds.height) + 10

    def wrap(self, available_width, available_height):
        if self.width > available_width:
            raise ValueError("Mathematical expression is too wide for the PDF column")
        return self.width, self.height

    def draw(self):
        from matplotlib.path import Path as VectorPath

        canvas = self.canv
        canvas.saveState()
        canvas.translate(-float(self.bounds.x0), 5 - float(self.bounds.y0))
        canvas.setFillColor(colors.HexColor("#17212B"))
        path = canvas.beginPath()
        current = (0.0, 0.0)
        start = current
        for vertices, code in self.outline.iter_segments(curves=True, simplify=False):
            points = [float(value) for value in vertices]
            if code == VectorPath.MOVETO:
                path.moveTo(*points)
                current = start = tuple(points)
            elif code == VectorPath.LINETO:
                path.lineTo(*points)
                current = tuple(points)
            elif code == VectorPath.CURVE3:
                control = points[:2]
                end = points[2:4]
                first = [
                    current[i] + 2 * (control[i] - current[i]) / 3
                    for i in range(2)
                ]
                second = [
                    end[i] + 2 * (control[i] - end[i]) / 3
                    for i in range(2)
                ]
                path.curveTo(*(first + second + end))
                current = tuple(end)
            elif code == VectorPath.CURVE4:
                path.curveTo(*points)
                current = tuple(points[-2:])
            elif code == VectorPath.CLOSEPOLY:
                path.close()
                current = start
            elif code == VectorPath.STOP:
                break
            else:
                raise ValueError("Unsupported vector path command")
        canvas.drawPath(path, stroke=0, fill=1, fillMode=1)
        canvas.restoreState()


class WorkingSpace(Flowable):
    """Reserve transparent working space over the continuous page grid."""

    def __init__(self, lines):
        Flowable.__init__(self)
        require(type(lines) is int and lines >= 0, "Invalid working-space size")
        self.lines = lines
        self.width = CONTENT_WIDTH
        self.height = lines * 18 + 8
        self.cell = 5 * mm

    def wrap(self, available_width, available_height):
        self.width = min(CONTENT_WIDTH, available_width)
        return self.width, self.height

    def draw(self):
        # The page background supplies the grid. Retain the measured height,
        # including any extra height reserved beside a diagram.
        pass


def styles(theme=None):
    """Paragraph styles for a theme; with no theme, the classic look."""
    theme = theme or THEMES[DEFAULT_THEME]
    return {
        "title": ParagraphStyle(
            "WorksheetTitle", fontName=theme.bold_font, fontSize=21,
            leading=26, textColor=colors.HexColor(theme.title_ink), spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "WorksheetSubtitle", fontName=theme.body_font, fontSize=9,
            leading=13, textColor=colors.HexColor(theme.muted_ink), spaceAfter=16,
        ),
        "body": ParagraphStyle(
            "WorksheetBody", fontName=theme.body_font, fontSize=11,
            leading=16, alignment=TA_LEFT, spaceAfter=6,
            textColor=colors.HexColor(theme.body_ink),
        ),
        "label": ParagraphStyle(
            "QuestionLabel", fontName=theme.bold_font, fontSize=10,
            leading=14, spaceAfter=5, textColor=colors.HexColor(theme.accent),
        ),
        "source": ParagraphStyle(
            "QuestionSource", fontName=theme.body_font, fontSize=7.5,
            leading=10, spaceAfter=5, textColor=colors.HexColor(theme.source_ink),
        ),
    }


@lru_cache(maxsize=1)
def _registry():
    from .catalogue import build_registry
    return build_registry()


@lru_cache(maxsize=None)
def generator_title(generator_id):
    """The generator's human title; falls back to its ID so rendering never fails."""
    try:
        return _registry().get(generator_id).info.title
    except Exception:
        return generator_id


def source_line(question):
    """Topic hint for students and a debugging handle for the teacher."""
    return "{} \u00b7 {} v{}".format(
        generator_title(question.generator_id),
        question.generator_id, question.generator_version,
    )


def paragraph(text, style):
    return Paragraph(escape(text).replace("\n", "<br/>"), style)


# Difficulty is shown as filled stars, one to four.
#
# Only the filled star is used: the standard PDF Helvetica font has no
# hollow star glyph, and an unfilled slot renders as a solid box instead.
# Do not reintroduce U+2606 without embedding a font that contains it.
FILLED_STAR = "\u2605"
DIFFICULTY_LEVELS = 4


def difficulty_stars(difficulty):
    """Write a difficulty as that many filled stars, out of a maximum of four."""
    require(difficulty in range(1, DIFFICULTY_LEVELS + 1), "Unsupported difficulty")
    return FILLED_STAR * difficulty


def question_prompt(question, style):
    """Render explicit rich blocks or preserve the legacy display contract."""
    if question.prompt.blocks:
        from .content_rendering import content_flowables
        return content_flowables(
            question.prompt, style, question.generator_id + " question",
        )
    if question.prompt.math_tex:
        # Generators supply a separate lead-in; never guess how to remove
        # an equation from the plain-text fallback.
        lead = getattr(question.prompt, "display_text", None)
        require(lead is not None, "Math prompt requires explicit display_text")
        result = [paragraph(lead, style)] if lead else []
        result.append(MathLine(question.prompt.math_tex))
        return result
    lead = question.prompt.display_text
    return [paragraph(question.prompt.text if lead is None else lead, style)]


def visual_blocks(question, mode):
    """Build audience-specific assets without falling back to answer content."""
    from .visuals import VisualFlowable

    blocks = []
    for asset in question.visual_assets(mode):
        blocks.extend([Spacer(1, 8), VisualFlowable(asset), Spacer(1, 8)])
    return blocks


def scene_working_row(question, available_width):
    """Fit one schematic beside transparent working space.

    The actual rendered drawing determines the panel width. Its design
    canvas must not determine how much white space appears on the page.
    """
    from .visuals import VisualFlowable

    panel_padding = 12
    gap = 16

    visual = VisualFlowable(
        question.visual_assets("questions")[0],
        preferred_width=238,
    )

    # Measure the diagram at its normal rendering scale first.
    # VisualFlowable preserves this drawing during the nested table wrap.
    drawing_width, drawing_height = visual.wrap(238, 10000)

    panel_width = drawing_width + panel_padding
    panel_height = drawing_height + panel_padding

    working_width = available_width - panel_width - gap

    require(
        working_width >= 180,
        "Insufficient width for diagram and working",
    )

    working = WorkingSpace(question.layout_hint.working_lines)
    working.height = max(working.height, panel_height)

    diagram_panel = white_panel([visual], panel_width)

    row = Table(
        [[diagram_panel, "", working]],
        colWidths=[panel_width, gap, working_width],
        hAlign="LEFT",
    )

    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    return row


def compact_action_panel(question, maximum_width):
    """Size the white backing to the question's visible action links.

    Ask ReportLab to measure the actual linked paragraph instead of
    estimating its width from text. Grow the panel only when necessary
    to keep the available links on one line.
    """
    from .question_actions import link_flowable

    link = link_flowable(question)
    width = min(100, maximum_width)
    horizontal_padding = 12

    while width < maximum_width:
        _, text_height = link.wrap(
            width - horizontal_padding, 10000
        )

        if text_height <= link.style.leading + 0.01:
            break

        width = min(width + 12, maximum_width)

    return white_panel([link], width)


class QuestionBlock(KeepTogether):
    """Move an intact question to the next page or reject an oversized one."""

    def __init__(self, blocks, maximum_height, number):
        KeepTogether.__init__(self, blocks)
        self.maximum_height = maximum_height
        self.question_number = number

    def wrap(self, available_width, available_height):
        result = KeepTogether.wrap(self, available_width, available_height)
        require(
            self._H <= self.maximum_height,
            "Question {} is too tall for one page. Reduce its visual height "
            "or working space, or divide it into separate questions.".format(
                self.question_number
            ),
        )
        return result


def render_pdf(worksheet, destination, mode="questions"):
    """Write one variant. Refuse unsupported diagrams rather than omit them."""
    require(mode in ("questions", "answers", "worked"), "Unknown PDF mode")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    theme = theme_for(worksheet.specification)
    style = styles(theme)
    show_source = worksheet.specification.get("show_source", True)
    labels = {
        "questions": "Practice worksheet",
        "answers": "Answer sheet",
        "worked": "Worked solutions",
    }
    document = SimpleDocTemplate(
        str(destination), pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=19 * mm, bottomMargin=19 * mm,
        title=worksheet.title + " - " + labels[mode],
        author="Mathsgen",
        pageCompression=1,
    )
    story = [
        paragraph(worksheet.title, style["title"]),
        paragraph(labels[mode], style["subtitle"]),
    ]
    if mode == "questions":
        story.extend([
            paragraph("Name: ________________________    Date: ______________", style["body"]),
            Spacer(1, 12),
        ])

    if mode == "questions":
        story = [white_panel(story, document.width - 12), Spacer(1, 10)]

    for number, question in enumerate(worksheet.questions, 1):
        question_label_style = ParagraphStyle(
            "QuestionLabel_" + question.topic,
            parent=style["label"],
            textColor=colors.HexColor(
                topic_style(question.topic)[1] if theme.topic_colours else theme.accent
            ),
        )
        heading = "Question {}".format(number)
        if worksheet.specification.get("show_difficulty", True):
            heading += "    " + difficulty_stars(question.difficulty)

        if (
            mode == "questions"
            and worksheet.specification.get("interactive_links", True)
        ):
            from .question_actions import action_links_markup

            # Keep the question number, difficulty and action links in
            # one paragraph inside the existing white question panel.
            # Links retain their own font and colour rather than
            # inheriting the bold, topic-coloured heading style.
            heading_markup = (
                escape(heading)
                + " &nbsp;&nbsp; "
                + '<font name="{}" size="9">'.format(theme.body_font)
                + action_links_markup(question, theme.link_ink)
                + "</font>"
            )
            blocks = [Paragraph(heading_markup, question_label_style)]
        else:
            blocks = [paragraph(heading, question_label_style)]
        if show_source:
            blocks.append(paragraph(source_line(question), style["source"]))

        student_assets = question.visual_assets("questions")
        beside = (
            mode == "questions"
            and len(student_assets) == 1
            and student_assets[0].get("kind") == "scene"
            and not question.choices
            and question.layout_hint.working_lines > 0
        )
        if mode != "answers":
            blocks.extend(question_prompt(question, style["body"]))
            if not beside:
                blocks.extend(visual_blocks(question, "questions"))
        if mode != "answers" and question.choices:
            for index, choice in enumerate(question.choices):
                content = choice.content
                if content.blocks:
                    from .content_rendering import content_flowables
                    option = content_flowables(
                        content, style["body"],
                        question.generator_id + " choice " + str(index + 1),
                    )
                else:
                    option = (
                        MathLine(content.math_tex, size=12) if content.math_tex
                        else paragraph(content.text, style["body"])
                    )
                row = Table(
                    [[paragraph(chr(65 + index) + ".", style["label"]), option]],
                    colWidths=[25, document.width - (49 if mode == "questions" else 37)],
                    hAlign="LEFT",
                )
                row.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]))
                blocks.append(row)
        if mode == "questions":
            # Only the actual question content gets white backing.
            # Reserved writing space remains transparent to the page grid.
            blocks = [white_panel(blocks, document.width - 12)]
            if beside:
                blocks.append(Spacer(1, 6))
                blocks.append(scene_working_row(question, document.width - 12))
                blocks.append(Spacer(1, 6))
            else:
                blocks.append(WorkingSpace(question.layout_hint.working_lines))
        elif mode == "answers":
            if question.answer_display.blocks:
                from .content_rendering import content_flowables
                blocks.extend(content_flowables(
                    question.answer_display, style["body"],
                    question.generator_id + " answer",
                ))
            elif question.answer_display.math_tex:
                blocks.append(MathLine(question.answer_display.math_tex))
            else:
                blocks.append(paragraph(question.answer_display.text, style["body"]))
        else:
            blocks.append(Spacer(1, 6))
            for step in question.worked_solution:
                if step.blocks:
                    from .content_rendering import content_flowables
                    blocks.extend(content_flowables(
                        step, style["body"], question.generator_id + " worked step",
                    ))
                else:
                    if step.text:
                        blocks.append(paragraph(step.text, style["body"]))
                    if step.math_tex:
                        blocks.append(MathLine(step.math_tex, size=12))
        if mode in ("answers", "worked"):
            blocks.extend(visual_blocks(question, "answers"))
        # Action links are now part of the question heading. There is
        # no separate action panel beneath the working space.
        blocks.append(Spacer(1, 14))
        # SimpleDocTemplate's default frame has six-point padding per edge.
        story.append(QuestionBlock(blocks, document.height - 12, number))

    def footer(canvas, doc):
        # Page callbacks execute before flowables, so every panel paints over
        # the grid rather than having grid lines drawn through its content.
        if mode == "questions":
            draw_page_grid(canvas, PAGE_WIDTH, PAGE_HEIGHT,
                           theme.grid_ink, theme.grid_width)
        canvas.saveState()
        if mode == "questions":
            canvas.setFillColor(colors.white)
            canvas.rect(
                MARGIN - 4, 11 * mm - 3,
                PAGE_WIDTH - 2 * MARGIN + 8, 13,
                stroke=0, fill=1,
            )
        canvas.setFont(theme.body_font, 8)
        canvas.setFillColor(colors.HexColor(theme.muted_ink))
        canvas.drawString(MARGIN, 11 * mm, labels[mode])
        canvas.drawCentredString(
            PAGE_WIDTH / 2, 11 * mm, "Set " + worksheet.id[:10]
        )
        canvas.drawRightString(PAGE_WIDTH - MARGIN, 11 * mm, str(doc.page))
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return {
        "mode": mode,
        "path": str(destination),
        "pages": document.page,
        "page_size_points": [PAGE_WIDTH, PAGE_HEIGHT],
        "bytes": destination.stat().st_size,
    }