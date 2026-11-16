"""Expanding and factorising: a single bracket up to factorising
ax^2 + bx + c by splitting the middle term.

Problems carry meta['forms']: the question, intermediate lines and answer
as Python, which tests/smoke_lessons.py evaluates at random values. Every
form must agree, so a wrong factorisation fails the test.
"""
import math

from .. import algebra
from ..algebra import Term, mono
from ..lesson import Fact, Lesson, Line, Problem, Stage, Worked

X = mono('x')
X2 = mono('x^2')
tex = algebra.tex
plain = algebra.plain


def nonzero(rng, size=9):
    return rng.choice([value for value in range(-size, size + 1) if value])


def worked(lines, forms):
    answer = lines[-1].tex
    return Problem(statement=lines[0].tex, answer=answer, solution=Worked(lines, answer),
                   meta={'forms': forms})


def pair_tex(first, second, joiner):
    return r'%s %s %s' % (algebra.number_tex(first), joiner, algebra.number_tex(second))


# --- Stages -------------------------------------------------------------------

def expand_single(rng):
    outside = rng.choice([Term(k) for k in (2, 3, 4, 5, 6, 7, -2, -3, -4, -5)]
                         + [Term(1, X), Term(2, X), Term(3, X), Term(-1, X)])
    inside = [Term(rng.choice((1, 1, 2, 3, 4, 5)), X), Term(nonzero(rng))]
    result = algebra.expand(outside, inside)
    products = ' + '.join(r'%s \times %s' % (algebra.factor_tex(outside), algebra.factor_tex(term))
                          for term in inside)
    lines = [Line('Expand', algebra.bracket_tex(outside, inside)),
             Line('Multiply every term inside the bracket by the term outside', products),
             Line('Answer', tex(result))]
    return worked(lines, [algebra.bracket_plain(outside, inside), plain(result)])


def factorise_single(rng):
    with_x = rng.random() < 0.5
    while True:
        a, b = rng.randint(1, 6), nonzero(rng)
        if math.gcd(a, abs(b)) == 1:
            break
    hcf = Term(rng.randint(1, 5), X) if with_x else Term(rng.randint(2, 9))
    inside = [Term(a, X), Term(b)]
    question = algebra.expand(hcf, inside)
    divisions = r', \quad '.join(
        r'%s \div %s = %s' % (algebra.signed_tex(whole), algebra.signed_tex(hcf), algebra.signed_tex(part))
        for whole, part in zip(question, inside))
    lines = [Line('Factorise', tex(question)),
             Line('Find the highest common factor of every term',
                  r'\text{HCF} = %s' % algebra.signed_tex(hcf)),
             Line('Divide each term by the HCF', divisions),
             Line('Write the HCF outside the bracket', algebra.bracket_tex(hcf, inside))]
    return worked(lines, [plain(question), algebra.bracket_plain(hcf, inside)])


def expand_simplify(rng):
    k1 = rng.randint(2, 6)
    k2 = rng.choice([value for value in range(-6, 7) if value not in (0, 1, -1)])
    first = [Term(rng.choice((1, 1, 2, 3)), X), Term(nonzero(rng))]
    second = [Term(rng.choice((1, 1, 2, 3)), X), Term(nonzero(rng))]
    expanded = algebra.expand(Term(k1), first) + algebra.expand(Term(k2), second)
    result = algebra.collect(expanded)
    question = '%s %s %s' % (algebra.bracket_tex(Term(k1), first), '-' if k2 < 0 else '+',
                             algebra.bracket_tex(Term(abs(k2)), second))
    colours = algebra.family_colours(expanded)
    lines = [Line('Expand and simplify', question),
             Line('Expand each bracket; the sign in front goes with its number',
                  tex(expanded, colours)),
             Line('Collect like terms', tex(result))]
    forms = [algebra.bracket_plain(Term(k1), first) + '+' + algebra.bracket_plain(Term(k2), second),
             plain(expanded), plain(result)]
    return worked(lines, forms)


