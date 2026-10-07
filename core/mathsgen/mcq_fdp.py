"""Place-value and percentage-scale errors for single FDP conversions."""
from fractions import Fraction

from .core import Content, rational_text, rational_tex
from .multiple_choice import RationalCandidate
from .rounding import decimal_text


SUPPORTED_LEVELS = {"number.fdp.fraction_to_decimal": (1, 2)}


def conversion(question):
    """Return source form, target form and exact underlying value, or None."""
    if question.difficulty not in SUPPORTED_LEVELS.get(question.generator_id, ()):
        return None
    outer = question.parameters
    if set(outer) != {"source", "source_level", "inner"}:
        return None
    p = outer["inner"]
    if outer["source"] == "conversions" and p.get("form") == "conversion":
        source, target = p["direction"].split("_to_")
        return source, target, Fraction(p["value"])
    if outer["source"] == "fraction_decimal":
        if p.get("form") == "convert":
            return "fraction", "decimal", Fraction(p["fraction"])
        if p.get("form") == "reverse":
            return "decimal", "fraction", Fraction(p["fraction"])
    return None


def candidate(value, mistake, explanation):
    return RationalCandidate(Fraction(value), mistake, explanation)


def candidates(question):
    converted = conversion(question)
    if converted is None:
        return None
    source, target, value = converted
    if source == "percentage":
        return [
            candidate(value * 100, "omit_division_by_hundred",
                      "Uses the percentage number without dividing by one hundred."),
            candidate(value * 10, "divide_by_ten",
                      "Divides the percentage number by ten instead of one hundred."),
            candidate(value / 100, "divide_by_hundred_twice",
                      "Divides by one hundred twice."),
        ]
    if target == "percentage":
        return [
            candidate(value / 100, "append_percent_sign",
                      "Adds a percent sign to the decimal value without multiplying by one hundred."),
            candidate(value / 10, "multiply_by_ten",
                      "Multiplies the decimal value by ten instead of one hundred."),
            candidate(value * 100, "multiply_by_hundred_twice",
                      "Multiplies by one hundred twice before adding the percent sign."),
        ]
    result = [
        candidate(value * 10, "place_value_ten_times_large",
                  "Uses a place value ten times too large in the conversion."),
        candidate(value / 10, "place_value_ten_times_small",
                  "Uses a place value ten times too small in the conversion."),
    ]
    if source == "fraction":
        result.append(candidate(
            Fraction(value.numerator, 100), "denominator_as_hundred",
            "Treats the fraction's denominator as one hundred without rescaling its numerator."))
    else:
        result.append(candidate(
            1 / value, "invert_fraction",
            "Reverses the numerator and denominator of the converted fraction."))
    return result


def format_candidate(question, entry):
    """All entries use the target form; percentages retain exact value semantics."""
    _, target, _ = conversion(question)
    if target == "fraction":
        return Content(rational_text(entry.value), rational_tex(entry.value))
    if target == "percentage":
        number = decimal_text(entry.value * 100)
        return Content(number + "%", number + r"\%")
    number = decimal_text(entry.value)
    return Content(number, number)