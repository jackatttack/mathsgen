"""Straight-line graphs: plotting, reading y = mx + c, gradient, midpoint,
finding equations, parallel and perpendicular lines.

Every problem carries meta['on_line'] = (m, c, points): tests check each
point the problem used satisfies the final y = mx + c exactly. Plotted
problems carry a lesson.Plot the Lesson page draws as a live graph.
"""
from fractions import Fraction as F

from ..lesson import Fact, Lesson, Line, Plot, Problem, Stage, Worked
from ..numbers import frac_tex, paren_tex

GRADIENTS = [F(value) for value in (1, 2, 3, 4, -1, -2, -3)] + [F(1, 2), F(-1, 2), F(1, 3), F(2, 3), F(-1, 3)]
WHOLE_GRADIENTS = [F(value) for value in (1, 2, 3, 4, 5, -1, -2, -3, -4)]


# --- Writing lines and points -------------------------------------------------

def line_tex(m, c):
    """y = mx + c's right-hand side: 3x - 2, -x, \\frac{1}{2}x + 4, 5."""
    m, c = F(m), F(c)
    if m == 0:
        return frac_tex(c)
    lead = 'x' if m == 1 else '-x' if m == -1 else frac_tex(m) + 'x'
    if c == 0:
        return lead
    return '%s %s %s' % (lead, '+' if c > 0 else '-', frac_tex(abs(c)))


def line_text(m, c):
    """The same line as text the graph reads: (1/2)*x + (3)."""
    return '(%s)*x + (%s)' % (F(m), F(c))


def point_tex(x, y):
    return '(%s, %s)' % (frac_tex(x), frac_tex(y))


def nonzero(rng, low=-6, high=6):
    return rng.choice([value for value in range(low, high + 1) if value])


def x_multiple(rng, m, low=-6, high=6):
    """An x that keeps m * x whole."""
    step = F(m).denominator
    return rng.choice([value for value in range(low, high + 1) if value % step == 0])


def made(lines, m, c, points, figure=None, extra=None):
    answer = lines[-1].tex
    meta = {'on_line': (F(m), F(c), [(F(x), F(y)) for x, y in points])}
    meta.update(extra or {})
    return Problem(statement=lines[0].tex or lines[0].say, answer=answer,
                   solution=Worked(lines, answer), meta=meta, figure=figure)


def plot_of(lines_mc, around=(), square=False):
    """A Plot of one or more lines, framed around the given points."""
    xs = [x for x, _ in around] or [0]
    low, high = min(min(xs), -2) - 3, max(max(xs), 2) + 3
    curves = [line_text(m, c) for m, c in lines_mc]
    title = ',  '.join('y = %s' % line_tex(m, c).replace('\\frac', '').replace('{', '')
                       .replace('}', '/').rstrip('/') for m, c in lines_mc)
    return Plot(curves, x=(int(low), int(high)), title=title, square=square)


def find_c_lines(m, x, y):
    """Lines for substituting a point into y = mx + c and solving for c."""
    c = F(y) - F(m) * F(x)
    return c, [
        Line('Put the point in: x = %s, y = %s' % (x, y),
             r'%s = %s \times %s + c' % (frac_tex(y), frac_tex(m), paren_tex(x))),
        Line('Work out c', r'%s = %s + c \;\Rightarrow\; c = %s'
             % (frac_tex(y), frac_tex(F(m) * F(x)), frac_tex(c)))]


# --- Stages -------------------------------------------------------------------

