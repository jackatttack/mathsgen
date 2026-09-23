"""Worded contexts for number.factors.hcf and number.multiples.lcm.

HCF  L2: cut two lengths into equal pieces.   L3: three lengths.
     L4: the greatest number of identical bags, and what is in each.
LCM  L2: when two buses next leave together.  L3: three flashing lights.
     L4: the least number of packs so two items match.

check() uses math.gcd; solve() searches divisors and multiples directly,
so the two routes are mathematically distinct.
"""
from functools import reduce
from math import gcd

from .core import Content, require
from . import worded
from .worded import (Context, NAMES, distinct_names, integers, quantity,
                     sentence_case)


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {2: 0.4, 3: 0.4, 4: 0.5}
MARKS = {2: 2, 3: 3, 4: 3}
WORKING_LINES = {2: 4, 3: 5, 4: 6}

BAG_ITEMS = {
    "stationery": ("pencils", "rubbers"), "treats": ("sweets", "stickers"),
    "fruit": ("apples", "oranges"), "party": ("badges", "balloons"),
}
PACK_ITEMS = {
    "barbecue": ("bread rolls", "burgers"), "picnic": ("cups", "plates"),
    "party": ("balloons", "party hats"), "camp": ("hot dogs", "hot dog buns"),
}


def hcf(values):
    return reduce(gcd, values)


