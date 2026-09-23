"""Worded contexts for ratio.sharing.

Level 2: find the total from the difference between two shares.
Level 3: work from one known share (money) to another share or the total.
Level 4: the ratio changes after a gift; find a starting amount.

check() solves from the displayed numbers with exact Fractions.
solve() sets up the story's equations separately and solves them in SymPy.
"""
from fractions import Fraction
from functools import reduce
from math import gcd

from .core import Content, require
from . import worded
from .worded import (Context, NAMES, distinct_names, integers, money_answer,
                     pounds, quantity, sympy_solve, whole)


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {2: 0.4, 3: 0.4, 4: 0.5}
MARKS = {2: 3, 3: 3, 4: 4}
WORKING_LINES = {2: 5, 3: 5, 4: 8}

THINGS = ("sweets", "stickers", "marbles", "cards", "badges")


def ratio_text(parts):
    return " : ".join(str(part) for part in parts)


def simplified(parts):
    common = reduce(gcd, parts)
    return [part // common for part in parts]


# --------------------------------------------------- level 2: difference

def build_difference(rng):
    a, b = sorted(rng.sample(range(1, 10), 2))
    first, second = rng.sample(NAMES, 2)
    return {"context": "difference", "first": first, "second": second,
            "thing": rng.choice(THINGS), "a": a, "b": b,
            "more": (b - a) * rng.randint(2, 15)}


def check_difference(p):
    integers(p, "a b more")
    distinct_names(p["first"], p["second"])
    require(p["thing"] in THINGS, "Unknown thing")
    require(1 <= p["a"] < p["b"] <= 9 and gcd(p["a"], p["b"]) == 1,
            "Ratio must be simplified with the second part larger")
    unit = whole(Fraction(p["more"], p["b"] - p["a"]), 2, 15, "One part outside bounds")
    return (p["a"] + p["b"]) * unit


def parts_difference(p):
    total = check_difference(p)
    text = ("{first} and {second} share some {thing} in the ratio {a} : {b}. "
            "{second} gets {more} more {thing} than {first}. "
            "How many {thing} are there altogether?").format(**p)
    return {"prompt": Content(text), "answer": quantity(total, p["thing"]),
            "answer_display": Content("{} {}".format(total, p["thing"]))}


def solve_difference(p, sympy):
    A, B = sympy.symbols("A B")
    first, second = sympy_solve(sympy, [sympy.Eq(A * p["b"], B * p["a"]),
                                        sympy.Eq(B - A, p["more"])], [A, B])
    return quantity(first + second, p["thing"])


# ---------------------------------------------------- level 3: one share

def build_one_share(rng):
    ratio = simplified(rng.sample(range(1, 10), 3))
    known_index = rng.randint(0, 2)
    return {"context": "one_share", "names": rng.sample(NAMES, 3), "ratio": ratio,
            "known_index": known_index,
            "known": ratio[known_index] * 25 * rng.randint(1, 24),
            "ask": rng.choice([-1] + [j for j in range(3) if j != known_index])}


def check_one_share(p):
    integers(p, "known_index known ask")
    names, ratio = p["names"], p["ratio"]
    require(isinstance(names, list) and len(names) == 3, "Three names")
    distinct_names(*names)
    require(isinstance(ratio, list) and len(ratio) == 3
            and all(type(r) is int and 1 <= r <= 9 for r in ratio)
            and len(set(ratio)) == 3 and reduce(gcd, ratio) == 1,
            "Ratio must be three distinct simplified parts")
    require(0 <= p["known_index"] <= 2, "Known share index")
    require(p["ask"] in (-1, 0, 1, 2) and p["ask"] != p["known_index"], "Asked share")
    unit = whole(Fraction(p["known"], ratio[p["known_index"]]), 25, 600,
                 "One part outside bounds")
    require(unit % 25 == 0, "One part must be a multiple of 25p")
    shares = [r * unit for r in ratio]
    return sum(shares) if p["ask"] == -1 else shares[p["ask"]]


def parts_one_share(p):
    value = check_one_share(p)
    names = p["names"]
    if p["ask"] == -1:
        question = "How much money is shared altogether?"
    else:
        question = "How much does {} receive?".format(names[p["ask"]])
    text = "{}, {} and {} share some money in the ratio {}. {} receives {}. {}".format(
        names[0], names[1], names[2], ratio_text(p["ratio"]),
        names[p["known_index"]], pounds(p["known"]), question)
    return {"prompt": Content(text), "answer": money_answer(value),
            "answer_display": Content(pounds(value))}


def solve_one_share(p, sympy):
    u = sympy.Symbol("u")
    (unit,) = sympy_solve(sympy, [sympy.Eq(p["ratio"][p["known_index"]] * u, p["known"])], [u])
    shares = [r * unit for r in p["ratio"]]
    return money_answer(sum(shares) if p["ask"] == -1 else shares[p["ask"]])


# -------------------------------------------------- level 4: ratio change

def build_ratio_change(rng):
    a, b = simplified(rng.sample(range(1, 10), 2))
    unit = rng.randint(2, 12)
    k = rng.randint(2, a * unit - 1) if a * unit >= 3 else 0
    c, d = simplified([a * unit - k, b * unit + k]) if k else (0, 0)
    first, second = rng.sample(NAMES, 2)
    return {"context": "ratio_change", "first": first, "second": second,
            "thing": rng.choice(THINGS), "a": a, "b": b, "k": k, "c": c, "d": d}


def check_ratio_change(p):
    integers(p, "a b k c d")
    distinct_names(p["first"], p["second"])
    require(p["thing"] in THINGS, "Unknown thing")
    require(1 <= p["a"] <= 9 and 1 <= p["b"] <= 9 and p["a"] != p["b"]
            and gcd(p["a"], p["b"]) == 1, "Starting ratio")
    require(1 <= p["c"] <= 30 and 1 <= p["d"] <= 30 and gcd(p["c"], p["d"]) == 1
            and (p["c"], p["d"]) != (p["a"], p["b"]), "New ratio")
    require(2 <= p["k"] <= 60, "Gift bounds")
    determinant = p["a"] * p["d"] - p["b"] * p["c"]
    require(determinant != 0, "The ratio must genuinely change")
    unit = whole(Fraction(p["k"] * (p["c"] + p["d"]), determinant), 2, 12,
                 "One part outside bounds")
    require(p["a"] * unit - p["k"] >= 1, "The giver must have some left")
    return p["a"] * unit


def parts_ratio_change(p):
    start = check_ratio_change(p)
    text = ("{first} and {second} have some {thing} in the ratio {a} : {b}. "
            "{first} gives {k} {thing} to {second}. The ratio is now {c} : {d}. "
            "How many {thing} did {first} have at the start?").format(**p)
    return {"prompt": Content(text), "answer": quantity(start, p["thing"]),
            "answer_display": Content("{} had {} {} at the start.".format(
                p["first"], start, p["thing"]))}


def solve_ratio_change(p, sympy):
    X, Y = sympy.symbols("X Y")
    first, _ = sympy_solve(sympy, [
        sympy.Eq(X * p["b"], Y * p["a"]),
        sympy.Eq((X - p["k"]) * p["d"], (Y + p["k"]) * p["c"]),
    ], [X, Y])
    return quantity(first, p["thing"])


# ------------------------------------------------------------ registry

PAIR_KEYS = {"context", "first", "second", "thing"}

CONTEXTS = {
    "difference": Context(2, frozenset(PAIR_KEYS | {"a", "b", "more"}),
                          build_difference, check_difference, parts_difference,
                          solve_difference),
    "one_share": Context(3, frozenset({"context", "names", "ratio", "known_index",
                                       "known", "ask"}),
                         build_one_share, check_one_share, parts_one_share,
                         solve_one_share),
    "ratio_change": Context(4, frozenset(PAIR_KEYS | {"a", "b", "k", "c", "d"}),
                            build_ratio_change, check_ratio_change, parts_ratio_change,
                            solve_ratio_change),
}


def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    import sympy
    expected = CONTEXTS[q.parameters["context"]].solve(q.parameters, sympy)
    require(expected == q.answer, "Independent ratio solution disagrees")
    return True