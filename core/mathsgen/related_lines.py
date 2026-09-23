"""Parallel and perpendicular lines with a deliberate four-stage progression."""
from fractions import Fraction
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .straight_lines import linear_text, implicit_text


INFO = GeneratorInfo(
    id="algebra.graphs.related_lines", version=1,
    topic="algebra", subtopic="straight_line_graphs",
    title="Parallel and perpendicular lines",
    difficulty_descriptions={
        1: "Find a parallel line from its given y-intercept.",
        2: "Find a parallel line through a point with nonzero x-coordinate.",
        3: "Find a perpendicular line through a point.",
        4: "Rearrange line A, then find a parallel or perpendicular line through a point.",
    },
    tags=("graphs", "parallel", "perpendicular", "equations"),
)

SLOPES = {
    1: tuple(Fraction(v) for v in (-4, -3, -2, -1, 1, 2, 3, 4)),
    2: tuple(Fraction(v) for v in (-3, -2, -1, 1, 2, 3)) + (
        Fraction(-3, 2), Fraction(-1, 2), Fraction(1, 2), Fraction(3, 2),
    ),
    3: tuple(Fraction(v) for v in (-4, -3, -2, -1, 1, 2, 3, 4)) + (
        Fraction(-1, 2), Fraction(1, 2), Fraction(-2, 3), Fraction(2, 3),
    ),
}


def source_coefficients(parameters):
    a, b, d = parameters["line_a"]
    return Fraction(-a, b), Fraction(d, b)


def presentation(parameters, level):
    m, c = source_coefficients(parameters)
    x, y = parameters["point"]
    relation = parameters["relation"]
    instruction = (
        "Lines A and B are {}. Line B passes through ({}, {}). "
        "Find the equation of line B in the form y = mx + c. "
        "The equation of line A is:"
    ).format(relation, x, y)
    if level == 4:
        equation = implicit_text(*parameters["line_a"])
        tex = equation
    else:
        equation = linear_text(m, c)
        tex = linear_text(m, c, True)
    return Content(instruction + " " + equation, tex, display_text=instruction)


class RelatedLines:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        if difficulty == 4:
            b = rng.randint(2, 5)
            a = rng.choice([
                value for value in range(-9, 10)
                if value and gcd(abs(value), b) == 1
            ])
            original_m = Fraction(-a, b)
            relation = rng.choice(("parallel", "perpendicular"))
        else:
            original_m = rng.choice(SLOPES[difficulty])
            a, b = -original_m.numerator, original_m.denominator
            relation = "perpendicular" if difficulty == 3 else "parallel"

        target_m = original_m if relation == "parallel" else -1 / original_m
        target_c = rng.randint(-8, 8)
        source_c = rng.choice([
            value for value in range(-9, 10)
            if value != 0 and (relation != "parallel" or value != target_c)
        ])
        if difficulty == 1:
            x = 0
        else:
            # A multiple of the gradient's denominator keeps the stated point
            # integral without requiring the answer gradient to be integral.
            x = target_m.denominator * rng.choice((-3, -2, -1, 1, 2, 3))
        y = target_m * x + target_c
        require(y.denominator == 1, "Point construction lost exact integrality")
        parameters = {
            "line_a": [a, b, b * source_c],
            "relation": relation,
            "point": [x, y.numerator],
        }
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=presentation(parameters, difficulty),
            answer={
                "kind": "linear_equation",
                "m": rational_text(target_m), "c": rational_text(Fraction(target_c)),
            },
            answer_display=Content(
                linear_text(target_m, Fraction(target_c)),
                linear_text(target_m, Fraction(target_c), True),
            ),
            worked_solution=(), marks=2 if difficulty == 1 else (4 if difficulty == 4 else 3),
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=3 if difficulty == 1 else 5),
            parameters=parameters,
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        p = q.parameters
        require(set(p) == {"line_a", "relation", "point"}, "Unexpected parameters")
        coefficients = p["line_a"]
        require(isinstance(coefficients, list) and len(coefficients) == 3
                and all(type(v) is int for v in coefficients), "Invalid source equation")
        a, b, d = coefficients
        require(a != 0 and b > 0 and gcd(abs(a), b) == 1,
                "Expected a reduced, nonhorizontal and nonvertical source line")
        original_m, original_c = source_coefficients(p)
        require(original_c.denominator == 1 and 1 <= abs(original_c) <= 9,
                "Source intercept outside bounds")
        relation = p["relation"]
        if level == 4:
            require(2 <= b <= 5 and 1 <= abs(a) <= 9,
                    "Expected a non-unit y coefficient")
            require(relation in ("parallel", "perpendicular"), "Invalid relationship")
        else:
            require(original_m in SLOPES[level], "Gradient outside level rules")
            require(relation == ("perpendicular" if level == 3 else "parallel"),
                    "Relationship does not match level")

        point = p["point"]
        require(isinstance(point, list) and len(point) == 2
                and all(type(v) is int for v in point), "Invalid stated point")
        x, y = point
        expected_m = original_m if relation == "parallel" else -1 / original_m
        if level == 1:
            require(x == 0, "Level 1 must give the y-intercept directly")
        else:
            require(x in [expected_m.denominator * k for k in (-3, -2, -1, 1, 2, 3)],
                    "Expected a nonzero, bounded x-coordinate")
        expected_c = y - expected_m * x
        require(expected_c.denominator == 1 and -8 <= expected_c <= 8,
                "Target intercept outside bounds")
        if relation == "parallel":
            require(expected_c != original_c, "Parallel lines must be distinct")
        require(q.answer == {
            "kind": "linear_equation",
            "m": rational_text(expected_m), "c": rational_text(expected_c),
        }, "Incorrect line B")
        require(q.prompt == presentation(p, level), "Prompt mismatch")
        require(q.answer_display == Content(
            linear_text(expected_m, expected_c), linear_text(expected_m, expected_c, True),
        ), "Answer display mismatch")
        require(not q.visual_assets("worked"), "Unexpected visual assets")
        return True

    def validate_independently(self, q):
        """Check direction vectors and point incidence without rearranging A."""
        import sympy

        a, b, d = map(sympy.Integer, q.parameters["line_a"])
        m, c = sympy.Rational(q.answer["m"]), sympy.Rational(q.answer["c"])
        x, y = map(sympy.Integer, q.parameters["point"])
        require(m * x + c == y, "Line B does not pass through the stated point")
        # Direction vectors: A = (b, -a); B = (1, m).
        if q.parameters["relation"] == "parallel":
            require(b * m + a == 0, "Direction-vector cross product is not zero")
            require(b * c != d, "Line B coincides with line A")
        else:
            require(q.parameters["relation"] == "perpendicular", "Unknown relationship")
            require(b - a * m == 0, "Direction-vector dot product is not zero")
        return True