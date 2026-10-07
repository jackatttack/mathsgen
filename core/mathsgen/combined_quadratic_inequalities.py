"""Intersect two quadratic solution sets using exact rational boundaries."""
from fractions import Fraction
from math import isqrt

from . import rich_blocks as rb
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)
from .quadratic_monic import polynomial

OPS = ("<", "<=", ">", ">=")
TEX = {"<": "<", "<=": r"\leq", ">": ">", ">=": r"\geq"}
REVERSE = {"<": ">", "<=": ">=", ">": "<", ">=": "<="}


def roots_of(coefficients):
    a, b, c = coefficients
    require(a != 0, "Expected a quadratic")
    discriminant = b * b - 4 * a * c
    require(discriminant > 0, "Expected two distinct real roots")
    square = isqrt(discriminant)
    require(square * square == discriminant, "Expected rational roots")
    return tuple(sorted((Fraction(-b - square, 2 * a),
                         Fraction(-b + square, 2 * a))))


def intervals_for(item):
    low, high = roots_of(item["coefficients"])
    op = item["operator"]
    closed = op in ("<=", ">=")
    inside = (item["coefficients"][0] > 0) == (op in ("<", "<="))
    if inside:
        return [(low, high, closed, closed)]
    return [(None, low, False, closed), (high, None, closed, False)]


def intersect(first, second):
    """Intersect ordered disjoint interval lists; None denotes infinity."""
    result = []
    for a, b, ac, bc in first:
        for c, d, cc, dc in second:
            if a is None:
                low, lc = c, cc
            elif c is None or a > c:
                low, lc = a, ac
            elif c > a:
                low, lc = c, cc
            else:
                low, lc = a, ac and cc
            if b is None:
                high, hc = d, dc
            elif d is None or b < d:
                high, hc = b, bc
            elif d < b:
                high, hc = d, dc
            else:
                high, hc = b, bc and dc
            if low is None or high is None or low < high or (
                    low == high and lc and hc):
                result.append((low, high, lc, hc))
    return sorted(result, key=lambda v: (
        v[0] is not None, v[0] if v[0] is not None else 0))


def check_parameters(p, level):
    require(isinstance(p, dict) and set(p) == {"inequalities"},
            "Unexpected parameters")
    items = p["inequalities"]
    require(isinstance(items, list) and len(items) == 2,
            "Expected two inequalities")
    roots = []
    for item in items:
        require(isinstance(item, dict)
                and set(item) == {"coefficients", "operator"},
                "Unexpected inequality data")
        coefficients = item["coefficients"]
        require(isinstance(coefficients, list) and len(coefficients) == 3
                and all(type(v) is int and abs(v) <= 200 for v in coefficients),
                "Invalid coefficients")
        require(item["operator"] in OPS, "Invalid operator")
        pair = roots_of(coefficients)
        require(all(abs(v) <= 6 and v.denominator <= 3 for v in pair),
                "Roots outside teaching bounds")
        roots.extend(pair)
    require(len(set(roots)) == 4, "Expected four distinct boundaries")
    first, second = map(intervals_for, items)
    result = intersect(first, second)
    require(result and result != first and result != second,
            "Both inequalities must constrain the answer")
    require(all(lo is not None and hi is not None and lo < hi
                for lo, hi, _, _ in result), "Expected bounded intervals")
    if level == 1:
        require(all(v.denominator == 1 for v in roots),
                "Expected integer roots")
        require(len(first) == len(second) == len(result) == 1,
                "Expected overlapping bounded solution sets")
    else:
        require(level == 2 and len(result) == 2,
                "Expected a disconnected intersection")
        require(any(v.denominator > 1 for v in roots),
                "Expected at least one fractional boundary")
    return result


def prompt_for(p):
    instruction = "Find all values of x that satisfy both inequalities."
    blocks = [rb.prose(instruction)]
    plain = []
    for item in p["inequalities"]:
        coefficients, op = item["coefficients"], item["operator"]
        text = polynomial(coefficients) + " " + op + " 0"
        tex = polynomial(coefficients, True) + " " + TEX[op] + " 0"
        plain.append(text)
        blocks.append(rb.equation(tex, text))
    return Content(instruction + " " + " and ".join(plain), blocks=tuple(blocks))


