"""Monic quadratic equations constructed backwards from two distinct roots."""
from fractions import Fraction
from math import isqrt

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


def polynomial(coefficients, tex=False):
    pieces = []
    for value, degree in zip(coefficients, (2, 1, 0)):
        if value == 0:
            continue
        magnitude = abs(value)
        if degree == 0:
            body = str(magnitude)
        else:
            body = "" if magnitude == 1 else str(magnitude)
            body += "x"
            if degree == 2:
                body += "^{2}" if tex else "^2"
        if pieces:
            pieces.append((" - " if value < 0 else " + ") + body)
        else:
            pieces.append(("-" if value < 0 else "") + body)
    return "".join(pieces) or "0"


def prompt_for(left, right):
    plain = polynomial(left) + " = " + polynomial(right)
    maths = polynomial(left, True) + " = " + polynomial(right, True)
    instruction = "Solve the equation. Give both solutions."
    return Content(instruction + " " + plain, maths, display_text=instruction)


def display_for(roots):
    text = "x = {} or x = {}".format(*roots)
    maths = "x = " + roots[0] + r"\quad\mathrm{or}\quad x = " + roots[1]
    return Content(text, maths)


class MonicQuadratic:
    info = GeneratorInfo(
        id="algebra.quadratic.factorisable_monic",
        version=1,
        topic="algebra",
        subtopic="quadratic_equations",
        title="Solve a factorisable monic quadratic",
        difficulty_descriptions={
            1: "Standard form with two distinct positive integer roots.",
            2: "Standard form with roots of opposite signs.",
            3: "Rearrange a constant from the right before factorising.",
            4: "Collect linear and constant terms from both sides.",
        },
        tags=("quadratics", "factorising", "equations", "monic"),
    )

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        if difficulty == 1:
            roots = sorted(rng.sample(range(1, 10), 2))
        elif difficulty == 2:
            first = rng.randint(1, 9)
            second = -rng.choice([n for n in range(1, 10) if n != first])
            roots = sorted((first, second))
        else:
            candidates = [
                (a, b) for a in range(-9, 10) for b in range(a + 1, 10)
                if a != 0 and b != 0 and a + b != 0
            ]
            roots = list(rng.choice(candidates))
        linear = -sum(roots)
        constant = roots[0] * roots[1]
        if difficulty < 3:
            right = [0, 0, 0]
        else:
            offset = rng.choice([
                n for n in range(-12, 13) if n != 0 and constant + n != 0
            ])
            shift = 0 if difficulty == 3 else rng.choice([
                n for n in range(-7, 8) if n != 0 and linear + n != 0
            ])
            right = [0, shift, offset]
        left = [1, linear + right[1], constant + right[2]]
        root_strings = [str(root) for root in roots]
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic, subtopic=self.info.subtopic,
            difficulty=difficulty, seed=seed, settings=context.settings,
            prompt=prompt_for(left, right),
            answer={"kind": "roots", "variable": "x", "values": root_strings},
            answer_display=display_for(root_strings),
            worked_solution=(), marks=3 if difficulty < 3 else 4,
            tags=self.info.tags, layout_hint=LayoutHint(working_lines=7),
            parameters={"left": left, "right": right},
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(not question.settings, "Unexpected settings")
        left = question.parameters["left"]
        right = question.parameters["right"]
        require(len(left) == len(right) == 3, "Expected polynomial coefficients")
        require(all(type(n) is int for n in left + right), "Expected integers")
        require(left[0] == 1 and right[0] == 0, "Expected monic quadratic")
        linear = left[1] - right[1]
        constant = left[2] - right[2]
        require(0 < abs(linear) <= 18 and 0 < abs(constant) <= 81,
                "Reduced coefficients outside intended bounds")
        if level < 3:
            require(right == [0, 0, 0], "Expected standard form")
        else:
            require(0 < abs(right[2]) <= 12 and left[2] != 0,
                    "Expected nonzero constants on both sides")
            if level == 3:
                require(right[1] == 0, "Expected constant-only rearrangement")
            else:
                require(0 < abs(right[1]) <= 7 and left[1] != 0,
                        "Expected linear terms on both sides")
        stored = question.answer["values"]
        require(len(stored) == 2, "Both roots are required")
        roots = [Fraction(value) for value in stored]
        require(roots[0] < roots[1], "Expected distinct sorted roots")
        require(all(root.denominator == 1 and 0 < abs(root) <= 9 for root in roots),
                "Roots outside intended bounds")
        require(question.answer == {
            "kind": "roots", "variable": "x",
            "values": [rational_text(root) for root in roots],
        }, "Noncanonical answer")
        for root in roots:
            require(root * root + linear * root + constant == 0,
                    "Root fails substitution")
        if level == 1:
            require(roots[0] > 0, "Expected positive roots")
        elif level == 2:
            require(roots[0] < 0 < roots[1], "Expected opposite-sign roots")
        require(question.prompt == prompt_for(left, right), "Prompt mismatch")
        require(question.answer_display == display_for(stored), "Display mismatch")
        return True

    def validate_independently(self, question):
        """Recover the complete root set using the quadratic formula."""
        left = question.parameters["left"]
        right = question.parameters["right"]
        a, b, c = [x - y for x, y in zip(left, right)]
        require(a != 0, "Not a quadratic")
        discriminant = b * b - 4 * a * c
        require(discriminant > 0, "Expected two real roots")
        square_root = isqrt(discriminant)
        require(square_root * square_root == discriminant, "Non-square discriminant")
        expected = sorted((
            Fraction(-b - square_root, 2 * a),
            Fraction(-b + square_root, 2 * a),
        ))
        submitted = [Fraction(value) for value in question.answer["values"]]
        require(submitted == expected, "Independent quadratic formula disagrees")
        return True