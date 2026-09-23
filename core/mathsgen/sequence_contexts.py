"""Worded arithmetic-sequence problems, mixed with the existing bare nth terms.

L1 translates equal rows into bn. L2 finds bn+c from a first term and
constant increase. L3 infers a decreasing rule from two readings. L4
infers a fare from two balances, finds the first threshold crossing, then
calculates the remaining balance. All money and readings are exact.
"""
from .core import Content, rational_text, require
from . import worded
from .worded import Context, integers, pounds

# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {1: 0.35, 2: 0.40, 3: 0.50, 4: 0.60}
MARKS = {1: 2, 2: 3, 3: 4, 4: 5}
WORKING_LINES = {1: 4, 2: 5, 3: 7, 4: 9}
FARES_PENCE = (50, 150, 250)


def polynomial_answer(slope, constant=0):
    return {"kind": "polynomial", "variable": "n",
            "coefficients_descending": [
                "0", rational_text(slope), rational_text(constant)]}


def polynomial_parts(text, slope, constant=0):
    from .nth_term import expression
    coefficients = polynomial_answer(slope, constant)["coefficients_descending"]
    return {"prompt": Content(text),
            "answer": polynomial_answer(slope, constant),
            "answer_display": Content(expression(coefficients),
                                      expression(coefficients, True))}


# ------------------------------------------------------------ level 1: rows

def build_rows(rng):
    return {"context": "chair_rows", "chairs": rng.randint(2, 9)}


def check_rows(p):
    integers(p, "chairs")
    require(2 <= p["chairs"] <= 9, "Chairs per row outside bounds")
    return p["chairs"]


def parts_rows(p):
    chairs = check_rows(p)
    return polynomial_parts(
        "A hall has n identical rows of chairs, with {} chairs in each row. "
        "Write an expression for the total number of chairs.".format(chairs),
        chairs)


def solve_rows(p, sympy):
    n = sympy.Symbol("n")
    formula = sympy.expand(sum(sympy.Integer(p["chairs"])
                               for _ in range(1)) * n)
    return polynomial_answer(formula.coeff(n), formula.subs(n, 0))


# ----------------------------------------------------- level 2: linked tables

def build_tables(rng):
    increase = rng.randint(2, 6)
    end_seats = rng.randint(2, 5)
    return {"context": "linked_tables",
            "first": increase + end_seats, "increase": increase}


def check_tables(p):
    integers(p, "first increase")
    require(2 <= p["increase"] <= 6, "Increase outside bounds")
    require(2 <= p["first"] - p["increase"] <= 5,
            "First table must add end seats")
    return p["increase"], p["first"] - p["increase"]


def parts_tables(p):
    slope, constant = check_tables(p)
    return polynomial_parts(
        "One table seats {} people. When tables are joined in a line, "
        "each extra table provides {} more seats. Write an expression "
        "for the number of seats with n tables.".format(
            p["first"], p["increase"]), slope, constant)


def solve_tables(p, sympy):
    n = sympy.Symbol("n")
    total = sympy.expand(p["first"] + (n - 1) * p["increase"])
    return polynomial_answer(total.coeff(n), total.subs(n, 0))


# ----------------------------------------- level 3: infer a decreasing rule

def build_readings(rng):
    start = rng.randint(70, 100)
    loss = rng.randint(2, 8)
    return {"context": "battery_readings",
            "after_two": start - 2 * loss,
            "after_five": start - 5 * loss}


def check_readings(p):
    integers(p, "after_two after_five")
    difference = p["after_two"] - p["after_five"]
    require(difference > 0 and difference % 3 == 0,
            "Readings must give a whole hourly loss")
    loss = difference // 3
    start = p["after_two"] + 2 * loss
    require(2 <= loss <= 8 and 70 <= start <= 100
            and p["after_five"] > 0, "Battery bounds")
    return -loss, start


def parts_readings(p):
    slope, start = check_readings(p)
    return polynomial_parts(
        "A battery loses the same percentage points of charge each hour. "
        "After 2 hours its charge is {}%; after 5 hours it is {}%. "
        "Write an expression for its percentage charge after n hours.".format(
            p["after_two"], p["after_five"]), slope, start)


