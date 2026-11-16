"""Angles: on a line, around a point, triangles, quadrilaterals, parallel
lines, polygons, and angles written as expressions. Every problem draws
its diagram (mathskit/diagrams.py) with the unknown in the accent colour.

Problems carry meta got (from the rule in the working) and expected (from
the angles the diagram was built from) for tests/smoke_lessons.py.
"""
from fractions import Fraction as F

from .. import algebra, diagrams
from ..algebra import Term, mono
from ..lesson import Fact, Lesson, Line, Problem, Stage, Worked

X = mono('x')
POLYGON_NAMES = {3: 'triangle', 4: 'quadrilateral', 5: 'pentagon', 6: 'hexagon', 7: 'heptagon',
                 8: 'octagon', 9: 'nonagon', 10: 'decagon', 12: 'dodecagon'}
REGULAR_SIDES = (3, 4, 5, 6, 8, 9, 10, 12, 15, 18, 20, 24, 36)
RULES = {'line': ('Angles on a straight line add up to 180\u00b0', 180),
         'point': ('Angles around a point add up to 360\u00b0', 360),
         'triangle': ('Angles in a triangle add up to 180\u00b0', 180)}


def deg(value):
    return r'%s^{\circ}' % value


def deg_text(value):
    return '%s\u00b0' % value


def polygon_name(n):
    return POLYGON_NAMES.get(n, '%d-sided polygon' % n)


def made(lines, answer, got, expected, figure=None):
    return Problem(statement=lines[0].tex or lines[0].say, answer=answer,
                   solution=Worked(lines, answer), meta={'got': got, 'expected': expected},
                   figure=figure)


def split(rng, total, count, low=20, high=170):
    """count whole angles adding to total, each between low and high, none 90."""
    while True:
        cuts = sorted(rng.sample(range(low, total - low + 1), count - 1))
        sizes = [b - a for a, b in zip([0] + cuts, cuts + [total])]
        if all(low <= size <= high for size in sizes) and 90 not in sizes:
            return sizes


def subtract_lines(rule, total, known, x):
    sum_tex = ' + '.join(deg(value) for value in known)
    working = r'x = %s - %s = %s' % (deg(total), deg(sum(known)), deg(x)) if len(known) > 1 \
        else r'x = %s - %s = %s' % (deg(total), deg(known[0]), deg(x))
    return [Line(rule, r'x + %s = %s' % (sum_tex, deg(total))),
            Line('Take the known angles away from %d\u00b0' % total, working)]


def labelled(sizes, unknown_index):
    return ['x' if index == unknown_index else deg_text(size) for index, size in enumerate(sizes)]


# --- Stages -------------------------------------------------------------------

def on_a_line(rng):
    sizes = split(rng, 180, rng.choice((2, 3, 3)))
    hidden = rng.randrange(len(sizes))
    known = [size for index, size in enumerate(sizes) if index != hidden]
    x = 180 - sum(known)
    lines = [Line('Find x')] + subtract_lines(RULES['line'][0], 180, known, x)
    figure = diagrams.angles_at_point(sizes, labelled(sizes, hidden), line=True)
    return made(lines, 'x = ' + deg_text(x), x, sizes[hidden], figure)


def around_point(rng):
    sizes = split(rng, 360, rng.choice((3, 4)), low=30)
    hidden = rng.randrange(len(sizes))
    known = [size for index, size in enumerate(sizes) if index != hidden]
    x = 360 - sum(known)
    lines = [Line('Find x')] + subtract_lines(RULES['point'][0], 360, known, x)
    figure = diagrams.angles_at_point(sizes, labelled(sizes, hidden))
    return made(lines, 'x = ' + deg_text(x), x, sizes[hidden], figure)


