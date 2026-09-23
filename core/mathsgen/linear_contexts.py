"""Worded contexts for algebra.linear.two_sided.

Levels 1, 3 and 4 mix these with the bare equations. The student forms a
linear equation from the story, solves it and, at level 4, uses the
solution to answer a follow-up question.

Every context is built backwards from a chosen whole-number solution, then
checked forwards: check() solves the story's equation with exact Fractions
using only the displayed numbers. validate_independently() solves it again
with SymPy from separately written story relationships.

Each context supplies:
    build(rng)          -> JSON-compatible parameters (may break the rules;
                           generation retries until check() accepts them)
    check(p)            -> the whole-number solution, or raises ValueError
    parts(p)            -> dict(prompt, answer, answer_display)
    solve(p, sympy)     -> the final answer, computed independently
"""
from fractions import Fraction

from .core import Content, rational_text, require
from . import rich_blocks as rb
from . import worded
from .worded import Context


# ------------------------------------------------------------ editable knobs

# Chance that a question at each level is worded rather than a bare equation.
CONTEXT_SHARE = {1: 0.35, 2: 0.0, 3: 0.5, 4: 0.6}

MARKS = {1: 3, 3: 4, 4: 5}
WORKING_LINES = {1: 6, 3: 8, 4: 9}

NAMES = (
    "Amir", "Beth", "Chloe", "Dev", "Ella", "Finn", "Grace", "Hassan",
    "Isla", "Jay", "Kofi", "Lena", "Maya", "Noah", "Omar", "Priya",
    "Rosa", "Sam", "Tariq", "Zara",
)

# service: (group noun, unit, plural unit, firm names)
SERVICES = {
    "taxi": ("taxi firms", "mile", "miles", ("Swift Cabs", "City Taxis", "Metro Cars")),
    "plumber": ("plumbers", "hour", "hours", ("PipeRight", "Flow Fix", "Tapworks")),
    "bike": ("bike hire shops", "day", "days", ("Pedal Hire", "Cycle Stop", "Spoke and Go")),
    "gym": ("gyms", "month", "months", ("FitZone", "Core Gym", "Pulse Fitness")),
    "van": ("van hire companies", "day", "days", ("MoveIt Vans", "Road Ready", "Van Direct")),
}

POLYGONS = {
    3: "equilateral triangle", 4: "square",
    5: "regular pentagon", 6: "regular hexagon",
}

TRIANGLES = ("ABC", "DEF", "LMN", "PQR", "XYZ")

AGE_ASKS = ("older_now", "younger_then", "total_now")


# ------------------------------------------------------------ small helpers

def context_share(level):
    return CONTEXT_SHARE.get(level, 0.0)


def integers(p, names):
    for name in names.split():
        require(type(p[name]) is int, "Expected an integer " + name)


def whole(value, low, high, message):
    """Require an exact whole number within bounds and return it as int."""
    require(value.denominator == 1 and low <= value <= high, message)
    return int(value)


def money(pence):
    pounds, rest = divmod(pence, 100)
    if rest == 0:
        return "£{}".format(pounds)
    return "£{}.{:02d}".format(pounds, rest)


def times(k):
    return "twice" if k == 2 else "{} times".format(k)


def article(noun):
    return ("an " if noun[0] in "aeiou" else "a ") + noun


def bracketed(coefficient, constant):
    """A bracketed linear expression as a (tex, plain) maths piece.

    Integer coefficients format identically in TeX and plain text.
    """
    from .linear_two_sided import linear_expression
    plain = "(" + linear_expression(coefficient, constant) + ")"
    return (plain, plain)


def rich_prompt(*sentences):
    """Each sentence is a sequence of prose strings and (tex, plain) pieces."""
    blocks, plain = [], []
    for pieces in sentences:
        runs, words = [], []
        for piece in pieces:
            if isinstance(piece, str):
                runs.append(rb.text(piece))
                words.append(piece)
            else:
                tex, fallback = piece
                runs.append(rb.maths(tex, fallback))
                words.append(fallback)
        blocks.append(rb.paragraph(*runs))
        plain.append("".join(words))
    return Content(" ".join(plain), blocks=tuple(blocks))


def quantity(value, unit):
    return {"kind": "quantity", "value": rational_text(value), "unit": unit}


def single_solution(sympy, equation, symbol):
    solutions = sympy.solve(equation, symbol)
    require(len(solutions) == 1, "Story equation must have exactly one solution")
    return solutions[0]


# ------------------------------------------------ level 1: think of a number

