"""Worded contexts for number.percentages.of_amount.

Level 1: the amount taken off in a sale (familiar percentages).
Level 2: a new price after an increase or decrease.
Level 3: compare a percentage discount with a money discount.
Level 4: successive changes, or a percentage of a percentage.

Money is exact whole pence: a whole-pound price times a whole-number
percentage is a whole number of pence. check() works in integer pence;
solve() recomputes independently with SymPy multipliers.
"""
from fractions import Fraction

from .core import Content, require
from . import worded
from .worded import (Context, article, integers, money_answer, pounds,
                     quantity, sentence_case, whole)


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {1: 0.35, 2: 0.4, 3: 0.5, 4: 0.5}
MARKS = {1: 2, 2: 3, 3: 4, 4: 4}
WORKING_LINES = {1: 4, 2: 5, 3: 6, 4: 7}

ITEMS = ("coat", "bike", "laptop", "sofa", "tent", "watch", "guitar",
         "games console", "jacket", "printer")

DISCOUNT_RATES = (10, 20, 25, 50, 75)
CHANGE_RATES = (5, 12, 15, 35, 45, 65)
OFFER_RATES = (12, 15, 35, 45)
SUCCESSIVE_RATES = (5, 10, 15, 20, 25, 30)
SHARE_RATES = (15, 20, 25, 30, 40, 60, 75, 80)
DIRECTIONS = ("increase", "decrease")

# scenario: (situation, question)
SCENARIOS = {
    "school": ("A school has {n} students. {p}% of the students walk to school. "
               "{q}% of the students who walk to school walk with a friend.",
               "How many students walk to school with a friend?"),
    "survey": ("{n} people were asked about pets. {p}% of them own a pet. "
               "{q}% of the pet owners own a dog.",
               "How many of the people own a dog?"),
    "orchard": ("An orchard has {n} trees. {p}% of the trees are apple trees. "
                "{q}% of the apple trees are more than ten years old.",
                "How many apple trees are more than ten years old?"),
}


def item_intro(p):
    return "{} costs £{}.".format(sentence_case(article(p["item"])), p["price"])


# ------------------------------------------------------ level 1: discount

def build_discount(rng):
    return {"context": "discount", "item": rng.choice(ITEMS),
            "price": rng.randint(12, 400), "rate": rng.choice(DISCOUNT_RATES)}


def check_discount(p):
    integers(p, "price rate")
    require(p["item"] in ITEMS and p["rate"] in DISCOUNT_RATES, "Story choices")
    require(12 <= p["price"] <= 400, "Price bounds")
    return p["price"] * p["rate"]  # pounds x percent = pence


def parts_discount(p):
    pence = check_discount(p)
    text = "{} In a sale, its price is reduced by {}%. How much money is taken off the price?".format(
        item_intro(p), p["rate"])
    return {"prompt": Content(text), "answer": money_answer(pence),
            "answer_display": Content(pounds(pence))}


def solve_discount(p, sympy):
    return money_answer(sympy.Integer(p["price"]) * 100 * sympy.Rational(p["rate"], 100))


# ------------------------------------------------------ level 2: new price

def build_new_price(rng):
    return {"context": "new_price", "item": rng.choice(ITEMS),
            "price": rng.randint(12, 400), "rate": rng.choice(CHANGE_RATES),
            "direction": rng.choice(DIRECTIONS)}


def check_new_price(p):
    integers(p, "price rate")
    require(p["item"] in ITEMS and p["rate"] in CHANGE_RATES
            and p["direction"] in DIRECTIONS, "Story choices")
    require(12 <= p["price"] <= 400, "Price bounds")
    sign = 1 if p["direction"] == "increase" else -1
    return p["price"] * 100 + sign * p["price"] * p["rate"]


def parts_new_price(p):
    pence = check_new_price(p)
    text = "{} Its price {}s by {}%. Work out the new price.".format(
        item_intro(p), p["direction"], p["rate"])
    return {"prompt": Content(text), "answer": money_answer(pence),
            "answer_display": Content(pounds(pence))}


def solve_new_price(p, sympy):
    sign = 1 if p["direction"] == "increase" else -1
    multiplier = 1 + sign * sympy.Rational(p["rate"], 100)
    return money_answer(p["price"] * 100 * multiplier)


# ------------------------------------------------------ level 3: offers

def build_offers(rng):
    price, rate = rng.randint(20, 300), rng.choice(OFFER_RATES)
    cut = price * rate // 100 + rng.choice((-4, -3, -2, -1, 1, 2, 3, 4))
    return {"context": "offers", "item": rng.choice(ITEMS),
            "price": price, "rate": rate, "cut": cut}


def offer_answer(choice, pence):
    return {"kind": "choice_money", "choice": choice, "pence": int(pence)}


