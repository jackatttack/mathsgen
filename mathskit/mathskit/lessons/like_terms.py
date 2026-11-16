"""Collecting like terms: one letter up to a stretch with several kinds of
term and plenty of minus signs. Each family of like terms gets its own
colour in the working. Problems carry meta['forms'] (question and answer
as Python) for tests/smoke_lessons.py to evaluate.
"""
from .. import algebra
from ..algebra import Term, mono
from ..lesson import Fact, Lesson, Line, Problem, Stage, Worked

LETTERS = 'abmnpqxy'
TRIES = 300


def coefficient(rng, negative):
    size = rng.randint(1, 9)
    return -size if rng.random() < negative else size


def build(rng, families, counts=(1, 2, 2), negative=0.3, allow_cancel=False):
    """Terms for each (monomial, spellings) family, shuffled; None when the
    draw is no good (nothing to collect, or a family cancels out)."""
    terms = []
    for monomial, spellings in families:
        for _ in range(rng.choice(counts)):
            terms.append(Term(coefficient(rng, negative), monomial, rng.choice(spellings)))
    rng.shuffle(terms)
    if negative < 0.4 and terms[0].coefficient < 0:
        terms[0].coefficient = -terms[0].coefficient
    if len(algebra.families(terms)) == len(terms):
        return None
    totals = {}
    for term in terms:
        totals[term.monomial] = totals.get(term.monomial, 0) + term.coefficient
    if not allow_cancel and 0 in totals.values():
        return None
    if not any(totals.values()):
        return None
    return terms


def simplify_problem(terms):
    """The worked lines: colour the families, group them, collect each."""
    colours = algebra.family_colours(terms)
    order = algebra.families(terms)
    grouped = [term for monomial in order for term in terms if term.monomial == monomial]
    result = algebra.collect(terms)
    lines = [Line('Simplify', algebra.tex(terms)),
             Line('Colour the like terms: same letters, same powers',
                  algebra.tex(terms, colours))]
    if [id(term) for term in grouped] != [id(term) for term in terms]:
        lines.append(Line('Move each group together; each sign stays with its term',
                          algebra.tex(grouped, colours)))
    for monomial in order:
        group = [term for term in terms if term.monomial == monomial]
        if len(group) < 2:
            continue
        total = Term(sum(term.coefficient for term in group), monomial)
        say = ('Collect the numbers' if not monomial
               else 'Collect the %s terms' % Term(1, monomial).letters_words())
        lines.append(Line(say, '%s = %s' % (algebra.tex(group, colours),
                                            algebra.tex([total], colours)
                                            if total.coefficient else '0')))
    answer = algebra.tex(result)
    lines.append(Line('Answer', answer))
    return Problem(statement=lines[0].tex, answer=answer, solution=Worked(lines, answer),
                   meta={'forms': [algebra.plain(terms), algebra.plain(result)]})


def stage_maker(choose):
    def make_problem(rng):
        for _ in range(TRIES):
            terms = choose(rng)
            if terms:
                return simplify_problem(terms)
        raise RuntimeError('No good draw: widen the settings.')
    return make_problem


# --- What each stage draws ----------------------------------------------------

def one_letter(rng):
    return build(rng, [(mono(rng.choice(LETTERS)), (None,))], counts=(3, 4), negative=0.25)


def two_letters(rng):
    first, second = rng.sample(LETTERS, 2)
    return build(rng, [(mono(first), (None,)), (mono(second), (None,))])


def with_numbers(rng):
    letters = rng.sample(LETTERS, rng.choice((1, 2)))
    families = [(mono(letter), (None,)) for letter in letters] + [((), (None,))]
    return build(rng, families)


def powers(rng):
    letter = rng.choice('xyab')
    families = [(mono(letter + '^2'), (None,)), (mono(letter), (None,))]
    if rng.random() < 0.5:
        families.append(((), (None,)))
    return build(rng, families)


def products(rng):
    first, second = sorted(rng.sample('abxypq', 2))
    families = [(mono(first + second), (None, second + first))]
    families += [(mono(letter), (None,)) for letter in rng.sample((first, second), rng.choice((1, 2)))]
    return build(rng, families)


def stretch(rng):
    pool = [(mono('x^2'), (None,)), (mono('x'), (None,)), (mono('y'), (None,)),
            (mono('xy'), (None, 'yx')), ((), (None,))]
    return build(rng, rng.sample(pool, rng.choice((3, 4))), negative=0.45, allow_cancel=True)


# --- Facts (editable) ---------------------------------------------------------

FACTS = [
    Fact('Like terms',
         r'Same letters with the same powers: $3x$ and $5x$, $x^{2}$ and $4x^{2}$, '
         r'$ab$ and $ba$.'),
    Fact('Unlike terms',
         r'$x$ and $x^{2}$ are different; so are $x$ and $y$. $3x + 2y$ cannot be '
         r'simplified.'),
    Fact('The sign goes with the term after it',
         r'In $5x - 2y + 3x$ the minus belongs to $2y$: collect to $8x - 2y$.'),
    Fact('ab = ba',
         r'Multiplying works in any order, so $3ab + 2ba = 5ab$.'),
    Fact('A letter on its own',
         r'$x$ means $1x$ and $-x$ means $-1x$: $4x - x = 3x$.'),
    Fact('Collecting to zero',
         r'$3x - 3x = 0$, so the $x$ terms disappear: $3x + 2 - 3x = 2$.'),
]


# --- The ladder (editable) ----------------------------------------------------
LESSON = Lesson(
    key='like_terms',
    title='Collecting like terms',
    area='Algebra',
    keywords=('simplify', 'collect', 'terms', 'expressions'),
    intro='Like terms have the same letters with the same powers. Add their numbers; '
          'leave unlike terms alone.',
    facts=FACTS,
    stages=[
        Stage('one_letter', 'One letter',
              r'Every term is the same letter, so add and subtract the numbers in front: '
              r'$3a + 5a - 2a = 6a$.',
              stage_maker(one_letter)),
        Stage('two_letters', 'Two letters',
              r'Colour each kind of term, then collect each colour on its own: $a$ terms '
              r'with $a$ terms, $b$ terms with $b$ terms.',
              stage_maker(two_letters)),
        Stage('with_numbers', 'With numbers',
              r'Numbers on their own are like terms too. Collect them separately from '
              r'the letters.',
              stage_maker(with_numbers)),
        Stage('powers', 'Powers',
              r'$x^{2}$ and $x$ are unlike terms: they stay apart.',
              stage_maker(powers)),
        Stage('products', 'Products',
              r'$ab$ and $ba$ are the same term, since $a \times b = b \times a$.',
              stage_maker(products)),
        Stage('stretch', 'Stretch',
              r'Several kinds of term and lots of minus signs. Keep each sign with the '
              r'term after it. A group can collect to $0$ and disappear.',
              stage_maker(stretch)),
    ])
