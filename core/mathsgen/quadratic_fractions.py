"""Fractional equations that cross-multiply to a factorisable quadratic.

Each level states an equation in fractions. Clearing the denominators
produces a quadratic with two distinct integer roots, so the equation is
solved by factorising once the fractions are gone.

Every form records the values of x that would make a denominator zero.
Those are never roots: if an excluded value solved the quadratic, the
original equation would share a factor top and bottom and would collapse
to a linear equation, so such cases are rejected during construction.

Difficulty follows the shape of the equation rather than the size of the
numbers: one simple denominator, then a linear denominator against x, then
two linear denominators, then a sum of two fractions.
"""
from fractions import Fraction
from math import isqrt

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)


INFO = GeneratorInfo(
    id="algebra.quadratic.fractional_equation", version=1,
    topic="algebra", subtopic="quadratic_equations",
    title="Solve a fractional equation by cross-multiplying",
    difficulty_descriptions={
        1: "Cross-multiply a single pair of fractions.",
        2: "Cross-multiply where one denominator contains x.",
        3: "Cross-multiply two linear denominators.",
        4: "Clear a sum of two fractions, then solve.",
    },
    tags=("algebra", "quadratics", "fractions", "equations"),
)


def linear_text(constant, tex=False):
    """Write x + c, x - c or x, as the constant requires."""
    if constant == 0:
        return "x"
    return "x {} {}".format("+" if constant > 0 else "-", abs(constant))


def fraction_text(top, bottom, tex=False):
    if tex:
        return r"\frac{" + top + "}{" + bottom + "}"
    # Brackets only where a part has more than one term: "3/x" reads
    # better than "(3) / (x)", but "x + 7" still needs them.
    def wrapped(part):
        return "(" + part + ")" if " " in part else part
    return "{}/{}".format(wrapped(top), wrapped(bottom))


def equation_text(p, tex=False):
    form = p["form"]
    if form == "simple":
        left = fraction_text(linear_text(p["a"]), str(p["b"]), tex)
        right = fraction_text(str(p["c"]), "x", tex)
    elif form == "one_linear":
        left = fraction_text(linear_text(p["a"]), linear_text(p["b"]), tex)
        right = fraction_text(str(p["c"]), "x", tex)
    elif form == "two_linear":
        left = fraction_text(linear_text(p["a"]), linear_text(p["b"]), tex)
        right = fraction_text(str(p["c"]), linear_text(p["d"]), tex)
    else:
        first = fraction_text("1", "x", tex)
        second = fraction_text("1", linear_text(p["a"]), tex)
        third = fraction_text("1", str(p["k"]), tex)
        return "{} + {} = {}".format(first, second, third)
    return "{} = {}".format(left, right)


def quadratic_of(p):
    """The quadratic that clearing the denominators produces."""
    form = p["form"]
    if form == "simple":
        # x(x + a) = bc
        return [1, p["a"], -p["b"] * p["c"]]
    if form == "one_linear":
        # x(x + a) = c(x + b)
        return [1, p["a"] - p["c"], -p["c"] * p["b"]]
    if form == "two_linear":
        # (x + a)(x + d) = c(x + b)
        return [1, p["a"] + p["d"] - p["c"], p["a"] * p["d"] - p["c"] * p["b"]]
    # k(x + a) + kx = x(x + a)
    return [1, p["a"] - 2 * p["k"], -p["k"] * p["a"]]


def excluded_values(p):
    """The values of x that would make a denominator zero."""
    form = p["form"]
    if form == "simple":
        return [0]
    if form == "one_linear":
        return [0, -p["b"]]
    if form == "two_linear":
        return [-p["b"], -p["d"]]
    return [0, -p["a"]]


