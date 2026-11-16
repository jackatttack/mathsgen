"""Probability basics: picking at random and the complement, probability
tables, expected outcomes, counting outcomes, sample spaces, then Stretch.
Venn diagrams and tree diagrams are their own lessons (venn.py, trees.py),
which share this file's helpers.

Every problem carries meta got (from the working) and expected (by another
route: counting what is not wanted, listing every outcome, a different
order of multiplying) for tests/smoke_lessons.py.
"""
import itertools
import math
from fractions import Fraction as F

from .. import diagrams
from ..lesson import Fact, Lesson, Line, Problem, Stage, Worked
from ..numbers import frac_tex

COLOURS = ('red', 'blue', 'green', 'yellow', 'white', 'black', 'purple')
SHORT_COLOURS = ('red', 'blue', 'green', 'pink')          # fit a tree's branch labels
ITEMS = ('counters', 'sweets', 'beads', 'marbles', 'balls')


# --- Helpers (shared with venn.py and trees.py) ---------------------------------

def and_list(words):
    return words[0] if len(words) == 1 else ', '.join(words[:-1]) + ' and ' + words[-1]


def dec(value):
    """An exact decimal as text: 0.35, 0.7, 0.343."""
    return ('%.4f' % float(value)).rstrip('0').rstrip('.')


def whole(value):
    return str(int(value)) if F(value).denominator == 1 else frac_tex(F(value))


def ptex(count, total):
    """count over total as TeX, then simplified after an = when it can be."""
    out = r'\frac{%d}{%d}' % (count, total)
    if F(count, total).denominator != total:
        out += ' = ' + frac_tex(F(count, total))
    return out


def made(lines, answer, got, expected, figure=None):
    return Problem(statement=lines[0].tex or lines[0].say, answer=answer,
                   solution=Worked(lines, answer), meta={'got': got, 'expected': expected},
                   figure=figure)


def spinner(rng):
    """A spinner's colours and probabilities: the known ones, then x (and 2x,
    sometimes). Hundredths that are multiples of 0.05, so decimals stay short."""
    count = rng.choice((3, 4))
    names = rng.sample(COLOURS, count)
    twice = rng.random() < 0.4
    while True:
        known = [rng.randrange(5, 45, 5) for _ in range(count - (2 if twice else 1))]
        left = 100 - sum(known)
        if twice and left >= 15 and left % 15 == 0:
            return names, [F(k, 100) for k in known], [F(left, 300), F(left, 150)]
        if not twice and 5 <= left <= 60:
            return names, [F(k, 100) for k in known], [F(left, 100)]


def table_working(names, known, unknowns):
    """The table as a Line, the lines that solve it, the asked probability
    and the asked colour (the last one: x, or 2x when there are two)."""
    twice = len(unknowns) == 2
    shown = [dec(value) for value in known] + (['x', '2x'] if twice else ['x'])
    table = Line('The table', r'\begin{array}{|l|%s|}\hline \text{Colour} & %s \\ \hline P & %s '
                              r'\\ \hline\end{array}'
                 % ('|'.join('c' * len(names)), ' & '.join(r'\text{%s}' % name for name in names),
                    ' & '.join(shown)))
    asked = names[-1]
    known_sum = sum(known)
    lines = [Line('The probabilities add up to 1',
                  r'%s + %s = 1' % (' + '.join(dec(value) for value in known),
                                    'x + 2x' if twice else 'x'))]
    if twice:
        rest = 1 - known_sum
        x = rest / 3
        got = 2 * x
        lines += [Line('Collect the x terms and take the known ones from 1',
                       r'3x = 1 - %s = %s' % (dec(known_sum), dec(rest))),
                  Line('Divide by 3', r'x = %s' % dec(x)),
                  Line('%s is the 2x one' % asked.capitalize(),
                       r'P(\text{%s}) = 2 \times %s = %s' % (asked, dec(x), dec(got)))]
    else:
        got = 1 - known_sum
        lines.append(Line('Take the known ones from 1',
                          r'x = 1 - %s = %s' % (dec(known_sum), dec(got))))
    return table, lines, got, asked


# --- Stages -------------------------------------------------------------------