def plotting(rng):
    m = rng.choice([F(1), F(2), F(3), F(-1), F(-2), F(1, 2), F(-1, 2)])
    c = F(rng.randint(-4, 5))
    xs = [-2, -1, 0, 1, 2, 3]
    ys = [m * x + c for x in xs]
    table = (r'\begin{array}{c|cccccc} x & %s \\ \hline y & %s \end{array}'
             % (' & '.join(str(x) for x in xs), ' & '.join(frac_tex(y) for y in ys)))
    lines = [Line('Plot the line', 'y = ' + line_tex(m, c)),
             Line('Choose some x values and work out y for each one', table),
             Line('Check one: put x = 2 in',
                  r'y = %s \times 2 %s %s = %s' % (frac_tex(m), '+' if c >= 0 else '-',
                                                  frac_tex(abs(c)), frac_tex(m * 2 + c))),
             Line('Plot the points and join them with a ruler. It crosses the y axis at c',
                  r'\text{crosses the } y \text{ axis at } (0, %s)' % frac_tex(c))]
    figure = plot_of([(m, c)], around=list(zip(xs, ys)))
    return made(lines, m, c, list(zip(xs, ys)), figure)


def gradient_intercept(rng):
    form = rng.choice(('standard', 'swapped', 'scaled', 'general', 'general'))
    lines = []
    if form in ('standard', 'swapped', 'scaled'):
        m, c = rng.choice(WHOLE_GRADIENTS), F(nonzero(rng, -9, 9))
        if form == 'standard':
            lines.append(Line('Find the gradient and the y-intercept', 'y = ' + line_tex(m, c)))
        elif form == 'swapped':
            given = '%s %s %s' % (frac_tex(c), '+' if m > 0 else '-',
                                  ('x' if abs(m) == 1 else frac_tex(abs(m)) + 'x'))
            lines += [Line('Find the gradient and the y-intercept', 'y = ' + given),
                      Line('Write the x term first', 'y = ' + line_tex(m, c))]
        else:
            k = rng.randint(2, 4)
            lines += [Line('Find the gradient and the y-intercept',
                           '%dy = %s' % (k, line_tex(k * m, k * c))),
                      Line('Divide every term by %d to get y on its own' % k,
                           'y = ' + line_tex(m, c))]
        points = [(0, c), (1, m + c)]
    else:
        a, b = nonzero(rng, -5, 5), rng.randint(1, 5)
        d = nonzero(rng, -12, 12)
        m, c = F(-a, b), F(d, b)
        x_part = 'x' if a == 1 else '-x' if a == -1 else '%dx' % a
        b_part = 'y' if b == 1 else '%dy' % b
        lines += [Line('Find the gradient and the y-intercept', '%s + %s = %d' % (x_part, b_part, d)),
                  Line('Move the x term to the other side',
                       '%s = %s' % (b_part, line_tex(-a, d)))]
        if b != 1:
            lines.append(Line('Divide every term by %d' % b, 'y = ' + line_tex(m, c)))
        points = [(x, (d - a * x) / F(b)) for x in (0, 1, 2)]
    lines += [Line('Compare with y = mx + c', r'm = %s, \quad c = %s' % (frac_tex(m), frac_tex(c))),
              Line('Answer', r'\text{gradient } %s, \quad y\text{-intercept } (0, %s)'
                   % (frac_tex(m), frac_tex(c)))]
    return made(lines, m, c, points)


def two_point_pair(rng, whole=False):
    while True:
        x1, x2 = rng.randint(-6, 6), rng.randint(-6, 6)
        y1, y2 = rng.randint(-8, 8), rng.randint(-8, 8)
        if x1 == x2 or (x1, y1) == (x2, y2):
            continue
        m = F(y2 - y1, x2 - x1)
        if whole and m.denominator != 1:
            continue
        if m == 0 and rng.random() < 0.8:
            continue
        return x1, y1, x2, y2, m


def gradient_lines(x1, y1, x2, y2):
    m = F(y2 - y1, x2 - x1)
    rise, run = y2 - y1, x2 - x1
    working = r'm = \frac{%d - %s}{%d - %s} = \frac{%d}{%d}' % (y2, paren_tex(y1), x2, paren_tex(x1),
                                                              rise, run)
    if (m.numerator, m.denominator) != (rise, run):     # it simplifies, or the sign moves up
        working += ' = ' + frac_tex(m)
    return m, [Line('Gradient = change in y \u00f7 change in x',
                    r'm = \frac{y_2 - y_1}{x_2 - x_1}'),
               Line('Substitute the coordinates', working)]


