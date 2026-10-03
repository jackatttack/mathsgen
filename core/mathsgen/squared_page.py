"""Continuous page paper and measured panels with theme-controlled backing."""
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


def draw_page_background(canvas, width, height, theme, squared=True):
    """Paint the paper before its grid and before any question content."""
    canvas.saveState()
    try:
        canvas.setFillColor(colors.HexColor(theme.paper_ink))
        canvas.rect(0, 0, width, height, stroke=0, fill=1)
    finally:
        canvas.restoreState()
    if squared:
        draw_page_grid(canvas, width, height, theme.grid_ink, theme.grid_width)


def content_panel(blocks, width, theme=None):
    """Keep panel measurement and padding; omit backing for open-paper themes."""
    background = "#FFFFFF" if theme is None else (
        theme.paper_ink if theme.opaque_panels else None
    )
    return white_panel(blocks, width, background)


def white_panel(blocks, width, background="#FFFFFF"):
    """A single unsplit table cell measures and backs all contained content.

    ReportLab measures the actual paragraphs, maths and visuals.
    A None background leaves the page visible. The six-point padding and
    unsplit layout are identical with or without backing.
    """
    panel = Table(
        [[list(blocks)]], colWidths=[width], hAlign="LEFT",
        splitByRow=0,
    )
    panel.setStyle(TableStyle([

        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    if background is not None:
        panel.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(background)),
        ]))
    return panel