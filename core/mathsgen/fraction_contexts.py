"""Worded contexts for the fraction families, keyed by generator ID.

number.fractions.addition        L2/L3 fraction left over; L4 how many are left
number.fractions.multiplication  L2 fraction of a fraction; L3 batches; L4 rug area
number.fractions.division        L2 shared equally; L3 how many pieces; L4 shelves
number.fractions.mixed_numbers   L2/L3 distances or ribbon; L4 paint coverage

Fractions are stored as canonical rational_text strings and shown with rich
maths runs. check() uses Fractions; solve() recomputes with SymPy rationals.
"""
from fractions import Fraction
from math import gcd

from .core import Content, rational_tex, rational_text, require
from . import worded
from .worded import (Context, NAMES, distinct_names, exact, integers, quantity,
                     rich_prompt, whole)
from .mixed_numbers import mixed_text


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {2: 0.4, 3: 0.4, 4: 0.5}
MARKS = {2: 3, 3: 3, 4: 4}
WORKING_LINES = {2: 5, 3: 5, 4: 6}

SPLIT = {
    "pizza": ("{first} eats ", " of a pizza. {second} eats ", " of the same pizza.",
              "What fraction of the pizza is left?"),
    "garden": ("In a garden, ", " of the area is lawn and ", " is patio.",
               "The rest is flower beds. What fraction of the garden is flower beds?"),
    "travel": ("In a class, ", " of the students walk to school and ", " come by bus.",
               "The rest come by car. What fraction of the students come by car?"),
    "money": ("{first} spends ", " of their pocket money on clothes and ", " on food.",
              "What fraction of their pocket money is left?"),
}
COUNT = {
    "class": ("In a class of {n} students, ", " walk to school and ", " come by bus.",
              "The rest come by car. How many students come by car?"),
    "survey": ("{n} people were asked to name their favourite sport. ",
               " chose football and ", " chose tennis.",
               "The rest chose swimming. How many people chose swimming?"),
    "library": ("A library shelf holds {n} books. ", " are novels and ", " are comics.",
                "The rest are poetry books. How many poetry books are there?"),
}
PART_OF_PART = {
    "school": ("", " of the students in a school are girls. ", " of the girls play football.",
               "What fraction of all the students are girls who play football?"),
    "cars": ("", " of the cars in a car park are red. ", " of the red cars are electric.",
             "What fraction of all the cars are red electric cars?"),
    "garden": ("", " of a garden is planted with flowers. ", " of the flowers are roses.",
               "What fraction of the garden is planted with roses?"),
}
BATCHES = {
    "sugar": ("A recipe uses ", " of a cup of sugar for one batch of biscuits.",
              "{first} makes {n} batches. How many cups of sugar does {first} use?", "cups"),
    "ribbon": ("Each bow uses ", " m of ribbon.",
               "{first} makes {n} bows. How many metres of ribbon does {first} use?", "m"),
}
SHARES = {
    "cake": ("", " of a cake is shared equally between {n} people.",
             "What fraction of the whole cake does each person get?"),
    "pizza": ("", " of a pizza is shared equally between {n} friends.",
              "What fraction of the whole pizza does each friend get?"),
}
PIECES = {
    "ribbon": ("A ribbon is {n} m long. It is cut into pieces that are each ", " m long.",
               "How many pieces are there?", "pieces"),
    "juice": ("A jug holds {n} litres of juice. Each glass holds ", " of a litre.",
              "How many glasses can be filled?", "glasses"),
}
# operation: (start, middle, end, question, unit)
MIXED_STORIES = {
    "add": ("{first} walks ", " km in the morning and ", " km in the afternoon.",
            "How far does {first} walk altogether?", "km"),
    "subtract": ("A ribbon is ", " m long. {first} cuts off ", " m.",
                 "How much ribbon is left?", "m"),
}
COPRIME_PAIRS = tuple((a, b) for a in range(2, 10) for b in range(a + 1, 13)
                      if gcd(a, b) == 1 and a * b <= 72)
MIXED_PAIRS = ((2, 3), (3, 4), (4, 6), (2, 5), (3, 5), (4, 5), (6, 8))


