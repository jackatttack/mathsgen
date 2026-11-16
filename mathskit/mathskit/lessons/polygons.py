"""Polygons: the interior angle sum, regular exterior and interior angles,
the number of sides from an angle, an irregular polygon's missing angle,
then Stretch. Regular polygons up to 12 sides are drawn
(mathskit/diagrams.py).

Problems carry meta got (from the working) and expected (from the polygon
the question was built from) for tests/smoke_lessons.py.
"""
from fractions import Fraction as F

from .. import diagrams
from ..lesson import Fact, Lesson, Line, Stage
from .angles import deg, deg_text, made, split, times_x

POLYGON_NAMES = {3: 'triangle', 4: 'quadrilateral', 5: 'pentagon', 6: 'hexagon', 7: 'heptagon',
                 8: 'octagon', 9: 'nonagon', 10: 'decagon', 12: 'dodecagon'}
REGULAR_SIDES = (3, 4, 5, 6, 8, 9, 10, 12, 15, 18, 20, 24, 36)


def polygon_name(n):
    return POLYGON_NAMES.get(n, '%d-sided polygon' % n)


def regular(rng):
    n = rng.choice(REGULAR_SIDES)
    exterior = 360 // n
    return n, exterior, 180 - exterior, polygon_name(n)


# --- Stages -------------------------------------------------------------------

def interior_sum(rng):
    n = rng.randint(4, 12)
    total = (n - 2) * 180
    lines = [Line('Find the sum of the interior angles of a %s (%d sides)' % (polygon_name(n), n)),
             Line('Split it into triangles from one corner: two fewer than the sides',
                  r'%d - 2 = %d \text{ triangles}' % (n, n - 2)),
             Line('Each triangle adds 180\u00b0', r'%d \times 180^{\circ} = %s' % (n - 2, deg(total)))]
    figure = diagrams.polygon_angles(n) if n <= 10 else None
    return made(lines, deg_text(total), total, 180 * n - 360, figure)


def exterior(rng):
    n, outside, inside, name = regular(rng)
    lines = [Line('Find each exterior angle of a regular %s (%d sides)' % (name, n)),
             Line('Exterior angles add up to 360\u00b0', r'360^{\circ} \div %d = %s' % (n, deg(outside)))]
    figure = diagrams.polygon_angles(n, exterior='x') if n <= 12 else None
    return made(lines, 'x = ' + deg_text(outside), outside, F(360, n), figure)


def interior(rng):
    n, outside, inside, name = regular(rng)
    lines = [Line('Find each interior angle of a regular %s (%d sides)' % (name, n)),
             Line('Exterior angles add up to 360\u00b0', r'360^{\circ} \div %d = %s' % (n, deg(outside))),
             Line('Interior and exterior angles add up to 180\u00b0',
                  r'180^{\circ} - %s = %s' % (deg(outside), deg(inside)))]
    figure = diagrams.polygon_angles(n, interior='x') if n <= 12 else None
    return made(lines, 'x = ' + deg_text(inside), inside, F((n - 2) * 180, n), figure)


