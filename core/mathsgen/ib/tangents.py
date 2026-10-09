"""IB AI SL differentiation: gradients, tangents and normals.

Functions are sums of terms c x^n, including negative n (as in
f(x) = 3x - 1 + 4x^-2), stored as [coefficient text, power] pairs.
Level 3 cubics are built from the x-values where f'(x) = k, so those
points are exact; level 4 hides a and b behind a point and a normal.
"""
from fractions import Fraction
from math import isqrt

from ..core import GeneratorInfo, rational_text, require
from ..family import GeneratorFamily
from .. import rich_blocks as rb
from . import common as ib


# --- Editable pools ---------------------------------------------------------
FORMS = ("quadratic", "cubic", "negative")
SMALL = tuple(v for v in range(-9, 10) if v)
LEADING = (-3, -2, -1, 1, 2, 3, 4, 5)
POINTS = (-4, -3, -2, -1, 1, 2, 3, 4)
CUBIC_LEADING = (-2, -1, 1, 2)


# ------------------------------------------------------------ mathematics

def as_terms(stored):
    return [(Fraction(c), p) for c, p in stored]


def evaluate(terms, x):
    x = Fraction(x)
    return sum(c * x ** p for c, p in terms)


def derivative(terms):
    return [(c * p, p - 1) for c, p in terms if p != 0 and c != 0]


def poly_text(terms, tex=False):
    """Descending powers: 3x^2 - 4x + 1 or with x^-2 for negative powers."""
    pieces = []
    for coefficient, power in sorted(terms, key=lambda t: -t[1]):
        if coefficient == 0:
            continue
        size = abs(coefficient)
        number = ib.exact_or_fraction(size)
        if power == 0:
            body = number
        else:
            if size == 1:
                number = ""
            if power == 1:
                body = number + "x"
            elif tex:
                body = number + "x^{" + str(power) + "}"
            else:
                body = number + "x^" + str(power)
        if pieces:
            pieces.append(" {} {}".format("-" if coefficient < 0 else "+", body))
        else:
            pieces.append(("-" if coefficient < 0 else "") + body)
    return "".join(pieces) or "0"


def line_text(gradient, intercept):
    gradient, intercept = Fraction(gradient), Fraction(intercept)
    if gradient == 0:
        return "y = " + ib.exact_or_fraction(intercept)
    # Exact when short; otherwise 3 s.f., as IB mark schemes give line equations.
    slope = {1: "", -1: "-"}.get(gradient, ib.nice(gradient))
    text = "y = {}x".format(slope)
    if intercept:
        text += " {} {}".format("-" if intercept < 0 else "+", ib.nice(abs(intercept)))
    return text


def linear_combination(pairs, constant):
    """'4a + 2b = 14' from [(4, 'a'), (2, 'b')] and 14."""
    pieces = []
    for coefficient, name in pairs:
        if coefficient == 0:
            continue
        size = abs(coefficient)
        body = ("" if size == 1 else ib.exact_or_fraction(size)) + name
        if pieces:
            pieces.append(" {} {}".format("-" if coefficient < 0 else "+", body))
        else:
            pieces.append(("-" if coefficient < 0 else "") + body)
    return "".join(pieces) + " = " + ib.exact_or_fraction(constant)


def gradient_points(terms, k):
    """Exact x-values where f'(x) = k for a cubic, or None if not rational."""
    slope = dict((p, c) for c, p in derivative(terms))
    a, b, c = slope.get(2, 0), slope.get(1, 0), slope.get(0, 0) - k
    disc = b * b - 4 * a * c
    if a == 0 or disc <= 0:
        return None
    numerator, denominator = disc.numerator, disc.denominator
    root_n, root_d = isqrt(numerator), isqrt(denominator)
    if root_n * root_n != numerator or root_d * root_d != denominator:
        return None
    root = Fraction(root_n, root_d)
    return sorted(((-b - root) / (2 * a), (-b + root) / (2 * a)))


def hidden_coefficients(p):
    """(a, b) for y = ax^2 + bx + c through T with the given normal gradient."""
    x0, y0, c = Fraction(p["x"]), Fraction(p["y"]), Fraction(p["c"])
    slope = -1 / Fraction(p["normal"])
    a = (y0 - c - slope * x0) / (-x0 * x0)
    return a, slope - 2 * a * x0


def function_runs(terms, label="f(x)"):
    return [rb.maths(label + " = " + poly_text(terms, True), label + " = " + poly_text(terms))]


# ------------------------------------------------------------ generator

