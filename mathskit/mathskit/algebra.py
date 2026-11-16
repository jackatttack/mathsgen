"""Algebra for lessons: terms, expressions, their TeX, and plain Python
forms for tests to evaluate. Pure Python.

A Term is a whole-number coefficient times a monomial. A monomial is a
tuple of (letter, power) pairs in alphabetical order; () is a number.

    from mathskit.algebra import Term, mono
    terms = [Term(3, mono('x')), Term(-1, mono('ab'), shown='ba'), Term(5)]
    tex(terms)          # '3x - ba + 5'
    collect(terms)      # like terms added up, in the usual order
    plain(terms)        # '(3)*x+(-1)*a*b+(5)'
"""

# Colours for families of like terms (KaTeX \textcolor). Bright enough for
# dark themes, deep enough for light ones.
FAMILY_COLOURS = ('#f0883e', '#58a6ff', '#3fb950', '#d2a8ff', '#e3b341')
SUPERSCRIPTS = {2: '\u00b2', 3: '\u00b3'}


def mono(spec=''):
    """'x', 'x^2', 'ab', 'x^2y' -> ((letter, power), ...) in letter order."""
    powers = {}
    index = 0
    while index < len(spec):
        letter = spec[index]
        index += 1
        power = 1
        if index < len(spec) and spec[index] == '^':
            index += 1
            start = index
            while index < len(spec) and spec[index].isdigit():
                index += 1
            power = int(spec[start:index])
        powers[letter] = powers.get(letter, 0) + power
    return tuple(sorted(powers.items()))


class Term:
    """coefficient times monomial. shown spells the letters as a question
    wrote them ('ba' for ab); collecting always writes them in order."""

    def __init__(self, coefficient, monomial=(), shown=None):
        self.coefficient = coefficient
        self.monomial = tuple(monomial)
        self.shown = shown

    def letters_tex(self):
        if self.shown:
            return self.shown
        return ''.join(letter if power == 1 else '%s^{%d}' % (letter, power)
                       for letter, power in self.monomial)

    def letters_words(self):
        """The letters for a line of words: x², ab."""
        return ''.join(letter if power == 1 else letter + SUPERSCRIPTS.get(power, '^%d' % power)
                       for letter, power in self.monomial)


# --- TeX ----------------------------------------------------------------------

def body_tex(term):
    """The term without its sign: 3x, x, ab, 7."""
    size = abs(term.coefficient)
    letters = term.letters_tex()
    if not letters:
        return str(size)
    return letters if size == 1 else '%d%s' % (size, letters)


def signed_tex(term):
    return ('-' if term.coefficient < 0 else '') + body_tex(term)


def factor_tex(term):
    """A term to multiply by: negatives in brackets, (-3)."""
    return '(%s)' % signed_tex(term) if term.coefficient < 0 else signed_tex(term)


def number_tex(value):
    return '(%d)' % value if value < 0 else str(value)


def tex(terms, colours=None):
    """An expression; colours maps a monomial to a colour for its family."""
    out = []
    for term in terms:
        if term.coefficient == 0:
            continue
        index = len(out)
        body = body_tex(term)
        colour = colours.get(term.monomial) if colours else None
        if colour:
            body = r'\textcolor{%s}{%s}' % (colour, body)
        negative = term.coefficient < 0
        if index == 0:
            out.append('-' + body if negative else body)
        else:
            out.append(' %s %s' % ('-' if negative else '+', body))
    return ''.join(out) if out else '0'


def bracket_tex(outside, inside):
    """outside(inside): 3(x + 4), -2(x - 5), x(x + 3), (x + 1) for 1."""
    if outside.monomial:
        lead = signed_tex(outside)
    elif outside.coefficient == 1:
        lead = ''
    elif outside.coefficient == -1:
        lead = '-'
    else:
        lead = str(outside.coefficient)
    return '%s(%s)' % (lead, tex(inside))


def family_colours(terms):
    return {monomial: FAMILY_COLOURS[index % len(FAMILY_COLOURS)]
            for index, monomial in enumerate(families(terms))}


# --- Plain Python (for tests) -------------------------------------------------

def term_plain(term):
    parts = ['(%d)' % term.coefficient]
    for letter, power in term.monomial:
        parts.append(letter if power == 1 else '%s**%d' % (letter, power))
    return '*'.join(parts)


def plain(terms):
    return '+'.join(term_plain(term) for term in terms) or '0'


def bracket_plain(outside, inside):
    return '%s*(%s)' % (term_plain(outside), plain(inside))


# --- Working ------------------------------------------------------------------

def families(terms):
    """Monomials in the order they first appear."""
    seen = []
    for term in terms:
        if term.monomial not in seen:
            seen.append(term.monomial)
    return seen


def order_key(term):
    """Highest power first, letters in order, the number last."""
    degree = sum(power for _, power in term.monomial)
    if not degree:
        return (1,)
    highest = max(power for _, power in term.monomial)
    return (0, -degree, -highest, term.monomial)


def collect(terms):
    """Like terms added up, zeros dropped, in the usual order."""
    totals = {}
    for term in terms:
        totals[term.monomial] = totals.get(term.monomial, 0) + term.coefficient
    return sorted((Term(total, monomial) for monomial, total in totals.items() if total),
                  key=order_key)


def multiply(first, second):
    powers = dict(first.monomial)
    for letter, power in second.monomial:
        powers[letter] = powers.get(letter, 0) + power
    return Term(first.coefficient * second.coefficient, tuple(sorted(powers.items())))


def expand(outside, inside):
    return [multiply(outside, term) for term in inside]
