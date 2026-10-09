"""Scene building for IB geometry diagrams, on the shared figures engine.

figure() takes true coordinates (y up, matching the PDF canvas), places
them with figures.place, and adds outlines, lines, arcs, right-angle marks
and labels in canvas points. Arcs are sampled into the placement so they
are never clipped. require_drawable() rejects any scene that would render
with clipped or overlapping labels.
"""
import math

from .. import figures
from ..core import require


VERTEX_GAP = 12
ARC_SAMPLE_STEP = 15


def scene(nodes, height):
    return {"kind": "scene", "version": 1, "width": 360, "height": height,
            "caption": "Not drawn accurately", "nodes": nodes}


def _arc_samples(points, arcs):
    samples = {}
    for index, (centre, radius, start, sweep) in enumerate(arcs):
        cx, cy = points[centre]
        steps = max(2, int(abs(sweep) // ARC_SAMPLE_STEP) + 1)
        for k in range(steps + 1):
            angle = math.radians(start + sweep * k / steps)
            samples["_arc{}_{}".format(index, k)] = (cx + radius * math.cos(angle),
                                                     cy + radius * math.sin(angle))
    return samples


def figure(points, polygons=(), lines=(), dashed=(), names=None, sides=(), angles=(),
           right_angles=(), arcs=(), labels=()):
    """A scene from true coordinates.

    points: {role: (x, y)}; names: {role: text} for outward vertex labels;
    sides: (first, second, text); angles: (vertex, first, second, text);
    right_angles: (vertex, first, second); arcs: (centre, radius, start, sweep)
    in true units and degrees; labels: (role, text) centred on a point.
    """
    points = {role: (float(x), float(y)) for role, (x, y) in points.items()}
    everything = dict(points)
    everything.update(_arc_samples(points, arcs))
    placed, height = figures.place(everything, [0, False])
    scale = None
    roles = list(points)
    for first in roles:
        for second in roles:
            distance = math.dist(points[first], points[second])
            if distance > 1e-9:
                scale = math.dist(placed[first], placed[second]) / distance
                break
        if scale:
            break
    require(scale is not None, "A figure needs two distinct points")
    named = [placed[role] for role in (names or points)]
    centre = (sum(p[0] for p in named) / len(named), sum(p[1] for p in named) / len(named))

    nodes = [{"type": "polygon", "points": [placed[role] for role in polygon]} for polygon in polygons]
    nodes += [{"type": "line", "points": [placed[a], placed[b]]} for a, b in lines]
    nodes += [{"type": "line", "points": [placed[a], placed[b]], "dashed": True} for a, b in dashed]
    for role, radius, start, sweep in arcs:
        nodes.append({"type": "arc", "center": placed[role], "radius": round(radius * scale, 2),
                      "start": round(float(start), 2), "sweep": round(float(sweep), 2)})
    for vertex, first, second in right_angles:
        nodes.append({"type": "right_angle", "vertex": placed[vertex],
                      "first": placed[first], "second": placed[second]})
    for role, text in (names or {}).items():
        x, y = placed[role]
        away = (x - centre[0], y - centre[1])
        direction = figures.unit(away) if math.hypot(*away) > 1e-6 else (0.0, 1.0)
        nodes.append({"type": "label", "text": text, "point": figures.rounded(
            (x + direction[0] * VERTEX_GAP, y + direction[1] * VERTEX_GAP))})
    for first, second, text in sides:
        nodes.append({"type": "label", "text": text,
                      "point": figures.side_label(placed[first], placed[second], centre, len(text))})
    for vertex, first, second, text in angles:
        nodes.append({"type": "label", "text": text,
                      "point": figures.angle_label(placed[vertex], placed[first], placed[second], len(text))})
    for role, text in labels:
        nodes.append({"type": "label", "text": text, "point": placed[role]})
    return scene(nodes, height)


def require_drawable(parts):
    for visual in parts.get("question_visuals", ()):
        require(figures.renderable(visual), "Diagram does not render cleanly")