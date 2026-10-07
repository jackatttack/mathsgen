"""Misconception-based options for percentage multipliers (find direction).

number.percentages.multiplier asks for a decimal multiplier (direct and
context forms at every level, repeated changes at level 3, compound change
at level 4) or, at level 2, for a new amount found with a multiplier. Each
distractor follows a named wrong method.

The interpret direction answers with a percentage and a direction rather
than a single number, so it does not opt in.
"""
from fractions import Fraction

from .core import Content
from .multiple_choice import RationalCandidate
from .percentage_multiplier import money_text, multiplier_for
from .rounding import decimal_text


FIND = "number.percentages.multiplier"
SUPPORTED_LEVELS = {FIND: (1, 2, 3, 4)}
PLACE_VALUE_SLIP_BELOW = 10  # 4% -> 1.4 is a believable slip; 40% -> 5 is not


def candidate(value, mistake, explanation):
    return RationalCandidate(Fraction(value), mistake, explanation)


def positive(found):
    """A multiplier or amount of zero or less is not a believable answer."""
    return [item for item in found if item.value > 0]


def sign_of(direction):
    return 1 if direction == "increase" else -1


def candidates(question):
    if question.difficulty not in SUPPORTED_LEVELS.get(question.generator_id, ()):
        return None
    p = question.parameters
    form = p.get("form")
    if form in ("direct", "context"):
        return single_change(Fraction(p["percentage"]), p["direction"])
    if form == "apply":
        return apply_change(Fraction(p["amount"]), Fraction(p["percentage"]), p["direction"])
    if form == "repeated":
        return repeated_change(p["first"], p["second"])
    if form == "compound":
        return compound_change(Fraction(p["percentage"]), p["direction"], p["years"])
    return None


def single_change(percentage, direction):
    sign = sign_of(direction)
    found = [
        candidate(percentage / 100, "percentage_as_multiplier",
                  "Uses the percentage itself as the multiplier, without adding to or subtracting from 1."),
        candidate(1 - sign * percentage / 100, "wrong_direction",
                  "Uses the multiplier for the opposite change."),
    ]
    if percentage < PLACE_VALUE_SLIP_BELOW:
        found.append(candidate(1 + sign * percentage / 10, "place_value_slip",
                               "Puts the percentage in the wrong decimal place, such as 1.4 for a 4% increase."))
    return positive(found)


def apply_change(amount, percentage, direction):
    sign = sign_of(direction)
    found = [
        candidate(amount * percentage / 100, "change_only",
                  "Gives the change itself instead of the new amount."),
        candidate(amount * (1 - sign * percentage / 100), "wrong_direction",
                  "Applies the opposite change."),
        candidate(amount + sign * percentage, "percentage_as_pounds",
                  "Adds or subtracts the percentage as a number of pounds."),
    ]
    if percentage < PLACE_VALUE_SLIP_BELOW:
        found.append(candidate(amount * (1 + sign * percentage / 10), "place_value_slip",
                               "Uses a multiplier with the percentage in the wrong decimal place."))
    return positive(found)


def repeated_change(first, second):
    (a, first_direction), (b, second_direction) = first, second
    a, b = Fraction(a), Fraction(b)
    first_multiplier = multiplier_for(a, first_direction)
    second_multiplier = multiplier_for(b, second_direction)
    total = sign_of(first_direction) * a + sign_of(second_direction) * b
    return positive([
        candidate(1 + total / 100, "add_percentages",
                  "Adds the two percentage changes and uses one multiplier for the total."),
        candidate(first_multiplier + second_multiplier, "add_multipliers",
                  "Adds the two multipliers instead of multiplying them."),
        candidate(second_multiplier, "second_change_only",
                  "Uses only the second change."),
        candidate(first_multiplier, "first_change_only",
                  "Uses only the first change."),
    ])


def compound_change(percentage, direction, years):
    multiplier = multiplier_for(percentage, direction)
    return positive([
        candidate(1 + sign_of(direction) * years * percentage / 100, "simple_change",
                  "Adds the yearly percentage once per year instead of compounding."),
        candidate(multiplier * years, "multiplier_times_years",
                  "Multiplies the yearly multiplier by the number of years instead of raising it to that power."),
        candidate(multiplier, "one_year_only",
                  "Gives the multiplier for one year only."),
    ])


def format_candidate(question, candidate):
    """Money as pounds and pence; multipliers as exact decimals, like the original answer."""
    value = Fraction(candidate.value)
    if question.answer.get("kind") == "money":
        return Content(money_text(value))
    return Content(decimal_text(value))