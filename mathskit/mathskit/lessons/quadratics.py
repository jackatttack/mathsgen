"""Quadratics: solving by factorising, completing the square, the
formula, and sketching.

Solving problems carry meta['roots'] = (the quadratic as Python, [roots]);
tests/smoke_lessons.py checks every root makes it zero. Completing the
square carries meta['forms'] like the brackets lesson. Sketching carries a
lesson.Plot that the Lesson page draws as a live graph.
"""
import math
from fractions import Fraction as F

from .. import algebra, numbers
from ..algebra import Term, mono
from ..lesson import Fact, Lesson, Line, Plot, Problem, Stage, Worked

X = mono('x')
X2 = mono('x^2')
tex = algebra.tex
plain = algebra.plain
OR = r' \quad \text{or} \quad '


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


# --- Stages -------------------------------------------------------------------

def solve_factorising(rng):
    kind = rng.choice(('trinomial', 'trinomial', 'trinomial', 'trinomial', 'common', 'squares'))
    if kind == 'common':
        b = nonzero(rng)
        poly = [Term(1, X2), Term(b, X)]
        other = tex([Term(1, X), Term(b)])
        say, factored = 'Take out the common factor x', 'x(%s) = 0' % other
        zero = 'x = 0' + OR + '%s = 0' % other
        roots = [0, -b]
    elif kind == 'squares':
        k = rng.randint(1, 12)
        poly = [Term(1, X2), Term(-k * k)]
        say, factored = 'Difference of two squares', '(x + %d)(x - %d) = 0' % (k, k)
        zero = 'x + %d = 0' % k + OR + 'x - %d = 0' % k
        roots = [-k, k]
    else:
        while True:
            p, q = nonzero(rng), nonzero(rng)
            if p + q and p != q:
                break
        poly = [Term(1, X2), Term(p + q, X), Term(p * q)]
        first, second = tex([Term(1, X), Term(p)]), tex([Term(1, X), Term(q)])
        say = 'Factorise: two numbers that multiply to %d and add to %d' % (p * q, p + q)
        factored = '(%s)(%s) = 0' % (first, second)
        zero = '%s = 0' % first + OR + '%s = 0' % second
        roots = [-p, -q]
    lines = [Line('Solve', tex(poly) + ' = 0'),
             Line(say, factored),
             Line('One of the factors must be 0', zero),
             Line('Solve each one', roots_line(roots))]
    return made(lines, lines[-1].tex, {'roots': (plain(poly), roots)})


def solve_a_not_1(rng):
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


def complete_square(rng):
    h, c = nonzero(rng, 6), nonzero(rng, 12)
    k = c - h * h
    poly = [Term(1, X2), Term(2 * h, X), Term(c)]
    inner = tex([Term(1, X), Term(h)])
    answer = squared_tex(inner, k)
    lines = [Line('Complete the square', tex(poly)),
             Line('Halve the x number', r'\frac{%d}{2} = %d' % (2 * h, h)),
             Line('Write the bracket squared, then take away the extra %d' % (h * h),
                  r'(%s)^{2} - %d %s %d' % (inner, h * h, '+' if c > 0 else '-', abs(c))),
             Line('Tidy the numbers', answer),
             Line('So the turning point is', '(%d, %d)' % (-h, k))]
    return made(lines, answer, {'forms': [plain(poly), '(x+(%d))**2+(%d)' % (h, k)]})


def solve_by_square(rng):
    while True:
        h, c = nonzero(rng, 6), nonzero(rng, 15)
        s = h * h - c
        if s > 0:
            break
    poly = [Term(1, X2), Term(2 * h, X), Term(c)]
    inner = tex([Term(1, X), Term(h)])
    root = math.isqrt(s)
    lines = [Line('Solve by completing the square', tex(poly) + ' = 0'),
             Line('Complete the square', squared_tex(inner, -s) + ' = 0'),
             Line('Move the number to the other side', r'(%s)^{2} = %d' % (inner, s)),
             Line('Square root both sides: plus or minus', r'%s = \pm %s' % (inner, surd_tex(s)))]
    move = '%s %d from both sides' % ('Take' if h > 0 else 'Add', abs(h))
    if root * root == s:
        roots = [-h + root, -h - root]
        lines.append(Line(move, roots_line(roots)))
    else:
        roots = [-h + math.sqrt(s), -h - math.sqrt(s)]
        lines.append(Line(move, r'x = %d \pm %s' % (-h, surd_tex(s))))
    return made(lines, lines[-1].tex, {'roots': (plain(poly), roots)})


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


