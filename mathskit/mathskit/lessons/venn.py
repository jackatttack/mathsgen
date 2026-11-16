"""Venn diagrams and sets: reading a diagram, set notation, filling one from
totals, two-way tables, given that, three sets, then Stretch (regions in x).

Diagrams come from mathskit/diagrams.py. A diagram that is part of the
question is filled in (reading off, three sets); one the working fills is
drawn blank. Every problem carries meta got (from the regions) and expected
(inclusion and exclusion, set operations, column totals) for
tests/smoke_lessons.py.
"""
from fractions import Fraction as F

from .. import diagrams
from ..lesson import Fact, Lesson, Line, Stage
from ..numbers import frac_tex
from .probability import made, ptex

# group, first set, second set, and their short names (distinct first letters)
VENN_SETS = (('students', 'study French', 'study Spanish', 'French', 'Spanish'),
             ('people', 'own a cat', 'own a dog', 'Cat', 'Dog'),
             ('students', 'play football', 'play tennis', 'Football', 'Tennis'),
             ('guests', 'had tea', 'had coffee', 'Tea', 'Coffee'))

# group, verb, the three sets
THREE_SETS = (('students', 'take', ('French', 'Spanish', 'German')),
              ('students', 'play', ('football', 'tennis', 'hockey')),
              ('guests', 'ate', ('cake', 'fruit', 'cheese')))

# group, rows, columns
TWO_WAY = (('students', ('Year 10', 'Year 11'), ('Walk', 'Bus', 'Car')),
           ('students', ('Class A', 'Class B'), ('Maths', 'Art', 'Music')),
           ('visitors', ('Saturday', 'Sunday'), ('Cake', 'Fruit', 'Crisps')))


def regions_for(rng):
    """Region counts (only first, both, only second, neither), each at least 1."""
    return rng.randint(2, 15), rng.randint(1, 10), rng.randint(2, 15), rng.randint(1, 12)


def set_tex(numbers):
    return r'\{%s\}' % ', '.join(map(str, sorted(numbers))) if numbers else r'\varnothing'


# --- Stages -------------------------------------------------------------------

# key: (question form in words, TeX form, regions (only X, both, only Y, neither))
READ_ASKS = {
    'x': ('P(X)', r'P(X)', (0, 1)),
    'not_y': ('P(Y\u2032)', r"P(Y')", (0, 3)),
    'and': ('P(X \u2229 Y)', r'P(X \cap Y)', (1,)),
    'or': ('P(X \u222a Y)', r'P(X \cup Y)', (0, 1, 2)),
    'x_not_y': ('P(X \u2229 Y\u2032)', r"P(X \cap Y')", (0,)),
    'neither': ('P((X \u222a Y)\u2032)', r"P((X \cup Y)')", (3,)),
}


def read(rng):
    group, first, second, short1, short2 = rng.choice(VENN_SETS)
    a, b = short1[0], short2[0]
    regions = regions_for(rng)
    only1, both, only2, neither = regions
    n = sum(regions)
    n1, n2 = only1 + both, both + only2
    key = rng.choice(sorted(READ_ASKS))
    words, tex, wanted = READ_ASKS[key]
    words = words.replace('X', a).replace('Y', b)
    tex = tex.replace('X', a).replace('Y', b)
    count = sum(regions[index] for index in wanted)
    lines = [Line('The Venn diagram shows %d %s: %s = %s (%s) and %s = %s (%s). One is picked at '
                  'random. Find %s.' % (n, group, a, short1, first, b, short2, second, words)),
             Line('Find the regions %s covers' % words,
                  r'%s = %d' % (' + '.join(str(regions[index]) for index in wanted), count)
                  if len(wanted) > 1 else r'%d' % count),
             Line('Out of everyone in the box', r'%s = %s' % (tex, ptex(count, n)))]
    expected = {'x': n1, 'not_y': n - n2, 'and': n1 + n2 - (n - neither), 'or': n - neither,
                'x_not_y': n1 - both, 'neither': n - (n1 + n2 - both)}[key]
    figure = diagrams.venn(('%s (%s)' % (short1, a), '%s (%s)' % (short2, b)),
                           [str(region) for region in regions], highlight=wanted)
    got = F(count, n)
    return made(lines, frac_tex(got), got, F(expected, n), figure)


def properties(size):
    """(name, set) pairs of whole-number properties up to size."""
    numbers = range(1, size + 1)
    primes = {k for k in numbers if k > 1 and all(k % d for d in range(2, int(k ** 0.5) + 1))}
    found = [('even numbers', {k for k in numbers if k % 2 == 0}),
             ('odd numbers', {k for k in numbers if k % 2}),
             ('prime numbers', primes),
             ('square numbers', {k * k for k in range(1, 5) if k * k <= size})]
    found += [('multiples of %d' % m, {k for k in numbers if k % m == 0}) for m in (3, 4, 5)]
    found += [('factors of %d' % f, {k for k in numbers if f % k == 0}) for f in (12, 18, 20, 24)]
    return found


