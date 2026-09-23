"""Worded contexts for ratio.simplifying and ratio.combining.three_part.

ratio.simplifying
  L1 a ratio from a two-way count     L2 a three-way count
  L3 ratio to fraction, fraction to ratio
  L4 mixed units: p : £, minutes : hours, g : kg, ml : litres
ratio.combining.three_part
  L2/L3 combine two ratios from a story   L4 combine, then a count from a total

check() works with exact integers and Fractions; solve() rebuilds each answer
independently with SymPy (normalising to one part, then clearing denominators).
"""
from fractions import Fraction
from functools import reduce
from math import gcd

from .core import Content, rational_tex, rational_text, require
from . import worded
from .worded import Context, integers, quantity, rich_prompt, whole
from .combine_ratios import permitted_shared_parts
from .rounding import decimal_text, terminates


# ------------------------------------------------------------ editable knobs

SHARES_BY_GENERATOR = {
    "ratio.simplifying": {1: 0.35, 2: 0.4, 3: 0.5, 4: 0.5},
    "ratio.combining.three_part": {2: 0.4, 3: 0.4, 4: 0.5},
}
MARKS = {1: 2, 2: 2, 3: 3, 4: 3}
WORKING_LINES = {1: 3, 2: 4, 3: 4, 4: 5}

PAIRS = {
    "class": ("In a class there are {a} boys and {b} girls.",
              "Write the ratio of boys to girls in its simplest form."),
    "garden": ("A garden centre has {a} roses and {b} tulips.",
               "Write the ratio of roses to tulips in its simplest form."),
    "club": ("A club has {a} adult members and {b} junior members.",
             "Write the ratio of adults to juniors in its simplest form."),
}
TRIPLES = {
    "counters": ("A bag contains {a} red, {b} blue and {c} green counters.",
                 "Write the ratio red : blue : green in its simplest form."),
    "votes": ("In a vote, {a} people chose pizza, {b} chose pasta and {c} chose curry.",
              "Write the ratio pizza : pasta : curry in its simplest form."),
}
RATIO_TO_FRACTION = {
    "club": ("The ratio of boys to girls in a club is {a} : {b}.",
             "What fraction of the club are girls?"),
    "paint": ("Blue paint and yellow paint are mixed in the ratio {a} : {b}.",
              "What fraction of the mixture is yellow paint?"),
}
FRACTION_TO_RATIO = {
    "club": (" of the members of a club are adults. The rest are children.",
             "Write the ratio adults : children in its simplest form."),
    "sweets": (" of the sweets in a bag are red. The rest are yellow.",
               "Write the ratio red : yellow in its simplest form."),
}
# units: (small unit, large unit, small units per large unit, step in small units)
UNITS = {
    "money": ("p", "£", 100, 5), "time": ("minutes", "hours", 60, 5),
    "mass": ("g", "kg", 1000, 50), "volume": ("ml", "litres", 1000, 50),
}
TRIOS = {
    "trip": ("On a school trip, the ratio of boys to girls is {a} : {b}. "
             "The ratio of girls to teachers is {c} : {d}.",
             ("boys", "girls", "teachers"), "people"),
    "sweets": ("In a bag of sweets, the ratio of red sweets to green sweets is {a} : {b}. "
               "The ratio of green sweets to yellow sweets is {c} : {d}.",
               ("red", "green", "yellow"), "sweets"),
    "cinema": ("At a cinema, the ratio of adults to teenagers is {a} : {b}. "
               "The ratio of teenagers to children is {c} : {d}.",
               ("adults", "teenagers", "children"), "people"),
}


# ------------------------------------------------------------ helpers

