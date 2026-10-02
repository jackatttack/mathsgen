"""Applied forms for ratio.money.problems: prices across currencies.

L2 currency_compare  one item priced in euros abroad and in pounds at home;
                     which city is cheaper, and by how much in pounds
L3 fuel_compare      fuel bought by the litre in euros and by the gallon in
                     pounds; is the claim about which is cheaper correct?
L4 fuel_percent      the same comparison as a percentage, to 1 decimal place

check() compares prices per litre in pounds with exact Fractions.
validate_independently() compares per gallon instead, and the currency form
by cross-multiplying.
"""
from fractions import Fraction

from .core import Content, require
from . import worded
from .worded import NAMES, Context, pounds


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {2: 0.3, 3: 0.35, 4: 0.35}
MARKS = {2: 3, 3: 4, 4: 5}
WORKING_LINES = {2: 5, 3: 7, 4: 8}

ITEMS = ("pair of trainers", "watch", "camera", "jacket", "games console")
CITIES = (("Paris", "London"), ("Madrid", "Cardiff"), ("Rome", "Glasgow"),
          ("Lisbon", "Belfast"))
EURO_RATES_CENTS = (110, 115, 120, 125, 140)      # £1 = €1.15 is 115
COUNTRIES = (("Spain", "Wales"), ("France", "Scotland"), ("Italy", "England"),
             ("Portugal", "Northern Ireland"))
POUNDS_PER_EURO = ("0.84", "0.85", "0.86", "0.88", "0.9")
LITRES_PER_GALLON = Fraction(9, 2)
MINIMUM_FUEL_GAP = Fraction(3, 100)               # prices differ by at least 3%


def context_share(level):
    return CONTEXT_SHARE.get(level, 0.0)


def is_applied(question):
    p = question.parameters
    return isinstance(p, dict) and p.get("context") in CONTEXTS


# ------------------------------------------------------------ money text

def euros(cents):
    whole, rest = divmod(cents, 100)
    return "€{}".format(whole) if rest == 0 else "€{}.{:02d}".format(whole, rest)


