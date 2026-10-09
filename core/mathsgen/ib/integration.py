"""IB AI SL integration of polynomials.

Level 1 indefinite and definite integrals; level 2 f(x) from f'(x) and a
point; level 3 the same, then an area under the curve; level 4 the
smooth-join design (three equations in a, b and c, then an area).
Everything is exact; the independent check uses SymPy.
"""
from fractions import Fraction

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from .. import rich_blocks as rb
from . import common as ib
from .tangents import evaluate, linear_combination, poly_text


# --- Editable pools ---------------------------------------------------------
MULTIPLES = tuple(v for v in range(-4, 5) if v)
CONSTANTS = tuple(v for v in range(-9, 10) if v)
JOIN_GRADIENTS = ("-0.4", "-0.6", "-0.8", "-1", "-1.2", "-1.5", "-2")
JOIN_HEIGHTS = ("0.5", "1", "1.2", "1.5", "2")


# ------------------------------------------------------------ mathematics

def antiderivative(terms):
    return [(Fraction(c) / (p + 1), p + 1) for c, p in terms]


def definite(terms, low, high):
    whole = antiderivative(terms)
    return evaluate(whole, high) - evaluate(whole, low)


def derivative_terms(p):
    """f'(x) built so every antiderivative coefficient is a whole number."""
    return [((power + 1) * k, power) for k, power in p["slope"]]


def curve(p):
    """f(x) through (x0, y0) for the stored f'(x)."""
    whole = antiderivative(derivative_terms(p))
    constant = p["y0"] - evaluate(whole, p["x0"])
    return whole + [(constant, 0)]


def join(p):
    """(a, b, c) for h = ax^2 + bx + c with h(end) = height, h'(near) = g, h'(low) = 0."""
    g, height = Fraction(p["gradient"]), Fraction(p["height"])
    a = g / (2 * (p["near"] - p["low"]))
    b = -2 * a * p["low"]
    c = height - a * p["end"] ** 2 - b * p["end"]
    return a, b, c


def runs(label, terms):
    return rb.maths(label + " = " + poly_text(terms, True), label + " = " + poly_text(terms))


def positive_between(terms, low, high, steps=400):
    return all(evaluate(terms, Fraction(low) + Fraction(high - low) * i / steps) > 0
               for i in range(steps + 1))


# ------------------------------------------------------------ generator

