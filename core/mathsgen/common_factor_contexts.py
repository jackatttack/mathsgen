"""Applied forms for algebra.factorising.common_factor.

L1 rectangle_side    area f(ax + b) cm² with one side f cm: the other side
L2 always_multiple   show f·a·n + f·b is a multiple of f for every whole n
L3 rectangle_letter  area fx(ax + b) cm² with one side fx cm: the other side
L4 incomplete        a partial factorisation to explain and complete

Every bracket is primitive (no number or letter left to take out), so the
stated side or factor is the greatest common factor. check() uses the
generator's own term arithmetic; validate_independently() rebuilds the
expression in SymPy and uses SymPy's gcd and division instead.
"""
from functools import reduce
from math import gcd

from .core import Content, require
from . import worded
from .worded import NAMES, Context
from .common_factor import LETTER_PAIRS, expression_text, factorised_text, monomial


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {1: 0.3, 2: 0.3, 3: 0.35, 4: 0.35}
MARKS = {1: 2, 2: 2, 3: 3, 4: 3}
WORKING_LINES = {1: 3, 2: 3, 3: 4, 4: 5}

COMPOSITE_FACTORS = (4, 6, 8, 9)          # so part of the number can be missed
INNER_SHAPES = (((1, 0), (0, 1)), ((2, 0), (0, 1)), ((1, 0), (0, 2)))


def context_share(level):
    return CONTEXT_SHARE.get(level, 0.0)


# ------------------------------------------------------------- term helpers

def times(factor, powers, inner):
    """factor·letters^powers multiplied into each inner term."""
    return [(factor * c, tuple(a + b for a, b in zip(powers, p))) for c, p in inner]


def lists(terms):
    return [[c, list(p)] for c, p in terms]


def two_terms(raw, width, limit=9):
    """Parameter terms as tuples, after checking their shape and bounds."""
    require(isinstance(raw, list) and len(raw) == 2, "Expected two terms")
    terms = []
    for item in raw:
        require(isinstance(item, list) and len(item) == 2, "Term must be [c, powers]")
        c, powers = item
        require(type(c) is int and c != 0 and abs(c) <= limit, "Coefficient out of bounds")
        require(isinstance(powers, list) and len(powers) == width
                and all(type(x) is int and 0 <= x <= 2 for x in powers),
                "Powers out of bounds")
        terms.append((c, tuple(powers)))
    return terms


def require_primitive(inner):
    require(reduce(gcd, [abs(c) for c, _ in inner]) == 1, "Bracket has a numerical factor")
    for index in range(len(inner[0][1])):
        require(min(p[index] for _, p in inner) == 0, "Bracket has a letter factor")


def maths(terms, letters):
    return (expression_text(terms, letters, True), expression_text(terms, letters))


def bracketed(terms, letters):
    tex, plain = maths(terms, letters)
    return (r"\left(" + tex + r"\right)", "(" + plain + ")")


def factor_answer(factor, powers, inner, letters):
    return {"kind": "common_factor_form", "factor": factor, "factor_powers": list(powers),
            "inner": lists(inner), "letters": list(letters)}


def linear_inner(p):
    """ax + b with positive a and b, and nothing left to take out."""
    inner = two_terms(p["inner"], 1)
    require(inner[0][1] == (1,) and inner[1][1] == (0,), "Expected ax + b")
    require(inner[0][0] > 0 and inner[1][0] > 0, "Expected positive terms")
    require_primitive(inner)
    return inner


def build_linear_inner(rng):
    return [[rng.randint(1, 9), [1]], [rng.randint(1, 9), [0]]]


def expression_answer(inner, letters, unit=""):
    answer = {"kind": "expression", "terms": lists(inner), "letters": list(letters)}
    return answer, Content(expression_text(inner, letters) + unit)


# ------------------------------------------------ L1 and L3: rectangle side

SIDE_LETTER_POWER = {"rectangle_side": 0, "rectangle_letter": 1}


def build_rectangle(rng, context):
    return {"context": context, "side": rng.randint(2, 9 if context == "rectangle_side" else 6),
            "inner": build_linear_inner(rng)}


def check_rectangle(p):
    side = p["side"]
    require(type(side) is int and 2 <= side <= 9, "Side out of bounds")
    return linear_inner(p)