# ------------------------------------------------------------ helpers

def frac(value):
    value = Fraction(value)
    return (rational_tex(value), rational_text(value))


def mixed(value):
    value = Fraction(value)
    return (mixed_text(value, True), mixed_text(value))


def fraction_value(p, key):
    require(isinstance(p[key], str), "Fractions are stored as text")
    value = Fraction(p[key])
    require(p[key] == rational_text(value), "Non-canonical fraction")
    return value


def proper_value(p, key, max_denominator=12):
    value = fraction_value(p, key)
    require(0 < value < 1 and 2 <= value.denominator <= max_denominator, "Proper fraction")
    return value


def mixed_value(p, key, max_whole, max_denominator):
    value = fraction_value(p, key)
    require(1 < value < max_whole + 1 and 2 <= value.denominator <= max_denominator,
            "Mixed number bounds")
    return value


def proper(rng, denominator):
    numerator = rng.choice([n for n in range(1, denominator) if gcd(n, denominator) == 1])
    return Fraction(numerator, denominator)


def mixed_number(rng, wholes, denominators):
    return rng.randint(*wholes) + proper(rng, rng.choice(denominators))


def rational_answer(value):
    return {"kind": "rational", "value": rational_text(exact(value))}


def fraction_display(value, unit=""):
    value = exact(value)
    if unit:
        return Content("{} {}".format(mixed_text(value), unit))
    return Content(mixed_text(value), mixed_text(value, True))


def story(p, table, first_piece, second_piece=None):
    """Two-sentence prompt: a story sentence with maths pieces, then a question."""
    parts = table[p["scenario"]]
    fields = dict(p)
    if second_piece is None:
        start, end, question = parts[:3]
        sentence = (start.format(**fields), first_piece, end.format(**fields))
    else:
        start, middle, end, question = parts[:4]
        sentence = (start.format(**fields), first_piece, middle.format(**fields),
                    second_piece, end.format(**fields))
    return rich_prompt(sentence, (question.format(**fields),))


# ------------------------------------------------- addition: what is left

SPLIT_LEVEL = {"split_nested": 2, "split_coprime": 3, "split_count": 4}