def gradient_two_points(rng):
    x1, y1, x2, y2, m = two_point_pair(rng)
    c = F(y1) - m * x1
    lines = [Line('Find the gradient of the line through %s and %s'
                  % (point_tex(x1, y1), point_tex(x2, y2)),
                  r'%s \text{ and } %s' % (point_tex(x1, y1), point_tex(x2, y2)))]
    m, working = gradient_lines(x1, y1, x2, y2)
    lines += working + [Line('Answer', 'm = ' + frac_tex(m))]
    figure = plot_of([(m, c)], around=[(x1, y1), (x2, y2)])
    return made(lines, m, c, [(x1, y1), (x2, y2)], figure)


def midpoint(rng):
    x1, y1, x2, y2, m = two_point_pair(rng)
    mx, my = F(x1 + x2, 2), F(y1 + y2, 2)
    lines = [Line('Find the midpoint of %s and %s' % (point_tex(x1, y1), point_tex(x2, y2)),
                  r'%s \text{ and } %s' % (point_tex(x1, y1), point_tex(x2, y2))),
             Line('Add the x coordinates and halve; the same for y',
                  r'\left(\frac{x_1 + x_2}{2}, \frac{y_1 + y_2}{2}\right)'),
             Line('Substitute', r'\left(\frac{%d + %s}{2}, \frac{%d + %s}{2}\right)'
                  % (x1, paren_tex(x2), y1, paren_tex(y2))),
             Line('Answer', point_tex(mx, my))]
    c = F(y1) - m * x1
    return made(lines, m, c, [(x1, y1), (x2, y2), (mx, my)],
                extra={'got': (mx, my), 'expected': (x1 + F(x2 - x1, 2), y1 + F(y2 - y1, 2))})


def from_point(rng):
    m = rng.choice(GRADIENTS)
    x = x_multiple(rng, m)
    y = F(rng.randint(-8, 8))
    lines = [Line('Find the equation of the line with gradient %s through %s'
                  % (m, point_tex(x, y)),
                  r'm = %s, \quad %s' % (frac_tex(m), point_tex(x, y))),
             Line('Start from y = mx + c with the gradient in', 'y = %s + c' % line_tex(m, 0))]
    c, working = find_c_lines(m, x, y)
    lines += working + [Line('Answer', 'y = ' + line_tex(m, c))]
    return made(lines, m, c, [(x, y)], plot_of([(m, c)], around=[(x, y)]))


def through_two_points(rng):
    whole = rng.random() < 0.75
    x1, y1, x2, y2, m = two_point_pair(rng, whole=whole)
    lines = [Line('Find the equation of the line through %s and %s'
                  % (point_tex(x1, y1), point_tex(x2, y2)),
                  r'%s \text{ and } %s' % (point_tex(x1, y1), point_tex(x2, y2)))]
    m, working = gradient_lines(x1, y1, x2, y2)
    lines += working
    c, working = find_c_lines(m, x1, y1)
    lines += working + [Line('Answer', 'y = ' + line_tex(m, c))]
    return made(lines, m, c, [(x1, y1), (x2, y2)], plot_of([(m, c)], around=[(x1, y1), (x2, y2)]))


