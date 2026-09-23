"""Shared PDF/SVG vector assets. Coordinates describe layout, not mathematical truth.

Scene coordinates use x rightwards and y upwards in a 360-point design space.
Geometry scales to the requested width; fonts and stroke widths do not.
Generators retain exact mathematical data separately in Question.parameters.
"""
import math
from functools import lru_cache

from reportlab.graphics.shapes import (
    Drawing, Group, Line, Polygon, Circle, Rect, String, Path,
)
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Flowable

from .core import require


INK = "#202936"
SHADE = "#E7EBF0"
GRID = "#A8B1BC"
FONT_SIZE = 11


def scene(nodes, height=220, caption="Not drawn accurately"):
    return {
        "kind": "scene", "version": 1, "width": 360,
        "height": height, "caption": caption, "nodes": nodes,
    }


def line(first, second, **style):
    return dict(type="line", points=[first, second], **style)


def label(point, text="", tex=""):
    return {"type": "label", "point": point, "text": text, "tex": tex}


@lru_cache(maxsize=256)
def math_path(tex, size):
    """Convert MathText to a portable vector path, without external LaTeX."""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    from matplotlib.path import Path as MPLPath

    outline = TextPath(
        (0, 0), "$" + tex + "$", size=size,
        prop=FontProperties(family="DejaVu Sans"), usetex=False,
    )
    bounds = outline.get_extents()
    path = Path(fillColor=HexColor(INK), strokeColor=None)
    current = start = (0, 0)
    for vertices, code in outline.iter_segments(curves=True, simplify=False):
        values = list(map(float, vertices))
        if code == MPLPath.MOVETO:
            path.moveTo(*values)
            current = start = tuple(values)
        elif code == MPLPath.LINETO:
            path.lineTo(*values)
            current = tuple(values)
        elif code == MPLPath.CURVE3:
            control, end = values[:2], values[2:]
            one = [current[i] + (control[i] - current[i]) * 2 / 3 for i in (0, 1)]
            two = [end[i] + (control[i] - end[i]) * 2 / 3 for i in (0, 1)]
            path.curveTo(*(one + two + end))
            current = tuple(end)
        elif code == MPLPath.CURVE4:
            path.curveTo(*values)
            current = tuple(values[-2:])
        elif code == MPLPath.CLOSEPOLY:
            path.closePath()
            current = start
        elif code != MPLPath.STOP:
            raise ValueError("Unsupported mathematical path command")
    return path, tuple(map(float, (bounds.x0, bounds.y0, bounds.width, bounds.height)))


def text_shape(content, x, y, bold=False):
    """Return centered text and its conservative bounding box."""
    if isinstance(content, str):
        content = {"text": content}
    tex = content.get("tex", "")
    if tex:
        path, (left, bottom, width, height) = math_path(tex, FONT_SIZE)
        group = Group()
        group.add(path)
        group.translate(x - width / 2 - left, y - height / 2 - bottom)
        return group, (x - width / 2, y - height / 2, x + width / 2, y + height / 2)
    text = content.get("text", "")
    require(isinstance(text, str) and "\n" not in text, "Labels must be single-line text")
    font = "Helvetica-Bold" if bold else "Helvetica"
    width = stringWidth(text, font, FONT_SIZE)
    shape = String(
        x, y - FONT_SIZE * 0.35, text, fontName=font,
        fontSize=FONT_SIZE, textAnchor="middle", fillColor=HexColor(INK),
    )
    return shape, (x - width / 2, y - 6, x + width / 2, y + 6)


def unit(vector):
    length = math.hypot(*vector)
    require(length > 0, "A marking needs a nonzero segment")
    return (vector[0] / length, vector[1] / length)


def add_segment(drawing, first, second, dashed=False, width=1.2, color=INK):
    drawing.add(Line(
        *first, *second, strokeColor=HexColor(color), strokeWidth=width,
        strokeDashArray=[4, 3] if dashed else None,
    ))


def arc_path(center, radius, start, sweep):
    """Circular arc as cubic Bezier segments, shared by PDF and SVG."""
    require(radius > 0 and 0 < abs(sweep) <= 360, "Invalid arc")
    path = Path(fillColor=None, strokeColor=HexColor(INK), strokeWidth=1)
    count = max(1, int(math.ceil(abs(sweep) / 90)))
    angle = math.radians(start)
    step = math.radians(sweep / count)
    cx, cy = center
    path.moveTo(cx + radius * math.cos(angle), cy + radius * math.sin(angle))
    for _ in range(count):
        end = angle + step
        k = 4 / 3 * math.tan(step / 4)
        path.curveTo(
            cx + radius * (math.cos(angle) - k * math.sin(angle)),
            cy + radius * (math.sin(angle) + k * math.cos(angle)),
            cx + radius * (math.cos(end) + k * math.sin(end)),
            cy + radius * (math.sin(end) - k * math.cos(end)),
            cx + radius * math.cos(end), cy + radius * math.sin(end),
        )
        angle = end
    return path


