"""Two-stage probability trees with deliberate label-to-branch clearance.

All positions belong to the diagram layout, not the probability model.
Probability labels sit outside their branches. First-stage outcome labels
sit beyond their branch endpoints, above or below the next pair of lines.

The same layout supports student blanks and completed teacher diagrams.
"""
from fractions import Fraction

from .core import require
from .visuals import scene, text_shape


# --- Editable diagram geometry -------------------------------------------

WIDTH = 360
HEIGHT = 320

ROOT = (20, 160)
FIRST_RED = (112, 240)
FIRST_BLUE = (112, 80)

END_RED_RED = (250, 285)
END_RED_BLUE = (250, 195)
END_BLUE_RED = (250, 125)
END_BLUE_BLUE = (250, 35)

BRANCHES = (
    (ROOT, FIRST_RED),
    (ROOT, FIRST_BLUE),
    (FIRST_RED, END_RED_RED),
    (FIRST_RED, END_RED_BLUE),
    (FIRST_BLUE, END_BLUE_RED),
    (FIRST_BLUE, END_BLUE_BLUE),
)

# Probabilities are deliberately offset from the branch lines.
PROBABILITY_POSITIONS = (
    (55, 235),
    (55, 85),
    (180, 300),
    (180, 178),
    (180, 142),
    (180, 20),
)

# Place first-stage outcomes outside the fan of second-stage branches.
# Keep probability and outcome labels clear of every branch at 250 points.
OUTCOME_LABELS = (
    ("Red", (135, 275)),
    ("Blue", (135, 45)),
    ("Red", (288, 285)),
    ("Blue", (288, 195)),
    ("Red", (288, 125)),
    ("Blue", (288, 35)),
)


# --- Probability formatting ----------------------------------------------

def decimal_if_exact(value):
    """Return an exact terminating decimal, or None if it recurs."""
    value = Fraction(value)
    for places in range(1, 5):
        scale = 10 ** places
        if scale % value.denominator == 0:
            integer = value.numerator * scale // value.denominator
            whole, fractional = divmod(integer, scale)
            decimal = str(fractional).zfill(places).rstrip("0")
            return str(whole) + ("." + decimal if decimal else "")
    return None


def probability_text(value, use_decimal):
    value = Fraction(value)
    if use_decimal:
        decimal = decimal_if_exact(value)
        if decimal is not None:
            return decimal
    return "{}/{}".format(value.numerator, value.denominator)


def branch_probabilities(red, blue, replacement=False):
    """Return the six exact probabilities in diagram branch order."""
    require(
        type(red) is int and type(blue) is int
        and red >= 2 and blue >= 2,
        "Both counter colours need at least two counters",
    )
    total = red + blue
    remaining = total if replacement else total - 1
    removed_red = 0 if replacement else 1
    removed_blue = 0 if replacement else 1

    return (
        Fraction(red, total),
        Fraction(blue, total),
        Fraction(red - removed_red, remaining),
        Fraction(blue, remaining),
        Fraction(red, remaining),
        Fraction(blue - removed_blue, remaining),
    )


# --- Diagram construction ------------------------------------------------

def tree_scene(red=3, blue=2, replacement=False, student=False):
    """Create one complete tree or one with selected missing probabilities."""
    probabilities = branch_probabilities(red, blue, replacement)
    nodes = []

    for start, end in BRANCHES:
        nodes.append({
            "type": "line",
            "points": [list(start), list(end)],
        })

    for index, (position, probability) in enumerate(
        zip(PROBABILITY_POSITIONS, probabilities)
    ):
        missing = student and index in (1, 2, 5)
        text = "?" if missing else probability_text(
            probability, use_decimal=index % 2 == 1
        )
        nodes.append({
            "type": "label",
            "point": list(position),
            "text": text,
        })

    for text, position in OUTCOME_LABELS:
        nodes.append({
            "type": "label",
            "point": list(position),
            "text": text,
        })

    return scene(nodes, height=HEIGHT, caption="")


# --- Label-to-line geometry checks ---------------------------------------

def segment_crosses_box(start, end, box):
    """Check whether a segment enters an axis-aligned label rectangle."""
    left, bottom, right, top = box
    x, y = start
    dx = end[0] - x
    dy = end[1] - y
    lower, upper = 0.0, 1.0

    for direction, distance in (
        (-dx, x - left),
        (dx, right - x),
        (-dy, y - bottom),
        (dy, top - y),
    ):
        if abs(direction) < 1e-12:
            if distance < 0:
                return False
            continue

        ratio = distance / direction
        if direction < 0:
            lower = max(lower, ratio)
        else:
            upper = min(upper, ratio)

        if lower > upper:
            return False

    return True


def check_label_clearance(spec, rendered_width, padding=2):
    """Reject branch collisions and overlapping labels at the actual width.

    Text remains at its intended font size when geometry is scaled.
    Therefore checking the nominal 360-point layout alone is insufficient.
    """
    scale = rendered_width / spec["width"]
    lines = []
    boxes = []

    for node in spec["nodes"]:
        if node["type"] == "line":
            lines.append(tuple(
                (point[0] * scale, point[1] * scale)
                for point in node["points"]
            ))
            continue

        require(node["type"] == "label", "Unexpected diagram node")
        x, y = (coordinate * scale for coordinate in node["point"])
        _, bounds = text_shape(node, x, y)
        left, bottom, right, top = bounds
        padded = (
            left - padding, bottom - padding,
            right + padding, top + padding,
        )

        require(
            left >= 3 and bottom >= 2
            and right <= rendered_width - 3
            and top <= HEIGHT * scale - 2,
            "Label extends beyond the diagram",
        )

        for start, end in lines:
            require(
                not segment_crosses_box(start, end, padded),
                "Label intersects a tree branch: " + node["text"],
            )

        for other in boxes:
            overlap = (
                padded[0] < other[2]
                and padded[2] > other[0]
                and padded[1] < other[3]
                and padded[3] > other[1]
            )
            require(
                not overlap,
                "Probability-tree labels overlap: " + node["text"],
            )

        boxes.append(padded)

    return True