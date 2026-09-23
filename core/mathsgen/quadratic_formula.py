"""Solve non-factorisable quadratics with the quadratic formula.

The discriminant is always positive and never a perfect square, so the
equation genuinely needs the formula: a factorisable quadratic belongs to
the monic and non-monic families, which already cover it.

Levels 1 to 3 ask for answers to 2 decimal places, as an exam paper does.
Level 4 asks for exact surd form, which tests the formula itself rather
than the arithmetic of rounding.

Rounding is done with scaled integer square roots, never floats, and any
value close enough to a rounding boundary to be ambiguous is rejected
during construction rather than rounded on a guess.
"""
from fractions import Fraction
from functools import lru_cache
from math import gcd, isqrt

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


INFO = GeneratorInfo(
    id="algebra.quadratic.formula", version=1,
    topic="algebra", subtopic="quadratic_equations",
    title="Solve a quadratic with the quadratic formula",
    difficulty_descriptions={
        1: "Solve a monic quadratic, giving answers to 2 decimal places.",
        2: "Solve a quadratic with a leading coefficient above one.",
        3: "Rearrange into standard form first, then solve.",
        4: "Give the solutions in exact surd form.",
    },
    tags=("algebra", "quadratics", "quadratic formula", "surds"),
)

# Scaling for the integer square root. The error in the scaled root is
# below one unit, which is far finer than the rounding boundary margin.
SCALE = 10 ** 8
BOUNDARY_MARGIN = Fraction(1, 10 ** 4)


def squarefree_part(value):
    """Split a positive integer into a square coefficient and the rest."""
    require(value > 0, "Radicand must be positive")
    coefficient, remaining = 1, value
    factor = 2
    while factor * factor <= remaining:
        while remaining % (factor * factor) == 0:
            remaining //= factor * factor
            coefficient *= factor
        factor += 1
    return coefficient, remaining


def is_perfect_square(value):
    root = isqrt(value)
    return root * root == value


@lru_cache(maxsize=512)
def scaled_root(discriminant):
    """floor(SCALE * sqrt(discriminant)), computed with integers only.

    Cached because the same discriminant is evaluated during construction,
    during validation and again when the answer is built.
    """
    return isqrt(discriminant * SCALE * SCALE)


