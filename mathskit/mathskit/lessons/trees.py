"""Tree diagrams: independent events, with and without replacement,
dependent events, reading a missing branch back, at least one, then
Stretch.

Every two-stage problem draws its tree (mathskit/diagrams.py). Problems
carry meta got (along and between the branches) and expected (one minus
the branches not wanted, combinations, a difference of powers) for
tests/smoke_lessons.py.
"""
import math
from fractions import Fraction as F

from .. import diagrams
from ..lesson import Fact, Lesson, Line, Stage
from ..numbers import frac_tex
from .probability import COLOURS, ITEMS, SHORT_COLOURS, dec, made, ptex

# yes branch, no branch, the event in words, one trial
REPEATED = (('Rain', 'Dry', 'it rains', 'day'),
            ('Late', 'On time', 'the bus is late', 'day'),
            ('Win', 'Lose', 'the team wins', 'match'),
            ('Hit', 'Miss', 'Sam hits the target', 'throw'))

# first yes and no, second yes and no, the first event, the second event
DEPENDENT = (('Rain', 'Dry', 'Late', 'On time', 'it rains', 'Ana is late'),
             ('Pass', 'Fail', 'Pass', 'Fail', 'Kim passes the theory test', 'she passes the practical test'),
             ('Win', 'Lose', 'Win', 'Lose', 'the team wins its first match', 'it wins its second match'))

ORDINALS = {2: 'second', 3: 'third', 4: 'fourth'}

TREE_ASKS = {'both': ((0, 0),), 'neither': ((1, 1),), 'exactly one': ((0, 1), (1, 0)),
             'at least one': ((0, 0), (0, 1), (1, 0))}


def tenth(rng):
    return F(rng.randint(1, 9), 10)


def branch_lines(chances, wanted, branches, show):
    """Multiply along each wanted branch, then add them when there are several."""
    lines = [Line('Multiply along each branch you want', r', \quad '.join(
        r'%s \times %s = %s' % (show(chances[0][i]), show(chances[1][i][j]), show(branches[(i, j)]))
        for i, j in wanted))]
    if len(wanted) > 1:
        lines.append(Line('Add the branches', r'%s = %s' % (
            ' + '.join(show(branches[key]) for key in wanted), show(sum(branches[key] for key in wanted)))))
    return lines


# --- Stages -------------------------------------------------------------------

def independent(rng):
    yes, no, event, trial = rng.choice(REPEATED)
    same = rng.random() < 0.5
    p1 = tenth(rng)
    p2 = p1 if same else tenth(rng)
    ask = rng.choice(sorted(TREE_ASKS))
    first = (p1, 1 - p1)
    second = (p2, 1 - p2)
    chances = (first, (second, second))
    branches = {(i, j): first[i] * second[j] for i in (0, 1) for j in (0, 1)}
    wanted = TREE_ASKS[ask]
    if same:
        question = ('The probability that %s is %s on each %s, independently. Find the probability '
                    'that it happens on %s of two %ss.' % (event, dec(p1), trial, ask, trial))
    else:
        question = ('The probability that %s on Saturday is %s, and on Sunday it is %s, independently. '
                    'Find the probability that it happens on %s of the two days.'
                    % (event, dec(p1), dec(p2), ask))
    lines = [Line(question),
             Line('Each pair of branches adds to 1', r'1 - %s = %s%s' % (
                 dec(p1), dec(1 - p1), '' if same else r', \quad 1 - %s = %s' % (dec(p2), dec(1 - p2))))]
    lines += branch_lines(chances, wanted, branches, dec)
    got = sum(branches[key] for key in wanted)
    expected = 1 - sum(value for key, value in branches.items() if key not in wanted)
    level2 = [(yes, dec(p2)), (no, dec(1 - p2))]
    figure = diagrams.tree([(yes, dec(p1)), (no, dec(1 - p1))], [level2, level2])
    return made(lines, dec(got), got, expected, figure)


REPLACEMENT_ASKS = ('both first', 'same', 'different', 'at least one second')


def bag(rng):
    first, second = rng.sample(SHORT_COLOURS, 2)
    r, b = rng.randint(2, 7), rng.randint(2, 7)
    ask = rng.choice(REPLACEMENT_ASKS)
    phrase = {'both first': 'both are %s' % first, 'same': 'both are the same colour',
              'different': 'they are different colours',
              'at least one second': 'at least one is %s' % second}[ask]
    wanted = {'both first': [(0, 0)], 'same': [(0, 0), (1, 1)], 'different': [(0, 1), (1, 0)],
              'at least one second': [(0, 1), (1, 0), (1, 1)]}[ask]
    return first, second, r, b, ask, phrase, wanted


