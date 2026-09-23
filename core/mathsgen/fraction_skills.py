"""Fractions of amounts and recurring decimals, with exact answers.

Both generators have two forms per level (see FORMS below each class).

Recurring decimals are stored as digit strings: integer part, non-recurring
prefix and recurring period. The displayed form is required to be minimal
(no 0.33-dot, no 0.9-dot); the independent check proves this by long
division, which must reproduce exactly the displayed digits.
"""
from fractions import Fraction
from math import gcd

from .core import Content, GeneratorInfo, rational_tex, rational_text, require
from .family import GeneratorFamily
from . import rich_blocks as rb


# ------------------------------------------------------------ choice pools

NAMES = ("Amir", "Beth", "Chloe", "Dev", "Ella", "Femi")
UNIT_FRACTIONS = [(1, b) for b in range(2, 11)]
NON_UNIT_FRACTIONS = [(a, b) for b in range(3, 13) for a in range(2, b) if gcd(a, b) == 1]
STAGE_FRACTIONS = [(a, b) for b in range(3, 7) for a in range(1, b) if gcd(a, b) == 1]
MAX_SPENDING_AMOUNT = 600


def fraction_run(pair):
    a, b = pair
    return rb.maths(r"\frac{" + str(a) + "}{" + str(b) + "}", "{}/{}".format(a, b))


def number_parts(value, marks, lines, money=False):
    text = rational_text(value)
    shown = "£" + text if money else text
    return {
        "answer": {"kind": "rational", "value": text},
        "answer_display": Content(shown, shown) if not money else Content(shown),
        "marks": marks, "working_lines": lines,
    }


def pair_in(pair, pool):
    return (
        isinstance(pair, list) and len(pair) == 2
        and all(type(v) is int for v in pair) and tuple(pair) in pool
    )


def sentence(before, pair, after):
    """A prompt with one fraction in the middle: plain fallback plus rich blocks."""
    a, b = pair
    return Content(before + "{}/{}".format(a, b) + after,
                   blocks=(rb.paragraph(rb.text(before), fraction_run(pair), rb.text(after)),))


# ------------------------------------------------------- fractions of amounts

AMOUNT_FORMS = {
    1: ("unit", "unit_context"),
    2: ("non_unit", "remaining"),
    3: ("reverse", "reverse_context"),
    4: ("two_stage", "two_stage_reverse"),
}
AMOUNT_KEYS = {
    "unit": {"fraction", "amount"},
    "unit_context": {"fraction", "amount", "context"},
    "non_unit": {"fraction", "amount"},
    "remaining": {"fraction", "amount", "context"},
    "reverse": {"fraction", "part"},
    "reverse_context": {"fraction", "part", "name", "context"},
    "two_stage": {"name", "amount", "first", "second"},
    "two_stage_reverse": {"name", "left", "first", "second"},
}
# (text before the fraction, text after it); {amount}, {part}, {name} fill in.
UNIT_CONTEXTS = (
    ("A class has {amount} pupils. ", " of them walk to school. How many pupils walk to school?"),
    ("A bag holds {amount} sweets. ", " of the sweets are red. How many sweets are red?"),
    ("A farmer has {amount} sheep. ", " of the sheep are black. How many sheep are black?"),
)
REMAINING_CONTEXTS = (
    ("A box holds {amount} eggs. ", " of the eggs are broken. How many eggs are not broken?"),
    ("A cinema has {amount} seats. ", " of the seats are taken. How many seats are empty?"),
    ("A runner plans to run {amount} km. She has run ",
     " of the distance so far. How many kilometres are left?"),
)
# (before, after, answer is money)
REVERSE_CONTEXTS = (
    ("{name} spent ", " of their money. They spent £{part}. "
     "How much money did {name} have to start with?", True),
    ("In a school, ", " of the pupils are in Year 7. There are {part} pupils in Year 7. "
     "How many pupils are in the school?", False),
    ("A tank is ", " full. It holds {part} litres of water. "
     "How many litres does it hold when full?", False),
)


