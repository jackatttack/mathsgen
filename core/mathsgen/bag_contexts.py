"""Applied forms for probability.basics.events: counting objects in a bag.

L2 bag_total  two colours; one count and its probability give the other count
L3 bag_ratio  three colours; one count and its probability, the other two in
              a ratio: find one of them
L4 bag_added  two colours in a ratio; more of one colour are added and the
              new probability is given: find how many of the other colour

Bare questions store an integer "context" (which event wording), so an
applied question is recognised by is_applied(): its context names one of
the CONTEXTS below. check() works with exact Fractions; validate_
independently() solves the probability equation with SymPy.
"""
from fractions import Fraction

from .core import Content, require
from . import worded
from .worded import Context, quantity


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {2: 0.3, 3: 0.35, 4: 0.35}
MARKS = {2: 2, 3: 3, 4: 4}
WORKING_LINES = {2: 3, 3: 5, 4: 6}

COLOURS = ("red", "blue", "yellow", "green", "white", "black")
OBJECTS = {"discs": "disc", "counters": "counter", "beads": "bead", "marbles": "marble"}
PROBABILITIES = (10, 12, 15, 16, 20, 24, 25, 30, 35, 40, 45)   # in hundredths
RATIOS = ((1, 2), (2, 1), (2, 3), (3, 2), (3, 4), (4, 3), (5, 4), (4, 5), (1, 3), (3, 1))
NEW_PROBABILITIES = ((1, 2), (1, 3), (2, 3), (2, 5), (3, 5))


def context_share(level):
    return CONTEXT_SHARE.get(level, 0.0)


def is_applied(question):
    p = question.parameters
    return isinstance(p, dict) and isinstance(p.get("context"), str) \
        and p.get("context") in CONTEXTS


# ------------------------------------------------------------------ helpers

def decimal_text(hundredths):
    return "0.{:02d}".format(hundredths).rstrip("0")


def colours(p, count):
    chosen = p["colours"]
    require(isinstance(chosen, list) and len(chosen) == count and len(set(chosen)) == count
            and all(colour in COLOURS for colour in chosen), "Colours")
    return chosen


def objects(p):
    require(p["object"] in OBJECTS, "Unknown object")
    return p["object"], OBJECTS[p["object"]]


def whole_in(value, low, high, message):
    require(type(value) is int and low <= value <= high, message)
    return value


def count_answer(value, colour, plural):
    return {"answer": quantity(value, colour + " " + plural),
            "answer_display": Content("{} {} {}".format(value, colour, plural))}


def total_from(count, hundredths):
    total = Fraction(count * 100, hundredths)
    require(total.denominator == 1 and 20 <= total <= 300, "Total out of bounds")
    return int(total)


# ---------------------------------------------------- L2: the other colour

