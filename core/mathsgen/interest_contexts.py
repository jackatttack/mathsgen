"""Applied forms for number.percentages.simple_interest: interest after tax.

L2 after_tax      one year at R%, then T% tax on the interest: the amount kept
L3 tax_rate       the amount kept after tax is given: find the rate R
L4 tax_principal  several years at R% simple interest, T% tax on each year's
                  interest; the total kept is given: find the amount invested

Bare simple-interest questions already store an integer "context" (which
wording to use), so an applied question is recognised by a STRING context:
use is_applied(), not worded.is_worded(), for this generator.

check() computes with exact Fractions. validate_independently() solves the
story's equation with SymPy, adding the kept interest year by year.
"""
from fractions import Fraction

from .core import Content, require
from . import worded
from .worded import NAMES, Context, money_answer, pounds


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {2: 0.35, 3: 0.4, 4: 0.4}
MARKS = {2: 2, 3: 3, 4: 4}
WORKING_LINES = {2: 3, 3: 5, 4: 6}

PRINCIPAL_POUNDS = (1500, 2000, 2500, 3000, 4000, 4500, 5000, 5500, 6000, 8000)
RATES = ("1.5", "2", "2.4", "2.5", "3", "3.2", "3.5", "4", "4.5", "5")
TAX_RATES = (20, 40, 45)
YEARS = (2, 3, 4, 5)


def context_share(level):
    return CONTEXT_SHARE.get(level, 0.0)


def is_applied(question):
    p = question.parameters
    return isinstance(p, dict) and isinstance(p.get("context"), str)


# ------------------------------------------------------------------ shared

def build(rng, context):
    return {
        "context": context, "name": rng.choice(NAMES),
        "principal_pence": rng.choice(PRINCIPAL_POUNDS) * 100,
        "rate": rng.choice(RATES), "tax": rng.choice(TAX_RATES),
        "years": rng.choice(YEARS) if context == "tax_principal" else 1,
    }


def check(p):
    """The interest kept after tax, in whole pence."""
    require(p["name"] in NAMES, "Unknown name")
    require(p["principal_pence"] in [v * 100 for v in PRINCIPAL_POUNDS], "Principal")
    require(p["rate"] in RATES, "Rate outside bounds")
    require(p["tax"] in TAX_RATES, "Tax rate outside bounds")
    expected_years = YEARS if p["context"] == "tax_principal" else (1,)
    require(p["years"] in expected_years, "Years outside bounds")
    yearly = Fraction(p["principal_pence"]) * Fraction(p["rate"]) / 100
    kept = yearly * (1 - Fraction(p["tax"], 100)) * p["years"]
    require(kept.denominator == 1 and kept > 0, "Kept interest must be whole pence")
    return int(kept)


def parts_after_tax(p):
    kept = check(p)
    name = p["name"]
    text = ("{n} invests {money} in an account paying {r}% interest per year. After one "
            "year, {n} pays tax of {t}% on the interest. How much of the interest does "
            "{n} keep?").format(n=name, money=pounds(p["principal_pence"]), r=p["rate"],
                                t=p["tax"])
    return {"prompt": Content(text), "answer": money_answer(kept),
            "answer_display": Content(pounds(kept))}


def parts_tax_rate(p):
    kept = check(p)
    name = p["name"]
    text = ("A savings account pays interest at a rate of R% per year. {n} invests {money} "
            "for one year. At the end of the year, {n} pays tax of {t}% on the interest, "
            "and keeps {kept}. Work out the value of R.").format(
        n=name, money=pounds(p["principal_pence"]), t=p["tax"], kept=pounds(kept))
    return {"prompt": Content(text), "answer": {"kind": "rate", "value": p["rate"]},
            "answer_display": Content("R = " + p["rate"])}


def parts_tax_principal(p):
    kept = check(p)
    name = p["name"]
    text = ("{n} invests some money at {r}% simple interest per year for {y} years. Each "
            "year, {n} pays tax of {t}% on that year's interest. Altogether, {n} keeps "
            "{kept} of interest. How much did {n} invest?").format(
        n=name, r=p["rate"], y=p["years"], t=p["tax"], kept=pounds(kept))
    return {"prompt": Content(text), "answer": money_answer(p["principal_pence"]),
            "answer_display": Content(pounds(p["principal_pence"]))}


# ----------------------------------------------------------------- registry

KEYS = frozenset({"context", "name", "principal_pence", "rate", "tax", "years"})

CONTEXTS = {
    "after_tax": Context(2, KEYS, lambda rng: build(rng, "after_tax"),
                         check, parts_after_tax, None),
    "tax_rate": Context(3, KEYS, lambda rng: build(rng, "tax_rate"),
                        check, parts_tax_rate, None),
    "tax_principal": Context(4, KEYS, lambda rng: build(rng, "tax_principal"),
                             check, parts_tax_principal, None),
}


# ------------------------------------------------ generate and validate

def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    """Solve the story with SymPy, adding each year's kept interest separately."""
    import sympy
    p = q.parameters
    rate = sympy.Rational(p["rate"])
    tax = sympy.Rational(p["tax"], 100)

    def kept_over_years(principal, r):
        total = sympy.Integer(0)
        for _ in range(p["years"]):
            interest = principal * r / 100
            total += interest - interest * tax
        return total

    if p["context"] == "after_tax":
        expected = kept_over_years(sympy.Integer(p["principal_pence"]), rate)
        require(expected == q.answer["pence"], "Independent kept interest disagrees")
        return True
    kept = check(p)
    if p["context"] == "tax_rate":
        r = sympy.Symbol("r", positive=True)
        solutions = sympy.solve(
            sympy.Eq(kept_over_years(sympy.Integer(p["principal_pence"]), r), kept), r)
        require(solutions == [sympy.Rational(q.answer["value"])], "Independent rate disagrees")
        return True
    principal = sympy.Symbol("principal", positive=True)
    solutions = sympy.solve(sympy.Eq(kept_over_years(principal, rate), kept), principal)
    require(solutions == [q.answer["pence"]], "Independent principal disagrees")
    return True