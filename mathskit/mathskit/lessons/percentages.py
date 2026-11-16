"""Percentages: amounts, the 1% method, change, multipliers, reverse
percentages, repeated change.

The method throughout: find 1% (or 10%), then build what you need.
Reverse percentages use it too: 75% = 1200, 1% = 16, 100% = 1600.
Numbers are chosen so the working stays exact. Each problem carries
meta['got'] (from the working shown) and meta['expected'] (straight from
the formula) for tests/smoke_lessons.py to compare.
"""
from fractions import Fraction as F

from .. import numbers
from ..lesson import Fact, Lesson, Line, Problem, Stage, Worked

num = numbers.text


def pct(p):
    """TeX for p percent: the % must be escaped or KaTeX reads a comment."""
    return r'%s\%%' % num(p)


def worked(lines, answer, got, expected):
    return Problem(statement=lines[0].tex or lines[0].say, answer=answer,
                   solution=Worked(lines, answer), meta={'got': got, 'expected': expected})


# --- Stages -------------------------------------------------------------------

BUILD_PERCENTS = (5, 15, 20, 25, 30, 35, 40, 45, 60, 65, 70, 75, 85, 12, 21, 32, 3, 11)


def of_amount(rng):
    """Build p% from 10%, 5% and 1%."""
    p = rng.choice(BUILD_PERCENTS)
    tens, rest = divmod(p, 10)
    needs_one = rest not in (0, 5)
    amount = rng.randrange(2, 90) * 10 if needs_one else rng.randrange(2, 45) * 20
    ten, one = F(amount, 10), F(amount, 100)
    lines = [Line('Find %d%% of %s' % (p, num(amount)),
                  r'%s \text{ of } %s' % (pct(p), num(amount)))]
    parts = []
    if tens or rest == 5:
        lines.append(Line('10% is the amount divided by 10',
                          r'10\%% = %s \div 10 = %s' % (num(amount), num(ten))))
    if tens > 1:
        lines.append(Line('Times by %d for %d%%' % (tens, tens * 10),
                          r'%s = %s \times %d = %s' % (pct(tens * 10), num(ten), tens,
                                                       num(ten * tens))))
    if tens:
        parts.append(ten * tens)
    if rest == 5:
        lines.append(Line('5% is half of 10%',
                          r'5\%% = %s \div 2 = %s' % (num(ten), num(ten / 2))))
        parts.append(ten / 2)
    elif rest:
        lines.append(Line('1% is the amount divided by 100',
                          r'1\%% = %s \div 100 = %s' % (num(amount), num(one))))
        if rest > 1:
            lines.append(Line('Times by %d for %d%%' % (rest, rest),
                              r'%s = %s \times %d = %s' % (pct(rest), num(one), rest,
                                                           num(one * rest))))
        parts.append(one * rest)
    got = sum(parts)
    if len(parts) > 1:
        lines.append(Line('Add the pieces',
                          r'%s = %s = %s' % (pct(p), ' + '.join(num(v) for v in parts),
                                             num(got))))
    answer = '%d%% of %s = %s' % (p, num(amount), num(got))
    return worked(lines, answer, got, F(amount * p, 100))


def one_percent(rng):
    p = rng.choice([value for value in range(2, 99) if value % 5])
    amount = rng.randrange(3, 60) * 50
    one = F(amount, 100)
    got = one * p
    lines = [Line('Find %d%% of %s' % (p, num(amount)),
                  r'%s \text{ of } %s' % (pct(p), num(amount))),
             Line('Find 1% first: divide by 100',
                  r'1\%% = %s \div 100 = %s' % (num(amount), num(one))),
             Line('Then times by %d' % p,
                  r'%s = %s \times %d = %s' % (pct(p), num(one), p, num(got)))]
    answer = '%d%% of %s = %s' % (p, num(amount), num(got))
    return worked(lines, answer, got, F(amount * p, 100))


WHOLES = (20, 25, 40, 50, 80, 125, 200, 250, 400, 500)


def as_percentage(rng):
    whole = rng.choice(WHOLES)
    part = rng.randrange(1, whole)
    got = F(part, whole) * 100
    lines = [Line('Write %d as a percentage of %d' % (part, whole),
                  r'%d \text{ out of } %d' % (part, whole)),
             Line('Write it as a fraction', r'\frac{%d}{%d}' % (part, whole)),
             Line('Times by 100 to make a percentage',
                  r'\frac{%d}{%d} \times 100 = %s' % (part, whole, pct(got)))]
    answer = '%d out of %d is %s%%' % (part, whole, num(got))
    return worked(lines, answer, got, F(100 * part) / whole)


