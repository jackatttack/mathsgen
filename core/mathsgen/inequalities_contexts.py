"""Worded contexts for algebra.inequalities.linear.

Level 1: the greatest whole number within a budget.
Level 2: the least whole number that first exceeds a target.
Level 3: a decreasing quantity first crossing a threshold, so forming
         start - rate * t < threshold forces the direction to reverse.
Level 4: a double inequality from a context; list the whole-number values.

check() works from exact Fraction bounds with floor and ceil.
solve(p, sympy) is independent: it enumerates candidate whole numbers and
tests each directly against the story, returning the full expected answer.
"""
from fractions import Fraction
from math import ceil, floor

from .core import Content, rational_text, require
from . import worded
from .worded import Context, rich_prompt


# ------------------------------------------------------------ editable knobs

# Chance that a question at each level is worded rather than bare.
CONTEXT_SHARE = {1: 0.3, 2: 0.4, 3: 0.5, 4: 0.5}

MARKS = {1: 3, 2: 3, 3: 3, 4: 4}
WORKING_LINES = {1: 4, 2: 4, 3: 5, 4: 6}

NAMES = (
    "Amir", "Beth", "Chloe", "Dev", "Ella", "Finn", "Grace", "Hassan",
    "Isla", "Jay", "Kofi", "Lena", "Maya", "Noah", "Omar", "Priya",
)

# purchase: (costs sentence, question, unit)
PURCHASES = {
    "concert": ("Tickets for a concert cost £{price} each, plus a booking fee of £{fee}.",
                "What is the greatest number of tickets {name} can buy?", "tickets"),
    "plants": ("Plant pots cost £{price} each, plus a delivery charge of £{fee}.",
               "What is the greatest number of plant pots {name} can buy?", "plant pots"),
    "taxi": ("A taxi charges £{price} per mile, plus a fixed fee of £{fee}.",
             "What is the greatest whole number of miles {name} can travel?", "miles"),
    "lessons": ("Swimming lessons cost £{price} each, plus a joining fee of £{fee}.",
                "What is the greatest number of lessons {name} can pay for?", "lessons"),
}

# story: (situation, question, unit)
EXCEEDS = {
    "phone": ("A phone contract costs £{fee} to set up and £{rate} per month.",
              "After how many whole months will the total cost first be more than £{target}?",
              "months"),
    "savings": ("{name} has £{fee} and saves £{rate} each week.",
                "After how many whole weeks will {name} first have more than £{target}?",
                "weeks"),
    "gym": ("A gym charges a £{fee} joining fee and £{rate} per visit.",
            "What is the least number of visits for which the total cost is more than £{target}?",
            "visits"),
}

# story: (situation, question, unit, start range, rate range, threshold range)
FALLING = {
    "battery": ("A phone battery is at {start}% and loses {rate}% every hour.",
                "After how many whole hours will the battery first be below {threshold}%?",
                "hours", (40, 100), (3, 15), (5, 30)),
    "tank": ("A tank holds {start} litres of water and drains at {rate} litres per minute.",
             "After how many whole minutes will the tank first hold less than {threshold} litres?",
             "minutes", (100, 900), (5, 40), (10, 200)),
    "candle": ("A candle is {start} mm tall and burns down by {rate} mm every hour.",
               "After how many whole hours will the candle first be shorter than {threshold} mm?",
               "hours", (100, 300), (4, 20), (10, 60)),
}

LOWER_WORDS = {"<": "more than", "<=": "at least"}
UPPER_WORDS = {"<": "less than", "<=": "at most"}


# ------------------------------------------------------------ helpers

def integers(p, names):
    for name in names.split():
        require(type(p[name]) is int, "Expected an integer " + name)


def quantity(value, unit):
    return {"kind": "quantity", "value": rational_text(value), "unit": unit}


def within(value, bounds, message):
    require(bounds[0] <= value <= bounds[1], message)


def holds(lower, lower_op, value, upper_op, upper):
    above = lower < value if lower_op == "<" else lower <= value
    below = value < upper if upper_op == "<" else value <= upper
    return above and below


# ------------------------------------------------------- level 1: budget

def build_budget(rng):
    price, fee = rng.randint(2, 20), rng.randint(1, 15)
    count = rng.randint(2, 25)
    return {"context": "budget", "purchase": rng.choice(sorted(PURCHASES)),
            "name": rng.choice(NAMES), "price": price, "fee": fee,
            "budget": fee + price * count + rng.randint(0, price - 1)}


