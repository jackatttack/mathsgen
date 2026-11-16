"""Solving quadratics: factorising, the special cases, a not 1, rearranging
first, the formula, how many roots, then Stretch. Completing the square and
the graph are their own lesson (completing_square.py), which shares this
file's helpers.

Solving problems carry meta['roots'] = (the quadratic as Python, [roots]);
tests/smoke_lessons.py checks every root makes it zero.
"""
import math
from fractions import Fraction as F

from .. import algebra, numbers
from ..algebra import Term, mono
from ..lesson import Fact, Lesson, Line, Problem, Stage, Worked

X = mono('x')
X2 = mono('x^2')
tex = algebra.tex
plain = algebra.plain
OR = r' \quad \text{or} \quad '


# --- Helpers (shared with completing_square.py) ---------------------------------

def nonzero(rng, size=9):
    return rng.choice([value for value in range(-size, size + 1) if value])


def value_tex(value):
    """A root: whole, or a fraction."""
    value = F(value)
    if value.denominator == 1:
        return str(value.numerator)
    return r'%s\frac{%d}{%d}' % ('-' if value < 0 else '', abs(value.numerator), value.denominator)


def roots_line(roots):
    if roots[0] == roots[1]:
        return 'x = %s' % value_tex(roots[0])
    return 'x = %s' % value_tex(roots[0]) + OR + 'x = %s' % value_tex(roots[1])


def bracket(root_factor):
    """(x + 3) from its terms; plain x when the number is 0."""
    return '(%s)' % tex(root_factor) if len([t for t in root_factor if t.coefficient]) > 1 \
        else tex(root_factor)


def surd_tex(n):
    """sqrt(n) simplified: 12 -> 2\\sqrt{3}, 9 -> 3."""
    outside, inside = 1, n
    for k in range(math.isqrt(n), 1, -1):
        if n % (k * k) == 0:
            outside, inside = k, n // (k * k)
            break
    if inside == 1:
        return str(outside)
    return '%s\\sqrt{%d}' % (outside if outside > 1 else '', inside)


def squared_tex(inner, k):
    """(x + h)^2 + k, with no + 0."""
    out = '(%s)^{2}' % inner
    if k:
        out += ' %s %d' % ('+' if k > 0 else '-', abs(k))
    return out


def made(lines, answer, meta, figure=None):
    return Problem(statement=lines[0].tex or lines[0].say, answer=answer,
                   solution=Worked(lines, answer), meta=meta, figure=figure)


def two_numbers(rng):
    """p and q for (x + p)(x + q): different, not cancelling."""
    while True:
        p, q = nonzero(rng), nonzero(rng)
        if p + q and p != q:
            return p, q


# --- Stages -------------------------------------------------------------------

def factorising(rng):
    p, q = two_numbers(rng)
    poly = [Term(1, X2), Term(p + q, X), Term(p * q)]
    first, second = tex([Term(1, X), Term(p)]), tex([Term(1, X), Term(q)])
    lines = [Line('Solve', tex(poly) + ' = 0'),
             Line('Factorise: two numbers that multiply to %d and add to %d' % (p * q, p + q),
                  '(%s)(%s) = 0' % (first, second)),
             Line('One of the brackets must be 0', '%s = 0' % first + OR + '%s = 0' % second),
             Line('Solve each one', roots_line([-p, -q]))]
    return made(lines, lines[-1].tex, {'roots': (plain(poly), [-p, -q])})


