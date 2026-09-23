"""Function notation: evaluation, inverses, composites and combined problems.

Every function is stored as exact integer coefficients, so each question can
be rebuilt from its parameters and checked against what was displayed.

Polynomials are ascending coefficient lists: [c0, c1, c2] means
c0 + c1 x + c2 x^2.

Inverse questions store a Mobius form [p, q, r, s] meaning
(p x + q) / (r x + s). Its inverse is (s x - q) / (p - r x), which covers
ax + b, (ax + b)/c, a/(x + b) and (ax + b)/(x + c) with one rule.

Composite labels follow GCSE notation: fg(x) means f(g(x)).
"""
from fractions import Fraction
from math import gcd, isqrt

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from . import rich_blocks as rb
from .family import GeneratorFamily


# ------------------------------------------------------------ choice pools
# Editable: widen or narrow these to change variety. Validation checks
# membership, so emitted questions always stay inside these pools.

NONZERO_CONSTANTS = tuple(v for v in range(-12, 13) if v != 0)
SMALL_CONSTANTS = tuple(v for v in range(-9, 10) if v != 0)
TINY_CONSTANTS = tuple(v for v in range(-6, 7) if v != 0)
LINEAR_SLOPES = (2, 3, 4, 5, 6, 7, 8, 9, -2, -3, -4, -5)
COMPOSITE_SLOPES = (2, 3, 4, 5, -2, -3)
QUADRATIC_MIDDLE = tuple(v for v in range(-5, 6) if v != 0)
INVERSE_NUMERATORS = tuple(range(2, 13)) + (-2, -3, -4, -5, -6)
SELF_INVERSE_SLOPES = (2, 3, 4, 5, 6, -2, -3, -4)
UNKNOWN_CONSTANT_SLOPES = (2, 3, 4, 5, -2, -3)
UNKNOWN_CONSTANT_INPUTS = (1, 2, 3, 4, 5, -1, -2)
SUBSTITUTIONS = (
    [1, 1], [2, 1], [3, 1], [-1, 1], [-2, 1], [-3, 1],
    [0, 2], [0, 3], [0, -1], [1, 2], [-1, 2], [1, 3], [-1, 3],
)


# ------------------------------------------------------ polynomial arithmetic

def trimmed(coefficients):
    values = list(coefficients)
    while len(values) > 1 and values[-1] == 0:
        values.pop()
    return values


def poly_add(first, second):
    size = max(len(first), len(second))
    return trimmed([
        (first[i] if i < len(first) else 0)
        + (second[i] if i < len(second) else 0)
        for i in range(size)
    ])


def poly_multiply(first, second):
    result = [0] * (len(first) + len(second) - 1)
    for i, a in enumerate(first):
        for j, b in enumerate(second):
            result[i + j] += a * b
    return trimmed(result)


def compose(outer, inner):
    """Coefficients of outer(inner(x))."""
    result = [0]
    power = [1]
    for coefficient in outer:
        result = poly_add(result, [coefficient * v for v in power])
        power = poly_multiply(power, inner)
    return result


def evaluate(coefficients, value):
    return sum(c * value ** i for i, c in enumerate(coefficients))


# ------------------------------------------------------------- formatting

def terms_text(terms, tex=False):
    """Join (coefficient, degree) terms in the given order, skipping zeros."""
    pieces = []
    for value, degree in terms:
        if value == 0:
            continue
        magnitude = abs(value)
        if degree == 0:
            body = str(magnitude)
        else:
            body = ("" if magnitude == 1 else str(magnitude)) + "x"
            if degree > 1:
                body += ("^{" + str(degree) + "}") if tex else ("^" + str(degree))
        if pieces:
            pieces.append((" - " if value < 0 else " + ") + body)
        else:
            pieces.append(("-" if value < 0 else "") + body)
    return "".join(pieces) or "0"


def poly_text(coefficients, tex=False):
    """Descending powers, e.g. [3, -2, 1] -> x^2 - 2x + 3."""
    terms = [(c, degree) for degree, c in enumerate(coefficients)]
    return terms_text(list(reversed(terms)), tex)


def linear_text(constant, slope, tex=False):
    """Lead with a positive term: 5 - 2x rather than -2x + 5."""
    if slope < 0 < constant:
        return terms_text([(constant, 0), (slope, 1)], tex)
    return terms_text([(slope, 1), (constant, 0)], tex)


