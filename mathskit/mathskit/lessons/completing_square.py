"""Completing the square and graphs: completing the square, the turning
point, a not 1, solving by completing the square, sketching, then Stretch.

Completed forms carry meta['forms'] (evaluated at random values against the
original); turning points carry got/expected (from -b/2a); solving carries
meta['roots']. Graph stages carry a lesson.Plot drawn live.
"""
import math
from fractions import Fraction as F

from ..algebra import Term
from ..lesson import Fact, Lesson, Line, Plot, Stage
from .quadratics import (X, X2, bracket, made, nonzero, plain, roots_line, squared_tex, surd_tex,
                         tex)


def curve_text(poly):
    return tex(poly).replace('^{2}', '^2')


# --- Stages -------------------------------------------------------------------

def complete(rng):
    h, c = nonzero(rng, 6), nonzero(rng, 12)
    k = c - h * h
    poly = [Term(1, X2), Term(2 * h, X), Term(c)]
    inner = tex([Term(1, X), Term(h)])
    answer = squared_tex(inner, k)
    lines = [Line('Complete the square', tex(poly)),
             Line('Halve the x number', r'\frac{%d}{2} = %d' % (2 * h, h)),
             Line('Write the bracket squared, then take away the extra %d' % (h * h),
                  r'(%s)^{2} - %d %s %d' % (inner, h * h, '+' if c > 0 else '-', abs(c))),
             Line('Tidy the numbers', answer)]
    return made(lines, answer, {'forms': [plain(poly), '(x+(%d))**2+(%d)' % (h, k)]})


def turning_point(rng):
    h, k = nonzero(rng, 6), rng.randint(-9, 9)
    c = h * h + k
    if c == 0:
        k += 1
        c += 1
    poly = [Term(1, X2), Term(2 * h, X), Term(c)]
    inner = tex([Term(1, X), Term(h)])
    lines = [Line('Find the turning point and the line of symmetry', 'y = ' + tex(poly)),
             Line('Complete the square', 'y = ' + squared_tex(inner, k)),
             Line('A square is never negative, so y is smallest when the bracket is 0', 'x = %d' % -h),
             Line('Then the bracket is gone', 'y = %d' % k),
             Line('Turning point (a minimum) and line of symmetry', r'(%d, %d), \quad x = %d' % (-h, k, -h))]
    vertex = F(-2 * h, 2)                               # -b / 2a, the other route
    expected = (vertex, vertex ** 2 + 2 * h * vertex + c)
    figure = Plot([curve_text(poly)], x=(-h - 6, -h + 6), y=(k - 2, k + 20),
                  title='y = ' + curve_text(poly))
    return made(lines, '(%d, %d)' % (-h, k),
                {'got': (F(-h), F(k)), 'expected': expected,
                 'forms': [plain(poly), '(x+(%d))**2+(%d)' % (h, k)]}, figure)


def complete_a(rng):
    a, h, c = rng.randint(2, 5), nonzero(rng, 5), nonzero(rng, 20)
    k = c - a * h * h
    poly = [Term(a, X2), Term(2 * a * h, X), Term(c)]
    inner = tex([Term(1, X), Term(h)])
    sign = '+' if c > 0 else '-'
    answer = '%d%s' % (a, squared_tex(inner, k))
    lines = [Line('Complete the square', tex(poly)),
             Line('Take %d out of the x terms only' % a,
                  r'%d(%s) %s %d' % (a, tex([Term(1, X2), Term(2 * h, X)]), sign, abs(c))),
             Line('Complete the square inside the bracket',
                  r'%d\left[(%s)^{2} - %d\right] %s %d' % (a, inner, h * h, sign, abs(c))),
             Line('Multiply %d back into the square bracket' % a,
                  r'%d(%s)^{2} - %d %s %d' % (a, inner, a * h * h, sign, abs(c))),
             Line('Tidy the numbers', answer)]
    return made(lines, answer, {'forms': [plain(poly), '%d*(x+(%d))**2+(%d)' % (a, h, k)]})


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
                  r'x = \frac{%d + %s}{2} = %d, \quad y = %d' % (r1, '(%d)' % r2 if r2 < 0 else r2, h, k)),
             Line('Turning point', '(%d, %d)' % (h, k))]
    top = 3 * (r2 - r1 + 3)
    figure = Plot([curve_text(poly)], x=(r1 - 3, r2 + 3), y=(k - 2, top + 2),
                  title='y = ' + curve_text(poly))
    return made(lines, 'Turning point (%d, %d)' % (h, k), {'roots': (plain(poly), [r1, r2])}, figure)


