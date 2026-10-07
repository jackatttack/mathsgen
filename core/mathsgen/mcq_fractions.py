"""Authored mistakes for bare fraction arithmetic.

Worded forms deliberately opt out until their own reasoning rules are added.
Candidates are prioritised by relevance; accidental correct answers and
equivalent distractors are removed by the shared engine.
"""
from fractions import Fraction
from math import gcd

from .multiple_choice import RationalCandidate


SUPPORTED_LEVELS = {
    "number.fractions.addition": (1, 2, 3, 4),
    "number.fractions.multiplication": (1, 2, 3, 4),
    "number.fractions.division": (1, 2, 3, 4),
}


def fraction_candidate(numerator, denominator, mistake, explanation, raw=False):
    return RationalCandidate(
        Fraction(numerator, denominator), mistake, explanation,
        (numerator, denominator) if raw else (),
    )


def candidates(question):
    """Only accept the inspected bare form, whose operands are explicit."""
    if question.generator_id not in SUPPORTED_LEVELS:
        return None
    if set(question.parameters) != {"left", "right"}:
        return None
    left = Fraction(question.parameters["left"])
    right = Fraction(question.parameters["right"])
    a, b = left.numerator, left.denominator
    c, d = right.numerator, right.denominator
    operation = question.generator_id.rsplit(".", 1)[-1]
    if operation == "addition":
        common = b * d // gcd(b, d)
        result = [
            fraction_candidate(
                a + c, b + d, "add_tops_and_bottoms",
                "Adds the numerators and also adds the denominators.", raw=True),
            fraction_candidate(
                a + c, common, "change_denominators_only",
                "Finds a common denominator but does not scale the numerators."),
            fraction_candidate(
                a + c, b * d, "multiply_bottoms_only",
                "Multiplies the denominators but only adds the original numerators."),
            RationalCandidate(
                left * right, "multiply_instead",
                "Multiplies the fractions instead of adding them."),
        ]
        if left < 0 or right < 0:
            result.insert(1, RationalCandidate(
                abs(left) + abs(right), "ignore_negative_sign",
                "Adds the magnitudes and ignores the negative sign."))
        return result
    if operation == "multiplication":
        result = [
            RationalCandidate(
                left / right, "invert_second_unnecessarily",
                "Uses the reciprocal rule for division when multiplying."),
            fraction_candidate(
                a * c, b + d, "add_denominators",
                "Multiplies the numerators but adds the denominators."),
            RationalCandidate(
                left + right, "add_instead",
                "Adds the fractions instead of multiplying them."),
        ]
        if b == d:
            result.insert(0, fraction_candidate(
                a * c, b, "keep_common_denominator",
                "Multiplies the numerators but keeps the common denominator."))
        if left < 0 or right < 0:
            result.insert(0, RationalCandidate(
                abs(left * right), "lose_negative_sign",
                "Treats a positive times a negative as positive."))
        return result
    result = [
        RationalCandidate(
            left * right, "do_not_invert",
            "Multiplies straight across without taking the reciprocal."),
        RationalCandidate(
            right / left, "invert_first",
            "Inverts the first fraction instead of the second."),
        RationalCandidate(
            1 / (left * right), "invert_both",
            "Inverts both fractions before multiplying."),
    ]
    if left < 0 or right < 0:
        result.insert(0, RationalCandidate(
            abs(left / right), "lose_negative_sign",
            "Treats division with one negative operand as positive."))
    return result