def double(rng):
    kind = rng.choice(('simple', 'simple', 'coefficients', 'square'))
    a, b = nonzero(rng), nonzero(rng)
    p = q = 1
    if kind == 'coefficients':
        p, q = rng.randint(1, 4), rng.randint(2, 5)
    if kind == 'square':
        b = a
    first = [Term(p, X), Term(a)]
    second = [Term(q, X), Term(b)]
    products = [algebra.multiply(left, right) for left in first for right in second]
    result = algebra.collect(products)
    lines = [Line('Expand', '(%s)^{2}' % tex(first) if kind == 'square'
                  else '(%s)(%s)' % (tex(first), tex(second)))]
    if kind == 'square':
        lines.append(Line('Squaring means times by itself', '(%s)(%s)' % (tex(first), tex(first))))
    lines += [Line('Times each term in the first bracket by each term in the second',
                   tex(products, algebra.family_colours(products))),
              Line('Collect the x terms', tex(result))]
    forms = ['(%s)*(%s)' % (plain(first), plain(second)), plain(products), plain(result)]
    return worked(lines, forms)


def factorise_quadratic(rng):
    while True:
        p, q = sorted((nonzero(rng), nonzero(rng)))
        if p + q:
            break
    b, c = p + q, p * q
    question = [Term(1, X2), Term(b, X), Term(c)]
    answer = '(%s)(%s)' % (tex([Term(1, X), Term(p)]), tex([Term(1, X), Term(q)]))
    lines = [Line('Factorise', tex(question)),
             Line('Find two numbers that multiply to %d and add to %d' % (c, b),
                  r'%s = %d, \quad %s = %d' % (pair_tex(p, q, r'\times'), c, pair_tex(p, q, '+'), b)),
             Line('Write them in the brackets', answer)]
    forms = [plain(question), '(x+(%d))*(x+(%d))' % (p, q)]
    return worked(lines, forms)


def dots(rng):
    while True:
        a, b = rng.choice((1, 1, 2, 3, 4, 5)), rng.randint(1, 12)
        if math.gcd(a, b) == 1:
            break
    question = [Term(a * a, X2), Term(-b * b)]
    ax = algebra.signed_tex(Term(a, X))
    lines = [Line('Factorise', tex(question)),
             Line('Both terms are squares, with a minus between them',
                  r'%s = (%s)^{2}, \quad %d = %d^{2}' % (algebra.signed_tex(Term(a * a, X2)), ax,
                                                         b * b, b)),
             Line('Difference of two squares', r'A^{2} - B^{2} = (A + B)(A - B)'),
             Line('Answer', '(%s + %d)(%s - %d)' % (ax, b, ax, b))]
    forms = [plain(question), '((%d)*x+(%d))*((%d)*x-(%d))' % (a, b, a, b)]
    return worked(lines, forms)


def factorise_ax2(rng):
    while True:
        p, q = rng.randint(1, 3), rng.randint(2, 5)
        a, b = nonzero(rng, 7), nonzero(rng, 7)
        if math.gcd(p, abs(a)) != 1 or math.gcd(q, abs(b)) != 1:
            continue
        if p * b + q * a:
            break
    big_a, big_b, big_c = p * q, p * b + q * a, a * b
    m, n = p * b, q * a
    inner = [Term(q, X), Term(b)]
    question = [Term(big_a, X2), Term(big_b, X), Term(big_c)]
    split = [Term(big_a, X2), Term(m, X), Term(n, X), Term(big_c)]
    pairs = '%s %s %s' % (algebra.bracket_tex(Term(p, X), inner), '-' if a < 0 else '+',
                          algebra.bracket_tex(Term(abs(a)), inner))
    answer = '(%s)(%s)' % (tex([Term(p, X), Term(a)]), tex(inner))
    lines = [Line('Factorise', tex(question)),
             Line('Multiply the x\u00b2 number by the number term',
                  r'%d \times %s = %d' % (big_a, algebra.number_tex(big_c), big_a * big_c)),
             Line('Find two numbers that multiply to %d and add to %d' % (big_a * big_c, big_b),
                  r'%s = %d, \quad %s = %d' % (pair_tex(m, n, r'\times'), big_a * big_c,
                                               pair_tex(m, n, '+'), big_b)),
             Line('Split the middle term', tex(split)),
             Line('Factorise each pair', pairs),
             Line('Take out the common bracket', answer)]
    forms = [plain(question), plain(split),
             algebra.bracket_plain(Term(p, X), inner) + '+' + algebra.bracket_plain(Term(a), inner),
             '(%s)*(%s)' % (plain([Term(p, X), Term(a)]), plain(inner))]
    return worked(lines, forms)


