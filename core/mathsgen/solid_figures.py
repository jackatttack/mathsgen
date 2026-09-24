"""Prisms and cylinders drawn at true proportions, labelled in the final frame.

prism_scene(section, depth, ...) draws an oblique prism: the cross-section is
the front face at its true shape, and the back face is offset at 30 degrees
by half the depth (up-right, or up-left when mirrored). A back vertex that
falls inside the front face is hidden, so its edges are dashed. All labels
are placed after projection with figures.side_label, so they respect the
edge directions actually drawn.

cylinder_scene(radius, height, ...) draws an upright cylinder at its true
radius-to-height ratio with elliptical ends.
"""
import math

from . import figures


# ------------------------------------------------------------ editable knobs

DEPTH_ANGLE = 30
DEPTH_SCALE = 0.5
MAX_WIDTH = figures.MAX_FIGURE_WIDTH
MAX_HEIGHT = 180
ELLIPSE_RATIO = 0.3
ELLIPSE_POINTS = 48


# ------------------------------------------------------------ helpers

def inside(point, polygon):
    """Strictly inside a simple polygon (ray casting)."""
    x, y = point
    result = False
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
        if (y1 > y) != (y2 > y):
            crossing = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if crossing > x + 1e-9:
                result = not result
    return result


def centroid(points):
    return (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))