def special(rng):
    kind = rng.choice(('common', 'common_a', 'squares', 'squares_a'))
    if kind in ('common', 'common_a'):
        a = 1 if kind == 'common' else rng.randint(2, 6)
        b = nonzero(rng)
        poly = [Term(a, X2), Term(a * b, X)]
        other = tex([Term(1, X), Term(b)])
        outside = 'x' if a == 1 else '%dx' % a
        lines = [Line('Solve', tex(poly) + ' = 0'),
                 Line('Take out the common factor %s' % outside, '%s(%s) = 0' % (outside, other)),
                 Line('One of the factors must be 0', '%s = 0' % outside + OR + '%s = 0' % other),
                 Line('Solve each one', roots_line([0, -b]))]
        return made(lines, lines[-1].tex, {'roots': (plain(poly), [0, -b])})
    while True:
        m = 1 if kind == 'squares' else rng.randint(2, 5)
        k = rng.randint(1, 12)
        if math.gcd(m, k) == 1:
            break
    poly = [Term(m * m, X2), Term(-k * k)]
    lead = 'x' if m == 1 else '%dx' % m
    lines = [Line('Solve', tex(poly) + ' = 0'),
             Line('Difference of two squares: (%s)\u00b2 - %d\u00b2' % (lead, k),
                  '(%s + %d)(%s - %d) = 0' % (lead, k, lead, k)),
             Line('One of the brackets must be 0', '%s + %d = 0' % (lead, k) + OR + '%s - %d = 0' % (lead, k)),
             Line('Solve each one', roots_line([F(-k, m), F(k, m)]))]
    return made(lines, lines[-1].tex, {'roots': (plain(poly), [F(-k, m), F(k, m)])})


def a_not_1(rng):
    while True:
        p, q = rng.randint(1, 3), rng.randint(2, 5)
        a, b = nonzero(rng, 7), nonzero(rng, 7)
        if math.gcd(p, abs(a)) == 1 and math.gcd(q, abs(b)) == 1 and p * b + q * a:
            break
    poly = [Term(p * q, X2), Term(p * b + q * a, X), Term(a * b)]
    first, second = tex([Term(p, X), Term(a)]), tex([Term(q, X), Term(b)])
    roots = [F(-a, p), F(-b, q)]
    lines = [Line('Solve', tex(poly) + ' = 0'),
             Line('Factorise (split the middle term)', '(%s)(%s) = 0' % (first, second)),
             Line('One of the brackets must be 0', '%s = 0' % first + OR + '%s = 0' % second),
             Line('Solve each one', roots_line(roots))]
    return made(lines, lines[-1].tex, {'roots': (plain(poly), roots)})


def rearrange(rng):
    while True:
        p, q = two_numbers(rng)
        if p * q:
            break
    s, product = p + q, p * q
    poly = [Term(1, X2), Term(s, X), Term(product)]
    form = rng.choice(('move_number', 'bracket', 'move_x'))
    if form == 'move_number':
        given, step = '%s = %d' % (tex([Term(1, X2), Term(s, X)]), -product), 'Get 0 on one side'
    elif form == 'bracket':
        given = 'x(%s) = %d' % (tex([Term(1, X), Term(s)]), -product)
        step = 'Expand the bracket, then get 0 on one side'
    else:
        given, step = 'x^{2} = %s' % tex([Term(-s, X), Term(-product)]), 'Move every term to the left'
    first, second = tex([Term(1, X), Term(p)]), tex([Term(1, X), Term(q)])
    lines = [Line('Solve', given),
             Line(step, tex(poly) + ' = 0'),
             Line('Factorise: two numbers that multiply to %d and add to %d' % (product, s),
                  '(%s)(%s) = 0' % (first, second)),
             Line('Solve each one', roots_line([-p, -q]))]
    return made(lines, lines[-1].tex, {'roots': (plain(poly), [-p, -q])})


