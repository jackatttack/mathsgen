"""Mixed prose and vector mathematics with explicit runs and measured wrapping.

Runs are {"text": "..."} or {"tex": "...", "text": "plain fallback"}.
Whitespace allows wrapping; adjacent runs without whitespace stay together.
This module does not infer mathematics from prose or evaluate expressions.
"""
import math
import re
from functools import lru_cache

from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Flowable

from .core import require


@lru_cache(maxsize=512)
def math_geometry(tex, size):
    """Immutable outline commands and metrics; preserve the mathematical baseline."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath, TextToPath
    font = FontProperties(family="DejaVu Sans", size=size)
    source = "$" + tex + "$"
    try:
        advance, height, descent = TextToPath().get_text_width_height_descent(
            source, font, ismath=True,
        )
        outline = TextPath((0, 0), source, prop=font, size=size, usetex=False)
        bounds = outline.get_extents()
        values = (advance, height, descent, bounds.x0, bounds.y0, bounds.x1, bounds.y1)
        require(all(math.isfinite(float(value)) for value in values), "Nonfinite metrics")
        commands = tuple(
            (tuple(float(value) for value in vertices), int(code))
            for vertices, code in outline.iter_segments(curves=True, simplify=False)
        )
    except Exception as error:
        raise ValueError("Cannot render mathematical run {!r}: {}".format(tex, error)) from error
    left_padding = max(0.0, -float(bounds.x0))
    width = max(float(advance), float(bounds.x1)) + left_padding
    ascent = max(0.0, float(height - descent), float(bounds.y1))
    below = max(0.0, float(descent), -float(bounds.y0))
    return width, ascent, below, left_padding, commands


def draw_math(canvas, commands):
    """Draw immutable Matplotlib outline commands on a ReportLab canvas."""
    from matplotlib.path import Path
    path = canvas.beginPath()
    current = start = (0.0, 0.0)
    for vertices, code in commands:
        if code == Path.MOVETO:
            path.moveTo(*vertices)
            current = start = vertices
        elif code == Path.LINETO:
            path.lineTo(*vertices)
            current = vertices
        elif code == Path.CURVE3:
            control, end = vertices[:2], vertices[2:4]
            first = tuple(current[i] + (control[i] - current[i]) * 2 / 3 for i in (0, 1))
            second = tuple(end[i] + (control[i] - end[i]) * 2 / 3 for i in (0, 1))
            path.curveTo(*(first + second + end))
            current = end
        elif code == Path.CURVE4:
            path.curveTo(*vertices)
            current = vertices[-2:]
        elif code == Path.CLOSEPOLY:
            path.close()
            current = start
        elif code != Path.STOP:
            raise ValueError("Unsupported mathematical outline command")
    canvas.drawPath(path, stroke=0, fill=1, fillMode=1)


class RichParagraph(Flowable):
    """Wrap words and atomic maths on shared baselines, without clipping tall runs."""

    def __init__(self, runs, size=11, leading=16, color="#17212B", context="rich paragraph"):
        Flowable.__init__(self)
        require(isinstance(runs, (list, tuple)) and bool(runs), "Runs must be nonempty")
        require(8 <= size <= 24 and leading >= size, "Invalid typography settings")
        self.size = size
        self.leading = leading
        self.color = color
        self.context = context
        self.spaceAfter = 6
        self.words = []
        self.lines = []
        self._wrapped_width = None
        current = []

        def finish_word():
            if current:
                self.words.append(tuple(current))
                current.clear()

        for run in runs:
            require(isinstance(run, dict) and set(run) in ({"text"}, {"text", "tex"}),
                    "Run must contain text, optionally tex")
            require(isinstance(run["text"], str), "Run fallback must be text")
            if "tex" in run:
                require(isinstance(run["tex"], str) and bool(run["tex"].strip()),
                        "Mathematical run needs nonempty TeX")
                try:
                    width, ascent, descent, offset, commands = math_geometry(run["tex"], size)
                except ValueError as error:
                    raise ValueError(context + ": " + str(error)) from error
                current.append((width, ascent, descent, "math", commands, offset))
            else:
                for fragment in re.findall(r"\s+|\S+", run["text"]):
                    if fragment.isspace():
                        finish_word()
                    else:
                        current.append((
                            stringWidth(fragment, "Helvetica", size),
                            size * 0.8, size * 0.23, "text", fragment, 0,
                        ))
        finish_word()
        require(bool(self.words), "Paragraph has no visible content")

    def wrap(self, available_width, available_height):
        require(available_width > 0, "Paragraph needs positive width")
        if self._wrapped_width == available_width:
            return self.width, self.height
        self.lines = []
        space = stringWidth(" ", "Helvetica", self.size)
        pieces = []
        used = 0.0
        ascent, descent = self.size * 0.8, self.size * 0.23

        def finish_line():
            nonlocal pieces, used, ascent, descent
            if pieces:
                line_height = max(self.leading, ascent + descent + 4)
                self.lines.append((tuple(pieces), ascent, descent, line_height))
            pieces = []
            used = 0.0
            ascent, descent = self.size * 0.8, self.size * 0.23

        for word in self.words:
            width = sum(piece[0] for piece in word)
            require(
                width <= available_width,
                "{}: unbreakable text/maths group is {:.1f} pt wide; column is {:.1f} pt. "
                "Use a separate equation or an explicit space.".format(
                    self.context, width, available_width,
                ),
            )
            gap = space if pieces else 0
            if pieces and used + gap + width > available_width:
                finish_line()
                gap = 0
            used += gap
            for piece in word:
                pieces.append((used, piece))
                used += piece[0]
                ascent = max(ascent, piece[1])
                descent = max(descent, piece[2])
        finish_line()
        self.width = available_width
        self.height = sum(line[3] for line in self.lines)
        self._wrapped_width = available_width
        return self.width, self.height

    def split(self, available_width, available_height):
        # QuestionBlock owns question pagination; never split a math run.
        return []

    def draw(self):
        require(self._wrapped_width is not None, "Paragraph must be wrapped before drawing")
        canvas = self.canv
        canvas.saveState()
        try:
            canvas.setFillColor(HexColor(self.color))
            canvas.setFont("Helvetica", self.size)
            top = self.height
            for pieces, ascent, descent, line_height in self.lines:
                baseline = top - 2 - ascent
                for x, piece in pieces:
                    width, above, below, kind, payload, offset = piece
                    if kind == "text":
                        canvas.drawString(x, baseline, payload)
                    else:
                        canvas.saveState()
                        try:
                            canvas.translate(x + offset, baseline)
                            draw_math(canvas, payload)
                        finally:
                            canvas.restoreState()
                top -= line_height
        finally:
            canvas.restoreState()