# key: (words, TeX, regions (only A, both, only B, neither), the set operation)
NOTATION_ASKS = {
    'and': ('A \u2229 B', r'A \cap B', (1,), lambda a, b, u: a & b),
    'or': ('A \u222a B', r'A \cup B', (0, 1, 2), lambda a, b, u: a | b),
    'not_a': ('A\u2032', r"A'", (2, 3), lambda a, b, u: u - a),
    'a_not_b': ('A \u2229 B\u2032', r"A \cap B'", (0,), lambda a, b, u: a - b),
    'neither': ('(A \u222a B)\u2032', r"(A \cup B)'", (3,), lambda a, b, u: u - (a | b)),
}


def notation(rng):
    size = rng.randint(12, 20)
    universe = set(range(1, size + 1))
    choices = properties(size)
    while True:
        (name_a, set_a), (name_b, set_b) = rng.sample(choices, 2)
        key = rng.choice(sorted(NOTATION_ASKS))
        words, tex, wanted, operation = NOTATION_ASKS[key]
        result = operation(set_a, set_b, universe)
        if set_a & set_b and set_a - set_b and set_b - set_a and 0 < len(result) < size:
            break
    regions = ([k for k in sorted(universe) if k in set_a and k not in set_b],
               [k for k in sorted(universe) if k in set_a and k in set_b],
               [k for k in sorted(universe) if k in set_b and k not in set_a],
               [k for k in sorted(universe) if k not in set_a and k not in set_b])
    chosen = sorted(k for index in wanted for k in regions[index])
    lines = [Line('\u03be = {1, 2, ..., %d}. A is the %s and B is the %s. List the members of %s and '
                  'find the probability that a number picked at random from \u03be is in %s.'
                  % (size, name_a, name_b, words, words)),
             Line('List A and B', r'A = %s, \quad B = %s' % (set_tex(set_a), set_tex(set_b))),
             Line('The middle is in both', r'A \cap B = %s' % set_tex(regions[1])),
             Line('Then the rest of each circle, then outside',
                  r'\text{only } A = %s, \; \text{only } B = %s, \; \text{outside} = %s'
                  % (set_tex(regions[0]), set_tex(regions[2]), set_tex(regions[3]))),
             Line('%s is those regions' % words, r'%s = %s' % (tex, set_tex(chosen))),
             Line('Count them over the %d numbers in \u03be' % size, r'P = %s' % ptex(len(chosen), size))]
    got = (chosen, F(len(chosen), size))
    expected = (sorted(result), F(len(result), size))
    answer = r'%s = %s, \; P = %s' % (tex, set_tex(chosen), frac_tex(got[1]))
    return made(lines, answer, got, expected, diagrams.venn(('A', 'B'), ['', '', '', '']))


VENN_ASKS = {
    # the question's ending, the regions wanted (only first, both, only second, neither)
    'both': ('%s and %s', (1,)),
    'either': ('%s or %s, or both', (0, 1, 2)),
    'neither': ('neither %s nor %s', (3,)),
    'exactly_one': ('%s or %s but not both', (0, 2)),
}


def from_totals(rng):
    group, first, second, short1, short2 = rng.choice(VENN_SETS)
    only1, both, only2, neither = regions_for(rng)
    n1, n2 = only1 + both, both + only2
    n = only1 + both + only2 + neither
    ask = rng.choice(sorted(VENN_ASKS))
    pattern, wanted = VENN_ASKS[ask]
    regions = (only1, both, only2, neither)
    count = sum(regions[index] for index in wanted)
    lines = [Line('There are %d %s. %d %s, %d %s and %d do both. One is picked at random. Find the '
                  'probability they %s.' % (n, group, n1, first, n2, second, both,
                                            pattern % (first, second))),
             Line('Start in the middle: both', r'%d' % both),
             Line('The rest of the %s circle' % short1, r'%d - %d = %d' % (n1, both, only1)),
             Line('The rest of the %s circle' % short2, r'%d - %d = %d' % (n2, both, only2)),
             Line('Outside both circles', r'%d - %d - %d - %d = %d' % (n, only1, both, only2, neither))]
    if len(wanted) > 1:
        lines.append(Line('Add the regions wanted',
                          r'%s = %d' % (' + '.join(str(regions[index]) for index in wanted), count)))
    lines.append(Line('Out of everyone', r'P = %s' % ptex(count, n)))
    expected = {'both': n1 + n2 - (n - neither), 'either': n1 + n2 - both,
                'neither': n - (n1 + n2 - both), 'exactly_one': n1 + n2 - 2 * both}[ask]
    got = F(count, n)
    return made(lines, frac_tex(got), got, F(expected, n),
                diagrams.venn((short1, short2), ['', '', '', '']))


