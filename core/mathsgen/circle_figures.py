"""Circle-theorem diagrams from true positions: points, angle marks, safe orientation.

Author scenes in canvas points around CENTRE, then pass them through
figures.orient_scene(). choose_orientation() here is stricter than the one in
figures: besides rendering at both widths, every label must stay clear of every
straight line, because circle diagrams put many chords through a small area.
"""
import math

from . import figures


# ------------------------------------------------------------ editable knobs

CENTRE = (180.0, 150.0)
RADIUS = 100.0
VERTEX_GAP = 16
CENTRE_GAP = 15
ARC_RADIUS = 18
LABEL_CLEARANCE = 2
# pdf.scene_working_row draws a scene beside working space at 238 pt, which is
# narrower than figures.RENDER_WIDTHS, so circle diagrams are checked there too.
CHECK_WIDTHS = figures.RENDER_WIDTHS + (238,)


# ------------------------------------------------------------ positions

def on_circle(degrees):
    """Point on the circle; degrees use scene coordinates (y increases downward)."""
    angle = math.radians(float(degrees))
    return (CENTRE[0] + RADIUS * math.cos(angle), CENTRE[1] + RADIUS * math.sin(angle))


def direction(origin, target):
    return math.degrees(math.atan2(target[1] - origin[1], target[0] - origin[0])) % 360


def circle_nodes():
    return [
        {"type": "circle", "center": figures.rounded(CENTRE), "radius": RADIUS},
        {"type": "circle", "center": figures.rounded(CENTRE), "radius": 1.6, "shade": True},
    ]


def line(first, second):
    return {"type": "line", "points": [figures.rounded(first), figures.rounded(second)]}


def vertex_label(point, text, away_from=CENTRE, gap=VERTEX_GAP):
    """A letter just beyond point, on the side away from away_from."""
    outward = figures.unit(figures.minus(point, away_from))
    return {
        "type": "label",
        "point": figures.rounded((point[0] + outward[0] * gap, point[1] + outward[1] * gap)),
        "text": text,
    }


def label_in_angle(vertex, first, second, text, minimum=14.0, allowance=16.0):
    """A plain letter on the bisector of angle first-vertex-second, clear of both arms."""
    u = figures.unit(figures.minus(first, vertex))
    v = figures.unit(figures.minus(second, vertex))
    bisector = figures.unit((u[0] + v[0], u[1] + v[1]))
    half = math.acos(max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1]))) / 2
    distance = max(minimum, allowance / max(math.sin(half), 0.2))
    return {
        "type": "label",
        "point": figures.rounded((vertex[0] + bisector[0] * distance,
                                  vertex[1] + bisector[1] * distance)),
        "text": text,
    }


def angle_mark(vertex, first, second, tex, text_length, arc_radius=ARC_RADIUS):
    """Arc and label for the angle first-vertex-second (always the one under 180)."""
    start = direction(vertex, first)
    sweep = (direction(vertex, second) - start + 180) % 360 - 180
    half = math.radians(abs(sweep) / 2)
    middle = math.radians(start + sweep / 2)
    # Short labels still need room at the 250 pt width, where text shrinks
    # less than the geometry; hence the floor of 18 before dividing.
    distance = max(9 + 3.0 * text_length, 18.0) / max(math.sin(half), 0.2)
    distance = min(90.0, max(arc_radius + 12.0, distance))
    label = (vertex[0] + distance * math.cos(middle), vertex[1] + distance * math.sin(middle))
    return [
        {"type": "arc", "center": figures.rounded(vertex), "radius": arc_radius,
         "start": round(start, figures.DIGITS), "sweep": round(sweep, figures.DIGITS)},
        {"type": "label", "point": figures.rounded(label), "tex": tex},
    ]


# ------------------------------------------------------------ safety

def renders_everywhere(spec):
    """True when the scene renders without overlap or clipping at every check width."""
    from .visuals import drawing_for
    try:
        for width in CHECK_WIDTHS:
            drawing_for(spec, width)
    except ValueError:
        return False
    return True


def labels_clear(scene, widths=CHECK_WIDTHS, clearance=LABEL_CLEARANCE):
    """True when no label box comes within clearance of a straight line."""
    from .visuals import text_shape
    from .plots import clip_segment
    for width in widths:
        scale = width / scene["width"]
        edges = [
            [[value * scale for value in point] for point in node["points"]]
            for node in scene["nodes"] if node["type"] == "line"
        ]
        for node in scene["nodes"]:
            if node["type"] != "label":
                continue
            x, y = [value * scale for value in node["point"]]
            _, box = text_shape(node, x, y)
            for first, second in edges:
                if clip_segment(
                    first, second,
                    [box[0] - clearance, box[2] + clearance],
                    [box[1] - clearance, box[3] + clearance],
                ) is not None:
                    return False
    return True


def choose_orientation(rng, make_spec):
    """Seeded first orientation whose scene renders and keeps labels off lines."""
    candidates = list(figures.ORIENTATIONS)
    rng.shuffle(candidates)
    candidates.remove((0, False))
    candidates.append((0, False))
    for orientation in candidates:
        spec = make_spec(list(orientation))
        if labels_clear(spec) and renders_everywhere(spec):
            return list(orientation)
    raise ValueError("No orientation keeps every circle label clear")