"""Angle facts: on a line, around a point, vertically opposite, triangles,
quadrilaterals, and angles written as expressions, then Stretch. Parallel
lines and polygons are their own lessons (parallel_lines.py, polygons.py),
which share this file's helpers. Every problem draws its diagram
(mathskit/diagrams.py) with the unknown in the accent colour.

Problems carry meta got (from the rule in the working) and expected (from
the angles the diagram was built from) for tests/smoke_lessons.py.
"""
from fractions import Fraction as F

from .. import algebra, diagrams
from ..algebra import Term, mono
from ..lesson import Fact, Lesson, Line, Problem, Stage, Worked

X = mono('x')
RULES = {'line': ('Angles on a straight line add up to 180\u00b0', 180),
         'point': ('Angles around a point add up to 360\u00b0', 360),
         'triangle': ('Angles in a triangle add up to 180\u00b0', 180)}


# --- Helpers (shared with parallel_lines.py and polygons.py) ----------------------

def deg(value):
    return r'%s^{\circ}' % value


def deg_text(value):
    return '%s\u00b0' % value


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


def expression_text(a, c):
    lead = 'x' if a == 1 else '%dx' % a
    if c == 0:
        return lead
    return '%s %s %d' % (lead, '+' if c > 0 else '-', abs(c))


def times_x(k):
    return 'x' if k == 1 else '%dx' % k


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


def vertically_opposite(rng):
    while True:
        a = rng.randint(30, 150)
        if abs(a - 90) > 8:
            break
    sizes = [a, 180 - a, a, 180 - a]                  # two straight lines crossing
    hidden = rng.randrange(4)
    known_index = rng.choice([index for index in range(4) if index != hidden])
    known = sizes[known_index]
    texts = [''] * 4
    texts[known_index], texts[hidden] = deg_text(known), 'x'
    lines = [Line('Two straight lines cross. Find x. Give a reason.')]
    if (hidden - known_index) % 2 == 0:
        x = known
        lines.append(Line('x is opposite %s: vertically opposite angles are equal' % deg_text(known),
                          'x = ' + deg(x)))
        reason = 'vertically opposite angles are equal'
    else:
        x = 180 - known
        lines.append(Line('x is next to %s on a straight line: they add up to 180\u00b0' % deg_text(known),
                          r'x = 180^{\circ} - %s = %s' % (deg(known), deg(x))))
        reason = 'angles on a straight line add up to 180\u00b0'
    figure = diagrams.angles_at_point(sizes, texts)
    return made(lines, 'x = %s (%s)' % (deg_text(x), reason), x, sizes[hidden], figure)


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


def problems(rng):
    """Stretch: an isosceles triangle with angles in a given relation, the
    exterior angle of a triangle, and an isosceles triangle with its base
    extended."""
    kind = rng.choice(('isosceles_ratio', 'exterior', 'extended_base'))
    if kind == 'isosceles_ratio':
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
    if kind == 'exterior':
        while True:
            a, b = rng.randint(25, 100), rng.randint(25, 100)
            if 40 <= 180 - a - b and a + b != 90 and a != b:
                break
        c = 180 - a - b
        lines = [Line('A triangle has angles %s and %s. The side at its third corner is extended, '
                      'making an exterior angle x next to the third angle. Find x.'
                      % (deg_text(a), deg_text(b))),
                 Line('The third angle', r'180^{\circ} - %s - %s = %s' % (deg(a), deg(b), deg(c))),
                 Line('x and the third angle are on a straight line',
                      r'x = 180^{\circ} - %s = %s' % (deg(c), deg(a + b))),
                 Line('Check: an exterior angle equals the two opposite angles added',
                      r'%s + %s = %s' % (deg(a), deg(b), deg(a + b)))]
        return made(lines, 'x = ' + deg_text(a + b), 180 - c, a + b)
    exterior = rng.randint(100, 155)
    base = 180 - exterior
    top = 180 - 2 * base
    lines = [Line('An isosceles triangle has its base extended at one end. The exterior angle there '
                  'is %s. Find the top angle.' % deg_text(exterior)),
             Line('Angles on a straight line: the base angle', r'180^{\circ} - %s = %s' % (deg(exterior), deg(base))),
             Line('The other base angle is equal (isosceles)', deg(base)),
             Line('Angles in a triangle add up to 180\u00b0',
                  r'180^{\circ} - %s - %s = %s' % (deg(base), deg(base), deg(top)))]
    figure = diagrams.triangle_angles(base, base, (deg_text(base), deg_text(base), 'x'), ticks=True)
    return made(lines, deg_text(top), top, 2 * exterior - 180, figure)
# --- Facts (editable) ---------------------------------------------------------

FACTS = [
    Fact('On a straight line', r'Angles on a straight line add up to $180^{\circ}$.',
         diagrams.angles_at_point([115, 65], ['a', 'b'], unknown='', line=True)),
    Fact('Around a point', r'Angles around a point add up to $360^{\circ}$.'),
    Fact('Vertically opposite', r'Where two straight lines cross, opposite angles are equal.',
         diagrams.angles_at_point([60, 120, 60, 120], ['a', '', 'a', ''], unknown='')),
    Fact('In a triangle', r'Angles in a triangle add up to $180^{\circ}$. In an isosceles '
                          r'triangle the two base angles are equal.',
         diagrams.triangle_angles(70, 70, ('a', 'a', 'b'), unknown='', ticks=True)),
    Fact('Exterior angle of a triangle', r'It equals the two opposite interior angles added '
                                         r'together.'),
    Fact('In a quadrilateral', r'Angles in a quadrilateral add up to $360^{\circ}$.'),
    Fact('Give a reason', r'Name the rule every time: "angles on a straight line add up to '
                          r'$180^{\circ}$". The reason earns marks.'),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='angles',
    title='Angle facts',
    area='Geometry',
    keywords=('angles', 'angles on a line', 'around a point', 'vertically opposite', 'triangle',
              'isosceles', 'quadrilateral', 'exterior angle of a triangle', 'angle reasons'),
    intro='Lines, points, triangles and quadrilaterals: know the totals and give the reason.',
    facts=FACTS,
    stages=[
        Stage('on_a_line', 'On a line',
              r'Angles on a straight line add up to $180^{\circ}$: take the ones you know away.',
              on_a_line),
        Stage('around_point', 'Around a point',
              r'Angles around a point add up to $360^{\circ}$.',
              around_point),
        Stage('vertically_opposite', 'Vertically opposite',
              r'Where two lines cross, opposite angles are equal and neighbours add up to '
              r'$180^{\circ}$.',
              vertically_opposite),
        Stage('triangles', 'Triangles',
              r'Angles in a triangle add up to $180^{\circ}$. Isosceles: the two base angles '
              r'(under the equal sides) are equal.',
              triangles),
        Stage('quadrilaterals', 'Quadrilaterals',
              r'Angles in a quadrilateral add up to $360^{\circ}$: it is two triangles.',
              quadrilaterals),
        Stage('algebraic', 'Algebra with angles',
              r'Write the angle fact as an equation, collect like terms, solve for $x$, then '
              r'put $x$ back in to find each angle.',
              algebraic),
        Stage('problems', 'Stretch',
              r'Chain the facts: a straight line into a triangle, isosceles triangles described in '
              r'words, exterior angles.',
              problems),
    ])
