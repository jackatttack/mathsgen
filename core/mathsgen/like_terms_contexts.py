"""Applied forms for algebra.expressions.like_terms.

Each form asks for an expression in its simplest form, so a worded answer
has exactly the bare question's shape (polynomial_answer of collected
terms) and the same answer checks apply.

Forms, one per level:
    1 triangle_perimeter   three sides ax + b; the perimeter
    2 rectangle_perimeter  length av + bw, width cv + d; the perimeter
    3 missing_side         a triangle's perimeter and two sides; the third side
    4 pyramid              an algebra pyramid's bottom row; the top brick

check() collects the displayed expressions with the generator's own term
arithmetic. solve() rebuilds each answer in SymPy straight from the
story's relationships, and validate_independently() compares the two.
"""
from . import worded
from .core import require
from .worded import Context
from .algebra_basics import (
    PAIRS, VARIABLES, collect, expression_text, polynomial_answer, require_simplified,
)


# ------------------------------------------------------------ editable knobs

# Chance that a question at each level is applied rather than bare.
CONTEXT_SHARE = {1: 0.3, 2: 0.3, 3: 0.35, 4: 0.35}
MARKS = {1: 2, 2: 2, 3: 3, 4: 3}
WORKING_LINES = {1: 3, 2: 4, 3: 4, 4: 5}
MAX_COEFFICIENT = 9

SIMPLEST = "Give your answer in its simplest form."


def context_share(level):
    return CONTEXT_SHARE.get(level, 0.0)


# ------------------------------------------------------- expression helpers

def linear(letter, a, b):
    """Terms of a·letter + b (the constant is left out when zero)."""
    terms = [[a, [[letter, 1]]]]
    if b:
        terms.append([b, []])
    return terms


def two_letter(letters, a, b):
    first, second = letters
    return [[a, [[first, 1]]], [b, [[second, 1]]]]


def piece(terms):
    """A (tex, plain) maths piece for worded.rich_prompt."""
    return (expression_text(terms, True), expression_text(terms))


def negated(terms):
    return [[-coefficient, monomial] for coefficient, monomial in terms]


def pair(values, low, high, message):
    require(isinstance(values, list) and len(values) == 2, message)
    for value in values:
        require(type(value) is int and low <= value <= high, message)
    return values


def one_letter(p):
    require(p["letter"] in VARIABLES, "Unknown letter")
    return p["letter"]


def letter_pair(p):
    require(isinstance(p["letters"], list) and tuple(p["letters"]) in PAIRS,
            "Unknown letters")
    return p["letters"]


def simplest(terms):
    """(answer, displayed answer) for collected terms."""
    collected = collect(terms)
    require(bool(collected), "Expression cancels to zero")
    return polynomial_answer(collected)


def result(prompt, terms):
    answer, shown = simplest(terms)
    return {"prompt": prompt, "answer": answer, "answer_display": shown}


# ------------------------------------------- level 1: triangle perimeter

def build_triangle(rng):
    return {
        "context": "triangle_perimeter", "letter": rng.choice(VARIABLES),
        "sides": [[rng.randint(1, 6), rng.randint(0, 9)] for _ in range(3)],
    }


def triangle_sides(p):
    letter = one_letter(p)
    require(isinstance(p["sides"], list) and len(p["sides"]) == 3, "Three sides expected")
    sides = [pair(side, 0, MAX_COEFFICIENT, "Side out of bounds") for side in p["sides"]]
    require(all(a >= 1 for a, _ in sides), "Every side needs a letter term")
    require(any(b for _, b in sides), "Expected a number term somewhere")
    return [linear(letter, a, b) for a, b in sides]


def check_triangle(p):
    return simplest([term for side in triangle_sides(p) for term in side])


def parts_triangle(p):
    sides = triangle_sides(p)
    prompt = worded.rich_prompt(
        ("The sides of a triangle are ", piece(sides[0]), ", ", piece(sides[1]),
         " and ", piece(sides[2]), "."),
        ("Write an expression for the perimeter of the triangle. " + SIMPLEST,),
    )
    return result(prompt, [term for side in sides for term in side])


def solve_triangle(p, sympy):
    x = sympy.Symbol(p["letter"])
    return sum(a * x + b for a, b in p["sides"])


# ------------------------------------------ level 2: rectangle perimeter

def build_rectangle(rng):
    return {
        "context": "rectangle_perimeter", "letters": list(rng.choice(PAIRS)),
        "length": [rng.randint(1, 7), rng.randint(1, 7)],
        "width": [rng.randint(1, 5), rng.randint(1, 9)],
    }


def rectangle_sides(p):
    letters = letter_pair(p)
    length = two_letter(letters, *pair(p["length"], 1, MAX_COEFFICIENT, "Length out of bounds"))
    width = linear(letters[0], *pair(p["width"], 1, MAX_COEFFICIENT, "Width out of bounds"))
    return length, width