# --- Facts (editable) ---------------------------------------------------------

GRID = (
    '<svg viewBox="0 0 200 150" width="200" height="150" xmlns="http://www.w3.org/2000/svg" '
    'fill="none" stroke="currentColor" stroke-width="2" font-family="-apple-system, sans-serif">'
    '<path d="M60 50 H190 M60 100 H190 M60 145 H190 M60 50 V145 M125 50 V145 M190 50 V145"/>'
    '<g fill="currentColor" stroke="none" font-size="17" text-anchor="middle">'
    '<text x="92" y="38">x</text><text x="157" y="38">+5</text>'
    '<text x="35" y="81">x</text><text x="35" y="129">+2</text>'
    '<text x="92" y="81">x\u00b2</text><text x="157" y="81">5x</text>'
    '<text x="92" y="129">2x</text><text x="157" y="129">10</text>'
    '</g></svg>')

FACTS = [
    Fact('Expanding', r'Multiply every term inside: $3(x + 4) = 3x + 12$.'),
    Fact('Factorising is the reverse',
         r'Take out the highest common factor: $6x + 9 = 3(2x + 3)$.'),
    Fact('Double brackets',
         r'Each term times each term: $(x + 2)(x + 5) = x^{2} + 5x + 2x + 10 = x^{2} + 7x + 10$.',
         GRID),
    Fact('Squaring a bracket',
         r'$(x + 3)^{2} = (x + 3)(x + 3) = x^{2} + 6x + 9$, not $x^{2} + 9$.'),
    Fact('Factorising quadratics',
         r'Find two numbers that multiply to $c$ and add to $b$: '
         r'$x^{2} + 7x + 12 = (x + 3)(x + 4)$.'),
    Fact('Difference of two squares', r'$A^{2} - B^{2} = (A + B)(A - B)$: $x^{2} - 25 = (x + 5)(x - 5)$.'),
    Fact('When a is not 1',
         r'Multiply $a \times c$, find two numbers that multiply to it and add to $b$, split '
         r'the middle term, then factorise in pairs.'),
    Fact('Check by expanding', r'Multiply your brackets back out: you should get the question.'),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='brackets',
    title='Expanding and factorising',
    area='Algebra',
    keywords=('expand', 'factorise', 'factorize', 'brackets', 'quadratic', 'hcf',
              'difference of two squares', 'double brackets'),
    intro='Expanding multiplies brackets out; factorising puts them back.',
    facts=FACTS,
    stages=[
        Stage('expand_single', 'Expand',
              r'Multiply every term inside the bracket by the term outside: $3(x + 4) = 3x + 12$.',
              expand_single),
        Stage('factorise_single', 'Factorise',
              r'Find the highest common factor of the terms, write it outside, and divide each '
              r'term by it to fill the bracket.',
              factorise_single),
        Stage('expand_simplify', 'Expand and simplify',
              r'Expand each bracket, keeping the sign in front with its number, then collect '
              r'like terms.',
              expand_simplify),
        Stage('double', 'Double brackets',
              r'Multiply each term in the first bracket by each term in the second: four '
              r'products, then collect the $x$ terms.',
              double),
        Stage('factorise_quadratic', 'Factorise quadratics',
              r'For $x^{2} + bx + c$, find two numbers that multiply to $c$ and add to $b$.',
              factorise_quadratic),
        Stage('dots', 'Difference of two squares',
              r'$A^{2} - B^{2} = (A + B)(A - B)$: spot two square terms with a minus between them.',
              dots),
        Stage('factorise_ax2', 'When a is not 1',
              r'For $ax^{2} + bx + c$: multiply $a \times c$, find two numbers that multiply to it '
              r'and add to $b$, split the middle term, then factorise in pairs.',
              factorise_ax2),
    ])