def lcm(values):
    return reduce(lambda a, b: a // gcd(a, b) * b, values, 1)


def hcf_by_search(values):
    return max(d for d in range(1, min(values) + 1) if all(v % d == 0 for v in values))


def lcm_by_search(values):
    step = max(values)
    multiple = step
    while any(multiple % v for v in values):
        multiple += step
    return multiple


def lengths(p, names):
    integers(p, names)
    values = [p[name] for name in names.split()]
    require(len(set(values)) == len(values), "Values must differ")
    return values


def no_divisors(values):
    require(all(a % b for a in values for b in values if a != b),
            "No value may divide another")


def clock(minutes):
    hour, minute = divmod(minutes, 60)
    suffix = "am" if hour < 12 else "pm"
    shown = hour if 1 <= hour <= 12 else (hour - 12 if hour > 12 else 12)
    return "{}:{:02d} {}".format(shown, minute, suffix)


def time_answer(minutes):
    return {"kind": "time", "value": "{:02d}:{:02d}".format(*divmod(minutes, 60))}


# ----------------------------------------------------------- HCF contexts

def build_ribbons(rng, count):
    g = rng.randint(3, 15) if count == 2 else rng.randint(2, 12)
    factors = rng.sample(range(2, 10), count)
    p = {"context": "ribbons{}".format(count)}
    for name, factor in zip("abc", factors):
        p[name] = g * factor
    return p


def check_ribbons(p):
    names = "a b" if p["context"] == "ribbons2" else "a b c"
    values = lengths(p, names)
    require(all(6 <= v <= 200 for v in values), "Length bounds")
    no_divisors(values)
    common = hcf(values)
    require(common >= 2, "Pieces must be longer than 1 cm")
    return common


def parts_ribbons(p):
    common = check_ribbons(p)
    if p["context"] == "ribbons2":
        intro = "Two ribbons are {} cm and {} cm long.".format(p["a"], p["b"])
    else:
        intro = "Three ribbons are {} cm, {} cm and {} cm long.".format(p["a"], p["b"], p["c"])
    every = "Both" if p["context"] == "ribbons2" else "All the"
    text = (intro + " {} ribbons are cut into pieces of the same length, with "
            "nothing left over. What is the greatest possible length of each "
            "piece?").format(every)
    return {"prompt": Content(text), "answer": quantity(common, "cm"),
            "answer_display": Content("{} cm".format(common))}


def solve_ribbons(p, sympy):
    names = "ab" if p["context"] == "ribbons2" else "abc"
    return quantity(hcf_by_search([p[n] for n in names]), "cm")


def build_bags(rng):
    g = rng.randint(3, 12)
    m, n = rng.sample(range(2, 10), 2)
    return {"context": "bags", "name": rng.choice(NAMES),
            "items": rng.choice(sorted(BAG_ITEMS)), "a": g * m, "b": g * n}


def bag_answer(p, bags):
    x, y = BAG_ITEMS[p["items"]]
    return {"kind": "named_values", "unit": "",
            "values": {"bags": str(bags), x: str(p["a"] // bags), y: str(p["b"] // bags)}}


def check_bags(p):
    values = lengths(p, "a b")
    distinct_names(p["name"])
    require(p["items"] in BAG_ITEMS, "Unknown items")
    require(all(6 <= v <= 150 for v in values), "Count bounds")
    no_divisors(values)
    bags = hcf(values)
    require(bags >= 3, "At least three bags")
    return bags


def parts_bags(p):
    bags = check_bags(p)
    x, y = BAG_ITEMS[p["items"]]
    text = ("{name} has {a} {x} and {b} {y}. {name} puts all of them into identical "
            "party bags, so that every bag has the same number of {x} and the same "
            "number of {y}, with none left over. What is the greatest number of bags "
            "{name} can make, and how many {x} and {y} are in each bag?").format(
        x=x, y=y, **p)
    return {"prompt": Content(text), "answer": bag_answer(p, bags),
            "answer_display": Content("{} bags, each with {} {} and {} {}.".format(
                bags, p["a"] // bags, x, p["b"] // bags, y))}


def solve_bags(p, sympy):
    return bag_answer(p, hcf_by_search([p["a"], p["b"]]))


# ----------------------------------------------------------- LCM contexts

def build_buses(rng):
    a, b = rng.sample(range(6, 31), 2)
    return {"context": "buses", "a": a, "b": b, "start": rng.randint(6, 10)}


def check_buses(p):
    values = lengths(p, "a b")
    integers(p, "start")
    require(all(6 <= v <= 30 for v in values) and 6 <= p["start"] <= 10, "Bounds")
    no_divisors(values)
    gap = lcm(values)
    require(20 <= gap <= 180, "Next departure must be within three hours")
    return p["start"] * 60 + gap


def parts_buses(p):
    minutes = check_buses(p)
    text = ("Bus A leaves the bus station every {} minutes. Bus B leaves every {} minutes. "
            "Both buses leave the bus station at {}. At what time will they next leave "
            "together?").format(p["a"], p["b"], clock(p["start"] * 60))
    return {"prompt": Content(text), "answer": time_answer(minutes),
            "answer_display": Content(clock(minutes))}


def solve_buses(p, sympy):
    return time_answer(p["start"] * 60 + lcm_by_search([p["a"], p["b"]]))


def build_lights(rng):
    a, b, c = rng.sample(range(4, 21), 3)
    return {"context": "lights", "a": a, "b": b, "c": c}


def check_lights(p):
    values = lengths(p, "a b c")
    require(all(4 <= v <= 20 for v in values), "Bounds")
    gap = lcm(values)
    require(max(values) < gap <= 600, "Next flash within ten minutes, and not trivial")
    return gap


def parts_lights(p):
    gap = check_lights(p)
    text = ("Three lights flash every {} seconds, {} seconds and {} seconds. They all "
            "flash together now. After how many seconds will they next all flash "
            "together?").format(p["a"], p["b"], p["c"])
    return {"prompt": Content(text), "answer": quantity(gap, "seconds"),
            "answer_display": Content("{} seconds".format(gap))}


def solve_lights(p, sympy):
    return quantity(lcm_by_search([p["a"], p["b"], p["c"]]), "seconds")


def build_packs(rng):
    a, b = rng.sample(range(4, 21), 2)
    return {"context": "packs", "name": rng.choice(NAMES),
            "items": rng.choice(sorted(PACK_ITEMS)), "a": a, "b": b}


def pack_answer(p, total):
    x, y = PACK_ITEMS[p["items"]]
    return {"kind": "named_values", "unit": "packs",
            "values": {x: str(total // p["a"]), y: str(total // p["b"])}}


def check_packs(p):
    values = lengths(p, "a b")
    distinct_names(p["name"])
    require(p["items"] in PACK_ITEMS, "Unknown items")
    require(all(4 <= v <= 20 for v in values), "Bounds")
    no_divisors(values)
    total = lcm(values)
    require(total <= 240, "Keep the totals sensible")
    return total


def parts_packs(p):
    total = check_packs(p)
    x, y = PACK_ITEMS[p["items"]]
    text = ("{} are sold in packs of {}. {} are sold in packs of {}. {} wants to buy "
            "exactly the same number of {} and {}. What is the least number of packs "
            "of each that {} must buy?").format(
        sentence_case(x), p["a"], sentence_case(y), p["b"], p["name"], x, y, p["name"])
    return {"prompt": Content(text), "answer": pack_answer(p, total),
            "answer_display": Content("{} packs of {} and {} packs of {}".format(
                total // p["a"], x, total // p["b"], y))}


def solve_packs(p, sympy):
    return pack_answer(p, lcm_by_search([p["a"], p["b"]]))


# ------------------------------------------------------------ registry

CONTEXTS_BY_OPERATION = {
    "hcf": {
        "ribbons2": Context(2, frozenset({"context", "a", "b"}),
                            lambda rng: build_ribbons(rng, 2), check_ribbons,
                            parts_ribbons, solve_ribbons),
        "ribbons3": Context(3, frozenset({"context", "a", "b", "c"}),
                            lambda rng: build_ribbons(rng, 3), check_ribbons,
                            parts_ribbons, solve_ribbons),
        "bags": Context(4, frozenset({"context", "name", "items", "a", "b"}),
                        build_bags, check_bags, parts_bags, solve_bags),
    },
    "lcm": {
        "buses": Context(2, frozenset({"context", "a", "b", "start"}),
                         build_buses, check_buses, parts_buses, solve_buses),
        "lights": Context(3, frozenset({"context", "a", "b", "c"}),
                          build_lights, check_lights, parts_lights, solve_lights),
        "packs": Context(4, frozenset({"context", "name", "items", "a", "b"}),
                         build_packs, check_packs, parts_packs, solve_packs),
    },
}


def generate(generator, context):
    contexts = CONTEXTS_BY_OPERATION[generator.operation]
    return worded.generate(generator, context, contexts, MARKS, WORKING_LINES)


def validate(generator, q):
    contexts = CONTEXTS_BY_OPERATION[generator.operation]
    return worded.validate(generator, q, contexts, MARKS, WORKING_LINES)


def validate_independently(generator, q):
    spec = CONTEXTS_BY_OPERATION[generator.operation][q.parameters["context"]]
    require(spec.solve(q.parameters, None) == q.answer, "Independent search disagrees")
    return True