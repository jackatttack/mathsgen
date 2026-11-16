"""Linear equations, solved the way they are taught.

    from mathskit import linear

    solution = linear.solve('3(x + 2) = 2x - 5')
    for step in solution.steps:
        print(step.say, '|', step.tex)
    print(solution.verdict)          # x = -11

solve() reads the equation and makes one Step per move, in the order a
teacher would: clear the fractions (cross multiply when it is one fraction
each side), expand the brackets, collect like terms, get the x terms on
the left, get the numbers on the right, then divide. Each Step holds the
whole equation after its move as LaTeX, and the terms that move changed
are wrapped in \\htmlClass{mk-hot}{...} so a page can light them up.

What it reads: one letter as the unknown, whole and decimal numbers,
+ - * / (and the symbols x-times, divide and minus), brackets (nested
too), implicit multiplication (3x, 2(x + 1)), and fractions over a number
((x + 1)/3, x/2, 3x/4). Anything else, or anything not linear, raises
NotLinear with a plain reason.

Pure Python (fractions only: no sympy, no ui), so it runs in Pythonista,
PythonIDE and Juno. tests/smoke_linear.py checks every answer against
sympy, and that no step changes the solution.
"""
import copy
import math
import re
from fractions import Fraction

# --- Settings (editable) ------------------------------------------------------

HOT_CLASS = 'mk-hot'     # terms the latest move changed (blocks.CSS colours them)
MAX_MOVES = 20           # a safety stop; a GCSE linear equation needs about six

# Short names for each kind of move ({x} is the unknown's letter). The
# student mode will offer these as the choices.
MOVE_NAMES = {
    'start': 'Start',
    'cross': 'Cross multiply',
    'clear': 'Clear the fractions',
    'expand': 'Expand the brackets',
    'collect': 'Collect like terms',
    'swap': 'Swap the sides',
    'unknowns': 'Get the {x} terms together',
    'numbers': 'Get the numbers together',
    'divide': 'Divide',
}

# Other ways of writing the four operations, read as the plain ones.
SYMBOLS = {'\u00d7': '*', '\u00b7': '*', '\u00f7': '/', '\u2212': '-', '\u2013': '-'}


class NotLinear(ValueError):
    """The text is not a linear equation solve() can read."""


# --- Terms --------------------------------------------------------------------

class Term:
    """One term of a side of an equation.

    Every kind answers the same questions: form() is its value as (a, b),
    meaning a*x + b; times(m) is a new term m times as big; negative() says
    whether it is written with a minus; tex_body(var) is its LaTeX without
    that minus. hot marks a term the latest move changed."""
    hot = False

    def negated(self):
        return self.times(-1)

    def lit(self):
        """A copy marked as changed by this move."""
        term = copy.copy(self)
        term.hot = True
        return term

    def cooled(self):
        if not self.hot:
            return self
        term = copy.copy(self)
        term.hot = False
        return term


class Number(Term):
    def __init__(self, value):
        self.value = Fraction(value)

    def form(self):
        return Fraction(0), self.value

    def negative(self):
        return self.value < 0

    def times(self, m):
        return Number(self.value * m)

    def tex_body(self, var):
        return number_tex(abs(self.value))


class Unknown(Term):
    """coefficient times the unknown: 3x, -x, 1/2 x."""

    def __init__(self, coefficient=1):
        self.coefficient = Fraction(coefficient)

    def form(self):
        return self.coefficient, Fraction(0)

    def negative(self):
        return self.coefficient < 0

    def times(self, m):
        return Unknown(self.coefficient * m)

    def tex_body(self, var):
        size = abs(self.coefficient)
        return var if size == 1 else number_tex(size) + var