CHANGE_PERCENTS = (5, 10, 15, 20, 25, 30, 35, 40, 12, 8, 3, 17)


def change(rng):
    p = rng.choice(CHANGE_PERCENTS)
    up = rng.random() < 0.5
    amount = rng.randrange(2, 60) * 10
    one = F(amount, 100)
    part = one * p
    new = amount + part if up else amount - part
    word = 'Increase' if up else 'Decrease'
    lines = [Line('%s %s by %d%%' % (word, num(amount), p),
                  r'\text{%s } %s \text{ by } %s' % (word.lower(), num(amount), pct(p))),
             Line('Find 1%', r'1\%% = %s \div 100 = %s' % (num(amount), num(one))),
             Line('Find %d%%' % p, r'%s = %s \times %d = %s' % (pct(p), num(one), p, num(part))),
             Line('Add it on' if up else 'Take it away',
                  r'%s %s %s = %s' % (num(amount), '+' if up else '-', num(part), num(new)))]
    answer = '%s: %s' % (word, num(new))
    return worked(lines, answer, new, F(amount) * F(100 + (p if up else -p), 100))


def multipliers(rng):
    p = rng.choice(CHANGE_PERCENTS)
    up = rng.random() < 0.5
    amount = rng.randrange(2, 80) * 10
    left = 100 + p if up else 100 - p
    m = F(left, 100)
    new = amount * m
    word = 'Increase' if up else 'Decrease'
    lines = [Line('%s %s by %d%% using a multiplier' % (word, num(amount), p),
                  r'\text{%s } %s \text{ by } %s' % (word.lower(), num(amount), pct(p))),
             Line('Start at 100%%, then %s %d%%' % ('add' if up else 'take away', p),
                  r'100\%% %s %s = %s' % ('+' if up else '-', pct(p), pct(left))),
             Line('Divide by 100 for the multiplier',
                  r'%s \div 100 = %s' % (num(left), num(m))),
             Line('Times the amount by the multiplier',
                  r'%s \times %s = %s' % (num(amount), num(m), num(new)))]
    answer = '%s: %s' % (word, num(new))
    expected = F(amount) + (1 if up else -1) * F(amount * p, 100)
    return worked(lines, answer, new, expected)


PART_PERCENTS = (15, 20, 25, 30, 35, 40, 45, 60, 65, 70, 75, 80, 85)
REVERSE_CHANGES = (5, 10, 15, 20, 25, 30, 35, 40, 12)
REVERSE_SUBJECTS = (('A price', 'the original price'),
                    ('A salary', 'the salary before the change'),
                    ('A bill', 'the bill before the change'))


def reverse(rng):
    """The find-one method: what % you have, then 1%, then 100%."""
    one = rng.choice([F(value) for value in range(2, 40)] + [F(value, 2) for value in range(5, 40, 2)])
    original = one * 100
    form = rng.choice(('increase', 'decrease', 'part'))
    lines = []
    if form == 'part':
        have = rng.choice(PART_PERCENTS)
        known = one * have
        lines.append(Line('%d%% of a number is %s. Find the number.' % (have, num(known))))
    else:
        r = rng.choice(REVERSE_CHANGES)
        up = form == 'increase'
        have = 100 + r if up else 100 - r
        known = one * have
        subject, target = rng.choice(REVERSE_SUBJECTS)
        lines.append(Line('%s goes %s by %d%% to %s. Find %s.'
                          % (subject, 'up' if up else 'down', r, num(known), target)))
        lines.append(Line('The original is 100%%. After the %s, it is %d%%'
                          % ('increase' if up else 'decrease', have),
                          r'100\%% %s %s = %s' % ('+' if up else '-', pct(r), pct(have))))
    lines += [Line('So %d%% is %s' % (have, num(known)), r'%s = %s' % (pct(have), num(known))),
              Line('Find 1%%: divide by %d' % have,
                   r'1\%% = %s \div %d = %s' % (num(known), have, num(known / have))),
              Line('Then 100%: times by 100',
                   r'100\%% = %s \times 100 = %s' % (num(known / have), num(known / have * 100)))]
    got = known / have * 100
    answer = 'The original is %s' % num(got)
    return worked(lines, answer, got, original)