def remaining_after(amount, first, second):
    (p1, q1), (p2, q2) = first, second
    return amount * (q1 - p1) // q1 * (q2 - p2) // q2


class FractionOfAmount(GeneratorFamily):
    info = GeneratorInfo(
        id="number.fractions.of_amount",
        version=2,
        topic="number",
        subtopic="fractions_of_amounts",
        title="Find a fraction of an amount",
        difficulty_descriptions={
            1: "Unit fractions of amounts, bare or in a context.",
            2: "Non-unit fractions, or how much is left.",
            3: "Reverse: find the whole, bare or in a context.",
            4: "Spend a fraction, then a fraction of what is left, forwards or in reverse.",
        },
        tags=("fractions", "fractions_of_amounts", "reverse_fractions"),
    )

    def expected_keys(self, parameters, level):
        form = parameters.get("form")
        require(form in AMOUNT_FORMS[level], "Unexpected form for this level")
        return AMOUNT_KEYS[form] | {"form"}

    def build(self, level, rng):
        form = rng.choice(AMOUNT_FORMS[level])
        if form in ("unit", "unit_context"):
            a, b = rng.choice(UNIT_FRACTIONS)
            p = {"fraction": [a, b], "amount": b * rng.randint(2, 15)}
        elif form in ("non_unit", "remaining"):
            a, b = rng.choice(NON_UNIT_FRACTIONS)
            p = {"fraction": [a, b], "amount": b * rng.randint(2, 12)}
        elif form in ("reverse", "reverse_context"):
            a, b = rng.choice(NON_UNIT_FRACTIONS)
            p = {"fraction": [a, b], "part": a * rng.randint(2, 15)}
            if form == "reverse_context":
                p.update(name=rng.choice(NAMES), context=rng.randrange(len(REVERSE_CONTEXTS)))
        else:
            first, second = rng.choice(STAGE_FRACTIONS), rng.choice(STAGE_FRACTIONS)
            block = first[1] * second[1]
            amount = block * rng.randint(1, MAX_SPENDING_AMOUNT // block)
            p = {"name": rng.choice(NAMES), "first": list(first), "second": list(second)}
            if form == "two_stage":
                p["amount"] = amount
            else:
                p["left"] = remaining_after(amount, first, second)
        if form == "unit_context":
            p["context"] = rng.randrange(len(UNIT_CONTEXTS))
        if form == "remaining":
            p["context"] = rng.randrange(len(REMAINING_CONTEXTS))
        p["form"] = form
        return p

    def check_rules(self, p, level):
        form = p["form"]
        if form in ("unit", "unit_context", "non_unit", "remaining"):
            pool = UNIT_FRACTIONS if level == 1 else NON_UNIT_FRACTIONS
            require(pair_in(p["fraction"], pool), "Fraction outside this level")
            b, amount = p["fraction"][1], p["amount"]
            biggest = 15 if level == 1 else 12
            require(type(amount) is int and amount % b == 0 and 2 * b <= amount <= biggest * b,
                    "Amount outside bounds")
            contexts = {"unit_context": UNIT_CONTEXTS, "remaining": REMAINING_CONTEXTS}.get(form)
            if contexts:
                require(p["context"] in range(len(contexts)), "Invalid context")
        elif form in ("reverse", "reverse_context"):
            require(pair_in(p["fraction"], NON_UNIT_FRACTIONS), "Fraction outside this level")
            a, part = p["fraction"][0], p["part"]
            require(type(part) is int and part % a == 0 and 2 <= part // a <= 15,
                    "Part outside bounds")
            if form == "reverse_context":
                require(p["name"] in NAMES and p["context"] in range(len(REVERSE_CONTEXTS)),
                        "Invalid context")
        else:
            require(p["name"] in NAMES, "Unknown name")
            require(pair_in(p["first"], STAGE_FRACTIONS) and pair_in(p["second"], STAGE_FRACTIONS),
                    "Fractions outside this level")
            block = p["first"][1] * p["second"][1]
            if form == "two_stage":
                amount = p["amount"]
            else:
                left = p["left"]
                require(type(left) is int and left > 0, "Remaining amount must be whole")
                (p1, q1), (p2, q2) = p["first"], p["second"]
                start = Fraction(left * q1 * q2, (q1 - p1) * (q2 - p2))
                require(start.denominator == 1, "Starting amount must be whole")
                amount = int(start)
                require(remaining_after(amount, p["first"], p["second"]) == left,
                        "The stages do not divide exactly")
            require(type(amount) is int and amount % block == 0
                    and block <= amount <= MAX_SPENDING_AMOUNT,
                    "Amount must divide exactly at both stages")

    def parts(self, p, level):
        form = p["form"]
        if form in ("unit", "non_unit"):
            a, b = p["fraction"]
            amount = p["amount"]
            prompt = sentence("Find ", p["fraction"], " of {}.".format(amount))
            return dict(number_parts(amount * a // b, 1 if level == 1 else 2, 3), prompt=prompt)
        if form in ("unit_context", "remaining"):
            a, b = p["fraction"]
            amount = p["amount"]
            contexts = UNIT_CONTEXTS if form == "unit_context" else REMAINING_CONTEXTS
            before, after = contexts[p["context"]]
            prompt = sentence(before.format(amount=amount), p["fraction"], after)
            value = amount * a // b if form == "unit_context" else amount * (b - a) // b
            return dict(number_parts(value, 1 if level == 1 else 2, 3), prompt=prompt)
        if form == "reverse":
            a, b = p["fraction"]
            part = p["part"]
            prompt = sentence("", p["fraction"],
                              " of a number is {}. Find the number.".format(part))
            return dict(number_parts(part * b // a, 2, 4), prompt=prompt)
        if form == "reverse_context":
            a, b = p["fraction"]
            before, after, money = REVERSE_CONTEXTS[p["context"]]
            fill = {"name": p["name"], "part": p["part"]}
            prompt = sentence(before.format(**fill), p["fraction"], after.format(**fill))
            return dict(number_parts(p["part"] * b // a, 3, 4, money=money), prompt=prompt)
        name = p["name"]
        (p1, q1), (p2, q2) = p["first"], p["second"]
        if form == "two_stage":
            amount = p["amount"]
            remaining = remaining_after(amount, p["first"], p["second"])
            fallback = (
                "{name} has £{amount}. {name} spends {p1}/{q1} of it, then {p2}/{q2} of what is "
                "left. How much money does {name} have left?"
            ).format(name=name, amount=amount, p1=p1, q1=q1, p2=p2, q2=q2)
            prompt = Content(fallback, blocks=(rb.paragraph(
                rb.text("{} has £{}. {} spends ".format(name, amount, name)),
                fraction_run(p["first"]), rb.text(" of it, then "),
                fraction_run(p["second"]),
                rb.text(" of what is left. How much money does {} have left?".format(name)),
            ),))
            return {
                "prompt": prompt,
                "answer": {"kind": "rational", "value": rational_text(remaining)},
                "answer_display": Content("£{}".format(remaining)),
                "marks": 3, "working_lines": 5,
            }
        start = p["left"] * q1 * q2 // ((q1 - p1) * (q2 - p2))
        fallback = (
            "{name} spends {p1}/{q1} of their money, then {p2}/{q2} of what is left. "
            "{name} now has £{left}. How much money did {name} have to start with?"
        ).format(name=name, p1=p1, q1=q1, p2=p2, q2=q2, left=p["left"])
        prompt = Content(fallback, blocks=(rb.paragraph(
            rb.text("{} spends ".format(name)), fraction_run(p["first"]),
            rb.text(" of their money, then "), fraction_run(p["second"]),
            rb.text(" of what is left. {} now has £{}. How much money did {} have to "
                    "start with?".format(name, p["left"], name)),
        ),))
        return {
            "prompt": prompt,
            "answer": {"kind": "rational", "value": rational_text(start)},
            "answer_display": Content("£{}".format(start)),
            "marks": 4, "working_lines": 6,
        }

    def validate_independently(self, question):
        """Recompute with SymPy rationals directly from the displayed story."""
        import sympy
        p = question.parameters
        form = p["form"]
        answer = sympy.Rational(question.answer["value"])
        if form in ("unit", "unit_context", "non_unit"):
            expected = sympy.Rational(*p["fraction"]) * p["amount"]
        elif form == "remaining":
            expected = (1 - sympy.Rational(*p["fraction"])) * p["amount"]
        elif form in ("reverse", "reverse_context"):
            expected = p["part"] / sympy.Rational(*p["fraction"])
        elif form == "two_stage":
            left = p["amount"] * (1 - sympy.Rational(*p["first"]))
            expected = left * (1 - sympy.Rational(*p["second"]))
        else:
            # Run the story forwards from the claimed start; it must leave the stated amount.
            after = answer * (1 - sympy.Rational(*p["first"])) * (1 - sympy.Rational(*p["second"]))
            require(after == p["left"], "Starting amount does not leave the stated money")
            expected = answer
        require(expected == answer and answer.q == 1 and answer > 0,
                "Independent fraction check failed")
        return True


# ------------------------------------------------------- recurring decimals

def recurring_value(integer, prefix, period):
    """Exact value of integer.prefix(period recurring)."""
    whole = int(str(integer) + prefix + period)
    head = int(str(integer) + prefix)
    return Fraction(whole - head, 10 ** len(prefix) * (10 ** len(period) - 1))


def expansion(value):
    """(integer, non-recurring digits, recurring digits) by long division."""
    integer, remainder = divmod(value.numerator, value.denominator)
    digits, seen = [], {}
    while remainder and remainder not in seen:
        seen[remainder] = len(digits)
        remainder *= 10
        digits.append(str(remainder // value.denominator))
        remainder %= value.denominator
    if not remainder:
        return integer, "".join(digits), ""
    start = seen[remainder]
    return integer, "".join(digits[:start]), "".join(digits[start:])


def recurring_display(integer, prefix, period):
    """(plain, tex). Dots sit over the first and last recurring digits."""
    dots = "".join(r"\dot{" + d + "}" for d in (period if len(period) <= 2 else period[0] + period[-1]))
    plain = "{}.{}({})".format(integer, prefix, period)
    return plain, "{}.{}{}".format(integer, prefix, dots)


RECURRING_FORMS = {
    1: ("to_fraction", "to_recurring"),
    2: ("to_fraction", "to_recurring"),
    3: ("to_fraction", "show_that"),
    4: ("to_fraction", "to_recurring"),
}
# (level, form) -> (prefix length, period length, whole-number part range)
SHAPES = {
    (1, "to_fraction"): (0, 1, (0, 0)), (1, "to_recurring"): (0, 1, (0, 0)),
    (2, "to_fraction"): (0, 2, (0, 0)), (2, "to_recurring"): (0, 2, (0, 0)),
    (3, "to_fraction"): (1, 1, (0, 0)), (3, "show_that"): (1, 1, (0, 0)),
    (4, "to_fraction"): (1, 2, (1, 3)), (4, "to_recurring"): (1, 1, (0, 0)),
}


class RecurringDecimals(GeneratorFamily):
    info = GeneratorInfo(
        id="number.fractions.recurring_decimals",
        version=2,
        topic="number",
        subtopic="recurring_decimals",
        title="Convert between recurring decimals and fractions",
        difficulty_descriptions={
            1: "One recurring digit, either direction.",
            2: "Two recurring digits, either direction.",
            3: "One non-recurring digit then one recurring digit: convert, or show that.",
            4: "Whole-number part with two recurring digits, or a fraction to a decimal "
               "with a non-recurring digit.",
        },
        tags=("recurring_decimals", "fractions", "decimals"),
    )
    keys = {level: {"form", "integer", "prefix", "period"} for level in (1, 2, 3, 4)}

    def build(self, level, rng):
        form = rng.choice(RECURRING_FORMS[level])
        prefix_length, period_length, (low, high) = SHAPES[(level, form)]
        digits = "0123456789"
        if period_length == 1:
            period = str(rng.randint(1, 8))
        else:
            first, second = rng.sample(digits, 2)
            period = first + second
        prefix = ""
        if prefix_length:
            prefix = rng.choice([d for d in digits if d != period[-1]])
        return {"form": form, "integer": rng.randint(low, high),
                "prefix": prefix, "period": period}

    def check_rules(self, p, level):
        form = p["form"]
        require(form in RECURRING_FORMS[level], "Unexpected form for this level")
        integer, prefix, period = p["integer"], p["prefix"], p["period"]
        require(type(integer) is int and isinstance(prefix, str) and isinstance(period, str),
                "Invalid digit fields")
        require((prefix + period).isdigit() or (not prefix and period.isdigit()), "Digits only")
        prefix_length, period_length, (low, high) = SHAPES[(level, form)]
        require((len(prefix), len(period)) == (prefix_length, period_length),
                "Digit pattern outside this level")
        require(low <= integer <= high, "Whole-number part outside bounds")
        require(period not in ("0", "9"), "Period must genuinely recur")
        require(len(period) == 1 or period[0] != period[1], "Period is not minimal")
        require(not prefix or prefix[-1] != period[-1], "Non-recurring digit could join the period")

    def parts(self, p, level):
        form = p["form"]
        plain, tex = recurring_display(p["integer"], p["prefix"], p["period"])
        value = recurring_value(p["integer"], p["prefix"], p["period"])
        marks = {1: 2, 2: 2, 3: 3, 4: 3}[level]
        lines = {1: 4, 2: 4, 3: 5, 4: 6}[level]
        if form == "to_recurring":
            prompt = Content(
                "Write {} as a recurring decimal.".format(rational_text(value)),
                blocks=(rb.paragraph(
                    rb.text("Write "), rb.maths(rational_tex(value), rational_text(value)),
                    rb.text(" as a recurring decimal."),
                ),),
            )
            return {
                "prompt": prompt,
                "answer": {"kind": "recurring", "integer": p["integer"],
                           "prefix": p["prefix"], "period": p["period"]},
                "answer_display": Content(plain, tex),
                "marks": marks, "working_lines": lines,
            }
        if form == "show_that":
            prompt = Content(
                "Show that {} = {}. The digits in brackets recur.".format(
                    plain, rational_text(value)),
                blocks=(rb.paragraph(
                    rb.text("Show that "),
                    rb.maths(tex + " = " + rational_tex(value),
                             plain + " = " + rational_text(value)),
                    rb.text("."),
                ),),
            )
        else:
            prompt = Content(
                "Write {} as a fraction in its simplest form. The digits in brackets recur.".format(plain),
                blocks=(rb.paragraph(
                    rb.text("Write "), rb.maths(tex, plain),
                    rb.text(" as a fraction in its simplest form."),
                ),),
            )
        return {
            "prompt": prompt,
            "answer": {"kind": "rational", "value": rational_text(value)},
            "answer_display": Content(rational_text(value), rational_tex(value)),
            "marks": marks, "working_lines": lines,
        }

    def validate_independently(self, question):
        """Long division must reproduce the displayed digits exactly."""
        p = question.parameters
        answer = question.answer
        if answer["kind"] == "recurring":
            # The fraction shown in the prompt, divided out, must give the answer digits.
            value = recurring_value(p["integer"], p["prefix"], p["period"])
            digits = expansion(value)
            require(digits == (answer["integer"], answer["prefix"], answer["period"]),
                    "Long division of the fraction disagrees with the answer")
            return True
        integer, prefix, period = expansion(Fraction(answer["value"]))
        require((integer, prefix, period) == (p["integer"], p["prefix"], p["period"]),
                "Answer does not expand to the displayed recurring decimal")
        return True