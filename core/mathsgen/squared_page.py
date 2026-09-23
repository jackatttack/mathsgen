"""Continuous page grid and opaque, content-sized question panels."""
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle


def draw_page_grid(canvas, width, height, colour="#D0BDE7", line_width=0.35):
    """Anchor every line to page coordinates so the grid stays continuous.

    colour and line_width come from the worksheet theme (theme.py).
    """
    canvas.saveState()
    try:
        canvas.setStrokeColor(colors.HexColor(colour))
        canvas.setLineWidth(line_width)
        cell = 5 * mm
        for column in range(int(width / cell) + 1):
            x = column * cell
            canvas.line(x, 0, x, height)
        for row in range(int(height / cell) + 1):
            y = row * cell
            canvas.line(0, y, width, y)
    finally:
        canvas.restoreState()


def white_panel(blocks, width):
    """A single unsplit table cell measures and backs all contained content.

    ReportLab measures the actual paragraphs, maths and visuals before drawing
    the white background. No estimated text height or overlay coordinates.
    Six-point padding keeps glyphs and diagrams away from the surrounding grid.
    """
    panel = Table(
        [[list(blocks)]], colWidths=[width], hAlign="LEFT",
        splitByRow=0,
    )
    panel.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return panel