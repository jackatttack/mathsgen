"""Worded quadratic sequences mixed with the original five-term questions.

The final level derives a quadratic rule from three scores and uses it to
find the highest score over six rounds. The displayed numbers alone
determine the rule; no hidden coefficients are stored in the question.
"""
from fractions import Fraction

from .core import Content, rational_text, require
from . import worded
from .worded import Context, integers

# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {1: 0.35, 2: 0.40, 3: 0.50, 4: 0.60}
MARKS = {1: 3, 2: 3, 3: 4, 4: 5}
WORKING_LINES = {1: 5, 2: 6, 3: 8, 4: 9}
GRID_ITEMS = ("a mosaic", "a floor pattern", "a display")


def polynomial_answer(a, b, c):
    return {"kind": "polynomial", "variable": "n",
            "coefficients_descending": [
                rational_text(a), rational_text(b), rational_text(c)]}


def polynomial_parts(text, a, b, c):
    from .nth_term import expression
    coefficients = polynomial_answer(a, b, c)["coefficients_descending"]
    return {"prompt": Content(text),
            "answer": polynomial_answer(a, b, c),
            "answer_display": Content(
                expression(coefficients), expression(coefficients, True))}


# ----------------------------------------------- level 1: square and extras

def build_square(rng):
    return {"context": "square_grid", "item": rng.choice(GRID_ITEMS),
            "extra": rng.randint(1, 9)}


def check_square(p):
    integers(p, "extra")
    require(p["item"] in GRID_ITEMS and 1 <= p["extra"] <= 9,
            "Square-grid choices outside bounds")
    return 1, 0, p["extra"]


def parts_square(p):
    a, b, c = check_square(p)
    text = (
        "At stage n, {} has a square grid with n tiles along each side "
        "and {} extra tiles beside it. Write an expression for the total "
        "number of tiles."
    ).format(p["item"], c)
    return polynomial_parts(text, a, b, c)


def solve_square(p, sympy):
    n = sympy.Symbol("n")
    polynomial = sympy.Poly(n * n + p["extra"], n)
    return polynomial_answer(*polynomial.all_coeffs())


# ------------------------------------------- level 2: rectangle plus extras

def build_rectangle(rng):
    return {"context": "growing_rectangle",
            "extra_columns": rng.randint(2, 6),
            "spare_tiles": rng.randint(1, 9)}


def check_rectangle(p):
    integers(p, "extra_columns spare_tiles")
    require(2 <= p["extra_columns"] <= 6
            and 1 <= p["spare_tiles"] <= 9,
            "Rectangle dimensions outside bounds")
    return 1, p["extra_columns"], p["spare_tiles"]


def parts_rectangle(p):
    a, b, c = check_rectangle(p)
    text = (
        "A stage-n tile pattern has n rows. Each row has {} more tiles "
        "than the stage number. There are also {} separate tiles in every stage. "
        "Write an expression for the total number of tiles at stage n."
    ).format(b, c)
    return polynomial_parts(text, a, b, c)


def solve_rectangle(p, sympy):
    n = sympy.Symbol("n")
    polynomial = sympy.Poly(
        sympy.expand(n * (n + p["extra_columns"]) + p["spare_tiles"]), n)
    return polynomial_answer(*polynomial.all_coeffs())


# -------------------------------------- level 3: infer changing row width

def build_widths(rng):
    a, b = rng.randint(2, 5), rng.randint(1, 6)
    return {"context": "changing_width",
            "width_one": a + b, "width_three": 3 * a + b,
            "extra": rng.randint(1, 9)}


def check_widths(p):
    integers(p, "width_one width_three extra")
    difference = p["width_three"] - p["width_one"]
    require(difference > 0 and difference % 2 == 0,
            "Row widths must grow by a whole number")
    a = difference // 2
    b = p["width_one"] - a
    require(2 <= a <= 5 and 1 <= b <= 6 and 1 <= p["extra"] <= 9,
            "Pattern dimensions outside bounds")
    return a, b, p["extra"]


def parts_widths(p):
    a, b, c = check_widths(p)
    text = (
        "A growing display has n rows at stage n. Its number of tiles "
        "per row increases at a constant rate: stage 1 has {} tiles "
        "per row and stage 3 has {} tiles per row. There are also {} "
        "fixed tiles outside the rows. Write an expression for the "
        "total number of tiles at stage n."
    ).format(p["width_one"], p["width_three"], c)
    return polynomial_parts(text, a, b, c)


