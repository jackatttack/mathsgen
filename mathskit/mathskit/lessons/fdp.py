"""Fractions, decimals and percentages: converting each way, the three
together, ordering a mixed list, short division to recurring decimals,
recurring decimals back to fractions, then Stretch.

Recurring decimals are checked by long division: the working's fraction is
divided out again and its digits compared with the question's. Other
problems carry meta got (from the working) and expected (the value the
question was built from) for tests/smoke_lessons.py.
"""
import math
from fractions import Fraction as F

from ..lesson import Fact, Lesson, Line, Problem, Stage, Worked
from ..numbers import frac_tex

TERMINATING = (2, 4, 5, 8, 20, 25, 40, 50)
RECURRING = (3, 6, 7, 9, 11, 12, 15, 18, 22)
FORMS = ('fraction', 'decimal', 'percent')
DOT = r'\overset{\cdot}{%d}'     # a recurring dot; KaTeX's \dot does not show in Pythonista


# --- Helpers ------------------------------------------------------------------

def ft(top, bottom):
    return r'\frac{%d}{%d}' % (top, bottom)


def dec(value):
    return ('%.4f' % float(value)).rstrip('0').rstrip('.')


def over(top, bottom):
    out = ft(top, bottom)
    if F(top, bottom).denominator != bottom:
        out += ' = ' + frac_tex(F(top, bottom))
    return out


def power_for(bottom):
    """The smallest power of 10 that bottom divides."""
    power = 10
    while power % bottom:
        power *= 10
    return power


def made(lines, answer, got, expected):
    return Problem(statement=lines[0].tex or lines[0].say, answer=answer,
                   solution=Worked(lines, answer), meta={'got': got, 'expected': expected})


def long_division(top, bottom):
    """top / bottom by short division: (whole, digits before the repeat,
    repeating digits, steps). repeat is empty when the decimal ends; each
    step is (carried, digit, remainder)."""
    whole, rest = divmod(top, bottom)
    seen, digits, steps = {}, [], []
    while rest and rest not in seen:
        seen[rest] = len(digits)
        carried = rest * 10
        digit, rest = divmod(carried, bottom)
        digits.append(digit)
        steps.append((carried, digit, rest))
    if not rest:
        return whole, digits, [], steps
    start = seen[rest]
    return whole, digits[:start], digits[start:], steps


def value_of(whole, prefix, repeat):
    """The exact value of whole.prefix(repeat repeating)."""
    places = len(prefix)
    value = whole + F(int(''.join(map(str, prefix)) or 0), 10 ** places)
    if repeat:
        value += F(int(''.join(map(str, repeat))), (10 ** len(repeat) - 1) * 10 ** places)
    return value


def recurring_tex(whole, prefix, repeat):
    """Dot notation: a dot over the first and last repeating digits. Drawn
    with overset, not \\dot: Pythonista's web view drops KaTeX's \\dot accent."""
    text = '%d.%s' % (whole, ''.join(map(str, prefix)))
    if len(repeat) == 1:
        text += DOT % repeat[0]
    elif repeat:
        text += DOT % repeat[0] + ''.join(map(str, repeat[1:-1])) + DOT % repeat[-1]
    return text


def pure_repeat(rng, longest=3):
    """Repeating digits whose shortest block is the whole list (not 0s, not 9s)."""
    length = rng.choice([1, 2, 2, 3][:longest + 1 if longest < 3 else 4])
    while True:
        digits = [rng.randint(0, 9) for _ in range(length)]
        if length == 1 and digits[0] not in (0, 9):
            return digits
        if length > 1 and len(set(digits)) > 1:
            return digits


def shown(value, form):
    """(TeX, plain words) for a value written as a fraction, decimal or percent."""
    if form == 'fraction':
        return ft(value.numerator, value.denominator), '%d/%d' % (value.numerator, value.denominator)
    if form == 'decimal':
        return dec(value), dec(value)
    return r'%s\%%' % dec(value * 100), '%s%%' % dec(value * 100)