def selection(rng):
    count = rng.choice((2, 3, 3, 4))
    colours = rng.sample(COLOURS, count)
    amounts = [rng.randint(1, 9) for _ in colours]
    total = sum(amounts)
    which = rng.randrange(count)
    target, wanted = colours[which], amounts[which]
    listing = and_list(['%d %s' % pair for pair in zip(amounts, colours)])
    item = rng.choice(ITEMS)
    counted = Line('Count everything in the bag', r'%s = %d' % (' + '.join(map(str, amounts)), total))
    if rng.random() < 0.4:
        got = 1 - F(wanted, total)
        lines = [Line('A bag holds %s %s. One is taken at random. What is the probability it is '
                      'not %s?' % (listing, item, target)),
                 counted,
                 Line('First the probability it is %s' % target,
                      r'P(\text{%s}) = \frac{%d}{%d}' % (target, wanted, total)),
                 Line('Not %s: take that from 1' % target,
                      r'P(\text{not %s}) = 1 - \frac{%d}{%d} = %s'
                      % (target, wanted, total, ptex(total - wanted, total)))]
        expected = F(total - wanted, total)           # count the others straight off
    else:
        got = F(wanted, total)
        lines = [Line('A bag holds %s %s. One is taken at random. What is the probability it is '
                      '%s?' % (listing, item, target)),
                 counted,
                 Line('%d of them are %s' % (wanted, target),
                      r'P(\text{%s}) = %s' % (target, ptex(wanted, total)))]
        expected = 1 - F(total - wanted, total)
    return made(lines, frac_tex(got), got, expected)


def missing(rng):
    names, known, unknowns = spinner(rng)
    table, solving, got, asked = table_working(names, known, unknowns)
    lines = [Line('A spinner lands on one of %d colours. The table shows the probabilities. '
                  'Find the probability it lands on %s.' % (len(names), asked)), table] + solving
    return made(lines, dec(got), got, unknowns[-1])


