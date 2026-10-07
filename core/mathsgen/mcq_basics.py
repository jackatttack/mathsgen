"""Misconceptions for introductory percentages and substitution.

Support is deliberately limited to inspected forms at levels 1 and 2.
All candidates are derived from the displayed parameters, with no random
offsets or arbitrary nearby numbers.
"""
from fractions import Fraction

from .multiple_choice import RationalCandidate


SUPPORTED_LEVELS = {
    "number.percentages.of_amount": (1, 2),
    "algebra.substitution.values": (1, 2),
}


def candidate(value, mistake, explanation):
    return RationalCandidate(Fraction(value), mistake, explanation)


def percentage_candidates(parameters):
    percentage = Fraction(parameters["percentage"])
    amount = Fraction(parameters["amount"])
    part = amount * percentage / 100
    return [
        candidate(
            amount - part, "give_amount_remaining",
            "Subtracts the percentage amount and gives what remains."),
        candidate(
            amount / 100, "stop_at_one_percent",
            "Finds one percent but does not multiply by the requested percentage."),
        candidate(
            amount * percentage / 10, "divide_by_ten",
            "Divides by ten instead of one hundred when converting the percentage."),
        candidate(
            percentage, "copy_percentage_number",
            "Uses the percentage number itself as the amount."),
    ]


def substitution_candidates(parameters):
    from .algebra_basics import evaluate_terms
    terms = parameters["terms"]
    values = parameters["values"]
    result = []

    if any(value < 0 for value in values.values()):
        result.append(candidate(
            evaluate_terms(terms, {name: abs(value) for name, value in values.items()}),
            "ignore_negative_values",
            "Substitutes positive magnitudes instead of the given negative values."))

    # These levels contain constants and single linear letters only.
    added = 0
    dropped = 0
    for coefficient, monomial in terms:
        if monomial:
            value = values[monomial[0][0]]
            added += coefficient + value
            dropped += value
        else:
            added += coefficient
            dropped += coefficient
    result.extend([
        candidate(
            added, "add_coefficient_and_value",
            "Reads a coefficient next to a letter as addition instead of multiplication."),
        candidate(
            dropped, "omit_coefficients",
            "Substitutes each letter but omits its multiplying coefficient."),
    ])

    if any(coefficient < 0 for coefficient, _ in terms):
        result.append(candidate(
            evaluate_terms([[abs(c), m] for c, m in terms], values),
            "ignore_expression_minus_signs",
            "Treats the negative terms in the expression as positive terms."))

    if any(not monomial for _, monomial in terms):
        result.append(candidate(
            evaluate_terms([[c, m] for c, m in terms if m], values),
            "omit_constant",
            "Evaluates the letter terms but leaves out the constant term."))
    return result


def format_candidate(question, entry):
    """Percentage amounts use exact decimals; substitution keeps integer notation."""
    if question.generator_id == "number.percentages.of_amount":
        from .core import Content
        from .rounding import decimal_text
        text = decimal_text(entry.value)
        return Content(text, text)
    return entry.content()


def candidates(question):
    levels = SUPPORTED_LEVELS.get(question.generator_id, ())
    if question.difficulty not in levels:
        return None
    parameters = question.parameters
    if question.generator_id == "number.percentages.of_amount":
        if set(parameters) != {"percentage", "amount"}:
            return None
        return percentage_candidates(parameters)
    if set(parameters) != {"terms", "values"}:
        return None
    return substitution_candidates(parameters)