def fraction_text(top, bottom):
    return '%d/%d' % (top, bottom)


def with_replacement(rng):
    first, second, r, b, ask, phrase, wanted = bag(rng)
    n = r + b
    item = rng.choice(ITEMS)
    pick = (F(r, n), F(b, n))
    branches = {(i, j): pick[i] * pick[j] for i in (0, 1) for j in (0, 1)}
    count = sum((r, b)[i] * (r, b)[j] for i, j in wanted)
    lines = [Line('A bag holds %d %s and %d %s %s. One is taken at random, put back, then a second '
                  'is taken. Find the probability that %s.' % (r, first, b, second, item, phrase)),
             Line('It goes back, so both picks are out of %d' % n,
                  r'P(\text{%s}) = \frac{%d}{%d}, \quad P(\text{%s}) = \frac{%d}{%d}'
                  % (first, r, n, second, b, n)),
             Line('Multiply along each branch you want', r', \quad '.join(
                 r'\frac{%d}{%d} \times \frac{%d}{%d} = \frac{%d}{%d}'
                 % ((r, b)[i], n, (r, b)[j], n, (r, b)[i] * (r, b)[j], n * n) for i, j in wanted))]
    if len(wanted) > 1:
        lines.append(Line('Add the branches', r'%s = %s' % (
            ' + '.join(r'\frac{%d}{%d}' % ((r, b)[i] * (r, b)[j], n * n) for i, j in wanted),
            ptex(count, n * n))))
    else:
        lines.append(Line('Simplify', r'P = %s' % ptex(count, n * n)))
    got = F(count, n * n)
    expected = 1 - sum(value for key, value in branches.items() if key not in wanted)
    level = [(first.capitalize(), fraction_text(r, n)), (second.capitalize(), fraction_text(b, n))]
    return made(lines, frac_tex(got), got, expected, diagrams.tree(level, [level, level]))


def without_replacement(rng):
    first, second, r, b, ask, phrase, wanted = bag(rng)
    n = r + b
    item = rng.choice(ITEMS)
    tops = {(0, 0): (r, r - 1), (0, 1): (r, b), (1, 0): (b, r), (1, 1): (b, b - 1)}
    below = n * (n - 1)
    count = sum(tops[key][0] * tops[key][1] for key in wanted)
    lines = [Line('A bag holds %d %s and %d %s %s. Two are taken at random without replacement. '
                  'Find the probability that %s.' % (r, first, b, second, item, phrase)),
             Line('The first pick is out of %d; the second is out of %d, one fewer' % (n, n - 1),
                  r'P(\text{%s first}) = \frac{%d}{%d}, \quad P(\text{%s first}) = \frac{%d}{%d}'
                  % (first, r, n, second, b, n)),
             Line('Multiply along each branch you want', r', \quad '.join(
                 r'\frac{%d}{%d} \times \frac{%d}{%d} = \frac{%d}{%d}'
                 % (tops[key][0], n, tops[key][1], n - 1, tops[key][0] * tops[key][1], below)
                 for key in wanted))]
    if len(wanted) > 1:
        lines.append(Line('Add the branches', r'%s = %s' % (
            ' + '.join(r'\frac{%d}{%d}' % (tops[key][0] * tops[key][1], below) for key in wanted),
            ptex(count, below))))
    else:
        lines.append(Line('Simplify', r'P = %s' % ptex(count, below)))
    pairs = math.comb(n, 2)
    expected = {'both first': F(math.comb(r, 2), pairs),
                'same': F(math.comb(r, 2) + math.comb(b, 2), pairs),
                'different': F(r * b, pairs),
                'at least one second': 1 - F(math.comb(r, 2), pairs)}[ask]
    figure = diagrams.tree(
        [(first.capitalize(), fraction_text(r, n)), (second.capitalize(), fraction_text(b, n))],
        [[(first.capitalize(), fraction_text(r - 1, n - 1)), (second.capitalize(), fraction_text(b, n - 1))],
         [(first.capitalize(), fraction_text(r, n - 1)), (second.capitalize(), fraction_text(b - 1, n - 1))]])
    got = F(count, below)
    return made(lines, frac_tex(got), got, expected, figure)