def ordinal(number):
    if 10 <= number % 100 <= 20:
        return '%dth' % number
    return '%d%s' % (number, {1: 'st', 2: 'nd', 3: 'rd'}.get(number % 10, 'th'))


def coprime_top(rng, bottom):
    return rng.choice([top for top in range(1, bottom) if math.gcd(top, bottom) == 1])


# --- Stages -------------------------------------------------------------------

def convert(rng):
    bottom = rng.choice(TERMINATING)
    top = coprime_top(rng, bottom)
    value = F(top, bottom)
    text = dec(value)
    if rng.random() < 0.5:
        power = power_for(bottom)
        k = power // bottom
        lines = [Line('Write %d/%d as a decimal.' % (top, bottom)),
                 Line('Make the denominator %d: multiply top and bottom by %d' % (power, k),
                      r'%s = %s' % (ft(top, bottom), ft(top * k, power))),
                 Line('Read it as a decimal', r'%s = %s' % (ft(top * k, power), text))]
        return made(lines, text, F(text), value)
    places = len(text.split('.')[1])
    digits = int(text.split('.')[1])
    power = 10 ** places
    h = math.gcd(digits, power)
    lines = [Line('Write %s as a fraction in its simplest form.' % text),
             Line('%d decimal place%s, so over %d' % (places, '' if places == 1 else 's', power),
                  r'%s = %s' % (text, ft(digits, power))),
             Line('Simplify: divide the top and bottom by %d' % h,
                  r'%s = %s' % (ft(digits, power), ft(digits // h, power // h)))]
    return made(lines, ft(top, bottom), F(digits // h, power // h), value)


def percentages(rng):
    bottom = rng.choice((2, 4, 5, 8, 10, 20, 25, 50))
    top = coprime_top(rng, bottom)
    value = F(top, bottom)
    decimal, percent = dec(value), dec(value * 100)
    places = len(decimal.split('.')[1])
    power, digits = 10 ** places, int(decimal.split('.')[1])
    to_fraction = r'%s = %s' % (decimal, ft(digits, power))
    if digits != top:
        to_fraction += ' = ' + ft(top, bottom)
    start = rng.choice(FORMS)
    if start == 'fraction':
        k = power_for(bottom) // bottom
        lines = [Line('Write %d/%d as a decimal and as a percentage.' % (top, bottom)),
                 Line('Make the denominator %d, then read the decimal' % power_for(bottom),
                      r'%s = %s = %s' % (ft(top, bottom), ft(top * k, power_for(bottom)), decimal)),
                 Line('Multiply by 100 for the percentage', r'%s \times 100 = %s\%%' % (decimal, percent))]
        got = (F(top * k, power_for(bottom)), F(decimal), F(percent) / 100)
    elif start == 'decimal':
        lines = [Line('Write %s as a percentage and as a fraction in its simplest form.' % decimal),
                 Line('Multiply by 100 for the percentage', r'%s \times 100 = %s\%%' % (decimal, percent)),
                 Line('Over %d, then simplify' % power, to_fraction)]
        got = (F(digits, power), F(decimal), F(percent) / 100)
    else:
        lines = [Line('Write %s%% as a decimal and as a fraction in its simplest form.' % percent),
                 Line('Divide by 100 for the decimal', r'%s \div 100 = %s' % (percent, decimal)),
                 Line('Over %d, then simplify' % power, to_fraction)]
        got = (F(digits, power), F(decimal), F(percent) / 100)
    answer = r'%s = %s = %s\%%' % (ft(top, bottom), decimal, percent)
    return made(lines, answer, got, (value, value, value))


def ordering(rng):
    pool = sorted(set(F(k, d) for d in (2, 4, 5, 8, 10, 20, 25) for k in range(1, d)))
    count = rng.choice((4, 5))
    while True:
        values = rng.sample(pool, count)
        if max(values) - min(values) <= F(1, 2):
            break
    forms = list(FORMS) + [rng.choice(FORMS) for _ in range(count - 3)]
    rng.shuffle(forms)
    items = [(shown(value, form), form, value) for value, form in zip(values, forms)]
    by_decimal = sorted(items, key=lambda item: float(dec(item[2])))
    lines = [Line('Write these in order, smallest first: %s.' % ', '.join(item[0][1] for item in items)),
             Line('Change each one to a decimal', r', \; '.join(
                 r'%s = %s' % (item[0][0], dec(item[2])) for item in items if item[1] != 'decimal')),
             Line('Order the decimals', r' < '.join(dec(item[2]) for item in by_decimal)),
             Line('Back in their original forms', r', \; '.join(item[0][0] for item in by_decimal))]
    got = [item[0][0] for item in by_decimal]
    expected = [item[0][0] for item in sorted(items, key=lambda item: item[2])]
    return made(lines, r', \; '.join(got), got, expected)


def recurring(rng):
    while True:
        bottom = rng.choice(RECURRING)
        top = coprime_top(rng, bottom)
        whole, prefix, repeat, steps = long_division(top, bottom)
        if repeat and len(steps) <= 8:
            break
    lines = [Line('Write %d/%d as a decimal.' % (top, bottom)),
             Line('Short division: each remainder carries on as tens', r', \; '.join(
                 r'%d \div %d = %d \text{ r } %d' % (carried, bottom, digit, rest)
                 for carried, digit, rest in steps)),
             Line('Remainder %d has come round again, so the digits repeat from there' % steps[-1][2],
                  r'%s = %s' % (ft(top, bottom), recurring_tex(whole, prefix, repeat)))]
    return made(lines, recurring_tex(whole, prefix, repeat), value_of(whole, prefix, repeat),
                F(top, bottom))


def recurring_fraction(rng):
    repeat = pure_repeat(rng)
    block = ''.join(map(str, repeat))
    size = len(repeat)
    m = 10 ** size
    lines = [Line('Write 0.%s... (%s recurring) as a fraction in its simplest form.' % (block * 3, block)),
             Line('Call it x and write out a few repeats', r'x = 0.%s\ldots' % (block * 3)),
             Line('The block is %d digit%s long, so multiply by %d' % (size, '' if size == 1 else 's', m),
                  r'%dx = %d.%s\ldots' % (m, int(block), block * 2)),
             Line('Subtract x: the repeating tails cancel',
                  r'%dx - x = %d \;\Rightarrow\; %dx = %d' % (m, int(block), m - 1, int(block))),
             Line('Divide, then simplify', r'x = %s' % over(int(block), m - 1))]
    value = F(int(block), m - 1)
    return made(lines, frac_tex(value), long_division(value.numerator, value.denominator)[:3],
                (0, [], repeat))


def problems(rng):
    """Stretch: a decimal that starts repeating after one digit, or a far
    digit of a recurring decimal found from the length of its block."""
    if rng.random() < 0.5:
        while True:
            first = rng.randint(1, 9)
            repeat = pure_repeat(rng, longest=2)
            if first != repeat[-1]:
                break
        block = ''.join(map(str, repeat))
        size = len(repeat)
        big = 10 ** (1 + size)
        joined = int('%d%s' % (first, block))
        value = F(joined - first, big - 10)
        written = recurring_tex(0, [first], repeat)
        lines = [Line('Write 0.%d%s... (only the %s recurring) as a fraction in its simplest form.'
                      % (first, block * 3, block)),
                 Line('Call it x', r'x = %s = 0.%d%s\ldots' % (written, first, block * 3)),
                 Line('Move the point past the digit that does not repeat',
                      r'10x = %d.%s\ldots' % (first, block * 3)),
                 Line('And past one whole block more', r'%dx = %d.%s\ldots' % (big, joined, block * 2)),
                 Line('Subtract: the repeating tails cancel',
                      r'%dx - 10x = %d - %d \;\Rightarrow\; %dx = %d' % (big, joined, first, big - 10, joined - first)),
                 Line('Divide, then simplify', r'x = %s' % over(joined - first, big - 10))]
        return made(lines, frac_tex(value), long_division(value.numerator, value.denominator)[:3],
                    (0, [first], repeat))
    bottom = rng.choice((7, 11, 13, 27, 37))
    top = coprime_top(rng, bottom)
    whole, prefix, repeat, steps = long_division(top, bottom)
    place = rng.randint(15, 60)
    size = len(repeat)
    lots, extra = divmod(place, size)
    position = extra if extra else size
    digit = repeat[position - 1]
    lines = [Line('What is the %s digit after the decimal point when %d/%d is written as a decimal?'
                  % (ordinal(place), top, bottom)),
             Line('Divide it out', r'%s = %s' % (ft(top, bottom), recurring_tex(whole, prefix, repeat))),
             Line('The repeating block is %s: %d digit%s' % (''.join(map(str, repeat)), size, '' if size == 1 else 's'),
                  r'%d = %d \times %d + %d' % (place, lots, size, extra)),
             Line('So the %s digit is the %s digit of the block' % (ordinal(place), ordinal(position)),
                  r'%d' % digit)]
    rest = top
    for _ in range(place):                            # divide out every digit, the long way
        found, rest = divmod(rest * 10, bottom)
    return made(lines, str(digit), digit, found)
# --- Facts (editable) ---------------------------------------------------------

FACTS = [
    Fact('Know these', r'Common ones to know by heart.',
         tex=r'\begin{array}{c|c|c} \frac{1}{2} & 0.5 & 50\% \\ \frac{1}{4} & 0.25 & 25\% \\ '
             r'\frac{3}{4} & 0.75 & 75\% \\ \frac{1}{5} & 0.2 & 20\% \\ \frac{1}{8} & 0.125 & 12.5\% '
             r'\\ \frac{1}{3} & 0.\overset{\cdot}{3} & 33.\overset{\cdot}{3}\% \end{array}'),
    Fact('Fraction to decimal', r'Make the denominator $10$, $100$ or $1000$, or divide the top by the '
                                r'bottom.'),
    Fact('Decimal to fraction', r'Over $10$, $100$ or $1000$ by the number of decimal places, then '
                                r'simplify: $0.35 = \frac{35}{100} = \frac{7}{20}$.'),
    Fact('Percentages', r'Per cent means out of $100$: multiply a decimal by $100$, or divide a '
                        r'percentage by $100$.'),
    Fact('Recurring decimals', r'Dots go over the first and last digits of the repeating block: '
                               r'$0.\overset{\cdot}{1}4\overset{\cdot}{2} = 0.142142\ldots$'),
    Fact('Recurring to fraction', r'Multiply by $10^n$ for a block of $n$ digits, subtract the '
                                  r'original, and divide: $99x = 45$ gives $x = \frac{5}{11}$.'),
    Fact('Which decimals end', r'A fraction in its simplest form ends as a decimal only when its '
                               r'denominator has no prime factors but $2$ and $5$.'),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='fdp',
    title='Fractions, decimals and percentages',
    area='Number',
    keywords=('fdp', 'decimals', 'percentages', 'converting', 'fraction to decimal',
              'decimal to fraction', 'ordering', 'recurring decimals', 'dot notation',
              'recurring to fraction', 'short division'),
    intro='Decimals over powers of ten, percentages out of 100, recurring decimals by algebra.',
    facts=FACTS,
    stages=[
        Stage('convert', 'Fractions and decimals',
              r'Make the denominator a power of $10$; or put the decimal over one and simplify.',
              convert),
        Stage('percentages', 'All three together',
              r'Decimal $\times 100$ is the percentage; percentage $\div 100$ is the decimal.',
              percentages),
        Stage('ordering', 'Ordering',
              r'Change everything to decimals, order them, then write them back as they were given.',
              ordering),
        Stage('recurring', 'Recurring decimals',
              r'Divide the top by the bottom. When a remainder comes round again, the digits repeat.',
              recurring),
        Stage('recurring_fraction', 'Recurring to fraction',
              r'Call it $x$, multiply by $10^n$ for an $n$-digit block, subtract, divide.',
              recurring_fraction),
        Stage('problems', 'Stretch',
              r'Move the point past the part that does not repeat first. For far digits, use the '
              r'length of the block.',
              problems),
    ])