def parts_rectangle(p):
    inner = check_rectangle(p)
    letters = ("x",)
    power = (SIDE_LETTER_POWER[p["context"]],)
    area = times(p["side"], power, inner)
    side = (monomial(p["side"], power, letters, True), monomial(p["side"], power, letters))
    prompt = worded.rich_prompt(
        ("The area of a rectangle is ", bracketed(area, letters), " cm²."),
        ("One side is ", side, " cm long."),
        ("Find an expression for the length of the other side.",),
    )
    answer, shown = expression_answer(inner, letters, " cm")
    return {"prompt": prompt, "answer": answer, "answer_display": shown}


def solve_rectangle(p, sympy):
    x = sympy.Symbol("x", positive=True)
    (a, _), (b, _) = p["inner"]
    side = p["side"] * x ** SIDE_LETTER_POWER[p["context"]]
    return "divide", sympy.expand(side * (a * x + b)), side, {"x": x}


# --------------------------------------------------- L2: always a multiple

def build_multiple(rng):
    return {"context": "always_multiple", "factor": rng.randint(2, 9),
            "inner": build_linear_inner(rng)}


def check_multiple(p):
    require(type(p["factor"]) is int and 2 <= p["factor"] <= 9, "Factor out of bounds")
    return linear_inner(p)


def parts_multiple(p):
    inner = check_multiple(p)
    letters = ("n",)
    factor = p["factor"]
    terms = times(factor, (0,), inner)
    prompt = worded.rich_prompt(
        ("Show that ", maths(terms, letters),
         " is a multiple of {} for every whole number n.".format(factor)),
    )
    written = expression_text(terms, letters)
    shown = Content("{} = {}. {} is a whole number, so {} is a multiple of {}.".format(
        written, factorised_text(factor, (0,), inner, letters),
        expression_text(inner, letters), written, factor))
    return {"prompt": prompt, "answer": factor_answer(factor, (0,), inner, letters),
            "answer_display": shown}


def solve_multiple(p, sympy):
    n = sympy.Symbol("n", positive=True)
    (a, _), (b, _) = p["inner"]
    return "factor", sympy.expand(p["factor"] * (a * n + b)), None, {"n": n}


# --------------------------------------------- L4: an incomplete factorisation

def smallest_prime(number):
    return next(d for d in range(2, number + 1) if number % d == 0)


def build_incomplete(rng):
    shape = rng.choice(INNER_SHAPES)
    a = rng.randint(1, 6)
    b = rng.choice([v for v in range(-6, 7) if v])
    return {
        "context": "incomplete", "name": rng.choice(NAMES),
        "letters": list(rng.choice(LETTER_PAIRS)),
        "factor": rng.choice(COMPOSITE_FACTORS),
        "factor_powers": [rng.randint(1, 2), rng.randint(1, 2)],
        "inner": [[a, list(shape[0])], [b, list(shape[1])]],
        "partial": rng.choice(("number", "letter")), "letter_index": rng.randint(0, 1),
    }


