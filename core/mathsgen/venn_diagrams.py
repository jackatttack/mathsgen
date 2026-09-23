"""Two-set Venn diagrams with independently shaded regions.

Regions are ordered as:
    A only, A intersection B, B only, neither.

The three circular regions are constructed from cubic Bezier arcs.
The exterior is filled first; the three interior regions are then
drawn individually. This avoids approximate polygon intersections.

All coordinates describe presentation, never mathematical truth.
"""
import math

from reportlab.graphics.shapes import (
    Drawing, Group, Rect, Circle, Path, String,
)
from reportlab.lib.colors import HexColor

from .core import require
from .visuals import INK, text_shape


# --- Editable appearance -------------------------------------------------

DESIGN_WIDTH = 360
DESIGN_HEIGHT = 270

BACKGROUND = "#FFFFFF"
SELECTED = "#BBDCF8"

LEFT_CENTER = (135, 130)
RIGHT_CENTER = (225, 130)
RADIUS = 75

REGION_POSITIONS = (
    (103, 130),    # A only
    (180, 130),    # Intersection
    (257, 130),    # B only
    (310, 60),     # Neither
)

SET_LABELS = (
    ("A", 115, 226),
    ("B", 245, 226),
    ("U", 30, 232),
)


# --- Circle intersection geometry ---------------------------------------

def intersection_geometry():
    """Return the angles and crossing points of the two equal circles."""
    separation = RIGHT_CENTER[0] - LEFT_CENTER[0]

    require(
        0 < separation < 2 * RADIUS,
        "Venn circles must overlap",
    )

    angle = math.acos(separation / (2 * RADIUS))
    crossing_height = RADIUS * math.sin(angle)
    midpoint = (LEFT_CENTER[0] + RIGHT_CENTER[0]) / 2

    upper = (midpoint, LEFT_CENTER[1] + crossing_height)
    lower = (midpoint, LEFT_CENTER[1] - crossing_height)

    return angle, upper, lower


def append_arc(path, center, radius, start, sweep):
    """Append a circular arc as cubic Bezier segments.

    Angles are in radians. Each segment spans at most 90 degrees.
    """
    count = max(1, math.ceil(abs(sweep) / (math.pi / 2)))
    step = sweep / count

    for index in range(count):
        first = start + index * step
        last = first + step

        coefficient = 4 * math.tan(step / 4) / 3

        first_x = center[0] + radius * math.cos(first)
        first_y = center[1] + radius * math.sin(first)

        last_x = center[0] + radius * math.cos(last)
        last_y = center[1] + radius * math.sin(last)

        path.curveTo(
            first_x - coefficient * radius * math.sin(first),
            first_y + coefficient * radius * math.cos(first),
            last_x + coefficient * radius * math.sin(last),
            last_y - coefficient * radius * math.cos(last),
            last_x,
            last_y,
        )


def region_path(region, colour):
    """Construct the exact curved boundary of one interior Venn region."""
    angle, upper, lower = intersection_geometry()

    path = Path(
        fillColor=HexColor(colour),
        strokeColor=None,
    )
    path.moveTo(*upper)

    if region == 0:
        # A only: the long outside arc of A and the short left arc of B.
        append_arc(
            path, LEFT_CENTER, RADIUS,
            angle, 2 * math.pi - 2 * angle,
        )
        append_arc(
            path, RIGHT_CENTER, RADIUS,
            math.pi + angle, -2 * angle,
        )

    elif region == 1:
        # Intersection: the facing arcs of the two circles.
        append_arc(
            path, LEFT_CENTER, RADIUS,
            angle, -2 * angle,
        )
        append_arc(
            path, RIGHT_CENTER, RADIUS,
            math.pi + angle, -2 * angle,
        )

    elif region == 2:
        # B only: the long outside arc of B and the short right arc of A.
        append_arc(
            path, RIGHT_CENTER, RADIUS,
            math.pi - angle, -(2 * math.pi - 2 * angle),
        )
        append_arc(
            path, LEFT_CENTER, RADIUS,
            -angle, 2 * angle,
        )

    else:
        raise ValueError("Unknown interior Venn region")

    path.closePath()
    return path


