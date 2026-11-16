"""Linear equations to practise on, each with a whole-number answer.

    from mathskit import generate

    generate.equation('brackets', seed=3)    # e.g. '4(x - 2) = 2x + 6'
    generate.mixed(10, seed=1)               # ten, every kind in turn

Kinds:
    one_step           x + a = b, ax = b, x/a = b
    two_step           ax + b = c, x/a + b = c
    fraction_one_side  (ax + b)/p = c
    stretch            b - ax = cx + d, -ax + b = c (answers may be fractions)
    both_sides     ax + b = cx + d
    brackets       a(x + b) = cx + d
    fractions      (x + a)/p = (x + b)/q
    two_brackets   a(x + b) - c(x + d) = e

Each is built backwards from its answer, so the answer is always a
whole number in ANSWER_RANGE (never 0). Pure Python. Later, mathsgen's
generators can feed practice instead.
"""
import random

# --- Settings (editable) ------------------------------------------------------
KINDS = ('both_sides', 'brackets', 'fractions', 'two_brackets')
ANSWER_RANGE = (-9, 12)               # inclusive
COEFFICIENTS = (2, 3, 4, 5, 6, 7)     # numbers in front of x and brackets
CONSTANTS = (-9, 9)                   # numbers inside brackets and beside x
DENOMINATORS = (2, 3, 4, 5)


def equation(kind, seed=None, rng=None):
    """One equation of kind, as text solve() reads."""
    rng = rng or random.Random(seed)
    build = BUILDERS[kind]
    for _ in range(200):
        text = build(rng)
        if text:
            return text
    raise RuntimeError('No %s equation found: widen the settings.' % kind)


def mixed(count, seed=None):
    """count equations, cycling through every kind in a shuffled order."""
    rng = random.Random(seed)
    kinds = list(KINDS)
    rng.shuffle(kinds)
    return [equation(kinds[index % len(kinds)], rng=rng) for index in range(count)]


# --- Writing numbers ----------------------------------------------------------

def unknown(a, var='x'):
    if a == 1:
        return var
    if a == -1:
        return '-' + var
    return '%d%s' % (a, var)


def plus(b):
    """' + 3', ' - 3', or nothing for 0."""
    if b == 0:
        return ''
    return ' + %d' % b if b > 0 else ' - %d' % -b


def answer(rng):
    low, high = ANSWER_RANGE
    return rng.choice([value for value in range(low, high + 1) if value != 0])


def constant(rng):
    low, high = CONSTANTS
    return rng.choice([value for value in range(low, high + 1) if value != 0])


# --- The kinds, built from the answer s ---------------------------------------

def both_sides(rng):
    s = answer(rng)
    a, c = rng.sample(COEFFICIENTS, 2)
    b = constant(rng)
    d = a * s + b - c * s
    return '%s%s = %s%s' % (unknown(a), plus(b), unknown(c), plus(d))


def brackets(rng):
    s = answer(rng)
    a = rng.choice(COEFFICIENTS)
    c = rng.choice([value for value in (1,) + COEFFICIENTS if value != a])
    b = constant(rng)
    d = a * (s + b) - c * s
    return '%d(x%s) = %s%s' % (a, plus(b), unknown(c), plus(d))


def fractions(rng):
    s = answer(rng)
    p, q = rng.sample(DENOMINATORS, 2)
    k = rng.choice([value for value in range(-4, 6) if value != 0])
    a, b = k * p - s, k * q - s
    if a == 0 or b == 0:
        return None
    return '(x%s)/%d = (x%s)/%d' % (plus(a), p, plus(b), q)


def two_brackets(rng):
    s = answer(rng)
    a, c = rng.sample(COEFFICIENTS[:5], 2)
    b, d = constant(rng), constant(rng)
    e = a * (s + b) - c * (s + d)
    return '%d(x%s) - %d(x%s) = %d' % (a, plus(b), c, plus(d), e)


# --- Lesson stages (mathskit/lessons/linear.py) -------------------------------

def one_step(rng):
    s = answer(rng)
    form = rng.choice(('add', 'times', 'over'))
    if form == 'add':
        a = constant(rng)
        return 'x%s = %d' % (plus(a), s + a)
    if form == 'times':
        a = rng.choice(COEFFICIENTS)
        return '%dx = %d' % (a, a * s)
    p = rng.choice(DENOMINATORS)
    return 'x/%d = %d' % (p, s)                    # answer is p * s


def two_step(rng):
    s = answer(rng)
    b = constant(rng)
    if rng.random() < 0.6:
        a = rng.choice(COEFFICIENTS)
        return '%s%s = %d' % (unknown(a), plus(b), a * s + b)
    p = rng.choice(DENOMINATORS)
    return 'x/%d%s = %d' % (p, plus(b), s + b)     # answer is p * s


def fraction_one_side(rng):
    s = answer(rng)
    p = rng.choice(DENOMINATORS)
    a = rng.choice((1,) + COEFFICIENTS[:3])
    b = constant(rng)
    top = a * s + b
    if top % p:
        return None
    return '(%s%s)/%d = %d' % (unknown(a), plus(b), p, top // p)


def stretch(rng):
    """Negative x terms; the answer is often a fraction."""
    a, c = rng.choice(COEFFICIENTS), rng.choice(COEFFICIENTS)
    b, d = constant(rng), constant(rng)
    if rng.random() < 0.5:
        return '%d - %s = %s%s' % (b, unknown(a), unknown(c), plus(d))   # b - ax = cx + d
    if b == d:
        return None
    return '%s%s = %d' % (unknown(-a), plus(b), d)                       # -ax + b = d


BUILDERS = {'both_sides': both_sides, 'brackets': brackets,
            'fractions': fractions, 'two_brackets': two_brackets,
            'one_step': one_step, 'two_step': two_step,
            'fraction_one_side': fraction_one_side, 'stretch': stretch}
