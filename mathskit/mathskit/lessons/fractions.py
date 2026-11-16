"""Fractions: equivalent fractions and simplifying, mixed numbers, adding
and subtracting, mixed numbers added and taken away, multiplying, dividing,
fractions of amounts, then Stretch.

Problems carry meta got (from the working) and expected (Fraction
arithmetic, or the value the question was built from) for
tests/smoke_lessons.py. Fractions of amounts draw a bar model.
"""
import math
from fractions import Fraction as F

from .. import diagrams
from ..lesson import Fact, Lesson, Line, Problem, Stage, Worked
from ..numbers import frac_tex


# --- Helpers ------------------------------------------------------------------

def ft(top, bottom):
    """A fraction exactly as written, not simplified."""
    return r'\frac{%d}{%d}' % (top, bottom)


def mixed_tex(value):
    """A positive fraction as a whole number, a proper fraction or a mixed number."""
    whole, rest = divmod(value.numerator, value.denominator)
    if rest == 0:
        return str(whole)
    if whole == 0:
        return ft(rest, value.denominator)
    return r'%d%s' % (whole, ft(rest, value.denominator))


def proper(rng, low, high):
    """A proper fraction in its simplest form, as (top, bottom)."""
    bottom = rng.randint(low, high)
    return rng.choice([top for top in range(1, bottom) if math.gcd(top, bottom) == 1]), bottom


def two_proper(rng, low, high):
    """Two proper fractions with different denominators."""
    while True:
        a, b = proper(rng, low, high)
        c, d = proper(rng, low, high)
        if b != d:
            return a, b, c, d


def tidy_line(top, bottom):
    """A last line that simplifies or makes a mixed number, or None when the
    fraction is already as simple as it gets."""
    value = F(top, bottom)
    if value.denominator == bottom and value < 1:
        return None
    return Line('Simplify' if value < 1 else 'Simplify and write as a mixed number',
                r'%s = %s' % (ft(top, bottom), mixed_tex(value)))


def made(lines, answer, got, expected, figure=None):
    lines = [line for line in lines if line is not None]
    return Problem(statement=lines[0].tex or lines[0].say, answer=answer,
                   solution=Worked(lines, answer), meta={'got': got, 'expected': expected},
                   figure=figure)


# --- Stages -------------------------------------------------------------------