def dependent(rng):
    yes1, no1, yes2, no2, first, second = rng.choice(DEPENDENT)
    p, a, b = tenth(rng), tenth(rng), tenth(rng)
    total = rng.random() < 0.6
    chances = ((p, 1 - p), ((a, 1 - a), (b, 1 - b)))
    branches = {(i, j): chances[0][i] * chances[1][i][j] for i in (0, 1) for j in (0, 1)}
    wanted = ((0, 0), (1, 0)) if total else ((0, 0),)
    ask = second if total else '%s and %s' % (first, second)
    lines = [Line('The probability that %s is %s. If so, the probability that %s is %s; if not, it '
                  'is %s. Find the probability that %s.' % (first, dec(p), second, dec(a), dec(b), ask)),
             Line('The second branches depend on the first: each pair still adds to 1',
                  r'1 - %s = %s, \quad 1 - %s = %s' % (dec(a), dec(1 - a), dec(b), dec(1 - b)))]
    lines += branch_lines(chances, wanted, branches, dec)
    got = sum(branches[key] for key in wanted)
    expected = 1 - sum(value for key, value in branches.items() if key not in wanted)
    figure = diagrams.tree([(yes1, dec(p)), (no1, dec(1 - p))],
                           [[(yes2, dec(a)), (no2, dec(1 - a))], [(yes2, dec(b)), (no2, dec(1 - b))]])
    return made(lines, dec(got), got, expected, figure)


def missing_branch(rng):
    yes1, no1, yes2, no2, first, second = rng.choice(DEPENDENT)
    p, a = tenth(rng), tenth(rng)
    both = p * a
    lines = [Line('The probability that %s is %s. The probability that %s and %s is %s. Find the '
                  'probability that %s, given that %s.' % (first, dec(p), first, second, dec(both),
                                                          second, first)),
             Line('Call the missing branch x and multiply along the top',
                  r'%s \times x = %s' % (dec(p), dec(both))),
             Line('Divide', r'x = %s \div %s = %s' % (dec(both), dec(p), dec(both / p))),
             Line('Its partner branch adds to 1', r'1 - %s = %s' % (dec(both / p), dec(1 - both / p)))]
    figure = diagrams.tree([(yes1, dec(p)), (no1, dec(1 - p))],
                           [[(yes2, '?'), (no2, '')], [(yes2, ''), (no2, '')]])
    return made(lines, dec(both / p), both / p, a, figure)


def at_least(rng):
    yes, no, event, trial = rng.choice(REPEATED)
    p = tenth(rng)
    q = 1 - p
    goes = rng.choice((3, 4))
    got = 1 - q ** goes
    lines = [Line('The probability that %s is %s on each %s, independently. Find the probability that '
                  'it happens on at least one of %d %ss.' % (event, dec(p), trial, goes, trial)),
             Line('At least one is everything except none at all',
                  r'P(\text{at least one}) = 1 - P(\text{none})'),
             Line('None means %s every time' % no.lower(),
                  r'P(\text{none}) = %s^%d = %s' % (dec(q), goes, dec(q ** goes))),
             Line('Take it from 1', r'1 - %s = %s' % (dec(q ** goes), dec(got)))]
    expected = sum(math.comb(goes, hits) * p ** hits * q ** (goes - hits) for hits in range(1, goes + 1))
    return made(lines, dec(got), got, expected)


