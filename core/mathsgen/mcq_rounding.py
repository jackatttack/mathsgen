"""Exact rounding misconceptions for the consolidated rounding family."""
from fractions import Fraction

from .core import Content
from .multiple_choice import RationalCandidate
from .rounding import (
    fixed_text, significant_text, round_half_up, round_significant,
    significant_exponent,
)


SUPPORTED_LEVELS = {"number.rounding.decimal_places": (1, 2)}


def candidate(value, mistake, explanation):
    return RationalCandidate(Fraction(value), mistake, explanation)


def candidates(question):
    if question.difficulty not in SUPPORTED_LEVELS.get(question.generator_id, ()):
        return None
    outer = question.parameters
    if set(outer) != {"source", "source_level", "inner"}:
        return None
    source = outer["source"]
    p = outer["inner"]
    if source not in ("places", "figures") or p.get("form") not in ("round", "context"):
        return None
    value = Fraction(p["digits"]) * Fraction(10) ** p["exponent"]
    amount = p["amount"]
    places = amount if source == "places" else amount - 1 - significant_exponent(value)
    scale = Fraction(10) ** places
    magnitude = abs(value) * scale
    whole = magnitude.numerator // magnitude.denominator
    sign = -1 if value < 0 else 1
    truncated = sign * Fraction(whole) / scale
    upward = sign * Fraction(whole + (magnitude != whole)) / scale
    rounding = round_half_up if source == "places" else round_significant
    confused = round_significant if source == "places" else round_half_up
    result = [
        candidate(truncated, "truncate",
                  "Drops the remaining digits without checking whether to round up."),
        candidate(upward, "always_round_up",
                  "Rounds the magnitude up whenever any digits are discarded."),
        candidate(confused(value, amount), "confuse_places_and_figures",
                  "Uses significant figures instead of decimal places, or vice versa."),
    ]
    if amount > 1:
        result.append(candidate(
            rounding(value, amount - 1), "one_fewer_place_or_figure",
            "Rounds to one fewer decimal place or significant figure than requested."))
    result.append(candidate(
        rounding(value, amount + 1), "one_extra_place_or_figure",
        "Keeps one extra decimal place or significant figure."))
    return result


def format_candidate(question, entry):
    """Use decimal notation, retaining meaningful trailing zeros."""
    outer = question.parameters
    amount = outer["inner"]["amount"]
    if outer["source"] == "places":
        text = fixed_text(entry.value, amount)
    else:
        # Zero can occur as a wrong result and has no significant exponent.
        text = significant_text(entry.value, amount) if entry.value else "0"
    return Content(text, text)