def solve_readings(p, sympy):
    start, loss = sympy.symbols("start loss")
    solutions = sympy.solve(
        [start - 2 * loss - p["after_two"],
         start - 5 * loss - p["after_five"]],
        (start, loss), dict=True)
    require(len(solutions) == 1, "Readings do not define one rule")
    return polynomial_answer(-solutions[0][loss], solutions[0][start])


# ---------------------------- level 4: infer a fare, then use the balance

def build_travel_card(rng):
    start = 100 * rng.randint(25, 70)
    fare = rng.choice(FARES_PENCE)
    trip = rng.randint(6, 14)
    return {"context": "travel_card",
            "after_two": start - 2 * fare,
            "after_five": start - 5 * fare,
            "threshold_pence": start - (trip - 1) * fare}


def check_travel_card(p):
    integers(p, "after_two after_five threshold_pence")
    difference = p["after_two"] - p["after_five"]
    require(difference > 0 and difference % 3 == 0,
            "Balances must give a whole-pence fare")
    fare = difference // 3
    start = p["after_two"] + 2 * fare
    require(fare in FARES_PENCE and 2500 <= start <= 7000
            and start % 100 == 0 and p["after_five"] > 0,
            "Travel card or fare outside bounds")
    threshold = p["threshold_pence"]
    require(0 < threshold < start, "Threshold outside bounds")
    for trip in range(1, 31):
        remaining = start - trip * fare
        if remaining < threshold:
            require(6 <= trip <= 14 and remaining > 0,
                    "Crossing outside useful trip range")
            return trip, remaining
    raise ValueError("Threshold never crossed")


def travel_answer(trip, remaining):
    return {"kind": "trip_balance", "trip": int(trip),
            "pence": int(remaining)}


def parts_travel_card(p):
    trip, remaining = check_travel_card(p)
    prompt = (
        "A prepaid travel card loses the same fare for every trip. Its "
        "balance is {} after 2 trips and {} after 5 trips. After which "
        "trip will its balance first be below {}, and what balance "
        "will remain then?"
    ).format(pounds(p["after_two"]), pounds(p["after_five"]),
             pounds(p["threshold_pence"]))
    return {"prompt": Content(prompt),
            "answer": travel_answer(trip, remaining),
            "answer_display": Content(
                "After trip {}, {} remains.".format(trip, pounds(remaining)))}


def solve_travel_card(p, sympy):
    start, fare = sympy.symbols("start fare")
    solutions = sympy.solve(
        [start - 2 * fare - p["after_two"],
         start - 5 * fare - p["after_five"]],
        (start, fare), dict=True)
    require(len(solutions) == 1, "Balances do not define one fare")
    start = solutions[0][start]
    fare = solutions[0][fare]
    threshold = sympy.Integer(p["threshold_pence"])
    for trip in range(1, 31):
        remaining = start - trip * fare
        if remaining < threshold:
            require(remaining.q == 1, "Balance is not whole pence")
            return travel_answer(trip, remaining)
    raise ValueError("Independent threshold was never crossed")


CONTEXTS = {
    "chair_rows": Context(1, {"context", "chairs"},
                          build_rows, check_rows, parts_rows, solve_rows),
    "linked_tables": Context(2, {"context", "first", "increase"},
                             build_tables, check_tables, parts_tables, solve_tables),
    "battery_readings": Context(
        3, {"context", "after_two", "after_five"},
        build_readings, check_readings, parts_readings, solve_readings),
    "travel_card": Context(
        4, {"context", "after_two", "after_five", "threshold_pence"},
        build_travel_card, check_travel_card, parts_travel_card, solve_travel_card),
}


def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, question):
    return worded.validate(generator, question, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(question):
    import sympy
    p = question.parameters
    require(p.get("context") in CONTEXTS, "Unknown sequence context")
    expected = CONTEXTS[p["context"]].solve(p, sympy)
    require(question.answer == expected,
            "Independent sequence story disagrees")
    return True