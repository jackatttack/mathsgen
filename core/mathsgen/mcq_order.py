"""Authored precedence and bracket errors for introductory calculations."""
from fractions import Fraction

from .multiple_choice import RationalCandidate


SUPPORTED_LEVELS = {"number.operations.order": (1, 2)}


def candidate(value, mistake, explanation):
    return RationalCandidate(Fraction(value), mistake, explanation)


def candidates(question):
    if question.difficulty not in SUPPORTED_LEVELS.get(question.generator_id, ()):
        return None
    p = question.parameters
    if set(p) != {"template", "values"}:
        return None
    name = p["template"]
    v = p["values"]
    a, b, c = (Fraction(v[key]) for key in ("a", "b", "c"))

    if name == "plus_times":
        return [
            candidate((a + b) * c, "left_to_right",
                      "Adds the first two numbers before multiplying."),
            candidate(a + b + c, "multiplication_as_addition",
                      "Adds all three numbers, treating multiplication as addition."),
            candidate(a * b * c, "addition_as_multiplication",
                      "Multiplies all three numbers, treating addition as multiplication."),
        ]
    if name == "times_minus":
        return [
            candidate(a * (b - c), "subtraction_first",
                      "Subtracts the final number before carrying out the multiplication."),
            candidate(a * b + c, "lose_subtraction_sign",
                      "Multiplies correctly but adds the final number."),
            candidate(a + b - c, "multiplication_as_addition",
                      "Adds the first two numbers instead of multiplying."),
        ]
    if name == "minus_times":
        return [
            candidate((a - b) * c, "left_to_right",
                      "Subtracts the first two numbers before multiplying."),
            candidate(a + b * c, "lose_subtraction_sign",
                      "Finds the product but adds it instead of subtracting it."),
            candidate(a - b - c, "subtract_factors_separately",
                      "Subtracts each factor separately instead of subtracting their product."),
        ]
    if name == "plus_divide":
        return [
            candidate((a + b) / c, "left_to_right",
                      "Adds the first two numbers before dividing."),
            candidate(a + b * c, "multiply_instead_of_divide",
                      "Multiplies the last two numbers instead of dividing."),
            candidate(a + c / b, "reverse_division",
                      "Reverses the dividend and divisor in the final operation."),
        ]
    if name == "bracket_times":
        return [
            candidate(a + b * c, "multiply_second_term_only",
                      "Multiplies only the second term inside the bracket."),
            candidate(a * c + b, "multiply_first_term_only",
                      "Multiplies only the first term inside the bracket."),
            candidate(a + b + c, "add_multiplier",
                      "Adds the multiplier to the bracket total instead of multiplying."),
        ]
    if name == "times_bracket":
        return [
            candidate(a * b - c, "multiply_first_term_only",
                      "Multiplies the first term but leaves the subtracted term unmultiplied."),
            candidate(b - a * c, "multiply_second_term_only",
                      "Multiplies only the second term inside the bracket."),
            candidate(a * (b + c), "lose_bracket_minus",
                      "Adds the bracket terms instead of subtracting."),
        ]
    if name == "bracket_divide":
        return [
            candidate(a - b / c, "divide_second_term_only",
                      "Divides only the second term inside the bracket."),
            candidate(a / c - b, "divide_first_term_only",
                      "Divides only the first term inside the bracket."),
            candidate((a - b) * c, "multiply_instead_of_divide",
                      "Multiplies the bracket result instead of dividing."),
        ]
    if name == "four_terms":
        d = Fraction(v["d"])
        return [
            candidate((a + b) * c - d, "left_to_right",
                      "Adds the first two numbers before multiplying."),
            candidate((a + b) * (c - d), "addition_subtraction_first",
                      "Completes both the addition and subtraction before multiplying."),
            candidate(a + b * c + d, "lose_final_minus",
                      "Uses multiplication first but adds the final number."),
        ]
    return None