def incomplete_parts(p):
    """Letters, the full factorisation, the student's partial one and what is left over."""
    require(p["name"] in NAMES, "Unknown name")
    letters = tuple(p["letters"]) if isinstance(p["letters"], list) else None
    require(letters in LETTER_PAIRS, "Unknown letters")
    factor = p["factor"]
    require(factor in COMPOSITE_FACTORS, "Factor must have a proper divisor")
    powers = p["factor_powers"]
    require(isinstance(powers, list) and len(powers) == 2
            and all(type(x) is int and 1 <= x <= 2 for x in powers), "Factor powers")
    powers = tuple(powers)
    inner = two_terms(p["inner"], 2, limit=6)
    require_primitive(inner)
    require(p["partial"] in ("number", "letter"), "Unknown partial kind")
    require(p["letter_index"] in (0, 1), "Unknown letter index")
    if p["partial"] == "number":
        divisor = smallest_prime(factor)
        partial_factor, partial_powers = factor // divisor, powers
        left_over = str(divisor)
    else:
        index = p["letter_index"]
        partial_factor = factor
        partial_powers = tuple(x - (1 if i == index else 0) for i, x in enumerate(powers))
        left_over = letters[index]
    terms = times(factor, powers, inner)
    partial_inner = [(c // partial_factor, tuple(x - y for x, y in zip(q, partial_powers)))
                     for c, q in terms]
    require(times(partial_factor, partial_powers, partial_inner) == terms,
            "The partial factorisation must expand back to the expression")
    return letters, factor, powers, inner, partial_factor, partial_powers, partial_inner, left_over


def check_incomplete(p):
    return incomplete_parts(p)


def parts_incomplete(p):
    (letters, factor, powers, inner, partial_factor, partial_powers,
     partial_inner, left_over) = incomplete_parts(p)
    terms = times(factor, powers, inner)
    partial = (factorised_text(partial_factor, partial_powers, partial_inner, letters, True),
               factorised_text(partial_factor, partial_powers, partial_inner, letters))
    prompt = worded.rich_prompt(
        (p["name"] + " factorises ", maths(terms, letters), " and writes ", partial, "."),
        ("Explain why this is not fully factorised, then factorise it fully.",),
    )
    shown = Content("The bracket still has a common factor of {}. Fully factorised: {}.".format(
        left_over, factorised_text(factor, powers, inner, letters)))
    return {"prompt": prompt, "answer": factor_answer(factor, powers, inner, letters),
            "answer_display": shown}


def solve_incomplete(p, sympy):
    symbols = {name: sympy.Symbol(name, positive=True) for name in p["letters"]}
    first, second = (symbols[name] for name in p["letters"])
    outside = p["factor"] * first ** p["factor_powers"][0] * second ** p["factor_powers"][1]
    inside = sum(c * first ** q[0] * second ** q[1] for c, q in p["inner"])
    return "factor", sympy.expand(outside * inside), None, symbols


# ----------------------------------------------------------------- registry

RECTANGLE_KEYS = frozenset({"context", "side", "inner"})

CONTEXTS = {
    "rectangle_side": Context(
        1, RECTANGLE_KEYS, lambda rng: build_rectangle(rng, "rectangle_side"),
        check_rectangle, parts_rectangle, solve_rectangle),
    "always_multiple": Context(
        2, frozenset({"context", "factor", "inner"}),
        build_multiple, check_multiple, parts_multiple, solve_multiple),
    "rectangle_letter": Context(
        3, RECTANGLE_KEYS, lambda rng: build_rectangle(rng, "rectangle_letter"),
        check_rectangle, parts_rectangle, solve_rectangle),
    "incomplete": Context(
        4, frozenset({"context", "name", "letters", "factor", "factor_powers", "inner",
                      "partial", "letter_index"}),
        build_incomplete, check_incomplete, parts_incomplete, solve_incomplete),
}


# ------------------------------------------------ generate and validate

def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    """Rebuild the story's expression in SymPy and check the answer against it.

    divide: the answer must equal the area divided by the given side.
    factor: the answer's outside factor must be SymPy's gcd of the terms
            (up to sign) and must expand back to the expression.
    """
    import sympy
    p = q.parameters
    kind, expression, divisor, symbols = CONTEXTS[p["context"]].solve(p, sympy)
    answer = q.answer
    letters = [symbols[name] for name in answer["letters"]]

    def build(terms):
        total = sympy.Integer(0)
        for coefficient, powers in terms:
            term = sympy.Integer(coefficient)
            for symbol, power in zip(letters, powers):
                term *= symbol ** power
            total += term
        return total

    if kind == "divide":
        require(answer["kind"] == "expression", "Expected an expression answer")
        require(sympy.simplify(build(answer["terms"]) - expression / divisor) == 0,
                "Independent division disagrees")
        return True
    require(answer["kind"] == "common_factor_form", "Expected a factorised answer")
    common = reduce(sympy.gcd, sympy.Add.make_args(expression))
    outside = sympy.Integer(answer["factor"])
    for symbol, power in zip(letters, answer["factor_powers"]):
        outside *= symbol ** power
    ratio = sympy.simplify(outside / common)
    require(ratio in (1, -1), "The factor is not the greatest common factor")
    require(sympy.expand(outside * build(answer["inner"]) - expression) == 0,
            "Independent expansion disagrees")
    return True