# --- Public visual specification ----------------------------------------

def venn_asset(shaded=(), values=None, missing=()):
    """Create a JSON-compatible visual specification.

    shaded: indices of regions to colour, from 0 to 3.
    values: optional four integer counts, one per region.
    missing: indices whose count is hidden from the student.
    """
    shaded = list(shaded)
    missing = list(missing)

    require(
        len(set(shaded)) == len(shaded)
        and all(type(index) is int and 0 <= index <= 3
                for index in shaded),
        "Invalid shaded regions",
    )

    require(
        len(set(missing)) == len(missing)
        and all(type(index) is int and 0 <= index <= 3
                for index in missing),
        "Invalid missing regions",
    )

    if values is None:
        require(not missing, "Cannot hide values from an empty diagram")
    else:
        require(
            isinstance(values, (list, tuple))
            and len(values) == 4
            and all(type(value) is int and value >= 0
                    for value in values),
            "Venn counts must be four nonnegative integers",
        )
        values = list(values)

    return {
        "kind": "venn",
        "version": 1,
        "shaded": sorted(shaded),
        "values": values,
        "missing": sorted(missing),
    }


# --- Vector drawing ------------------------------------------------------

def render_venn(spec, width):
    """Render independent region fills and fixed-size readable labels."""
    require(
        set(spec) == {
            "kind", "version", "shaded", "values", "missing",
        },
        "Unexpected Venn specification",
    )

    require(
        spec["kind"] == "venn" and spec["version"] == 1,
        "Unsupported Venn specification",
    )

    # Validate the specification even if supplied by another generator.
    venn_asset(
        shaded=spec["shaded"],
        values=spec["values"],
        missing=spec["missing"],
    )

    require(width >= 220, "Venn drawing needs at least 220 points")

    scale = width / DESIGN_WIDTH
    height = DESIGN_HEIGHT * scale

    drawing = Drawing(width, height)

    background = HexColor(BACKGROUND)
    selected = HexColor(SELECTED)
    ink = HexColor(INK)

    def point(x, y):
        return x * scale, y * scale

    def add_text(text, x, y):
        x, y = point(x, y)
        shape, bounds = text_shape(str(text), x, y)

        require(
            bounds[0] >= 3
            and bounds[1] >= 3
            and bounds[2] <= width - 3
            and bounds[3] <= height - 3,
            "Venn label extends outside diagram",
        )

        drawing.add(shape)

    # Region 3 is the universal set outside both circles.
    drawing.add(Rect(
        15 * scale, 15 * scale,
        330 * scale, 230 * scale,
        fillColor=selected if 3 in spec["shaded"] else background,
        strokeColor=None,
    ))

    # Build all three curved regions in the original design space.
    # Scale the containing group, rather than assigning an unsupported
    # transform attribute to individual ReportLab Path objects.
    regions = Group()

    for region in range(3):
        regions.add(region_path(
            region,
            SELECTED if region in spec["shaded"] else BACKGROUND,
        ))

    regions.scale(scale, scale)
    drawing.add(regions)

    # Draw the visible circle boundaries over the filled regions.
    for center in (LEFT_CENTER, RIGHT_CENTER):
        x, y = point(*center)
        drawing.add(Circle(
            x, y, RADIUS * scale,
            fillColor=None,
            strokeColor=ink,
            strokeWidth=1.35,
        ))

    drawing.add(Rect(
        15 * scale, 15 * scale,
        330 * scale, 230 * scale,
        fillColor=None,
        strokeColor=ink,
        strokeWidth=1.1,
    ))

    for text, x, y in SET_LABELS:
        add_text(text, x, y)

    if spec["values"] is not None:
        for index, position in enumerate(REGION_POSITIONS):
            value = (
                "?" if index in spec["missing"]
                else str(spec["values"][index])
            )
            add_text(value, *position)

    return drawing