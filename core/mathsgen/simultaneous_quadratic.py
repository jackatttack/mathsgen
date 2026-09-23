"""Linear/quadratic systems with two exact, correctly paired solutions.

The quadratic stores coefficients of x^2, xy, y^2, x, y and 1.
The line stores coefficients u, v, w for ux + vy = w.
"""
from fractions import Fraction
from math import gcd, isqrt

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)


INFO = GeneratorInfo(
    id="algebra.simultaneous.linear_quadratic", version=1,
    topic="algebra", subtopic="simultaneous_equations",
    title="Solve simultaneous linear and quadratic equations",
    difficulty_descriptions={
        1: "Substitute a line stated as y = mx + c into a parabola.",
        2: "Rearrange a linear equation before substitution; fractional values.",
        3: "Substitute into an equation containing xy.",
        4: "Find both intersections of a line and a circle.",
    },
    tags=("algebra", "simultaneous", "quadratics", "substitution"),
)


def expression(coefficients, names):
    pieces = []
    for value, name in zip(coefficients, names):
        if value == 0:
            continue
        magnitude = abs(value)
        body = ("" if magnitude == 1 and name else str(magnitude)) + name
        if not pieces:
            pieces.append(("-" if value < 0 else "") + body)
        else:
            pieces.append((" - " if value < 0 else " + ") + body)
    return "".join(pieces) or "0"


def equations(p, level, tex=False):
    u, v, w = p["line"]
    a, b, c, d, e, f = p["quadratic"]
    square = "x^{2}" if tex else "x^2"
    if level == 1:
        first = "y = " + expression([-u, w], ["x", ""])
    else:
        first = expression([u, v], ["x", "y"]) + " = " + str(w)
    if level in (1, 2):
        second = expression([-e], ["y"]) + " = " + expression(
            [a, d, f], [square, "x", ""]
        )
    elif level == 3:
        second = "xy = " + str(-f)
    else:
        second = square + " + " + ("y^{2}" if tex else "y^2") + " = " + str(-f)
    return first, second


def prompt_for(p, level):
    instruction = "Solve the simultaneous equations. Give both pairs of values."
    return Content(
        instruction + " " + "; ".join(equations(p, level)),
        r"\qquad ".join(equations(p, level, True)),
        display_text=instruction,
    )


def reduced(p):
    """Substitute y = (w - ux)/v, retaining exact coefficients."""
    u, v, w = p["line"]
    a, b, c, d, e, f = p["quadratic"]
    slope, intercept = Fraction(-u, v), Fraction(w, v)
    return (
        a + b * slope + c * slope * slope,
        b * intercept + 2 * c * slope * intercept + d + e * slope,
        c * intercept * intercept + e * intercept + f,
    )


def solution_pairs(p):
    a, b, c = reduced(p)
    require(a != 0, "Substitution is not quadratic")
    discriminant = b * b - 4 * a * c
    require(discriminant > 0, "Expected two real solutions")
    numerator = isqrt(discriminant.numerator)
    denominator = isqrt(discriminant.denominator)
    require(numerator ** 2 == discriminant.numerator
            and denominator ** 2 == discriminant.denominator,
            "Expected rational solutions")
    root = Fraction(numerator, denominator)
    xs = sorted(((-b - root) / (2 * a), (-b + root) / (2 * a)))
    u, v, w = p["line"]
    return [[rational_text(x), rational_text((w - u * x) / v)] for x in xs]


def answer_for(p):
    return {"kind": "solution_pairs", "variables": ["x", "y"],
            "pairs": solution_pairs(p)}


def display_for(answer):
    plain, maths = [], []
    for x, y in answer["pairs"]:
        plain.append("(x, y) = ({}, {})".format(x, y))
        maths.append("(x,y) = (" + rational_tex(Fraction(x)) + ", "
                     + rational_tex(Fraction(y)) + ")")
    return Content(" or ".join(plain), r"\quad\mathrm{or}\quad ".join(maths))


