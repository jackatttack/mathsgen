"""Shared helpers for IB Mathematics: applications and interpretation SL.

IB conventions are decided here, in one place:
- final answers to three significant figures unless a question says
  otherwise; money to two decimal places;
- a question is a short context followed by lettered parts, each with its
  marks, and later parts may build on earlier ones;
- every numeric answer keeps an unrounded value (up to 12 significant
  figures) for checking, as a mark scheme does.

Values stay exact Fractions wherever the mathematics allows, so rounding
decisions are made on digits rather than on floats.
"""
from fractions import Fraction

from ..core import Content, require
from .. import rich_blocks as rb
from ..rounding import (
    decimal_text, fixed_text, round_half_up, round_significant,
    significant_exponent, terminates,
)


TOPIC = "ib_ai_sl"
# Current course: first exams 2021, last exams 2028. A set for the next
# syllabus (first exams 2029) can sit beside it under its own tag.
SYLLABUS_TAG = "ib_ai_sl_2021"
BASE_TAGS = ("ib", TOPIC, SYLLABUS_TAG)

# --- Editable context pools ------------------------------------------------
NAMES = (
    "Adaeze", "Bruno", "Camila", "Dev", "Elif", "Felix", "Grace", "Haruto",
    "Ines", "Jonah", "Kofi", "Lena", "Mateo", "Nadia", "Oskar", "Priya",
    "Rafael", "Saanvi", "Tomas", "Wen",
)
# Currency symbol -> the word used in "to the nearest dollar".
CURRENCIES = {"$": "dollar", "€": "euro", "£": "pound"}


# ------------------------------------------------------------ number text

def exact_text(value):
    """A terminating value written in full, such as 2.5 or 1200."""
    return decimal_text(Fraction(value))


def significant(value, figures):
    """Exactly `figures` significant figures, however small the value.

    rounding.significant_text caps decimals at 12 places, which tiny
    probabilities exceed, so the digits are written out here directly.
    """
    value = round_significant(Fraction(value), figures)
    places = max(figures - 1 - significant_exponent(value), 0)
    scaled = abs(value) * 10 ** places
    require(scaled.denominator == 1, "Rounded value is not on its last place")
    digits = str(scaled.numerator)
    if places:
        digits = digits.rjust(places + 1, "0")
        digits = digits[:-places] + "." + digits[-places:]
    return ("-" if value < 0 else "") + digits


def sf3(value):
    """Three significant figures, the IB default."""
    value = Fraction(value)
    if value == 0:
        return "0"
    return significant(value, 3)


def _short_exact(value, digits):
    """The exact decimal if it has at most `digits` significant digits."""
    if not terminates(value):
        return None
    try:
        text = decimal_text(value)
    except ValueError:
        return None
    significant = text.replace("-", "").replace(".", "").lstrip("0")
    return text if len(significant) <= digits else None


def nice(value):
    """Exact when it is short, otherwise three significant figures."""
    value = Fraction(value)
    short = _short_exact(value, 6)
    return short if short is not None else sf3(value)


def exact_or_fraction(value):
    """2.5 when the decimal terminates briefly, otherwise 1/3."""
    value = Fraction(value)
    short = _short_exact(value, 8)
    if short is not None:
        return short
    return "{}/{}".format(value.numerator, value.denominator)


def standard_form(value, figures=3):
    """a × 10^k with 1 <= a < 10, the mantissa to `figures` significant figures."""
    value = Fraction(value)
    require(value > 0, "Standard form needs a positive value")
    exponent = significant_exponent(value)
    mantissa = round_significant(value / Fraction(10) ** exponent, figures)
    if mantissa >= 10:
        mantissa, exponent = mantissa / 10, exponent + 1
    return "{} × 10^{}".format(significant(mantissa, figures), exponent)


def probability_text(value):
    """An exact fraction when its denominator is small, else 3 s.f."""
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    if value.denominator <= 1000:
        return "{}/{}".format(value.numerator, value.denominator)
    return sf3(value)


def to_cents(value):
    """A money value rounded to two decimal places, as an exact Fraction."""
    return round_half_up(Fraction(value), 2)


def round_whole(value):
    return round_half_up(Fraction(value), 0)


def money(value):
    return fixed_text(to_cents(value), 2)


def cash(currency, value):
    """$1234.50"""
    return currency + money(value)


def cash_whole(currency, value):
    """$1235, to the nearest whole unit."""
    return currency + decimal_text(round_whole(value))


def stored(value):
    """Answer value kept for checking: exact if short, else 12 s.f."""
    value = Fraction(value)
    if value == 0:
        return "0"
    short = _short_exact(value, 12)
    if short is not None:
        return short
    return significant(value, 12)


# ------------------------------------------------------------ question shape

def part(label, task, marks, shown, value=None):
    """One lettered part.

    task is plain text or a list of rich runs; shown is the answer text a
    teacher reads; value is the exact numeric answer, or None for a written
    answer such as an expression or a name.
    """
    runs = [rb.text(task)] if isinstance(task, str) else list(task)
    return {"label": label, "runs": runs, "marks": marks, "shown": shown, "value": value}


def plain(runs):
    return "".join(run["text"] for run in runs)


def assemble(context, parts):
    """Prompt, answer, display, marks and working space for one question.

    context is a list of paragraphs, each plain text or a list of rich runs.
    A single part is printed without a letter, as on a short Paper 1 item.
    """
    require(bool(parts), "A question needs at least one part")
    blocks, lines = [], []
    for item in context:
        runs = [rb.text(item)] if isinstance(item, str) else list(item)
        blocks.append(rb.paragraph(*runs))
        lines.append(plain(runs))
    lettered = len(parts) > 1
    answers, shown, total = [], [], 0
    for item in parts:
        prefix = "({}) ".format(item["label"]) if lettered else ""
        runs = ([rb.text(prefix)] if prefix else []) + item["runs"]
        runs.append(rb.text(" [{}]".format(item["marks"])))
        blocks.append(rb.paragraph(*runs))
        lines.append(plain(runs))
        value = item["value"]
        answers.append({
            "label": item["label"],
            "shown": item["shown"],
            "value": None if value is None else stored(value),
        })
        shown.append(prefix + item["shown"])
        total += item["marks"]
    return {
        "prompt": Content("\n".join(lines), blocks=tuple(blocks)),
        "answer": {"kind": "ib_parts", "parts": answers},
        "answer_display": Content("\n".join(shown),
                                  blocks=tuple(rb.prose(line) for line in shown)),
        "marks": total,
        # Long multi-part questions must still fit one PDF page.
        "working_lines": min(3 + total, 14),
    }


# ------------------------------------------------------------ building and checking

def pick_valid(rng, candidate, check, attempts=500):
    """Draw candidates until one passes check, which raises ValueError."""
    for _ in range(attempts):
        parameters = candidate(rng)
        try:
            check(parameters)
        except ValueError:
            continue
        return parameters
    raise ValueError("No valid parameters found")


def require_int(value, low, high, message):
    require(type(value) is int and low <= value <= high, message)


def answer_values(question):
    """{label: stored value text} for every part."""
    return {item["label"]: item["value"] for item in question.answer["parts"]}


def answer_shown(question):
    return {item["label"]: item["shown"] for item in question.answer["parts"]}


def close(stored_text, expected, relative=1e-9):
    """Whether a stored answer matches an independently computed float."""
    require(stored_text is not None, "Expected a numeric answer")
    actual = float(Fraction(stored_text))
    return abs(actual - expected) <= relative * max(1.0, abs(expected))