def parallel_perpendicular(rng):
    kind = rng.choice(('parallel', 'perpendicular', 'perpendicular'))
    m1 = rng.choice([F(value) for value in (1, 2, 3, 4, -1, -2, -3)] + [F(1, 2), F(-1, 2), F(-1, 3)])
    c1 = F(nonzero(rng, -6, 6))
    m2 = m1 if kind == 'parallel' else -1 / m1
    x = x_multiple(rng, m2)
    y = F(rng.randint(-6, 6))
    lines = [Line('Find the equation of the %s line through the point' % kind,
                  r'\text{%s to } y = %s \text{ through } %s' % (kind, line_tex(m1, c1), point_tex(x, y))),
             Line('The gradient of the given line', 'm = ' + frac_tex(m1))]
    if kind == 'parallel':
        lines.append(Line('Parallel lines have the same gradient', 'm = ' + frac_tex(m2)))
    else:
        lines.append(Line('Perpendicular: flip the gradient and change its sign',
                          r'm = %s \quad \text{since} \quad %s \times %s = -1'
                          % (frac_tex(m2), paren_tex(m1), paren_tex(m2))))
    c, working = find_c_lines(m2, x, y)
    lines += working + [Line('Answer', 'y = ' + line_tex(m2, c))]
    figure = plot_of([(m1, c1), (m2, c)], around=[(x, y)], square=True)
    return made(lines, m2, c, [(x, y)], figure,
                extra={'product': (kind, m1 * m2)})


def problems(rng):
    """Stretch: where two lines meet, or a perpendicular bisector."""
    if rng.random() < 0.5:
        x0, y0 = rng.randint(-5, 5), rng.randint(-6, 6)
        m1, m2 = rng.sample(WHOLE_GRADIENTS, 2)
        c1, c2 = y0 - m1 * x0, y0 - m2 * x0
        lines = [Line('Find where the two lines meet',
                      r'y = %s \quad \text{and} \quad y = %s' % (line_tex(m1, c1), line_tex(m2, c2))),
                 Line('Where they meet, the y values are equal',
                      '%s = %s' % (line_tex(m1, c1), line_tex(m2, c2))),
                 Line('Get the x terms on one side and solve',
                      r'%s = %s \;\Rightarrow\; x = %d' % (line_tex(m1 - m2, 0), frac_tex(c2 - c1), x0)),
                 Line('Put x into the first equation',
                      r'y = %s \times %s + %s = %s' % (frac_tex(m1), paren_tex(x0), paren_tex(c1),
                                                       frac_tex(y0))),
                 Line('They meet at', point_tex(x0, y0))]
        x_check = (c2 - c1) / (m1 - m2)
        figure = plot_of([(m1, c1), (m2, c2)], around=[(x0, y0)])
        return made(lines, m1, c1, [(x0, y0)], figure,
                    extra={'got': (F(x0), F(y0)), 'expected': (x_check, m2 * x_check + c2)})
    while True:
        x1, x2 = rng.randint(-6, 6), rng.randint(-6, 6)
        y1, y2 = rng.randint(-6, 6), rng.randint(-6, 6)
        if x1 != x2 and y1 != y2 and (x1 + x2) % 2 == 0 and (y1 + y2) % 2 == 0:
            break
    mx, my = F(x1 + x2, 2), F(y1 + y2, 2)
    lines = [Line('Find the equation of the perpendicular bisector of %s and %s'
                  % (point_tex(x1, y1), point_tex(x2, y2)),
                  r'%s \text{ and } %s' % (point_tex(x1, y1), point_tex(x2, y2))),
             Line('It passes through the midpoint',
                  r'\left(\frac{%d + %s}{2}, \frac{%d + %s}{2}\right) = %s'
                  % (x1, paren_tex(x2), y1, paren_tex(y2), point_tex(mx, my)))]
    m, working = gradient_lines(x1, y1, x2, y2)
    perpendicular = -1 / m
    lines += working
    lines.append(Line('Perpendicular: flip the gradient and change its sign',
                      'm = ' + frac_tex(perpendicular)))
    c, working = find_c_lines(perpendicular, mx, my)
    lines += working + [Line('Answer', 'y = ' + line_tex(perpendicular, c))]
    figure = plot_of([(m, y1 - m * x1), (perpendicular, c)], around=[(x1, y1), (x2, y2)], square=True)
    return made(lines, perpendicular, c, [(mx, my)], figure,
                extra={'product': ('perpendicular', m * perpendicular)})
# --- Facts (editable) ---------------------------------------------------------

