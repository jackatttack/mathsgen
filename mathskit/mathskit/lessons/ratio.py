"""Ratio, taught with the find-one method throughout: work out what one
part is worth, then multiply up. Sharing problems draw a bar model
(mathskit/diagrams.py) with one colour per person.

Problems carry meta got (through the find-one working) and expected
(straight from the formula) for tests/smoke_lessons.py to compare.
"""
import math
from fractions import Fraction as F
from functools import reduce

from .. import diagrams, numbers
from ..lesson import Fact, Lesson, Line, Problem, Stage, Worked
from ..numbers import frac_tex

NAMES = ('Ava', 'Ben', 'Cara', 'Dev', 'Eli', 'Fay', 'Gus', 'Hana')
GROUPS = (('boys', 'girls'), ('red', 'blue'), ('cats', 'dogs'), ('adults', 'children'))
INGREDIENTS = (('flour', 'g'), ('milk', 'ml'), ('sugar', 'g'), ('butter', 'g'), ('oats', 'g'))
num = numbers.text


# --- Helpers ------------------------------------------------------------------

def coprime_ratio(rng, count, low=1, high=7):
    while True:
        parts = [rng.randint(low, high) for _ in range(count)]
        if reduce(math.gcd, parts) == 1 and len(set(parts)) > 1:
            return parts


def ratio_text(parts):
    return ' : '.join(str(part) for part in parts)


def and_list(words):
    return words[0] if len(words) == 1 else ', '.join(words[:-1]) + ' and ' + words[-1]


def made(lines, answer, got, expected, figure=None):
    return Problem(statement=lines[0].tex or lines[0].say, answer=answer,
                   solution=Worked(lines, answer), meta={'got': got, 'expected': expected},
                   figure=figure)


def one_part_line(amount, parts, one):
    return Line('Find one part', r'1 \text{ part} = %s \div %d = %s' % (num(amount), parts, num(one)))


# --- Stages -------------------------------------------------------------------

