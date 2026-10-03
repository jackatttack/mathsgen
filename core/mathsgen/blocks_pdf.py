"""PDF layout for block sheets: each block in its own style, one document.

Question blocks print exactly as on a normal worksheet (pdf.question_story)
and are numbered continuously across the sheet. Drill blocks print exactly
as drill exercises (drill_pdf.exercise_story), numbered Exercise 1, 2, ...
in sheet order. One header and one footer cover the whole sheet.
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Spacer

from .core import require
from .drill import drill_stages
from .drill_pdf import exercise_story
from .pdf import MARGIN, PAGE_HEIGHT, PAGE_WIDTH, paragraph, question_story, styles
from .squared_page import content_panel, draw_page_background
from .theme import theme_for
from .worksheets import Worksheet


PAGE_LABELS = {"questions": "Practice worksheet", "answers": "Answer sheet"}


def block_parts(worksheet):
    """[(segment, part)] in sheet order, each block's questions as a worksheet.

    Drill parts carry their drill specification, so drill_stages regroups
    them into stages exactly as on a drill sheet.
    """
    parts = []
    for segment in worksheet.specification["segments"]:
        start = segment["start"]
        chunk = tuple(worksheet.questions[start:start + segment["count"]])
        if segment["kind"] == "drill":
            specification = {"mode": "drill", "title": worksheet.title,
                             "blocks": segment["drill_blocks"]}
        else:
            specification = {"mode": "questions"}
        parts.append((segment, Worksheet(
            worksheet.id, worksheet.title, worksheet.seed, specification, chunk)))
    return parts


def render_blocks_pdf(worksheet, destination, mode="questions"):
    """Write the question or answer variant of a block sheet."""
    require(mode in PAGE_LABELS, "Block sheets support question and answer PDFs only.")
    require(worksheet.specification.get("mode") == "blocks", "Not a block sheet.")
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

    story = [
        paragraph(worksheet.title, style["title"]),
        paragraph(PAGE_LABELS[mode], style["subtitle"]),
    ]
    if on_paper:
        story.extend([
            paragraph("Name: ________________________    Date: ______________", style["body"]),
            Spacer(1, 12),
        ])
        story = [content_panel(story, width, theme), Spacer(1, 10)]

    question_number = exercise_number = 0
    report = []
    for segment, part in block_parts(worksheet):
        if segment["kind"] == "drill":
            for block, stages in drill_stages(part):
                exercise_number += 1
                flowables, block_report = exercise_story(
                    exercise_number, block, stages, style, theme, width, on_paper)
                story.extend(flowables)
                report.append(block_report)
        else:
            for question in part.questions:
                question_number += 1
                story.append(question_story(
                    question, question_number, mode, worksheet.specification,
                    style, theme, document.width, document.height,
                ))

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
        "questions_numbered": question_number,
    }