"""Worded contexts for number.integers.negatives.

L1: a temperature change.   L2: a temperature difference, or a bank balance.
L3: a steady fall, or a quiz with negative marking.
L4: a mean temperature, or a missing temperature from a mean.

check() computes from the displayed numbers; solve() recomputes with SymPy
from the story written a different way (sums, products and a mean equation).
"""
from fractions import Fraction

from .core import Content, require
from . import worded
from .worded import (Context, NAMES, distinct_names, integers, quantity,
                     sympy_solve, whole)


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {1: 0.35, 2: 0.4, 3: 0.4, 4: 0.5}
MARKS = {1: 1, 2: 2, 3: 2, 4: 3}
WORKING_LINES = {1: 2, 2: 3, 3: 3, 4: 5}

PLACES = ("Oslo", "Moscow", "Reykjavik", "Helsinki", "Warsaw", "Toronto",
          "Aberdeen", "Edinburgh")
TIMES = (("6 am", "noon"), ("midnight", "9 am"), ("3 pm", "11 pm"), ("8 pm", "5 am"))
TEMPERATURE_LOW, TEMPERATURE_HIGH = -15, 10


def degrees(value):
    return "{}°C".format(value)


def temperature_answer(value):
    return quantity(value, "°C")


# ------------------------------------------------- L1: temperature change

def build_change(rng):
    change = rng.choice([v for v in range(-15, 16) if abs(v) >= 3])
    return {"context": "temperature_change", "place": rng.choice(PLACES),
            "times": rng.randrange(len(TIMES)),
            "start": rng.choice([v for v in range(-12, 9) if v]), "change": change}


def check_change(p):
    integers(p, "times start change")
    require(p["place"] in PLACES and 0 <= p["times"] < len(TIMES), "Story choices")
    require(-12 <= p["start"] <= 8 and p["start"] != 0, "Start bounds")
    require(3 <= abs(p["change"]) <= 15, "Change bounds")
    end = p["start"] + p["change"]
    require(end != 0 and abs(end) <= 20, "End bounds")
    require(p["start"] < 0 or end < 0, "A negative temperature must be involved")
    return end


def parts_change(p):
    end = check_change(p)
    first, second = TIMES[p["times"]]
    moved = "risen" if p["change"] > 0 else "fallen"
    text = ("At {} the temperature in {} was {}. By {} it had {} by {} degrees. "
            "What was the temperature at {}?").format(
        first, p["place"], degrees(p["start"]), second, moved, abs(p["change"]), second)
    return {"prompt": Content(text), "answer": temperature_answer(end),
            "answer_display": Content(degrees(end))}


def solve_change(p, sympy):
    t = sympy.Symbol("t")
    (end,) = sympy_solve(sympy, [sympy.Eq(t - p["change"], p["start"])], [t])
    return temperature_answer(end)


# --------------------------------------------- L2: temperature difference

def build_difference(rng):
    a = rng.randint(-20, -1)
    return {"context": "temperature_difference",
            "place_a": rng.choice(PLACES), "place_b": rng.choice(PLACES),
            "a": a, "b": rng.randint(a + 3, 25)}


def check_difference(p):
    integers(p, "a b")
    require(p["place_a"] in PLACES and p["place_b"] in PLACES
            and p["place_a"] != p["place_b"], "Two different places")
    require(-20 <= p["a"] <= -1 and p["a"] + 3 <= p["b"] <= 25, "Temperature bounds")
    return p["b"] - p["a"]


def parts_difference(p):
    gap = check_difference(p)
    text = ("The temperature in {} is {}. The temperature in {} is {}. "
            "How many degrees warmer is it in {} than in {}?").format(
        p["place_a"], degrees(p["a"]), p["place_b"], degrees(p["b"]),
        p["place_b"], p["place_a"])
    return {"prompt": Content(text), "answer": quantity(gap, "degrees"),
            "answer_display": Content("{} degrees".format(gap))}


def solve_difference(p, sympy):
    d = sympy.Symbol("d")
    (gap,) = sympy_solve(sympy, [sympy.Eq(p["a"] + d, p["b"])], [d])
    return quantity(gap, "degrees")