def triangles(rng):
    kind = rng.choice(('two', 'two', 'right', 'isosceles_apex', 'isosceles_base'))
    if kind == 'isosceles_apex':
        apex = rng.choice(range(20, 142, 2))
        base = (180 - apex) // 2
        lines = [Line('Find x. The triangle is isosceles.'),
                 Line('The two base angles are equal: both are x',
                      r'x + x + %s = 180^{\circ}' % deg(apex)),
                 Line('Take the top angle away from 180\u00b0',
                      r'2x = 180^{\circ} - %s = %s' % (deg(apex), deg(180 - apex))),
                 Line('Halve it', r'x = %s' % deg(base))]
        figure = diagrams.triangle_angles(base, base, ('x', 'x', deg_text(apex)), ticks=True)
        return made(lines, 'x = ' + deg_text(base), F(180 - apex, 2), base, figure)
    if kind == 'isosceles_base':
        base = rng.randint(30, 80)
        apex = 180 - 2 * base
        lines = [Line('Find x. The triangle is isosceles.'),
                 Line('The base angles are equal, so the other one is also %s' % deg_text(base),
                      r'%s + %s + x = 180^{\circ}' % (deg(base), deg(base))),
                 Line('Take them away from 180\u00b0',
                      r'x = 180^{\circ} - %s = %s' % (deg(2 * base), deg(apex)))]
        figure = diagrams.triangle_angles(base, base, (deg_text(base), '', 'x'), ticks=True)
        return made(lines, 'x = ' + deg_text(apex), 180 - 2 * base, apex, figure)
    while True:
        a = 90 if kind == 'right' else rng.randint(30, 110)
        b = rng.randint(25, 130)
        c = 180 - a - b
        if c >= 20 and 90 not in (b, c) and (kind == 'right' or a != 90):
            break
    sizes = [a, b, c]
    hidden = rng.choice((1, 2)) if kind == 'right' else rng.randrange(3)
    known = [size for index, size in enumerate(sizes) if index != hidden]
    x = 180 - sum(known)
    lines = [Line('Find x')] + subtract_lines(RULES['triangle'][0], 180, known, x)
    figure = diagrams.triangle_angles(a, b, labelled(sizes, hidden))
    return made(lines, 'x = ' + deg_text(x), x, sizes[hidden], figure)


def quadrilaterals(rng):
    sizes = split(rng, 360, 4, low=50, high=150)
    hidden = rng.randrange(4)
    known = [size for index, size in enumerate(sizes) if index != hidden]
    x = 360 - sum(known)
    lines = [Line('Find x')] + subtract_lines('Angles in a quadrilateral add up to 360\u00b0',
                                              360, known, x)
    figure = diagrams.quadrilateral(labelled(sizes, hidden))
    return made(lines, 'x = ' + deg_text(x), x, sizes[hidden], figure)


PAIRS = {
    'alternate': [(('upper', 'BL'), ('lower', 'TR')), (('upper', 'BR'), ('lower', 'TL'))],
    'corresponding': [(('upper', corner), ('lower', corner)) for corner in ('TR', 'TL', 'BL', 'BR')],
    'co-interior': [(('upper', 'BL'), ('lower', 'TL')), (('upper', 'BR'), ('lower', 'TR'))],
    'vertically opposite': [((crossing, 'TR'), (crossing, 'BL')) for crossing in ('upper', 'lower')]
                           + [((crossing, 'TL'), (crossing, 'BR')) for crossing in ('upper', 'lower')],
}
EQUAL = {'alternate': 'Alternate angles are equal', 'corresponding': 'Corresponding angles are equal',
         'vertically opposite': 'Vertically opposite angles are equal'}


