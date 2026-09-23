"""Worded contexts for algebra.simultaneous.linear.

Level 1: matching coefficients (sum and difference, or a shop where one
item count matches). Level 2: a shop where one equation must be scaled.
Level 3: ticket prices (scale both) or a coin jar. Level 4: solve, then
use both values (a new basket, or a rectangle's perimeter or area).

Built backwards from chosen positive whole-number solutions, checked
forwards by Cramer's rule with exact Fractions from the displayed numbers,
and checked independently by SymPy from the story's own equations.
solve(p, sympy) returns the complete expected answer dict.
"""
from fractions import Fraction

from .core import Content, rational_text, require
from . import worded
from .worded import Context, article, rich_prompt, sentence_case
from .simultaneous_linear import COEFFICIENTS


# ------------------------------------------------------------ editable knobs

# Chance that a question at each level is worded rather than bare equations.
CONTEXT_SHARE = {1: 0.35, 2: 0.4, 3: 0.5, 4: 0.6}

MARKS = {1: 3, 2: 3, 3: 4, 4: 5}
WORKING_LINES = {1: 6, 2: 8, 3: 8, 4: 10}

# items: (singular x, plural x, singular y, plural y)
ITEMS = {
    "stationery": ("pen", "pens", "ruler", "rulers"),
    "cafe": ("tea", "teas", "coffee", "coffees"),
    "fruit": ("apple", "apples", "banana", "bananas"),
    "bakery": ("cupcake", "cupcakes", "cookie", "cookies"),
    "lunch": ("sandwich", "sandwiches", "drink", "drinks"),
    "school": ("notebook", "notebooks", "pencil", "pencils"),
}

TICKETS = ("adult ticket", "adult tickets", "child ticket", "child tickets")
VENUES = ("cinema", "zoo", "theme park", "museum", "theatre", "aquarium")

COINS = ((5, 10), (10, 20), (10, 50), (20, 50), (50, 100))

RECTANGLE_ASKS = ("perimeter", "area")


# ------------------------------------------------------------ helpers

def integers(p, names):
    for name in names.split():
        require(type(p[name]) is int, "Expected an integer " + name)


def whole(value, low, high, message):
    require(value.denominator == 1 and low <= value <= high, message)
    return int(value)


def money(pence):
    if pence < 100:
        return "{}p".format(pence)
    pounds, rest = divmod(pence, 100)
    return "£{}".format(pounds) if rest == 0 else "£{}.{:02d}".format(pounds, rest)


def coin(value):
    return "£1" if value == 100 else "{}p".format(value)


def count_of(n, singular, plural):
    return article(singular) if n == 1 else "{} {}".format(n, plural)


def cramer(a, b, c, d, first, second):
    """Solve ax + by = first, cx + dy = second exactly."""
    determinant = a * d - b * c
    require(determinant != 0, "Equations are not independent")
    return (Fraction(first * d - b * second, determinant),
            Fraction(a * second - first * c, determinant))


def named(values, unit):
    return {"kind": "named_values", "unit": unit,
            "values": {key: rational_text(value) for key, value in values.items()}}


def quantity(value, unit):
    return {"kind": "quantity", "value": rational_text(value), "unit": unit}


def expression(terms, constant=0):
    """Plain linear expression in x and y; identical in TeX for integers."""
    pieces = [(c < 0, (letter if abs(c) == 1 else str(abs(c)) + letter))
              for c, letter in terms if c != 0]
    if constant:
        pieces.append((constant < 0, str(abs(constant))))
    text = ""
    for index, (negative, body) in enumerate(pieces):
        if index == 0:
            text = ("-" if negative else "") + body
        else:
            text += (" - " if negative else " + ") + body
    return text


def bracketed(terms, constant=0):
    plain = "(" + expression(terms, constant) + ")"
    return (plain, plain)


def sympy_pair(sympy, equations, symbols):
    solutions = sympy.solve(equations, symbols, dict=True)
    require(len(solutions) == 1, "Story equations must have one solution")
    return tuple(Fraction(str(solutions[0][s])) for s in symbols)


# ------------------------------------------------ level 1: sum and difference

def build_sum_difference(rng):
    smaller = rng.randint(1, 25)
    larger = smaller + rng.randint(1, 20)
    return {"context": "sum_difference", "total": larger + smaller,
            "difference": larger - smaller}


def check_sum_difference(p):
    integers(p, "total difference")
    require(3 <= p["total"] <= 80 and 1 <= p["difference"] < p["total"], "Bounds")
    larger, smaller = cramer(1, 1, 1, -1, p["total"], p["difference"])
    return whole(larger, 2, 45, "Larger number"), whole(smaller, 1, 44, "Smaller number")