def two_way(rng):
    group, rows, cols = rng.choice(TWO_WAY)
    values = [[rng.randint(3, 30) for _ in cols] for _ in rows]
    row_totals = [sum(row) for row in values]
    col_totals = [values[0][j] + values[1][j] for j in range(len(cols))]
    grand = sum(row_totals)
    hidden = rng.sample(range(len(cols)), 2)          # the gap in row 0, then in row 1
    r = rng.randrange(2)
    c = hidden[r] if rng.random() < 0.6 else rng.randrange(len(cols))
    given = rng.random() < 0.4

    def cell(i, j):
        return '?' if hidden[i] == j else str(values[i][j])

    table = (r'\begin{array}{|l|%s|c|}\hline & %s & \text{Total} \\ \hline %s \\ \hline '
             r'\text{Total} & %s & %d \\ \hline\end{array}'
             % ('|'.join('c' * len(cols)), ' & '.join(r'\text{%s}' % name for name in cols),
                r' \\ \hline '.join(r'\text{%s} & %s & %d' % (rows[i], ' & '.join(cell(i, j) for j in range(len(cols))),
                                                              row_totals[i]) for i in range(2)),
                ' & '.join(map(str, col_totals)), grand))
    if given:
        question = ('One of the %s from %s is picked at random. Find the probability they chose %s.'
                    % (group, rows[r], cols[c]))
    else:
        question = ('One of the %s is picked at random. Find the probability they are from %s and '
                    'chose %s.' % (group, rows[r], cols[c]))
    lines = [Line('The two-way table shows the %s. %s' % (group, question)), Line('The table', table)]
    filled = [row[:] for row in values]
    for i in range(2):
        j = hidden[i]
        others = [values[i][k] for k in range(len(cols)) if k != j]
        filled[i][j] = row_totals[i] - sum(others)
        lines.append(Line('Fill the gap in %s: the row total minus the others' % rows[i],
                          r'%d - %s = %d' % (row_totals[i], ' - '.join(map(str, others)), filled[i][j])))
    by_column = col_totals[c] - values[1 - r][c]      # the same cell, read down its column
    if given:
        lines.append(Line('Only the %s row counts' % rows[r], r'P = %s' % ptex(filled[r][c], row_totals[r])))
        got, expected = F(filled[r][c], row_totals[r]), F(by_column, row_totals[r])
    else:
        lines.append(Line('Out of everyone', r'P = %s' % ptex(filled[r][c], grand)))
        got, expected = F(filled[r][c], grand), F(by_column, grand)
    return made(lines, frac_tex(got), got, expected)


def given(rng):
    group, first, second, short1, short2 = rng.choice(VENN_SETS)
    only1, both, only2, neither = regions_for(rng)
    n1, n2 = only1 + both, both + only2
    n = only1 + both + only2 + neither
    lines = [Line('There are %d %s. %d %s, %d %s and %d do both. One of those who %s is picked at '
                  'random. Find the probability they also %s.'
                  % (n, group, n1, first, n2, second, both, second, first)),
             Line('Only the %s circle counts now' % short2, r'%d \text{ %s}' % (n2, group)),
             Line('Of those, the middle also %s' % first, r'%d' % both),
             Line('Out of the %s circle, not out of everyone' % short2, r'P = %s' % ptex(both, n2))]
    got = F(both, n2)
    expected = F(both, n) / F(n2, n)                  # P(A and B) over P(B)
    return made(lines, frac_tex(got), got, expected, diagrams.venn((short1, short2), ['', '', '', '']))


# key: (words, regions (only A, only B, only C, AB, AC, BC, ABC, none))
THREE_ASKS = {
    'all': ('all three', (6,)),
    'exactly_two': ('exactly two of them', (3, 4, 5)),
    'exactly_one': ('exactly one of them', (0, 1, 2)),
    'none': ('none of them', (7,)),
    'at_least_two': ('at least two of them', (3, 4, 5, 6)),
    'a_not_c': (None, (0, 3)),
}