def solve_widths(p, sympy):
    a, b, n = sympy.symbols("a b n")
    solutions = sympy.solve(
        [a + b - p["width_one"],
         3 * a + b - p["width_three"]],
        (a, b), dict=True)
    require(len(solutions) == 1, "Row widths do not define one rule")
    polynomial = sympy.Poly(
        sympy.expand(n * (solutions[0][a] * n + solutions[0][b])
                     + p["extra"]), n)
    return polynomial_answer(*polynomial.all_coeffs())


# -------------------------------- level 4: infer a rule and use its maximum

def build_game(rng):
    a = -rng.randint(1, 4)
    peak = rng.randint(4, 5)
    b = -2 * a * peak
    c = rng.randint(25, 60)

    def score(round_number):
        return a * round_number ** 2 + b * round_number + c

    return {"context": "game_peak",
            "round_one": score(1), "round_two": score(2),
            "round_three": score(3)}


def check_game(p):
    integers(p, "round_one round_two round_three")
    first = p["round_two"] - p["round_one"]
    second = p["round_three"] - 2 * p["round_two"] + p["round_one"]
    require(second < 0 and second % 2 == 0,
            "Scores must have a negative even second difference")
    a = second // 2
    b = first - 3 * a
    c = p["round_one"] - a - b
    require(-4 <= a <= -1 and 25 <= c <= 60,
            "Quadratic score rule outside bounds")
    peak = Fraction(-b, 2 * a)
    require(peak.denominator == 1 and 4 <= peak <= 5,
            "Peak must come after the three stated rounds")
    scores = [a * n * n + b * n + c for n in range(1, 7)]
    require(all(0 < score <= 200 for score in scores),
            "All six scores must be positive and reasonable")
    maximum = max(scores)
    require(scores.count(maximum) == 1,
            "The highest scoring round must be unique")
    return scores.index(maximum) + 1, maximum


def peak_answer(round_number, score):
    return {"kind": "peak_score", "round": int(round_number),
            "score": int(score)}


def parts_game(p):
    round_number, score = check_game(p)
    text = (
        "A six-round game awards points in a quadratic sequence. "
        "The first three round scores are {}, {} and {} points. "
        "Which round scores the most points, and how many points "
        "are scored in that round?"
    ).format(p["round_one"], p["round_two"], p["round_three"])
    return {"prompt": Content(text),
            "answer": peak_answer(round_number, score),
            "answer_display": Content(
                "Round {}: {} points.".format(round_number, score))}


def solve_game(p, sympy):
    a, b, c, n = sympy.symbols("a b c n")
    solutions = sympy.solve(
        [a + b + c - p["round_one"],
         4 * a + 2 * b + c - p["round_two"],
         9 * a + 3 * b + c - p["round_three"]],
        (a, b, c), dict=True)
    require(len(solutions) == 1, "Three scores do not define one quadratic")
    polynomial = (solutions[0][a] * n ** 2
                  + solutions[0][b] * n + solutions[0][c])
    scored = [(int(polynomial.subs(n, day)), day) for day in range(1, 7)]
    score, round_number = max(scored)
    return peak_answer(round_number, score)


CONTEXTS = {
    "square_grid": Context(
        1, {"context", "item", "extra"},
        build_square, check_square, parts_square, solve_square),
    "growing_rectangle": Context(
        2, {"context", "extra_columns", "spare_tiles"},
        build_rectangle, check_rectangle, parts_rectangle, solve_rectangle),
    "changing_width": Context(
        3, {"context", "width_one", "width_three", "extra"},
        build_widths, check_widths, parts_widths, solve_widths),
    "game_peak": Context(
        4, {"context", "round_one", "round_two", "round_three"},
        build_game, check_game, parts_game, solve_game),
}


def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, question):
    return worded.validate(generator, question, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(question):
    import sympy
    p = question.parameters
    require(p.get("context") in CONTEXTS, "Unknown quadratic-sequence context")
    expected = CONTEXTS[p["context"]].solve(p, sympy)
    require(question.answer == expected,
            "Independent quadratic sequence story disagrees")
    return True