def bracketed(text, coefficients):
    return "(" + text + ")" if all(c != 0 for c in coefficients) else text


def fraction_text(numerator, denominator, tex=False):
    """numerator/denominator are ascending linear pairs [constant, slope]."""
    if denominator == [1, 0]:
        return linear_text(numerator[0], numerator[1], tex)
    top = linear_text(numerator[0], numerator[1], tex)
    bottom = linear_text(denominator[0], denominator[1], tex)
    if tex:
        return r"\frac{" + top + "}{" + bottom + "}"
    return bracketed(top, numerator) + "/" + bracketed(bottom, denominator)


def definition(name, coefficients, tex=False):
    return name + "(x) = " + poly_text(coefficients, tex)


def definitions(named, tex=False):
    joiner = r",\quad " if tex else " and "
    return joiner.join(definition(name, c, tex) for name, c in named)


def capitalised(task):
    return task[0].upper() + task[1:]


def prompt_content(plain, tex, task, task_runs):
    """Definitions as a display equation, then the task with inline maths.

    task is the lowercase plain-text task used in the CLI fallback;
    task_runs are the same words as rich runs, without the full stop.
    """
    return Content(
        "{}. {}.".format(plain, capitalised(task)),
        blocks=(
            rb.equation(tex, plain),
            rb.paragraph(*task_runs, rb.text(".")),
        ),
    )


def number_answer(value):
    return {"kind": "rational", "value": rational_text(value)}


def number_display(label, value):
    text = "{} = {}".format(label, rational_text(value))
    return Content(text, text)


def polynomial_answer(coefficients):
    return {"kind": "polynomial", "coefficients": list(coefficients)}


def polynomial_display(label, coefficients):
    return Content(
        label + " = " + poly_text(coefficients),
        label + " = " + poly_text(coefficients, True),
    )


# -------------------------------------------------------------- rule checks

def require_integers(values, message):
    require(
        isinstance(values, list) and all(type(v) is int for v in values),
        message,
    )


def is_linear(coefficients, slopes, constants):
    return (
        isinstance(coefficients, list) and len(coefficients) == 2
        and all(type(v) is int for v in coefficients)
        and coefficients[1] in slopes and coefficients[0] in constants
    )


def is_simple_quadratic(coefficients):
    """x^2 + c with a nonzero constant."""
    return (
        isinstance(coefficients, list) and len(coefficients) == 3
        and all(type(v) is int for v in coefficients)
        and coefficients[2] == 1 and coefficients[1] == 0
        and coefficients[0] in SMALL_CONSTANTS
    )


def is_full_quadratic(coefficients):
    """ax^2 + bx + c with a in 1..2 and b nonzero."""
    return (
        isinstance(coefficients, list) and len(coefficients) == 3
        and all(type(v) is int for v in coefficients)
        and coefficients[2] in (1, 2) and coefficients[1] in QUADRATIC_MIDDLE
        and -6 <= coefficients[0] <= 6
    )


def composite_linear(coefficients):
    return is_linear(coefficients, COMPOSITE_SLOPES, SMALL_CONSTANTS)


def ordered(parameters):
    """(outer, inner) for the requested composite order."""
    f, g = parameters["f"], parameters["g"]
    return (f, g) if parameters["order"] == "fg" else (g, f)


# ------------------------------------------------------- SymPy helpers

def sympy_poly(coefficients, symbol):
    import sympy
    return sum(sympy.Integer(c) * symbol ** i for i, c in enumerate(coefficients))


# ------------------------------------------------------------ shared flow

# The shared flow lives in family.py; this name is kept for existing readers.
FunctionFamily = GeneratorFamily


# ------------------------------------------------------------- evaluation

