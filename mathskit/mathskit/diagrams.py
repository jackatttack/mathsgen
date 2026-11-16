"""Diagrams for lessons as inline SVG, drawn with currentColor so they suit
light and dark themes. Pure Python.

    diagrams.right_triangle(4, 3, '4', '3', 'x')                  # Pythagoras
    diagrams.right_triangle(4, 3, '', 'x', '12', angle=('B', '35\u00b0'))

The label equal to unknown is drawn bold in the accent colour.
"""
import math
from html import escape

ACCENT = '#f0883e'
FONT = 'font-family="-apple-system, sans-serif"'


def label(x, y, text, anchor='middle', unknown=False, size=16):
    colour = ACCENT if unknown else 'currentColor'
    weight = ' font-weight="700"' if unknown else ''
    return ('<text x="%.1f" y="%.1f" text-anchor="%s" fill="%s" stroke="none" '
            'font-size="%d"%s>%s</text>' % (x, y, anchor, colour, size, weight, escape(text)))


PALETTE = ('#58a6ff', '#f0883e', '#3fb950', '#bc8cff')


# --- Angles -------------------------------------------------------------------
# Directions are degrees anticlockwise from east, as in maths; SVG's y runs
# down, so _toward flips it.

def _open(width, height):
    return ('<svg viewBox="0 0 %d %d" width="%d" height="%d" xmlns="http://www.w3.org/2000/svg" '
            'fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
            'stroke-linejoin="round" %s>' % (width, height, width, height, FONT))


def _toward(px, py, angle, distance):
    radians = math.radians(angle)
    return px + distance * math.cos(radians), py - distance * math.sin(radians)


def _direction(p, q):
    return math.degrees(math.atan2(-(q[1] - p[1]), q[0] - p[0])) % 360


def _line(p, q, extra=''):
    return '<path d="M%.1f %.1f L%.1f %.1f"%s/>' % (p[0], p[1], q[0], q[1], extra)


def arc(px, py, start, end, text, unknown=False, radius=28, gap=18):
    """An angle at (px, py) turning anticlockwise from direction start to end,
    with its label just outside the arc."""
    size = (end - start) % 360
    sx, sy = _toward(px, py, start, radius)
    ex, ey = _toward(px, py, end, radius)
    colour = ' stroke="%s"' % ACCENT if unknown else ''
    out = ('<path d="M%.1f %.1f A%d %d 0 %d 0 %.1f %.1f" stroke-width="1.6"%s/>'
           % (sx, sy, radius, radius, 1 if size > 180 else 0, ex, ey, colour))
    if text:
        if size < 35:
            gap += 12
        tx, ty = _toward(px, py, start + size / 2, radius + gap)
        out += label(tx, ty + 5, text, unknown=unknown, size=14)
    return out


def corner_arc(vertex, first, second, text, unknown=False, radius=26, gap=18):
    """The angle inside a corner: the smaller turn between its two neighbours."""
    d1, d2 = _direction(vertex, first), _direction(vertex, second)
    if (d2 - d1) % 360 > 180:
        d1, d2 = d2, d1
    return arc(vertex[0], vertex[1], d1, d2, text, unknown, radius, gap)


def tick(p, q):
    """A small equal-sides mark across the middle of p-q."""
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    direction = _direction(p, q) + 90
    a = _toward(mx, my, direction, 6)
    b = _toward(mx, my, direction + 180, 6)
    return _line(a, b, ' stroke-width="2"')


def angles_at_point(sizes, texts, unknown='x', line=False):
    """Angles side by side at one point: on a straight line (line=True,
    sizes add to 180) or a full turn (sizes add to 360). To scale."""
    if line:
        px, py, height, start, length = 160.0, 140.0, 165, 0.0, 115
    else:
        px, py, height, start, length = 160.0, 100.0, 200, 15.0, 90
    out = [_open(320, height)]
    if line:
        out.append('<path d="M25 %.1f H295"/>' % py)
    edges = [start]
    for size in sizes:
        edges.append(edges[-1] + size)
    for angle in (edges[1:-1] if line else edges[:-1]):
        out.append(_line((px, py), _toward(px, py, angle, length)))
    for index, (size, text) in enumerate(zip(sizes, texts)):
        out.append(arc(px, py, edges[index], edges[index] + size, text, text == unknown,
                       radius=28 + 10 * (index % 2)))
    out.append('<circle cx="%.1f" cy="%.1f" r="2.5" fill="currentColor" stroke="none"/>' % (px, py))
    out.append('</svg>')
    return ''.join(out)


