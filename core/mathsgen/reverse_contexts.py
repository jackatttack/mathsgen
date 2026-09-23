"""Worded contexts for number.percentages.reverse.

Level 3: a price before 20% VAT, or a salary before a pay rise.
Level 4: undo two successive percentage changes.

Originals are whole pounds. check() divides exact Fractions;
solve() sets up the forward story equation and solves it in SymPy.
"""
from fractions import Fraction

from .core import Content, require
from . import worded
from .worded import (Context, NAMES, article, distinct_names, integers,
                     money_answer, pounds, sympy_solve, whole)


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {3: 0.5, 4: 0.5}
MARKS = {3: 3, 4: 4}
WORKING_LINES = {3: 5, 4: 6}

ITEMS = ("coat", "bike", "laptop", "sofa", "tent", "watch", "guitar",
         "games console", "jacket", "printer")
PAY_RISES = (2, 3, 4, 5, 6, 8, 10)
SUCCESSIVE_RATES = (5, 10, 15, 20, 25, 30, 40, 50)
VAT_RATE = 20


# ------------------------------------------------------------ level 3: VAT

def build_vat(rng):
    return {"context": "vat", "item": rng.choice(ITEMS),
            "given": rng.randint(10, 500) * (100 + VAT_RATE)}


def check_vat(p):
    integers(p, "given")
    require(p["item"] in ITEMS, "Unknown item")
    original = whole(Fraction(p["given"] * 100, 100 + VAT_RATE), 1000, 50000,
                     "Price before VAT outside bounds")
    require(original % 100 == 0, "Expected a whole-pound price before VAT")
    return original


def parts_vat(p):
    original = check_vat(p)
    text = ("The price of {} including VAT at {}% is {}. "
            "Work out the price before VAT was added.").format(
        article(p["item"]), VAT_RATE, pounds(p["given"]))
    return {"prompt": Content(text), "answer": money_answer(original),
            "answer_display": Content(pounds(original))}


def solve_vat(p, sympy):
    x = sympy.Symbol("x")
    (original,) = sympy_solve(sympy, [sympy.Eq(x + x * sympy.Rational(VAT_RATE, 100),
                                               p["given"])], [x])
    return money_answer(original)


# --------------------------------------------------------- level 3: salary

def build_salary(rng):
    rate = rng.choice(PAY_RISES)
    original = 500 * rng.randint(30, 120)
    return {"context": "salary", "name": rng.choice(NAMES), "rate": rate,
            "new": original * (100 + rate) // 100}


def check_salary(p):
    integers(p, "rate new")
    distinct_names(p["name"])
    require(p["rate"] in PAY_RISES, "Pay rise choice")
    original = whole(Fraction(p["new"] * 100, 100 + p["rate"]), 10000, 80000,
                     "Salary must be whole pounds")
    return original * 100


def parts_salary(p):
    pence = check_salary(p)
    text = ("{name} gets a pay rise of {rate}%. {name}'s new salary is £{new:,}. "
            "What was {name}'s salary before the pay rise?").format(**p)
    return {"prompt": Content(text), "answer": money_answer(pence),
            "answer_display": Content(pounds(pence))}


def solve_salary(p, sympy):
    s = sympy.Symbol("s")
    (salary,) = sympy_solve(sympy, [sympy.Eq(s * (1 + sympy.Rational(p["rate"], 100)),
                                             p["new"])], [s])
    return money_answer(salary * 100)


# ----------------------------------------------------- level 4: successive

def build_successive(rng):
    up, down = rng.choice(SUCCESSIVE_RATES), rng.choice(SUCCESSIVE_RATES)
    original = rng.randint(20, 800) * 100
    final = Fraction(original * (100 + up) * (100 - down), 10000)
    return {"context": "successive", "item": rng.choice(ITEMS), "up": up, "down": down,
            "final": int(final) if final.denominator == 1 else 0}


def check_successive(p):
    integers(p, "up down final")
    require(p["item"] in ITEMS and p["up"] in SUCCESSIVE_RATES
            and p["down"] in SUCCESSIVE_RATES, "Story choices")
    require(p["final"] > 0, "Final price must be positive")
    original = whole(Fraction(p["final"] * 10000, (100 + p["up"]) * (100 - p["down"])),
                     2000, 80000, "Original outside bounds")
    require(original % 100 == 0, "Expected a whole-pound original price")
    return original


def parts_successive(p):
    original = check_successive(p)
    text = ("The price of {} was increased by {}%. The new price was then reduced by {}% "
            "in a sale. It now costs {}. Work out the original price.").format(
        article(p["item"]), p["up"], p["down"], pounds(p["final"]))
    return {"prompt": Content(text), "answer": money_answer(original),
            "answer_display": Content(pounds(original))}


def solve_successive(p, sympy):
    R, o = sympy.Rational, sympy.Symbol("o")
    (original,) = sympy_solve(sympy, [sympy.Eq(
        o * (1 + R(p["up"], 100)) * (1 - R(p["down"], 100)), p["final"])], [o])
    return money_answer(original)


# ------------------------------------------------------------ registry

CONTEXTS = {
    "vat": Context(3, frozenset({"context", "item", "given"}),
                   build_vat, check_vat, parts_vat, solve_vat),
    "salary": Context(3, frozenset({"context", "name", "rate", "new"}),
                      build_salary, check_salary, parts_salary, solve_salary),
    "successive": Context(4, frozenset({"context", "item", "up", "down", "final"}),
                          build_successive, check_successive, parts_successive,
                          solve_successive),
}


def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    import sympy
    expected = CONTEXTS[q.parameters["context"]].solve(q.parameters, sympy)
    require(expected == q.answer, "Independent reverse percentage disagrees")
    return True