class Bracket(Term):
    """factor times (terms): 3(x + 2), -(x - 4)."""

    def __init__(self, factor, terms):
        self.factor = Fraction(factor)
        self.terms = list(terms)

    def form(self):
        a, b = side_form(self.terms)
        return self.factor * a, self.factor * b

    def negative(self):
        return self.factor < 0

    def times(self, m):
        return Bracket(self.factor * m, self.terms)

    def expanded(self):
        """The terms with the factor multiplied in."""
        return [simplest(term.times(self.factor)) for term in self.terms]

    def tex_body(self, var):
        size = abs(self.factor)
        lead = '' if size == 1 else number_tex(size)
        return lead + r'\left(' + side_tex(self.terms, var) + r'\right)'


class Over(Term):
    """factor times (terms), over a whole number: (x + 1)/3, x/2, 3x/4."""

    def __init__(self, factor, terms, denominator):
        self.factor = Fraction(factor)
        self.terms = list(terms)
        self.denominator = int(denominator)

    def form(self):
        a, b = side_form(self.terms)
        scale = self.factor / self.denominator
        return a * scale, b * scale

    def negative(self):
        return self.factor < 0

    def negated(self):
        return Over(-self.factor, self.terms, self.denominator)

    def times(self, m):
        value = self.factor * m / self.denominator
        if value.denominator == 1:
            return simplest(Bracket(value, self.terms))     # the fraction bar is gone
        return Over(value.numerator, self.terms, value.denominator)

    def tex_body(self, var):
        size = abs(self.factor)
        if size == 1:
            lead, top = '', self.terms
        elif len(self.terms) == 1:
            lead, top = '', [simplest(self.terms[0].times(size))]   # 3x/4, not 3 x/4
        else:
            lead, top = number_tex(size), self.terms
        return lead + r'\frac{' + side_tex(top, var) + '}{' + str(self.denominator) + '}'


def simplest(term):
    """A bracket around one term is just that term, times the factor."""
    if isinstance(term, Bracket):
        if term.factor == 0:
            return Number(0)
        if len(term.terms) == 1:
            return simplest(term.terms[0].times(term.factor))
    return term


# --- Writing it down ----------------------------------------------------------

def number_tex(value):
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return r'\frac{%d}{%d}' % (value.numerator, value.denominator)


def number_text(value):
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return '%d/%d' % (value.numerator, value.denominator)


def unknown_text(coefficient, var):
    return var if coefficient == 1 else number_text(coefficient) + var


def hot_tex(piece):
    return r'\htmlClass{%s}{%s}' % (HOT_CLASS, piece)


def side_tex(terms, var):
    if not terms:
        return '0'
    out = []
    for index, term in enumerate(terms):
        body = term.tex_body(var)
        if index == 0:
            piece = ('-' if term.negative() else '') + body
            out.append(hot_tex(piece) if term.hot else piece)
        else:
            out.append(' - ' if term.negative() else ' + ')
            out.append(hot_tex(body) if term.hot else body)
    return ''.join(out)


def side_form(terms):
    a, b = Fraction(0), Fraction(0)
    for term in terms:
        term_a, term_b = term.form()
        a += term_a
        b += term_b
    return a, b


# --- Equations, steps and solutions -------------------------------------------

class Equation:
    def __init__(self, left, right, var):
        self.left = list(left)
        self.right = list(right)
        self.var = var

    def tex(self):
        return side_tex(self.left, self.var) + ' = ' + side_tex(self.right, self.var)

    def form(self):
        """left - right as (a, b): the equation says a*x + b = 0."""
        left_a, left_b = side_form(self.left)
        right_a, right_b = side_form(self.right)
        return left_a - right_a, left_b - right_b

    def cooled(self):
        return Equation([term.cooled() for term in self.left],
                        [term.cooled() for term in self.right], self.var)


class Step:
    """One line of working: the move made (kind, name, say) and the
    equation after it (equation, tex)."""

    def __init__(self, kind, say, equation):
        self.kind = kind
        self.name = MOVE_NAMES[kind].format(x=equation.var)
        self.say = say
        self.equation = equation
        self.tex = equation.tex()