# ------------------------------------------------------------ L2: bank

def build_bank(rng):
    balance = rng.randint(5, 80)
    return {"context": "bank", "name": rng.choice(NAMES), "balance": balance,
            "bill": rng.randint(balance + 1, 150)}


def check_bank(p):
    integers(p, "balance bill")
    distinct_names(p["name"])
    require(5 <= p["balance"] < p["bill"] <= 150, "The bill must overdraw the account")
    return p["balance"] - p["bill"]


def bank_display(value):
    return "-£{}".format(-value)


def parts_bank(p):
    left = check_bank(p)
    text = ("{name} has £{balance} in a bank account. {name} pays a bill of £{bill}. "
            "What is the balance of the account now?").format(**p)
    return {"prompt": Content(text), "answer": quantity(left, "£"),
            "answer_display": Content(bank_display(left))}


def solve_bank(p, sympy):
    return quantity(sympy.Integer(p["balance"]) + (-p["bill"]), "£")


# ------------------------------------------------------- L3: steady fall

def build_falling(rng):
    return {"context": "falling", "place": rng.choice(PLACES),
            "start": rng.randint(-5, 10), "rate": rng.randint(2, 6),
            "hours": rng.randint(2, 8)}


def check_falling(p):
    integers(p, "start rate hours")
    require(p["place"] in PLACES, "Unknown place")
    require(-5 <= p["start"] <= 10 and 2 <= p["rate"] <= 6 and 2 <= p["hours"] <= 8,
            "Bounds")
    end = p["start"] - p["rate"] * p["hours"]
    require(-40 <= end < 0, "The temperature must end below zero")
    return end


def parts_falling(p):
    end = check_falling(p)
    text = ("At midnight the temperature in {} was {}. It fell by {} degrees every hour "
            "for {} hours. What was the temperature at the end of this time?").format(
        p["place"], degrees(p["start"]), p["rate"], p["hours"])
    return {"prompt": Content(text), "answer": temperature_answer(end),
            "answer_display": Content(degrees(end))}


def solve_falling(p, sympy):
    change = sympy.Integer(-p["rate"]) * p["hours"]
    return temperature_answer(p["start"] + change)


# ------------------------------------------------------------- L3: quiz

def build_quiz(rng):
    return {"context": "quiz", "name": rng.choice(NAMES),
            "right_points": rng.randint(2, 5), "wrong_points": rng.randint(2, 5),
            "right": rng.randint(1, 8), "wrong": rng.randint(3, 15)}


def check_quiz(p):
    integers(p, "right_points wrong_points right wrong")
    distinct_names(p["name"])
    require(2 <= p["right_points"] <= 5 and 2 <= p["wrong_points"] <= 5, "Scoring")
    require(1 <= p["right"] <= 8 and 3 <= p["wrong"] <= 15, "Answer counts")
    total = p["right_points"] * p["right"] - p["wrong_points"] * p["wrong"]
    require(total < 0, "Keep the total negative so the sign matters")
    return total


def parts_quiz(p):
    total = check_quiz(p)
    correct = "1 answer" if p["right"] == 1 else "{} answers".format(p["right"])
    text = ("In a quiz, each correct answer scores {right_points} points and each wrong "
            "answer scores -{wrong_points} points. {name} gets {correct} correct and "
            "{wrong} answers wrong. What is {name}'s total score?").format(
        correct=correct, **p)
    return {"prompt": Content(text), "answer": quantity(total, "points"),
            "answer_display": Content("{} points".format(total))}


def solve_quiz(p, sympy):
    scores = [p["right_points"]] * p["right"] + [-p["wrong_points"]] * p["wrong"]
    return quantity(sum(sympy.Integer(s) for s in scores), "points")


# ---------------------------------------------------- L4: mean temperature

def build_mean(rng):
    mean = rng.randint(-8, 3)
    temps = [rng.randint(TEMPERATURE_LOW, TEMPERATURE_HIGH) for _ in range(4)]
    temps.append(5 * mean - sum(temps))
    return {"context": "mean_temps", "place": rng.choice(PLACES), "temps": temps}