def build_split(rng, name):
    if name == "split_nested":
        d1 = rng.choice((2, 3, 4, 5, 6))
        d2 = d1 * rng.choice((2, 3))
    else:
        d1, d2 = rng.choice(COPRIME_PAIRS)
    a, b = proper(rng, d1), proper(rng, d2)
    if rng.random() < 0.5:
        a, b = b, a
    p = {"context": name, "a": rational_text(a), "b": rational_text(b)}
    if name == "split_count":
        common = d1 * d2 // gcd(d1, d2)
        p["scenario"] = rng.choice(sorted(COUNT))
        p["n"] = common * rng.randint(1, max(1, 120 // common))
    else:
        p["scenario"] = rng.choice(sorted(SPLIT))
        p["first"], p["second"] = rng.sample(NAMES, 2)
    return p


def check_split(p):
    a, b = proper_value(p, "a"), proper_value(p, "b")
    small, large = sorted((a.denominator, b.denominator))
    require(small != large, "Different denominators")
    if p["context"] == "split_nested":
        require(large % small == 0, "One denominator divides the other")
    else:
        require((small, large) in COPRIME_PAIRS, "Coprime denominators")
    rest = 1 - a - b
    require(rest > 0, "Something must be left")
    if p["context"] == "split_count":
        require(p["scenario"] in COUNT, "Unknown scenario")
        integers(p, "n")
        require(12 <= p["n"] <= 120, "Group size")
        for part in (a, b):
            whole(p["n"] * part, 1, p["n"], "Each group must be whole")
        return whole(p["n"] * rest, 1, p["n"], "The rest must be whole")
    require(p["scenario"] in SPLIT, "Unknown scenario")
    distinct_names(p["first"], p["second"])
    return rest


def split_answer(p, rest):
    if p["context"] == "split_count":
        return quantity(rest, "")
    return rational_answer(rest)


def parts_split(p):
    rest = check_split(p)
    table = COUNT if p["context"] == "split_count" else SPLIT
    display = Content(str(rest)) if p["context"] == "split_count" else fraction_display(rest)
    return {"prompt": story(p, table, frac(p["a"]), frac(p["b"])),
            "answer": split_answer(p, rest), "answer_display": display}


def solve_split(p, sympy):
    R = sympy.Rational
    rest = 1 - R(p["a"]) - R(p["b"])
    if p["context"] == "split_count":
        rest = p["n"] * rest
    return split_answer(p, rest)


# ------------------------------------------- multiplication contexts

def build_part_of_part(rng):
    return {"context": "part_of_part", "scenario": rng.choice(sorted(PART_OF_PART)),
            "a": rational_text(proper(rng, rng.randint(2, 9))),
            "b": rational_text(proper(rng, rng.randint(2, 9)))}


def check_part_of_part(p):
    require(p["scenario"] in PART_OF_PART, "Unknown scenario")
    return proper_value(p, "a", 9) * proper_value(p, "b", 9)


def parts_part_of_part(p):
    value = check_part_of_part(p)
    return {"prompt": story(p, PART_OF_PART, frac(p["a"]), frac(p["b"])),
            "answer": rational_answer(value), "answer_display": fraction_display(value)}


def solve_part_of_part(p, sympy):
    return rational_answer(sympy.Rational(p["a"]) * sympy.Rational(p["b"]))


def build_batches(rng):
    return {"context": "batches", "scenario": rng.choice(sorted(BATCHES)),
            "first": rng.choice(NAMES), "f": rational_text(proper(rng, rng.randint(2, 9))),
            "n": rng.randint(2, 12)}


def check_batches(p):
    require(p["scenario"] in BATCHES, "Unknown scenario")
    distinct_names(p["first"])
    integers(p, "n")
    require(2 <= p["n"] <= 12, "Batch count")
    value = proper_value(p, "f", 9) * p["n"]
    require(value.denominator > 1, "Keep a fractional answer")
    return value


def parts_batches(p):
    value = check_batches(p)
    return {"prompt": story(p, BATCHES, frac(p["f"])), "answer": rational_answer(value),
            "answer_display": fraction_display(value, BATCHES[p["scenario"]][3])}


def solve_batches(p, sympy):
    return rational_answer(sum([sympy.Rational(p["f"])] * p["n"]))


def build_rug(rng):
    return {"context": "rug",
            "a": rational_text(mixed_number(rng, (1, 4), (2, 3, 4, 5))),
            "b": rational_text(mixed_number(rng, (1, 3), (2, 3, 4, 5)))}


def check_rug(p):
    area = mixed_value(p, "a", 4, 5) * mixed_value(p, "b", 3, 5)
    require(area <= 30, "Area bounds")
    return area


def parts_rug(p):
    area = check_rug(p)
    prompt = rich_prompt(("A rectangular rug is ", mixed(p["a"]), " m long and ",
                          mixed(p["b"]), " m wide."), ("Work out the area of the rug.",))
    return {"prompt": prompt, "answer": rational_answer(area),
            "answer_display": fraction_display(area, "m²")}


def solve_rug(p, sympy):
    return rational_answer(sympy.Rational(p["a"]) * sympy.Rational(p["b"]))


# ------------------------------------------------- division contexts

def build_share(rng):
    return {"context": "share_cake", "scenario": rng.choice(sorted(SHARES)),
            "a": rational_text(proper(rng, rng.randint(2, 9))), "n": rng.randint(2, 6)}


def check_share(p):
    require(p["scenario"] in SHARES, "Unknown scenario")
    integers(p, "n")
    require(2 <= p["n"] <= 6, "Number of people")
    return proper_value(p, "a", 9) / p["n"]


def parts_share(p):
    value = check_share(p)
    return {"prompt": story(p, SHARES, frac(p["a"])), "answer": rational_answer(value),
            "answer_display": fraction_display(value)}


def solve_share(p, sympy):
    x = sympy.Symbol("x")
    (value,) = worded.sympy_solve(sympy, [sympy.Eq(p["n"] * x, sympy.Rational(p["a"]))], [x])
    return rational_answer(value)


def build_pieces(rng):
    f = proper(rng, rng.randint(2, 9))
    return {"context": "pieces", "scenario": rng.choice(sorted(PIECES)),
            "f": rational_text(f), "n": f.numerator * rng.randint(1, 6)}


def check_pieces(p):
    require(p["scenario"] in PIECES, "Unknown scenario")
    integers(p, "n")
    require(2 <= p["n"] <= 20, "Total bounds")
    return whole(p["n"] / proper_value(p, "f", 9), 2, 60, "Pieces must be whole")


def parts_pieces(p):
    count = check_pieces(p)
    unit = PIECES[p["scenario"]][3]
    return {"prompt": story(p, PIECES, frac(p["f"])), "answer": quantity(count, unit),
            "answer_display": Content("{} {}".format(count, unit))}


def solve_pieces(p, sympy):
    count = sympy.Integer(p["n"]) / sympy.Rational(p["f"])
    return quantity(count, PIECES[p["scenario"]][3])


def build_shelves(rng):
    shelf = mixed_number(rng, (1, 2), (2, 3, 4))
    return {"context": "shelves", "shelf": rational_text(shelf),
            "length": rational_text(shelf * rng.randint(2, 8))}


def check_shelves(p):
    shelf = mixed_value(p, "shelf", 2, 4)
    length = fraction_value(p, "length")
    require(0 < length <= 24, "Plank length bounds")
    return whole(length / shelf, 2, 8, "Shelves must be a whole number")


def parts_shelves(p):
    count = check_shelves(p)
    prompt = rich_prompt(("A plank of wood is ", mixed(p["length"]),
                          " m long. It is cut into shelves that are each ",
                          mixed(p["shelf"]), " m long."),
                         ("How many shelves are there?",))
    return {"prompt": prompt, "answer": quantity(count, "shelves"),
            "answer_display": Content("{} shelves".format(count))}


def solve_shelves(p, sympy):
    k = sympy.Symbol("k")
    (count,) = worded.sympy_solve(sympy, [sympy.Eq(k * sympy.Rational(p["shelf"]),
                                                   sympy.Rational(p["length"]))], [k])
    return quantity(count, "shelves")


# ------------------------------------------------- mixed-number contexts

def build_mixed_sum(rng, name):
    operation = rng.choice(("add", "subtract"))
    if name == "mixed_same":
        d = rng.choice((3, 4, 5, 6, 8))
        dens = (d, d)
    else:
        dens = rng.choice(MIXED_PAIRS)
    a = rng.randint(2, 6) + proper(rng, dens[0])
    b = rng.randint(1, 4) + proper(rng, dens[1])
    return {"context": name, "operation": operation, "first": rng.choice(NAMES),
            "a": rational_text(a), "b": rational_text(b)}


def check_mixed_sum(p):
    require(p["operation"] in MIXED_STORIES, "Unknown operation")
    distinct_names(p["first"])
    a, b = mixed_value(p, "a", 6, 8), mixed_value(p, "b", 4, 8)
    if p["context"] == "mixed_same":
        require(a.denominator == b.denominator, "Same denominators")
    else:
        require(tuple(sorted((a.denominator, b.denominator))) in MIXED_PAIRS,
                "Different denominators")
    result = a + b if p["operation"] == "add" else a - b
    require(result > 0, "Result must be positive")
    return result


def parts_mixed_sum(p):
    result = check_mixed_sum(p)
    start, middle, end, question, unit = MIXED_STORIES[p["operation"]]
    fields = dict(p)
    prompt = rich_prompt((start.format(**fields), mixed(p["a"]), middle.format(**fields),
                          mixed(p["b"]), end.format(**fields)), (question.format(**fields),))
    return {"prompt": prompt, "answer": rational_answer(result),
            "answer_display": fraction_display(result, unit)}


def solve_mixed_sum(p, sympy):
    R = sympy.Rational
    x = sympy.Symbol("x")
    if p["operation"] == "add":
        equation = sympy.Eq(x - R(p["b"]), R(p["a"]))
    else:
        equation = sympy.Eq(x + R(p["b"]), R(p["a"]))
    (result,) = worded.sympy_solve(sympy, [equation], [x])
    return rational_answer(result)


def build_paint(rng):
    return {"context": "paint",
            "a": rational_text(mixed_number(rng, (3, 8), (2, 3, 4, 5))),
            "b": rational_text(mixed_number(rng, (1, 4), (2, 3, 4)))}


def check_paint(p):
    value = mixed_value(p, "a", 8, 5) * mixed_value(p, "b", 4, 4)
    require(value <= 60, "Coverage bounds")
    return value


def parts_paint(p):
    value = check_paint(p)
    prompt = rich_prompt(("One tin of paint covers ", mixed(p["a"]), " m² of wall."),
                         ("How much wall can ", mixed(p["b"]), " tins of paint cover?"))
    return {"prompt": prompt, "answer": rational_answer(value),
            "answer_display": fraction_display(value, "m²")}


def solve_paint(p, sympy):
    return rational_answer(sympy.Rational(p["a"]) * sympy.Rational(p["b"]))


# ------------------------------------------------------------ registry

MIXED_SUM_KEYS = frozenset({"context", "operation", "first", "a", "b"})

CONTEXTS_BY_GENERATOR = {
    "number.fractions.addition": {
        "split_nested": Context(2, frozenset({"context", "scenario", "first", "second", "a", "b"}),
                                lambda rng: build_split(rng, "split_nested"),
                                check_split, parts_split, solve_split),
        "split_coprime": Context(3, frozenset({"context", "scenario", "first", "second", "a", "b"}),
                                 lambda rng: build_split(rng, "split_coprime"),
                                 check_split, parts_split, solve_split),
        "split_count": Context(4, frozenset({"context", "scenario", "n", "a", "b"}),
                               lambda rng: build_split(rng, "split_count"),
                               check_split, parts_split, solve_split),
    },
    "number.fractions.multiplication": {
        "part_of_part": Context(2, frozenset({"context", "scenario", "a", "b"}),
                                build_part_of_part, check_part_of_part, parts_part_of_part,
                                solve_part_of_part),
        "batches": Context(3, frozenset({"context", "scenario", "first", "f", "n"}),
                           build_batches, check_batches, parts_batches, solve_batches),
        "rug": Context(4, frozenset({"context", "a", "b"}),
                       build_rug, check_rug, parts_rug, solve_rug),
    },
    "number.fractions.division": {
        "share_cake": Context(2, frozenset({"context", "scenario", "a", "n"}),
                              build_share, check_share, parts_share, solve_share),
        "pieces": Context(3, frozenset({"context", "scenario", "f", "n"}),
                          build_pieces, check_pieces, parts_pieces, solve_pieces),
        "shelves": Context(4, frozenset({"context", "shelf", "length"}),
                           build_shelves, check_shelves, parts_shelves, solve_shelves),
    },
    "number.fractions.mixed_numbers": {
        "mixed_same": Context(2, MIXED_SUM_KEYS, lambda rng: build_mixed_sum(rng, "mixed_same"),
                              check_mixed_sum, parts_mixed_sum, solve_mixed_sum),
        "mixed_different": Context(3, MIXED_SUM_KEYS,
                                   lambda rng: build_mixed_sum(rng, "mixed_different"),
                                   check_mixed_sum, parts_mixed_sum, solve_mixed_sum),
        "paint": Context(4, frozenset({"context", "a", "b"}),
                         build_paint, check_paint, parts_paint, solve_paint),
    },
}


def contexts_for(generator):
    return CONTEXTS_BY_GENERATOR[generator.info.id]


def generate(generator, context):
    return worded.generate(generator, context, contexts_for(generator), MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, contexts_for(generator), MARKS, WORKING_LINES)


def validate_independently(generator, q):
    import sympy
    spec = contexts_for(generator)[q.parameters["context"]]
    require(spec.solve(q.parameters, sympy) == q.answer, "Independent fraction check disagrees")
    return True