class Solution:
    """Every step, and what they come to. kind is 'one' (answer is a
    Fraction), 'all' (true for every value) or 'none' (no solution)."""

    def __init__(self, text, var, steps):
        self.text = text
        self.var = var
        self.steps = steps
        a, b = steps[-1].equation.form()
        if a != 0:
            self.kind, self.answer = 'one', -b / a
            self.verdict = '%s = %s' % (var, number_text(self.answer))
        elif b == 0:
            self.kind, self.answer = 'all', None
            self.verdict = 'True for every value of %s: both sides are the same.' % var
        else:
            self.kind, self.answer = 'none', None
            self.verdict = 'No solution: the %s terms cancel and what is left is false.' % var


def solve(text):
    """Read text as a linear equation and solve it, one move per Step."""
    equation = read(text)
    steps = [Step('start', 'Solve for %s' % equation.var, equation)]
    for _ in range(MAX_MOVES):
        if is_solved(equation):
            break
        step = next_move(equation.cooled())
        if step is None:
            break
        steps.append(step)
        equation = step.equation
    return Solution(text, equation.var, steps)


def is_solved(equation):
    left, right = equation.left, equation.right
    return (len(left) == 1 and isinstance(left[0], Unknown) and left[0].coefficient == 1
            and len(right) <= 1 and all(isinstance(term, Number) for term in right))


def next_move(equation):
    """The first move in teaching order that applies, as a Step, or None."""
    for move in MOVES:
        step = move(equation)
        if step is not None:
            return step
    return None


# --- The moves, in teaching order ---------------------------------------------

def clear_fractions(equation):
    bars = [term for term in equation.left + equation.right if isinstance(term, Over)]
    if not bars:
        return None
    one_each_side = (len(equation.left) == 1 and len(equation.right) == 1 and len(bars) == 2
                     and bars[0].denominator != bars[1].denominator)
    if one_each_side:
        multiplier = bars[0].denominator * bars[1].denominator
        kind, say = 'cross', 'Cross multiply'
    else:
        multiplier = lowest_common_multiple(bar.denominator for bar in bars)
        kind, say = 'clear', 'Multiply every term by %d' % multiplier

    def multiplied(side):
        return [simplest(term.times(multiplier)).lit() for term in side]

    return Step(kind, say, Equation(multiplied(equation.left), multiplied(equation.right),
                                    equation.var))


def expand_brackets(equation):
    brackets = [term for term in equation.left + equation.right if isinstance(term, Bracket)]
    if not brackets:
        return None

    def opened(side):
        out = []
        for term in side:
            if isinstance(term, Bracket):
                out.extend(part.lit() for part in term.expanded())
            else:
                out.append(term)
        return out

    if all(bracket.factor == 1 for bracket in brackets):
        say = 'Remove the brackets'
    else:
        say = 'Expand the bracket' if len(brackets) == 1 else 'Expand the brackets'
    return Step('expand', say, Equation(opened(equation.left), opened(equation.right),
                                        equation.var))


def collect_side(side):
    """The side with like terms added up, or None if there is nothing to collect."""
    if not all(isinstance(term, (Number, Unknown)) for term in side):
        return None
    unknowns = [term for term in side if isinstance(term, Unknown)]
    numbers = [term for term in side if isinstance(term, Number)]
    zeros = [term for term in side if term.form() == (0, 0)]
    if len(unknowns) <= 1 and len(numbers) <= 1 and not (zeros and len(side) > 1):
        return None
    a, b = side_form(side)
    out = []
    if a != 0:
        out.append(Unknown(a).lit())
    if b != 0 or not out:
        out.append(Number(b).lit())
    return out


def collect_like_terms(equation):
    left = collect_side(equation.left)
    right = collect_side(equation.right)
    if left is None and right is None:
        return None
    return Step('collect', 'Collect like terms',
                Equation(left or equation.left, right or equation.right, equation.var))