def build_think_number(rng):
    b = rng.randint(1, 5)
    a = b + rng.randint(1, 6)
    number = rng.randint(2, 12)
    c = rng.randint(1, 15)
    return {"context": "think_number", "a": a, "b": b, "c": c,
            "d": (a - b) * number + c}


def check_think_number(p):
    integers(p, "a b c d")
    require(1 <= p["b"] < p["a"] <= 11, "Multiplier bounds")
    require(1 <= p["c"] <= 15, "Added constant bounds")
    return whole(Fraction(p["d"] - p["c"], p["a"] - p["b"]), 2, 12,
                 "Number outside bounds")


def parts_think_number(p):
    number = check_think_number(p)
    if p["b"] == 1:
        second = "I get the same answer if I add {} to my number.".format(p["d"])
    else:
        second = "I get the same answer if I multiply my number by {} and add {}.".format(
            p["b"], p["d"])
    text = "I think of a number. I multiply it by {} and add {}. {} What is my number?".format(
        p["a"], p["c"], second)
    return {
        "prompt": Content(text),
        "answer": quantity(number, ""),
        "answer_display": Content("The number is {}.".format(number)),
    }


def solve_think_number(p, sympy):
    n = sympy.Symbol("n")
    right = n + p["d"] if p["b"] == 1 else p["b"] * n + p["d"]
    return single_solution(sympy, sympy.Eq(p["a"] * n + p["c"], right), n)


# ------------------------------------------------------- level 3: tariffs

def build_tariffs(rng):
    service = rng.choice(sorted(SERVICES))
    first, second = rng.sample(SERVICES[service][3], 2)
    count = rng.randint(3, 20)
    rate_low = 50 * rng.randint(1, 10)
    rate_high = rate_low + 50 * rng.randint(1, 6)
    fixed_low = 50 * rng.randint(2, 30)
    fixed_high = fixed_low + (rate_high - rate_low) * count
    offers = [(fixed_low, rate_high), (fixed_high, rate_low)]
    rng.shuffle(offers)
    return {"context": "tariffs", "service": service, "first": first, "second": second,
            "fixed_a": offers[0][0], "rate_a": offers[0][1],
            "fixed_b": offers[1][0], "rate_b": offers[1][1]}


def check_tariffs(p):
    integers(p, "fixed_a rate_a fixed_b rate_b")
    require(p["service"] in SERVICES, "Unknown service")
    firms = SERVICES[p["service"]][3]
    require(p["first"] in firms and p["second"] in firms
            and p["first"] != p["second"], "Firm names")
    for key in ("fixed_a", "rate_a", "fixed_b", "rate_b"):
        require(p[key] > 0 and p[key] % 50 == 0, "Money must be a positive multiple of 50p")
    require(max(p["fixed_a"], p["fixed_b"]) <= 10000, "Fixed charge bounds")
    require(max(p["rate_a"], p["rate_b"]) <= 1000, "Rate bounds")
    require(p["rate_a"] != p["rate_b"], "Rates must differ")
    return whole(Fraction(p["fixed_b"] - p["fixed_a"], p["rate_a"] - p["rate_b"]), 3, 20,
                 "Break-even count outside bounds")


def parts_tariffs(p):
    count = check_tariffs(p)
    group, unit, units, _ = SERVICES[p["service"]]
    text = ("{} charges {} plus {} per {}. {} charges {} plus {} per {}. "
            "For how many {} do the two {} charge the same amount?").format(
        p["first"], money(p["fixed_a"]), money(p["rate_a"]), unit,
        p["second"], money(p["fixed_b"]), money(p["rate_b"]), unit,
        units, group)
    return {
        "prompt": Content(text),
        "answer": quantity(count, units),
        "answer_display": Content("{} {}".format(count, units)),
    }


def solve_tariffs(p, sympy):
    n = sympy.Symbol("n")
    cost_a = p["fixed_a"] + p["rate_a"] * n
    cost_b = p["fixed_b"] + p["rate_b"] * n
    return single_solution(sympy, sympy.Eq(cost_a, cost_b), n)


# ------------------------------------------------------- level 3: savings

def build_savings(rng):
    first, second = rng.sample(NAMES, 2)
    weeks = rng.randint(3, 20)
    weekly_a = rng.randint(2, 15)
    if rng.random() < 0.5:
        weekly_b = rng.randint(1, weekly_a - 1)
    else:
        weekly_b = -rng.randint(2, 12)
    start_a = 5 * rng.randint(1, 12)
    start_b = start_a + (weekly_a - weekly_b) * weeks
    return {"context": "savings", "first": first, "second": second,
            "start_a": start_a, "weekly_a": weekly_a,
            "start_b": start_b, "weekly_b": weekly_b}


