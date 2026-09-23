"""Bracketed and fractional forms for the existing two-sided linear family."""
from fractions import Fraction
from math import gcd

from .core import (
    Content, LayoutHint, Question, rational_text, rational_tex, require,
)


def presentation(p, level):
    from .linear_two_sided import linear_expression
    a, b, c, d, m, n = (p[key] for key in ("a", "b", "c", "d", "m", "n"))
    left = linear_expression(a, c)
    right = linear_expression(b, d)
    if level == 3:
        plain = "{}({}) = {}({})".format(m, left, n, right)
        tex = (
            str(m) + r"\left(" + left + r"\right) = "
            + str(n) + r"\left(" + right + r"\right)"
        )
    else:
        plain = "({})/{} = ({})/{}".format(left, m, right, n)
        tex = r"\frac{" + left + "}{" + str(m) + "} = "
        tex += r"\frac{" + right + "}{" + str(n) + "}"
    return Content("Solve for x: " + plain, tex, display_text="Solve for x:")


def solution_for(p, level):
    a, b, c, d, m, n = (p[key] for key in ("a", "b", "c", "d", "m", "n"))
    if level == 3:
        coefficient, constant = m * a - n * b, n * d - m * c
    else:
        coefficient, constant = n * a - m * b, m * d - n * c
    require(coefficient != 0, "Equation must have exactly one solution")
    return Fraction(constant, coefficient)


def check_structure(p, level):
    require(set(p) == {"a", "b", "c", "d", "m", "n"}, "Unexpected parameters")
    require(all(type(v) is int for v in p.values()), "Expected integer parameters")
    require(all(1 <= abs(p[k]) <= 6 for k in ("a", "b")), "Coefficient bounds")
    require(all(1 <= abs(p[k]) <= 12 for k in ("c", "d")), "Constant bounds")
    if level == 3:
        require(2 <= p["m"] <= 5 and 2 <= abs(p["n"]) <= 5,
                "Both sides must require expansion")
        require(p["a"] > 0 and p["b"] > 0, "Bracket coefficient structure")
        require(gcd(p["m"], abs(p["n"])) == 1,
                "Outer multipliers must not share a cancellable factor")
    else:
        require(2 <= p["m"] <= 6 and 2 <= p["n"] <= 6,
                "Denominator bounds")
        require(gcd(p["m"], p["n"]) == 1, "Use distinct coprime denominators")
        require(gcd(gcd(abs(p["a"]), abs(p["c"])), p["m"]) == 1,
                "Left fraction cancels wholesale")
        require(gcd(gcd(abs(p["b"]), abs(p["d"])), p["n"]) == 1,
                "Right fraction cancels wholesale")
    value = solution_for(p, level)
    require(0 < abs(value) <= 12 and value.denominator <= 6,
            "Solution outside intended bounds")
    if level == 3:
        require(value.denominator > 1, "Retain fractional-answer practice")
    return value


def generate(generator, context):
    rng, level = context.rng, context.difficulty
    nonzero = list(range(-12, 0)) + list(range(1, 13))
    for _ in range(2000):
        p = {
            "a": rng.randint(1, 6), "b": rng.randint(1, 6),
            "c": rng.choice(nonzero), "d": rng.choice(nonzero),
            "m": rng.randint(2, 5 if level == 3 else 6),
            "n": rng.randint(2, 5 if level == 3 else 6),
        }
        if level == 3:
            p["n"] *= rng.choice((-1, 1))
        else:
            p["a"] *= rng.choice((-1, 1))
            p["b"] *= rng.choice((-1, 1))
        try:
            value = check_structure(p, level)
        except ValueError:
            continue
        break
    else:
        raise ValueError("Could not construct a suitable linear equation")
    info = generator.info
    q = Question(
        id=context.identity, generator_id=info.id, generator_version=info.version,
        topic=info.topic, subtopic=info.subtopic, difficulty=level,
        seed=context.seed, settings=context.settings,
        prompt=presentation(p, level),
        answer={"kind": "variable_values", "values": {"x": rational_text(value)}},
        answer_display=Content("x = " + rational_text(value),
                               "x = " + rational_tex(value)),
        worked_solution=(), marks=4,
        tags=info.tags, layout_hint=LayoutHint(working_lines=7),
        parameters=p,
    )
    generator.validate(q)
    return q


def validate(generator, q):
    require(q.generator_id == generator.info.id, "Generator mismatch")
    require(q.generator_version == generator.info.version, "Version mismatch")
    require(type(q.difficulty) is int and q.difficulty in (3, 4), "Invalid level")
    require(q.settings == {}, "Unsupported settings")
    value = check_structure(q.parameters, q.difficulty)
    require(q.answer == {
        "kind": "variable_values", "values": {"x": rational_text(value)},
    }, "Incorrect answer")
    require(q.prompt == presentation(q.parameters, q.difficulty), "Prompt mismatch")
    require(q.answer_display == Content(
        "x = " + rational_text(value), "x = " + rational_tex(value),
    ), "Answer display mismatch")
    return True


def validate_independently(q):
    import sympy
    x = sympy.Symbol("x")
    p = q.parameters
    left, right = p["a"] * x + p["c"], p["b"] * x + p["d"]
    if q.difficulty == 3:
        left, right = p["m"] * left, p["n"] * right
    else:
        left, right = left / p["m"], right / p["n"]
    solutions = sympy.solve(sympy.Eq(left, right), x)
    require(solutions == [sympy.Rational(q.answer["values"]["x"])],
            "Independent solution of original equation disagrees")
    return True