def problems(rng):
    """Stretch: show a quadratic is always positive, or find p and q from
    the turning point."""
    if rng.random() < 0.5:
        h, k = nonzero(rng, 6), rng.randint(1, 12)
        c = h * h + k
        poly = [Term(1, X2), Term(2 * h, X), Term(c)]
        inner = tex([Term(1, X), Term(h)])
        lines = [Line('Show that this is always positive', tex(poly)),
                 Line('Complete the square', squared_tex(inner, k)),
                 Line('A square is never negative', r'(%s)^{2} \geq 0' % inner),
                 Line('So the whole thing is at least %d, which is positive' % k,
                      r'%s \geq %d > 0' % (squared_tex(inner, k), k))]
        return made(lines, r'\text{smallest value } %d > 0' % k,
                    {'forms': [plain(poly), '(x+(%d))**2+(%d)' % (h, k)], 'got': k,
                     'expected': F(c) - F(4 * h * h, 4)})
    while True:
        h, k = nonzero(rng, 6), rng.randint(-9, 9)
        p, q = -2 * h, h * h + k
        if q:
            break
    expanded = 'y = %s' % tex([Term(1, X2), Term(-2 * h, X), Term(h * h)])
    if k:
        expanded += ' %s %d' % ('+' if k > 0 else '-', abs(k))
    lines = [Line('The curve y = x\u00b2 + px + q has its turning point at (%d, %d). Find p and q.' % (h, k)),
             Line('Write it in completed-square form from the turning point',
                  'y = ' + squared_tex(tex([Term(1, X), Term(-h)]), k)),
             Line('Expand the bracket', expanded),
             Line('Collect the numbers', 'y = ' + tex([Term(1, X2), Term(p, X), Term(q)])),
             Line('Compare', r'p = %d, \quad q = %d' % (p, q))]
    return made(lines, r'p = %d, \; q = %d' % (p, q),
                {'forms': ['x**2+(%d)*x+(%d)' % (p, q), '(x-(%d))**2+(%d)' % (h, k)],
                 'got': (F(-p, 2), F(q) - F(p * p, 4)), 'expected': (F(h), F(k))})
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
    Fact('Completing the square',
         r'$x^{2} + bx + c = \left(x + \frac{b}{2}\right)^{2} - \left(\frac{b}{2}\right)^{2} + c$: '
         r'$x^{2} + 6x + 1 = (x + 3)^{2} - 8$.'),
    Fact('Turning point',
         r'From $(x + p)^{2} + q$ the turning point is $(-p, q)$ and the line of symmetry is '
         r'$x = -p$.', PARABOLA),
    Fact('When a is not 1', r'Take $a$ out of the $x$ terms only, complete the square inside, then '
                            r'multiply $a$ back in: $2x^{2} + 12x + 5 = 2(x + 3)^{2} - 13$.'),
    Fact('Plus or minus',
         r'Square rooting gives two answers: $(x + 1)^{2} = 9$ gives $x + 1 = 3$ or $x + 1 = -3$.'),
    Fact('Sketching',
         r'Find the $y$ intercept ($x = 0$), the roots ($y = 0$) and the turning point, '
         r'halfway between the roots.'),
    Fact('Always positive', r'If $(x + p)^{2} + q$ has $q > 0$, it is never below $q$, so always '
                            r'positive.'),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='completing_square',
    title='Completing the square and graphs',
    area='Algebra',
    keywords=('complete the square', 'completing the square', 'turning point', 'vertex',
              'line of symmetry', 'minimum', 'parabola', 'sketch', 'quadratic graphs', 'surds'),
    intro='Write it as a square plus a number: the turning point, the solutions and the graph follow.',
    facts=FACTS,
    stages=[
        Stage('complete', 'Completing the square',
              r'Halve the $x$ number for the bracket, then take away its square: '
              r'$x^{2} + 6x + 1 = (x + 3)^{2} - 9 + 1$.',
              complete),
        Stage('turning_point', 'Turning point',
              r'From $(x + p)^{2} + q$: the turning point is $(-p, q)$, the line of symmetry $x = -p$.',
              turning_point),
        Stage('complete_a', 'When a is not 1',
              r'Take $a$ out of the $x$ terms, complete the square inside, multiply $a$ back in.',
              complete_a),
        Stage('solve_by_square', 'Solve by completing the square',
              r'Complete the square, move the number across, square root with $\pm$, then '
              r'get $x$ on its own. Leave surds in their simplest form.',
              solve_by_square),
        Stage('sketch', 'Sketching',
              r'Where it crosses the $y$ axis, where it crosses the $x$ axis, and the turning '
              r'point halfway between.',
              sketch),
        Stage('problems', 'Stretch',
              r'Use the completed square as an argument: its smallest value, or work backwards '
              r'from the turning point.',
              problems),
    ])
