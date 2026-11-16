"""mathsgen diagrams as inline SVG for the question card.

    from mathskit import figures
    figures.svg_for(asset)          # a question's visual asset -> '<svg ...>'

mathsgen draws every visual kind (scene, plot, table, venn, boxplot) as a
reportlab Drawing through visuals.drawing_for. reportlab's own renderSVG
needs a freetype extension Pythonista lacks, so this walks the Drawing and
writes the SVG itself: groups (with their transforms), lines, rects,
circles, ellipses, polygons, polylines, paths and strings. reportlab's y
axis points up, so the whole drawing sits in one flip, and each string
flips back so its letters read the right way up.

Shapes it does not know yet are listed in SKIPPED (tests/smoke_questions.py
prints them) rather than failing the card. Pure Python apart from mathsgen.
"""
from html import escape

WIDTH = 320              # points: mathsgen lays diagrams out for this width
SKIPPED = set()          # shape class names met but not drawn

FONT_FAMILIES = {'Helvetica': 'Helvetica, Arial, sans-serif', 'Times': 'Times, serif',
                 'Courier': 'Menlo, Courier, monospace'}
LINE_CAPS = {0: 'butt', 1: 'round', 2: 'square'}
LINE_JOINS = {0: 'miter', 1: 'round', 2: 'bevel'}
ANCHORS = {'start': 'start', 'middle': 'middle', 'end': 'end', 'numeric': 'end'}


def svg_for(asset, width=WIDTH):
    from mathsgen import visuals
    return drawing_svg(visuals.drawing_for(asset, width))


def drawing_svg(drawing):
    width, height = float(drawing.width), float(drawing.height)
    out = ['<svg class="qc-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s">'
           % (number(width), number(height)),
           '<g transform="matrix(1 0 0 -1 0 %s)">' % number(height)]
    transform = getattr(drawing, 'transform', None)
    if transform and tuple(transform) != (1, 0, 0, 1, 0, 0):
        out.append('<g transform="matrix(%s)">' % ' '.join(number(v) for v in transform))
        walk(drawing, out)
        out.append('</g>')
    else:
        walk(drawing, out)
    out.append('</g></svg>')
    return ''.join(out)


# --- Shapes -------------------------------------------------------------------

def walk(group, out):
    for shape in getattr(group, 'contents', ()):
        name = type(shape).__name__
        if hasattr(shape, 'contents'):
            transform = getattr(shape, 'transform', (1, 0, 0, 1, 0, 0))
            out.append('<g transform="matrix(%s)">' % ' '.join(number(v) for v in transform))
            walk(shape, out)
            out.append('</g>')
        elif name == 'Line':
            out.append('<line x1="%s" y1="%s" x2="%s" y2="%s"%s/>'
                       % (number(shape.x1), number(shape.y1), number(shape.x2), number(shape.y2),
                          paint(shape, filled=False)))
        elif name == 'Rect':
            out.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" ry="%s"%s/>'
                       % (number(shape.x), number(shape.y), number(shape.width),
                          number(shape.height), number(getattr(shape, 'rx', 0) or 0),
                          number(getattr(shape, 'ry', 0) or 0), paint(shape)))
        elif name == 'Circle':
            out.append('<circle cx="%s" cy="%s" r="%s"%s/>'
                       % (number(shape.cx), number(shape.cy), number(shape.r), paint(shape)))
        elif name == 'Ellipse':
            out.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s"%s/>'
                       % (number(shape.cx), number(shape.cy), number(shape.rx), number(shape.ry),
                          paint(shape)))
        elif name == 'Polygon':
            out.append('<polygon points="%s"%s/>' % (points(shape.points), paint(shape)))
        elif name == 'PolyLine':
            out.append('<polyline points="%s"%s/>' % (points(shape.points), paint(shape, filled=False)))
        elif name == 'Path':
            out.append('<path d="%s"%s/>' % (path_data(shape), paint(shape)))
        elif name == 'String':
            out.append(text(shape))
        elif hasattr(shape, 'asPolygon'):
            holder = type('Holder', (), {})()
            holder.contents = [shape.asPolygon()]
            walk(holder, out)
        else:
            SKIPPED.add(name)