def check_savings(p):
    integers(p, "start_a weekly_a start_b weekly_b")
    require(p["first"] in NAMES and p["second"] in NAMES
            and p["first"] != p["second"], "Names")
    require(5 <= p["start_a"] <= 60 and p["start_b"] <= 700, "Starting amounts")
    require(2 <= p["weekly_a"] <= 15, "First weekly amount")
    require(p["weekly_b"] != 0 and -12 <= p["weekly_b"] < p["weekly_a"],
            "Second weekly amount")
    return whole(Fraction(p["start_b"] - p["start_a"], p["weekly_a"] - p["weekly_b"]),
                 3, 20, "Weeks outside bounds")


def parts_savings(p):
    weeks = check_savings(p)
    if p["weekly_b"] > 0:
        action = "adds £{} each week".format(p["weekly_b"])
    else:
        action = "spends £{} each week".format(-p["weekly_b"])
    text = ("{} has £{} saved and adds £{} each week. {} has £{} saved and {}. "
            "After how many weeks will {} and {} have the same amount of money?").format(
        p["first"], p["start_a"], p["weekly_a"],
        p["second"], p["start_b"], action,
        p["first"], p["second"])
    return {
        "prompt": Content(text),
        "answer": quantity(weeks, "weeks"),
        "answer_display": Content("{} weeks".format(weeks)),
    }


def solve_savings(p, sympy):
    w = sympy.Symbol("w")
    balance_a = p["start_a"] + p["weekly_a"] * w
    balance_b = p["start_b"] + p["weekly_b"] * w
    return single_solution(sympy, sympy.Eq(balance_a, balance_b), w)


# ------------------------- levels 3 and 4: rectangle and regular polygon

POLYGON_KEYS = frozenset({"context", "a", "c", "width", "sides", "b", "e"})


def build_polygon(rng, name):
    x = rng.randint(2, 10)
    a = rng.randint(2, 6)
    c = rng.choice([v for v in range(-3, 10) if v != 0])
    width = rng.randint(2, 15)
    sides = rng.choice(sorted(POLYGONS))
    b = rng.randint(1, 4)
    total = 2 * (a * x + c) + 2 * width
    e = total // sides - b * x if total % sides == 0 else 0
    return {"context": name, "a": a, "c": c, "width": width,
            "sides": sides, "b": b, "e": e}


def check_polygon(p):
    integers(p, "a c width sides b e")
    require(2 <= p["a"] <= 6 and 1 <= p["b"] <= 4, "Coefficient bounds")
    require(-3 <= p["c"] <= 9 and p["c"] != 0, "Rectangle constant bounds")
    require(2 <= p["width"] <= 15 and 1 <= p["e"] <= 15, "Length bounds")
    require(p["sides"] in POLYGONS, "Unknown polygon")
    require(2 * p["a"] != p["sides"] * p["b"], "Perimeters must not be parallel")
    x = whole(Fraction(p["sides"] * p["e"] - 2 * p["c"] - 2 * p["width"],
                       2 * p["a"] - p["sides"] * p["b"]), 2, 10, "x outside bounds")
    length = p["a"] * x + p["c"]
    require(length >= 2 and length != p["width"], "Rectangle must be a genuine rectangle")
    return x


def polygon_prompt(p, ask):
    shape = POLYGONS[p["sides"]]
    return rich_prompt(
        ("A rectangle has length ", bracketed(p["a"], p["c"]),
         " cm and width {} cm.".format(p["width"])),
        (article(shape).capitalize() + " has sides of length ",
         bracketed(p["b"], p["e"]), " cm."),
        ("The rectangle and the {} have the same perimeter.".format(shape),),
        ask,
    )


def parts_polygon_perimeter(p):
    x = check_polygon(p)
    return {
        "prompt": polygon_prompt(p, ("Work out the value of ", ("x", "x"), ".")),
        "answer": {"kind": "variable_values", "values": {"x": str(x)}},
        "answer_display": Content("x = {}".format(x), "x = {}".format(x)),
    }


def parts_rectangle_area(p):
    x = check_polygon(p)
    area = (p["a"] * x + p["c"]) * p["width"]
    return {
        "prompt": polygon_prompt(p, ("Work out the area of the rectangle.",)),
        "answer": quantity(area, "cm²"),
        "answer_display": Content("x = {}, so the area is {} cm².".format(x, area)),
    }