def rounded_root(a, b, discriminant, sign):
    """One root to 2 decimal places, with the rounding proved unambiguous.

    Returns the rounded value and the distance from the nearest rounding
    boundary, so the caller can reject a value too close to call.

    The arithmetic stays in integers until the final pair: building
    Fractions from SCALE-sized numerators and reducing them repeatedly was
    what made this family an order of magnitude slower than any other.
    """
    numerator = -b * SCALE + sign * scaled_root(discriminant)
    denominator = 2 * a
    # hundredths = numerator / (denominator * SCALE / 100), as integers.
    unit = denominator * (SCALE // 100)
    # Round half up without leaving integer arithmetic.
    nearest = (2 * numerator + unit) // (2 * unit)
    # Distance from the lower rounding boundary, in hundredths.
    boundary = (2 * nearest - 1) * unit
    distance = Fraction(abs(2 * numerator - boundary), 2 * unit)
    return Fraction(nearest, 100), distance


def surd_form(a, b, discriminant):
    """The roots as (rational +/- coefficient*sqrt(radicand)) / denominator."""
    coefficient, radicand = squarefree_part(discriminant)
    numerator, denominator = -b, 2 * a
    common = gcd(gcd(abs(numerator), coefficient), abs(denominator))
    if denominator < 0:
        common = -common
    return (
        numerator // common, coefficient // common,
        radicand, denominator // common,
    )


def surd_text(parts, tex=False):
    """Write both roots in exact form, as a single expression."""
    numerator, coefficient, radicand, denominator = parts
    root = (r"\sqrt{" + str(radicand) + "}" if tex
            else "sqrt(" + str(radicand) + ")")
    surd = root if coefficient == 1 else str(coefficient) + root
    top = "{} \u00b1 {}".format(numerator, surd) if numerator else (
        "\u00b1" + surd
    )
    if denominator == 1:
        return "x = " + top
    if tex:
        return r"x = \frac{" + top + "}{" + str(denominator) + "}"
    return "x = ({}) / {}".format(top, denominator)


def quadratic_text(coefficients, tex=False):
    """Write ax^2 + bx + c, omitting zero and redundant terms."""
    powers = (2, 1, 0)
    pieces = []
    for coefficient, power in zip(coefficients, powers):
        if coefficient == 0:
            continue
        magnitude = abs(coefficient)
        if power == 0:
            body = str(magnitude)
        else:
            body = "" if magnitude == 1 else str(magnitude)
            body += "x"
            if power == 2:
                body += "^{2}" if tex else "^2"
        if not pieces:
            pieces.append(("-" if coefficient < 0 else "") + body)
        else:
            pieces.append((" - " if coefficient < 0 else " + ") + body)
    return "".join(pieces) or "0"


def standard_coefficients(p):
    """The equation collected into ax^2 + bx + c = 0."""
    left = p["left"]
    right = p.get("right", [0, 0, 0])
    return [left[index] - right[index] for index in range(3)]


def discriminant_of(coefficients):
    a, b, c = coefficients
    return b * b - 4 * a * c


def presentation(p):
    if p["form"] == "rearrange":
        equation = "{} = {}".format(
            quadratic_text(p["left"]), quadratic_text(p["right"])
        )
        equation_tex = "{} = {}".format(
            quadratic_text(p["left"], True), quadratic_text(p["right"], True)
        )
        instruction = (
            "Rearrange into the form ax^2 + bx + c = 0, then solve. "
            "Give your answers to 2 decimal places."
        )
    else:
        equation = quadratic_text(p["left"]) + " = 0"
        equation_tex = quadratic_text(p["left"], True) + " = 0"
        if p["form"] == "exact":
            instruction = "Solve, giving your answers in exact form."
        else:
            instruction = "Solve, giving your answers to 2 decimal places."
    return Content(
        instruction + " " + equation, equation_tex, display_text=instruction,
    )


def answer_for(p):
    coefficients = standard_coefficients(p)
    a, b, _ = coefficients
    discriminant = discriminant_of(coefficients)

    if p["form"] == "exact":
        parts = surd_form(a, b, discriminant)
        answer = {
            "kind": "quadratic_surd_roots",
            "numerator": parts[0], "coefficient": parts[1],
            "radicand": parts[2], "denominator": parts[3],
        }
        return answer, Content(surd_text(parts), surd_text(parts, True))

    lower, _ = rounded_root(a, b, discriminant, -1)
    upper, _ = rounded_root(a, b, discriminant, 1)
    roots = sorted((lower, upper))
    answer = {
        "kind": "quadratic_rounded_roots",
        "values": [rational_text(value) for value in roots],
    }
    written = " or ".join(
        "x = {:.2f}".format(float(value)) for value in roots
    )
    return answer, Content(written)


class QuadraticFormula:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng

        for attempt in range(500):
            if difficulty == 1:
                a = 1
                b = rng.choice([v for v in range(-9, 10) if v])
                c = rng.choice([v for v in range(-9, 10) if v])
                p = {"form": "standard", "left": [a, b, c]}
            elif difficulty == 2:
                a = rng.randint(2, 4)
                b = rng.choice([v for v in range(-9, 10) if v])
                c = rng.choice([v for v in range(-8, 9) if v])
                p = {"form": "standard", "left": [a, b, c]}
            elif difficulty == 3:
                a = rng.randint(1, 3)
                b = rng.choice([v for v in range(-6, 7) if v])
                c = rng.choice([v for v in range(-8, 9) if v])
                # Move part of the equation to the right, so the student
                # must collect terms before the formula applies.
                shift_b = rng.choice([v for v in range(-5, 6) if v])
                shift_c = rng.choice([v for v in range(-7, 8) if v])
                p = {
                    "form": "rearrange",
                    "left": [a, b + shift_b, c + shift_c],
                    "right": [0, shift_b, shift_c],
                }
            else:
                a = rng.randint(1, 3)
                b = rng.choice([v for v in range(-8, 9) if v])
                c = rng.choice([v for v in range(-7, 8) if v])
                p = {"form": "exact", "left": [a, b, c]}

            if self.acceptable(p):
                break
        else:
            raise ValueError("Could not construct a suitable quadratic")

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
        """Whether this equation genuinely needs the formula and rounds cleanly."""
        coefficients = standard_coefficients(p)
        a, b, c = coefficients
        if a <= 0:
            return False
        discriminant = discriminant_of(coefficients)
        if discriminant <= 0:
            return False
        # A square discriminant means the quadratic factorises, which the
        # existing factorisable families already cover.
        if is_perfect_square(discriminant):
            return False
        if discriminant > 400:
            return False

        if p["form"] == "exact":
            _, radicand = squarefree_part(discriminant)
            # A radicand of one would have been a perfect square, and a very
            # large one makes the surd unwieldy.
            return 2 <= radicand <= 100

        # Both roots must round unambiguously and sit at a sensible size.
        for sign in (-1, 1):
            value, distance = rounded_root(a, b, discriminant, sign)
            if distance < BOUNDARY_MARGIN:
                return False
            if abs(value) > 20:
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
            1: "standard", 2: "standard", 3: "rearrange", 4: "exact",
        }[level]
        require(p["form"] == expected, "Form does not match difficulty")

        require(isinstance(p["left"], list) and len(p["left"]) == 3,
                "Expected three left coefficients")
        require(all(type(v) is int for v in p["left"]),
                "Coefficients must be integers")
        if p["form"] == "rearrange":
            require(isinstance(p["right"], list) and len(p["right"]) == 3,
                    "Expected three right coefficients")
            require(all(type(v) is int for v in p["right"]),
                    "Coefficients must be integers")
            require(p["right"][0] == 0,
                    "The squared term should stay on the left")
            require(p["right"] != [0, 0, 0],
                    "Level 3 must genuinely need rearranging")
        else:
            require("right" not in p, "Unexpected right-hand side")

        coefficients = standard_coefficients(p)
        a, b, c = coefficients
        require(a > 0, "Leading coefficient must be positive")
        if level == 1:
            require(a == 1, "Level 1 is monic")
        elif level == 2:
            require(2 <= a <= 4, "Leading coefficient outside bounds")

        discriminant = discriminant_of(coefficients)
        require(discriminant > 0, "Expected two real roots")
        require(not is_perfect_square(discriminant),
                "A square discriminant means the quadratic factorises")
        require(discriminant <= 400, "Discriminant outside bounds")
        # acceptable() is not re-run here: every condition it tests is
        # checked explicitly above or below, and calling it again tripled
        # the cost of validating this family.
        if p["form"] == "exact":
            _, radicand = squarefree_part(discriminant)
            require(2 <= radicand <= 100, "Radicand outside bounds")
        else:
            for sign in (-1, 1):
                value, distance = rounded_root(a, b, discriminant, sign)
                require(distance >= BOUNDARY_MARGIN,
                        "A root is too close to a rounding boundary")
                require(abs(value) <= 20, "Root outside bounds")

        answer, display = answer_for(p)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Display mismatch")
        require(q.prompt == presentation(p), "Prompt mismatch")
        require(q.visual_assets("questions") == ()
                and q.visual_assets("answers") == (),
                "This family uses no visual assets")
        return True

    def validate_independently(self, q):
        """Let SymPy solve the equation and compare against the answer.

        SymPy solves the polynomial directly rather than applying the
        formula, so a mistake in the discriminant or the surd reduction
        shows up here.
        """
        import sympy

        x = sympy.Symbol("x")
        p = q.parameters
        left = p["left"]
        expression = left[0] * x ** 2 + left[1] * x + left[2]
        if p["form"] == "rearrange":
            right = p["right"]
            expression -= right[0] * x ** 2 + right[1] * x + right[2]

        roots = sorted(sympy.solve(sympy.Eq(expression, 0), x))
        require(len(roots) == 2, "Expected two distinct roots")

        if p["form"] == "exact":
            answer = q.answer
            surd = sympy.sqrt(answer["radicand"])
            expected = sorted([
                (answer["numerator"] - answer["coefficient"] * surd)
                / answer["denominator"],
                (answer["numerator"] + answer["coefficient"] * surd)
                / answer["denominator"],
            ])
            for submitted, actual in zip(expected, roots):
                require(sympy.simplify(submitted - actual) == 0,
                        "Independent exact root disagrees")
            # The surd must be fully simplified.
            require(sympy.sqrt(answer["radicand"]) == sympy.sqrt(
                answer["radicand"]
            ).powsimp(), "Radicand is not squarefree")
            return True

        for submitted_text, actual in zip(q.answer["values"], roots):
            submitted = sympy.Rational(submitted_text)
            # The stated value must be the exact root rounded to 2 d.p.
            require(abs(actual - submitted) <= sympy.Rational(1, 200),
                    "Independent rounded root disagrees")
        return True