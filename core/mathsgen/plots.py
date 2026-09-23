"""Vector coordinate plots with explicit scales and clipped continuous segments.

Specifications contain sampled coordinates, not executable expressions.
Generators own the mathematics and must split curves at discontinuities.
Equal units are optional; unequal axes retain explicit numerical scales.
"""
import math
from fractions import Fraction

from reportlab.graphics.shapes import Drawing, Line, Path, Rect, String
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth

from .core import require


INK = HexColor("#202936")
MAJOR = HexColor("#C4CDD7")
MINOR = HexColor("#E9EDF2")


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def axis_ticks(bounds, step):
    require(len(bounds) == 2 and all(finite(v) for v in bounds),
            "Axis bounds must be finite numbers")
    low, high = map(lambda v: Fraction(str(v)), bounds)
    require(low < high, "Axis range must increase")
    require(finite(step) and step > 0, "Tick step must be positive")
    spacing = Fraction(str(step))
    first = math.ceil(low / spacing)
    last = math.floor(high / spacing)
    require(2 <= last - first + 1 <= 31, "Choose between 2 and 31 major ticks")
    return [float(index * spacing) for index in range(first, last + 1)]


def clip_segment(first, second, x_bounds, y_bounds):
    """Clip a segment against a rectangular data window (Liang-Barsky)."""
    x, y = first
    dx, dy = second[0] - x, second[1] - y
    lower, upper = 0.0, 1.0
    for direction, distance in (
        (-dx, x - x_bounds[0]), (dx, x_bounds[1] - x),
        (-dy, y - y_bounds[0]), (dy, y_bounds[1] - y),
    ):
        if direction == 0:
            if distance < 0:
                return None
            continue
        ratio = distance / direction
        if direction < 0:
            lower = max(lower, ratio)
        else:
            upper = min(upper, ratio)
        if lower > upper:
            return None
    return ((x + lower * dx, y + lower * dy),
            (x + upper * dx, y + upper * dy))


def coordinates(points):
    require(isinstance(points, list), "Coordinates must be a list")
    require(all(isinstance(p, (list, tuple)) and len(p) == 2
                and all(finite(value) for value in p) for p in points),
            "Coordinates must be finite pairs; split discontinuous curves explicitly")
    return points