def parts_sum_difference(p):
    larger, smaller = check_sum_difference(p)
    text = ("Two numbers have a sum of {} and a difference of {}. "
            "Work out the two numbers.").format(p["total"], p["difference"])
    return {
        "prompt": Content(text),
        "answer": named({"larger": larger, "smaller": smaller}, ""),
        "answer_display": Content("The numbers are {} and {}.".format(larger, smaller)),
    }


def solve_sum_difference(p, sympy):
    l, s = sympy.symbols("l s")
    larger, smaller = sympy_pair(sympy, [sympy.Eq(l + s, p["total"]),
                                         sympy.Eq(l - s, p["difference"])], [l, s])
    return named({"larger": larger, "smaller": smaller}, "")


# ------------------------------------------------ levels 1, 2 and 4: shop

SHOP_KEYS = frozenset({"context", "items", "a", "b", "c", "d", "total_one", "total_two"})
SHOP_POOLS = {"shop_matching": COEFFICIENTS[1], "shop_scaled": COEFFICIENTS[2],
              "shop_followup": COEFFICIENTS[3]}


def build_shop(rng, name):
    a, b, c, d = rng.choice(SHOP_POOLS[name])
    price_x, price_y = 5 * rng.randint(4, 60), 5 * rng.randint(4, 60)
    p = {"context": name, "items": rng.choice(sorted(ITEMS)),
         "a": a, "b": b, "c": c, "d": d,
         "total_one": a * price_x + b * price_y,
         "total_two": c * price_x + d * price_y}
    if name == "shop_followup":
        p["ask_x"], p["ask_y"] = rng.randint(1, 6), rng.randint(1, 6)
    return p


def check_shop(p):
    integers(p, "a b c d total_one total_two")
    require(p["items"] in ITEMS, "Unknown items")
    require((p["a"], p["b"], p["c"], p["d"]) in SHOP_POOLS[p["context"]],
            "Coefficients violate the level structure")
    require(0 < p["total_one"] <= 5000 and 0 < p["total_two"] <= 5000, "Total bounds")
    x, y = cramer(p["a"], p["b"], p["c"], p["d"], p["total_one"], p["total_two"])
    price_x = whole(x, 20, 300, "First price outside bounds")
    price_y = whole(y, 20, 300, "Second price outside bounds")
    require(price_x % 5 == 0 and price_y % 5 == 0, "Prices must be multiples of 5p")
    require(price_x != price_y, "Prices must differ")
    if p["context"] == "shop_followup":
        integers(p, "ask_x ask_y")
        require(1 <= p["ask_x"] <= 6 and 1 <= p["ask_y"] <= 6, "Basket bounds")
        basket = (p["ask_x"], p["ask_y"])
        require(basket not in ((p["a"], p["b"]), (p["c"], p["d"])),
                "The new basket must not repeat a given one")
    return price_x, price_y


def shop_sentences(p):
    one_x, many_x, one_y, many_y = ITEMS[p["items"]]
    first = sentence_case("{} and {} cost {}.".format(
        count_of(p["a"], one_x, many_x), count_of(p["b"], one_y, many_y),
        money(p["total_one"])))
    second = sentence_case("{} and {} cost {}.".format(
        count_of(p["c"], one_x, many_x), count_of(p["d"], one_y, many_y),
        money(p["total_two"])))
    return first, second


def price_statement(one_x, price_x, one_y, price_y):
    return "{} costs {} and {} costs {}".format(
        sentence_case(article(one_x)), money(price_x), article(one_y), money(price_y))


def parts_shop(p):
    price_x, price_y = check_shop(p)
    one_x, many_x, one_y, many_y = ITEMS[p["items"]]
    first, second = shop_sentences(p)
    if p["context"] == "shop_followup":
        total = p["ask_x"] * price_x + p["ask_y"] * price_y
        ask = "Work out the cost of {} and {}.".format(
            count_of(p["ask_x"], one_x, many_x), count_of(p["ask_y"], one_y, many_y))
        return {
            "prompt": Content(" ".join((first, second, ask))),
            "answer": quantity(total, "p"),
            "answer_display": Content("{}, so the total is {}.".format(
                price_statement(one_x, price_x, one_y, price_y), money(total))),
        }
    ask = "Work out the cost of one {} and the cost of one {}.".format(one_x, one_y)
    return {
        "prompt": Content(" ".join((first, second, ask))),
        "answer": named({one_x: price_x, one_y: price_y}, "p"),
        "answer_display": Content(price_statement(one_x, price_x, one_y, price_y) + "."),
    }


def solve_shop(p, sympy):
    X, Y = sympy.symbols("X Y")
    price_x, price_y = sympy_pair(sympy, [
        sympy.Eq(p["a"] * X + p["b"] * Y, p["total_one"]),
        sympy.Eq(p["c"] * X + p["d"] * Y, p["total_two"]),
    ], [X, Y])
    one_x, _, one_y, _ = ITEMS[p["items"]]
    if p["context"] == "shop_followup":
        return quantity(p["ask_x"] * price_x + p["ask_y"] * price_y, "p")
    return named({one_x: price_x, one_y: price_y}, "p")