def triangle_angles(a, b, texts, unknown='x', ticks=False):
    """A triangle with angle a bottom left, b bottom right and 180 - a - b at
    the top, to scale. texts: (bottom left, bottom right, top). ticks marks
    the two sides meeting at the top as equal (isosceles)."""
    c = 180 - a - b
    side = math.sin(math.radians(b)) / math.sin(math.radians(c))
    top = (side * math.cos(math.radians(a)), side * math.sin(math.radians(a)))
    xs = (0.0, 1.0, top[0])
    width, height = max(xs) - min(xs), top[1]
    scale = min(250.0 / width, 140.0 / height)
    middle = (min(xs) + max(xs)) / 2

    def place(x, y):
        return 160 + (x - middle) * scale, 178 - y * scale

    p1, p2, p3 = place(0, 0), place(1, 0), place(*top)
    out = [_open(320, 200),
           '<path d="M%.1f %.1f L%.1f %.1f L%.1f %.1f Z"/>' % (p1 + p2 + p3),
           corner_arc(p1, p2, p3, texts[0], texts[0] == unknown),
           corner_arc(p2, p3, p1, texts[1], texts[1] == unknown),
           corner_arc(p3, p1, p2, texts[2], texts[2] == unknown)]
    if ticks:
        out += [tick(p1, p3), tick(p2, p3)]
    out.append('</svg>')
    return ''.join(out)


def quadrilateral(texts, unknown='x'):
    """A fixed four-sided shape with an angle label at each corner (bottom
    left, bottom right, top right, top left). Not to scale, and says so."""
    points = [(60.0, 165.0), (262.0, 165.0), (232.0, 48.0), (98.0, 32.0)]
    out = [_open(320, 200),
           '<path d="M%.1f %.1f L%.1f %.1f L%.1f %.1f L%.1f %.1f Z"/>'
           % tuple(value for point in points for value in point)]
    for index, text in enumerate(texts):
        out.append(corner_arc(points[index], points[index - 1], points[(index + 1) % 4],
                              text, text == unknown))
    out.append(label(312, 194, 'Not drawn accurately', 'end', size=11))
    out.append('</svg>')
    return ''.join(out)


PARALLEL_CORNERS = ('TR', 'TL', 'BL', 'BR')


def parallel_lines(theta, marks, unknown='x'):
    """Two parallel lines (arrow marks) cut by a transversal at theta
    degrees. marks maps (crossing, corner) to a label: crossing 'upper' or
    'lower', corner TR, TL, BL or BR around that crossing."""
    upper_y, lower_y = 70.0, 145.0
    run = (lower_y - upper_y) / math.tan(math.radians(theta))
    upper, lower = (160 + run / 2, upper_y), (160 - run / 2, lower_y)
    out = [_open(320, 210)]
    for y in (upper_y, lower_y):
        out.append('<path d="M20 %.1f H300"/>' % y)
        out.append('<path d="M54 %.1f L60 %.1f L54 %.1f" stroke-width="1.8"/>' % (y - 5, y, y + 5))
    out.append(_line(_toward(lower[0], lower[1], theta + 180, 50),
                     _toward(upper[0], upper[1], theta, 50)))
    turns = {'TR': (0, theta), 'TL': (theta, 180), 'BL': (180, 180 + theta),
             'BR': (180 + theta, 360)}
    for (crossing, corner), text in marks.items():
        px, py = upper if crossing == 'upper' else lower
        start, end = turns[corner]
        out.append(arc(px, py, start, end, text, text == unknown, radius=22, gap=16))
    out.append('</svg>')
    return ''.join(out)


def polygon_angles(n, interior=None, exterior=None, unknown='x'):
    """A regular n-sided polygon, flat on the bottom, with an interior and/or
    exterior angle marked at the bottom-right corner (the bottom side is
    extended, dashed, for the exterior angle)."""
    cx, cy, radius = 150.0, 108.0, 80.0
    points = [_toward(cx, cy, 270 - 180.0 / n + 360.0 * k / n, radius) for k in range(n)]
    out = [_open(320, 200),
           '<path d="M%s Z"/>' % ' L'.join('%.1f %.1f' % point for point in points)]
    corner, before, after = points[1], points[0], points[2]
    if interior:
        out.append(corner_arc(corner, before, after, interior, interior == unknown, radius=22))
    if exterior:
        reach = _toward(corner[0], corner[1], _direction(before, corner), 60)
        out.append(_line(corner, reach, ' stroke-dasharray="5 4"'))
        out.append(corner_arc(corner, reach, after, exterior, exterior == unknown, radius=30))
    out.append('</svg>')
    return ''.join(out)