class EvaluateFunctions(FunctionFamily):
    info = GeneratorInfo(
        id="algebra.functions.evaluate",
        version=2,
        topic="algebra",
        subtopic="functions",
        title="Evaluate and use function notation",
        difficulty_descriptions={
            1: "Evaluate a linear function at a positive integer.",
            2: "Evaluate a quadratic function at a negative integer.",
            3: "Solve f(x) = k for a linear function.",
            4: "Substitute an expression, such as f(x + 2), and simplify.",
        },
        tags=("functions", "function_notation", "substitution"),
    )
    keys = {
        1: {"f", "input"}, 2: {"f", "input"},
        3: {"f", "target"}, 4: {"f", "substitution"},
    }

    def build(self, level, rng):
        if level == 1:
            return {
                "f": [rng.choice(NONZERO_CONSTANTS), rng.choice(LINEAR_SLOPES)],
                "input": rng.randint(1, 10),
            }
        if level == 2:
            return {
                "f": [rng.choice(SMALL_CONSTANTS), rng.randint(-6, 6), rng.randint(1, 3)],
                "input": rng.randint(-5, -1),
            }
        if level == 3:
            constant = rng.choice(NONZERO_CONSTANTS)
            slope = rng.choice(LINEAR_SLOPES)
            solution = rng.randint(-6, 10)
            return {"f": [constant, slope], "target": slope * solution + constant}
        return {
            "f": [rng.randint(-9, 9), rng.choice(QUADRATIC_MIDDLE), rng.randint(1, 2)],
            "substitution": list(rng.choice(SUBSTITUTIONS)),
        }

    def check_rules(self, p, level):
        f = p["f"]
        if level in (1, 3):
            require(is_linear(f, LINEAR_SLOPES, NONZERO_CONSTANTS), "Function outside linear rules")
        if level == 1:
            require(type(p["input"]) is int and 1 <= p["input"] <= 10, "Input outside bounds")
        elif level == 2:
            require_integers(f, "Coefficients must be integers")
            require(
                len(f) == 3 and f[2] in (1, 2, 3) and -6 <= f[1] <= 6
                and f[0] in SMALL_CONSTANTS,
                "Function outside quadratic rules",
            )
            require(type(p["input"]) is int and -5 <= p["input"] <= -1, "Input must be small and negative")
        elif level == 3:
            require(type(p["target"]) is int, "Target must be an integer")
            solution = Fraction(p["target"] - f[0], f[1])
            require(solution.denominator == 1 and -6 <= solution <= 10, "Solution outside bounds")
        else:
            require_integers(f, "Coefficients must be integers")
            require(
                len(f) == 3 and f[2] in (1, 2) and f[1] in QUADRATIC_MIDDLE
                and -9 <= f[0] <= 9,
                "Function outside quadratic rules",
            )
            require_integers(p["substitution"], "Substitution must be integers")
            require(p["substitution"] in [list(s) for s in SUBSTITUTIONS], "Substitution outside rules")

    def parts(self, p, level):
        f = p["f"]
        plain, tex = definition("f", f), definition("f", f, True)

        if level in (1, 2):
            label = "f({})".format(p["input"])
            value = evaluate(f, p["input"])
            task = "find " + label
            runs = [rb.text("Find "), rb.maths(label, label)]
            answer, shown = number_answer(value), number_display(label, value)
            marks, lines = (1 if level == 1 else 2), 3
        elif level == 3:
            solution = (p["target"] - f[0]) // f[1]
            equation_text = "f(x) = {}".format(p["target"])
            task = "solve " + equation_text
            runs = [rb.text("Solve "), rb.maths(equation_text, equation_text)]
            answer, shown = number_answer(solution), number_display("x", solution)
            marks, lines = 2, 4
        else:
            label = "f({})".format(poly_text(p["substitution"]))
            result = compose(f, p["substitution"])
            task = "find and simplify an expression for " + label
            runs = [rb.text("Find and simplify an expression for "), rb.maths(label, label)]
            answer, shown = polynomial_answer(result), polynomial_display(label, result)
            marks, lines = 3, 6
        return {
            "prompt": prompt_content(plain, tex, task, runs),
            "answer": answer, "answer_display": shown,
            "marks": marks, "working_lines": lines,
        }

    def validate_independently(self, question):
        """Substitute or solve directly with SymPy."""
        import sympy
        x = sympy.Symbol("x")
        p, level = question.parameters, question.difficulty
        f = sympy_poly(p["f"], x)
        if level in (1, 2):
            expected = sympy.Rational(question.answer["value"])
            require(f.subs(x, p["input"]) == expected, "Independent evaluation failed")
        elif level == 3:
            solutions = sympy.solve(sympy.Eq(f, p["target"]), x)
            require(solutions == [sympy.Rational(question.answer["value"])], "Independent solve failed")
        else:
            substituted = sympy.expand(f.subs(x, sympy_poly(p["substitution"], x)))
            given = sympy_poly(question.answer["coefficients"], x)
            require(sympy.expand(substituted - given) == 0, "Independent substitution failed")
        return True