def sketch(rng):
    while True:
        r1, r2 = rng.randint(-7, 7), rng.randint(-7, 7)
        if r1 < r2 and (r1 + r2) % 2 == 0:
            break
    poly = [Term(1, X2), Term(-(r1 + r2), X), Term(r1 * r2)]
    h = (r1 + r2) // 2
    k = (h - r1) * (h - r2)
    factors = '%s%s = 0' % (bracket([Term(1, X), Term(-r1)]), bracket([Term(1, X), Term(-r2)]))
    lines = [Line('Sketch', 'y = ' + tex(poly)),
             Line('Where it crosses the y axis: put x = 0', 'y = %d' % (r1 * r2)),
             Line('Where it crosses the x axis: solve y = 0',
                  factors + r' \;\Rightarrow\; ' + roots_line([r1, r2])),
             Line('The turning point is halfway between the roots',
                  r'x = \frac{%d + %s}{2} = %d, \quad y = %d' % (r1, algebra.number_tex(r2), h, k)),
             Line('Turning point', '(%d, %d)' % (h, k))]
    top = 3 * (r2 - r1 + 3)
    curve = tex(poly).replace('^{2}', '^2')
    figure = Plot([curve], x=(r1 - 3, r2 + 3), y=(k - 2, top + 2), title='y = ' + curve)
    return made(lines, 'Turning point (%d, %d)' % (h, k),
                {'roots': (plain(poly), [r1, r2])}, figure)


# --- Facts (editable) ---------------------------------------------------------

PARABOLA = (
    '<svg viewBox="0 0 220 150" width="220" height="150" xmlns="http://www.w3.org/2000/svg" '
    'fill="none" stroke="currentColor" stroke-width="2" font-family="-apple-system, sans-serif">'
    '<path d="M10 70 H210 M110 10 V145" stroke-opacity="0.45"/>'
    '<path d="M40 15 Q110 175 180 15" stroke-width="2.5"/>'
    '<g fill="currentColor" stroke="none" font-size="13">'
    '<circle cx="66" cy="70" r="3.5"/><circle cx="154" cy="70" r="3.5"/>'
    '<circle cx="110" cy="95" r="3.5"/>'
    '<text x="56" y="62" text-anchor="middle">root</text>'
    '<text x="166" y="62" text-anchor="middle">root</text>'
    '<text x="110" y="118" text-anchor="middle">turning point</text>'
    '</g></svg>')

FACTS = [
    Fact('Solving by factorising',
         r'Get $0$ on one side, factorise, then set each factor to $0$: '
         r'$(x - 2)(x + 5) = 0$ gives $x = 2$ or $x = -5$.'),
    Fact('Completing the square',
         r'$x^{2} + bx + c = \left(x + \frac{b}{2}\right)^{2} - \left(\frac{b}{2}\right)^{2} + c$: '
         r'$x^{2} + 6x + 1 = (x + 3)^{2} - 8$.'),
    Fact('Turning point',
         r'From $(x + p)^{2} + q$ the turning point is $(-p, q)$.', PARABOLA),
    Fact('The quadratic formula', r'$x = \frac{-b \pm \sqrt{b^{2} - 4ac}}{2a}$'),
    Fact('The discriminant',
         r'$b^{2} - 4ac$: positive gives two roots, $0$ gives one, negative gives none.'),
    Fact('Plus or minus',
         r'Square rooting gives two answers: $(x + 1)^{2} = 9$ gives $x + 1 = 3$ or $x + 1 = -3$.'),
    Fact('Sketching',
         r'Find the $y$ intercept ($x = 0$), the roots ($y = 0$) and the turning point, '
         r'halfway between the roots.'),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='quadratics',
    title='Quadratics',
    area='Algebra',
    keywords=('complete the square', 'completing the square', 'quadratic formula',
              'discriminant', 'roots', 'turning point', 'parabola', 'solve', 'sketch',
              'factorise', 'surds'),
    intro='Solve them, complete the square, use the formula, and sketch the curve.',
    facts=FACTS,
    stages=[
        Stage('solve_factorising', 'Solve by factorising',
              r'Factorise, then one of the factors must be $0$: solve each one.',
              solve_factorising),
        Stage('solve_a_not_1', 'When a is not 1',
              r'Factorise by splitting the middle term, then set each bracket to $0$. The '
              r'answers can be fractions.',
              solve_a_not_1),
        Stage('complete_square', 'Completing the square',
              r'Halve the $x$ number for the bracket, then take away its square: '
              r'$x^{2} + 6x + 1 = (x + 3)^{2} - 9 + 1$.',
              complete_square),
        Stage('solve_by_square', 'Solve by completing the square',
              r'Complete the square, move the number across, square root with $\pm$, then '
              r'get $x$ on its own. Leave surds in their simplest form.',
              solve_by_square),
        Stage('formula', 'The formula',
              r'Write down $a$, $b$ and $c$, substitute carefully with brackets, and work out '
              r'$b^{2} - 4ac$ first.',
              formula),
        Stage('sketch', 'Sketching',
              r'Where it crosses the $y$ axis, where it crosses the $x$ axis, and the turning '
              r'point halfway between.',
              sketch),
    ])