def expected_outcomes(rng):
    if rng.random() < 0.5:
        setup, outcome, trials = rng.choice((('A biased coin lands on heads', 'heads', 'flips'),
                                             ('A spinner lands on red', 'reds', 'spins'),
                                             ('A player scores a penalty', 'goals', 'penalties')))
        d = rng.choice((4, 5, 10, 20))
        a = rng.choice([k for k in range(1, d) if math.gcd(k, d) == 1])
        p = F(a, d)
        n = d * rng.randint(3, 25)
        got = p * n
        lines = [Line('%s with probability %s. There are %d %s. How many %s would you expect?'
                      % (setup, dec(p), n, trials, outcome)),
                 Line('Expected number = probability times number of trials',
                      r'%s \times %d = %s' % (dec(p), n, whole(got)))]
        return made(lines, whole(got), got, (n // d) * a)
    m = rng.choice((20, 25, 40, 50, 80, 100, 200))
    k = rng.randint(1, m - 1)
    step = m // math.gcd(k, m)
    n = step * rng.randint(2, 40)
    while n <= m:
        n += step
    estimate = F(k, m)
    got = estimate * n
    lines = [Line('A drawing pin is dropped %d times and lands point up %d times. Estimate how many '
                  'times it would land point up in %d drops.' % (m, k, n)),
             Line('Relative frequency estimates the probability',
                  r'P(\text{point up}) \approx %s' % ptex(k, m)),
             Line('Multiply by the number of drops',
                  r'%s \times %d = %s' % (frac_tex(estimate), n, whole(got)))]
    return made(lines, whole(got), got, F(n, m) * k)


MENUS = (('starters', 'mains', 'desserts'), ('tops', 'pairs of trousers', 'pairs of shoes'),
         ('breads', 'fillings', 'drinks'))
SPINNER_EVENTS = (('an even number', lambda k: k % 2 == 0),
                  ('a prime number', lambda k: k in (2, 3, 5)),
                  ('a number greater than 2', lambda k: k > 2))


def counting(rng):
    if rng.random() < 0.5:
        kinds = rng.choice(MENUS)
        kinds = kinds if rng.random() < 0.5 else kinds[:2]
        sizes = [rng.randint(2, 7) for _ in kinds]
        got = 1
        for size in sizes:
            got *= size
        lines = [Line('A menu has %s. Choosing one of each, how many different combinations are '
                      'there?' % and_list(['%d %s' % pair for pair in zip(sizes, kinds)])),
                 Line('Product rule: multiply the number of choices for each',
                      r'%s = %d' % (r' \times '.join(map(str, sizes)), got))]
        listed = len(list(itertools.product(*[range(size) for size in sizes])))
        return made(lines, str(got), got, listed)
    sides = rng.choice((4, 5, 6))
    face = rng.choice(('H', 'T'))
    words, test = rng.choice(SPINNER_EVENTS)
    outcomes = ['%s%d' % (coin, number) for coin in 'HT' for number in range(1, sides + 1)]
    wanted = [outcome for outcome in outcomes if outcome[0] == face and test(int(outcome[1:]))]
    side = 'heads' if face == 'H' else 'tails'
    lines = [Line('A coin is flipped and a fair spinner numbered 1 to %d is spun. List all the '
                  'outcomes and find the probability of %s and %s.' % (sides, side, words)),
             Line('List them in order: H with each number, then T',
                  r'\text{%s}' % ', '.join(outcomes)),
             Line('Count them', r'2 \times %d = %d \text{ outcomes}' % (sides, 2 * sides)),
             Line('The ones with %s and %s' % (side, words), r'\text{%s}' % ', '.join(wanted)),
             Line('Outcomes wanted over all outcomes', r'P = %s' % ptex(len(wanted), 2 * sides))]
    got = F(len(wanted), 2 * sides)
    numbers = sum(1 for number in range(1, sides + 1) if test(number))
    return made(lines, frac_tex(got), got, F(1, 2) * F(numbers, sides))


SPACE_OPERATIONS = {
    'sum': ('total', 'added', '+', lambda a, b: a + b),
    'product': ('product', 'multiplied', '\u00d7', lambda a, b: a * b),
    'difference': ('difference', 'taken from each other (bigger minus smaller)', '\u2212',
                   lambda a, b: abs(a - b)),
}


def sample_space(rng):
    dice = rng.random() < 0.6
    if dice:
        rows = cols = list(range(1, 7))
    else:
        rows = list(range(1, rng.choice((4, 5)) + 1))
        cols = list(range(1, rng.choice((3, 4, 5, 6)) + 1))
    noun, verb, symbol, combine = SPACE_OPERATIONS[rng.choice(('sum', 'sum', 'product', 'difference'))]
    values = [[combine(a, b) for b in cols] for a in rows]
    possible = sorted(set(value for row in values for value in row))
    total = len(rows) * len(cols)
    while True:
        target = rng.choice(possible)
        if rng.random() < 0.5:
            words, test = 'equal to %d' % target, (lambda value, t=target: value == t)
        else:
            words, test = 'greater than %d' % target, (lambda value, t=target: value > t)
        count = sum(1 for row in values for value in row if test(value))
        if 0 < count < total:
            break
    marked = [(i, j) for i in range(len(rows)) for j in range(len(cols)) if test(values[i][j])]
    if dice:
        setup = 'Two fair six-sided dice are rolled and the scores are %s.' % verb
    else:
        setup = ('Two fair spinners, numbered 1 to %d and 1 to %d, are spun and the scores are %s.'
                 % (len(rows), len(cols), verb))
    lines = [Line('%s Find the probability that the %s is %s.' % (setup, noun, words)),
             Line('Draw the sample space: every pair is equally likely',
                  r'%d \times %d = %d \text{ outcomes}' % (len(rows), len(cols), total)),
             Line('Count the outcomes where the %s is %s (shaded)' % (noun, words),
                  r'%d \text{ outcomes}' % count),
             Line('Outcomes wanted over all outcomes', r'P = %s' % ptex(count, total))]
    got = F(count, total)
    misses = sum(1 for a in rows for b in cols if not test(combine(a, b)))
    figure = diagrams.sample_space(rows, cols, values, marked, corner=symbol)
    return made(lines, frac_tex(got), got, 1 - F(misses, total), figure)


DICE_CONDITIONS = (('the total is even', lambda a, b: (a + b) % 2 == 0),
                   ('the total is greater than 7', lambda a, b: a + b > 7),
                   ('at least one dice shows a 6', lambda a, b: 6 in (a, b)),
                   ('the total is a multiple of 3', lambda a, b: (a + b) % 3 == 0))
DICE_EVENTS = (('it is a double', lambda a, b: a == b),
               ('the total is 8', lambda a, b: a + b == 8),
               ('one of the dice shows a 5', lambda a, b: 5 in (a, b)),
               ('the total is 10 or more', lambda a, b: a + b >= 10))


def problems(rng):
    """Stretch: solve a probability table, then use it to predict; or a
    sample space where only the outcomes meeting a condition count."""
    if rng.random() < 0.5:
        names, known, unknowns = spinner(rng)
        spins = 20 * rng.randint(2, 15)
        table, solving, chance, asked = table_working(names, known, unknowns)
        got = chance * spins
        lines = ([Line('The table shows the probabilities for a spinner. It is spun %d times. How '
                       'many times would you expect it to land on %s?' % (spins, asked)), table]
                 + solving
                 + [Line('Expected number = probability times number of spins',
                         r'%s \times %d = %s' % (dec(chance), spins, whole(got)))])
        return made(lines, whole(got), got, unknowns[-1] * spins)
    while True:
        condition_words, condition = rng.choice(DICE_CONDITIONS)
        event_words, event = rng.choice(DICE_EVENTS)
        inside = [(a, b) for a in range(1, 7) for b in range(1, 7) if condition(a, b)]
        wanted = [cell for cell in inside if event(*cell)]
        if 0 < len(wanted) < len(inside):
            break
    lines = [Line('Two fair dice are rolled. Given that %s, find the probability that %s.'
                  % (condition_words, event_words)),
             Line('Only the outcomes where %s count now (shaded)' % condition_words,
                  r'%d \text{ outcomes}' % len(inside)),
             Line('Of those, count where %s' % event_words, r'%d \text{ outcomes}' % len(wanted)),
             Line('Out of the shaded outcomes, not all 36', r'P = %s' % ptex(len(wanted), len(inside)))]
    got = F(len(wanted), len(inside))
    expected = F(len(wanted), 36) / F(len(inside), 36)
    values = [[a + b for b in range(1, 7)] for a in range(1, 7)]
    figure = diagrams.sample_space(list(range(1, 7)), list(range(1, 7)), values,
                                   [(a - 1, b - 1) for a, b in inside])
    return made(lines, frac_tex(got), got, expected, figure)
# --- Facts (editable) ---------------------------------------------------------

FACTS = [
    Fact('Probability', r'When every outcome is equally likely, $P = \dfrac{\text{outcomes wanted}}'
                        r'{\text{all outcomes}}$. It runs from $0$ (impossible) to $1$ (certain).'),
    Fact('Not happening', r'$P(\text{not } A) = 1 - P(A)$.'),
    Fact('Adding to 1', r'The probabilities of all the outcomes add up to $1$: use that to find a '
                        r'missing one.'),
    Fact('Expected outcomes', r'Expected number $=$ probability $\times$ number of trials: '
                              r'$0.3 \times 200 = 60$.'),
    Fact('Relative frequency', r'Times it happened $\div$ number of trials. More trials give a better '
                               r'estimate.'),
    Fact('Product rule', r'$3$ starters and $4$ mains make $3 \times 4 = 12$ different meals.'),
    Fact('Sample space', r'List every pair in a grid, then count: two dice give $36$ outcomes.',
         diagrams.sample_space([1, 2, 3], [1, 2, 3], [[a + b for b in (1, 2, 3)] for a in (1, 2, 3)],
                               [(0, 2), (1, 1), (2, 0)])),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='probability',
    title='Probability',
    area='Probability',
    keywords=('probability', 'chance', 'complement', 'expected', 'relative frequency',
              'sample space', 'two dice', 'product rule', 'listing outcomes', 'given that'),
    intro='Count what you want over everything possible.',
    facts=FACTS,
    stages=[
        Stage('selection', 'Picking at random',
              r'Outcomes wanted over all outcomes. For "not", take the probability from $1$.',
              selection),
        Stage('missing', 'Probability tables',
              r'All the probabilities add up to $1$: write that as an equation and solve it.',
              missing),
        Stage('expected', 'Expected outcomes',
              r'Probability $\times$ number of trials. Relative frequency estimates the probability.',
              expected_outcomes),
        Stage('counting', 'Counting outcomes',
              r'List outcomes in order so none are missed, or multiply the choices (product rule).',
              counting),
        Stage('sample_space', 'Sample spaces',
              r'Put every pair in a grid, shade the ones you want and count.',
              sample_space),
        Stage('problems', 'Stretch',
              r'Solve the table, then predict. "Given that" means only count the outcomes that '
              r'fit the condition.',
              problems),
    ])