def draw_scene(spec, width):
    scale = width / spec["width"]
    height = spec["height"] * scale

    # Suppress the standard accuracy disclaimer in rendered diagrams.
    # Preserve any other caption that carries useful information.
    caption = spec.get("caption") or ""
    if caption.strip().casefold() == "not drawn accurately":
        caption = ""

    caption_height = 22 if caption else 0
    drawing = Drawing(width, height + caption_height)
    boxes = []

    def point(value):
        require(len(value) == 2 and all(math.isfinite(v) for v in value),
                "Invalid coordinate")
        return (value[0] * scale, value[1] * scale + caption_height)

    for node in spec["nodes"]:
        kind = node["type"]
        if kind == "label":
            x, y = point(node["point"])
            shape, box = text_shape(node, x, y)
            require(box[0] >= 3 and box[2] <= width - 3
                    and box[1] >= caption_height + 2
                    and box[3] <= drawing.height - 2, "Label extends outside diagram")
            for previous in boxes:
                overlap = (box[0] < previous[2] + 3 and box[2] > previous[0] - 3
                           and box[1] < previous[3] + 3 and box[3] > previous[1] - 3)
                require(not overlap, "Diagram labels overlap; adjust their positions")
            boxes.append(box)
            drawing.add(shape)
        elif kind in ("line", "polygon"):
            points = [point(value) for value in node["points"]]
            if kind == "line":
                require(len(points) == 2, "Line needs two points")
                add_segment(drawing, *points, dashed=node.get("dashed", False))
                if node.get("arrow"):
                    end = points[1]
                    u = unit((end[0] - points[0][0], end[1] - points[0][1]))
                    for sign in (-1, 1):
                        back = (end[0] - 7 * u[0] + sign * 3 * u[1],
                                end[1] - 7 * u[1] - sign * 3 * u[0])
                        add_segment(drawing, back, end)
            else:
                require(len(points) >= 3, "Polygon needs at least three points")
                drawing.add(Polygon(
                    [v for p in points for v in p],
                    strokeColor=HexColor(INK), strokeWidth=1.2,
                    fillColor=HexColor(SHADE) if node.get("shade") else None,
                ))
        elif kind == "circle":
            center = point(node["center"])
            require(node["radius"] > 0, "Invalid circle radius")
            drawing.add(Circle(
                *center, node["radius"] * scale,
                strokeColor=HexColor(INK), strokeWidth=1.2,
                fillColor=HexColor(SHADE) if node.get("shade") else None,
            ))
        elif kind == "arc":
            drawing.add(arc_path(
                point(node["center"]), node["radius"] * scale,
                node["start"], node["sweep"],
            ))
        elif kind == "right_angle":
            vertex = point(node["vertex"])
            first, second = point(node["first"]), point(node["second"])
            u = unit((first[0] - vertex[0], first[1] - vertex[1]))
            v = unit((second[0] - vertex[0], second[1] - vertex[1]))
            require(abs(u[0] * v[0] + u[1] * v[1]) < 0.001,
                    "Right-angle marker attached to nonperpendicular rays")
            size = 9
            p = (vertex[0] + size * u[0], vertex[1] + size * u[1])
            q = (p[0] + size * v[0], p[1] + size * v[1])
            r = (vertex[0] + size * v[0], vertex[1] + size * v[1])
            add_segment(drawing, p, q, width=1)
            add_segment(drawing, q, r, width=1)
        elif kind in ("ticks", "parallel"):
            first, second = [point(p) for p in node["points"]]
            u = unit((second[0] - first[0], second[1] - first[1]))
            fraction = node.get("position", 0.5)
            require(0 < fraction < 1, "Marking must lie inside segment")
            center = [first[i] + fraction * (second[i] - first[i]) for i in (0, 1)]
            count = node.get("count", 1)
            require(type(count) is int and 1 <= count <= 3, "Invalid marking count")
            for index in range(count):
                offset = (index - (count - 1) / 2) * 5
                x, y = center[0] + offset * u[0], center[1] + offset * u[1]
                if kind == "ticks":
                    add_segment(drawing, (x - 4 * u[1], y + 4 * u[0]),
                                (x + 4 * u[1], y - 4 * u[0]), width=1)
                else:
                    for sign in (-1, 1):
                        add_segment(
                            drawing, (x - 4 * u[0] + sign * 3 * u[1],
                                      y - 4 * u[1] - sign * 3 * u[0]),
                            (x + 3 * u[0], y + 3 * u[1]), width=1,
                        )
        else:
            raise ValueError("Unsupported diagram node: " + str(kind))

    # This catches overflowing shapes as well as labels.
    bounds = drawing.getBounds()
    if bounds:
        require(bounds[0] >= 1 and bounds[1] >= caption_height
                and bounds[2] <= width - 1 and bounds[3] <= drawing.height - 1,
                "Geometry extends outside diagram")
    if caption_height:
        drawing.add(String(
            width / 2, 5, caption, textAnchor="middle",
            fontName="Helvetica-Oblique", fontSize=9, fillColor=HexColor("#64748B"),
        ))

    # The design canvas provides coordinates, not required page whitespace.
    # Measure the finished diagram, including labels and curved geometry.
    # Move its existing shapes into a tighter canvas without rescaling them.
    visible = drawing.getBounds()
    if visible is None:
        return drawing

    left, bottom, right, top = visible
    padding = 5

    cropped = Drawing(
        right - left + 2 * padding,
        top - bottom + 2 * padding,
    )
    content = Group()
    for shape in drawing.contents:
        content.add(shape)

    content.translate(padding - left, padding - bottom)
    cropped.add(content)
    return cropped