def formula(rng):
    while True:
        a, b, c = rng.randint(1, 4), nonzero(rng), nonzero(rng)
        d = b * b - 4 * a * c
        if d > 0 and math.isqrt(d) ** 2 != d:
            break
    poly = [Term(a, X2), Term(b, X), Term(c)]
    roots = [(-b + math.sqrt(d)) / (2 * a), (-b - math.sqrt(d)) / (2 * a)]
    shown = [numbers.money(F(root)) for root in roots]
    lines = [Line('Solve, giving answers to 2 decimal places', tex(poly) + ' = 0'),
             Line('Write down a, b and c', r'a = %d, \quad b = %d, \quad c = %d' % (a, b, c)),
             Line('The quadratic formula', r'x = \frac{-b \pm \sqrt{b^{2} - 4ac}}{2a}'),
             Line('Substitute',
                  r'x = \frac{-(%d) \pm \sqrt{(%d)^{2} - 4 \times %d \times %s}}{2 \times %d}'
                  % (b, b, a, algebra.number_tex(c), a)),
             Line('Work out the part under the square root', r'b^{2} - 4ac = %d' % d),
             Line('Write both answers', r'x = \frac{%d \pm \sqrt{%d}}{%d}' % (-b, d, 2 * a)),
             Line('To 2 decimal places', 'x = %s' % shown[0] + OR + 'x = %s' % shown[1])]
    return made(lines, lines[-1].tex, {'roots': (plain(poly), roots)})


ROOT_WORDS = {2: 'two real roots', 1: 'one repeated root', 0: 'no real roots'}


def discriminant(rng):
    wanted = rng.choice((2, 2, 1, 0, 0))
    while True:
        a = rng.randint(1, 4)
        if wanted == 1:
            h = nonzero(rng, 6)
            b, c = 2 * a * h, a * h * h
        else:
            b, c = nonzero(rng), nonzero(rng)
        d = b * b - 4 * a * c
        if (wanted == 2 and d > 0) or (wanted == 0 and d < 0) or wanted == 1:
            break
    poly = [Term(a, X2), Term(b, X), Term(c)]
    count = 2 if d > 0 else 1 if d == 0 else 0
    sign, verdict = {2: ('>', 'Positive: two roots'), 1: ('=', 'Zero: one repeated root'),
                     0: ('<', 'Negative: no real roots')}[count]
    lines = [Line('How many real roots?', tex(poly) + ' = 0'),
             Line('Write down a, b and c', r'a = %d, \quad b = %d, \quad c = %d' % (a, b, c)),
             Line('Work out the discriminant',
                  r'b^{2} - 4ac = (%d)^{2} - 4 \times %d \times %s = %d' % (b, a, algebra.number_tex(c), d)),
             Line(verdict, r'%d %s 0' % (d, sign))]
    lowest = F(c) - F(b * b, 4 * a)                 # the curve's minimum value, the other route
    expected = 2 if lowest < 0 else 1 if lowest == 0 else 0
    return made(lines, r'\text{%s}' % ROOT_WORDS[count], {'got': count, 'expected': expected})