# ---------------------------------------------------------------- inverses

def inverse_of(mobius):
    """Canonical inverse of (p x + q)/(r x + s) as (numerator, denominator).

    The denominator leads positively and common factors are removed.
    """
    p, q, r, s = mobius
    numerator, denominator = [-q, s], [p, -r]
    if denominator[1] < 0 or (denominator[1] == 0 and denominator[0] < 0):
        numerator = [-v for v in numerator]
        denominator = [-v for v in denominator]
    common = gcd(gcd(numerator[0], numerator[1]), gcd(denominator[0], denominator[1]))
    return [v // common for v in numerator], [v // common for v in denominator]


def mobius_text(mobius, tex=False):
    p, q, r, s = mobius
    if r == 0 and s == 1:
        return poly_text([q, p], tex)
    return fraction_text([q, p], [s, r], tex)


class InverseFunctions(FunctionFamily):
    info = GeneratorInfo(
        id="algebra.functions.inverse",
        version=2,
        topic="algebra",
        subtopic="functions",
        title="Find an inverse function",
        difficulty_descriptions={
            1: "Invert f(x) = ax + b.",
            2: "Invert f(x) = (ax + b)/c.",
            3: "Invert f(x) = a/(x + b).",
            4: "Invert f(x) = (ax + b)/(x + c), collecting x on one side.",
        },
        tags=("functions", "inverse_functions", "rearranging"),
    )
    keys = {1: {"mobius"}, 2: {"mobius"}, 3: {"mobius"}, 4: {"mobius"}}

    def build(self, level, rng):
        if level == 1:
            return {"mobius": [rng.randint(2, 9), rng.choice(NONZERO_CONSTANTS), 0, 1]}
        if level == 2:
            pairs = [(a, c) for a in range(1, 8) for c in range(2, 7) if gcd(a, c) == 1]
            a, c = rng.choice(pairs)
            return {"mobius": [a, rng.choice(SMALL_CONSTANTS), 0, c]}
        if level == 3:
            return {"mobius": [0, rng.choice(INVERSE_NUMERATORS), 1, rng.choice(TINY_CONSTANTS)]}
        candidates = [
            (a, b, c)
            for a in range(2, 6) for b in SMALL_CONSTANTS for c in TINY_CONSTANTS
            if a * c - b != 0 and a + c != 0
        ]
        a, b, c = rng.choice(candidates)
        return {"mobius": [a, b, 1, c]}

    def check_rules(self, p, level):
        m = p["mobius"]
        require_integers(m, "Coefficients must be integers")
        require(len(m) == 4, "Expected four coefficients")
        a, b, c, d = m
        require(a * d - b * c != 0, "Degenerate function")
        if level == 1:
            require(2 <= a <= 9 and b in NONZERO_CONSTANTS and c == 0 and d == 1, "Outside level 1 rules")
        elif level == 2:
            require(
                1 <= a <= 7 and 2 <= d <= 6 and gcd(a, d) == 1
                and b in SMALL_CONSTANTS and c == 0,
                "Outside level 2 rules",
            )
        elif level == 3:
            require(a == 0 and b in INVERSE_NUMERATORS and c == 1 and d in TINY_CONSTANTS, "Outside level 3 rules")
        else:
            require(
                2 <= a <= 5 and b in SMALL_CONSTANTS and c == 1
                and d in TINY_CONSTANTS and a + d != 0,
                "Outside level 4 rules (self-inverse excluded)",
            )

    def parts(self, p, level):
        m = p["mobius"]
        plain = "f(x) = " + mobius_text(m)
        tex = "f(x) = " + mobius_text(m, True)
        if m[2] == 1:
            excluded = -m[3]
            plain += ", x ≠ {}".format(excluded)
            tex += r",\quad x \neq {}".format(excluded)
        numerator, denominator = inverse_of(m)
        prompt = prompt_content(
            plain, tex, "find an expression for f^-1(x)",
            [rb.text("Find an expression for "), rb.maths(r"f^{-1}(x)", "f^-1(x)")],
        )
        shown = Content(
            "f^-1(x) = " + fraction_text(numerator, denominator),
            "f^{-1}(x) = " + fraction_text(numerator, denominator, True),
        )
        return {
            "prompt": prompt,
            "answer": {
                "kind": "rational_function",
                "numerator": numerator, "denominator": denominator,
            },
            "answer_display": shown,
            "marks": {1: 2, 2: 2, 3: 3, 4: 4}[level],
            "working_lines": {1: 4, 2: 4, 3: 5, 4: 6}[level],
        }

    def validate_independently(self, question):
        """Solve y = f(x) for x with SymPy, then compare with the answer."""
        import sympy
        x, y = sympy.symbols("x y")
        p, q, r, s = question.parameters["mobius"]
        f = (p * x + q) / (r * x + s)
        solutions = sympy.solve(sympy.Eq(y, f), x)
        require(len(solutions) == 1, "Expected a unique inverse")
        expected = solutions[0].subs(y, x)
        given = (
            sympy_poly(question.answer["numerator"], x)
            / sympy_poly(question.answer["denominator"], x)
        )
        require(sympy.cancel(expected - given) == 0, "Independent inverse failed")
        return True


# -------------------------------------------------------------- composites

class CompositeFunctions(FunctionFamily):
    info = GeneratorInfo(
        id="algebra.functions.composite",
        version=2,
        topic="algebra",
        subtopic="functions",
        title="Composite functions",
        difficulty_descriptions={
            1: "Evaluate fg(a) or gf(a) for two linear functions.",
            2: "Find fg(x) or gf(x) for two linear functions.",
            3: "Find a composite involving x^2 + c, in either order.",
            4: "Substitute a linear function into ax^2 + bx + c and expand.",
        },
        tags=("functions", "composite_functions", "expanding"),
    )
    keys = {
        1: {"f", "g", "order", "input"}, 2: {"f", "g", "order"},
        3: {"f", "g", "order"}, 4: {"f", "g", "order"},
    }

    def build(self, level, rng):
        def linear():
            return [rng.choice(SMALL_CONSTANTS), rng.choice(COMPOSITE_SLOPES)]

        order = rng.choice(("fg", "gf"))
        if level == 1:
            return {"f": linear(), "g": linear(), "order": order, "input": rng.randint(-3, 6)}
        if level == 2:
            return {"f": linear(), "g": linear(), "order": order}
        if level == 3:
            quadratic = [rng.choice(SMALL_CONSTANTS), 0, 1]
            if rng.random() < 0.5:
                return {"f": quadratic, "g": linear(), "order": order}
            return {"f": linear(), "g": quadratic, "order": order}
        quadratic = [rng.randint(-6, 6), rng.choice(QUADRATIC_MIDDLE), rng.randint(1, 2)]
        if rng.random() < 0.5:
            return {"f": quadratic, "g": linear(), "order": "fg"}
        return {"f": linear(), "g": quadratic, "order": "gf"}

    def check_rules(self, p, level):
        require(p["order"] in ("fg", "gf"), "Unknown composite order")
        f, g = p["f"], p["g"]
        outer, inner = ordered(p)
        if level in (1, 2):
            require(composite_linear(f) and composite_linear(g), "Functions outside linear rules")
        if level == 1:
            require(type(p["input"]) is int and -3 <= p["input"] <= 6, "Input outside bounds")
        elif level == 3:
            require(
                (composite_linear(f) and is_simple_quadratic(g))
                or (is_simple_quadratic(f) and composite_linear(g)),
                "Expected one linear function and one x^2 + c",
            )
        elif level == 4:
            require(
                is_full_quadratic(outer) and composite_linear(inner),
                "Expected a quadratic outer function and linear inner function",
            )

    def parts(self, p, level):
        outer, inner = ordered(p)
        named = [("f", p["f"]), ("g", p["g"])]
        plain, tex = definitions(named), definitions(named, True)

        if level == 1:
            label = "{}({})".format(p["order"], p["input"])
            value = evaluate(outer, evaluate(inner, p["input"]))
            task = "find " + label
            runs = [rb.text("Find "), rb.maths(label, label)]
            answer, shown = number_answer(value), number_display(label, value)
            marks, lines = 2, 4
        else:
            label = p["order"] + "(x)"
            result = compose(outer, inner)
            task = "find and simplify an expression for " + label
            runs = [rb.text("Find and simplify an expression for "), rb.maths(label, label)]
            answer, shown = polynomial_answer(result), polynomial_display(label, result)
            marks, lines = (2 if level == 2 else 3), (5 if level == 2 else 6)
        return {
            "prompt": prompt_content(plain, tex, task, runs),
            "answer": answer, "answer_display": shown,
            "marks": marks, "working_lines": lines,
        }

    def validate_independently(self, question):
        """Compose with SymPy substitution and expansion."""
        import sympy
        x = sympy.Symbol("x")
        p = question.parameters
        outer, inner = ordered(p)
        composed = sympy.expand(sympy_poly(outer, x).subs(x, sympy_poly(inner, x)))
        if question.difficulty == 1:
            expected = sympy.Rational(question.answer["value"])
            require(composed.subs(x, p["input"]) == expected, "Independent composite value failed")
        else:
            given = sympy_poly(question.answer["coefficients"], x)
            require(sympy.expand(composed - given) == 0, "Independent composite expression failed")
        return True


# -------------------------------------------------------- combined problems

class CombinedFunctions(FunctionFamily):
    info = GeneratorInfo(
        id="algebra.functions.combined",
        version=2,
        topic="algebra",
        subtopic="functions",
        title="Problems combining function notation",
        difficulty_descriptions={
            1: "Solve fg(x) = k for two linear functions.",
            2: "Solve f(x) = f^-1(x) for a linear function.",
            3: "Solve fg(x) = k where the inner function is x^2 + c.",
            4: "Find an unknown constant a given ff(n) = k.",
        },
        tags=("functions", "composite_functions", "inverse_functions", "equations"),
    )
    keys = {
        1: {"f", "g", "order", "target"}, 2: {"f"},
        3: {"f", "g", "order", "target"}, 4: {"slope", "input", "target"},
    }

    def build(self, level, rng):
        def linear():
            return [rng.choice(SMALL_CONSTANTS), rng.choice(COMPOSITE_SLOPES)]

        if level == 1:
            p = {"f": linear(), "g": linear(), "order": rng.choice(("fg", "gf"))}
            outer, inner = ordered(p)
            p["target"] = evaluate(outer, evaluate(inner, rng.randint(-6, 8)))
            return p
        if level == 2:
            slope = rng.choice(SELF_INVERSE_SLOPES)
            solution = rng.choice(TINY_CONSTANTS)
            return {"f": [-solution * (slope - 1), slope]}
        if level == 3:
            quadratic, lin = [rng.choice(SMALL_CONSTANTS), 0, 1], linear()
            if rng.random() < 0.5:
                p = {"f": lin, "g": quadratic, "order": "fg"}
            else:
                p = {"f": quadratic, "g": lin, "order": "gf"}
            root = rng.randint(1, 6)
            p["target"] = evaluate(lin, root * root + quadratic[0])
            return p
        slope = rng.choice(UNKNOWN_CONSTANT_SLOPES)
        start = rng.choice(UNKNOWN_CONSTANT_INPUTS)
        constant = rng.choice(SMALL_CONSTANTS)
        return {
            "slope": slope, "input": start,
            "target": slope * slope * start + (slope + 1) * constant,
        }

    def check_rules(self, p, level):
        if level in (1, 3):
            require(p["order"] in ("fg", "gf"), "Unknown composite order")
            require(type(p["target"]) is int, "Target must be an integer")
        if level == 1:
            require(composite_linear(p["f"]) and composite_linear(p["g"]), "Functions outside linear rules")
            composed = compose(*ordered(p))
            solution = Fraction(p["target"] - composed[0], composed[1])
            require(solution.denominator == 1 and -6 <= solution <= 8, "Solution outside bounds")
        elif level == 2:
            f = p["f"]
            require_integers(f, "Coefficients must be integers")
            require(len(f) == 2 and f[1] in SELF_INVERSE_SLOPES and f[0] != 0, "Function outside rules")
            solution = Fraction(-f[0], f[1] - 1)
            require(solution.denominator == 1 and solution in TINY_CONSTANTS, "Solution outside bounds")
        elif level == 3:
            outer, inner = ordered(p)
            require(composite_linear(outer) and is_simple_quadratic(inner), "Expected linear outer, x^2 + c inner")
            square = Fraction(p["target"] - outer[0], outer[1]) - inner[0]
            require(square.denominator == 1 and square > 0, "Expected a positive square")
            root = isqrt(int(square))
            require(root * root == square and 1 <= root <= 6, "Expected a perfect square root in 1..6")
        else:
            require(p["slope"] in UNKNOWN_CONSTANT_SLOPES, "Slope outside rules")
            require(p["input"] in UNKNOWN_CONSTANT_INPUTS, "Input outside rules")
            require(type(p["target"]) is int, "Target must be an integer")
            constant = Fraction(p["target"] - p["slope"] ** 2 * p["input"], p["slope"] + 1)
            require(constant.denominator == 1 and constant in SMALL_CONSTANTS, "Constant outside rules")

    def parts(self, p, level):
        if level == 2:
            f = p["f"]
            plain = definition("f", f)
            solution = Fraction(-f[0], f[1] - 1)
            return {
                "prompt": prompt_content(
                    plain, definition("f", f, True), "solve f(x) = f^-1(x)",
                    [rb.text("Solve "), rb.maths(r"f(x) = f^{-1}(x)", "f(x) = f^-1(x)")],
                ),
                "answer": number_answer(solution),
                "answer_display": number_display("x", solution),
                "marks": 3, "working_lines": 6,
            }
        if level == 4:
            slope_term = terms_text([(p["slope"], 1)])
            constant = Fraction(p["target"] - p["slope"] ** 2 * p["input"], p["slope"] + 1)
            definition_text = "f(x) = {} + a".format(slope_term)
            condition = "ff({}) = {}".format(p["input"], p["target"])
            fallback = "{}, where a is a constant. Given that {}, find the value of a.".format(
                definition_text, condition)
            return {
                "prompt": Content(fallback, blocks=(rb.paragraph(
                    rb.maths(definition_text, definition_text),
                    rb.text(", where "), rb.maths("a", "a"),
                    rb.text(" is a constant. Given that "),
                    rb.maths(condition, condition),
                    rb.text(", find the value of "), rb.maths("a", "a"), rb.text("."),
                ),)),
                "answer": number_answer(constant),
                "answer_display": number_display("a", constant),
                "marks": 3, "working_lines": 6,
            }
        outer, inner = ordered(p)
        named = [("f", p["f"]), ("g", p["g"])]
        plain, tex = definitions(named), definitions(named, True)
        equation_text = "{}(x) = {}".format(p["order"], p["target"])
        prompt = prompt_content(
            plain, tex, "solve " + equation_text,
            [rb.text("Solve "), rb.maths(equation_text, equation_text)],
        )
        if level == 1:
            composed = compose(outer, inner)
            solution = Fraction(p["target"] - composed[0], composed[1])
            answer, shown = number_answer(solution), number_display("x", solution)
            marks = 3
        else:
            square = Fraction(p["target"] - outer[0], outer[1]) - inner[0]
            root = isqrt(int(square))
            answer = {"kind": "rational_list", "values": [rational_text(-root), rational_text(root)]}
            shown = Content(
                "x = {} or x = {}".format(-root, root),
                r"x = {}\quad\mathrm{{or}}\quad x = {}".format(-root, root),
            )
            marks = 3
        return {
            "prompt": prompt, "answer": answer, "answer_display": shown,
            "marks": marks, "working_lines": 6,
        }

    def validate_independently(self, question):
        """Solve each emitted equation directly with SymPy."""
        import sympy
        x, y, a = sympy.symbols("x y a")
        p, level = question.parameters, question.difficulty
        if level in (1, 3):
            outer, inner = ordered(p)
            composed = sympy_poly(outer, x).subs(x, sympy_poly(inner, x))
            solutions = set(sympy.solve(sympy.Eq(composed, p["target"]), x))
            if level == 1:
                expected = {sympy.Rational(question.answer["value"])}
            else:
                expected = {sympy.Rational(v) for v in question.answer["values"]}
            require(solutions == expected, "Independent composite equation failed")
        elif level == 2:
            f = sympy_poly(p["f"], x)
            inverse = sympy.solve(sympy.Eq(y, f), x)
            require(len(inverse) == 1, "Expected a unique inverse")
            solutions = set(sympy.solve(sympy.Eq(f, inverse[0].subs(y, x)), x))
            require(solutions == {sympy.Rational(question.answer["value"])}, "Independent f = f^-1 failed")
        else:
            f = p["slope"] * x + a
            ff = sympy.expand(f.subs(x, f))
            solutions = sympy.solve(sympy.Eq(ff.subs(x, p["input"]), p["target"]), a)
            require(solutions == [sympy.Rational(question.answer["value"])], "Independent constant failed")
        return True