def three_sets(rng):
    group, verb, names = rng.choice(THREE_SETS)
    regions = [rng.randint(1, 12) for _ in range(8)]
    n = sum(regions)
    key = rng.choice(sorted(THREE_ASKS))
    words, wanted = THREE_ASKS[key]
    if words is None:
        words = '%s but not %s' % (names[0], names[2])
    count = sum(regions[index] for index in wanted)
    lines = [Line('The Venn diagram shows what %d %s %s. One is picked at random. Find the '
                  'probability they %s %s.' % (n, group, verb, verb, words)),
             Line('Find the regions for %s' % words,
                  r'%s = %d' % (' + '.join(str(regions[index]) for index in wanted), count)
                  if len(wanted) > 1 else r'%d' % count),
             Line('Out of everyone in the box', r'P = %s' % ptex(count, n))]
    others = sum(regions[index] for index in range(8) if index not in wanted)
    figure = diagrams.venn3([name.capitalize() for name in names],
                            [str(region) for region in regions], highlight=wanted)
    got = F(count, n)
    return made(lines, frac_tex(got), got, 1 - F(others, n), figure)


def coefficient(k, letter='x'):
    return letter if k == 1 else '%d%s' % (k, letter)


def problems(rng):
    """Stretch: the regions are written in x. Add them to the total, solve
    for x, then find a probability."""
    group, first, second, short1, short2 = rng.choice(VENN_SETS)
    x = rng.randint(2, 9)
    k = rng.choice((2, 3))
    a, b = rng.randint(x + 2, x + 20), rng.randint(x + 2, x + 20)
    n = a + b + (k - 1) * x
    lines = [Line('There are %d %s. %d %s and %d %s. x %s do both, and %dx do neither. Find x, then '
                  'the probability that one picked at random does neither.'
                  % (n, group, a, first, b, second, 'of them', k)),
             Line('Write each region in x',
                  r'\text{only %s} = %d - x, \; \text{both} = x, \; \text{only %s} = %d - x, \; '
                  r'\text{neither} = %dx' % (short1, a, short2, b, k)),
             Line('The regions add up to %d' % n, r'(%d - x) + x + (%d - x) + %dx = %d' % (a, b, k, n)),
             Line('Simplify', r'%d + %s = %d' % (a + b, coefficient(k - 1), n)),
             Line('Solve', r'x = %d' % x),
             Line('Neither is %dx = %d' % (k, k * x), r'P(\text{neither}) = %s' % ptex(k * x, n))]
    solved = F(n - a - b, k - 1)
    got = F(k, 1) * solved / n
    figure = diagrams.venn((short1, short2), ['%d \u2212 x' % a, 'x', '%d \u2212 x' % b, '%dx' % k])
    return made(lines, 'x = %d, P = %s' % (x, frac_tex(F(k * x, n))), got, F(k * x, n), figure)
# --- Facts (editable) ---------------------------------------------------------

FACTS = [
    Fact('Filling a Venn diagram', r'Middle first, then the rest of each circle, then outside. '
                                   r'Check the regions add up to the total.',
         diagrams.venn(('A', 'B'), ['7', '3', '5', '5'])),
    Fact('Set notation', r'$A \cap B$: in both. $A \cup B$: in either or both. $A\'$: not in $A$. '
                         r'$\xi$: everything.'),
    Fact('Union', r'$P(A \cup B) = P(A) + P(B) - P(A \cap B)$: the middle is counted twice otherwise.'),
    Fact('Two-way tables', r'Each row and column adds to its total: fill gaps by subtracting, then '
                           r'count.'),
    Fact('Given that', r'Given $B$, only count inside $B$: '
                       r'$P(A \mid B) = \dfrac{n(A \cap B)}{n(B)}$.'),
    Fact('Three sets', r'Eight regions: fill from the middle (all three) outwards.',
         diagrams.venn3(['A', 'B', 'C'], ['5', '4', '6', '3', '2', '2', '1', '7'])),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='venn',
    title='Venn diagrams and sets',
    area='Probability',
    keywords=('venn', 'venn diagram', 'sets', 'set notation', 'union', 'intersection',
              'complement', 'universal set', 'two-way table', 'two way table', 'given that',
              'conditional', 'three sets'),
    intro='Fill from the middle out, then count the regions you want.',
    facts=FACTS,
    stages=[
        Stage('read', 'Reading a Venn diagram',
              r'Find the regions the question covers, add them, and divide by everyone in the box.',
              read),
        Stage('notation', 'Set notation',
              r'$\cap$ is both, $\cup$ is either, a dash means not. List the members region by region.',
              notation),
        Stage('from_totals', 'Filling from totals',
              r'Start with the middle, take it off each circle\'s total, then work out the outside.',
              from_totals),
        Stage('two_way', 'Two-way tables',
              r'Rows and columns add to their totals: subtract to fill the gaps.',
              two_way),
        Stage('given', 'Given that',
              r'Given that cuts down who counts: divide by the group you are told about.',
              given),
        Stage('three_sets', 'Three sets',
              r'Eight regions. Read the question carefully: exactly two is not the same as at least two.',
              three_sets),
        Stage('problems', 'Stretch',
              r'Write every region in $x$, add them to the total, solve, then answer the question asked.',
              problems),
    ])