def temperature_list(values):
    shown = [degrees(v) for v in values]
    return ", ".join(shown[:-1]) + " and " + shown[-1]


def check_mean(p):
    temps = p["temps"]
    require(p["place"] in PLACES, "Unknown place")
    require(isinstance(temps, list) and len(temps) == 5
            and all(type(t) is int and TEMPERATURE_LOW <= t <= TEMPERATURE_HIGH for t in temps),
            "Five temperatures within bounds")
    require(sum(1 for t in temps if t < 0) >= 2, "At least two negative temperatures")
    return whole(Fraction(sum(temps), 5), -15, 10, "The mean must be whole")


def parts_mean(p):
    mean = check_mean(p)
    text = ("The midnight temperatures in {} on five nights were {}. "
            "Work out the mean temperature.").format(p["place"], temperature_list(p["temps"]))
    return {"prompt": Content(text), "answer": temperature_answer(mean),
            "answer_display": Content(degrees(mean))}


def solve_mean(p, sympy):
    m = sympy.Symbol("m")
    (mean,) = sympy_solve(sympy, [sympy.Eq(5 * m, sum(p["temps"]))], [m])
    return temperature_answer(mean)


# -------------------------------------------------- L4: missing temperature

def build_missing(rng):
    mean = rng.randint(-8, 3)
    known = [rng.randint(TEMPERATURE_LOW, TEMPERATURE_HIGH) for _ in range(3)]
    return {"context": "missing_temp", "mean": mean, "known": known}


def check_missing(p):
    integers(p, "mean")
    known = p["known"]
    require(isinstance(known, list) and len(known) == 3
            and all(type(t) is int and TEMPERATURE_LOW <= t <= TEMPERATURE_HIGH for t in known),
            "Three temperatures within bounds")
    require(-8 <= p["mean"] <= 3, "Mean bounds")
    fourth = 4 * p["mean"] - sum(known)
    require(-20 <= fourth <= 15, "Fourth temperature outside bounds")
    require(sum(1 for t in known + [fourth] if t < 0) >= 2, "Keep it about negatives")
    return fourth


def parts_missing(p):
    fourth = check_missing(p)
    text = ("The mean of four temperatures is {}. Three of the temperatures are {}. "
            "What is the fourth temperature?").format(degrees(p["mean"]),
                                                     temperature_list(p["known"]))
    return {"prompt": Content(text), "answer": temperature_answer(fourth),
            "answer_display": Content(degrees(fourth))}


def solve_missing(p, sympy):
    t = sympy.Symbol("t")
    (fourth,) = sympy_solve(sympy, [sympy.Eq((sum(p["known"]) + t) / 4, p["mean"])], [t])
    return temperature_answer(fourth)


# ------------------------------------------------------------ registry

CONTEXTS = {
    "temperature_change": Context(1, frozenset({"context", "place", "times", "start", "change"}),
                                  build_change, check_change, parts_change, solve_change),
    "temperature_difference": Context(2, frozenset({"context", "place_a", "place_b", "a", "b"}),
                                      build_difference, check_difference, parts_difference,
                                      solve_difference),
    "bank": Context(2, frozenset({"context", "name", "balance", "bill"}),
                    build_bank, check_bank, parts_bank, solve_bank),
    "falling": Context(3, frozenset({"context", "place", "start", "rate", "hours"}),
                       build_falling, check_falling, parts_falling, solve_falling),
    "quiz": Context(3, frozenset({"context", "name", "right_points", "wrong_points",
                                  "right", "wrong"}),
                    build_quiz, check_quiz, parts_quiz, solve_quiz),
    "mean_temps": Context(4, frozenset({"context", "place", "temps"}),
                          build_mean, check_mean, parts_mean, solve_mean),
    "missing_temp": Context(4, frozenset({"context", "mean", "known"}),
                            build_missing, check_missing, parts_missing, solve_missing),
}


def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    import sympy
    expected = CONTEXTS[q.parameters["context"]].solve(q.parameters, sympy)
    require(expected == q.answer, "Independent negative-number calculation disagrees")
    return True