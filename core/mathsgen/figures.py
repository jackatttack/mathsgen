"""Varied geometry diagrams: real shapes, seeded orientation, measured labels.

Two entry points:
- place(points, orientation): rotate/reflect named figure points, then scale
  them uniformly into the 360-wide design canvas. Build nodes afterwards,
  so label offsets are in canvas points, not figure units.
- orient_scene(spec, orientation): rotate/reflect an existing scene's nodes
  (points, labels, circles, arcs, markers) and re-fit it, for generators
  whose layouts are already authored.

choose_orientation() tries orientations in a seeded order and keeps the first
whose scene actually renders at both 360 and 250 points, so a rotation can
never put clipped or overlapping labels on a worksheet. Validation never
renders: the orientation is stored in the parameters and the scene is rebuilt
exactly. Rotations and reflections preserve every angle, length ratio and
right-angle marker, so the mathematics is unchanged.
"""
import math

from .core import require


# ------------------------------------------------------------ editable knobs

ORIENTATIONS = tuple(
    (rotation, mirror) for rotation in range(0, 360, 30) for mirror in (False, True)
)
CANVAS_WIDTH = 360
MARGIN = 34
MAX_FIGURE_WIDTH = CANVAS_WIDTH - 2 * MARGIN
MAX_FIGURE_HEIGHT = 190
RENDER_WIDTHS = (360, 250)
DIGITS = 2


# ------------------------------------------------------------ vector helpers

def unit(vector):
    length = math.hypot(*vector)
    require(length > 1e-9, "Zero-length direction")
    return (vector[0] / length, vector[1] / length)


def minus(p, q):
    return (p[0] - q[0], p[1] - q[1])


def rounded(point):
    return [round(point[0], DIGITS), round(point[1], DIGITS)]


def transform(point, orientation):
    rotation, mirror = orientation
    x, y = point
    if mirror:
        x = -x
    angle = math.radians(rotation)
    return (x * math.cos(angle) - y * math.sin(angle),
            x * math.sin(angle) + y * math.cos(angle))


def valid_orientation(value):
    return (isinstance(value, list) and len(value) == 2
            and (value[0], value[1]) in ORIENTATIONS and type(value[1]) is bool)


# ------------------------------------------------------------ placing points

def place(points, orientation, max_height=MAX_FIGURE_HEIGHT):
    """Orient named points and fit them into the canvas. Returns (points, height)."""
    moved = {name: transform(p, orientation) for name, p in points.items()}
    xs = [p[0] for p in moved.values()]
    ys = [p[1] for p in moved.values()]
    width, height = max(xs) - min(xs), max(ys) - min(ys)
    scale = min(MAX_FIGURE_WIDTH / width if width else math.inf,
                max_height / height if height else math.inf)
    require(math.isfinite(scale), "Figure has no extent")
    left = (CANVAS_WIDTH - width * scale) / 2
    placed = {
        name: rounded((left + (x - min(xs)) * scale, MARGIN + (y - min(ys)) * scale))
        for name, (x, y) in moved.items()
    }
    return placed, round(height * scale + 2 * MARGIN, DIGITS)


def angle_label(vertex, first, second, text_length):
    """A label point on the bisector of angle first-vertex-second.

    Sharp angles and long labels push the label further out, so the text
    clears both arms of the angle.
    """
    u = unit(minus(first, vertex))
    v = unit(minus(second, vertex))
    bisector = unit((u[0] + v[0], u[1] + v[1]))
    half = math.acos(max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1]))) / 2
    distance = (10 + 2.6 * text_length) / max(math.sin(half), 0.2)
    distance = min(95.0, max(24.0, distance))
    return rounded((vertex[0] + bisector[0] * distance, vertex[1] + bisector[1] * distance))


def side_label(first, second, inside, text_length, gap=14):
    """A label point beside the midpoint of a side, on the side away from inside."""
    middle = ((first[0] + second[0]) / 2, (first[1] + second[1]) / 2)
    direction = unit(minus(second, first))
    normal = (-direction[1], direction[0])
    towards = minus(inside, middle)
    if normal[0] * towards[0] + normal[1] * towards[1] > 0:
        normal = (-normal[0], normal[1] * -1)
    clearance = gap + abs(normal[0]) * 3.1 * text_length
    return rounded((middle[0] + normal[0] * clearance, middle[1] + normal[1] * clearance))


# ------------------------------------------------------------ whole scenes

POINT_KEYS = ("point", "vertex", "first", "second", "center")


def orient_scene(spec, orientation, max_height=260):
    """Rotate/reflect every node of an authored scene, then re-fit it."""
    rotation, mirror = orientation
    coordinates = []

    def collect(value):
        coordinates.append(transform(value, orientation))
        return coordinates[-1]

    moved_nodes = []
    for node in spec["nodes"]:
        moved = dict(node)
        if "points" in node:
            moved["points"] = [collect(p) for p in node["points"]]
        for key in POINT_KEYS:
            if key in node:
                moved[key] = collect(node[key])
        if node["type"] == "arc":
            start = 180 - node["start"] if mirror else node["start"]
            moved["start"] = (start + rotation) % 360
            moved["sweep"] = -node["sweep"] if mirror else node["sweep"]
        moved_nodes.append(moved)

    extents = list(coordinates)
    for node in moved_nodes:
        if node["type"] in ("circle", "arc"):
            cx, cy = node["center"]
            r = node["radius"]
            extents += [(cx - r, cy - r), (cx + r, cy + r)]
    xs = [p[0] for p in extents]
    ys = [p[1] for p in extents]
    width, height = max(xs) - min(xs), max(ys) - min(ys)
    scale = min(1.0, MAX_FIGURE_WIDTH / width if width else 1.0,
                max_height / height if height else 1.0)
    left = (CANVAS_WIDTH - width * scale) / 2

    def fit(p):
        return rounded((left + (p[0] - min(xs)) * scale, MARGIN + (p[1] - min(ys)) * scale))

    for node in moved_nodes:
        if "points" in node:
            node["points"] = [fit(p) for p in node["points"]]
        for key in POINT_KEYS:
            if key in node:
                node[key] = fit(node[key])
        if "radius" in node:
            node["radius"] = round(node["radius"] * scale, DIGITS)
        if node["type"] == "arc":
            node["start"] = round(node["start"], DIGITS)
    oriented = dict(spec)
    oriented["nodes"] = moved_nodes
    oriented["height"] = round(height * scale + 2 * MARGIN, DIGITS)
    return oriented


# ------------------------------------------------------------ choosing safely

def renderable(spec):
    """True when the scene renders without clipped or overlapping labels."""
    from .visuals import drawing_for
    try:
        for width in RENDER_WIDTHS:
            drawing_for(spec, width)
    except ValueError:
        return False
    return True


def choose_orientation(rng, make_spec):
    """Seeded choice of the first orientation whose scene renders cleanly."""
    candidates = list(ORIENTATIONS)
    rng.shuffle(candidates)
    candidates.remove((0, False))
    candidates.append((0, False))
    for orientation in candidates:
        if renderable(make_spec(list(orientation))):
            return list(orientation)
    raise ValueError("No orientation renders this figure cleanly")