def check_offers(p):
    integers(p, "price rate cut")
    require(p["item"] in ITEMS and p["rate"] in OFFER_RATES, "Story choices")
    require(20 <= p["price"] <= 300 and 1 <= p["cut"] < p["price"], "Price bounds")
    shop_a = p["price"] * 100 - p["price"] * p["rate"]
    shop_b = (p["price"] - p["cut"]) * 100
    require(shop_a != shop_b, "The offers must differ")
    return ("Shop A" if shop_a < shop_b else "Shop B"), abs(shop_a - shop_b)


def parts_offers(p):
    choice, pence = check_offers(p)
    text = ("{} costs £{} in two shops. Shop A takes {}% off the price. "
            "Shop B takes £{} off the price. Which shop is cheaper, and by how much?").format(
        sentence_case(article(p["item"])), p["price"], p["rate"], p["cut"])
    return {"prompt": Content(text), "answer": offer_answer(choice, pence),
            "answer_display": Content("{} is cheaper, by {}.".format(choice, pounds(pence)))}


def solve_offers(p, sympy):
    shop_a = p["price"] * 100 * (1 - sympy.Rational(p["rate"], 100))
    shop_b = (p["price"] - p["cut"]) * 100
    choice = "Shop A" if shop_a < shop_b else "Shop B"
    return offer_answer(choice, money_answer(abs(shop_a - shop_b))["pence"])


# --------------------------------------------------- level 4: successive

def build_successive(rng):
    return {"context": "successive", "item": rng.choice(ITEMS),
            "price": rng.randint(20, 500), "up": rng.choice(SUCCESSIVE_RATES),
            "down": rng.choice(SUCCESSIVE_RATES)}


def check_successive(p):
    integers(p, "price up down")
    require(p["item"] in ITEMS and p["up"] in SUCCESSIVE_RATES
            and p["down"] in SUCCESSIVE_RATES, "Story choices")
    require(20 <= p["price"] <= 500, "Price bounds")
    return whole(Fraction(p["price"] * (100 + p["up"]) * (100 - p["down"]), 100),
                 1, 10 ** 6, "Final price must be whole pence")


def parts_successive(p):
    pence = check_successive(p)
    text = ("{} Its price is increased by {}%. The new price is then reduced by {}%. "
            "Work out the final price.").format(item_intro(p), p["up"], p["down"])
    return {"prompt": Content(text), "answer": money_answer(pence),
            "answer_display": Content(pounds(pence))}


def solve_successive(p, sympy):
    R = sympy.Rational
    return money_answer(p["price"] * 100 * (1 + R(p["up"], 100)) * (1 - R(p["down"], 100)))


# ------------------------------------------------ level 4: share of a share

def build_share_of_share(rng):
    return {"context": "share_of_share", "scenario": rng.choice(sorted(SCENARIOS)),
            "n": 20 * rng.randint(2, 100), "p": rng.choice(SHARE_RATES),
            "q": rng.choice(SHARE_RATES)}


def check_share_of_share(p):
    integers(p, "n p q")
    require(p["scenario"] in SCENARIOS and p["p"] in SHARE_RATES
            and p["q"] in SHARE_RATES, "Story choices")
    require(40 <= p["n"] <= 2000, "Group size bounds")
    first = whole(Fraction(p["n"] * p["p"], 100), 1, p["n"], "First share must be whole")
    return whole(Fraction(first * p["q"], 100), 1, p["n"], "Second share must be whole")


def parts_share_of_share(p):
    count = check_share_of_share(p)
    situation, question = SCENARIOS[p["scenario"]]
    text = situation.format(**p) + " " + question
    return {"prompt": Content(text), "answer": quantity(count, ""),
            "answer_display": Content(str(count))}


def solve_share_of_share(p, sympy):
    R = sympy.Rational
    return quantity(p["n"] * R(p["p"], 100) * R(p["q"], 100), "")


# ------------------------------------------------------------ registry

ITEM_PRICE = {"context", "item", "price"}

CONTEXTS = {
    "discount": Context(1, frozenset(ITEM_PRICE | {"rate"}),
                        build_discount, check_discount, parts_discount, solve_discount),
    "new_price": Context(2, frozenset(ITEM_PRICE | {"rate", "direction"}),
                         build_new_price, check_new_price, parts_new_price, solve_new_price),
    "offers": Context(3, frozenset(ITEM_PRICE | {"rate", "cut"}),
                      build_offers, check_offers, parts_offers, solve_offers),
    "successive": Context(4, frozenset(ITEM_PRICE | {"up", "down"}),
                          build_successive, check_successive, parts_successive,
                          solve_successive),
    "share_of_share": Context(4, frozenset({"context", "scenario", "n", "p", "q"}),
                              build_share_of_share, check_share_of_share,
                              parts_share_of_share, solve_share_of_share),
}


def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    import sympy
    expected = CONTEXTS[q.parameters["context"]].solve(q.parameters, sympy)
    require(expected == q.answer, "Independent percentage calculation disagrees")
    return True