def rate_text(cents):
    return "{}.{:02d}".format(cents // 100, cents % 100)


def rounded(value, places):
    """value rounded half up to places decimal places, as text."""
    scaled = Fraction(value) * 10 ** places
    whole, rest = divmod(int((scaled * 2 + 1) // 2), 10 ** places)
    return "{}.{:0{width}d}".format(whole, rest, width=places)


def whole_in(value, low, high, message):
    require(type(value) is int and low <= value <= high, message)
    return value


# -------------------------------------------- L2: one item, two currencies

def build_currency(rng):
    rate = rng.choice(EURO_RATES_CENTS)
    home_pounds = rng.randint(40, 300)
    abroad_pounds = home_pounds + rng.choice((-1, 1)) * rng.randint(3, 30)
    return {"context": "currency_compare", "item": rng.randrange(len(ITEMS)),
            "cities": rng.randrange(len(CITIES)), "rate_cents": rate,
            "home_pence": home_pounds * 100, "euro_cents": abroad_pounds * rate}


def check_currency(p):
    whole_in(p["item"], 0, len(ITEMS) - 1, "Unknown item")
    whole_in(p["cities"], 0, len(CITIES) - 1, "Unknown cities")
    require(p["rate_cents"] in EURO_RATES_CENTS, "Unknown exchange rate")
    whole_in(p["home_pence"], 1000, 50000, "Home price out of bounds")
    whole_in(p["euro_cents"], 1000, 60000, "Euro price out of bounds")
    abroad = Fraction(p["euro_cents"] * 100, p["rate_cents"])
    require(abroad.denominator == 1, "The euro price must convert to whole pence")
    difference = p["home_pence"] - int(abroad)
    require(abs(difference) >= 100, "Prices must differ by at least £1")
    return int(abroad), difference


def parts_currency(p):
    abroad, difference = check_currency(p)
    away, home = CITIES[p["cities"]]
    item = ITEMS[p["item"]]
    cheaper = away if difference > 0 else home
    text = ("A {item} costs {euro} in {away} and {home_price} in {home}. The exchange "
            "rate is £1 = €{rate}. In which city is the {item} cheaper, and by how much "
            "in pounds?").format(item=item, euro=euros(p["euro_cents"]), away=away,
                                 home_price=pounds(p["home_pence"]), home=home,
                                 rate=rate_text(p["rate_cents"]))
    shown = "{} is cheaper, by {}. ({} = {})".format(
        cheaper, pounds(abs(difference)), euros(p["euro_cents"]), pounds(abroad))
    return {"prompt": Content(text),
            "answer": {"kind": "cheaper", "place": cheaper, "difference_pence": abs(difference)},
            "answer_display": Content(shown)}


# ------------------------------------------- L3 and L4: fuel by litre and gallon

def build_fuel(rng, context):
    litres, gallons = rng.randint(15, 50), rng.randint(5, 12)
    p = {"context": context, "names": rng.sample(NAMES, 2),
         "countries": rng.randrange(len(COUNTRIES)), "rate": rng.choice(POUNDS_PER_EURO),
         "litres": litres, "euro_cents": litres * rng.randint(140, 185),
         "gallons": gallons,
         "pound_pence": int(round(gallons * 4.5 * rng.randint(125, 160)))}
    if context == "fuel_compare":
        p["claim"] = rng.randrange(2)
    return p


def fuel_prices(p):
    """(abroad, home) price per litre in pounds, after checking the story."""
    names = p["names"]
    require(isinstance(names, list) and len(names) == 2 and len(set(names)) == 2
            and all(name in NAMES for name in names), "Two distinct known names")
    whole_in(p["countries"], 0, len(COUNTRIES) - 1, "Unknown countries")
    require(p["rate"] in POUNDS_PER_EURO, "Unknown exchange rate")
    whole_in(p["litres"], 10, 60, "Litres out of bounds")
    whole_in(p["euro_cents"], 1000, 12000, "Euro price out of bounds")
    whole_in(p["gallons"], 3, 15, "Gallons out of bounds")
    whole_in(p["pound_pence"], 1000, 15000, "Pound price out of bounds")
    abroad = Fraction(p["euro_cents"], 100) * Fraction(p["rate"]) / p["litres"]
    home = Fraction(p["pound_pence"], 100) / (p["gallons"] * LITRES_PER_GALLON)
    require(abs(abroad - home) >= MINIMUM_FUEL_GAP * max(abroad, home),
            "Prices too close to compare fairly")
    return abroad, home


def fuel_story(p):
    away, home = COUNTRIES[p["countries"]]
    first, second = p["names"]
    return ("In {away}, {first} pays {euro} for {litres} litres of petrol. In {home}, "
            "{second} pays {pound} for {gallons} gallons of the same petrol. "
            "€1 = £{rate} and 1 gallon = 4.5 litres.").format(
        away=away, home=home, first=first, second=second, euro=euros(p["euro_cents"]),
        litres=p["litres"], pound=pounds(p["pound_pence"]), gallons=p["gallons"],
        rate=p["rate"])


def check_compare(p):
    require(p["claim"] in (0, 1), "Unknown claim")
    return fuel_prices(p)


def parts_compare(p):
    abroad, home_price = check_compare(p)
    away, home = COUNTRIES[p["countries"]]
    first = p["names"][0]
    claimed = (away, home)[p["claim"]]
    cheaper = away if abroad < home_price else home
    correct = cheaper == claimed
    text = fuel_story(p) + (" {first} thinks petrol is cheaper in {claimed}. Is {first} "
                            "correct? You must show how you get your answer.").format(
        first=first, claimed=claimed)
    shown = "{}: £{} per litre. {}: £{} per litre. Petrol is cheaper in {}, so {} is {}correct.".format(
        away, rounded(abroad, 3), home, rounded(home_price, 3), cheaper, first,
        "" if correct else "not ")
    return {"prompt": Content(text),
            "answer": {"kind": "verdict", "correct": correct, "cheaper": cheaper},
            "answer_display": Content(shown)}


def percent_cheaper(abroad, home_price):
    cheap, dear = min(abroad, home_price), max(abroad, home_price)
    return (dear - cheap) / dear * 100


def check_percent(p):
    return fuel_prices(p)


def parts_percent(p):
    abroad, home_price = check_percent(p)
    away, home = COUNTRIES[p["countries"]]
    cheap, dear = (away, home) if abroad < home_price else (home, away)
    value = rounded(percent_cheaper(abroad, home_price), 1)
    text = fuel_story(p) + (" By what percentage is petrol cheaper in {cheap} than in "
                            "{dear}? Give your answer to 1 decimal place.").format(
        cheap=cheap, dear=dear)
    return {"prompt": Content(text), "answer": {"kind": "percent", "value": value},
            "answer_display": Content(value + "%")}


# ----------------------------------------------------------------- registry

FUEL_KEYS = frozenset({"context", "names", "countries", "rate", "litres", "euro_cents",
                       "gallons", "pound_pence"})

CONTEXTS = {
    "currency_compare": Context(
        2, frozenset({"context", "item", "cities", "rate_cents", "home_pence", "euro_cents"}),
        build_currency, check_currency, parts_currency, None),
    "fuel_compare": Context(
        3, FUEL_KEYS | {"claim"}, lambda rng: build_fuel(rng, "fuel_compare"),
        check_compare, parts_compare, None),
    "fuel_percent": Context(
        4, FUEL_KEYS, lambda rng: build_fuel(rng, "fuel_percent"),
        check_percent, parts_percent, None),
}


# ------------------------------------------------ generate and validate

def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    """Currency by cross-multiplying; fuel per gallon rather than per litre."""
    import sympy
    p, answer = q.parameters, q.answer
    if p["context"] == "currency_compare":
        away, home = CITIES[p["cities"]]
        abroad_cheaper = p["euro_cents"] * 100 < p["home_pence"] * p["rate_cents"]
        require(answer["place"] == (away if abroad_cheaper else home),
                "Independent comparison disagrees")
        gap = abs(sympy.Rational(p["home_pence"]) - sympy.Rational(p["euro_cents"] * 100,
                                                                    p["rate_cents"]))
        require(gap == answer["difference_pence"], "Independent difference disagrees")
        return True
    away, home = COUNTRIES[p["countries"]]
    abroad_gallon = (sympy.Rational(p["euro_cents"], 100) * sympy.Rational(p["rate"])
                     / p["litres"] * sympy.Rational(9, 2))
    home_gallon = sympy.Rational(p["pound_pence"], 100) / p["gallons"]
    cheaper = away if abroad_gallon < home_gallon else home
    if p["context"] == "fuel_compare":
        require(answer["cheaper"] == cheaper, "Independent cheaper country disagrees")
        require(answer["correct"] == (cheaper == (away, home)[p["claim"]]),
                "Independent verdict disagrees")
        return True
    cheap, dear = sorted((abroad_gallon, home_gallon))
    percent = (1 - cheap / dear) * 100
    tenths = sympy.floor(percent * 10 + sympy.Rational(1, 2))
    require(sympy.Rational(answer["value"]) == tenths / 10, "Independent percentage disagrees")
    return True