def simplified(parts):
    common = reduce(gcd, parts)
    return [part // common for part in parts]


def ratio_text(parts):
    return " : ".join(str(part) for part in parts)


def ratio_answer(parts):
    return {"kind": "ratio", "values": list(parts)}


def ratio_display(parts):
    text = ratio_text(parts)
    return Content(text, text)


def sympy_simplest(sympy, values):
    """Clear denominators and divide by the integer GCD, all in SymPy."""
    values = [sympy.Rational(v) for v in values]
    scale = sympy.ilcm(*[int(v.q) for v in values])
    integers_ = [int(v * scale) for v in values]
    common = sympy.igcd(*integers_)
    return [value // common for value in integers_]


# ------------------------------------------------ simplifying: L1 and L2

def build_count(rng, name):
    size = 2 if name == "pair_count" else 3
    parts = simplified(rng.sample(range(1, 11), size))
    multiplier = rng.randint(2, 12)
    table = PAIRS if size == 2 else TRIPLES
    p = {"context": name, "scenario": rng.choice(sorted(table))}
    for key, part in zip("abc", parts):
        p[key] = part * multiplier
    return p


def count_keys(p):
    return "a b" if p["context"] == "pair_count" else "a b c"


def check_count(p):
    names = count_keys(p)
    integers(p, names)
    table = PAIRS if p["context"] == "pair_count" else TRIPLES
    require(p["scenario"] in table, "Unknown scenario")
    values = [p[k] for k in names.split()]
    require(all(2 <= v <= 120 for v in values), "Count bounds")
    require(reduce(gcd, values) > 1, "The ratio must need simplifying")
    parts = simplified(values)
    require(all(part <= 10 for part in parts), "Simplest parts too large")
    return parts


def parts_count(p):
    parts = check_count(p)
    table = PAIRS if p["context"] == "pair_count" else TRIPLES
    story, question = table[p["scenario"]]
    return {"prompt": Content(story.format(**p) + " " + question),
            "answer": ratio_answer(parts), "answer_display": ratio_display(parts)}


def solve_count(p, sympy):
    return ratio_answer(sympy_simplest(sympy, [p[k] for k in count_keys(p).split()]))


# ------------------------------------------ simplifying: L3 conversions

def build_ratio_to_fraction(rng):
    a, b = simplified(rng.sample(range(1, 10), 2))
    return {"context": "ratio_to_fraction", "scenario": rng.choice(sorted(RATIO_TO_FRACTION)),
            "a": a, "b": b}


def check_ratio_to_fraction(p):
    integers(p, "a b")
    require(p["scenario"] in RATIO_TO_FRACTION, "Unknown scenario")
    require(1 <= p["a"] <= 9 and 1 <= p["b"] <= 9 and p["a"] != p["b"]
            and gcd(p["a"], p["b"]) == 1, "Simplified ratio")
    return Fraction(p["b"], p["a"] + p["b"])


def parts_ratio_to_fraction(p):
    value = check_ratio_to_fraction(p)
    story, question = RATIO_TO_FRACTION[p["scenario"]]
    return {"prompt": Content(story.format(**p) + " " + question),
            "answer": {"kind": "rational", "value": rational_text(value)},
            "answer_display": Content(rational_text(value), rational_tex(value))}


def solve_ratio_to_fraction(p, sympy):
    x = sympy.Symbol("x")
    # parts a : b means the second share is b/(a+b) of the total 1.
    (value,) = worded.sympy_solve(sympy, [sympy.Eq(x * (p["a"] + p["b"]), p["b"])], [x])
    return {"kind": "rational", "value": rational_text(value)}


def build_fraction_to_ratio(rng):
    denominator = rng.randint(3, 12)
    numerator = rng.choice([n for n in range(1, denominator) if gcd(n, denominator) == 1])
    return {"context": "fraction_to_ratio", "scenario": rng.choice(sorted(FRACTION_TO_RATIO)),
            "f": rational_text(Fraction(numerator, denominator))}


def check_fraction_to_ratio(p):
    require(p["scenario"] in FRACTION_TO_RATIO, "Unknown scenario")
    require(isinstance(p["f"], str), "Fraction stored as text")
    f = Fraction(p["f"])
    require(p["f"] == rational_text(f) and 0 < f < 1 and 3 <= f.denominator <= 12,
            "Proper fraction")
    return [f.numerator, f.denominator - f.numerator]


def parts_fraction_to_ratio(p):
    parts = check_fraction_to_ratio(p)
    rest, question = FRACTION_TO_RATIO[p["scenario"]]
    f = Fraction(p["f"])
    prompt = rich_prompt(((rational_tex(f), rational_text(f)), rest), (question,))
    return {"prompt": prompt, "answer": ratio_answer(parts),
            "answer_display": ratio_display(parts)}


def solve_fraction_to_ratio(p, sympy):
    f = sympy.Rational(p["f"])
    return ratio_answer(sympy_simplest(sympy, [f, 1 - f]))


# ------------------------------------------ simplifying: L4 mixed units

def large_text(p):
    small_unit, large_unit, factor, _ = UNITS[p["units"]]
    value = Fraction(p["large"])
    if p["units"] == "money":
        pence = int(value * 100)
        return "£{}.{:02d}".format(pence // 100, pence % 100)
    return "{} {}".format(decimal_text(value), large_unit)


def small_text(p):
    unit = UNITS[p["units"]][0]
    return "{}p".format(p["small"]) if p["units"] == "money" else "{} {}".format(p["small"], unit)


def build_mixed_units(rng):
    units = rng.choice(sorted(UNITS))
    _, _, factor, step = UNITS[units]
    s0, s1 = simplified(rng.sample(range(1, 11), 2))
    unit = step * rng.randint(1, 12)
    return {"context": "mixed_units", "units": units, "small": s0 * unit,
            "large": rational_text(Fraction(s1 * unit, factor)),
            "small_first": rng.random() < 0.5}


def check_mixed_units(p):
    integers(p, "small")
    require(p["units"] in UNITS, "Unknown units")
    require(type(p["small_first"]) is bool, "Order flag")
    _, _, factor, step = UNITS[p["units"]]
    require(isinstance(p["large"], str), "Large value stored as text")
    large = Fraction(p["large"])
    require(p["large"] == rational_text(large) and 0 < large < 10, "Large value bounds")
    require(terminates(large) and (large * 100).denominator == 1, "At most two decimal places")
    require(p["small"] >= step and p["small"] % step == 0, "Small value step")
    converted = whole(large * factor, 1, 10 ** 5, "Conversion must be whole")
    require(converted != p["small"], "The quantities must differ")
    parts = [p["small"], converted] if p["small_first"] else [converted, p["small"]]
    parts = simplified(parts)
    require(max(parts) <= 20, "Simplest parts too large")
    return parts


def parts_mixed_units(p):
    parts = check_mixed_units(p)
    shown = [small_text(p), large_text(p)]
    if not p["small_first"]:
        shown.reverse()
    text = "Write the ratio {} : {} in its simplest form.".format(*shown)
    return {"prompt": Content(text), "answer": ratio_answer(parts),
            "answer_display": ratio_display(parts)}


def solve_mixed_units(p, sympy):
    factor = UNITS[p["units"]][2]
    small = sympy.Integer(p["small"])
    large = sympy.Rational(p["large"]) * factor
    values = [small, large] if p["small_first"] else [large, small]
    return ratio_answer(sympy_simplest(sympy, values))


# ------------------------------------------------------------ combining

COMBINE_LEVEL = {"combine_story2": 2, "combine_story3": 3, "combine_total": 4}


def build_combine(rng, name):
    level = min(COMBINE_LEVEL[name], 3)
    b, c = rng.choice(permitted_shared_parts(level))
    a = rng.choice([n for n in range(1, 13) if gcd(n, b) == 1])
    d = rng.choice([n for n in range(1, 13) if gcd(n, c) == 1])
    p = {"context": name, "story": rng.choice(sorted(TRIOS)), "a": a, "b": b, "c": c, "d": d}
    if name == "combine_total":
        common = b * c // gcd(b, c)
        parts = simplified([a * common // b, common, d * common // c])
        p["total"] = sum(parts) * rng.randint(2, 6)
    return p


def check_combine(p):
    integers(p, "a b c d")
    require(p["story"] in TRIOS, "Unknown story")
    level = min(COMBINE_LEVEL[p["context"]], 3)
    a, b, c, d = p["a"], p["b"], p["c"], p["d"]
    require((b, c) in permitted_shared_parts(level), "Scaling structure")
    require(1 <= a <= 12 and 1 <= d <= 12 and gcd(a, b) == 1 and gcd(c, d) == 1,
            "Input ratios must be simplified")
    common = b * c // gcd(b, c)
    parts = simplified([a * common // b, common, d * common // c])
    require(max(parts) <= 144, "Parts too large")
    if p["context"] == "combine_total":
        integers(p, "total")
        multiple = whole(Fraction(p["total"], sum(parts)), 2, 6, "Total must be a multiple")
        return parts, multiple * parts[2]
    return parts, None


def parts_combine(p):
    parts, count = check_combine(p)
    story, names, noun = TRIOS[p["story"]]
    intro = story.format(**p)
    if count is None:
        question = "Write the ratio {} : {} : {} in its simplest form.".format(*names)
        return {"prompt": Content(intro + " " + question), "answer": ratio_answer(parts),
                "answer_display": ratio_display(parts)}
    question = "There are {} {} altogether. How many {} are there?".format(
        p["total"], noun, names[2])
    return {"prompt": Content(intro + " " + question), "answer": quantity(count, names[2]),
            "answer_display": Content("{} {}".format(count, names[2]))}


def solve_combine(p, sympy):
    # Normalise so the shared quantity is 1, then clear denominators.
    first = sympy.Rational(p["a"], p["b"])
    third = sympy.Rational(p["d"], p["c"])
    parts = sympy_simplest(sympy, [first, 1, third])
    if p["context"] == "combine_total":
        names = TRIOS[p["story"]][1]
        return quantity(p["total"] * third / (first + 1 + third), names[2])
    return ratio_answer(parts)


# ------------------------------------------------------------ registry

CONTEXTS_BY_GENERATOR = {
    "ratio.simplifying": {
        "pair_count": Context(1, frozenset({"context", "scenario", "a", "b"}),
                              lambda rng: build_count(rng, "pair_count"),
                              check_count, parts_count, solve_count),
        "triple_count": Context(2, frozenset({"context", "scenario", "a", "b", "c"}),
                                lambda rng: build_count(rng, "triple_count"),
                                check_count, parts_count, solve_count),
        "ratio_to_fraction": Context(3, frozenset({"context", "scenario", "a", "b"}),
                                     build_ratio_to_fraction, check_ratio_to_fraction,
                                     parts_ratio_to_fraction, solve_ratio_to_fraction),
        "fraction_to_ratio": Context(3, frozenset({"context", "scenario", "f"}),
                                     build_fraction_to_ratio, check_fraction_to_ratio,
                                     parts_fraction_to_ratio, solve_fraction_to_ratio),
        "mixed_units": Context(4, frozenset({"context", "units", "small", "large", "small_first"}),
                               build_mixed_units, check_mixed_units, parts_mixed_units,
                               solve_mixed_units),
    },
    "ratio.combining.three_part": {
        "combine_story2": Context(2, frozenset({"context", "story", "a", "b", "c", "d"}),
                                  lambda rng: build_combine(rng, "combine_story2"),
                                  check_combine, parts_combine, solve_combine),
        "combine_story3": Context(3, frozenset({"context", "story", "a", "b", "c", "d"}),
                                  lambda rng: build_combine(rng, "combine_story3"),
                                  check_combine, parts_combine, solve_combine),
        "combine_total": Context(4, frozenset({"context", "story", "a", "b", "c", "d", "total"}),
                                 lambda rng: build_combine(rng, "combine_total"),
                                 check_combine, parts_combine, solve_combine),
    },
}


def share(generator, level):
    return SHARES_BY_GENERATOR[generator.info.id].get(level, 0.0)


def contexts_for(generator):
    return CONTEXTS_BY_GENERATOR[generator.info.id]


def generate(generator, context):
    return worded.generate(generator, context, contexts_for(generator), MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, contexts_for(generator), MARKS, WORKING_LINES)


def validate_independently(generator, q):
    import sympy
    spec = contexts_for(generator)[q.parameters["context"]]
    require(spec.solve(q.parameters, sympy) == q.answer, "Independent ratio check disagrees")
    return True