def check_rectangle(p):
    length, width = rectangle_sides(p)
    return simplest(length + width + length + width)


def parts_rectangle(p):
    length, width = rectangle_sides(p)
    prompt = worded.rich_prompt(
        ("A rectangle has length ", piece(length), " and width ", piece(width), "."),
        ("Write an expression for the perimeter of the rectangle. " + SIMPLEST,),
    )
    return result(prompt, length + width + length + width)


def solve_rectangle(p, sympy):
    v, w = (sympy.Symbol(letter) for letter in p["letters"])
    a, b = p["length"]
    c, d = p["width"]
    return 2 * ((a * v + b * w) + (c * v + d))


# ------------------------------------------------ level 3: missing side

def build_missing(rng):
    sides = [[rng.randint(1, 6), rng.randint(1, 9)] for _ in range(3)]
    return {
        "context": "missing_side", "letter": rng.choice(VARIABLES),
        "perimeter": [sum(a for a, _ in sides), sum(b for _, b in sides)],
        "sides": sides[:2],
    }


def missing_terms(p):
    letter = one_letter(p)
    perimeter = pair(p["perimeter"], 2, 30, "Perimeter out of bounds")
    require(isinstance(p["sides"], list) and len(p["sides"]) == 2, "Two sides expected")
    known = [pair(side, 1, MAX_COEFFICIENT, "Side out of bounds") for side in p["sides"]]
    third = [perimeter[0] - sum(a for a, _ in known), perimeter[1] - sum(b for _, b in known)]
    require(third[0] >= 1 and third[1] >= 1, "The third side must be positive")
    return (linear(letter, *perimeter),
            [linear(letter, a, b) for a, b in known])


def third_side(p):
    perimeter, known = missing_terms(p)
    return perimeter + negated(known[0]) + negated(known[1])


def check_missing(p):
    return simplest(third_side(p))


def parts_missing(p):
    perimeter, known = missing_terms(p)
    prompt = worded.rich_prompt(
        ("The perimeter of a triangle is ", piece(perimeter), "."),
        ("Two of its sides are ", piece(known[0]), " and ", piece(known[1]), "."),
        ("Find an expression for the length of the third side. " + SIMPLEST,),
    )
    return result(prompt, third_side(p))


def solve_missing(p, sympy):
    x = sympy.Symbol(p["letter"])
    total = p["perimeter"][0] * x + p["perimeter"][1]
    return total - sum(a * x + b for a, b in p["sides"])


# ------------------------------------------------- level 4: algebra pyramid

def build_pyramid(rng):
    return {
        "context": "pyramid", "letters": list(rng.choice(PAIRS)),
        "bricks": [[rng.randint(1, 6), rng.randint(1, 6)] for _ in range(3)],
    }


def pyramid_bricks(p):
    letters = letter_pair(p)
    require(isinstance(p["bricks"], list) and len(p["bricks"]) == 3, "Three bricks expected")
    return [two_letter(letters, *pair(brick, 1, MAX_COEFFICIENT, "Brick out of bounds"))
            for brick in p["bricks"]]


def top_brick(p):
    left, middle, right = pyramid_bricks(p)
    # Second row: left + middle and middle + right; the top adds those two.
    return left + middle + middle + right


def check_pyramid(p):
    return simplest(top_brick(p))


def parts_pyramid(p):
    left, middle, right = pyramid_bricks(p)
    prompt = worded.rich_prompt(
        ("In an algebra pyramid, each brick is the sum of the two bricks directly below it.",),
        ("The bottom row is ", piece(left), ", ", piece(middle), " and ", piece(right),
         ", in that order."),
        ("Find an expression for the top brick. " + SIMPLEST,),
    )
    return result(prompt, top_brick(p))


def solve_pyramid(p, sympy):
    v, w = (sympy.Symbol(letter) for letter in p["letters"])
    left, middle, right = (a * v + b * w for a, b in p["bricks"])
    second = (left + middle, middle + right)
    return second[0] + second[1]


# ----------------------------------------------------------------- registry

CONTEXTS = {
    "triangle_perimeter": Context(
        1, frozenset({"context", "letter", "sides"}),
        build_triangle, check_triangle, parts_triangle, solve_triangle),
    "rectangle_perimeter": Context(
        2, frozenset({"context", "letters", "length", "width"}),
        build_rectangle, check_rectangle, parts_rectangle, solve_rectangle),
    "missing_side": Context(
        3, frozenset({"context", "letter", "perimeter", "sides"}),
        build_missing, check_missing, parts_missing, solve_missing),
    "pyramid": Context(
        4, frozenset({"context", "letters", "bricks"}),
        build_pyramid, check_pyramid, parts_pyramid, solve_pyramid),
}


# ------------------------------------------------ generate and validate

def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    import sympy
    p = q.parameters
    expected = sympy.expand(CONTEXTS[p["context"]].solve(p, sympy))
    require_simplified(expected, q.answer["terms"])
    return True