# ------------------------------------------------------- level 3: tickets

TICKET_KEYS = frozenset({"context", "venue", "a", "b", "c", "d", "total_one", "total_two"})


def build_tickets(rng):
    a, b, c, d = rng.choice(COEFFICIENTS[3])
    adult = 50 * rng.randint(8, 40)
    child = 50 * rng.randint(4, adult // 50 - 1)
    return {"context": "tickets", "venue": rng.choice(VENUES),
            "a": a, "b": b, "c": c, "d": d,
            "total_one": a * adult + b * child, "total_two": c * adult + d * child}


def check_tickets(p):
    integers(p, "a b c d total_one total_two")
    require(p["venue"] in VENUES, "Unknown venue")
    require((p["a"], p["b"], p["c"], p["d"]) in COEFFICIENTS[3],
            "Coefficients violate the level structure")
    x, y = cramer(p["a"], p["b"], p["c"], p["d"], p["total_one"], p["total_two"])
    adult = whole(x, 400, 2000, "Adult price outside bounds")
    child = whole(y, 200, 1950, "Child price outside bounds")
    require(adult % 50 == 0 and child % 50 == 0, "Prices must be multiples of 50p")
    require(child < adult, "A child ticket should cost less")
    return adult, child


def parts_tickets(p):
    adult, child = check_tickets(p)
    one_a, many_a, one_c, many_c = TICKETS
    text = ("At {}, {} and {} cost {}. {} and {} cost {}. "
            "Work out the cost of one adult ticket and the cost of one child ticket.").format(
        article(p["venue"]),
        count_of(p["a"], one_a, many_a), count_of(p["b"], one_c, many_c),
        money(p["total_one"]),
        sentence_case(count_of(p["c"], one_a, many_a)), count_of(p["d"], one_c, many_c),
        money(p["total_two"]))
    return {
        "prompt": Content(text),
        "answer": named({"adult ticket": adult, "child ticket": child}, "p"),
        "answer_display": Content(price_statement(one_a, adult, one_c, child) + "."),
    }


def solve_tickets(p, sympy):
    A, C = sympy.symbols("A C")
    adult, child = sympy_pair(sympy, [
        sympy.Eq(p["a"] * A + p["b"] * C, p["total_one"]),
        sympy.Eq(p["c"] * A + p["d"] * C, p["total_two"]),
    ], [A, C])
    return named({"adult ticket": adult, "child ticket": child}, "p")


# ---------------------------------------------------------- level 3: coins

def build_coins(rng):
    low, high = rng.choice(COINS)
    n_low, n_high = rng.randint(2, 30), rng.randint(2, 30)
    return {"context": "coins", "low": low, "high": high,
            "count": n_low + n_high, "value": low * n_low + high * n_high}


def check_coins(p):
    integers(p, "low high count value")
    require((p["low"], p["high"]) in COINS, "Unknown coins")
    x, y = cramer(1, 1, p["low"], p["high"], p["count"], p["value"])
    return (whole(x, 1, 40, "Coin count outside bounds"),
            whole(y, 1, 40, "Coin count outside bounds"))


def coin_answer(p, n_low, n_high):
    return named({coin(p["low"]) + " coins": n_low,
                  coin(p["high"]) + " coins": n_high}, "")


def parts_coins(p):
    n_low, n_high = check_coins(p)
    text = ("A jar contains only {} and {} coins. There are {} coins altogether, "
            "with a total value of {}. How many of each coin are in the jar?").format(
        coin(p["low"]), coin(p["high"]), p["count"], money(p["value"]))
    return {
        "prompt": Content(text),
        "answer": coin_answer(p, n_low, n_high),
        "answer_display": Content("{} × {} and {} × {}".format(
            n_low, coin(p["low"]), n_high, coin(p["high"]))),
    }


def solve_coins(p, sympy):
    L, H = sympy.symbols("L H")
    n_low, n_high = sympy_pair(sympy, [
        sympy.Eq(L + H, p["count"]),
        sympy.Eq(p["low"] * L + p["high"] * H, p["value"]),
    ], [L, H])
    return coin_answer(p, n_low, n_high)


# ------------------------------------------------------ level 4: rectangle

RECTANGLE_KEYS = frozenset({"context", "a1", "b1", "e1", "f1", "p", "q", "r", "s", "ask"})


def build_rectangle(rng):
    x, y = rng.randint(2, 9), rng.randint(2, 9)
    a1 = rng.randint(2, 6)
    e1 = rng.randint(1, a1 - 1)
    b1 = rng.randint(1, 4)
    p_, q, r = rng.randint(1, 4), rng.randint(1, 10), rng.randint(1, 4)
    return {"context": "rectangle", "a1": a1, "b1": b1, "e1": e1,
            "f1": (a1 - e1) * x + b1 * y, "p": p_, "q": q, "r": r,
            "s": p_ * x + q - r * y, "ask": rng.choice(RECTANGLE_ASKS)}


def check_rectangle(p):
    integers(p, "a1 b1 e1 f1 p q r s")
    require(p["ask"] in RECTANGLE_ASKS, "Unknown question")
    require(2 <= p["a1"] <= 6 and 1 <= p["e1"] < p["a1"] and 1 <= p["b1"] <= 4,
            "AB and DC coefficient bounds")
    require(1 <= p["f1"] <= 60, "DC constant bounds")
    require(1 <= p["p"] <= 4 and 1 <= p["q"] <= 10 and 1 <= p["r"] <= 4
            and -20 <= p["s"] <= 30, "AD and BC bounds")
    # AB = DC and AD = BC, collected into standard form.
    x, y = cramer(p["a1"] - p["e1"], p["b1"], p["p"], -p["r"],
                  p["f1"], p["s"] - p["q"])
    x = whole(x, 1, 10, "x outside bounds")
    y = whole(y, 1, 10, "y outside bounds")
    length = p["a1"] * x + p["b1"] * y
    width = p["p"] * x + p["q"]
    require(length >= 2 and width >= 2, "Side lengths must be positive")
    require(length <= 40 and width <= 30, "Keep the rectangle a sensible size")
    return x, y, length, width


def rectangle_value(p, length, width):
    return 2 * (length + width) if p["ask"] == "perimeter" else length * width


def parts_rectangle(p):
    x, y, length, width = check_rectangle(p)
    value = rectangle_value(p, length, width)
    unit = "cm" if p["ask"] == "perimeter" else "cm²"
    prompt = rich_prompt(
        ("ABCD is a rectangle.",),
        ("AB = ", bracketed([(p["a1"], "x"), (p["b1"], "y")]),
         " cm and DC = ", bracketed([(p["e1"], "x")], p["f1"]), " cm."),
        ("AD = ", bracketed([(p["p"], "x")], p["q"]),
         " cm and BC = ", bracketed([(p["r"], "y")], p["s"]), " cm."),
        ("Work out the {} of the rectangle.".format(p["ask"]),),
    )
    return {
        "prompt": prompt,
        "answer": quantity(value, unit),
        "answer_display": Content("x = {} and y = {}, so the {} is {} {}.".format(
            x, y, p["ask"], value, unit)),
    }


def solve_rectangle(p, sympy):
    x, y = sympy.symbols("x y")
    ab = p["a1"] * x + p["b1"] * y
    dc = p["e1"] * x + p["f1"]
    ad = p["p"] * x + p["q"]
    bc = p["r"] * y + p["s"]
    xv, yv = sympy_pair(sympy, [sympy.Eq(ab, dc), sympy.Eq(ad, bc)], [x, y])
    length = Fraction(str(ab.subs({x: xv, y: yv})))
    width = Fraction(str(ad.subs({x: xv, y: yv})))
    unit = "cm" if p["ask"] == "perimeter" else "cm²"
    value = length + width + length + width if p["ask"] == "perimeter" else length * width
    return quantity(value, unit)


# ------------------------------------------------------------ registry

CONTEXTS = {
    "sum_difference": Context(
        1, frozenset({"context", "total", "difference"}),
        build_sum_difference, check_sum_difference, parts_sum_difference,
        solve_sum_difference),
    "shop_matching": Context(
        1, SHOP_KEYS, lambda rng: build_shop(rng, "shop_matching"),
        check_shop, parts_shop, solve_shop),
    "shop_scaled": Context(
        2, SHOP_KEYS, lambda rng: build_shop(rng, "shop_scaled"),
        check_shop, parts_shop, solve_shop),
    "tickets": Context(
        3, TICKET_KEYS, build_tickets, check_tickets, parts_tickets, solve_tickets),
    "coins": Context(
        3, frozenset({"context", "low", "high", "count", "value"}),
        build_coins, check_coins, parts_coins, solve_coins),
    "shop_followup": Context(
        4, SHOP_KEYS | {"ask_x", "ask_y"}, lambda rng: build_shop(rng, "shop_followup"),
        check_shop, parts_shop, solve_shop),
    "rectangle": Context(
        4, RECTANGLE_KEYS, build_rectangle, check_rectangle, parts_rectangle,
        solve_rectangle),
}


def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    import sympy
    expected = CONTEXTS[q.parameters["context"]].solve(q.parameters, sympy)
    require(expected == q.answer, "Independent story solution disagrees")
    return True