class TangentsNormals(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.calculus.tangents_normals",
        version=1,
        topic=ib.TOPIC,
        subtopic="differentiation",
        title="Gradients, tangents and normals",
        difficulty_descriptions={
            1: "Differentiate (including negative powers) and find a gradient.",
            2: "Gradient, then the equations of the tangent and the normal.",
            3: "Find the points on a cubic where the gradient takes a given value.",
            4: "Find a and b from a point on the curve and the gradient of the normal.",
        },
        tags=ib.BASE_TAGS + ("differentiation", "tangents", "normals", "gradients"),
    )
    keys = {
        1: {"form", "terms", "x"},
        2: {"form", "terms", "x"},
        3: {"terms", "gradient"},
        4: {"c", "x", "y", "normal"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        if level in (1, 2):
            form = rng.choice(FORMS)
            if form == "quadratic":
                terms = [[rng.choice(LEADING), 2], [rng.choice(SMALL), 1], [rng.choice(SMALL), 0]]
            elif form == "cubic":
                terms = [[rng.choice((-2, -1, 1, 2)), 3], [rng.choice(SMALL), 2],
                         [rng.choice(SMALL), 1], [rng.choice(SMALL), 0]]
            else:
                terms = [[rng.choice(LEADING), rng.choice((1, 2))],
                         [rng.choice(SMALL), rng.choice((-1, -2))], [rng.choice(SMALL), 0]]
            return {"form": form, "terms": [[str(c), p] for c, p in terms],
                    "x": rng.choice(POINTS)}
        if level == 3:
            a = rng.choice(CUBIC_LEADING)
            first = rng.randint(-4, 3)
            second = first + 2 * rng.randint(1, 3)
            k = rng.randint(-12, 12)
            b = Fraction(-3 * a * (first + second), 2)
            c = 3 * a * first * second + k
            terms = [[str(a), 3], [rational_text(b), 2], [str(c), 1], [str(rng.choice(SMALL)), 0]]
            return {"terms": terms, "gradient": k}
        a, b, x0 = rng.choice(LEADING), rng.randint(-6, 6), rng.choice(POINTS)
        slope = 2 * a * x0 + b
        c = rng.randint(-10, 10)
        return {"c": c, "x": x0, "y": a * x0 * x0 + b * x0 + c,
                "normal": rational_text(Fraction(-1, slope)) if slope else "0"}

    def check_rules(self, p, level):
        if level == 4:
            for key in ("c", "x", "y"):
                require(type(p[key]) is int, "Values must be integers")
            require(p["x"] in POINTS, "Point outside pool")
            require(isinstance(p["normal"], str) and Fraction(p["normal"]) != 0, "Normal gradient outside rules")
            a, b = hidden_coefficients(p)
            require(a in LEADING and b.denominator == 1 and -6 <= b <= 6, "Coefficients outside pools")
            return
        terms = p["terms"]
        require(isinstance(terms, list) and all(
            isinstance(t, list) and len(t) == 2 and isinstance(t[0], str) and type(t[1]) is int
            for t in terms), "Terms outside rules")
        parsed = as_terms(terms)
        require(len({power for _, power in parsed}) == len(parsed), "Repeated power")
        if level == 3:
            require(type(p["gradient"]) is int, "Gradient must be an integer")
            require(parsed[0][1] == 3 and parsed[0][0] in CUBIC_LEADING, "Level 3 needs a cubic")
            points = gradient_points(parsed, p["gradient"])
            require(points is not None and all(x.denominator == 1 for x in points),
                    "Gradient points must be integers")
            return
        require(p["form"] in FORMS, "Unknown form")
        require(p["x"] in POINTS, "Point outside pool")
        require(all(c != 0 for c, _ in parsed) and len(parsed) >= 3, "Every term must be nonzero")
        powers = sorted(power for _, power in parsed)
        allowed = {"quadratic": [0, 1, 2], "cubic": [0, 1, 2, 3]}
        if p["form"] in allowed:
            require(powers == allowed[p["form"]], "Powers do not match the form")
        else:
            require(len(powers) == 3 and powers[0] in (-2, -1) and powers[1] == 0
                    and powers[2] in (1, 2), "Powers do not match the form")
        if level == 2:
            require(evaluate(derivative(parsed), p["x"]) != 0, "Tangent must not be horizontal")

    def parts(self, p, level):
        if level == 4:
            a, b = hidden_coefficients(p)
            x0, y0, c = p["x"], p["y"], p["c"]
            slope = -1 / Fraction(p["normal"])
            curve = "y = ax^2 + bx {} {}".format("-" if c < 0 else "+", abs(c)) if c else "y = ax^2 + bx"
            curve_tex = curve.replace("x^2", "x^{2}")
            context = [[rb.text("The curve "), rb.maths(curve_tex, curve),
                        rb.text(" passes through T({}, {}). The normal to the curve at T has "
                                "gradient {}.".format(x0, y0, ib.exact_or_fraction(Fraction(p["normal"]))))]]
            return ib.assemble(context, [
                ib.part("a", "Use the point T to write down an equation in a and b.", 2,
                        linear_combination([(x0 * x0, "a"), (x0, "b")], y0 - c)),
                ib.part("b", "Find a second equation in a and b, using the gradient of the normal.", 3,
                        linear_combination([(2 * x0, "a"), (1, "b")], slope)),
                ib.part("c", "Hence find the value of a and the value of b.", 2,
                        "a = {}, b = {}".format(ib.exact_or_fraction(a), ib.exact_or_fraction(b)), a),
            ])
        terms = as_terms(p["terms"])
        slope_terms = derivative(terms)
        if level == 3:
            points = gradient_points(terms, p["gradient"])
            context = [function_runs(terms)]
            shown = " and ".join("({}, {})".format(ib.exact_or_fraction(x),
                                                   ib.exact_or_fraction(evaluate(terms, x)))
                                 for x in points)
            return ib.assemble(context, [
                ib.part("a", "Find f'(x).", 2, "f'(x) = " + poly_text(slope_terms)),
                ib.part("b", "Find the coordinates of the points on the graph of y = f(x) where the "
                        "gradient is {}.".format(p["gradient"]), 3, shown, points[0]),
            ])
        x0 = p["x"]
        gradient = evaluate(slope_terms, x0)
        context = [function_runs(terms)]
        if level == 1:
            return ib.assemble(context, [
                ib.part("a", "Find f'(x).", 2, "f'(x) = " + poly_text(slope_terms)),
                ib.part("b", "Find the gradient of the graph of y = f(x) at x = {}.".format(x0), 2,
                        ib.exact_or_fraction(gradient), gradient),
            ])
        y0 = evaluate(terms, x0)
        normal = -1 / gradient
        return ib.assemble(context, [
            ib.part("a", "Find the gradient of the graph of y = f(x) at x = {}.".format(x0), 2,
                    ib.exact_or_fraction(gradient), gradient),
            ib.part("b", "Find the equation of the tangent at x = {}, in the form y = mx + c.".format(x0),
                    2, line_text(gradient, y0 - gradient * x0), y0 - gradient * x0),
            ib.part("c", "Find the equation of the normal at x = {}, in the form y = mx + c.".format(x0),
                    2, line_text(normal, y0 - normal * x0), y0 - normal * x0),
        ])

    def validate_independently(self, question):
        """SymPy differentiates and solves."""
        import sympy
        p, level = question.parameters, question.difficulty
        values, shown = ib.answer_values(question), ib.answer_shown(question)
        x = sympy.Symbol("x")
        if level == 4:
            a, b = sympy.symbols("a b")
            curve = a * x ** 2 + b * x + p["c"]
            slope = -1 / sympy.Rational(p["normal"])
            solution = sympy.solve([curve.subs(x, p["x"]) - p["y"],
                                    sympy.diff(curve, x).subs(x, p["x"]) - slope], [a, b])
            require(sympy.Rational(values["c"]) == solution[a]
                    and "b = {}".format(ib.exact_or_fraction(Fraction(str(solution[b])))) in shown["c"],
                    "Independent a and b failed")
            return True
        f = sum(sympy.Rational(c) * x ** power for c, power in p["terms"])
        slope = sympy.diff(f, x)
        if level == 3:
            roots = sorted(sympy.solve(sympy.Eq(slope, p["gradient"]), x))
            require(sympy.Rational(values["b"]) == roots[0], "Independent gradient points failed")
            for root in roots:
                require("({}, {})".format(root, f.subs(x, root)) in shown["b"].replace(" ", " "),
                        "Independent coordinates failed")
            return True
        gradient = slope.subs(x, p["x"])
        label = "b" if level == 1 else "a"
        require(sympy.Rational(values[label]) == gradient, "Independent gradient failed")
        if level == 2:
            y0 = f.subs(x, p["x"])
            # Intercepts can be thirds or sevenths, stored to 12 s.f.: compare numerically.
            require(ib.close(values["b"], float(y0 - gradient * p["x"])), "Independent tangent failed")
            require(ib.close(values["c"], float(y0 + sympy.Rational(p["x"]) / gradient)),
                    "Independent normal failed")
        return True