def answer_for(intervals):
    data, texts, maths = [], [], []
    for low, high, lc, hc in intervals:
        data.append({
            "lower": None if low is None else rational_text(low),
            "upper": None if high is None else rational_text(high),
            "lower_closed": lc, "upper_closed": hc,
        })
        if low == high:
            texts.append("x = " + rational_text(low))
            maths.append("x = " + rational_tex(low))
        elif low is None:
            op = "<=" if hc else "<"
            texts.append("x " + op + " " + rational_text(high))
            maths.append("x " + TEX[op] + " " + rational_tex(high))
        elif high is None:
            op = ">=" if lc else ">"
            texts.append("x " + op + " " + rational_text(low))
            maths.append("x " + TEX[op] + " " + rational_tex(low))
        else:
            left, right = "<=" if lc else "<", "<=" if hc else "<"
            texts.append("{} {} x {} {}".format(
                rational_text(low), left, right, rational_text(high)))
            maths.append("{} {} x {} {}".format(
                rational_tex(low), TEX[left], TEX[right], rational_tex(high)))
    return (
        {"kind": "interval_union", "variable": "x", "intervals": data},
        Content(" or ".join(texts), r"\quad\mathrm{or}\quad".join(maths)),
    )


def make_inequality(low, high, inside, rng):
    # (q*x-p)(s*x-r), so coefficients remain integers.
    p, q = low.numerator, low.denominator
    r, s = high.numerator, high.denominator
    coefficients = [q * s, -(q * r + s * p), p * r]
    op = rng.choice(("<", "<=") if inside else (">", ">="))
    if rng.choice((False, True)):
        coefficients = [-v for v in coefficients]
        op = REVERSE[op]
    return {"coefficients": coefficients, "operator": op}


class CombinedQuadraticInequalities:
    info = GeneratorInfo(
        id="algebra.inequalities.combined_quadratic", version=1,
        topic="algebra", subtopic="inequalities",
        title="Solve two quadratic inequalities together",
        difficulty_descriptions={
            1: "Intersect two bounded solution sets with integer boundaries.",
            2: "Find a disconnected intersection with fractional boundaries.",
        },
        tags=("quadratics", "inequalities", "intersection", "intervals"),
    )

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        pool = sorted({Fraction(n, d) for d in (
            (1,) if difficulty == 1 else (1, 2, 3))
            for n in range(-12, 13) if abs(Fraction(n, d)) <= 6})
        for _ in range(200):
            a, b, c, d = sorted(rng.sample(pool, 4))
            if difficulty == 1:
                items = [make_inequality(a, c, True, rng),
                         make_inequality(b, d, True, rng)]
            else:
                if all(v.denominator == 1 for v in (a, b, c, d)):
                    continue
                items = [make_inequality(a, d, True, rng),
                         make_inequality(b, c, False, rng)]
            rng.shuffle(items)
            p = {"inequalities": items}
            result = check_parameters(p, difficulty)
            break
        else:
            raise ValueError("Could not construct fractional boundaries")
        answer, display = answer_for(result)
        info = self.info
        question = Question(
            id=context.identity, generator_id=info.id,
            generator_version=info.version, topic=info.topic,
            subtopic=info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(p),
            answer=answer, answer_display=display, worked_solution=(),
            marks=5 if difficulty == 1 else 6, tags=info.tags,
            layout_hint=LayoutHint(working_lines=9), parameters=p,
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        require(type(question.difficulty) is int
                and question.difficulty in (1, 2), "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")
        result = check_parameters(question.parameters, question.difficulty)
        answer, display = answer_for(result)
        require(question.answer == answer, "Incorrect intersection")
        require(question.answer_display == display, "Answer display mismatch")
        require(question.prompt == prompt_for(question.parameters), "Prompt mismatch")
        return True

    def validate_independently(self, question):
        import sympy
        x = sympy.Symbol("x", real=True)
        relations = {"<": sympy.Lt, "<=": sympy.Le,
                     ">": sympy.Gt, ">=": sympy.Ge}
        sets = []
        for item in question.parameters["inequalities"]:
            a, b, c = item["coefficients"]
            relation = relations[item["operator"]](a*x*x + b*x + c, 0)
            sets.append(sympy.solve_univariate_inequality(
                relation, x, relational=False))
        actual = sympy.Intersection(*sets)
        pieces = []
        for item in question.answer["intervals"]:
            low = -sympy.oo if item["lower"] is None else sympy.Rational(item["lower"])
            high = sympy.oo if item["upper"] is None else sympy.Rational(item["upper"])
            pieces.append(sympy.Interval(
                low, high, left_open=not item["lower_closed"],
                right_open=not item["upper_closed"]))
        require(actual == sympy.Union(*pieces), "Independent intersection disagrees")
        return True