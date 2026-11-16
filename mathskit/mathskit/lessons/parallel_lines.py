"""Parallel lines: alternate, corresponding and co-interior angles one at a
time, then mixed, two steps, algebra, and Stretch. Every problem draws the
two parallel lines and the transversal (mathskit/diagrams.py).

Corners: at each crossing the four angles are TR, TL, BL, BR. With the
transversal at theta degrees, TR and BL are theta, TL and BR are
180 - theta. Problems carry meta got (from the reasons in the working) and
expected (the drawn angle) for tests/smoke_lessons.py.
"""
from fractions import Fraction as F

from .. import diagrams
from ..lesson import Fact, Lesson, Line, Stage
from .angles import deg, deg_text, expression_text, made, times_x

PAIRS = {
    'alternate': [(('upper', 'BL'), ('lower', 'TR')), (('upper', 'BR'), ('lower', 'TL'))],
    'corresponding': [(('upper', corner), ('lower', corner)) for corner in ('TR', 'TL', 'BL', 'BR')],
    'co-interior': [(('upper', 'BL'), ('lower', 'TL')), (('upper', 'BR'), ('lower', 'TR'))],
    'vertically opposite': [((crossing, 'TR'), (crossing, 'BL')) for crossing in ('upper', 'lower')]
                           + [((crossing, 'TL'), (crossing, 'BR')) for crossing in ('upper', 'lower')],
}
EQUAL = {'alternate': 'Alternate angles are equal', 'corresponding': 'Corresponding angles are equal',
         'vertically opposite': 'Vertically opposite angles are equal'}
CORNERS = ('TR', 'TL', 'BL', 'BR')
OPPOSITE = {'TR': 'BL', 'BL': 'TR', 'TL': 'BR', 'BR': 'TL'}
ONE_STEP = (('BL', 'TR'), ('BR', 'TL'), ('BL', 'TL'), ('BR', 'TR'))   # (upper, lower) pairs a single rule links


def angle_at(theta, corner):
    return theta if corner in ('TR', 'BL') else 180 - theta


def pick_theta(rng):
    while True:
        theta = rng.randint(35, 145)
        if abs(theta - 90) > 12:
            return theta


def theta_for(value, corner):
    """The transversal's angle that makes the angle at corner equal value."""
    return value if corner in ('TR', 'BL') else 180 - value


# --- Stages -------------------------------------------------------------------

def pair_problem(rng, kind):
    theta = pick_theta(rng)
    pair = list(rng.choice(PAIRS[kind]))
    rng.shuffle(pair)
    known_at, unknown_at = pair
    known = angle_at(theta, known_at[1])
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
    return made(lines, 'x = %s (%s)' % (deg_text(x), reason), x, angle_at(theta, unknown_at[1]), figure)


def alternate(rng):
    return pair_problem(rng, 'alternate')


def corresponding(rng):
    return pair_problem(rng, 'corresponding')


def co_interior(rng):
    return pair_problem(rng, 'co-interior')


def mixed(rng):
    return pair_problem(rng, rng.choice(('alternate', 'corresponding', 'co-interior', 'co-interior',
                                         'vertically opposite')))


def second_step(known, from_corner, to_corner):
    """At one crossing: the angle at to_corner from the one at from_corner,
    with its line of working and its reason."""
    if OPPOSITE[from_corner] == to_corner:
        return known, Line('Vertically opposite angles are equal', 'x = ' + deg(known))
    return 180 - known, Line('Angles on a straight line add up to 180\u00b0',
                             r'x = 180^{\circ} - %s = %s' % (deg(known), deg(180 - known)))


def two_corners(rng):
    """(known crossing and corner, unknown crossing and corner) needing two steps."""
    while True:
        c1, c2 = rng.choice(CORNERS), rng.choice(CORNERS)
        known_upper = rng.random() < 0.5
        upper, lower = (c1, c2) if known_upper else (c2, c1)
        if c1 != c2 and (upper, lower) not in ONE_STEP:
            crossings = ('upper', 'lower') if known_upper else ('lower', 'upper')
            return (crossings[0], c1), (crossings[1], c2)


def two_steps(rng):
    theta = pick_theta(rng)
    known_at, unknown_at = two_corners(rng)
    known = angle_at(theta, known_at[1])
    x, step = second_step(known, known_at[1], unknown_at[1])
    lines = [Line('Find x. Give a reason for each step.'),
             Line('Corresponding angles are equal: the same corner at the other crossing is also %s'
                  % deg_text(known), deg(known)),
             step]
    figure = diagrams.parallel_lines(theta, {known_at: deg_text(known), unknown_at: 'x'})
    return made(lines, 'x = ' + deg_text(x), x, angle_at(theta, unknown_at[1]), figure)


