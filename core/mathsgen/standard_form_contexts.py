"""Worded contexts for number.standard_form.calculations.

L1 multiply in context (no renormalising)   L2 divide in context
L3 multiply or divide, then renormalise     L4 add or subtract distances or masses

Operands reuse the bare family's construction and its answer_for(), so the
level rules are identical; each story fixes the operation, sensible
exponent ranges and a unit. solve() recomputes the exact value in SymPy.
"""
from .core import Content, require
from . import worded
from .worded import Context, integers, rich_prompt
from .standard_form import standard_form_text


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {1: 0.4, 2: 0.4, 3: 0.5, 4: 0.5}
MARKS = {1: 2, 2: 2, 3: 3, 4: 3}
WORKING_LINES = {1: 3, 2: 3, 3: 4, 4: 4}

X, Y = "{x}", "{y}"

# story: (operation, sentence pieces, question, unit, first exponents, second exponents)
STORIES = {
    "virus": ("multiply", ("A virus is ", X, " m long. ", Y,
                           " of these viruses are placed end to end in a line."),
              "How long is the line?", "m", (-8, -6), (3, 5)),
    "signal": ("multiply", ("A signal travels ", X, " km every second."),
               "How far does it travel in {y} seconds?", "km", (4, 6), (1, 3)),
    "rice": ("multiply", ("A grain of rice has a mass of ", X, " kg. A sack contains ", Y,
                          " grains of rice."),
             "What is the total mass of the rice?", "kg", (-6, -4), (4, 6)),
    "density": ("divide", ("A country has a population of ", X,
                           " people and an area of ", Y, " km²."),
                "Work out the average number of people per km².", "", (6, 9), (4, 6)),
    "computer": ("divide", ("A computer does ", X, " calculations in ", Y, " seconds."),
                 "How many calculations does it do each second?", "", (8, 11), (1, 3)),
    "planets": ("subtract", ("Planet A is ", X, " km from its star. Planet B is ", Y,
                             " km from the same star."),
                "How much further from the star is Planet A than Planet B?", "km",
                (5, 9), None),
    "cargo": ("add", ("A ship carries ", X, " kg of grain and ", Y, " kg of steel."),
              "What is the total mass of the cargo?", "kg", (4, 7), None),
}

# context name: (level, story)
FORMS = {
    "virus": (1, "virus"), "signal": (1, "signal"), "rice": (1, "rice"),
    "density": (2, "density"), "computer": (2, "computer"),
    "rice_renormalise": (3, "rice"), "computer_renormalise": (3, "computer"),
    "planets": (4, "planets"), "cargo": (4, "cargo"),
}

KEYS = frozenset({"context", "operation", "first_digits", "first_exponent",
                  "second_digits", "second_exponent"})


def digits_ok(digits):
    return (isinstance(digits, str) and 1 <= len(digits) <= 2 and digits.isdigit()
            and digits[0] != "0" and digits[-1] != "0")


def make_digits(rng, length):
    if length == 1:
        return str(rng.randint(1, 9))
    return str(rng.randint(1, 9)) + str(rng.randint(1, 9))


def build(rng, name):
    level, story = FORMS[name]
    operation, _, _, _, first_range, second_range = STORIES[story]
    p = {"context": name, "operation": operation}
    if level == 4:
        gap = rng.randint(1, 2)
        base = rng.randint(*first_range)
        p.update(first_digits=make_digits(rng, 2), first_exponent=base + gap,
                 second_digits=make_digits(rng, 2), second_exponent=base)
        return p
    lengths = (2, 2) if level == 3 else (rng.choice((1, 2)), rng.choice((1, 2)))
    p.update(first_digits=make_digits(rng, lengths[0]),
             first_exponent=rng.randint(*first_range),
             second_digits=make_digits(rng, lengths[1]),
             second_exponent=rng.randint(*second_range))
    return p


def check(p):
    from .standard_form_calculations import answer_for, combine, normalise, renormalisation_needed
    require(p["context"] in FORMS, "Unknown form")
    level, story = FORMS[p["context"]]
    operation, _, _, _, first_range, second_range = STORIES[story]
    require(p["operation"] == operation, "Operation does not match the story")
    integers(p, "first_exponent second_exponent")
    require(digits_ok(p["first_digits"]) and digits_ok(p["second_digits"]), "Mantissa digits")
    if level == 4:
        gap = p["first_exponent"] - p["second_exponent"]
        require(gap in (1, 2) and first_range[0] <= p["second_exponent"] <= first_range[1],
                "Exponent structure")
        require(len(p["first_digits"]) == len(p["second_digits"]) == 2, "Two-digit mantissas")
    else:
        require(first_range[0] <= p["first_exponent"] <= first_range[1]
                and second_range[0] <= p["second_exponent"] <= second_range[1],
                "Exponent ranges")
        if level == 3:
            require(len(p["first_digits"]) == len(p["second_digits"]) == 2,
                    "Two-digit mantissas")
        require(renormalisation_needed(p) == (level == 3), "Renormalising must match the level")
    value = combine(p)
    require(value > 0, "Result must be positive")
    digits, exponent = normalise(value)
    require(len(digits) <= 4 and abs(exponent) <= 14, "Answer bounds")
    return answer_for(p)


def piece(p, which):
    digits, exponent = p[which + "_digits"], p[which + "_exponent"]
    return (standard_form_text(digits, exponent, True), standard_form_text(digits, exponent))


def parts(p):
    answer, display = check(p)
    _, story = FORMS[p["context"]]
    _, sentence, question, unit, _, _ = STORIES[story]
    pieces = tuple(piece(p, "first") if s == X else piece(p, "second") if s == Y else s
                   for s in sentence)
    question_pieces = (question,)
    if "{y}" in question:
        before, after = question.split("{y}")
        question_pieces = (before, piece(p, "second"), after)
    if unit:
        display = Content(display.text + " " + unit,
                          display.math_tex + r"\ \mathrm{" + unit + "}")
    return {"prompt": rich_prompt(pieces, question_pieces), "answer": answer,
            "answer_display": display}


def solve(p, sympy):
    from .standard_form_calculations import normalise

    def value(which):
        digits = p[which + "_digits"]
        return (sympy.Rational(int(digits), 10 ** (len(digits) - 1))
                * sympy.Integer(10) ** p[which + "_exponent"])

    first, second = value("first"), value("second")
    result = {"multiply": first * second, "divide": first / second,
              "add": first + second, "subtract": first - second}[p["operation"]]
    digits, exponent = normalise(worded.exact(result))
    return {"kind": "standard_form", "digits": digits, "exponent": exponent}


CONTEXTS = {
    name: Context(level, KEYS, (lambda rng, name=name: build(rng, name)), check, parts, solve)
    for name, (level, _) in FORMS.items()
}


def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    import sympy
    expected = CONTEXTS[q.parameters["context"]].solve(q.parameters, sympy)
    require(expected == q.answer, "Independent standard-form calculation disagrees")
    return True