"""Linear equations with two fractional expressions on the left.

The denominator is always a nonzero integer, so clearing denominators
introduces no excluded x values. Answers are bounded exact fractions.
"""
from fractions import Fraction
from math import gcd

from . import rich_blocks as rb
from .core import (
    Content, LayoutHint, Question, rational_text, rational_tex, require,
)

FORM = "fraction_sum"
DENOMINATORS = (2, 3, 4, 5, 6)


def solution_for(p):
    coefficient = Fraction(p["a"], p["m"]) + p["sign"] * Fraction(p["b"], p["n"]) - p["e"]
    constant = p["f"] - Fraction(p["c"], p["m"]) - p["sign"] * Fraction(p["d"], p["n"])
    require(coefficient != 0, "Equation must have exactly one solution")
    return constant / coefficient


def check_structure(p):
    require(isinstance(p, dict) and set(p) == {
        "form", "a", "b", "c", "d", "m", "n", "sign", "e", "f",
    }, "Unexpected fraction-sum parameters")
    require(p["form"] == FORM, "Unexpected equation form")
    require(all(type(value) is int for key, value in p.items() if key != "form"),
            "Integer equation parameters required")
    require(p["m"] in DENOMINATORS and p["n"] in DENOMINATORS
            and p["m"] != p["n"], "Use different positive denominators")
    require(p["sign"] in (-1, 1), "Expected addition or subtraction")
    require(all(1 <= p[key] <= 6 for key in ("a", "b")), "Coefficient bounds")
    require(all(1 <= abs(p[key]) <= 12 for key in ("c", "d")), "Constant bounds")
    require(-3 <= p["e"] <= 3 and 1 <= abs(p["f"]) <= 15, "Right-hand bounds")
    require(gcd(gcd(p["a"], abs(p["c"])), p["m"]) == 1
            and gcd(gcd(p["b"], abs(p["d"])), p["n"]) == 1,
            "A whole fractional expression cancels")
    value = solution_for(p)
    require(0 < abs(value) <= 12 and value.denominator <= 24,
            "Solution outside intended bounds")
    return value


def presentation(p):
    from .linear_two_sided import linear_expression
    first = linear_expression(p["a"], p["c"])
    second = linear_expression(p["b"], p["d"])
    right = linear_expression(p["e"], p["f"]) if p["e"] else str(p["f"])
    operator = " + " if p["sign"] == 1 else " - "
    plain = "({})/{}{}({})/{} = {}".format(
        first, p["m"], operator, second, p["n"], right)
    tex = (r"\frac{" + first + "}{" + str(p["m"]) + "}" + operator
           + r"\frac{" + second + "}{" + str(p["n"]) + "} = " + right)
    return Content("Solve for x: " + plain, blocks=(
        rb.prose("Solve for x:"), rb.equation(tex, plain),
    ))


def generate(generator, context):
    rng = context.rng
    constants = [n for n in range(-12, 13) if n]
    sign = rng.choice((-1, 1))
    # Half use a numerical RHS, matching the requested classroom form.
    e = 0 if rng.choice((True, False)) else rng.choice((-3, -2, -1, 1, 2, 3))
    for _ in range(2000):
        m, n = rng.sample(DENOMINATORS, 2)
        p = {
            "form": FORM, "a": rng.randint(1, 6), "b": rng.randint(1, 6),
            "c": rng.choice(constants), "d": rng.choice(constants),
            "m": m, "n": n, "sign": sign, "e": e,
            "f": rng.choice([v for v in range(-15, 16) if v]),
        }
        try:
            value = check_structure(p)
        except ValueError:
            continue
        break
    else:
        raise ValueError("Could not construct a suitable fractional linear equation")
    info = generator.info
    question = Question(
        id=context.identity, generator_id=info.id, generator_version=info.version,
        topic=info.topic, subtopic=info.subtopic, difficulty=4,
        seed=context.seed, settings=context.settings, prompt=presentation(p),
        answer={"kind": "variable_values", "values": {"x": rational_text(value)}},
        answer_display=Content("x = " + rational_text(value), "x = " + rational_tex(value)),
        worked_solution=(), marks=4, tags=info.tags,
        layout_hint=LayoutHint(working_lines=8), parameters=p,
    )
    generator.validate(question)
    return question


def validate(generator, question):
    require(question.generator_id == generator.info.id
            and question.generator_version == generator.info.version, "Generator mismatch")
    require(question.difficulty == 4 and type(question.difficulty) is int, "Expected level 4")
    require(question.settings == {}, "Unsupported settings")
    value = check_structure(question.parameters)
    require(question.answer == {
        "kind": "variable_values", "values": {"x": rational_text(value)},
    }, "Incorrect answer")
    require(question.prompt == presentation(question.parameters), "Prompt mismatch")
    require(question.answer_display == Content(
        "x = " + rational_text(value), "x = " + rational_tex(value)),
        "Answer display mismatch")
    return True


def validate_independently(question):
    import sympy
    p = question.parameters
    x = sympy.Symbol("x")
    left = ((p["a"] * x + p["c"]) / p["m"]
            + p["sign"] * (p["b"] * x + p["d"]) / p["n"])
    right = p["e"] * x + p["f"]
    solutions = sympy.solve(sympy.Eq(left, right), x)
    require(solutions == [sympy.Rational(question.answer["values"]["x"])],
            "Independent solution of fractional sum disagrees")
    return True