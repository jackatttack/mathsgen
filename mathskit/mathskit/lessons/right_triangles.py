"""Right-angled triangles: Pythagoras, then trigonometry (SOH CAH TOA) and
exact values. Every problem draws its own triangle to scale
(mathskit/diagrams.py) with the unknown in the accent colour, and the angle
at either acute corner so labelling O and A is practised.

Problems carry meta got (from the working shown) and expected (from the
triangle built another way) for tests/smoke_lessons.py to compare.
"""
import math
from fractions import Fraction as F

from .. import diagrams, numbers
from ..lesson import Fact, Lesson, Line, Problem, Stage, Worked
from ..numbers import frac_tex

TRIPLES = ((3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (20, 21, 29))
RATIOS = {('O', 'H'): 'sin', ('A', 'H'): 'cos', ('O', 'A'): 'tan'}
FUNCTIONS = {'sin': math.sin, 'cos': math.cos, 'tan': math.tan}
INVERSES = {'sin': math.asin, 'cos': math.acos, 'tan': math.atan}
NAMES = {'O': 'Opposite', 'A': 'Adjacent', 'H': 'Hypotenuse'}
DEGREES = '\u00b0'

# Exact values as (coefficient, root): coefficient times the square root of root.
EXACT = {('sin', 0): (F(0), 1), ('sin', 30): (F(1, 2), 1), ('sin', 45): (F(1, 2), 2),
         ('sin', 60): (F(1, 2), 3), ('sin', 90): (F(1), 1),
         ('cos', 0): (F(1), 1), ('cos', 30): (F(1, 2), 3), ('cos', 45): (F(1, 2), 2),
         ('cos', 60): (F(1, 2), 1), ('cos', 90): (F(0), 1),
         ('tan', 0): (F(0), 1), ('tan', 30): (F(1, 3), 3), ('tan', 45): (F(1), 1),
         ('tan', 60): (F(1), 3)}


# --- Helpers ------------------------------------------------------------------

def one_dp(value):
    return format(numbers.round_to(F(value), 1), 'f')


def exact_or_one_dp(value):
    return str(int(round(value))) if abs(value - round(value)) < 1e-9 else one_dp(value)


def triple(rng, most=30):
    while True:
        a, b, c = rng.choice(TRIPLES)
        k = rng.randint(1, 4)
        if c * k <= most:
            return a * k, b * k, c * k


def root_line(square):
    root = math.isqrt(square)
    if root * root == square:
        return r'x = \sqrt{%d} = %d' % (square, root), str(root)
    shown = one_dp(math.sqrt(square))
    return r'x = \sqrt{%d} \approx %s' % (square, shown), shown


def made(lines, answer, got, expected, figure=None):
    return Problem(statement=lines[0].say, answer=answer, solution=Worked(lines, answer),
                   meta={'got': got, 'expected': expected}, figure=figure)


def geometry(theta, known, length):
    """All three sides from the angle and one known side."""
    t = math.radians(theta)
    hyp = {'H': length, 'O': length / math.sin(t), 'A': length / math.cos(t)}[known]
    return {'O': hyp * math.sin(t), 'A': hyp * math.cos(t), 'H': hyp}


def trig_figure(corner, sides, labels, angle_text, unknown='x'):
    """Angle at B: opposite is the height, adjacent the base. Angle at C:
    opposite is the base, adjacent the height."""
    if corner == 'B':
        return diagrams.right_triangle(sides['A'], sides['O'], labels.get('A', ''),
                                       labels.get('O', ''), labels.get('H', ''),
                                       angle=('B', angle_text), unknown=unknown)
    return diagrams.right_triangle(sides['O'], sides['A'], labels.get('O', ''),
                                   labels.get('A', ''), labels.get('H', ''),
                                   angle=('C', angle_text), unknown=unknown)


def exact_tex(coefficient, root):
    """coefficient times sqrt(root): \\frac{\\sqrt{3}}{2}, 4\\sqrt{3}, 5."""
    coefficient = F(coefficient)
    if coefficient == 0:
        return '0'
    if root == 1:
        return frac_tex(coefficient)
    top = ('' if abs(coefficient.numerator) == 1 else str(abs(coefficient.numerator)))
    top += r'\sqrt{%d}' % root
    sign = '-' if coefficient < 0 else ''
    if coefficient.denominator == 1:
        return sign + top
    return r'%s\frac{%s}{%d}' % (sign, top, coefficient.denominator)


# --- Stages -------------------------------------------------------------------

def hypotenuse(rng):
    if rng.random() < 0.5:
        a, b, _ = triple(rng)
    else:
        a, b = rng.randint(3, 15), rng.randint(3, 15)
    if rng.random() < 0.5:
        a, b = b, a
    square = a * a + b * b
    root_tex, shown = root_line(square)
    lines = [Line('Find x, the hypotenuse (to 1 decimal place if it is not exact)'),
             Line('x is opposite the right angle, so it is the hypotenuse: use Pythagoras',
                  r'a^{2} + b^{2} = c^{2}'),
             Line('Substitute the two shorter sides', r'%d^{2} + %d^{2} = x^{2}' % (a, b)),
             Line('Square and add', r'%d + %d = x^{2} \;\Rightarrow\; x^{2} = %d'
                  % (a * a, b * b, square)),
             Line('Square root', root_tex)]
    figure = diagrams.right_triangle(a, b, str(a), str(b), 'x')
    return made(lines, 'x = ' + shown, shown, exact_or_one_dp(math.hypot(a, b)), figure)


def shorter_side(rng):
    if rng.random() < 0.5:
        a, _, c = triple(rng)
    else:
        c = rng.randint(8, 20)
        a = rng.randint(3, c - 2)
    square = c * c - a * a
    root_tex, shown = root_line(square)
    other = math.sqrt(square)
    if rng.random() < 0.5:
        figure = diagrams.right_triangle(other, a, 'x', str(a), str(c))
    else:
        figure = diagrams.right_triangle(a, other, str(a), 'x', str(c))
    lines = [Line('Find x (to 1 decimal place if it is not exact)'),
             Line('The hypotenuse (%d) is given, so x is a shorter side: subtract' % c,
                  r'x^{2} = c^{2} - a^{2}'),
             Line('Substitute and work it out',
                  r'x^{2} = %d^{2} - %d^{2} = %d - %d = %d' % (c, a, c * c, a * a, square)),
             Line('Square root', root_tex)]
    expected = exact_or_one_dp(math.sqrt((c - a) * (c + a)))
    return made(lines, 'x = ' + shown, shown, expected, figure)


def is_right(rng):
    a, b, c = triple(rng)
    if rng.random() < 0.5:
        c += rng.choice((-1, 1))
    sides = [a, b, c]
    rng.shuffle(sides)
    p, q, r = sorted(sides)
    left, right = p * p + q * q, r * r
    yes = left == right
    lines = [Line('A triangle has sides %d, %d and %d. Is it right-angled?' % tuple(sides)),
             Line('If it is, the longest side is the hypotenuse', 'c = %d' % r),
             Line('Square the two shorter sides and add',
                  r'%d^{2} + %d^{2} = %d + %d = %d' % (p, q, p * p, q * q, left)),
             Line('Square the longest side', r'%d^{2} = %d' % (r, right)),
             Line('Compare', r'%d %s %d \;\Rightarrow\; \text{%s}'
                  % (left, '=' if yes else r'\neq', right,
                     'right-angled' if yes else 'not right-angled'))]
    largest_angle = math.degrees(math.acos((p * p + q * q - r * r) / (2.0 * p * q)))
    return made(lines, 'Yes' if yes else 'No', yes, abs(largest_angle - 90) < 1e-9)


def trig_side(rng, on_top):
    (top, bottom) = rng.choice(list(RATIOS))
    name = RATIOS[(top, bottom)]
    unknown, known = (top, bottom) if on_top else (bottom, top)
    theta, corner = rng.randint(20, 70), rng.choice('BC')
    length = rng.randint(4, 20)
    ratio = FUNCTIONS[name](math.radians(theta))
    value = length * ratio if on_top else length / ratio
    shown = one_dp(value)
    sides = geometry(theta, known, length)
    put = {unknown: 'x', known: str(length)}
    lines = [Line('Find x to 1 decimal place (calculator in degrees)'),
             Line('Label the sides from the %d%s angle' % (theta, DEGREES),
                  r'\text{%s} = %s, \quad \text{%s} = %s' % (top, put[top], bottom, put[bottom])),
             Line('%s and %s: use %s (SOH CAH TOA)' % (NAMES[top], NAMES[bottom].lower(), name),
                  r'\%s\theta = \frac{\text{%s}}{\text{%s}}' % (name, top, bottom)),
             Line('Substitute', r'\%s %d^{\circ} = \frac{%s}{%s}' % (name, theta, put[top],
                                                                      put[bottom]))]
    if on_top:
        lines.append(Line('Multiply both sides by %d' % length,
                          r'x = %d \%s %d^{\circ} \approx %s' % (length, name, theta, shown)))
    else:
        lines.append(Line('x is on the bottom: swap x and %s %d%s' % (name, theta, DEGREES),
                          r'x = \frac{%d}{\%s %d^{\circ}} \approx %s' % (length, name, theta, shown)))
    figure = trig_figure(corner, sides, put, '%d%s' % (theta, DEGREES))
    return made(lines, 'x = ' + shown, shown, one_dp(sides[unknown]), figure)


def trig_top(rng):
    return trig_side(rng, on_top=True)


def trig_bottom(rng):
    return trig_side(rng, on_top=False)


def trig_angle(rng):
    (top, bottom) = rng.choice(list(RATIOS))
    name = RATIOS[(top, bottom)]
    if name == 'tan':
        p, q = rng.randint(3, 15), rng.randint(3, 15)
    else:
        p = rng.randint(3, 14)
        q = rng.randint(p + 2, p + 12)
    theta = math.degrees(INVERSES[name](p / q))
    shown = one_dp(theta)
    if name == 'sin':
        sides = {'O': p, 'H': q, 'A': math.sqrt(q * q - p * p)}
    elif name == 'cos':
        sides = {'A': p, 'H': q, 'O': math.sqrt(q * q - p * p)}
    else:
        sides = {'O': p, 'A': q, 'H': math.hypot(p, q)}
    lines = [Line('Find the angle \u03b8 to 1 decimal place (calculator in degrees)'),
             Line('Label the sides from \u03b8',
                  r'\text{%s} = %d, \quad \text{%s} = %d' % (top, p, bottom, q)),
             Line('%s and %s: use %s (SOH CAH TOA)' % (NAMES[top], NAMES[bottom].lower(), name),
                  r'\%s\theta = \frac{\text{%s}}{\text{%s}}' % (name, top, bottom)),
             Line('Substitute', r'\%s\theta = \frac{%d}{%d}' % (name, p, q)),
             Line('Use the inverse (shift %s)' % name,
                  r'\theta = \%s^{-1}\left(\frac{%d}{%d}\right) \approx %s^{\circ}'
                  % (name, p, q, shown))]
    figure = trig_figure(rng.choice('BC'), sides, {top: str(p), bottom: str(q)},
                         '\u03b8', unknown='\u03b8')
    expected = one_dp(math.degrees(math.atan2(sides['O'], sides['A'])))
    return made(lines, '\u03b8 = %s%s' % (shown, DEGREES), shown, expected, figure)


def exact_values(rng):
    if rng.random() < 0.4:
        name, angle = rng.choice(sorted(EXACT))
        coefficient, root = EXACT[(name, angle)]
        lines = [Line('Write down the exact value', r'\%s %d^{\circ}' % (name, angle)),
                 Line('From the exact values table',
                      r'\%s %d^{\circ} = %s' % (name, angle, exact_tex(coefficient, root)))]
        got = round(float(coefficient) * math.sqrt(root), 9)
        expected = round(FUNCTIONS[name](math.radians(angle)), 9)
        return made(lines, lines[-1].tex, got, expected)
    (top, bottom) = rng.choice(list(RATIOS))
    name = RATIOS[(top, bottom)]
    angle = rng.choice((30, 45, 60))
    length = rng.choice((2, 4, 6, 8, 10, 12, 14, 16, 18, 20))
    coefficient, root = EXACT[(name, angle)]
    answer = exact_tex(coefficient * length, root)
    sides = geometry(angle, bottom, length)
    put = {top: 'x', bottom: str(length)}
    lines = [Line('Find the exact value of x (no calculator)'),
             Line('Label the sides from the %d%s angle' % (angle, DEGREES),
                  r'\text{%s} = x, \quad \text{%s} = %d' % (top, bottom, length)),
             Line('%s and %s: use %s' % (NAMES[top], NAMES[bottom].lower(), name),
                  r'x = %d \%s %d^{\circ}' % (length, name, angle)),
             Line('Use the exact value', r'x = %d \times %s = %s'
                  % (length, exact_tex(coefficient, root), answer))]
    got = round(float(coefficient * length) * math.sqrt(root), 9)
    figure = trig_figure(rng.choice('BC'), sides, put, '%d%s' % (angle, DEGREES))
    return made(lines, 'x = ' + answer, got, round(sides[top], 9), figure)


def problems(rng):
    """Stretch: distance between points, a cuboid's diagonal, a ladder."""
    kind = rng.choice(('distance', 'cuboid', 'ladder'))
    if kind == 'distance':
        while True:
            x1, y1, x2, y2 = (rng.randint(-8, 8) for _ in range(4))
            dx, dy = x2 - x1, y2 - y1
            if dx and dy:
                break
        square = dx * dx + dy * dy
        root_tex, shown = root_line(square)
        lines = [Line('Find the distance between (%d, %d) and (%d, %d), to 1 decimal place if it '
                      'is not exact' % (x1, y1, x2, y2)),
                 Line('Make a right-angled triangle: the distance across and the distance up',
                      r'\text{across} = %d, \quad \text{up} = %d' % (abs(dx), abs(dy))),
                 Line('Pythagoras', r'd^{2} = %d^{2} + %d^{2} = %d' % (abs(dx), abs(dy), square)),
                 Line('Square root', root_tex.replace('x =', 'd ='))]
        figure = diagrams.right_triangle(abs(dx), abs(dy), str(abs(dx)), str(abs(dy)), 'd',
                                         unknown='d')
        expected = exact_or_one_dp(math.hypot(dx, dy))
        return made(lines, 'd = ' + shown, shown, expected, figure)
    if kind == 'cuboid':
        a, b, c = (rng.randint(2, 12) for _ in range(3))
        face, space = a * a + b * b, a * a + b * b + c * c
        root_tex, shown = root_line(space)
        lines = [Line('A cuboid measures %d by %d by %d. Find the length of its longest diagonal, '
                      'to 1 decimal place if it is not exact.' % (a, b, c)),
                 Line('First the diagonal across the base: Pythagoras',
                      r'd^{2} = %d^{2} + %d^{2} = %d' % (a, b, face)),
                 Line('Keep it as d\u00b2: it goes straight into the next step'),
                 Line('The longest diagonal uses that and the height',
                      r'D^{2} = d^{2} + %d^{2} = %d + %d = %d' % (c, face, c * c, space)),
                 Line('Square root', root_tex.replace('x =', 'D ='))]
        return made(lines, 'D = ' + shown, shown, exact_or_one_dp(math.sqrt(a * a + b * b + c * c)))
    length = rng.randint(4, 12)
    foot = rng.randint(1, length // 2)
    square = length * length - foot * foot
    height = math.sqrt(square)
    shown_height = exact_or_one_dp(height)
    angle = one_dp(math.degrees(math.acos(foot / length)))
    lines = [Line('A %d m ladder leans against a wall with its foot %d m from the wall. How high '
                  'up the wall does it reach, and what angle does it make with the ground?'
                  % (length, foot)),
             Line('Height: the ladder is the hypotenuse, so subtract',
                  r'h^{2} = %d^{2} - %d^{2} = %d' % (length, foot, square)),
             Line('Square root', r'h = \sqrt{%d} %s %s \text{ m}'
                  % (square, '=' if height == int(height) else r'\approx', shown_height)),
             Line('Angle with the ground: adjacent %d, hypotenuse %d, so cos' % (foot, length),
                  r'\cos\theta = \frac{%d}{%d}' % (foot, length)),
             Line('Inverse cos', r'\theta = \cos^{-1}\left(\frac{%d}{%d}\right) \approx %s^{\circ}'
                  % (foot, length, angle))]
    figure = diagrams.right_triangle(foot, height, str(foot), 'h', str(length),
                                     angle=('B', '\u03b8'), unknown='h')
    expected = (exact_or_one_dp(math.sqrt((length - foot) * (length + foot))),
                one_dp(math.degrees(math.atan2(height, foot))))
    return made(lines, 'h = %s m, angle %s\u00b0' % (shown_height, angle), (shown_height, angle),
                expected, figure)
# --- Facts (editable) ---------------------------------------------------------

PYTHAG = diagrams.right_triangle(4, 3, 'a', 'b', 'c', unknown='')
SOH = diagrams.right_triangle(4, 3, 'A', 'O', 'H', angle=('B', '\u03b8'), unknown='')
EXACT_TABLE = (r'\begin{array}{c|ccccc} & 0^{\circ} & 30^{\circ} & 45^{\circ} & 60^{\circ} '
               r'& 90^{\circ} \\ \hline \sin & 0 & \frac{1}{2} & \frac{\sqrt{2}}{2} & '
               r'\frac{\sqrt{3}}{2} & 1 \\ \cos & 1 & \frac{\sqrt{3}}{2} & \frac{\sqrt{2}}{2} & '
               r'\frac{1}{2} & 0 \\ \tan & 0 & \frac{\sqrt{3}}{3} & 1 & \sqrt{3} & - \end{array}')

FACTS = [
    Fact('The hypotenuse', r'The longest side, opposite the right angle.'),
    Fact('Pythagoras', r'$a^{2} + b^{2} = c^{2}$, where $c$ is the hypotenuse.', PYTHAG),
    Fact('Finding a shorter side', r'Subtract: $b^{2} = c^{2} - a^{2}$. A shorter side must '
                                   r'come out shorter than the hypotenuse.'),
    Fact('Is it right-angled?', r'Only if the two shorter sides squared add up to the longest '
                                r'side squared.'),
    Fact('SOH CAH TOA', r'$\sin\theta = \frac{O}{H}$, $\cos\theta = \frac{A}{H}$, '
                        r'$\tan\theta = \frac{O}{A}$.', SOH),
    Fact('Labelling the sides', r'Hypotenuse: opposite the right angle. Opposite: across from '
                                r'the angle. Adjacent: next to the angle, and not the hypotenuse.'),
    Fact('Finding an angle', r'Use the inverse: $\theta = \sin^{-1}\left(\frac{O}{H}\right)$. '
                             r'Check the calculator is in degrees.'),
    Fact('Exact values', r'Learn these for the non-calculator paper.', tex=EXACT_TABLE),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='right_triangles',
    title='Pythagoras and trigonometry',
    area='Geometry',
    keywords=('right-angled triangles', 'right angled triangles', 'pythagoras', 'trigonometry',
              'trig', 'sohcahtoa', 'soh cah toa', 'sin', 'cos', 'tan', 'hypotenuse',
              'exact values', 'angle'),
    intro=r'Pythagoras for two sides; SOH CAH TOA when an angle is involved.',
    facts=FACTS,
    stages=[
        Stage('hypotenuse', 'Hypotenuse',
              r'The hypotenuse is opposite the right angle and is the longest side. Square the '
              r'two shorter sides, add, then square root.',
              hypotenuse),
        Stage('shorter_side', 'Shorter side',
              r'Given the hypotenuse? Square both sides you know, subtract, then square root.',
              shorter_side),
        Stage('is_right', 'Is it right-angled?',
              r'Check whether $a^{2} + b^{2} = c^{2}$, with $c$ the longest side.',
              is_right),
        Stage('trig_top', 'Trig: a side',
              r'Label O, A and H from the angle, pick the ratio with the two sides you need, '
              r'substitute, then multiply.',
              trig_top),
        Stage('trig_bottom', 'Trig: x on the bottom',
              r'When $x$ is on the bottom of the fraction, swap $x$ and the trig value: '
              r'$x = \frac{10}{\sin 30^{\circ}}$.',
              trig_bottom),
        Stage('trig_angle', 'Trig: an angle',
              r'With two sides, write the ratio as a fraction, then use the inverse: '
              r'$\theta = \sin^{-1}\left(\frac{O}{H}\right)$.',
              trig_angle),
        Stage('exact_values', 'Exact values',
              r'Learn the values for $0^{\circ}$, $30^{\circ}$, $45^{\circ}$, $60^{\circ}$ and '
              r'$90^{\circ}$, and use them without a calculator.',
              exact_values),
        Stage('problems', 'Stretch',
              r'Find the right-angled triangle hiding in the problem: between two points, inside '
              r'a cuboid, or a ladder against a wall. Sometimes it takes two steps.',
              problems),
    ])