def polygon_x(p, sympy):
    x = sympy.Symbol("x")
    length = p["a"] * x + p["c"]
    rectangle = sum([length, p["width"], length, p["width"]])
    polygon = sum([p["b"] * x + p["e"]] * p["sides"])
    return x, length, single_solution(sympy, sympy.Eq(rectangle, polygon), x)


def solve_polygon_perimeter(p, sympy):
    return polygon_x(p, sympy)[2]


def solve_rectangle_area(p, sympy):
    x, length, value = polygon_x(p, sympy)
    return length.subs(x, value) * p["width"]


# ------------------------------------------ level 4: isosceles perimeter

def build_isosceles(rng):
    x = rng.randint(2, 10)
    a, b = rng.sample(range(1, 8), 2)
    c = rng.choice([v for v in range(-5, 13) if v != 0])
    return {"context": "isosceles_perimeter", "letters": rng.choice(TRIANGLES),
            "a": a, "c": c, "b": b, "d": (a - b) * x + c,
            "e": rng.randint(1, 5), "f": rng.randint(-5, 12)}


def check_isosceles(p):
    integers(p, "a c b d e f")
    require(p["letters"] in TRIANGLES, "Unknown triangle labels")
    require(1 <= p["a"] <= 7 and 1 <= p["b"] <= 7 and p["a"] != p["b"],
            "Equal-side coefficients")
    require(-5 <= p["c"] <= 12 and p["c"] != 0 and abs(p["d"]) <= 60,
            "Equal-side constants")
    require(1 <= p["e"] <= 5 and -5 <= p["f"] <= 12, "Base bounds")
    x = whole(Fraction(p["d"] - p["c"], p["a"] - p["b"]), 2, 10, "x outside bounds")
    equal = p["a"] * x + p["c"]
    base = p["e"] * x + p["f"]
    require(equal >= 2 and base >= 2, "Side lengths must be positive")
    require(base != equal, "Triangle must not be equilateral")
    require(base < 2 * equal, "Triangle inequality")
    return x


def parts_isosceles(p):
    x = check_isosceles(p)
    apex, left, right = p["letters"]
    first, second, base = apex + left, apex + right, left + right
    perimeter = 2 * (p["a"] * x + p["c"]) + p["e"] * x + p["f"]
    prompt = rich_prompt(
        ("Triangle {} is isosceles with {} = {}.".format(p["letters"], first, second),),
        ("{} = ".format(first), bracketed(p["a"], p["c"]),
         " cm, {} = ".format(second), bracketed(p["b"], p["d"]),
         " cm and {} = ".format(base), bracketed(p["e"], p["f"]), " cm."),
        ("Work out the perimeter of triangle {}.".format(p["letters"]),),
    )
    return {
        "prompt": prompt,
        "answer": quantity(perimeter, "cm"),
        "answer_display": Content("x = {}, so the perimeter is {} cm.".format(x, perimeter)),
    }


def solve_isosceles(p, sympy):
    x = sympy.Symbol("x")
    first = p["a"] * x + p["c"]
    second = p["b"] * x + p["d"]
    base = p["e"] * x + p["f"]
    value = single_solution(sympy, sympy.Eq(first, second), x)
    return (first + second + base).subs(x, value)


# ------------------------------------------------------------ level 4: ages

def build_ages(rng):
    younger_age = rng.randint(3, 15)
    direction = rng.choice(("future", "past"))
    if direction == "future":
        k = rng.randint(3, 7)
        m = rng.randint(2, k - 1)
        top, bottom = younger_age * (k - m), m - 1
    else:
        k = rng.randint(2, 6)
        m = rng.randint(k + 1, 9)
        top, bottom = younger_age * (m - k), m - 1
    older, younger = rng.sample(NAMES, 2)
    return {"context": "ages", "older": older, "younger": younger,
            "k": k, "m": m, "n": top // bottom if top % bottom == 0 else 0,
            "direction": direction, "ask": rng.choice(AGE_ASKS)}


def check_ages(p):
    integers(p, "k m n")
    require(p["older"] in NAMES and p["younger"] in NAMES
            and p["older"] != p["younger"], "Names")
    require(p["direction"] in ("future", "past"), "Unknown direction")
    require(p["ask"] in AGE_ASKS, "Unknown question")
    require(2 <= p["k"] <= 7 and 2 <= p["m"] <= 9 and p["k"] != p["m"], "Multiples")
    require(2 <= p["n"] <= 40, "Years bounds")
    sign = 1 if p["direction"] == "future" else -1
    younger_age = whole(Fraction(sign * p["n"] * (p["m"] - 1), p["k"] - p["m"]), 2, 20,
                        "Younger age outside bounds")
    require(p["k"] * younger_age <= 95, "Older age outside bounds")
    require(younger_age + sign * p["n"] >= 1, "Younger person must be born by then")
    return younger_age