def problems(rng):
    """Stretch: find n from a without-replacement probability (a quadratic),
    the first success on a given go, or three picks without replacement."""
    kind = rng.choice(('find_n', 'first_success', 'three_picks'))
    if kind == 'find_n':
        k = rng.randint(3, 8)
        size = rng.randint(k + 2, 20)
        p = F(k * (k - 1), size * (size - 1))
        c = size * (size - 1)
        colour = rng.choice(COLOURS)
        lines = [Line('A bag has n sweets and %d of them are %s. Two are taken at random without '
                      'replacement. The probability both are %s is %d/%d. Find n.'
                      % (k, colour, colour, p.numerator, p.denominator)),
                 Line('Multiply along the branch',
                      r'\frac{%d}{n} \times \frac{%d}{n - 1} = %s' % (k, k - 1, frac_tex(p))),
                 Line('Rearrange for n(n - 1)',
                      r'n(n - 1) = %d \div %s = %d' % (k * (k - 1), frac_tex(p), c)),
                 Line('Expand into a quadratic', r'n^2 - n - %d = 0' % c),
                 Line('Factorise', r'(n - %d)(n + %d) = 0' % (size, size - 1)),
                 Line('n counts sweets, so it is positive', r'n = %d' % size)]
        got = (1 + math.isqrt(1 + 4 * c)) // 2           # the quadratic formula's positive root
        return made(lines, 'n = %d' % size, got, size)
    if kind == 'first_success':
        yes, no, event, trial = rng.choice(REPEATED)
        p = tenth(rng)
        q = 1 - p
        go = rng.choice((2, 3, 4))
        got = q ** (go - 1) * p
        lines = [Line('The probability that %s is %s on each %s, independently. Find the probability '
                      'that it happens for the first time on the %s %s.'
                      % (event, dec(p), trial, ORDINALS[go], trial)),
                 Line('First on go %d means %d misses, then it happens' % (go, go - 1),
                      r'%s^{%d} \times %s = %s' % (dec(q), go - 1, dec(p), dec(got)))]
        return made(lines, dec(got), got, q ** (go - 1) - q ** go)
    first, second = rng.sample(SHORT_COLOURS, 2)
    r, b = rng.randint(3, 7), rng.randint(3, 7)
    n = r + b
    below = n * (n - 1) * (n - 2)
    tops = (r * (r - 1) * (r - 2), b * (b - 1) * (b - 2))
    lines = [Line('A bag holds %d %s and %d %s counters. Three are taken at random without '
                  'replacement. Find the probability that all three are the same colour.'
                  % (r, first, b, second)),
             Line('All %s' % first, r'\frac{%d}{%d} \times \frac{%d}{%d} \times \frac{%d}{%d} = \frac{%d}{%d}'
                  % (r, n, r - 1, n - 1, r - 2, n - 2, tops[0], below)),
             Line('All %s' % second, r'\frac{%d}{%d} \times \frac{%d}{%d} \times \frac{%d}{%d} = \frac{%d}{%d}'
                  % (b, n, b - 1, n - 1, b - 2, n - 2, tops[1], below)),
             Line('Add them', r'\frac{%d}{%d} + \frac{%d}{%d} = %s'
                  % (tops[0], below, tops[1], below, ptex(sum(tops), below)))]
    got = F(sum(tops), below)
    expected = F(math.comb(r, 3) + math.comb(b, 3), math.comb(n, 3))
    return made(lines, frac_tex(got), got, expected)
# --- Facts (editable) ---------------------------------------------------------

FACTS = [
    Fact('Along and between', r'Multiply along the branches for "and"; add the outcomes for "or".',
         diagrams.tree([('Red', '3/5'), ('Blue', '2/5')],
                       [[('Red', '2/4'), ('Blue', '2/4')], [('Red', '3/4'), ('Blue', '1/4')]])),
    Fact('Pairs add to 1', r'Every pair of branches from one point adds up to $1$.'),
    Fact('With replacement', r'It goes back: the second branches are the same as the first.'),
    Fact('Without replacement', r'One fewer in the bag: $\frac{3}{5}$ then $\frac{2}{4}$.'),
    Fact('Independent events', r'$P(A \text{ and } B) = P(A) \times P(B)$ when one does not affect the '
                               r'other.'),
    Fact('At least one', r'$P(\text{at least one}) = 1 - P(\text{none})$.'),
    Fact('Reading back', r'If $P(A) \times x = P(A \text{ and } B)$, then '
                         r'$x = P(A \text{ and } B) \div P(A)$.'),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='trees',
    title='Tree diagrams',
    area='Probability',
    keywords=('tree', 'tree diagram', 'with replacement', 'without replacement', 'independent',
              'dependent', 'conditional', 'at least one', 'and', 'or', 'branches'),
    intro='Multiply along the branches, add between them.',
    facts=FACTS,
    stages=[
        Stage('independent', 'Independent events',
              r'Multiply along the branches, add between them. Each pair of branches adds to $1$.',
              independent),
        Stage('with_replacement', 'With replacement',
              r'The item goes back, so the second picks are the same as the first.',
              with_replacement),
        Stage('without_replacement', 'Without replacement',
              r'The second pick has one fewer in the bag, so its fractions change.',
              without_replacement),
        Stage('dependent', 'Dependent events',
              r'The second branches depend on what happened first: read each one from the question.',
              dependent),
        Stage('missing_branch', 'Reading back',
              r'Call the missing branch $x$, multiply along, and solve.',
              missing_branch),
        Stage('at_least', 'At least one',
              r'At least one is $1 - P(\text{none})$: far quicker than adding every branch.',
              at_least),
        Stage('problems', 'Stretch',
              r'Set up the probability with an unknown and solve, or chain the branches for more '
              r'than two goes.',
              problems),
    ])
