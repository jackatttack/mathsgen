"""Horizontal box plots with a shared numerical scale and fixed-size labels."""
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth

from .core import require
from .plots import axis_ticks, finite


def render_boxplot(spec, width):
    allowed = {"kind", "version", "range", "step", "label", "groups"}
    require(set(spec) <= allowed, "Unknown box-plot setting")
    bounds, step = spec["range"], spec["step"]
    ticks = axis_ticks(bounds, step)
    groups = spec["groups"]
    require(isinstance(groups, list) and 1 <= len(groups) <= 4,
            "Box plots need one to four groups")
    title = spec.get("label", "")
    require(isinstance(title, str) and "\n" not in title,
            "Axis label must be single-line text")
    left, right, bottom = 28, 28, 48
    span = width - left - right
    require(stringWidth(title, "Helvetica", 11) <= span, "Axis label too long")
    tick_width = max(stringWidth(format(v, ".10g"), "Helvetica", 9) for v in ticks)
    require(span * step / (bounds[1] - bounds[0]) >= tick_width + 6,
            "Box-plot tick labels are too crowded")
    height = bottom + 85 * len(groups) + 12
    drawing = Drawing(width, height)
    ink = HexColor("#202936")

    def mapped(value):
        return left + (value - bounds[0]) * span / (bounds[1] - bounds[0])

    def line(x1, y1, x2, y2, color=ink, weight=1):
        drawing.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=weight))

    def text(x, y, value, size=11):
        drawing.add(String(
            x, y, value, textAnchor="middle", fontName="Helvetica",
            fontSize=size, fillColor=ink,
        ))

    for value in ticks:
        x = mapped(value)
        line(x, bottom, x, height - 12, HexColor("#E4E8EB"), 0.4)
        line(x, bottom - 3, x, bottom, weight=0.7)
        text(x, bottom - 16, format(value, ".10g"), 9)
    line(left, bottom, width - right, bottom)
    text(width / 2, 8, title)

    names = set()
    for index, group in enumerate(groups):
        require(isinstance(group, dict) and set(group) == {"label", "values"},
                "Each group needs label and values")
        name = group["label"]
        require(isinstance(name, str) and name.strip() and "\n" not in name,
                "Group label must be nonempty single-line text")
        require(name not in names, "Group labels must be distinct")
        names.add(name)
        require(stringWidth(name, "Helvetica", 11) <= span, "Group label too long")
        center = height - 59 - index * 85
        text(width / 2, center + 27, name)
        values = group["values"]
        # None deliberately leaves a student drawing space on the shared scale.
        if values is None:
            continue
        require(isinstance(values, (list, tuple)) and len(values) == 5
                and all(finite(v) for v in values),
                "A box plot needs five finite values")
        require(all(a <= b for a, b in zip(values, values[1:])),
                "Five-number summary must be ordered")
        require(bounds[0] <= values[0] <= values[-1] <= bounds[1],
                "Box plot falls outside the axis range")
        minimum, q1, median, q3, maximum = map(mapped, values)
        line(minimum, center, q1, center, weight=1.2)
        line(q3, center, maximum, center, weight=1.2)
        for x in (minimum, maximum):
            line(x, center - 9, x, center + 9, weight=1.2)
        if q3 > q1:
            drawing.add(Rect(
                q1, center - 13, q3 - q1, 26,
                fillColor=HexColor("#E7EBF0"), strokeColor=ink, strokeWidth=1.2,
            ))
        line(median, center - 13, median, center + 13, weight=1.5)
    return drawing