def parallel(rng):
    kind = rng.choice(('alternate', 'corresponding', 'co-interior', 'co-interior',
                       'vertically opposite'))
    while True:
        theta = rng.randint(35, 145)
        if abs(theta - 90) > 12:
            break
    pair = list(rng.choice(PAIRS[kind]))
    rng.shuffle(pair)
    known_at, unknown_at = pair
    size = {'TR': theta, 'BL': theta, 'TL': 180 - theta, 'BR': 180 - theta}
    known = size[known_at[1]]
    lines = [Line('Find x. Give a reason.'),
             Line('x and %s are %s angles' % (deg_text(known), kind), r'\text{%s angles}' % kind)]
    if kind == 'co-interior':
        x = 180 - known
        lines.append(Line('Co-interior angles add up to 180\u00b0',
                          r'x = 180^{\circ} - %s = %s' % (deg(known), deg(x))))
        reason = 'co-interior angles add up to 180\u00b0'
    else:
        x = known
        lines.append(Line(EQUAL[kind], 'x = ' + deg(x)))
        reason = EQUAL[kind].lower()
    figure = diagrams.parallel_lines(theta, {known_at: deg_text(known), unknown_at: 'x'})
    return made(lines, 'x = %s (%s)' % (deg_text(x), reason), x, size[unknown_at[1]], figure)