def has_unknown(side):
    return any(isinstance(term, Unknown) and term.coefficient != 0 for term in side)


def swap_sides(equation):
    if has_unknown(equation.left) or not has_unknown(equation.right):
        return None
    return Step('swap', 'Swap the sides, so %s is on the left' % equation.var,
                Equation(equation.right, equation.left, equation.var))


def move_unknowns(equation):
    moving = [term for term in equation.right if isinstance(term, Unknown)]
    if not moving:
        return None
    var = equation.var
    c = sum((term.coefficient for term in moving), Fraction(0))
    a = sum((term.coefficient for term in equation.left if isinstance(term, Unknown)),
            Fraction(0)) - c
    left = [Unknown(a).lit()] if a != 0 else []
    left += [term for term in equation.left if not isinstance(term, Unknown)]
    right = [term for term in equation.right if not isinstance(term, Unknown)] or [Number(0)]
    if c > 0:
        say = 'Subtract %s from both sides' % unknown_text(c, var)
    else:
        say = 'Add %s to both sides' % unknown_text(-c, var)
    return Step('unknowns', say, Equation(left, right, var))


def move_numbers(equation):
    numbers = [term for term in equation.left if isinstance(term, Number)]
    if not numbers or not has_unknown(equation.left):
        return None
    if not all(isinstance(term, Number) for term in equation.right):
        return None
    n = sum((term.value for term in numbers), Fraction(0))
    if n == 0:
        return None
    left = [term for term in equation.left if not isinstance(term, Number)]
    right = [Number(side_form(equation.right)[1] - n).lit()]
    if n > 0:
        say = 'Subtract %s from both sides' % number_text(n)
    else:
        say = 'Add %s to both sides' % number_text(-n)
    return Step('numbers', say, Equation(left, right, equation.var))


def divide(equation):
    if len(equation.left) != 1 or not isinstance(equation.left[0], Unknown):
        return None
    if not all(isinstance(term, Number) for term in equation.right):
        return None
    a = equation.left[0].coefficient
    if a in (0, 1):
        return None
    if a == -1:
        say = 'Multiply both sides by -1'
    elif a.denominator != 1 and a.numerator == 1:
        say = 'Multiply both sides by %d' % a.denominator
    else:
        say = 'Divide both sides by %s' % number_text(a)
    answer = side_form(equation.right)[1] / a
    return Step('divide', say, Equation([Unknown(1)], [Number(answer).lit()], equation.var))


MOVES = (clear_fractions, expand_brackets, collect_like_terms, swap_sides,
         move_unknowns, move_numbers, divide)


def lowest_common_multiple(numbers):
    result = 1
    for number in numbers:
        result = result * number // math.gcd(result, number)
    return result


# --- Reading the text ---------------------------------------------------------

TOKEN = re.compile(r'\s*(?:(\d+(?:\.\d+)?|\.\d+)|([A-Za-z])|(\S))')


def read(text):
    """The Equation text describes. Raises NotLinear with a reason."""
    text = str(text)
    for symbol, plain in SYMBOLS.items():
        text = text.replace(symbol, plain)
    if text.count('=') != 1:
        raise NotLinear('An equation needs exactly one "=".')
    left_text, right_text = text.split('=')
    reader = Reader()
    left = reader.side(left_text)
    right = reader.side(right_text)
    return Equation(left, right, reader.var or 'x')