def bar_model(groups, names, values=None, total=None):
    """A ratio bar: groups[i] equal boxes for names[i], each group in its own
    colour. values (one per group, or None) sit above the groups; total sits
    above the whole bar."""
    count = sum(groups)
    box = min(40.0, 280.0 / count)
    width = box * count
    x0, y0, height = (320 - width) / 2, 52.0, 34.0
    out = ['<svg viewBox="0 0 320 120" width="320" height="120" '
           'xmlns="http://www.w3.org/2000/svg" fill="none" stroke-width="1.6" %s>' % FONT]
    if total:
        out.append(label(x0 + width / 2, 20, total, unknown=total == '?', size=15))
    x = x0
    for index, size in enumerate(groups):
        colour = PALETTE[index % len(PALETTE)]
        start = x
        for _ in range(size):
            out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" '
                       'fill-opacity="0.28" stroke="%s"/>' % (x, y0, box, height, colour, colour))
            x += box
        centre = start + size * box / 2
        out.append(label(centre, y0 + height + 22, names[index], size=14))
        if values and values[index]:
            out.append(label(centre, y0 - 9, values[index], size=14))
    out.append('</svg>')
    return ''.join(out)


def right_triangle(base, height, base_label='', height_label='', hyp_label='',
                   angle=None, unknown='x'):
    """A right-angled triangle with the right angle bottom left, drawn to
    scale (kept readable when very long or very tall). angle is (corner,
    text): 'B' the bottom-right corner, 'C' the top corner."""
    scale = min(180.0 / base, 115.0 / height)
    w, h = max(base * scale, 70.0), max(height * scale, 50.0)
    ax, ay = 70.0, 165.0
    bx, by = ax + w, ay
    cx, cy = ax, ay - h
    out = ['<svg viewBox="0 0 320 200" width="320" height="200" '
           'xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" '
           'stroke-width="2.2" stroke-linejoin="round" %s>' % FONT,
           '<path d="M%.1f %.1f L%.1f %.1f L%.1f %.1f Z"/>' % (ax, ay, bx, by, cx, cy),
           '<path d="M%.1f %.1f H%.1f V%.1f" stroke-width="1.5"/>' % (ax, ay - 13, ax + 13, ay)]
    if base_label:
        out.append(label((ax + bx) / 2, ay + 24, base_label, unknown=base_label == unknown))
    if height_label:
        out.append(label(ax - 12, (ay + cy) / 2 + 6, height_label, 'end',
                         height_label == unknown))
    if hyp_label:
        length = math.hypot(w, h)
        nx, ny = h / length, -w / length            # outward, away from the right angle
        mx, my = (bx + cx) / 2, (by + cy) / 2
        out.append(label(mx + nx * 16, my + ny * 16 + 5, hyp_label, 'start',
                         hyp_label == unknown))
    if angle:
        corner, text = angle
        out += angle_mark(corner, text, (ax, ay), (bx, by), (cx, cy), text == unknown)
    out.append('</svg>')
    return ''.join(out)


def angle_mark(corner, text, a, b, c, unknown, radius=28):
    """An arc at corner B or C with its label just inside the triangle."""
    if corner == 'B':
        vertex, first, second, sweep = b, a, c, 1
    else:
        vertex, first, second, sweep = c, a, b, 0
    vx, vy = vertex

    def unit(point):
        dx, dy = point[0] - vx, point[1] - vy
        length = math.hypot(dx, dy)
        return dx / length, dy / length

    u1, u2 = unit(first), unit(second)
    start = (vx + u1[0] * radius, vy + u1[1] * radius)
    end = (vx + u2[0] * radius, vy + u2[1] * radius)
    mx, my = u1[0] + u2[0], u1[1] + u2[1]
    length = math.hypot(mx, my)
    tx = vx + mx / length * (radius + 18)
    ty = vy + my / length * (radius + 18) + 5
    return ['<path d="M%.1f %.1f A%d %d 0 0 %d %.1f %.1f" stroke-width="1.6"/>'
            % (start[0], start[1], radius, radius, sweep, end[0], end[1]),
            label(tx, ty, text, 'middle', unknown, size=15)]
