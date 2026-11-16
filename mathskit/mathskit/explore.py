"""Explore: solve an equation your own way.

    from mathskit import explore

    game = explore.Explorer('3(x + 2) = 2x - 5')
    print([step.say for step in game.options])   # every move on offer
    game.play('Expand the bracket')
    game.hint()        # the move a textbook would make from here
    game.verdict()     # None until x is on its own, then (kind, words, value)

Every move on offer is a real, correct thing to do to the equation in
front of you, built from its own terms: add or subtract any term on it,
divide by any x coefficient on it, multiply by any denominator on it,
expand, collect like terms, swap the sides. Not only the textbook's next
move: a student can wander, undo, and find their own way to x = n.
Moves are linear.Step objects, so each carries its equation and its hot
terms like the worked solutions do. Pure Python.
"""
from fractions import Fraction

from . import linear
from .linear import (Equation, Number, Over, Step, Unknown, number_text, side_form,
                     simplest, unknown_text)


class Explorer:
    """One equation being solved: the moves made so far and those on offer."""

    def __init__(self, text):
        self.text = text
        self.model = linear.solve(text)          # the worked solution, for hints and counts
        self.history = [self.model.steps[0]]
        self.options = []
        self.refresh()

    @property
    def equation(self):
        return self.history[-1].equation

    @property
    def moves_made(self):
        return len(self.history) - 1

    @property
    def worked_moves(self):
        return len(self.model.steps) - 1

    def refresh(self):
        self.options = [] if self.verdict() else available(self.equation.cooled())

    def play(self, say):
        """Make the move on offer called say. False if it is not on offer
        (a stale tap)."""
        for step in self.options:
            if step.say == say:
                self.history.append(step)
                self.refresh()
                return True
        return False

    def undo(self):
        if len(self.history) > 1:
            self.history.pop()
            self.refresh()

    def restart(self):
        self.history = self.history[:1]
        self.refresh()

    def hint(self):
        """The say of the move linear.solve would make from here, if it is on offer."""
        if not self.options:
            return None
        step = linear.next_move(self.equation.cooled())
        labels = [option.say for option in self.options]
        return step.say if step is not None and step.say in labels else None

    def verdict(self):
        return verdict(self.equation)


def verdict(equation):
    """(kind, words, value) once it is finished, else None. x = n and
    n = x both count; so does x vanishing from a flat equation."""
    var = equation.var
    for candidate in (equation, Equation(equation.right, equation.left, var)):
        if linear.is_solved(candidate):
            value = side_form(candidate.right)[1]
            return 'one', '%s = %s' % (var, number_text(value)), value
    flat = all(isinstance(term, (Number, Unknown)) for term in equation.left + equation.right)
    if flat and side_form(equation.left)[0] == 0 and side_form(equation.right)[0] == 0:
        if equation.form()[1] == 0:
            return 'all', 'True for every value of %s.' % var, None
        return 'none', 'No solution: what is left is false.', None
    return None


# --- Button labels -------------------------------------------------------------

SHORT_WORDS = {'Expand the bracket': 'Expand', 'Expand the brackets': 'Expand',
               'Remove the brackets': 'Remove ( )', 'Collect like terms': 'Collect',
               'Cross multiply': 'Cross \u00d7'}
SHORT_FORMS = [('Subtract ', ' from both sides', '\u2212'), ('Add ', ' to both sides', '+'),
               ('Divide both sides by ', '', '\u00f7'), ('Multiply both sides by ', '', '\u00d7'),
               ('Multiply every term by ', '', '\u00d7')]


def short_label(say):
    """A move as a button: +3x, \u22126, \u00d72, \u00f73, Expand. The working keeps the full words."""
    if say in SHORT_WORDS:
        return SHORT_WORDS[say]
    if say.startswith('Swap the sides'):
        return 'Swap sides'
    for start, end, sign in SHORT_FORMS:
        if say.startswith(start) and say.endswith(end):
            amount = say[len(start):len(say) - len(end)]
            if amount.startswith('-'):
                amount = '(\u2212%s)' % amount[1:]
            return sign + amount
    return say


# --- The moves on offer ---------------------------------------------------------

def available(equation):
    """Every sensible move from here, as Steps, in a steady order: tidying
    moves first, then moving terms, then dividing or multiplying."""
    found = []

    def offer(step):
        if step is None:
            return
        if short_label(step.say) in [short_label(known.say) for known in found]:
            return                       # two moves that would show the same button
        found.append(step)

    terms = equation.left + equation.right
    offer(linear.clear_fractions(equation))
    for denominator in sorted(set(term.denominator for term in terms if isinstance(term, Over))):
        offer(scale(equation, denominator, 'Multiply every term by %d' % denominator, 'clear'))
    offer(linear.expand_brackets(equation))
    offer(linear.collect_like_terms(equation))
    offer(linear.swap_sides(equation))
    for term in terms:
        if isinstance(term, Unknown) and term.coefficient != 0:
            offer(shift(equation, term))
    for term in terms:
        if isinstance(term, Number) and term.value != 0:
            offer(shift(equation, term))
    for term in terms:
        if isinstance(term, Unknown):
            for step in dividers(equation, term.coefficient):
                offer(step)
    return found


def shift(equation, term):
    """Take term away from both sides (add it, if it is negative)."""
    var = equation.var
    if isinstance(term, Unknown):
        size, kind, words = term.coefficient, 'unknowns', unknown_text(abs(term.coefficient), var)
    else:
        size, kind, words = term.value, 'numbers', number_text(abs(term.value))
    say = ('Subtract %s from both sides' if size > 0 else 'Add %s to both sides') % words
    removing = term.times(-1)
    return Step(kind, say, Equation(merged(equation.left, removing),
                                    merged(equation.right, removing), var))


def merged(side, extra):
    """side with extra added: it joins a like term if there is one (and
    vanishes with it if they cancel), or goes on the end."""
    out = list(side)
    for index, term in enumerate(out):
        if isinstance(term, Number) and isinstance(extra, Number):
            combined = Number(term.value + extra.value)
        elif isinstance(term, Unknown) and isinstance(extra, Unknown):
            combined = Unknown(term.coefficient + extra.coefficient)
        else:
            continue
        if combined.form() == (0, 0):
            del out[index]
        else:
            out[index] = combined.lit()
        return out or [Number(0)]
    out.append(extra.lit())
    return out


def dividers(equation, coefficient):
    """The ways to make an x coefficient 1: divide by it, multiply by its
    denominator, or multiply by -1."""
    c = Fraction(coefficient)
    if c in (0, 1):
        return []
    if c == -1:
        return [scale(equation, -1, 'Multiply both sides by -1', 'divide')]
    steps = []
    if c.denominator != 1:
        steps.append(scale(equation, c.denominator,
                           'Multiply both sides by %d' % c.denominator, 'divide'))
    if c.numerator != 1:
        steps.append(scale(equation, 1 / c, 'Divide both sides by %s' % number_text(c), 'divide'))
    return steps


def scale(equation, multiplier, say, kind):
    """Every term of both sides times multiplier."""
    m = Fraction(multiplier)

    def scaled(side):
        return [simplest(term.times(m)).lit() for term in side]

    return Step(kind, say, Equation(scaled(equation.left), scaled(equation.right), equation.var))