def sides(rng):
    n, outside, inside, name = regular(rng)
    if rng.random() < 0.5:
        lines = [Line('A regular polygon has exterior angles of %s. How many sides does it have?'
                      % deg_text(outside)),
                 Line('Exterior angles add up to 360\u00b0', r'n = 360^{\circ} \div %s = %d' % (deg(outside), n))]
        return made(lines, '%d sides' % n, 360 // outside, n)
    lines = [Line('A regular polygon has interior angles of %s. How many sides does it have?'
                  % deg_text(inside)),
             Line('The exterior angle is 180\u00b0 minus the interior angle',
                  r'180^{\circ} - %s = %s' % (deg(inside), deg(outside))),
             Line('Exterior angles add up to 360\u00b0', r'n = 360^{\circ} \div %s = %d' % (deg(outside), n))]
    return made(lines, '%d sides' % n, 360 // (180 - inside), n)


def irregular(rng):
    n = rng.randint(5, 8)
    total = (n - 2) * 180
    sizes = split(rng, total, n, low=70, high=175)
    hidden = rng.randrange(n)
    known = [size for index, size in enumerate(sizes) if index != hidden]
    x = total - sum(known)
    lines = [Line('An irregular %s has interior angles %s and x. Find x.'
                  % (polygon_name(n), ', '.join(deg_text(size) for size in known))),
             Line('Interior angles add up to (n - 2) \u00d7 180\u00b0',
                  r'(%d - 2) \times 180^{\circ} = %s' % (n, deg(total))),
             Line('Take the known angles away', r'x = %s - %s = %s' % (deg(total), deg(sum(known)), deg(x)))]
    return made(lines, 'x = ' + deg_text(x), x, sizes[hidden])


def problems(rng):
    """Stretch: regular polygons meeting at a point, interior as a multiple
    of exterior, and exterior angles written in x."""
    kind = rng.choice(('meeting', 'multiple', 'expressions'))
    if kind == 'meeting':
        while True:
            n1, n2 = rng.sample((3, 4, 5, 6, 8, 9, 10, 12), 2)
            i1, i2 = 180 - 360 // n1, 180 - 360 // n2
            x = 360 - i1 - i2
            if 20 <= x < 180:
                break
        name1, name2 = polygon_name(n1), polygon_name(n2)
        lines = [Line('A regular %s and a regular %s share a side and meet at a point. Find the '
                      'angle x left over at that point.' % (name1, name2)),
                 Line('Interior angle of the %s' % name1,
                      r'180^{\circ} - 360^{\circ} \div %d = %s' % (n1, deg(i1))),
                 Line('Interior angle of the %s' % name2,
                      r'180^{\circ} - 360^{\circ} \div %d = %s' % (n2, deg(i2))),
                 Line('Angles around a point add up to 360\u00b0',
                      r'x = 360^{\circ} - %s - %s = %s' % (deg(i1), deg(i2), deg(x)))]
        expected = 360 - F((n1 - 2) * 180, n1) - F((n2 - 2) * 180, n2)
        return made(lines, 'x = ' + deg_text(x), x, expected)
    if kind == 'multiple':
        k = rng.choice((1, 2, 3, 4, 5, 8, 9))
        outside = 180 // (k + 1)
        n = 360 // outside
        lines = [Line('In a regular polygon each interior angle is %d times the exterior angle. '
                      'How many sides does it have?' % k),
                 Line('Call the exterior angle x, so the interior angle is %s' % times_x(k),
                      r'x + %s = 180^{\circ}' % times_x(k)),
                 Line('Solve', r'%dx = 180^{\circ} \;\Rightarrow\; x = %s' % (k + 1, deg(outside))),
                 Line('Exterior angles add up to 360\u00b0',
                      r'n = 360^{\circ} \div %s = %d' % (deg(outside), n))]
        return made(lines, '%d sides' % n, n, 2 * k + 2,
                    diagrams.polygon_angles(n, interior=times_x(k), exterior='x', unknown='')
                    if n <= 12 else None)
    n = rng.choice((5, 6))
    while True:
        ks = [rng.randint(1, 4) for _ in range(n)]
        total = sum(ks)
        if 360 % total == 0 and max(ks) * (360 // total) < 180:
            x = 360 // total
            break
    shown = ', '.join(times_x(k) for k in ks)
    lines = [Line('The exterior angles of a %s are %s. Find x and the largest exterior angle.'
                  % (polygon_name(n), shown)),
             Line('Exterior angles add up to 360\u00b0', '%s = 360' % ' + '.join(times_x(k) for k in ks)),
             Line('Collect and solve', r'%dx = 360 \;\Rightarrow\; x = %d' % (total, x)),
             Line('The largest is %s' % times_x(max(ks)), r'%d \times %d = %s' % (max(ks), x, deg(max(ks) * x)))]
    return made(lines, 'x = %d, largest %s' % (x, deg_text(max(ks) * x)), F(360, total), x)
# --- Facts (editable) ---------------------------------------------------------

FACTS = [
    Fact('Interior angle sum', r'$(n - 2) \times 180^{\circ}$: split the polygon into $n - 2$ '
                               r'triangles from one corner.'),
    Fact('Exterior angles', r'The exterior angles of any polygon add up to $360^{\circ}$.',
         diagrams.polygon_angles(6, 'i', 'e', unknown='')),
    Fact('Regular polygons', r'Each exterior angle is $360^{\circ} \div n$; interior $= 180^{\circ} -$ '
                             r'exterior.'),
    Fact('Number of sides', r'$n = 360^{\circ} \div$ exterior angle. Find the exterior angle first if '
                            r'you are given the interior.'),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='polygons',
    title='Polygons',
    area='Geometry',
    keywords=('polygons', 'interior angles', 'exterior angles', 'regular polygon', 'sides',
              'angle sum', 'pentagon', 'hexagon', 'octagon', 'tessellation'),
    intro='Exterior angles add up to 360\u00b0; interior and exterior add up to 180\u00b0.',
    facts=FACTS,
    stages=[
        Stage('interior_sum', 'Interior angle sum',
              r'$(n - 2) \times 180^{\circ}$: from one corner the polygon splits into two fewer '
              r'triangles than it has sides.',
              interior_sum),
        Stage('exterior', 'Exterior angles',
              r'In a regular polygon each exterior angle is $360^{\circ} \div n$.',
              exterior),
        Stage('interior', 'Interior angles',
              r'Find the exterior angle first, then take it from $180^{\circ}$.',
              interior),
        Stage('sides', 'Number of sides',
              r'$n = 360^{\circ} \div$ exterior angle.',
              sides),
        Stage('irregular', 'Irregular polygons',
              r'Work out the total with $(n - 2) \times 180^{\circ}$, then take the known angles away.',
              irregular),
        Stage('problems', 'Stretch',
              r'Polygons meeting at a point, interior and exterior linked by an equation, exterior '
              r'angles written in $x$.',
              problems),
    ])