def integer_roots(coefficients):
    """Both roots when the monic quadratic factorises over the integers."""
    _, b, c = coefficients
    discriminant = b * b - 4 * c
    if discriminant <= 0:
        return None
    root = isqrt(discriminant)
    if root * root != discriminant:
        return None
    if (-b + root) % 2 or (-b - root) % 2:
        return None
    return sorted(((-b - root) // 2, (-b + root) // 2))


def presentation(p):
    instruction = "Solve the equation. Give both solutions."
    if p["form"] == "sum":
        instruction = (
            "Solve the equation by first clearing the fractions. "
            "Give both solutions."
        )
    return Content(
        instruction + " " + equation_text(p),
        equation_text(p, True),
        display_text=instruction,
    )


def answer_for(p):
    roots = integer_roots(quadratic_of(p))
    answer = {"kind": "roots", "variable": "x", "values": [str(v) for v in roots]}
    display = Content(
        "x = {} or x = {}".format(*roots),
        "x = {}".format(roots[0]) + r"\quad\mathrm{or}\quad x = "
        + str(roots[1]),
    )
    return answer, display


class FractionalQuadratic:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng

        for attempt in range(800):
            if difficulty == 1:
                p = {
                    "form": "simple",
                    "a": rng.choice([v for v in range(-8, 9) if v]),
                    "b": rng.randint(2, 6),
                    "c": rng.choice([v for v in range(-9, 10) if v]),
                }
            elif difficulty == 2:
                p = {
                    "form": "one_linear",
                    "a": rng.choice([v for v in range(-8, 9) if v]),
                    "b": rng.choice([v for v in range(-6, 7) if v]),
                    "c": rng.choice([v for v in range(-8, 9) if v]),
                }
            elif difficulty == 3:
                p = {
                    "form": "two_linear",
                    "a": rng.choice([v for v in range(-7, 8) if v]),
                    "b": rng.choice([v for v in range(-6, 7) if v]),
                    "c": rng.choice([v for v in range(-8, 9) if v]),
                    "d": rng.choice([v for v in range(-6, 7) if v]),
                }
            else:
                p = {
                    "form": "sum",
                    "a": rng.choice([v for v in range(-9, 10) if v]),
                    "k": rng.randint(2, 6),
                }

            if self.acceptable(p):
                break
        else:
            raise ValueError("Could not construct a suitable equation")

        prompt = presentation(p)
        answer, display = answer_for(p)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=3 if difficulty <= 2 else 4, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=6),
            parameters=p,
        )
        self.validate(question)
        return question

    def acceptable(self, p):
        """Whether the equation solves cleanly and is not degenerate."""
        if p["form"] == "two_linear" and p["b"] == p["d"]:
            # Equal denominators cancel and leave a linear equation.
            return False
        roots = integer_roots(quadratic_of(p))
        if roots is None:
            return False
        if roots[0] == roots[1]:
            return False
        if any(abs(value) > 20 for value in roots):
            return False
        # An excluded value that solves the quadratic means the original
        # equation shared a factor and was never really quadratic.
        if any(value in roots for value in excluded_values(p)):
            return False
        return True

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid level")
        require(q.settings == {}, "Unsupported settings")

        p = q.parameters
        expected = {
            1: "simple", 2: "one_linear", 3: "two_linear", 4: "sum",
        }[level]
        require(p["form"] == expected, "Form does not match difficulty")

        keys = {
            "simple": {"form", "a", "b", "c"},
            "one_linear": {"form", "a", "b", "c"},
            "two_linear": {"form", "a", "b", "c", "d"},
            "sum": {"form", "a", "k"},
        }[p["form"]]
        require(set(p) == keys, "Unexpected parameters")
        require(all(type(p[key]) is int for key in keys if key != "form"),
                "Parameters must be integers")

        if p["form"] == "simple":
            require(2 <= p["b"] <= 6, "Denominator outside bounds")
        if p["form"] == "sum":
            require(2 <= p["k"] <= 6, "Denominator outside bounds")
        if p["form"] == "two_linear":
            require(p["b"] != p["d"], "Equal denominators cancel")

        roots = integer_roots(quadratic_of(p))
        require(roots is not None, "The quadratic does not factorise")
        require(roots[0] < roots[1], "Expected two distinct roots")
        require(all(abs(value) <= 20 for value in roots),
                "Roots outside bounds")

        excluded = excluded_values(p)
        require(all(value not in roots for value in excluded),
                "A root would make a denominator zero")

        answer, display = answer_for(p)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Display mismatch")
        require(q.prompt == presentation(p), "Prompt mismatch")
        require(q.visual_assets("questions") == ()
                and q.visual_assets("answers") == (),
                "This family uses no visual assets")
        return True

    def validate_independently(self, q):
        """Substitute each root into the ORIGINAL fractional equation.

        Solving the cleared quadratic would repeat the generator's own
        reasoning. Substituting into the equation as written checks both
        that the root satisfies it and that no denominator vanishes.
        """
        import sympy

        x = sympy.Symbol("x")
        p = q.parameters
        form = p["form"]

        if form == "simple":
            left = (x + p["a"]) / sympy.Integer(p["b"])
            right = sympy.Integer(p["c"]) / x
            denominators = [x]
        elif form == "one_linear":
            left = (x + p["a"]) / (x + p["b"])
            right = sympy.Integer(p["c"]) / x
            denominators = [x, x + p["b"]]
        elif form == "two_linear":
            left = (x + p["a"]) / (x + p["b"])
            right = sympy.Integer(p["c"]) / (x + p["d"])
            denominators = [x + p["b"], x + p["d"]]
        else:
            left = 1 / x + 1 / (x + p["a"])
            right = sympy.Rational(1, p["k"])
            denominators = [x, x + p["a"]]

        for value in q.answer["values"]:
            root = sympy.Integer(int(value))
            for denominator in denominators:
                require(denominator.subs(x, root) != 0,
                        "A stated root makes a denominator zero")
            require(sympy.simplify(left.subs(x, root) - right.subs(x, root)) == 0,
                    "A stated root does not satisfy the original equation")

        # Both roots of the cleared quadratic must be stated, so no valid
        # solution is silently dropped.
        cleared = sympy.solve(sympy.Eq(left, right), x)
        require(sorted(int(v) for v in cleared)
                == sorted(int(v) for v in q.answer["values"]),
                "Independent solution set disagrees")
        return True