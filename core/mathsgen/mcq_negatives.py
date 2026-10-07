"""Sign misconceptions for introductory directed-number calculations.

Only inspected bare templates at levels 1-2 opt in. Every candidate follows
a stated wrong operation on the displayed numbers, rather than an arbitrary
offset from the correct answer.
"""
from fractions import Fraction

from .multiple_choice import RationalCandidate


SUPPORTED_LEVELS = {"number.integers.negatives": (1, 2)}


def candidate(value, mistake, explanation):
    return RationalCandidate(Fraction(value), mistake, explanation)


def candidates(question):
    if question.difficulty not in SUPPORTED_LEVELS.get(question.generator_id, ()):
        return None
    p = question.parameters
    if set(p) != {"template", "values"}:
        return None
    name = p["template"]
    values = p["values"]
    a, b = values["a"], values["b"]

    if name in ("negative_plus", "add_negative"):
        return [
            candidate(abs(a) + abs(b), "add_magnitudes_positive",
                      "Adds the magnitudes and gives a positive answer."),
            candidate(-abs(a) - abs(b), "add_magnitudes_negative",
                      "Adds the magnitudes and makes the result negative because one number is negative."),
            candidate(-(a + b), "reverse_difference_sign",
                      "Finds the difference of the magnitudes but assigns the opposite sign."),
        ]

    if name == "past_zero":
        return [
            candidate(b - a, "subtract_smaller_from_larger",
                      "Subtracts the smaller number from the larger and misses crossing zero."),
            candidate(a + b, "add_instead_of_subtract",
                      "Adds the numbers instead of subtracting."),
            candidate(-a - b, "negate_both_numbers",
                      "Makes both numbers negative and combines them."),
        ]

    if name == "negative_minus":
        return [
            candidate(a + b, "move_right_when_subtracting",
                      "Moves right by the subtracted amount instead of moving left."),
            candidate(abs(a) - b, "ignore_starting_minus",
                      "Drops the minus sign on the starting number before subtracting."),
            candidate(abs(a) + b, "positive_sum",
                      "Adds the magnitudes but gives a positive result."),
        ]

    if name == "subtract_negative":
        return [
            candidate(a + b, "subtract_negative_as_positive",
                      "Subtracts the magnitude of the negative number instead of adding it."),
            candidate(-(a - b), "reverse_result_sign",
                      "Reverses the sign after evaluating the subtraction."),
            candidate(abs(a) - abs(b), "discard_number_signs",
                      "Removes the signs on the numbers and subtracts their magnitudes."),
        ]

    if name not in ("two_negatives", "minus_then_negative", "mixed_signs"):
        return None
    c = values["c"]
    if name == "two_negatives":
        return [
            candidate(a - b - c, "add_negative_as_positive",
                      "Treats adding the negative middle number as adding its magnitude."),
            candidate(a + b + c, "subtract_negative_as_positive",
                      "Treats subtracting the final negative number as subtracting its magnitude."),
            candidate(a - b + c, "reverse_both_sign_rules",
                      "Adds the middle magnitude but subtracts the final magnitude."),
        ]
    if name == "minus_then_negative":
        return [
            candidate(a - b + c, "subtract_negative_as_positive",
                      "Subtracts the final magnitude instead of adding it."),
            candidate(a + b - c, "turn_first_subtraction_into_addition",
                      "Adds the positive middle number instead of subtracting it."),
            candidate(a - (b - c), "group_subtractions",
                      "Groups the two numbers after the first minus as a separate subtraction."),
        ]
    return [
        candidate(a + b + c, "subtract_negative_as_positive",
                  "Subtracts the middle magnitude instead of adding it."),
        candidate(a - b - c, "add_negative_as_positive",
                  "Adds the final magnitude instead of subtracting it."),
        candidate(a + b - c, "reverse_both_sign_rules",
                  "Subtracts the middle magnitude but adds the final magnitude."),
    ]