def age_answer(p, younger_age):
    sign = 1 if p["direction"] == "future" else -1
    return {
        "older_now": p["k"] * younger_age,
        "younger_then": younger_age + sign * p["n"],
        "total_now": (p["k"] + 1) * younger_age,
    }[p["ask"]]


def parts_ages(p):
    younger_age = check_ages(p)
    older, younger, n = p["older"], p["younger"], p["n"]
    first = "{} is {} as old as {}.".format(older, times(p["k"]), younger)
    if p["direction"] == "future":
        second = "In {} years' time, {} will be {} as old as {}.".format(
            n, older, times(p["m"]), younger)
        then_question = "How old will {} be in {} years' time?".format(younger, n)
    else:
        second = "{} years ago, {} was {} as old as {}.".format(
            n, older, times(p["m"]), younger)
        then_question = "How old was {} {} years ago?".format(younger, n)
    question = {
        "older_now": "How old is {} now?".format(older),
        "younger_then": then_question,
        "total_now": "What is the total of their ages now?",
    }[p["ask"]]
    value = age_answer(p, younger_age)
    if p["ask"] == "older_now":
        shown = "{} is {} now, so {} is {}.".format(younger, younger_age, older, value)
    elif p["ask"] == "younger_then" and p["direction"] == "future":
        shown = "{} is {} now, so in {} years' time {} will be {}.".format(
            younger, younger_age, n, younger, value)
    elif p["ask"] == "younger_then":
        shown = "{} is {} now, so {} years ago {} was {}.".format(
            younger, younger_age, n, younger, value)
    else:
        shown = "{} is {} and {} is {}, so the total is {}.".format(
            younger, younger_age, older, p["k"] * younger_age, value)
    return {
        "prompt": Content(" ".join((first, second, question))),
        "answer": quantity(value, "years"),
        "answer_display": Content(shown),
    }


def solve_ages(p, sympy):
    y = sympy.Symbol("y")
    shift = p["n"] if p["direction"] == "future" else -p["n"]
    older_then = p["k"] * y + shift
    younger_then = y + shift
    value = single_solution(sympy, sympy.Eq(older_then, p["m"] * younger_then), y)
    return {
        "older_now": p["k"] * value,
        "younger_then": value + shift,
        "total_now": p["k"] * value + value,
    }[p["ask"]]


# ------------------------------------------------------------ registry

CONTEXTS = {
    "think_number": Context(
        1, frozenset({"context", "a", "b", "c", "d"}),
        build_think_number, check_think_number, parts_think_number, solve_think_number),
    "tariffs": Context(
        3, frozenset({"context", "service", "first", "second",
                      "fixed_a", "rate_a", "fixed_b", "rate_b"}),
        build_tariffs, check_tariffs, parts_tariffs, solve_tariffs),
    "savings": Context(
        3, frozenset({"context", "first", "second",
                      "start_a", "weekly_a", "start_b", "weekly_b"}),
        build_savings, check_savings, parts_savings, solve_savings),
    "polygon_perimeter": Context(
        3, POLYGON_KEYS, lambda rng: build_polygon(rng, "polygon_perimeter"),
        check_polygon, parts_polygon_perimeter, solve_polygon_perimeter),
    "isosceles_perimeter": Context(
        4, frozenset({"context", "letters", "a", "c", "b", "d", "e", "f"}),
        build_isosceles, check_isosceles, parts_isosceles, solve_isosceles),
    "rectangle_area": Context(
        4, POLYGON_KEYS, lambda rng: build_polygon(rng, "rectangle_area"),
        check_polygon, parts_rectangle_area, solve_rectangle_area),
    "ages": Context(
        4, frozenset({"context", "older", "younger", "k", "m", "n",
                      "direction", "ask"}),
        build_ages, check_ages, parts_ages, solve_ages),
}


# ------------------------------------------------ generate and validate

def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    import sympy
    p = q.parameters
    expected = CONTEXTS[p["context"]].solve(p, sympy)
    if q.answer["kind"] == "variable_values":
        shown = q.answer["values"]["x"]
    else:
        shown = q.answer["value"]
    require(sympy.Rational(shown) == expected, "Independent story solution disagrees")
    return True