def draw_table(spec, width):
    headers, rows = spec["headers"], spec["rows"]
    columns = len(headers)
    require(columns > 0 and rows and all(len(row) == columns for row in rows),
            "Table must have matching headers and rows")
    weights = spec.get("weights", [1] * columns)
    require(len(weights) == columns and all(w > 0 for w in weights),
            "Invalid column weights")
    widths = [width * w / sum(weights) for w in weights]
    content = [headers] + rows
    cells = []
    heights = []
    for row_index, row in enumerate(content):
        measured = [text_shape(cell, 0, 0, bold=row_index == 0) for cell in row]
        for column, (_, box) in enumerate(measured):
            require(box[2] - box[0] + 20 <= widths[column],
                    "Table column too narrow; shorten its label or increase width")
        heights.append(max(30, max(box[3] - box[1] + 16 for _, box in measured)))
        cells.append(measured)
    height = sum(heights)
    drawing = Drawing(width, height)
    y = height
    for row_index, row in enumerate(content):
        row_height = heights[row_index]
        y -= row_height
        if row_index == 0 or row_index % 2 == 0:
            drawing.add(Rect(
                0, y, width, row_height, strokeColor=None,
                fillColor=HexColor("#E7EBF0" if row_index == 0 else "#F5F6F8"),
            ))
        x = 0
        for column, cell in enumerate(row):
            shape, _ = text_shape(
                cell, x + widths[column] / 2, y + row_height / 2,
                bold=row_index == 0,
            )
            drawing.add(shape)
            x += widths[column]
        add_segment(drawing, (0, y), (width, y), width=0.5, color=GRID)
    drawing.add(Rect(0, 0, width, height, fillColor=None,
                     strokeColor=HexColor(GRID), strokeWidth=0.7))
    x = 0
    for column_width in widths[:-1]:
        x += column_width
        add_segment(drawing, (x, 0), (x, height), width=0.5, color=GRID)
    return drawing


def drawing_for(spec, width=360):
    require(spec.get("version") == 1, "Unsupported visual specification version")
    require(math.isfinite(width) and width >= 220, "Visual needs at least 220 points")
    if spec["kind"] == "scene":
        require(spec["width"] > 0 and spec["height"] > 0, "Invalid scene dimensions")
        return draw_scene(spec, width)
    if spec["kind"] == "table":
        return draw_table(spec, width)
    if spec["kind"] == "plot":
        from .plots import render_plot
        return render_plot(spec, width)
    if spec["kind"] == "boxplot":
        from .boxplots import render_boxplot
        return render_boxplot(spec, width)
    if spec["kind"] == "venn":
        from .venn_diagrams import render_venn
        return render_venn(spec, width)
    raise ValueError("Unsupported visual kind: " + str(spec["kind"]))


def svg_text(spec, width=360):
    from reportlab.graphics import renderSVG
    value = renderSVG.drawToString(drawing_for(spec, width))
    return value.decode("utf-8") if isinstance(value, bytes) else value


class VisualFlowable(Flowable):
    """Fit geometry to the column without shrinking its typography."""
    def __init__(self, spec, preferred_width=360):
        Flowable.__init__(self)
        self.spec = spec
        self.preferred_width = preferred_width
        self.hAlign = "CENTER"
        self.drawing = None

    def wrap(self, available_width, available_height):
        # A cropped scene can be much narrower than its design canvas.
        # ReportLab may wrap it again inside a tightly fitted table.
        # Keep the existing drawing when it fits: rebuilding at the
        # cropped width would shrink the geometry and crowd its labels.
        if (
            self.spec["kind"] == "scene"
            and self.drawing is not None
            and self.width <= available_width + 0.01
        ):
            return self.width, self.height

        self.drawing = drawing_for(
            self.spec,
            min(self.preferred_width, available_width),
        )
        self.width, self.height = self.drawing.width, self.drawing.height
        return self.width, self.height

    def split(self, available_width, available_height):
        return []

    def draw(self):
        from reportlab.graphics import renderPDF
        require(self.drawing is not None, "Visual must be laid out before drawing")
        renderPDF.draw(self.drawing, self.canv, 0, 0)