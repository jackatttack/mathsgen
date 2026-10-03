"""Measured worksheet headings for Ivory's exercise-book design.

All dimensions are PDF points. Titles wrap at their actual available width;
decoration never occupies space needed by the title.
"""
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Flowable, Paragraph


# Editable heading proportions.
SECTION_TITLE_SIZE = 19
SECTION_NUMBER_SIZE = 34
QUESTION_TITLE_SIZE = 16
QUESTION_NUMBER_SIZE = 27
BADGE_SIZE = 9
RULE_WIDTH = 0.6


class LevelBadge(Flowable):
    """A small outlined label; no fill obscures the underlying paper."""

    def __init__(self, text, theme):
        super().__init__()
        self.text = str(text)
        self.theme = theme
        self.width = stringWidth(self.text, theme.body_font, BADGE_SIZE) + 14
        self.height = 19
        self.keepWithNext = True

    def wrap(self, available_width, available_height):
        if self.width > available_width:
            raise ValueError("Level badge is wider than its available space")
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        try:
            canvas.setStrokeColor(colors.HexColor(self.theme.link_ink))
            canvas.setFillColor(colors.HexColor(self.theme.link_ink))
            canvas.setLineWidth(0.55)
            canvas.rect(0, 1, self.width, 17, stroke=1, fill=0)
            canvas.setFont(self.theme.body_font, BADGE_SIZE)
            canvas.drawString(7, 6, self.text)
        finally:
            canvas.restoreState()


class SectionHeading(Flowable):
    """Large number, wrapping serif title, fine rule and optional level badge."""

    def __init__(self, number, title, theme, compact=False, badge=None):
        super().__init__()
        self.number = str(number)
        self.title = str(title)
        self.theme = theme
        self.title_size = QUESTION_TITLE_SIZE if compact else SECTION_TITLE_SIZE
        self.number_size = QUESTION_NUMBER_SIZE if compact else SECTION_NUMBER_SIZE
        self.badge = LevelBadge(badge, theme) if badge else None
        self.title_style = ParagraphStyle(
            "IvorySectionTitle", fontName=theme.bold_font,
            fontSize=self.title_size, leading=self.title_size + 4,
            textColor=colors.HexColor(theme.accent),
        )
        self.keepWithNext = True

    def wrap(self, available_width, available_height):
        self.width = available_width
        number_width = stringWidth(
            self.number, self.theme.bold_font, self.number_size)
        self.title_x = number_width + 14
        badge_space = self.badge.width + 12 if self.badge else 0
        title_width = available_width - self.title_x - badge_space
        if title_width < 50:
            raise ValueError("Section heading has insufficient title space")
        self.title_paragraph = Paragraph(escape(self.title), self.title_style)
        _, self.title_height = self.title_paragraph.wrap(title_width, 10000)
        self.height = max(self.number_size + 3, self.title_height) + 8
        self.title_width = title_width
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        try:
            ink = colors.HexColor(self.theme.accent)
            canvas.setFillColor(ink)
            canvas.setStrokeColor(ink)
            canvas.setLineWidth(RULE_WIDTH)
            top = self.height - 4
            canvas.setFont(self.theme.bold_font, self.number_size)
            canvas.drawString(0, top - self.number_size, self.number)
            title_bottom = top - self.title_height
            self.title_paragraph.drawOn(canvas, self.title_x, title_bottom)

            rule_end = self.width
            if self.badge:
                badge_x = self.width - self.badge.width
                self.badge.drawOn(canvas, badge_x, top - self.badge.height - 2)
                rule_end = badge_x - 12

            single_line = self.title_height <= self.title_style.leading + 0.1
            text_width = stringWidth(
                self.title, self.theme.bold_font, self.title_size)
            rule_start = self.title_x + text_width + 12
            if single_line and rule_end - rule_start >= 24:
                rule_y = title_bottom + self.title_size * 0.35
                canvas.line(rule_start, rule_y, rule_end, rule_y)
            else:
                # Long titles get their rule below, never through the text.
                canvas.line(self.title_x, 2, self.width, 2)
        finally:
            canvas.restoreState()