def algebraic(rng):
    kind = rng.choice(('alternate', 'corresponding', 'co-interior'))
    while True:
        x = rng.randint(5, 30)
        a1, a2 = rng.sample(range(1, 6), 2)
        b1 = rng.randint(-20, 40)
        v1 = a1 * x + b1
        v2 = 180 - v1 if kind == 'co-interior' else v1
        b2 = v2 - a2 * x
        if 35 <= v1 <= 145 and abs(v1 - 90) > 12 and abs(b2) <= 60:
            break
    pos1, pos2 = rng.choice(PAIRS[kind])
    e1, e2 = expression_text(a1, b1), expression_text(a2, b2)
    lines = [Line('Find x, then the size of each angle')]
    if kind == 'co-interior':
        total_a, total_b = a1 + a2, b1 + b2
        lines += [Line('Co-interior angles add up to 180\u00b0', '(%s) + (%s) = 180' % (e1, e2)),
                  Line('Collect like terms', '%s = 180' % expression_text(total_a, total_b)),
                  Line('Solve', r'%s = %d \;\Rightarrow\; x = %d' % (times_x(total_a), 180 - total_b, x))]
        got = F(180 - total_b, total_a)
    else:
        big, small = ((a1, b1), (a2, b2)) if a1 > a2 else ((a2, b2), (a1, b1))
        lines += [Line(EQUAL[kind], '%s = %s' % (e1, e2)),
                  Line('Get the x terms on one side and the numbers on the other',
                       '%s = %d' % (times_x(big[0] - small[0]), small[1] - big[1])),
                  Line('Solve', 'x = %d' % x)]
        got = F(small[1] - big[1], big[0] - small[0])
    lines.append(Line('Put x back into each angle', r'%s = %s, \quad %s = %s' % (e1, deg(v1), e2, deg(v2))))
    figure = diagrams.parallel_lines(theta_for(v1, pos1[1]), {pos1: e1, pos2: e2}, unknown='')
    return made(lines, 'x = %d' % x, got, x, figure)


def problems(rng):
    """Stretch: two steps that end in an equation, or co-interior angles in
    a ratio."""
    if rng.random() < 0.5:
        theta = pick_theta(rng)
        known_at, unknown_at = two_corners(rng)
        known = angle_at(theta, known_at[1])
        target = angle_at(theta, unknown_at[1])
        while True:
            x = rng.randint(5, 30)
            a = rng.randint(2, 5)
            b = target - a * x
            if b and abs(b) <= 60:
                break
        expression = expression_text(a, b)
        value, step = second_step(known, known_at[1], unknown_at[1])
        lines = [Line('Find x. Give a reason for each step.'),
                 Line('Corresponding angles are equal: the same corner at the other crossing is also %s'
                      % deg_text(known), deg(known)),
                 Line(step.say, '%s = %s' % (expression, deg(value))),
                 Line('Solve', r'%s = %d \;\Rightarrow\; x = %d' % (times_x(a), value - b, x))]
        figure = diagrams.parallel_lines(theta, {known_at: deg_text(known), unknown_at: expression},
                                         unknown='')
        return made(lines, 'x = %d' % x, F(value - b, a), x, figure)
    while True:
        p, q = rng.sample(range(1, 8), 2)
        if 180 % (p + q) == 0:
            k = 180 // (p + q)
            if 35 <= p * k <= 145 and abs(p * k - 90) > 12:
                break
    pos1, pos2 = rng.choice(PAIRS['co-interior'])
    lines = [Line('Two co-interior angles are in the ratio %d : %d. Find them.' % (p, q)),
             Line('Co-interior angles add up to 180\u00b0', '%dk + %dk = 180' % (p, q)),
             Line('Solve', r'%dk = 180 \;\Rightarrow\; k = %d' % (p + q, k)),
             Line('Each angle', r'%d \times %d = %s, \quad %d \times %d = %s' % (p, k, deg(p * k), q, k, deg(q * k)))]
    figure = diagrams.parallel_lines(theta_for(p * k, pos1[1]), {pos1: '%dk' % p, pos2: '%dk' % q},
                                     unknown='')
    return made(lines, '%s and %s' % (deg_text(p * k), deg_text(q * k)), (p * k, q * k),
                (F(180 * p, p + q), F(180 * q, p + q)), figure)
# --- Facts (editable) ---------------------------------------------------------

FACTS = [
    Fact('Alternate angles', r'Equal: the Z shape.',
         diagrams.parallel_lines(60, {('upper', 'BL'): 'a', ('lower', 'TR'): 'a'}, unknown='')),
    Fact('Corresponding angles', r'Equal: the F shape, the same corner at each crossing.',
         diagrams.parallel_lines(60, {('upper', 'TR'): 'a', ('lower', 'TR'): 'a'}, unknown='')),
    Fact('Co-interior angles', r'Add up to $180^{\circ}$: the C shape, between the lines on one side.',
         diagrams.parallel_lines(60, {('upper', 'BR'): 'a', ('lower', 'TR'): 'b'}, unknown='')),
    Fact('Two steps', r'Move an angle to the other crossing (corresponding), then use straight-line '
                      r'or vertically opposite angles.'),
    Fact('Give a reason', r'Name the pair: "alternate angles are equal". Say "angles", not "Z angles".'),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='parallel_lines',
    title='Parallel lines',
    area='Geometry',
    keywords=('parallel lines', 'alternate', 'corresponding', 'co-interior', 'allied',
              'transversal', 'z angles', 'f angles', 'c angles', 'angle reasons'),
    intro='Alternate and corresponding are equal; co-interior add up to 180\u00b0.',
    facts=FACTS,
    stages=[
        Stage('alternate', 'Alternate angles',
              r'Either side of the transversal, between the lines: they are equal (Z).',
              alternate),
        Stage('corresponding', 'Corresponding angles',
              r'The same corner at each crossing: they are equal (F).',
              corresponding),
        Stage('co_interior', 'Co-interior angles',
              r'The same side, between the lines: they add up to $180^{\circ}$ (C).',
              co_interior),
        Stage('mixed', 'Name the pair',
              r'Decide which pair it is first, then use its rule and say the reason.',
              mixed),
        Stage('two_steps', 'Two steps',
              r'Move the angle to the other crossing, then finish with straight-line or vertically '
              r'opposite angles. A reason for each step.',
              two_steps),
        Stage('algebraic', 'Algebra with parallel lines',
              r'Equal pairs: set the expressions equal. Co-interior: add them to $180$. Then solve.',
              algebraic),
        Stage('problems', 'Stretch',
              r'Chain the steps into an equation, or share $180^{\circ}$ in a ratio.',
              problems),
    ])
