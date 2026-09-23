"""Primitive non-monic quadratics built from constrained linear factors."""
from fractions import Fraction
from functools import lru_cache
from math import gcd, isqrt

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)
from .quadratic_monic import prompt_for


@lru_cache(maxsize=4)
def coefficient_bank(level):
    """Expand primitive factors; discard scalar multiples and degenerate cases."""
    results = set()
    first_factors = [
        (p, r) for p in range(2, 6) for r in range(-9, 10)
        if r != 0 and gcd(p, abs(r)) == 1
    ]
    second_leads = (1,) if level < 3 else range(2, 6)
    second_factors = [
        (q, s) for q in second_leads for s in range(-9, 10)
        if s != 0 and gcd(q, abs(s)) == 1
    ]
    for p, r in first_factors:
        for q, s in second_factors:
            if level == 1 and not (r < 0 and s < 0):
                continue
            if level == 2 and r * s >= 0:
                continue
            if Fraction(-r, p) == Fraction(-s, q):
                continue
            a, b, c = p * q, p * s + q * r, r * s
            if b == 0 or abs(b) > 70:
                continue
            if gcd(gcd(a, abs(b)), abs(c)) != 1:
                continue
            results.add((a, b, c))
    return tuple(sorted(results))


def roots_for(a, b, c):
    discriminant = b * b - 4 * a * c
    require(discriminant > 0, "Expected two real roots")
    square_root = isqrt(discriminant)
    require(square_root * square_root == discriminant, "Expected rational roots")
    return sorted((
        Fraction(-b - square_root, 2 * a),
        Fraction(-b + square_root, 2 * a),
    ))


def display_for(roots):
    return Content(
        "x = {} or x = {}".format(*(rational_text(root) for root in roots)),
        "x = " + rational_tex(roots[0])
        + r"\quad\mathrm{or}\quad x = " + rational_tex(roots[1]),
    )


class NonMonicQuadratic:
    info = GeneratorInfo(
        id="algebra.quadratic.factorisable_non_monic",
        version=2,
        topic="algebra",
        subtopic="quadratic_equations",
        title="Solve a factorisable non-monic quadratic",
        difficulty_descriptions={
            1: "One integer and one fractional positive root.",
            2: "Integer and fractional roots of opposite signs; or x from a rectangle's area.",
            3: "Two non-integer rational roots; or a triangle's area or a number puzzle.",
            4: "Rearrange from both sides; or solve, reject a root, then find a perimeter.",
        },
        tags=("quadratics", "factorising", "equations", "non_monic"),
    )

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        from . import quadratic_contexts as worded_forms
        if rng.random() < worded_forms.CONTEXT_SHARE.get(difficulty, 0.0):
            return worded_forms.generate(self, context)
        a, b, c = rng.choice(coefficient_bank(difficulty))
        right = [0, 0, 0]
        if difficulty == 4:
            right[1] = rng.choice([
                value for value in range(-7, 8) if value != 0 and b + value != 0
            ])
            right[2] = rng.choice([
                value for value in range(-12, 13) if value != 0 and c + value != 0
            ])
        left = [a, b + right[1], c + right[2]]
        roots = roots_for(a, b, c)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic, subtopic=self.info.subtopic,
            difficulty=difficulty, seed=seed, settings=context.settings,
            prompt=prompt_for(left, right),
            answer={
                "kind": "roots", "variable": "x",
                "values": [rational_text(root) for root in roots],
            },
            answer_display=display_for(roots),
            worked_solution=(), marks=4,
            tags=self.info.tags, layout_hint=LayoutHint(working_lines=8),
            parameters={"left": left, "right": right},
        )
        self.validate(question)
        return question

    def validate(self, question):
        from .worded import is_worded
        if is_worded(question):
            from .quadratic_contexts import validate as validate_worded
            return validate_worded(self, question)
        require(isinstance(question.answer, dict) and question.answer.get("kind") == "roots"
                and isinstance(question.answer.get("values"), list), "Unexpected answer shape")
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(not question.settings, "Unexpected settings")
        left = question.parameters["left"]
        right = question.parameters["right"]
        require(len(left) == len(right) == 3, "Expected polynomial coefficients")
        require(all(type(value) is int for value in left + right),
                "Expected integer coefficients")
        a, b, c = [x - y for x, y in zip(left, right)]
        require(right[0] == 0 and 2 <= a <= 25, "Expected non-monic equation")
        require(0 < abs(b) <= 70 and 0 < abs(c) <= 81, "Coefficient bounds")
        require(gcd(gcd(a, abs(b)), abs(c)) == 1,
                "Unintended common factor across the equation")
        if level < 4:
            require(right == [0, 0, 0], "Expected standard form")
        else:
            require(0 < abs(right[1]) <= 7 and 0 < abs(right[2]) <= 12,
                    "Expected rearrangement on both terms")
            require(left[1] != 0 and left[2] != 0, "Missing left-hand terms")
        stored = question.answer["values"]
        require(len(stored) == 2, "Both roots are required")
        roots = [Fraction(value) for value in stored]
        require(roots[0] < roots[1], "Expected distinct sorted roots")
        require(question.answer == {
            "kind": "roots", "variable": "x",
            "values": [rational_text(root) for root in roots],
        }, "Noncanonical roots")
        for root in roots:
            require(0 < abs(root) <= 9 and root.denominator <= 5, "Root bounds")
            require(a * root * root + b * root + c == 0, "Root fails substitution")
        integer_count = sum(root.denominator == 1 for root in roots)
        require(integer_count == (1 if level < 3 else 0), "Wrong root structure")
        if level == 1:
            require(roots[0] > 0, "Expected positive roots")
        elif level == 2:
            require(roots[0] < 0 < roots[1], "Expected opposite signs")
        require(question.prompt == prompt_for(left, right), "Prompt mismatch")
        require(question.answer_display == display_for(roots), "Display mismatch")
        return True

    def validate_independently(self, question):
        """Reconstruct the entire reduced polynomial from the submitted roots."""
        from .worded import is_worded
        if is_worded(question):
            from .quadratic_contexts import validate_independently as independent_worded
            return independent_worded(question)
        left = question.parameters["left"]
        right = question.parameters["right"]
        a, b, c = [x - y for x, y in zip(left, right)]
        values = question.answer["values"]
        require(len(values) == 2, "Expected both roots")
        first, second = map(Fraction, values)
        require(first < second, "Expected distinct sorted roots")
        require(a != 0 and -a * (first + second) == b
                and a * first * second == c,
                "Independent polynomial reconstruction disagrees")
        return True