def render_plot(spec, width):
    allowed = {
        "kind", "version", "x_range", "y_range", "x_step", "y_step",
        "x_label", "y_label", "equal_units", "minor_divisions",
        "curves", "points", "bars",
    }
    require(set(spec) <= allowed, "Unknown plot setting")
    x_bounds, y_bounds = spec["x_range"], spec["y_range"]
    xs = axis_ticks(x_bounds, spec["x_step"])
    ys = axis_ticks(y_bounds, spec["y_step"])
    equal = spec.get("equal_units", False)
    require(type(equal) is bool, "equal_units must be boolean")
    divisions = spec.get("minor_divisions", 1)
    require(type(divisions) is int and 1 <= divisions <= 5,
            "minor_divisions must be 1 through 5")

    left, bottom, right, top = 47, 43, 18, 32
    plot_width = width - left - right
    x_span = x_bounds[1] - x_bounds[0]
    y_span = y_bounds[1] - y_bounds[0]
    plot_height = plot_width * y_span / x_span if equal else plot_width * 0.78
    require(90 <= plot_height <= 350,
            "Plot aspect is too tall or too short; adjust ranges or equal_units")
    height = bottom + plot_height + top
    drawing = Drawing(width, height)

    def mapped(point):
        return (
            left + (point[0] - x_bounds[0]) * plot_width / x_span,
            bottom + (point[1] - y_bounds[0]) * plot_height / y_span,
        )

    def segment(first, second, color=INK, weight=1):
        drawing.add(Line(*first, *second, strokeColor=color, strokeWidth=weight))

    def text(x, y, value, anchor="middle", size=9):
        drawing.add(String(
            x, y, value, fontName="Helvetica", fontSize=size,
            textAnchor=anchor, fillColor=INK,
        ))

    x_tick_width = max(stringWidth(format(value, ".10g"), "Helvetica", 9) for value in xs)
    require(plot_width * spec["x_step"] / x_span >= x_tick_width + 5,
            "Horizontal tick labels are too crowded")
    require(plot_height * spec["y_step"] / y_span >= 13,
            "Vertical tick labels are too crowded")

    for bounds, step, vertical in (
        (x_bounds, spec["x_step"], True),
        (y_bounds, spec["y_step"], False),
    ):
        spacing = Fraction(str(step)) / divisions
        low, high = [Fraction(str(v)) for v in bounds]
        start, end = math.ceil(low / spacing), math.floor(high / spacing)
        require(end - start <= 155, "Too many grid lines")
        for index in range(start, end + 1):
            value = float(index * spacing)
            major = index % divisions == 0
            color, weight = (MAJOR, 0.55) if major else (MINOR, 0.3)
            if vertical:
                x = mapped((value, y_bounds[0]))[0]
                segment((x, bottom), (x, bottom + plot_height), color, weight)
            else:
                y = mapped((x_bounds[0], value))[1]
                segment((left, y), (left + plot_width, y), color, weight)

    drawing.add(Rect(
        left, bottom, plot_width, plot_height,
        strokeColor=MAJOR, strokeWidth=0.7, fillColor=None,
    ))
    if x_bounds[0] <= 0 <= x_bounds[1]:
        x = mapped((0, y_bounds[0]))[0]
        segment((x, bottom), (x, bottom + plot_height), weight=1)
    if y_bounds[0] <= 0 <= y_bounds[1]:
        y = mapped((x_bounds[0], 0))[1]
        segment((left, y), (left + plot_width, y), weight=1)

    for value in xs:
        x = mapped((value, y_bounds[0]))[0]
        segment((x, bottom), (x, bottom - 3), weight=0.7)
        text(x, bottom - 15, format(value, ".10g"))
    for value in ys:
        y = mapped((x_bounds[0], value))[1]
        segment((left - 3, y), (left, y), weight=0.7)
        text(left - 7, y - 3, format(value, ".10g"), anchor="end")

    x_label = spec.get("x_label", "x")
    y_label = spec.get("y_label", "y")
    for value in (x_label, y_label):
        require(isinstance(value, str) and "\n" not in value,
                "Axis labels must be single-line text")
        require(stringWidth(value, "Helvetica", 11) <= plot_width,
                "Axis label too long for this layout")
    text(left + plot_width / 2, 8, x_label, size=11)
    text(left + plot_width / 2, bottom + plot_height + 15, y_label, size=11)

    bars = spec.get("bars", [])
    require(isinstance(bars, list), "bars must be a list")
    previous_right = None
    for bar in bars:
        require(isinstance(bar, dict) and set(bar) == {"left", "right", "height"},
                "Each bar needs left, right and height")
        low, high, value = bar["left"], bar["right"], bar["height"]
        require(all(finite(v) for v in (low, high, value)),
                "Bar coordinates must be finite")
        require(low < high and value >= 0, "Invalid bar width or height")
        require(x_bounds[0] <= low < high <= x_bounds[1]
                and y_bounds[0] <= 0 <= value <= y_bounds[1],
                "Bars must fit the axes and include their zero baseline")
        require(previous_right is None or low >= previous_right,
                "Bars must be ordered and must not overlap")
        previous_right = high
        x0, y0 = mapped((low, 0))
        x1, y1 = mapped((high, value))
        if value:
            # Unfilled, so the grid stays visible inside the bar: a student
            # reading a frequency density needs the gridlines behind the bar,
            # not only beside it.
            drawing.add(Rect(
                x0, y0, x1 - x0, y1 - y0,
                strokeColor=INK, strokeWidth=1,
                fillColor=None,
            ))

    for curve in spec.get("curves", []):
        require(set(curve) <= {"segments", "dashed"}, "Unknown curve setting")
        dashed = curve.get("dashed", False)
        require(type(dashed) is bool, "dashed must be boolean")
        for continuous in curve["segments"]:
            points = coordinates(continuous)
            require(2 <= len(points) <= 5000, "Curve segment needs 2 to 5000 points")
            path = Path(
                strokeColor=INK, strokeWidth=1.6, fillColor=None,
                strokeDashArray=[5, 3] if dashed else None,
            )
            visible = False
            for first, second in zip(points, points[1:]):
                clipped = clip_segment(first, second, x_bounds, y_bounds)
                if clipped is not None:
                    path.moveTo(*mapped(clipped[0]))
                    path.lineTo(*mapped(clipped[1]))
                    visible = True
            if visible:
                drawing.add(path)

    for point in coordinates(spec.get("points", [])):
        require(x_bounds[0] <= point[0] <= x_bounds[1]
                and y_bounds[0] <= point[1] <= y_bounds[1],
                "Scatter point falls outside the axis ranges")
        x, y = mapped(point)
        # Fixed-size crosses remain visible when the plot becomes narrower.
        segment((x - 3, y - 3), (x + 3, y + 3), weight=1.3)
        segment((x - 3, y + 3), (x + 3, y - 3), weight=1.3)
    return drawing