def equivalent(rng):
    a, b = proper(rng, 2, 12)
    k = rng.randint(2, 9)
    if rng.random() < 0.5:
        top, bottom = k * a, k * b
        h = math.gcd(top, bottom)
        lines = [Line('Write %d/%d in its simplest form.' % (top, bottom)),
                 Line('Find the highest common factor of %d and %d' % (top, bottom), r'\text{HCF} = %d' % h),
                 Line('Divide the top and the bottom by %d' % h,
                      r'%s = %s' % (ft(top, bottom), ft(top // h, bottom // h)))]
        return made(lines, ft(a, b), (top // h, bottom // h), (a, b))
    lines = [Line('Find the missing number: %d/%d = ?/%d.' % (a, b, k * b)),
             Line('The bottom was multiplied by %d' % k, r'%d \times %d = %d' % (b, k, k * b)),
             Line('Do the same to the top', r'%d \times %d = %d' % (a, k, k * a)),
             Line('So', r'%s = %s' % (ft(a, b), ft(k * a, k * b)))]
    return made(lines, str(k * a), k * a, F(a, b) * (k * b))


def mixed(rng):
    a, b = proper(rng, 2, 12)
    whole = rng.randint(1, 9)
    top = whole * b + a
    if rng.random() < 0.5:
        lines = [Line('Write %d %d/%d as an improper fraction.' % (whole, a, b)),
                 Line('Multiply the whole number by the denominator', r'%d \times %d = %d' % (whole, b, whole * b)),
                 Line('Add the numerator', r'%d + %d = %d' % (whole * b, a, top)),
                 Line('Over the same denominator', r'%s = %s' % (mixed_tex(whole + F(a, b)), ft(top, b)))]
        return made(lines, ft(top, b), F(whole * b + a, b), whole + F(a, b))
    times, left = divmod(top, b)
    lines = [Line('Write %d/%d as a mixed number.' % (top, b)),
             Line('Divide: how many whole lots of %d fit, and what is left' % b,
                  r'%d \div %d = %d \text{ remainder } %d' % (top, b, times, left)),
             Line('The whole number, then the remainder over %d' % b,
                  r'%s = %s' % (ft(top, b), mixed_tex(F(top, b))))]
    return made(lines, mixed_tex(F(top, b)), times + F(left, b), F(top, b))


def add_subtract(rng):
    a, b, c, d = two_proper(rng, 2, 12)
    subtract = rng.random() < 0.5
    if subtract and F(a, b) < F(c, d):
        a, b, c, d = c, d, a, b
    sign = '-' if subtract else '+'
    m = b * d // math.gcd(b, d)
    a2, c2 = a * (m // b), c * (m // d)
    top = a2 - c2 if subtract else a2 + c2
    lines = [Line('Work out', r'%s %s %s' % (ft(a, b), sign, ft(c, d))),
             Line('Make the denominators the same: the LCM of %d and %d is %d' % (b, d, m),
                  r'%s = %s, \quad %s = %s' % (ft(a, b), ft(a2, m), ft(c, d), ft(c2, m))),
             Line('%s the numerators' % ('Subtract' if subtract else 'Add'),
                  r'%s %s %s = %s' % (ft(a2, m), sign, ft(c2, m), ft(top, m))),
             tidy_line(top, m)]
    expected = F(a, b) - F(c, d) if subtract else F(a, b) + F(c, d)
    return made(lines, mixed_tex(F(top, m)), F(top, m), expected)


def mixed_add(rng):
    a, b, c, d = two_proper(rng, 2, 10)
    w1, w2 = rng.randint(1, 5), rng.randint(1, 5)
    x, y = w1 + F(a, b), w2 + F(c, d)
    subtract = rng.random() < 0.5
    if subtract and x < y:
        (x, a, b, w1), (y, c, d, w2) = (y, c, d, w2), (x, a, b, w1)
    sign = '-' if subtract else '+'
    t1, t2 = w1 * b + a, w2 * d + c
    m = b * d // math.gcd(b, d)
    s1, s2 = t1 * (m // b), t2 * (m // d)
    top = s1 - s2 if subtract else s1 + s2
    lines = [Line('Work out', r'%s %s %s' % (mixed_tex(x), sign, mixed_tex(y))),
             Line('Change both to improper fractions',
                  r'%s = %s, \quad %s = %s' % (mixed_tex(x), ft(t1, b), mixed_tex(y), ft(t2, d))),
             Line('Give them a common denominator, %d' % m, r'%s %s %s' % (ft(s1, m), sign, ft(s2, m))),
             Line('%s the numerators' % ('Subtract' if subtract else 'Add'), r'= %s' % ft(top, m)),
             tidy_line(top, m)]
    return made(lines, mixed_tex(F(top, m)), F(top, m), x - y if subtract else x + y)


def times_or_divide(rng, divide):
    a, b = proper(rng, 2, 10)
    c, d = proper(rng, 2, 10)
    use_mixed = rng.random() < 0.35
    whole = rng.randint(1, 4) if use_mixed else 0
    x, y = whole + F(a, b), F(c, d)
    t1 = whole * b + a
    sign = r'\div' if divide else r'\times'
    lines = [Line('Work out', r'%s %s %s' % (mixed_tex(x), sign, ft(c, d)))]
    if use_mixed:
        lines.append(Line('Change the mixed number to an improper fraction', r'%s = %s' % (mixed_tex(x), ft(t1, b))))
    if divide:
        lines.append(Line('Keep the first, flip the second, change divide to times',
                          r'%s \div %s = %s \times %s' % (ft(t1, b), ft(c, d), ft(t1, b), ft(d, c))))
        second = (d, c)
    else:
        second = (c, d)
    top, bottom = t1 * second[0], b * second[1]
    lines.append(Line('Multiply the tops, multiply the bottoms',
                      r'%s \times %s = %s' % (ft(t1, b), ft(*second), ft(top, bottom))))
    lines.append(tidy_line(top, bottom))
    return made(lines, mixed_tex(F(top, bottom)), F(top, bottom), x / y if divide else x * y)


def multiply(rng):
    return times_or_divide(rng, divide=False)


def divide(rng):
    return times_or_divide(rng, divide=True)


def of_amount(rng):
    a, b = proper(rng, 2, 12)
    names = ['%d/%d' % (a, b), 'the rest']
    if rng.random() < 0.6:
        amount = b * rng.randint(2, 20)
        one = amount // b
        lines = [Line('Find %d/%d of %d.' % (a, b, amount)),
                 Line('Find one part: divide by the denominator', r'%d \div %d = %d' % (amount, b, one)),
                 Line('Multiply by the numerator', r'%d \times %d = %d' % (one, a, one * a))]
        figure = diagrams.bar_model([a, b - a], names, total=str(amount))
        return made(lines, str(one * a), one * a, F(a, b) * amount, figure)
    whole = b * rng.randint(2, 20)
    one = whole // b
    part = one * a
    lines = [Line('%d/%d of a number is %d. What is the number?' % (a, b, part)),
             Line('%d parts are worth %d, so find one part' % (a, part), r'%d \div %d = %d' % (part, a, one)),
             Line('The whole is %d parts' % b, r'%d \times %d = %d' % (one, b, whole))]
    figure = diagrams.bar_model([a, b - a], names, values=[str(part), None], total='?')
    return made(lines, str(whole), whole, F(part) / F(a, b), figure)


def problems(rng):
    """Stretch: what is left after spending twice, or a tank's capacity
    from the change in how full it is. Both end by dividing by a fraction."""
    if rng.random() < 0.5:
        pn, pd = proper(rng, 2, 6)
        qn, qd = proper(rng, 2, 6)
        p, q = F(pn, pd), F(qn, qd)
        kept = (1 - p) * (1 - q)
        start = pd * qd * rng.randint(2, 12) * 5
        left = start * kept
        lines = [Line('Mia spends %d/%d of her money on a coat and %d/%d of what is left on shoes. '
                      'She has \u00a3%d left. How much did she start with?' % (pn, pd, qn, qd, left)),
                 Line('After the coat, this fraction is left', r'1 - %s = %s' % (ft(pn, pd), frac_tex(1 - p))),
                 Line('The shoes take %d/%d of that, so she keeps the rest of it' % (qn, qd),
                      r'%s \times %s = %s' % (frac_tex(1 - p), frac_tex(1 - q), frac_tex(kept))),
                 Line('That fraction of her money is what she has left',
                      r'%s \text{ of the total} = %d' % (frac_tex(kept), left)),
                 Line('Divide by the fraction to find the total', r'%d \div %s = %d' % (left, frac_tex(kept), start))]
        return made(lines, r'\pounds %d' % start, left / kept, start)
    while True:
        a, b = proper(rng, 2, 8)
        c, d = proper(rng, 2, 8)
        if F(c, d) > F(a, b):
            break
    gap = F(c, d) - F(a, b)
    capacity = (b * d // math.gcd(b, d)) * rng.randint(2, 12)
    added = capacity * gap
    lines = [Line('A tank is %d/%d full. When %d litres are added it is %d/%d full. How much does '
                  'the tank hold when full?' % (a, b, added, c, d)),
             Line('The water added fills the difference', r'%s - %s = %s' % (ft(c, d), ft(a, b), frac_tex(gap))),
             Line('So that fraction of the tank is %d litres' % added,
                  r'%s \text{ of the tank} = %d' % (frac_tex(gap), added)),
             Line('Divide to find the whole tank', r'%d \div %s = %d' % (added, frac_tex(gap), capacity))]
    return made(lines, r'%d \text{ litres}' % capacity, added / gap, capacity)
# --- Facts (editable) ---------------------------------------------------------

FACTS = [
    Fact('Equivalent fractions', r'Multiply or divide the top and bottom by the same number: '
                                 r'$\frac{2}{3} = \frac{8}{12}$.'),
    Fact('Simplest form', r'Divide the top and bottom by their highest common factor: '
                          r'$\frac{18}{24} = \frac{3}{4}$.'),
    Fact('Mixed numbers', r'$2\frac{3}{5} = \frac{2 \times 5 + 3}{5} = \frac{13}{5}$.'),
    Fact('Adding and subtracting', r'Same denominator first (the LCM), then add or subtract the '
                                   r'numerators only.'),
    Fact('Multiplying', r'Tops times tops, bottoms times bottoms. Mixed numbers become improper '
                        r'first.'),
    Fact('Dividing', r'Keep, flip, change: $\frac{2}{3} \div \frac{4}{5} = \frac{2}{3} \times '
                     r'\frac{5}{4}$.'),
    Fact('Fraction of an amount', r'Divide by the bottom, times by the top: $\frac{3}{5}$ of '
                                  r'$40$ is $40 \div 5 \times 3 = 24$.',
         diagrams.bar_model([3, 2], ['3/5', 'the rest'], total='40')),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='fractions',
    title='Fractions',
    area='Number',
    keywords=('fractions', 'equivalent', 'simplify', 'simplest form', 'mixed numbers',
              'improper fractions', 'add fractions', 'subtract fractions', 'multiply fractions',
              'divide fractions', 'keep flip change', 'fraction of an amount', 'reverse fractions'),
    intro='Common denominators to add; tops times tops to multiply; flip to divide.',
    facts=FACTS,
    stages=[
        Stage('equivalent', 'Equivalent fractions',
              r'Do the same to the top and the bottom. Simplify by dividing by the HCF.',
              equivalent),
        Stage('mixed', 'Mixed numbers',
              r'Whole times denominator, plus the numerator. Back again: divide and keep the remainder.',
              mixed),
        Stage('add_subtract', 'Adding and subtracting',
              r'Change both to the same denominator (the LCM), then add or subtract the tops.',
              add_subtract),
        Stage('mixed_add', 'Mixed numbers: add and subtract',
              r'Change to improper fractions first, then use a common denominator.',
              mixed_add),
        Stage('multiply', 'Multiplying',
              r'Tops times tops, bottoms times bottoms, then simplify.',
              multiply),
        Stage('divide', 'Dividing',
              r'Keep the first, flip the second, change $\div$ to $\times$.',
              divide),
        Stage('of_amount', 'Fractions of amounts',
              r'Divide by the bottom to find one part, times by the top. Backwards: divide by the '
              r'top, times by the bottom.',
              of_amount),
        Stage('problems', 'Stretch',
              r'Track what fraction is left, then divide the amount by that fraction to find the whole.',
              problems),
    ])
