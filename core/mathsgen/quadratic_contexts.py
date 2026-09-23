"""Worded contexts for algebra.quadratic.factorisable_non_monic.

Every context forms (p x + r)(q x + s) = target, which expands to a
non-monic quadratic with one whole-number root that fits the story and one
root that must be rejected (negative, fractional-and-negative, or giving a
non-positive length). The answer display names the rejected root.

L2 rectangle area -> x     L3 triangle area -> base; number puzzle -> number
L4 rectangle area -> x -> perimeter

check() uses the bare family's exact roots_for(); solve() solves the story
equation directly in SymPy and filters roots by the story's own conditions.
"""
from fractions import Fraction

from .core import Content, rational_text, require
from . import worded
from .worded import Context, integers, quantity, rich_prompt, whole
from .quadratic_non_monic import roots_for


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {2: 0.4, 3: 0.5, 4: 0.5}
MARKS = {2: 4, 3: 5, 4: 5}
WORKING_LINES = {2: 8, 3: 9, 4: 9}


def bracketed(coefficient, constant):
    from .linear_two_sided import linear_expression
    text = "(" + linear_expression(coefficient, constant) + ")"
    return (text, text)


def fitting_root(first, second, target):
    """Solve (p x + r)(q x + s) = target; exactly one root must fit the story."""
    (p, r), (q, s) = first, second
    roots = roots_for(p * q, p * s + q * r, r * s - target)
    fits = [x for x in roots if x > 0 and p * x + r > 0 and q * x + s > 0]
    require(len(fits) == 1, "Exactly one root must fit the context")
    x = whole(fits[0], 1, 12, "The fitting root must be a whole number")
    rejected = [root for root in roots if root != fits[0]][0]
    return x, rejected


def reject_text(rejected):
    return "reject x = {}".format(rational_text(rejected))


# ------------------------------------------------ rectangle and triangle

SHAPE_KEYS = frozenset({"context", "p", "r", "s", "area"})


def build_shape(rng, name):
    x = rng.randint(2, 9)
    p = rng.randint(2, 5)
    r = rng.choice([v for v in range(-5, 10) if v])
    s = rng.choice([v for v in range(-4, 10) if v])
    product = (p * x + r) * (x + s)
    if name == "triangle_base":
        area = product // 2 if product % 2 == 0 else 0
    else:
        area = product
    return {"context": name, "p": p, "r": r, "s": s, "area": area}


def check_shape(p):
    integers(p, "p r s area")
    require(2 <= p["p"] <= 5 and p["r"] != 0 and -5 <= p["r"] <= 9
            and p["s"] != 0 and -4 <= p["s"] <= 9, "Coefficient bounds")
    require(4 <= p["area"] <= 400, "Area bounds")
    target = 2 * p["area"] if p["context"] == "triangle_base" else p["area"]
    x, rejected = fitting_root((p["p"], p["r"]), (1, p["s"]), target)
    first, second = p["p"] * x + p["r"], x + p["s"]
    require(first >= 2 and second >= 2, "Lengths must be at least 2 cm")
    return x, rejected, first, second


def shape_answer(p, x, first, second):
    if p["context"] == "rectangle_x":
        return {"kind": "variable_values", "values": {"x": str(x)}}
    if p["context"] == "rectangle_perimeter":
        return quantity(2 * (first + second), "cm")
    return quantity(first, "cm")


def parts_shape(p):
    x, rejected, first, second = check_shape(p)
    if p["context"] == "triangle_base":
        sides = ("A triangle has base ", bracketed(p["p"], p["r"]),
                 " cm and perpendicular height ", bracketed(1, p["s"]), " cm.")
        ask = ("Work out the length of the base.",)
        shown = "x = {} ({}), so the base is {} cm.".format(x, reject_text(rejected), first)
    else:
        sides = ("A rectangle has length ", bracketed(p["p"], p["r"]),
                 " cm and width ", bracketed(1, p["s"]), " cm.")
        if p["context"] == "rectangle_x":
            ask = ("Work out the value of ", ("x", "x"), ".")
            shown = "x = {} ({})".format(x, reject_text(rejected))
        else:
            ask = ("Work out the perimeter of the rectangle.",)
            shown = "x = {} ({}), so the perimeter is {} cm.".format(
                x, reject_text(rejected), 2 * (first + second))
    prompt = rich_prompt(sides, ("Its area is {} cm².".format(p["area"]),), ask)
    return {"prompt": prompt, "answer": shape_answer(p, x, first, second),
            "answer_display": Content(shown)}


def solve_shape(p, sympy):
    x = sympy.Symbol("x")
    first, second = p["p"] * x + p["r"], x + p["s"]
    area = first * second
    if p["context"] == "triangle_base":
        area = sympy.Rational(1, 2) * area
    fits = [v for v in sympy.solve(sympy.Eq(area, p["area"]), x)
            if v.is_real and v > 0 and first.subs(x, v) > 0 and second.subs(x, v) > 0]
    require(len(fits) == 1, "Story must have exactly one fitting solution")
    value = fits[0]
    return shape_answer(p, int(value), int(first.subs(x, value)), int(second.subs(x, value)))


# ------------------------------------------------------ number puzzle

def build_number(rng):
    n, p, r = rng.randint(2, 12), rng.randint(2, 5), rng.randint(1, 9)
    return {"context": "number_product", "p": p, "r": r, "total": n * (p * n + r)}


def check_number(p):
    integers(p, "p r total")
    require(2 <= p["p"] <= 5 and 1 <= p["r"] <= 9, "Coefficient bounds")
    require(10 <= p["total"] <= 800, "Total bounds")
    return fitting_root((p["p"], p["r"]), (1, 0), p["total"])


def parts_number(p):
    n, rejected = check_number(p)
    text = ("I think of a positive whole number. I multiply it by {r} more than {p} "
            "times the number. The answer is {total}. What is my number?").format(**p)
    return {"prompt": Content(text), "answer": quantity(n, ""),
            "answer_display": Content("The number is {} (reject {}).".format(
                n, rational_text(rejected)))}


def solve_number(p, sympy):
    n = sympy.Symbol("n")
    fits = [v for v in sympy.solve(sympy.Eq(n * (p["p"] * n + p["r"]), p["total"]), n)
            if v.is_integer and v > 0]
    require(len(fits) == 1, "Exactly one positive whole number")
    return quantity(int(fits[0]), "")


# ------------------------------------------------------------ registry

CONTEXTS = {
    "rectangle_x": Context(2, SHAPE_KEYS, lambda rng: build_shape(rng, "rectangle_x"),
                           check_shape, parts_shape, solve_shape),
    "triangle_base": Context(3, SHAPE_KEYS, lambda rng: build_shape(rng, "triangle_base"),
                             check_shape, parts_shape, solve_shape),
    "number_product": Context(3, frozenset({"context", "p", "r", "total"}),
                              build_number, check_number, parts_number, solve_number),
    "rectangle_perimeter": Context(4, SHAPE_KEYS,
                                   lambda rng: build_shape(rng, "rectangle_perimeter"),
                                   check_shape, parts_shape, solve_shape),
}


def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    import sympy
    expected = CONTEXTS[q.parameters["context"]].solve(q.parameters, sympy)
    require(expected == q.answer, "Independent quadratic story disagrees")
    return True