def check_parameters(p, level):
    require(set(p) == {"line", "quadratic"}, "Unexpected parameters")
    require(isinstance(p["line"], list) and len(p["line"]) == 3,
            "Invalid linear equation")
    require(isinstance(p["quadratic"], list) and len(p["quadratic"]) == 6,
            "Invalid quadratic equation")
    require(all(type(value) is int for value in p["line"] + p["quadratic"]),
            "Expected integer coefficients")
    u, v, w = p["line"]
    a, b, c, d, e, f = p["quadratic"]
    require(u != 0 and v > 0 and max(abs(u), v) <= 20 and abs(w) <= 100,
            "Line outside bounds")
    require(max(abs(value) for value in p["quadratic"]) <= 100,
            "Quadratic outside bounds")
    if level == 1:
        require(v == 1 and (a, b, c, e) == (1, 0, 0, -1),
                "Expected direct line and monic parabola")
    elif level == 2:
        require(v == 2 and u % 2 != 0 and w % 2 != 0
                and (a, b, c, e) == (1, 0, 0, -2),
                "Expected rearrangement with fractional solutions")
    elif level == 3:
        require(v == 1 and (a, b, c, d, e) == (0, 1, 0, 0, 0)
                and f != 0, "Expected a nondegenerate xy equation")
    else:
        require((a, b, c, d, e) == (1, 0, 1, 0, 0) and 0 < -f <= 100,
                "Expected a circle centred at the origin")
    pairs = [[Fraction(value) for value in pair] for pair in solution_pairs(p)]
    require(all(abs(value) <= 30 and value.denominator <= 2
                for pair in pairs for value in pair), "Solutions outside bounds")
    if level == 2:
        require(any(value.denominator == 2 for pair in pairs for value in pair),
                "Expected a fractional solution")
    else:
        require(all(value.denominator == 1 for pair in pairs for value in pair),
                "Expected integer solutions")


class SimultaneousQuadratic:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        for attempt in range(300):
            if difficulty == 1:
                r, s = rng.sample(range(-5, 6), 2)
                m = rng.choice((-3, -2, -1, 1, 2, 3))
                k = rng.randint(-6, 6)
                p = {"line": [-m, 1, k],
                     "quadratic": [1, 0, 0, m - r - s, -1, r * s + k]}
            elif difficulty == 2:
                r, s = rng.sample((-6, -4, -2, 0, 2, 4, 6), 2)
                u = rng.choice((-5, -3, -1, 1, 3, 5))
                w = rng.choice((-7, -5, -3, -1, 1, 3, 5, 7))
                p = {"line": [u, 2, w],
                     "quadratic": [1, 0, 0, -r - s - u, -2, r * s + w]}
            elif difficulty == 3:
                r, s = rng.sample((-5, -4, -3, -2, -1, 1, 2, 3, 4, 5), 2)
                m = rng.choice((-2, -1, 1, 2))
                k = -m * (r + s)
                p = {"line": [-m, 1, k],
                     "quadratic": [0, 1, 0, 0, 0, m * r * s]}
            else:
                x1, y1 = rng.sample((1, 2, 3, 4, 5, 6, 7), 2)
                x1 *= rng.choice((-1, 1))
                y1 *= rng.choice((-1, 1))
                x2, y2 = rng.choice(((y1, x1), (-y1, -x1)))
                u, v = y2 - y1, x1 - x2
                common = gcd(abs(u), abs(v))
                u, v = u // common, v // common
                if v < 0:
                    u, v = -u, -v
                w = u * x1 + v * y1
                p = {"line": [u, v, w],
                     "quadratic": [1, 0, 1, 0, 0, -x1*x1-y1*y1]}
            try:
                check_parameters(p, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a suitable system")
        answer = answer_for(p)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(p, difficulty),
            answer=answer, answer_display=display_for(answer), worked_solution=(),
            marks=5 if difficulty < 4 else 6, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=7), parameters=p,
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        require(type(q.difficulty) is int and q.difficulty in (1, 2, 3, 4),
                "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        check_parameters(q.parameters, q.difficulty)
        require(q.answer == answer_for(q.parameters), "Incorrect solution pairs")
        require(q.prompt == prompt_for(q.parameters, q.difficulty), "Prompt mismatch")
        require(q.answer_display == display_for(q.answer), "Display mismatch")
        require(not q.visual_assets("questions") and not q.visual_assets("answers"),
                "Unexpected visuals")
        return True

    def validate_independently(self, q):
        """Substitute in both originals; prove two distinct pairs are complete.

        A nonvertical line determines one y per x. A genuinely quadratic
        substitution has at most two roots, so two distinct verified pairs
        exhaust the solution set without repeating the root calculation.
        """
        u, v, w = q.parameters["line"]
        a, b, c, d, e, f = q.parameters["quadratic"]
        require(v != 0 and a*v*v - b*u*v + c*u*u != 0,
                "System does not reduce to a quadratic")
        require(q.answer["variables"] == ["x", "y"], "Wrong variable order")
        pairs = q.answer["pairs"]
        require(len(pairs) == 2 and all(len(pair) == 2 for pair in pairs),
                "Expected two pairs")
        values = [tuple(Fraction(value) for value in pair) for pair in pairs]
        require(values[0][0] < values[1][0], "Missing, duplicate or unordered roots")
        for x, y in values:
            require(u*x + v*y == w, "Pair fails the original line")
            require(a*x*x + b*x*y + c*y*y + d*x + e*y + f == 0,
                    "Pair fails the original quadratic")
        return True