def check_budget(p):
    integers(p, "price fee budget")
    require(p["purchase"] in PURCHASES and p["name"] in NAMES, "Story choices")
    require(2 <= p["price"] <= 20 and 1 <= p["fee"] <= 15 and p["budget"] <= 600,
            "Money bounds")
    count = floor(Fraction(p["budget"] - p["fee"], p["price"]))
    require(2 <= count <= 25, "Answer outside bounds")
    return count


def parts_budget(p):
    count = check_budget(p)
    costs, question, unit = PURCHASES[p["purchase"]]
    text = " ".join((costs.format(**p), "{} has £{} to spend.".format(p["name"], p["budget"]),
                     question.format(**p)))
    return {"prompt": Content(text), "answer": quantity(count, unit),
            "answer_display": Content("{} {}".format(count, unit))}


def solve_budget(p, sympy):
    count = max(n for n in range(0, 300) if p["price"] * n + p["fee"] <= p["budget"])
    return quantity(count, PURCHASES[p["purchase"]][2])


# ------------------------------------------------------ level 2: exceeds

def build_exceeds(rng):
    rate, fee, count = rng.randint(2, 40), rng.randint(5, 100), rng.randint(2, 30)
    return {"context": "exceeds", "story": rng.choice(sorted(EXCEEDS)),
            "name": rng.choice(NAMES), "fee": fee, "rate": rate,
            "target": fee + rate * (count - 1) + rng.randint(0, rate - 1)}


def check_exceeds(p):
    integers(p, "fee rate target")
    require(p["story"] in EXCEEDS and p["name"] in NAMES, "Story choices")
    require(2 <= p["rate"] <= 40 and 5 <= p["fee"] <= 100, "Money bounds")
    require(p["fee"] < p["target"] <= 1500, "Target bounds")
    count = floor(Fraction(p["target"] - p["fee"], p["rate"])) + 1
    require(2 <= count <= 30, "Answer outside bounds")
    return count


def parts_exceeds(p):
    count = check_exceeds(p)
    situation, question, unit = EXCEEDS[p["story"]]
    text = situation.format(**p) + " " + question.format(**p)
    return {"prompt": Content(text), "answer": quantity(count, unit),
            "answer_display": Content("{} {}".format(count, unit))}


def solve_exceeds(p, sympy):
    count = next(n for n in range(0, 1000) if p["fee"] + p["rate"] * n > p["target"])
    return quantity(count, EXCEEDS[p["story"]][2])


# ------------------------------------------------------ level 3: falling

def build_falling(rng):
    story = rng.choice(sorted(FALLING))
    _, _, _, starts, rates, thresholds = FALLING[story]
    return {"context": "falling", "story": story,
            "start": rng.randint(*starts), "rate": rng.randint(*rates),
            "threshold": rng.randint(*thresholds)}


def check_falling(p):
    integers(p, "start rate threshold")
    require(p["story"] in FALLING, "Unknown story")
    _, _, _, starts, rates, thresholds = FALLING[p["story"]]
    within(p["start"], starts, "Start outside bounds")
    within(p["rate"], rates, "Rate outside bounds")
    within(p["threshold"], thresholds, "Threshold outside bounds")
    require(p["threshold"] < p["start"], "Must start above the threshold")
    count = floor(Fraction(p["start"] - p["threshold"], p["rate"])) + 1
    require(2 <= count <= 40, "Answer outside bounds")
    return count


def parts_falling(p):
    count = check_falling(p)
    situation, question, unit = FALLING[p["story"]][:3]
    text = situation.format(**p) + " " + question.format(**p)
    return {"prompt": Content(text), "answer": quantity(count, unit),
            "answer_display": Content("{} {}".format(count, unit))}


def solve_falling(p, sympy):
    count = next(t for t in range(0, 1000) if p["start"] - p["rate"] * t < p["threshold"])
    return quantity(count, FALLING[p["story"]][2])


# ------------------------------------------------ level 4: double contexts

DOUBLE_OPS = ("<", "<=")


def whole_values_between(coefficient, constant, p):
    """Whole numbers v with lower (op) coefficient * v + constant (op) upper."""
    low = Fraction(p["lower"] - constant, coefficient)
    high = Fraction(p["upper"] - constant, coefficient)
    first = floor(low) + 1 if p["lower_op"] == "<" else ceil(low)
    last = ceil(high) - 1 if p["upper_op"] == "<" else floor(high)
    return list(range(first, last + 1))


def linear_rule(p):
    if p["context"] == "rectangle_double":
        return 4, 2 * p["a"]
    return p["k"], p["c"]