def fit(points):
    """A function mapping raw points into the canvas, plus the scene height."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    width, height = max(xs) - min(xs), max(ys) - min(ys)
    scale = min(MAX_WIDTH / width, MAX_HEIGHT / height)
    left = (figures.CANVAS_WIDTH - width * scale) / 2

    def place(p):
        return (left + (p[0] - min(xs)) * scale, figures.MARGIN + (p[1] - min(ys)) * scale)
    return place, round(height * scale + 2 * figures.MARGIN, figures.DIGITS)


def line(first, second, dashed=False):
    node = {"type": "line", "points": [figures.rounded(first), figures.rounded(second)]}
    if dashed:
        node["dashed"] = True
    return node


LABEL_GAP = 10
# Text keeps its size while the drawing shrinks, so offsets are sized for the
# narrowest width checked (238 pt, the PDF working row): 360 / 238 = 1.51.
NARROW_TEXT_FACTOR = 360 / 238
HALF_CHARACTER = 3.1 * NARROW_TEXT_FACTOR
HALF_LINE = 7 * NARROW_TEXT_FACTOR


def side_text(first, second, away_from, text):
    """A label beside an edge, clear of it for any edge direction.

    figures.side_label allows only for text width, which is enough for
    horizontal and vertical edges but not for slanted ones such as a
    hypotenuse; this offset allows for both the width and the height of
    the text box. (figures.side_label is left unchanged because existing
    generators rebuild their saved diagrams through it.)
    """
    middle = ((first[0] + second[0]) / 2, (first[1] + second[1]) / 2)
    direction = figures.unit(figures.minus(second, first))
    normal = (-direction[1], direction[0])
    towards = figures.minus(away_from, middle)
    if normal[0] * towards[0] + normal[1] * towards[1] > 0:
        normal = (-normal[0], -normal[1])
    clearance = (LABEL_GAP + abs(normal[0]) * HALF_CHARACTER * len(text)
                 + abs(normal[1]) * HALF_LINE)
    return {"type": "label", "text": text, "point": figures.rounded(
        (middle[0] + normal[0] * clearance, middle[1] + normal[1] * clearance))}


def scene(nodes, height):
    return {"kind": "scene", "version": 1, "width": 360, "height": height,
            "caption": "Not drawn accurately", "nodes": nodes}


# ------------------------------------------------------------ prisms

def prism_scene(section, depth, edge_labels, depth_label=None, mirror=False,
                right_angles=(), height_line=None):
    """section: [(x, y)] in cm, y up, in boundary order.

    edge_labels: {i: text} for the front edge from vertex i to vertex i + 1;
    a value (text, True) puts the label just inside the face instead.
    right_angles: front vertex indices to mark.
    height_line: (top_point, foot_point, neighbour_index, text) in section
    coordinates, drawn dashed with a right angle at the foot.
    """
    turn = math.radians(DEPTH_ANGLE)
    dx = depth * DEPTH_SCALE * math.cos(turn) * (-1 if mirror else 1)
    dy = depth * DEPTH_SCALE * math.sin(turn)
    front_raw = [(x, -y) for x, y in section]
    back_raw = [(x + dx, y - dy) for x, y in front_raw]
    extra_raw = []
    if height_line:
        extra_raw = [(height_line[0][0], -height_line[0][1]),
                     (height_line[1][0], -height_line[1][1])]
    place, height = fit(front_raw + back_raw)
    front = [place(p) for p in front_raw]
    back = [place(p) for p in back_raw]
    hidden = [inside(b, front_raw) for b in back_raw]
    n = len(section)
    nodes = []
    for i in range(n):
        j = (i + 1) % n
        nodes.append(line(back[i], back[j], dashed=hidden[i] or hidden[j]))
    for i in range(n):
        nodes.append(line(front[i], back[i], dashed=hidden[i]))
    for i in range(n):
        nodes.append(line(front[i], front[(i + 1) % n]))
    middle = centroid(front)
    for i in right_angles:
        nodes.append({"type": "right_angle", "vertex": figures.rounded(front[i]),
                      "first": figures.rounded(front[i - 1]),
                      "second": figures.rounded(front[(i + 1) % n])})
    for i, value in sorted(edge_labels.items()):
        text, inward = value if isinstance(value, tuple) else (value, False)
        first, second = front[i], front[(i + 1) % n]
        away = middle
        if inward:
            # Reflect the centroid across the edge so the label falls inside.
            mid = ((first[0] + second[0]) / 2, (first[1] + second[1]) / 2)
            away = (2 * mid[0] - middle[0], 2 * mid[1] - middle[1])
        nodes.append(side_text(first, second, away, text))
    if height_line:
        top, foot = place(extra_raw[0]), place(extra_raw[1])
        neighbour = front[height_line[2]]
        nodes.append(line(top, foot, dashed=True))
        nodes.append({"type": "right_angle", "vertex": figures.rounded(foot),
                      "first": figures.rounded(top), "second": figures.rounded(neighbour)})
        nodes.append(side_text(top, foot, neighbour, height_line[3]))
    if depth_label:
        visible = [i for i in range(n) if not hidden[i]]
        key = (lambda i: (-front[i][0], front[i][1])) if not mirror else (
            lambda i: (front[i][0], front[i][1]))
        corner = sorted(visible, key=key)[0]
        nodes.append(side_text(front[corner], back[corner], middle, depth_label))
    return scene(nodes, height)


# ------------------------------------------------------------ cylinders

def ellipse(centre, rx, ry):
    return [(centre[0] + rx * math.cos(2 * math.pi * i / ELLIPSE_POINTS),
             centre[1] + ry * math.sin(2 * math.pi * i / ELLIPSE_POINTS))
            for i in range(ELLIPSE_POINTS)]


def cylinder_scene(radius, height, radius_label=None, height_label=None, diameter=False):
    ry = radius * ELLIPSE_RATIO
    raw = [(-radius, -ry), (radius, height + ry)]
    place, scene_height = fit(raw)
    top_centre, bottom_centre = place((0, 0)), place((0, height))
    edge = place((radius, 0))
    rx = edge[0] - top_centre[0]
    ry_canvas = place((0, ry))[1] - top_centre[1]
    nodes = [
        {"type": "polygon", "points": [figures.rounded(p) for p in ellipse(top_centre, rx, ry_canvas)]},
        {"type": "polygon", "points": [figures.rounded(p) for p in ellipse(bottom_centre, rx, ry_canvas)]},
        line((top_centre[0] - rx, top_centre[1]), (bottom_centre[0] - rx, bottom_centre[1])),
        line((top_centre[0] + rx, top_centre[1]), (bottom_centre[0] + rx, bottom_centre[1])),
        {"type": "circle", "center": figures.rounded(top_centre), "radius": 1.6, "shade": True},
    ]
    above = (top_centre[0], top_centre[1] + 10)
    if radius_label:
        start = (top_centre[0] - rx, top_centre[1]) if diameter else top_centre
        end = (top_centre[0] + rx, top_centre[1])
        nodes.append(line(start, end))
        nodes.append(side_text(start, end, above, radius_label))
    if height_label:
        first = (top_centre[0] + rx, top_centre[1])
        second = (bottom_centre[0] + rx, bottom_centre[1])
        nodes.append(side_text(first, second, bottom_centre, height_label))
    return scene(nodes, scene_height)


# ------------------------------------------------------------ curved solids and pyramids
#
# These drawers build raw points with y upwards, the renderer's direction,
# and fit them to the canvas; unlike prism_scene they never negate y.

def rim(centre, rx, ry, front):
    """Half an ellipse as segments: the front (lower) half solid, the back half dashed."""
    count = ELLIPSE_POINTS // 2
    start = math.pi if front else 0.0
    points = [(centre[0] + rx * math.cos(start + math.pi * i / count),
               centre[1] + ry * math.sin(start + math.pi * i / count))
              for i in range(count + 1)]
    return [line(points[i], points[i + 1], dashed=not front) for i in range(count)]


def dot(point):
    return {"type": "circle", "center": figures.rounded(point), "radius": 1.6, "shade": True}


def beside(point, text, side):
    """A label to the right (side 1) or left (side -1) of a point, clear at every width."""
    offset = LABEL_GAP + HALF_CHARACTER * len(text)
    return {"type": "label", "text": text,
            "point": figures.rounded((point[0] + side * offset, point[1]))}


def dimension(x, low, high, text, side):
    """An exam-style vertical dimension line with arrows at both ends, labelled beside it."""
    middle = (x, (low + high) / 2)
    return [
        {"type": "line", "points": [figures.rounded(middle), figures.rounded((x, high))],
         "arrow": True},
        {"type": "line", "points": [figures.rounded(middle), figures.rounded((x, low))],
         "arrow": True},
        beside(middle, text, side),
    ]


# Canvas gap between a solid and its dimension line.
DIMENSION_GAP = 16
# Extra raw width, as a multiple of the radius, left for an outside label.
LABEL_REACH = 1.8


def cone_scene(radius, height, radius_label=None, height_label=None, slant_label=None):
    """Upright cone at true proportions; the back half of the base rim is dashed."""
    ry = radius * ELLIPSE_RATIO
    left_reach = -radius * (LABEL_REACH if height_label else 1)
    right_reach = radius * (LABEL_REACH if radius_label else 1)
    place, scene_height = fit([(left_reach, -ry), (right_reach, height)])
    centre, apex = place((0, 0)), place((0, height))
    right, left = place((radius, 0)), place((-radius, 0))
    rx, ry_canvas = right[0] - centre[0], place((0, ry))[1] - centre[1]
    nodes = rim(centre, rx, ry_canvas, True) + rim(centre, rx, ry_canvas, False)
    nodes += [line(apex, left), line(apex, right), dot(centre)]
    if radius_label:
        nodes.append(line(centre, right))
        nodes.append(beside(right, radius_label, 1))
    if height_label:
        nodes.append(line(apex, centre, dashed=True))
        nodes.append({"type": "right_angle", "vertex": figures.rounded(centre),
                      "first": figures.rounded(apex), "second": figures.rounded(right)})
        nodes += dimension(left[0] - DIMENSION_GAP, centre[1], apex[1], height_label, -1)
    if slant_label:
        nodes.append(side_text(apex, right, centre, slant_label))
    return scene(nodes, scene_height)


def sphere_scene(radius, radius_label=None):
    """Sphere outline with a dashed back equator and a labelled radius."""
    reach = radius * (LABEL_REACH if radius_label else 1)
    place, scene_height = fit([(-radius, -radius), (reach, radius)])
    centre = place((0, 0))
    right = place((radius, 0))
    outline = right[0] - centre[0]
    nodes = [{"type": "circle", "center": figures.rounded(centre), "radius": round(outline, 2)}]
    nodes += rim(centre, outline, outline * ELLIPSE_RATIO, True)
    nodes += rim(centre, outline, outline * ELLIPSE_RATIO, False)
    nodes.append(dot(centre))
    if radius_label:
        nodes.append(line(centre, right))
        nodes.append(beside(right, radius_label, 1))
    return scene(nodes, scene_height)


def hemisphere_scene(radius, radius_label=None):
    """Solid hemisphere on its flat face; the dome hides the back of the rim."""
    reach = radius * (LABEL_REACH if radius_label else 1)
    place, scene_height = fit([(-radius, -radius * ELLIPSE_RATIO), (reach, radius)])
    centre = place((0, 0))
    right = place((radius, 0))
    outline = right[0] - centre[0]
    nodes = [{"type": "arc", "center": figures.rounded(centre), "radius": round(outline, 2),
              "start": 0, "sweep": 180}]
    nodes += rim(centre, outline, outline * ELLIPSE_RATIO, True)
    nodes += rim(centre, outline, outline * ELLIPSE_RATIO, False)
    nodes.append(dot(centre))
    if radius_label:
        nodes.append(line(centre, right))
        nodes.append(beside(right, radius_label, 1))
    return scene(nodes, scene_height)


def pyramid_scene(side, height, side_label=None, height_label=None):
    """Square-based pyramid; the base is drawn obliquely and the back corner is hidden."""
    turn = math.radians(DEPTH_ANGLE)
    dx = side * DEPTH_SCALE * math.cos(turn)
    dy = side * DEPTH_SCALE * math.sin(turn)
    raw = {"A": (0, 0), "B": (side, 0), "C": (side + dx, dy), "D": (dx, dy)}
    base_centre = ((side + dx) / 2, dy / 2)
    raw["P"] = (base_centre[0], base_centre[1] + height)
    raw["O"] = base_centre
    room = [(side + dx + side * 0.8, 0)] if height_label else []
    place, scene_height = fit(list(raw.values()) + room)
    p = {name: place(point) for name, point in raw.items()}
    nodes = [
        line(p["A"], p["B"]), line(p["B"], p["C"]),
        line(p["C"], p["D"], dashed=True), line(p["D"], p["A"], dashed=True),
        line(p["P"], p["A"]), line(p["P"], p["B"]), line(p["P"], p["C"]),
        line(p["P"], p["D"], dashed=True),
    ]
    if side_label:
        nodes.append(side_text(p["A"], p["B"], p["P"], side_label))
    if height_label:
        nodes.append(line(p["P"], p["O"], dashed=True))
        edge = max(p["B"][0], p["C"][0]) + DIMENSION_GAP
        nodes += dimension(edge, p["O"][1], p["P"][1], height_label, 1)
    return scene(nodes, scene_height)


def frustum_scene(radius, height, scale, radius_label=None):
    """Frustum of a cone cut at (1 - scale) of its height; the removed cone is dashed."""
    ry = radius * ELLIPSE_RATIO
    reach = radius * (LABEL_REACH if radius_label else 1)
    place, scene_height = fit([(-radius, -ry), (reach, height)])
    centre, apex = place((0, 0)), place((0, height))
    top_centre = place((0, height * (1 - scale)))
    right = place((radius, 0))
    rx, ry_canvas = right[0] - centre[0], place((0, ry))[1] - centre[1]
    top_rx, top_ry = rx * scale, ry_canvas * scale
    nodes = rim(centre, rx, ry_canvas, True) + rim(centre, rx, ry_canvas, False)
    nodes.append({"type": "polygon", "points": [figures.rounded(point)
                                                for point in ellipse(top_centre, top_rx, top_ry)]})
    for sign in (-1, 1):
        bottom_edge = (centre[0] + sign * rx, centre[1])
        top_edge = (top_centre[0] + sign * top_rx, top_centre[1])
        nodes.append(line(bottom_edge, top_edge))
        nodes.append(line(top_edge, apex, dashed=True))
    nodes.append(dot(centre))
    if radius_label:
        nodes.append(line(centre, right))
        nodes.append(beside(right, radius_label, 1))
    return scene(nodes, scene_height)


def labels_ok(spec):
    """Clearance and rendering at every checked width (shared circle checks)."""
    from . import circle_figures
    return circle_figures.labels_clear(spec) and circle_figures.renders_everywhere(spec)