class Reader:
    """Reads one side at a time; remembers the unknown's letter across both."""

    def __init__(self):
        self.var = None
        self.tokens = []
        self.at = 0

    def side(self, text):
        self.tokens = tokenise(text)
        self.at = 0
        if not self.tokens:
            raise NotLinear('Both sides need something on them.')
        terms = self.expression()
        if self.at < len(self.tokens):
            raise NotLinear('Unexpected %r.' % (self.tokens[self.at][1],))
        return terms

    def peek(self):
        return self.tokens[self.at] if self.at < len(self.tokens) else (None, None)

    def take(self):
        token = self.peek()
        self.at += 1
        return token

    def expression(self):
        terms = []
        sign = 1
        kind, value = self.peek()
        if kind == 'op' and value in '+-':
            self.take()
            sign = -1 if value == '-' else 1
        while True:
            term = self.term()
            terms.append(term.negated() if sign < 0 else term)
            kind, value = self.peek()
            if kind == 'op' and value in '+-':
                self.take()
                sign = -1 if value == '-' else 1
            else:
                return terms

    def term(self):
        product = Product()
        product.use(*self.factor())
        while True:
            token = self.peek()
            if token == ('op', '*'):
                self.take()
                product.use(*self.factor())
            elif token == ('op', '/'):
                self.take()
                product.divide(*self.factor())
            elif token[0] in ('number', 'letter') or token == ('op', '('):
                product.use(*self.factor())        # implicit: 3x, 2(x + 1)
            else:
                return product.result()

    def factor(self):
        kind, value = self.take()
        if kind == 'number':
            return 'number', value
        if kind == 'letter':
            if self.var is None:
                self.var = value
            elif value != self.var:
                raise NotLinear('One unknown only: found %s and %s.' % (self.var, value))
            return 'unknown', None
        if (kind, value) == ('op', '('):
            terms = self.expression()
            if self.take() != ('op', ')'):
                raise NotLinear('A bracket is not closed.')
            return 'group', terms
        if (kind, value) == ('op', '-'):
            inner_kind, inner = self.factor()
            if inner_kind == 'number':
                return 'number', -inner
            if inner_kind == 'unknown':
                return 'group', [Unknown(-1)]
            return 'group', [term.negated() for term in inner]
        if kind is None:
            raise NotLinear('The equation ends too soon.')
        raise NotLinear('Unexpected %r.' % (value,))


class Product:
    """The factors of one term, multiplied as they are read. At most one
    factor may hold the unknown (piece); a fraction bar over the unknown
    is kept (denominator) so x/2 is written as it was typed."""

    def __init__(self):
        self.coefficient = Fraction(1)
        self.piece = None              # None, 'unknown' or a bracket's terms
        self.denominator = 1

    def use(self, kind, value):
        if kind == 'number':
            self.coefficient *= value
            return
        if kind == 'group':
            a, b = side_form(value)
            if a == 0:                 # a bracket of numbers is a number
                self.coefficient *= b
                return
        if self.piece is not None:
            raise NotLinear('That multiplies the unknown by itself, so it is not linear.')
        self.piece = 'unknown' if kind == 'unknown' else value

    def divide(self, kind, value):
        if kind == 'number':
            divisor = value
        elif kind == 'group' and side_form(value)[0] == 0:
            divisor = side_form(value)[1]
        else:
            raise NotLinear('Divide by numbers only: dividing by the unknown is not linear.')
        if divisor == 0:
            raise NotLinear('That divides by zero.')
        if self.piece is None:
            self.coefficient /= divisor
            return
        if divisor < 0:
            self.coefficient = -self.coefficient
            divisor = -divisor
        self.coefficient *= divisor.denominator
        self.denominator *= divisor.numerator

    def result(self):
        if self.piece is None:
            return Number(self.coefficient)
        inner = [Unknown(1)] if self.piece == 'unknown' else self.piece
        if self.denominator != 1:
            return Over(self.coefficient, inner, self.denominator)
        if self.piece == 'unknown':
            return Unknown(self.coefficient)
        return simplest(Bracket(self.coefficient, inner))


def tokenise(text):
    tokens = []
    for number, letter, other in TOKEN.findall(text):
        if number:
            tokens.append(('number', Fraction(number)))
        elif letter:
            tokens.append(('letter', letter))
        elif other in '+-*/()':
            tokens.append(('op', other))
        else:
            raise NotLinear('Unexpected %r.' % other)
    return tokens
