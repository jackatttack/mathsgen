"""Misconception-based options for Pythagoras lengths (levels 1-3).

Every triangle comes from a scaled Pythagorean triple, so every answer is
exact. A distractor that needs a square root is shown only when that root is
exact too; an irrational value would need rounding the question never asks
for. Level 4 (two linked triangles) stays a written question.

Options are written as lengths, such as 13 cm.
"""
from fractions import Fraction
import math

from .core import Content
from .multiple_choice import RationalCandidate
from .rounding import decimal_text


SUPPORTED_LEVELS = {"geometry.pythagoras.lengths": (1, 2, 3)}


def candidate(value, mistake, explanation):
    return RationalCandidate(Fraction(value), mistake, explanation)


def exact_root(value):
    """The exact square root of a positive rational, or None."""
    value = Fraction(value)
    if value <= 0:
        return None
    top, bottom = math.isqrt(value.numerator), math.isqrt(value.denominator)
    if top * top == value.numerator and bottom * bottom == value.denominator:
        return Fraction(top, bottom)
    return None


def candidates(question):
    if question.difficulty not in SUPPORTED_LEVELS.get(question.generator_id, ()):
        return None
    p = question.parameters
    if "sides" not in p:
        return None
    a, b, c = (Fraction(side) for side in p["sides"])
    found = []
    if p["missing"] == 2:
        found.append(candidate(a * a + b * b, "forgets_square_root",
                               "Adds the squares but forgets to take the square root."))
        found.append(candidate(a + b, "adds_sides",
                               "Adds the two shorter sides instead of using their squares."))
        found.append(candidate(2 * a + 2 * b, "doubles_instead_of_squaring",
                               "Doubles each side instead of squaring it, then adds."))
        root = exact_root(abs(a * a - b * b))
        if root is not None:
            found.append(candidate(root, "subtracts_squares",
                                   "Subtracts the squares instead of adding them."))
        return found
    known = b if p["missing"] == 0 else a
    found.append(candidate(c * c - known * known, "forgets_square_root",
                           "Subtracts the squares but forgets to take the square root."))
    found.append(candidate(c - known, "subtracts_lengths",
                           "Subtracts the lengths instead of their squares."))
    root = exact_root(c * c + known * known)
    if root is not None:
        found.append(candidate(root, "adds_squares",
                               "Adds the squares as if finding the hypotenuse."))
    found.append(candidate(c + known, "adds_lengths",
                           "Adds the two given lengths."))
    return found


def format_candidate(question, candidate):
    return Content(decimal_text(Fraction(candidate.value)) + " cm")