def simplify(rng):
    base = coprime_ratio(rng, 3 if rng.random() < 0.3 else 2, 1, 9)
    k = rng.randint(2, 12)
    given = [k * part for part in base]
    hcf = reduce(math.gcd, given)
    simplest = [part // hcf for part in given]
    lines = [Line('Write the ratio in its simplest form', ratio_text(given)),
             Line('Find the highest common factor of the parts', r'\text{HCF} = %d' % hcf),
             Line('Divide every part by %d' % hcf,
                  r'%s \;\to\; %s' % (ratio_text(given), ratio_text(simplest)))]
    return made(lines, ratio_text(simplest), simplest, base)


def share(rng):
    count = 3 if rng.random() < 0.3 else 2
    parts = coprime_ratio(rng, count)
    who = rng.sample(NAMES, count)
    total_parts, one = sum(parts), rng.randint(2, 25)
    amount = one * total_parts
    shares = [one * part for part in parts]
    lines = [Line('Share %d in the ratio %s between %s' % (amount, ratio_text(parts), and_list(who))),
             Line('Add the parts', r'%s = %d \text{ parts}' % (' + '.join(map(str, parts)), total_parts)),
             one_part_line(amount, total_parts, one),
             Line('Multiply up for each person', r', \quad '.join(
                 r'\text{%s} = %d \times %d = %d' % (name, part, one, value)
                 for name, part, value in zip(who, parts, shares))),
             Line('Check: the shares add up to %d' % amount,
                  r'%s = %d' % (' + '.join(map(str, shares)), sum(shares)))]
    answer = ', '.join('%s %d' % pair for pair in zip(who, shares))
    figure = diagrams.bar_model(parts, who, total=str(amount))
    return made(lines, answer, shares, [F(amount * part, total_parts) for part in parts], figure)


def one_share_known(rng):
    parts = coprime_ratio(rng, 2)
    who = rng.sample(NAMES, 2)
    one = rng.randint(2, 20)
    known, other = rng.sample((0, 1), 2)
    known_value = parts[known] * one
    ask_total = rng.random() < 0.35
    ask = ('How much is there altogether?' if ask_total
           else 'How much does %s get?' % who[other])
    lines = [Line('%s and %s share some money in the ratio %s. %s gets %d. %s'
                  % (who[0], who[1], ratio_text(parts), who[known], known_value, ask)),
             Line('%s has %d parts' % (who[known], parts[known]),
                  r'%d \text{ parts} = %d' % (parts[known], known_value)),
             one_part_line(known_value, parts[known], one)]
    wanted = sum(parts) if ask_total else parts[other]
    value = wanted * one
    say = ('Altogether there are %d parts' % wanted if ask_total
           else '%s has %d parts' % (who[other], wanted))
    lines.append(Line(say, r'%d \text{ parts} = %d \times %d = %d' % (wanted, wanted, one, value)))
    values = [None, None]
    values[known] = str(known_value)
    figure = diagrams.bar_model(parts, who, values=values, total='?' if ask_total else None)
    expected = F(known_value, parts[known]) * wanted
    return made(lines, str(value), value, expected, figure)


def difference(rng):
    parts = coprime_ratio(rng, 2)
    who = rng.sample(NAMES, 2)
    one = rng.randint(2, 15)
    big, small = (0, 1) if parts[0] > parts[1] else (1, 0)
    gap_parts = parts[big] - parts[small]
    gap = gap_parts * one
    shares = [part * one for part in parts]
    lines = [Line('%s and %s share sweets in the ratio %s. %s gets %d more than %s. How many '
                  'does each get?' % (who[0], who[1], ratio_text(parts), who[big], gap, who[small])),
             Line('The difference is %d parts' % gap_parts,
                  r'%d - %d = %d \text{ parts} = %d' % (parts[big], parts[small], gap_parts, gap)),
             one_part_line(gap, gap_parts, one),
             Line('Multiply up for each person', r', \quad '.join(
                 r'\text{%s} = %d \times %d = %d' % (name, part, one, value)
                 for name, part, value in zip(who, parts, shares)))]
    answer = ', '.join('%s %d' % pair for pair in zip(who, shares))
    figure = diagrams.bar_model(parts, who)
    expected = [F(gap, gap_parts) * part for part in parts]
    return made(lines, answer, shares, expected, figure)


def ratio_fraction(rng):
    parts = coprime_ratio(rng, 2, 1, 9)
    groups = rng.choice(GROUPS)
    which = rng.randint(0, 1)
    total_parts = sum(parts)
    total = total_parts * rng.randint(2, 12)
    fraction = F(parts[which], total_parts)
    count = fraction * total
    shown = r'\frac{%d}{%d}' % (parts[which], total_parts)
    if fraction.denominator != total_parts:
        shown += ' = ' + frac_tex(fraction)
    lines = [Line('The ratio of %s to %s is %s. There are %d altogether. What fraction are %s, '
                  'and how many is that?' % (groups[0], groups[1], ratio_text(parts), total,
                                            groups[which])),
             Line('Add the parts', r'%d + %d = %d \text{ parts}' % (parts[0], parts[1], total_parts)),
             Line('%s are %d of the %d parts' % (groups[which].capitalize(), parts[which],
                                                 total_parts), shown),
             Line('Take that fraction of %d' % total,
                  r'\frac{%d}{%d} \times %d = %s' % (parts[which], total_parts, total, num(count)))]
    figure = diagrams.bar_model(parts, list(groups), total=str(total))
    return made(lines, '%s, which is %s' % (frac_tex(fraction), num(count)), count,
                F(total, total_parts) * parts[which], figure)


def recipe(rng):
    while True:
        people = rng.choice((2, 3, 4, 5, 6, 8))
        new = rng.choice([value for value in range(2, 13) if value != people])
        per = rng.choice([F(value) for value in range(10, 125, 5)]
                         + [F(value, 2) for value in range(25, 155, 10)])
        if (per * people).denominator == 1:
            break
    item, unit = rng.choice(INGREDIENTS)
    amount, result = per * people, per * new
    lines = [Line('A recipe for %d people uses %s %s of %s. How much %s is needed for %d people?'
                  % (people, num(amount), unit, item, item, new)),
             Line('Find the amount for one person',
                  r'%s \div %d = %s' % (num(amount), people, num(per))),
             Line('Multiply up for %d people' % new, r'%s \times %d = %s' % (num(per), new, num(result))),
             Line('Answer', r'%s \text{ %s of %s}' % (num(result), unit, item))]
    return made(lines, '%s %s' % (num(result), unit), result, amount * new / F(people))


def combining(rng):
    who = rng.sample(NAMES, 3)
    while True:
        a, b1 = coprime_ratio(rng, 2, 1, 9)
        b2, c = coprime_ratio(rng, 2, 1, 9)
        if b1 != b2:
            break
    lcm = b1 * b2 // math.gcd(b1, b2)
    k1, k2 = lcm // b1, lcm // b2
    joined = [a * k1, lcm, c * k2]
    hcf = reduce(math.gcd, joined)
    simplest = [part // hcf for part in joined]
    lines = [Line('%s : %s = %d : %d and %s : %s = %d : %d. Write %s : %s : %s in its simplest form.'
                  % (who[0], who[1], a, b1, who[1], who[2], b2, c, who[0], who[1], who[2])),
             Line('%s is in both ratios: make their parts match' % who[1],
                  r'\text{LCM of } %d \text{ and } %d = %d' % (b1, b2, lcm)),
             Line('Scale the first ratio by %d' % k1,
                  r'%d : %d = %d : %d' % (a, b1, a * k1, lcm)),
             Line('Scale the second ratio by %d' % k2,
                  r'%d : %d = %d : %d' % (b2, c, lcm, c * k2)),
             Line('Put them together', ratio_text(joined))]
    if hcf > 1:
        lines.append(Line('Simplify: divide by %d' % hcf, ratio_text(simplest)))
    got = (F(simplest[0], simplest[1]), F(simplest[1], simplest[2]))
    return made(lines, ratio_text(simplest), got, (F(a, b1), F(b2, c)))


def k_term(n):
    return 'k' if n == 1 else '%dk' % n


def problems(rng):
    """Stretch: the ratio changes after counters are added or sweets move.
    Call one part k, write the new ratio, cross multiply, solve."""
    if rng.random() < 0.5:
        while True:
            a, b = coprime_ratio(rng, 2, 1, 7)
            p, q = coprime_ratio(rng, 2, 1, 5)
            if F(p, q) <= F(a, b):
                continue
            k = q * rng.randint(1, 6)
            t = p * b * k // q - a * k
            if 0 < t <= 40:
                break
        blue = b * k
        lines = [Line('A bag has red and blue counters in the ratio %s. %d more red counters are '
                      'added and the ratio becomes %s. How many blue counters are there?'
                      % (ratio_text([a, b]), t, ratio_text([p, q]))),
                 Line('Call one part k', r'\text{red} = %s, \quad \text{blue} = %s' % (k_term(a), k_term(b))),
                 Line('After adding the red counters',
                      r'(%s + %d) : %s = %d : %d' % (k_term(a), t, k_term(b), p, q)),
                 Line('Cross multiply', r'%d(%s + %d) = %d \times %s' % (q, k_term(a), t, p, k_term(b))),
                 Line('Expand and solve', r'%s + %d = %s \;\Rightarrow\; %s = %d \;\Rightarrow\; k = %d'
                      % (k_term(q * a), q * t, k_term(p * b), k_term(p * b - q * a), q * t, k)),
                 Line('Blue counters', r'%s = %d \times %d = %d' % (k_term(b), b, k, blue))]
        return made(lines, '%d blue counters' % blue, blue, b * F(q * t, p * b - q * a))
    while True:
        a, b = coprime_ratio(rng, 2, 1, 7)
        p, q = coprime_ratio(rng, 2, 1, 5)
        if q * a <= p * b:
            continue
        k = rng.randint(2, 12)
        top = (q * a - p * b) * k
        if top % (p + q):
            continue
        t = top // (p + q)
        if 0 < t < a * k:
            break
    who = rng.sample(NAMES, 2)
    start = a * k
    lines = [Line('%s and %s have sweets in the ratio %s. %s gives %s %d sweets and the ratio '
                  'becomes %s. How many sweets did %s have at the start?'
                  % (who[0], who[1], ratio_text([a, b]), who[0], who[1], t, ratio_text([p, q]),
                     who[0])),
             Line('Call one part k', r'\text{%s} = %s, \quad \text{%s} = %s'
                  % (who[0], k_term(a), who[1], k_term(b))),
             Line('After %d sweets move' % t,
                  r'(%s - %d) : (%s + %d) = %d : %d' % (k_term(a), t, k_term(b), t, p, q)),
             Line('Cross multiply', r'%d(%s - %d) = %d(%s + %d)' % (q, k_term(a), t, p, k_term(b), t)),
             Line('Expand and solve',
                  r'%s - %d = %s + %d \;\Rightarrow\; %s = %d \;\Rightarrow\; k = %d'
                  % (k_term(q * a), q * t, k_term(p * b), p * t, k_term(q * a - p * b),
                     (p + q) * t, k)),
             Line('%s at the start' % who[0], r'%s = %d \times %d = %d' % (k_term(a), a, k, start))]
    return made(lines, '%d sweets' % start, start, a * F((p + q) * t, q * a - p * b))
# --- Facts (editable) ---------------------------------------------------------

FACTS = [
    Fact('Find one part', r'The key move: if $3$ parts $= 45$, then $1$ part $= 15$. Then '
                          r'multiply up for whatever you need.',
         diagrams.bar_model([3, 5], ['A', 'B'], values=['45', None])),
    Fact('Sharing', r'Add the parts, find one part, multiply up: $40$ in $2 : 3$ is $5$ parts, '
                    r'$1$ part $= 8$, so $16$ and $24$.',
         diagrams.bar_model([2, 3], ['A', 'B'], total='40')),
    Fact('Simplifying', r'Divide every part by the highest common factor: '
                        r'$12 : 18 = 2 : 3$.'),
    Fact('Order matters', r'$2 : 3$ is not $3 : 2$. Keep the ratio in the order the question '
                          r'gives the names.'),
    Fact('Ratio and fractions', r'In $2 : 3$ there are $5$ parts, so the first share is '
                                r'$\frac{2}{5}$ of the total and the second is $\frac{3}{5}$.'),
    Fact('Difference', r'If one share is bigger by an amount, that amount is the difference '
                       r'in parts: $7 : 2$ differ by $5$ parts.'),
    Fact('Recipes and proportion', r'Find the amount for one, then multiply: $300$ g for $4$ '
                                   r'people is $75$ g each, so $450$ g for $6$.'),
    Fact('Combining ratios', r'Make the shared part the same with the LCM: $A : B = 2 : 3$ and '
                             r'$B : C = 4 : 5$ give $8 : 12 : 15$.'),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='ratio',
    title='Ratio',
    area='Number',
    keywords=('ratio', 'share', 'sharing', 'proportion', 'recipe', 'find one', 'parts',
              'direct proportion', 'simplify ratio', 'bar model'),
    intro='Find what one part is worth, then multiply up.',
    facts=FACTS,
    stages=[
        Stage('simplify', 'Simplifying',
              r'Divide every part by the highest common factor.',
              simplify),
        Stage('share', 'Sharing',
              r'Add the parts, find one part by dividing, then multiply up for each share. '
              r'Check they add up.',
              share),
        Stage('one_share_known', 'One share known',
              r'You know what some of the parts are worth: find one part, then multiply up.',
              one_share_known),
        Stage('difference', 'Difference known',
              r'The difference between the shares is the difference in parts: find one part '
              r'from that.',
              difference),
        Stage('ratio_fraction', 'Ratio and fractions',
              r'A share is its parts over the total parts: in $3 : 5$ the second is '
              r'$\frac{5}{8}$ of the total.',
              ratio_fraction),
        Stage('recipe', 'Recipes (find one)',
              r'Find the amount for one, then multiply up for the number you need.',
              recipe),
        Stage('combining', 'Combining ratios',
              r'Make the part the two ratios share the same, using the LCM, then write all '
              r'three together.',
              combining),
        Stage('problems', 'Stretch',
              r'When the ratio changes: call one part $k$, write the new ratio with $k$ in it, '
              r'cross multiply and solve.',
              problems),
    ])