def build_total(rng):
    h = rng.choice(PROBABILITIES)
    total = rng.choice([t for t in range(20, 201) if t * h % 100 == 0])
    return {"context": "bag_total", "object": rng.choice(sorted(OBJECTS)),
            "colours": rng.sample(COLOURS, 2), "count": total * h // 100, "hundredths": h}


def check_total(p):
    colours(p, 2)
    objects(p)
    require(p["hundredths"] in PROBABILITIES, "Unknown probability")
    count = whole_in(p["count"], 1, 200, "Count out of bounds")
    other = total_from(count, p["hundredths"]) - count
    require(other > 0, "The other colour must be present")
    return other


def parts_total(p):
    other = check_total(p)
    first, second = p["colours"]
    plural, single = objects(p)
    text = ("A bag contains only {a} and {b} {plural}. There are {n} {a} {plural} in the "
            "bag. The probability of taking a {a} {single} at random is {prob}. How many "
            "{b} {plural} are in the bag?").format(
        a=first, b=second, plural=plural, single=single, n=p["count"],
        prob=decimal_text(p["hundredths"]))
    return dict(prompt=Content(text), **count_answer(other, second, plural))


# ------------------------------------------------- L3: three colours, a ratio

def build_ratio(rng):
    h = rng.choice(PROBABILITIES)
    m, n = rng.choice(RATIOS)
    totals = [t for t in range(25, 301)
              if t * h % 100 == 0 and (t - t * h // 100) % (m + n) == 0]
    total = rng.choice(totals)
    return {"context": "bag_ratio", "object": rng.choice(sorted(OBJECTS)),
            "colours": rng.sample(COLOURS, 3), "count": total * h // 100,
            "hundredths": h, "ratio": [m, n]}


def check_ratio(p):
    colours(p, 3)
    objects(p)
    require(p["hundredths"] in PROBABILITIES, "Unknown probability")
    require(isinstance(p["ratio"], list) and tuple(p["ratio"]) in RATIOS, "Unknown ratio")
    count = whole_in(p["count"], 1, 200, "Count out of bounds")
    rest = total_from(count, p["hundredths"]) - count
    m, n = p["ratio"]
    require(rest > 0 and rest % (m + n) == 0, "The ratio must share the rest exactly")
    return m * rest // (m + n)


def parts_ratio(p):
    first_count = check_ratio(p)
    known, first, second = p["colours"]
    plural, single = objects(p)
    m, n = p["ratio"]
    text = ("There are only {a}, {b} and {k} {plural} in a bag. There are {n} {k} "
            "{plural}. A {single} is taken at random. The probability that it is {k} is "
            "{prob}. The number of {a} {plural} : the number of {b} {plural} = {m} : {r}. "
            "Work out the number of {a} {plural} in the bag.").format(
        a=first, b=second, k=known, plural=plural, single=single, n=p["count"],
        prob=decimal_text(p["hundredths"]), m=m, r=n)
    return dict(prompt=Content(text), **count_answer(first_count, first, plural))


# ----------------------------------------- L4: more added, a new probability

def build_added(rng):
    a, b = rng.choice(RATIOS)
    top, bottom = rng.choice(NEW_PROBABILITIES)
    x = rng.randint(2, 12)
    numerator = x * (top * (a + b) - bottom * a)
    added = numerator // (bottom - top) if numerator % (bottom - top) == 0 else -1
    return {"context": "bag_added", "object": rng.choice(sorted(OBJECTS)),
            "colours": rng.sample(COLOURS, 2), "ratio": [a, b], "added": added,
            "new": [top, bottom]}


def check_added(p):
    colours(p, 2)
    objects(p)
    require(isinstance(p["ratio"], list) and tuple(p["ratio"]) in RATIOS, "Unknown ratio")
    require(isinstance(p["new"], list) and tuple(p["new"]) in NEW_PROBABILITIES,
            "Unknown new probability")
    added = whole_in(p["added"], 1, 60, "Added count out of bounds")
    a, b = p["ratio"]
    top, bottom = p["new"]
    divisor = top * (a + b) - bottom * a
    require(divisor > 0, "Adding must raise the probability to the new value")
    x = Fraction(added * (bottom - top), divisor)
    require(x.denominator == 1 and 2 <= x <= 20, "The bag must hold whole groups")
    return b * int(x)


def parts_added(p):
    others = check_added(p)
    first, second = p["colours"]
    plural, single = objects(p)
    a, b = p["ratio"]
    top, bottom = p["new"]
    text = ("A bag contains only {f} and {s} {plural}. The number of {f} {plural} : the "
            "number of {s} {plural} = {a} : {b}. {k} more {f} {plural} are put into the "
            "bag. The probability of taking a {f} {single} at random is now {t}/{u}. How "
            "many {s} {plural} are in the bag?").format(
        f=first, s=second, plural=plural, single=single, a=a, b=b, k=p["added"],
        t=top, u=bottom)
    return dict(prompt=Content(text), **count_answer(others, second, plural))


# ----------------------------------------------------------------- registry

CONTEXTS = {
    "bag_total": Context(
        2, frozenset({"context", "object", "colours", "count", "hundredths"}),
        build_total, check_total, parts_total, None),
    "bag_ratio": Context(
        3, frozenset({"context", "object", "colours", "count", "hundredths", "ratio"}),
        build_ratio, check_ratio, parts_ratio, None),
    "bag_added": Context(
        4, frozenset({"context", "object", "colours", "ratio", "added", "new"}),
        build_added, check_added, parts_added, None),
}


# ------------------------------------------------ generate and validate

def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    """Solve each bag's probability equation with SymPy."""
    import sympy
    p = q.parameters
    stated = sympy.Rational(q.answer["value"])
    total = sympy.Symbol("total", positive=True)
    if p["context"] in ("bag_total", "bag_ratio"):
        found = sympy.solve(sympy.Eq(p["count"] / total, sympy.Rational(p["hundredths"], 100)),
                            total)
        require(len(found) == 1, "Expected one total")
        rest = found[0] - p["count"]
        if p["context"] == "bag_total":
            expected = rest
        else:
            m, n = p["ratio"]
            expected = rest * sympy.Rational(m, m + n)
    else:
        a, b = p["ratio"]
        x = sympy.Symbol("x", positive=True)
        found = sympy.solve(sympy.Eq((a * x + p["added"]) / ((a + b) * x + p["added"]),
                                     sympy.Rational(*p["new"])), x)
        require(len(found) == 1, "Expected one group size")
        expected = b * found[0]
    require(expected == stated, "Independent count disagrees")
    return True