def problems(rng):
    """Stretch: form a quadratic from a context, solve it, and reject the
    root that cannot be the answer."""
    if rng.random() < 0.5:
        while True:
            r, s = rng.randint(3, 12), -rng.randint(1, 15)
            a = rng.randint(1, 9)
            b = -(r + s) - a
            area = a * b - r * s
            if (area > 0 and b != 0 and r + a > 0 and r + b > 0
                    and s + a < 0 and s + b < 0):
                break
        poly = [Term(1, X2), Term(-(r + s), X), Term(r * s)]
        side1, side2 = tex([Term(1, X), Term(a)]), tex([Term(1, X), Term(b)])
        expanded = [Term(1, X2), Term(a + b, X), Term(a * b)]
        lines = [Line('A rectangle is (%s) cm long and (%s) cm wide. Its area is %d cm\u00b2. '
                      'Find x.' % (side1, side2, area)),
                 Line('Area = length \u00d7 width', '(%s)(%s) = %d' % (side1, side2, area)),
                 Line('Expand', '%s = %d' % (tex(expanded), area)),
                 Line('Make one side 0', tex(poly) + ' = 0'),
                 Line('Factorise', '(%s)(%s) = 0' % (tex([Term(1, X), Term(-r)]), tex([Term(1, X), Term(-s)]))),
                 Line('Solve each bracket', roots_line([r, s])),
                 Line('x = %d would make both sides negative, so' % s, 'x = %d' % r)]
        discriminant_value = (a + b) ** 2 - 4 * (a * b - area)
        expected = (-(a + b) + math.isqrt(discriminant_value)) // 2
        return made(lines, 'x = %d' % r, {'roots': (plain(poly), [r, s]), 'got': r,
                                           'expected': expected})
    n = rng.randint(4, 20)
    product = n * (n + 1)
    poly = [Term(1, X2), Term(1, X), Term(-product)]
    lines = [Line('Two consecutive positive whole numbers multiply to %d. Find them.' % product),
             Line('Call them x and x + 1', 'x(x + 1) = %d' % product),
             Line('Expand and make one side 0', tex(poly) + ' = 0'),
             Line('Factorise: two numbers that multiply to -%d and add to 1' % product,
                  '(x - %d)(x + %d) = 0' % (n, n + 1)),
             Line('Solve each bracket', roots_line([n, -(n + 1)])),
             Line('They must be positive, so x = %d' % n, r'%d \text{ and } %d' % (n, n + 1))]
    return made(lines, '%d and %d' % (n, n + 1),
                {'roots': (plain(poly), [n, -(n + 1)]), 'got': n, 'expected': math.isqrt(product)})
# --- Facts (editable) ---------------------------------------------------------

FACTS = [
    Fact('Solving by factorising',
         r'Get $0$ on one side, factorise, then set each factor to $0$: '
         r'$(x - 2)(x + 5) = 0$ gives $x = 2$ or $x = -5$.'),
    Fact('Common factor', r'$x^{2} + 5x = x(x + 5)$: one root is always $0$.'),
    Fact('Difference of two squares', r'$a^{2} - b^{2} = (a + b)(a - b)$: $4x^{2} - 9 = (2x + 3)(2x - 3)$.'),
    Fact('Rearrange first', r'Never divide by $x$: you lose the root $x = 0$. Get $0$ on one side '
                            r'instead.'),
    Fact('The quadratic formula', r'$x = \frac{-b \pm \sqrt{b^{2} - 4ac}}{2a}$'),
    Fact('The discriminant',
         r'$b^{2} - 4ac$: positive gives two roots, $0$ gives one, negative gives none.'),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='quadratics',
    title='Solving quadratics',
    area='Algebra',
    keywords=('quadratics', 'solve', 'factorise', 'factorising', 'difference of two squares',
              'quadratic formula', 'discriminant', 'roots', 'how many roots', 'rearrange'),
    intro='Get 0 on one side, then factorise or use the formula.',
    facts=FACTS,
    stages=[
        Stage('factorising', 'Solve by factorising',
              r'Two numbers that multiply to the number and add to the $x$ number. Then each '
              r'bracket equals $0$.',
              factorising),
        Stage('special', 'Common factor and squares',
              r'No number term: take out $x$. Square minus square: $(a + b)(a - b)$.',
              special),
        Stage('a_not_1', 'When a is not 1',
              r'Factorise by splitting the middle term, then set each bracket to $0$. The '
              r'answers can be fractions.',
              a_not_1),
        Stage('rearrange', 'Rearrange first',
              r'Expand any brackets and get $0$ on one side before factorising.',
              rearrange),
        Stage('formula', 'The formula',
              r'Write down $a$, $b$ and $c$, substitute carefully with brackets, and work out '
              r'$b^{2} - 4ac$ first.',
              formula),
        Stage('discriminant', 'How many roots',
              r'Only the discriminant: positive two, zero one, negative none.',
              discriminant),
        Stage('problems', 'Stretch',
              r'Turn a context into a quadratic, solve it, then decide which root makes sense: '
              r'lengths and counts cannot be negative.',
              problems),
    ])