RISE_RUN = (
    '<svg viewBox="0 0 230 150" width="230" height="150" xmlns="http://www.w3.org/2000/svg" '
    'fill="none" stroke="currentColor" stroke-width="2" font-family="-apple-system, sans-serif">'
    '<path d="M20 135 L210 15" stroke-width="2.5"/>'
    '<path d="M68 105 H158 V48" stroke-dasharray="5 4"/>'
    '<g fill="currentColor" stroke="none" font-size="13">'
    '<circle cx="68" cy="105" r="3.5"/><circle cx="158" cy="48" r="3.5"/>'
    '<text x="113" y="124" text-anchor="middle">change in x</text>'
    '<text x="166" y="82">change in y</text>'
    '</g></svg>')

FACTS = [
    Fact('y = mx + c', r'$m$ is the gradient (steepness) and $c$ is where the line crosses '
                       r'the $y$ axis, at $(0, c)$.'),
    Fact('Gradient', r'$m = \frac{\text{change in } y}{\text{change in } x} = '
                     r'\frac{y_2 - y_1}{x_2 - x_1}$', RISE_RUN),
    Fact('Positive and negative gradients',
         r'A positive gradient goes uphill from left to right; a negative one goes downhill. '
         r'A bigger number means steeper.'),
    Fact('Rearrange first', r'Get $y$ on its own before reading $m$ and $c$: $2y = 4x + 6$ '
                            r'gives $y = 2x + 3$.'),
    Fact('Finding c', r'Put a point on the line into $y = mx + c$: with $m = 2$ through '
                      r'$(3, 7)$, $7 = 6 + c$, so $c = 1$.'),
    Fact('Midpoint', r'$\left(\frac{x_1 + x_2}{2}, \frac{y_1 + y_2}{2}\right)$: the mean of '
                     r'the coordinates.'),
    Fact('Parallel lines', r'Parallel lines have the same gradient: $y = 3x + 1$ and '
                           r'$y = 3x - 4$.'),
    Fact('Perpendicular lines', r'Gradients multiply to $-1$: flip and change the sign. '
                                r'$2$ and $-\frac{1}{2}$ are perpendicular.'),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='straight_lines',
    title='Straight-line graphs',
    area='Graphs',
    keywords=('y = mx + c', 'gradient', 'intercept', 'midpoint', 'parallel', 'perpendicular',
              'coordinates', 'plot', 'table of values', 'equation of a line', 'linear graphs'),
    intro=r'Every straight line is $y = mx + c$: find $m$ and $c$ and you have it.',
    facts=FACTS,
    stages=[
        Stage('plotting', 'Plotting',
              r'Make a table of values: choose some $x$ values, work out $y$ for each, plot the '
              r'points and join them with a ruler.',
              plotting),
        Stage('gradient_intercept', 'Gradient and intercept',
              r'Get $y$ on its own, then read $m$ (the number in front of $x$) and $c$ (the '
              r'number on its own).',
              gradient_intercept),
        Stage('gradient_two_points', 'Gradient from two points',
              r'Change in $y$ divided by change in $x$: subtract in the same order on the top '
              r'and the bottom.',
              gradient_two_points),
        Stage('midpoint', 'Midpoint',
              r'Halfway between two points: add the $x$ coordinates and halve, then the same '
              r'for $y$.',
              midpoint),
        Stage('from_point', 'From a gradient and a point',
              r'Put the gradient into $y = mx + c$, then substitute the point to find $c$.',
              from_point),
        Stage('two_points', 'Through two points',
              r'Find the gradient first, then substitute either point to find $c$.',
              through_two_points),
        Stage('parallel_perpendicular', 'Parallel and perpendicular',
              r'Parallel: the same gradient. Perpendicular: flip the gradient and change its '
              r'sign, then find $c$ from the point.',
              parallel_perpendicular),
        Stage('problems', 'Stretch',
              r'Put the ideas together: where two lines meet (set the $y$ values equal), and the '
              r'perpendicular bisector (midpoint, then the perpendicular gradient).',
              problems),
    ])
