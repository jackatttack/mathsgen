"""Misconception-based options for ax + c = bx + d (bare levels 1-2).

The solution is (d - c) / (a - b). Each distractor follows one wrong step in
that chain. Worded questions and levels 3-4 (built by other modules with
different parameters) do not opt in and retry.

Answers at these levels are whole numbers, so a fractional option would be
an obvious giveaway: when the answer is whole, only whole distractors are
kept. Candidates are in priority order; the engine keeps the first three
distinct ones.
"""
from fractions import Fraction

from .core import Content, rational_tex, rational_text
from .multiple_choice import RationalCandidate


SUPPORTED_LEVELS = {"algebra.linear.two_sided": (1, 2)}


def candidates(question):
    if question.difficulty not in SUPPORTED_LEVELS.get(question.generator_id, ()):
        return None
    p = question.parameters
    if set(p) != {"a", "b", "c", "d"}:
        return None
    a, b, c, d = (Fraction(p[key]) for key in ("a", "b", "c", "d"))
    found = []

    def add(numerator, denominator, mistake, explanation):
        if denominator != 0:
            found.append(RationalCandidate(numerator / denominator, mistake, explanation))

    add(c - d, a - b, "answer_sign_flipped",
        "Subtracts the wrong way round, so the answer has the wrong sign.")
    add(d - c, a + b, "x_term_sign_kept",
        "Moves the x term to the other side without changing its sign.")
    add(d + c, a - b, "constant_sign_kept",
        "Moves the number term to the other side without changing its sign.")
    add(d - c, a, "ignores_right_x",
        "Ignores the x term on the right and divides by the left coefficient only.")
    add(d - c, 1, "forgets_to_divide", "Stops before dividing by the coefficient of x.")
    add(a - b, d - c, "divides_wrong_way",
        "Divides the coefficient of x by the number instead of the number by the coefficient.")
    if ((d - c) / (a - b)).denominator == 1:
        found = [item for item in found if item.value.denominator == 1]
    return found


def format_candidate(question, candidate):
    value = Fraction(candidate.value)
    return Content("x = " + rational_text(value), "x = " + rational_tex(value))