def polygons(rng):
    kind = rng.choice(('sum', 'interior', 'exterior', 'sides_exterior', 'sides_interior'))
    if kind == 'sum':
        n = rng.randint(4, 12)
        total = (n - 2) * 180
        lines = [Line('Find the sum of the interior angles of a %s (%d sides)' % (polygon_name(n), n)),
                 Line('Split it into triangles from one corner: two fewer than the sides',
                      r'%d - 2 = %d \text{ triangles}' % (n, n - 2)),
                 Line('Each triangle adds 180\u00b0', r'%d \times 180^{\circ} = %s' % (n - 2, deg(total)))]
        figure = diagrams.polygon_angles(n) if n <= 10 else None
        return made(lines, deg_text(total), total, 180 * n - 360, figure)
    n = rng.choice(REGULAR_SIDES)
    exterior = 360 // n
    interior = 180 - exterior
    name = polygon_name(n)
    if kind == 'exterior':
        lines = [Line('Find each exterior angle of a regular %s (%d sides)' % (name, n)),
                 Line('Exterior angles add up to 360\u00b0', r'360^{\circ} \div %d = %s' % (n, deg(exterior)))]
        figure = diagrams.polygon_angles(n, exterior='x') if n <= 12 else None
        return made(lines, 'x = ' + deg_text(exterior), exterior, F(360, n), figure)
    if kind == 'interior':
        lines = [Line('Find each interior angle of a regular %s (%d sides)' % (name, n)),
                 Line('Exterior angles add up to 360\u00b0', r'360^{\circ} \div %d = %s' % (n, deg(exterior))),
                 Line('Interior and exterior angles add up to 180\u00b0',
                      r'180^{\circ} - %s = %s' % (deg(exterior), deg(interior)))]
        figure = diagrams.polygon_angles(n, interior='x') if n <= 12 else None
        return made(lines, 'x = ' + deg_text(interior), interior, F((n - 2) * 180, n), figure)
    if kind == 'sides_exterior':
        lines = [Line('A regular polygon has exterior angles of %s. How many sides does it have?'
                      % deg_text(exterior)),
                 Line('Exterior angles add up to 360\u00b0', r'n = 360^{\circ} \div %s = %d' % (deg(exterior), n))]
        return made(lines, '%d sides' % n, 360 // exterior, n)
    lines = [Line('A regular polygon has interior angles of %s. How many sides does it have?'
                  % deg_text(interior)),
             Line('The exterior angle is 180\u00b0 minus the interior angle',
                  r'180^{\circ} - %s = %s' % (deg(interior), deg(exterior))),
             Line('Exterior angles add up to 360\u00b0', r'n = 360^{\circ} \div %s = %d' % (deg(exterior), n))]
    return made(lines, '%d sides' % n, 360 // (180 - interior), n)


def expression_text(a, c):
    lead = 'x' if a == 1 else '%dx' % a
    if c == 0:
        return lead
    return '%s %s %d' % (lead, '+' if c > 0 else '-', abs(c))


def algebraic(rng):
    kind = rng.choice(('line', 'point', 'triangle'))
    rule, total = RULES[kind]
    count = {'line': rng.choice((2, 3)), 'point': rng.choice((3, 4)), 'triangle': 3}[kind]
    while True:
        x = rng.randint(5, 30)
        coefficients = [rng.randint(1, 4) for _ in range(count)]
        constants = [rng.choice((0, rng.randint(-15, 40))) for _ in range(count - 1)]
        constants.append(total - sum(a * x + c for a, c in zip(coefficients, constants))
                         - coefficients[-1] * x)
        sizes = [a * x + c for a, c in zip(coefficients, constants)]
        if (all(20 <= size <= 165 for size in sizes) and 90 not in sizes
                and abs(constants[-1]) <= 60):
            break
    expressions = [[Term(a, X), Term(c)] for a, c in zip(coefficients, constants)]
    shown = ' + '.join('(%s)' % algebra.tex(e) if e[1].coefficient else algebra.tex(e)
                       for e in expressions)
    big_a, big_c = sum(coefficients), sum(constants)
    lines = [Line('Find x, then the size of each angle'),
             Line(rule, '%s = %d' % (shown, total)),
             Line('Collect like terms', '%s = %d' % (algebra.tex([Term(big_a, X), Term(big_c)]), total)),
             Line('Solve', r'%dx = %d \;\Rightarrow\; x = %d' % (big_a, total - big_c, x)),
             Line('Put x back into each angle', r', \quad '.join(
                 '%s = %s' % (algebra.tex(e), deg(size)) for e, size in zip(expressions, sizes)))]
    texts = [expression_text(a, c) for a, c in zip(coefficients, constants)]
    if kind == 'triangle':
        figure = diagrams.triangle_angles(sizes[0], sizes[1], texts, unknown='')
    else:
        figure = diagrams.angles_at_point(sizes, texts, unknown='', line=kind == 'line')
    got = F(total - big_c, big_a)
    return made(lines, 'x = %d' % x, got, x, figure)


def times_x(k):
    return 'x' if k == 1 else '%dx' % k


def problems(rng):
    """Stretch: polygons meeting at a point, interior as a multiple of
    exterior, an isosceles triangle with angles in a given relation."""
    kind = rng.choice(('meeting', 'multiple', 'isosceles_ratio'))
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
        exterior = 180 // (k + 1)
        n = 360 // exterior
        lines = [Line('In a regular polygon each interior angle is %d times the exterior angle. '
                      'How many sides does it have?' % k),
                 Line('Call the exterior angle x, so the interior angle is %s' % times_x(k),
                      r'x + %s = 180^{\circ}' % times_x(k)),
                 Line('Solve', r'%dx = 180^{\circ} \;\Rightarrow\; x = %s' % (k + 1, deg(exterior))),
                 Line('Exterior angles add up to 360\u00b0',
                      r'n = 360^{\circ} \div %s = %d' % (deg(exterior), n))]
        return made(lines, '%d sides' % n, n, 2 * k + 2,
                    diagrams.polygon_angles(n, interior=times_x(k), exterior='x', unknown='')
                    if n <= 12 else None)
    k = rng.choice((1, 2, 3, 4, 7, 8, 10))
    x = 180 // (k + 2)
    apex = k * x
    lines = [Line('In an isosceles triangle the top angle is %d times each base angle. Find all '
                  'three angles.' % k),
             Line('Call each base angle x, so the top angle is %s' % times_x(k),
                  r'x + x + %s = 180^{\circ}' % times_x(k)),
             Line('Collect and solve', r'%dx = 180^{\circ} \;\Rightarrow\; x = %s' % (k + 2, deg(x))),
             Line('The top angle', r'%d \times %s = %s' % (k, deg(x), deg(apex)))]
    figure = diagrams.triangle_angles(x, x, ('x', 'x', times_x(k)), unknown='', ticks=True)
    return made(lines, '%s, %s and %s' % (deg_text(x), deg_text(x), deg_text(apex)), (x, apex),
                (F(180, k + 2), F(180 * k, k + 2)), figure)
# --- Facts (editable) ---------------------------------------------------------

FACTS = [
    Fact('On a straight line', r'Angles on a straight line add up to $180^{\circ}$.',
         diagrams.angles_at_point([115, 65], ['a', 'b'], unknown='', line=True)),
    Fact('Around a point', r'Angles around a point add up to $360^{\circ}$.'),
    Fact('Vertically opposite', r'Where two straight lines cross, opposite angles are equal.'),
    Fact('In a triangle', r'Angles in a triangle add up to $180^{\circ}$. In an isosceles '
                          r'triangle the two base angles are equal.',
         diagrams.triangle_angles(70, 70, ('a', 'a', 'b'), unknown='', ticks=True)),
    Fact('In a quadrilateral', r'Angles in a quadrilateral add up to $360^{\circ}$.'),
    Fact('Parallel lines', r'Alternate angles are equal (Z). Corresponding angles are equal (F). '
                           r'Co-interior angles add up to $180^{\circ}$ (C).',
         diagrams.parallel_lines(60, {('upper', 'BL'): 'a', ('lower', 'TR'): 'a'}, unknown='')),
    Fact('Polygons', r'Interior angles add up to $(n - 2) \times 180^{\circ}$. In a regular '
                     r'polygon each exterior angle is $360^{\circ} \div n$, and interior '
                     r'$+$ exterior $= 180^{\circ}$.',
         diagrams.polygon_angles(6, 'i', 'e', unknown='')),
    Fact('Give a reason', r'Name the rule every time: "angles on a straight line add up to '
                          r'$180^{\circ}$". The reason earns marks.'),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='angles',
    title='Angles',
    area='Geometry',
    keywords=('angles on a line', 'around a point', 'vertically opposite', 'triangle',
              'isosceles', 'quadrilateral', 'parallel lines', 'alternate', 'corresponding',
              'co-interior', 'polygons', 'interior', 'exterior', 'regular polygon', 'sides',
              'angle reasons'),
    intro='Every angle fact, from a straight line to polygons.',
    facts=FACTS,
    stages=[
        Stage('on_a_line', 'On a line',
              r'Angles on a straight line add up to $180^{\circ}$: take the ones you know away.',
              on_a_line),
        Stage('around_point', 'Around a point',
              r'Angles around a point add up to $360^{\circ}$.',
              around_point),
        Stage('triangles', 'Triangles',
              r'Angles in a triangle add up to $180^{\circ}$. Isosceles: the two base angles '
              r'(under the equal sides) are equal.',
              triangles),
        Stage('quadrilaterals', 'Quadrilaterals',
              r'Angles in a quadrilateral add up to $360^{\circ}$: it is two triangles.',
              quadrilaterals),
        Stage('parallel', 'Parallel lines',
              r'Name the pair, then use the rule: alternate and corresponding are equal, '
              r'co-interior add up to $180^{\circ}$. Always give the reason.',
              parallel),
        Stage('polygons', 'Polygons',
              r'Interior sum $(n - 2) \times 180^{\circ}$. Regular polygons: exterior '
              r'$= 360^{\circ} \div n$, interior $= 180^{\circ} -$ exterior.',
              polygons),
        Stage('algebraic', 'Algebra with angles',
              r'Write the angle fact as an equation, collect like terms, solve for $x$, then '
              r'put $x$ back in to find each angle.',
              algebraic),
        Stage('problems', 'Stretch',
              r'Chain the angle facts: polygons meeting at a point, interior and exterior angles '
              r'linked by an equation, triangles described in words.',
              problems),
    ])