def build_double(rng, name):
    p = {"context": name}
    if name == "rectangle_double":
        p["a"] = rng.randint(1, 9)
    else:
        p["k"] = rng.randint(2, 6)
        p["c"] = rng.choice([v for v in range(-12, 13) if v != 0])
    coefficient, constant = linear_rule(p)
    first = rng.randint(2, 10)
    last = first + rng.randint(2, 5)
    p["lower_op"], p["upper_op"] = rng.choice(DOUBLE_OPS), rng.choice(DOUBLE_OPS)
    low_gap = (rng.randint(1, coefficient) if p["lower_op"] == "<"
               else rng.randint(0, coefficient - 1))
    high_gap = (rng.randint(1, coefficient) if p["upper_op"] == "<"
                else rng.randint(0, coefficient - 1))
    p["lower"] = coefficient * first + constant - low_gap
    p["upper"] = coefficient * last + constant + high_gap
    return p


def check_double(p):
    require(p["lower_op"] in DOUBLE_OPS and p["upper_op"] in DOUBLE_OPS, "Operators")
    integers(p, "lower upper")
    if p["context"] == "rectangle_double":
        integers(p, "a")
        require(1 <= p["a"] <= 9, "Length offset bounds")
    else:
        integers(p, "k c")
        require(2 <= p["k"] <= 6 and p["c"] != 0 and abs(p["c"]) <= 12, "Rule bounds")
    require(p["lower"] < p["upper"], "Reversed bounds")
    values = whole_values_between(*linear_rule(p), p)
    require(3 <= len(values) <= 6, "Unexpected number of solutions")
    require(values[0] >= 2, "The lower bound must do the work, not positivity")
    return values


def double_answer(variable, values):
    return {"kind": "integer_solutions", "variable": variable, "values": values}


def parts_double(p):
    values = check_double(p)
    bounds = "{} {} and {} {}".format(LOWER_WORDS[p["lower_op"]], p["lower"],
                                      UPPER_WORDS[p["upper_op"]], p["upper"])
    if p["context"] == "rectangle_double":
        variable = "x"
        length = "(x + {})".format(p["a"])
        prompt = rich_prompt(
            ("A rectangle has width ", ("x", "x"), " cm and length ", (length, length), " cm."),
            ("Its perimeter is {} cm.".format(bounds.replace(" and", " cm and")),),
            (("x", "x"), " is a whole number. List all the possible values of ",
             ("x", "x"), "."),
        )
    else:
        variable = "n"
        change = "added" if p["c"] > 0 else "subtracted"
        prompt = Content(
            "n is a whole number. When n is multiplied by {} and then {} is {}, "
            "the result is {}. List all the possible values of n.".format(
                p["k"], abs(p["c"]), change, bounds))
    return {"prompt": prompt, "answer": double_answer(variable, values),
            "answer_display": Content("{} = {}".format(
                variable, ", ".join(str(v) for v in values)))}


def solve_double(p, sympy):
    if p["context"] == "rectangle_double":
        rule, variable = (lambda x: x + (x + p["a"]) + x + (x + p["a"])), "x"
    else:
        rule, variable = (lambda n: p["k"] * n + p["c"]), "n"
    values = [v for v in range(1, 400)
              if holds(p["lower"], p["lower_op"], rule(v), p["upper_op"], p["upper"])]
    return double_answer(variable, values)


# ------------------------------------------------------------ registry

DOUBLE_BOUNDS = {"lower", "upper", "lower_op", "upper_op"}

CONTEXTS = {
    "budget": Context(
        1, frozenset({"context", "purchase", "name", "price", "fee", "budget"}),
        build_budget, check_budget, parts_budget, solve_budget),
    "exceeds": Context(
        2, frozenset({"context", "story", "name", "fee", "rate", "target"}),
        build_exceeds, check_exceeds, parts_exceeds, solve_exceeds),
    "falling": Context(
        3, frozenset({"context", "story", "start", "rate", "threshold"}),
        build_falling, check_falling, parts_falling, solve_falling),
    "rectangle_double": Context(
        4, frozenset({"context", "a"} | DOUBLE_BOUNDS),
        lambda rng: build_double(rng, "rectangle_double"),
        check_double, parts_double, solve_double),
    "number_double": Context(
        4, frozenset({"context", "k", "c"} | DOUBLE_BOUNDS),
        lambda rng: build_double(rng, "number_double"),
        check_double, parts_double, solve_double),
}


def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    expected = CONTEXTS[q.parameters["context"]].solve(q.parameters, None)
    require(expected == q.answer, "Independent enumeration disagrees")
    return True