def repeated(rng):
    p = rng.choice((2, 3, 4, 5, 8, 10, 15, 20))
    up = rng.random() < 0.6
    years = rng.choice((2, 3, 4, 5))
    amount = rng.randrange(5, 100) * 100
    left = 100 + p if up else 100 - p
    m = F(left, 100)
    got = numbers.round_to(amount * m ** years, 2)
    value = F(amount)
    for _ in range(years):
        value = value + value * F(p if up else -p, 100)
    if up:
        question = ('%s is invested at %d%% compound interest a year. Find its value '
                    'after %d years.' % (num(amount), p, years))
    else:
        question = ('A car worth %s loses %d%% of its value each year. Find its value '
                    'after %d years.' % (num(amount), p, years))
    lines = [Line(question),
             Line('Find the multiplier',
                  r'100\%% %s %s = %s \;\to\; \times %s'
                  % ('+' if up else '-', pct(p), pct(left), num(m))),
             Line('Times by it once for each year',
                  r'%s \times %s^{%d}' % (num(amount), num(m), years)),
             Line('Work it out, to 2 decimal places',
                  r'%s \times %s^{%d} \approx %s'
                  % (num(amount), num(m), years, numbers.money(got)))]
    answer = 'About %s after %d years' % (numbers.money(got), years)
    return worked(lines, answer, got, numbers.round_to(value, 2))


# --- Facts (editable) ---------------------------------------------------------

BAR = (
    '<svg viewBox="0 0 260 92" width="260" height="92" xmlns="http://www.w3.org/2000/svg" '
    'fill="none" stroke="currentColor" stroke-width="2" font-family="-apple-system, sans-serif">'
    '<rect x="10" y="30" width="180" height="28" fill="currentColor" fill-opacity="0.25" '
    'stroke="none"/>'
    '<rect x="10" y="30" width="240" height="28" rx="3"/>'
    '<path d="M190 30 L190 58"/>'
    '<text x="100" y="22" text-anchor="middle" fill="currentColor" stroke="none" '
    'font-size="15">75% = 1200</text>'
    '<text x="130" y="82" text-anchor="middle" fill="currentColor" stroke="none" '
    'font-size="15">100% = 1600</text>'
    '</svg>')

FACTS = [
    Fact('Percent means out of 100', r'$35\% = \frac{35}{100} = 0.35$'),
    Fact('10%, 5% and 1%',
         r'$10\%$: divide by $10$. $5\%$: half of $10\%$. $1\%$: divide by $100$.'),
    Fact('The 1% method',
         r'Find $1\%$, then multiply up: if $1\% = 6.4$ then $37\% = 6.4 \times 37 = 236.8$.'),
    Fact('Increase and decrease',
         r'Find the percentage, then add it on or take it away. A multiplier does it '
         r'in one step.'),
    Fact('Multipliers',
         r'Increase by $15\%$: $\times 1.15$. Decrease by $15\%$: $\times 0.85$. '
         r'Find $15\%$ of an amount: $\times 0.15$.'),
    Fact('Reverse percentages',
         r'Say what percentage you have, find $1\%$, then $100\%$: $75\% = 1200$, so '
         r'$1\% = 16$, so $100\% = 1600$.', BAR),
    Fact('The trap',
         r'After a $25\%$ increase to $1500$, the original is not $1500$ take away '
         r'$25\%$ of $1500$. The $25\%$ was of the original: $125\% = 1500$.'),
    Fact('Repeated change',
         r'Multiply by the multiplier once per year: $2000 \times 1.05^{3}$.'),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='percentages',
    title='Percentages',
    area='Number',
    keywords=('percent', 'multiplier', 'reverse', 'compound', 'interest', 'depreciation',
              'increase', 'decrease'),
    intro='Find $1\\%$ (or $10\\%$), then build whatever you need.',
    facts=FACTS,
    stages=[
        Stage('of_amount', 'Of an amount',
              r'Find $10\%$ by dividing by $10$, $5\%$ by halving that, and $1\%$ by '
              r'dividing by $100$. Build the percentage you need from those pieces.',
              of_amount),
        Stage('one_percent', 'The 1% method',
              r'Any percentage: find $1\%$ by dividing by $100$, then multiply by the '
              r'percentage you want.',
              one_percent),
        Stage('as_percentage', 'As a percentage',
              r'Write it as a fraction of the whole, then multiply by $100$.',
              as_percentage),
        Stage('change', 'Increase and decrease',
              r'Find the percentage of the amount, then add it on for an increase or '
              r'take it away for a decrease.',
              change),
        Stage('multipliers', 'Multipliers',
              r'Start from $100\%$ and add or take away the change. Divide by $100$ for '
              r'the multiplier, then multiply once: $15\%$ more is $\times 1.15$.',
              multipliers),
        Stage('reverse', 'Reverse',
              r'Work out what percentage you have been given, find $1\%$, then multiply '
              r'by $100$: $75\% = 1200$, $1\% = 16$, $100\% = 1600$.',
              reverse),
        Stage('repeated', 'Repeated change',
              r'Multiply by the multiplier once for every year: $A \times 1.05^{3}$.',
              repeated),
    ])