class Integration(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.calculus.integration",
        version=1,
        topic=ib.TOPIC,
        subtopic="integration",
        title="Integration and areas",
        difficulty_descriptions={
            1: "An indefinite integral and an exact definite integral.",
            2: "Find f(x) from f'(x) and a point on the curve.",
            3: "Find f(x) from f'(x) and a point, then an area under the curve.",
            4: "Smooth join: equations in a, b and c from conditions, then an area.",
        },
        tags=ib.BASE_TAGS + ("integration", "areas", "boundary_conditions"),
    )
    keys = {
        1: {"slope", "low", "high"},
        2: {"slope", "x0", "y0", "x1"},
        3: {"slope", "x0", "y0", "low", "high"},
        4: {"low", "near", "end", "gradient", "height"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        if level == 4:
            low = rng.randint(2, 4)
            return {"low": low, "near": low - 1, "end": low + rng.randint(1, 2),
                    "gradient": rng.choice(JOIN_GRADIENTS), "height": rng.choice(JOIN_HEIGHTS)}
        powers = sorted(rng.sample((0, 1, 2, 3), rng.choice((2, 3))), reverse=True)
        slope = [[rng.choice(MULTIPLES), power] for power in powers]
        if level == 1:
            low = rng.randint(-2, 2)
            return {"slope": slope, "low": low, "high": low + rng.randint(1, 3)}
        p = {"slope": slope, "x0": rng.randint(-2, 3), "y0": rng.randint(-10, 15)}
        if level == 2:
            p["x1"] = rng.choice([v for v in range(-3, 5) if v != p["x0"]])
        else:
            low = rng.randint(-1, 2)
            p.update(low=low, high=low + rng.randint(1, 3))
        return p

    def check_rules(self, p, level):
        if level == 4:
            ib.require_int(p["low"], 2, 4, "Turning point outside bounds")
            require(p["near"] == p["low"] - 1 and type(p["end"]) is int
                    and p["low"] < p["end"] <= p["low"] + 2, "Join points outside rules")
            require(p["gradient"] in JOIN_GRADIENTS and p["height"] in JOIN_HEIGHTS, "Conditions outside pools")
            a, b, c = join(p)
            terms = [(a, 2), (b, 1), (c, 0)]
            require(positive_between(terms, p["near"], p["end"]), "Slide must stay above the ground")
            return
        slope = p["slope"]
        require(isinstance(slope, list) and 2 <= len(slope) <= 3 and all(
            isinstance(t, list) and len(t) == 2 and t[0] in MULTIPLES and t[1] in (0, 1, 2, 3)
            for t in slope), "Derivative outside rules")
        require(len({t[1] for t in slope}) == len(slope), "Repeated power")
        if level == 1:
            require(type(p["low"]) is int and type(p["high"]) is int and p["low"] < p["high"],
                    "Bounds outside rules")
            require(definite(derivative_terms(p), p["low"], p["high"]) != 0, "Integral must be nonzero")
            return
        require(type(p["x0"]) is int and type(p["y0"]) is int, "Point must be integers")
        if level == 2:
            require(type(p["x1"]) is int and p["x1"] != p["x0"], "Second point outside rules")
        else:
            require(type(p["low"]) is int and type(p["high"]) is int and p["low"] < p["high"],
                    "Bounds outside rules")
            require(positive_between(curve(p), p["low"], p["high"]), "Curve must stay above the x-axis")

    def parts(self, p, level):
        if level == 4:
            a, b, c = join(p)
            terms = [(a, 2), (b, 1), (c, 0)]
            low, near, end = p["low"], p["near"], p["end"]
            g, height = Fraction(p["gradient"]), Fraction(p["height"])
            area = definite(terms, near, end)
            context = [[rb.text("Part of a water slide, for {} <= x <= {}, is modelled by ".format(near, end)),
                        rb.maths("h(x)=ax^{2}+bx+c", "h(x) = ax^2 + bx + c"),
                        rb.text(", where h is the height in metres above the ground.")],
                       "The design requires h({}) = {}, h'({}) = {} and h'({}) = 0.".format(
                           end, p["height"], near, p["gradient"], low)]
            equations = "; ".join([
                linear_combination([(end * end, "a"), (end, "b"), (1, "c")], height),
                linear_combination([(2 * near, "a"), (1, "b")], g),
                linear_combination([(2 * low, "a"), (1, "b")], 0),
            ])
            return ib.assemble(context, [
                ib.part("a", "Write down three equations in a, b and c.", 4, equations),
                ib.part("b", "Hence find a, b and c.", 2, "a = {}, b = {}, c = {}".format(
                    ib.exact_or_fraction(a), ib.exact_or_fraction(b), ib.exact_or_fraction(c)), a),
                ib.part("c", "Find the area under the slide between x = {} and x = {}.".format(near, end), 2,
                        "{} m^2".format(ib.nice(area)), area),
            ])
        slope = derivative_terms(p)
        if level == 1:
            value = definite(slope, p["low"], p["high"])
            expression = poly_text(slope)
            return ib.assemble([[rb.text("Let "), runs("f(x)", slope), rb.text(".")]], [
                ib.part("a", "Find the integral of f(x) with respect to x.", 2,
                        poly_text(antiderivative(slope)) + " + C"),
                ib.part("b", "Find the exact value of the integral of f(x) from x = {} to x = {}.".format(
                    p["low"], p["high"]), 2, ib.exact_or_fraction(value), value),
            ])
        f = curve(p)
        context = [[rb.text("The gradient of a curve is given by "), runs("f'(x)", slope),
                    rb.text(". The curve passes through the point ({}, {}).".format(p["x0"], p["y0"]))]]
        find_f = ib.part("a", "Find f(x).", 4, "f(x) = " + poly_text(f), f[-1][0])
        if level == 2:
            later = evaluate(f, p["x1"])
            return ib.assemble(context, [
                find_f,
                ib.part("b", "Find f({}).".format(p["x1"]), 1, ib.exact_or_fraction(later), later),
            ])
        area = definite(f, p["low"], p["high"])
        return ib.assemble(context, [
            find_f,
            ib.part("b", "Write down an integral for the area of the region enclosed by the graph of "
                    "y = f(x), the x-axis and the lines x = {} and x = {}.".format(p["low"], p["high"]), 1,
                    "Area = integral from {} to {} of ({}) dx".format(p["low"], p["high"], poly_text(f))),
            ib.part("c", "Find this area.", 2, ib.nice(area), area),
        ])

    def validate_independently(self, question):
        """SymPy integrates and solves the conditions."""
        import sympy
        p, level = question.parameters, question.difficulty
        values = ib.answer_values(question)
        x = sympy.Symbol("x")
        if level == 4:
            a, b, c = sympy.symbols("a b c")
            h = a * x ** 2 + b * x + c
            solution = sympy.solve([
                h.subs(x, p["end"]) - sympy.Rational(p["height"]),
                sympy.diff(h, x).subs(x, p["near"]) - sympy.Rational(p["gradient"]),
                sympy.diff(h, x).subs(x, p["low"])], [a, b, c])
            require(ib.close(values["b"], float(solution[a])), "Independent a failed")
            area = sympy.integrate(h.subs(solution), (x, p["near"], p["end"]))
            require(ib.close(values["c"], float(area)), "Independent area failed")
            return True
        slope = sum(sympy.Integer((power + 1) * k) * x ** power for k, power in p["slope"])
        if level == 1:
            value = sympy.integrate(slope, (x, p["low"], p["high"]))
            require(sympy.Rational(values["b"]) == value, "Independent definite integral failed")
            return True
        constant = sympy.Symbol("C")
        f = sympy.integrate(slope, x) + constant
        f = f.subs(constant, sympy.solve(f.subs(x, p["x0"]) - p["y0"], constant)[0])
        require(ib.close(values["a"], float(f.subs(x, 0))), "Independent constant failed")
        if level == 2:
            require(ib.close(values["b"], float(f.subs(x, p["x1"]))), "Independent value failed")
        else:
            require(ib.close(values["c"], float(sympy.integrate(f, (x, p["low"], p["high"])))),
                    "Independent area failed")
        return True