def path_data(shape):
    values = list(shape.points)
    parts, at = [], 0
    for operator in shape.operators:
        if operator == 0:
            parts.append('M%s %s' % (number(values[at]), number(values[at + 1])))
            at += 2
        elif operator == 1:
            parts.append('L%s %s' % (number(values[at]), number(values[at + 1])))
            at += 2
        elif operator == 2:
            parts.append('C' + ' '.join(number(value) for value in values[at:at + 6]))
            at += 6
        elif operator == 3:
            parts.append('Z')
    return ' '.join(parts)


def text(shape):
    font = str(getattr(shape, 'fontName', 'Helvetica') or 'Helvetica')
    family = next((value for key, value in FONT_FAMILIES.items() if font.startswith(key)),
                  FONT_FAMILIES['Helvetica'])
    weight = ' font-weight="bold"' if 'Bold' in font else ''
    style = ' font-style="italic"' if 'Oblique' in font or 'Italic' in font else ''
    anchor = ANCHORS.get(getattr(shape, 'textAnchor', 'start'), 'start')
    return ('<text transform="matrix(1 0 0 -1 %s %s)" font-size="%s" font-family="%s"%s%s '
            'text-anchor="%s" fill="%s">%s</text>'
            % (number(shape.x), number(shape.y), number(getattr(shape, 'fontSize', 10)),
               family, weight, style, anchor, colour(getattr(shape, 'fillColor', None), 'black'),
               escape(str(shape.text))))


# --- Paint and numbers --------------------------------------------------------

def colour(value, default='none'):
    if value is None:
        return default
    try:
        return 'rgb(%d,%d,%d)' % (round(value.red * 255), round(value.green * 255),
                                  round(value.blue * 255))
    except AttributeError:
        return default


def paint(shape, filled=True):
    fill = getattr(shape, 'fillColor', None) if filled else None
    stroke = getattr(shape, 'strokeColor', None)
    attributes = [' fill="%s"' % colour(fill), ' stroke="%s"' % colour(stroke)]
    for name, value in (('fill-opacity', alpha(fill, getattr(shape, 'fillOpacity', None))),
                        ('stroke-opacity', alpha(stroke, getattr(shape, 'strokeOpacity', None)))):
        if value is not None:
            attributes.append(' %s="%s"' % (name, number(value)))
    if stroke is not None:
        attributes.append(' stroke-width="%s"' % number(getattr(shape, 'strokeWidth', 1) or 1))
        dashes = getattr(shape, 'strokeDashArray', None)
        if dashes:
            if len(dashes) == 2 and isinstance(dashes[1], (list, tuple)):
                dashes = dashes[1]               # (offset, pattern)
            attributes.append(' stroke-dasharray="%s"' % ' '.join(number(v) for v in dashes))
        cap = LINE_CAPS.get(getattr(shape, 'strokeLineCap', None))
        join = LINE_JOINS.get(getattr(shape, 'strokeLineJoin', None))
        if cap:
            attributes.append(' stroke-linecap="%s"' % cap)
        if join:
            attributes.append(' stroke-linejoin="%s"' % join)
    return ''.join(attributes)


def alpha(value, explicit):
    if explicit is not None and explicit < 1:
        return explicit
    shade = getattr(value, 'alpha', 1) if value is not None else 1
    return shade if shade is not None and shade < 1 else None


def points(values):
    values = list(values)
    return ' '.join('%s,%s' % (number(values[i]), number(values[i + 1]))
                    for i in range(0, len(values) - 1, 2))


def number(value):
    text = '%.2f' % float(value)
    return text.rstrip('0').rstrip('.') if '.' in text else text
