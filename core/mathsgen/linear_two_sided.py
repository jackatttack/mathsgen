"""Construct ax + c = bx + d backwards from a chosen exact solution."""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_tex, rational_text, require,
)


INFO = GeneratorInfo(
    id="algebra.linear.two_sided",
    version=4,
    topic="algebra",
    subtopic="linear_equations",
    title="Solve a linear equation with unknowns on both sides",
    difficulty_descriptions={
        1: "Positive integer coefficients and solution; sometimes a think-of-a-number problem.",
        2: "Opposite-sign integer coefficients and a negative integer solution.",
        3: "Expand brackets for a fractional answer, or form and solve an equation from a context.",
        4: "Clear different denominators, or form, solve and use an equation in a multi-step context.",
    },
    tags=("equations", "linear", "unknowns_both_sides"),
)


def linear_expression(coefficient, constant, tex=False):
    """Format a nonzero x coefficient without '+ -', '1x' or empty terms."""
    coefficient, constant = Fraction(coefficient), Fraction(constant)
    formatter = rational_tex if tex else rational_text
    if coefficient == 1:
        first = "x"
    elif coefficient == -1:
        first = "-x"
    elif tex or coefficient.denominator == 1:
        first = formatter(coefficient) + "x"
    else:
        first = "(" + formatter(coefficient) + ")x"
    if constant == 0:
        return first
    return first + (" + " if constant > 0 else " - ") + formatter(abs(constant))


def equation(left_coefficient, left_constant, right_coefficient, right_constant):
    return Content(
        linear_expression(left_coefficient, left_constant)
        + " = " + linear_expression(right_coefficient, right_constant),
        linear_expression(left_coefficient, left_constant, True)
        + " = " + linear_expression(right_coefficient, right_constant, True),
    )


class TwoSidedLinear:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        from .linear_contexts import context_share, generate as generate_worded
        if context.rng.random() < context_share(difficulty):
            return generate_worded(self, context)
        if difficulty >= 3:
            from .linear_harder_forms import generate
            return generate(self, context)
        rng = context.rng

        if difficulty == 1:
            b = Fraction(rng.randint(1, 5))
            a = b + rng.randint(1, 6)
            solution = Fraction(rng.randint(1, 9))
        elif difficulty == 2:
            a = Fraction(rng.randint(1, 7))
            b = Fraction(-rng.randint(1, 7))
            solution = Fraction(-rng.randint(1, 9))
            if rng.choice((False, True)):
                a, b = b, a
        elif difficulty == 3:
            denominator = rng.choice((2, 3, 4, 5))
            numerators = [
                n for n in range(-11, 12)
                if Fraction(n, denominator).denominator == denominator
            ]
            solution = Fraction(rng.choice(numerators), denominator)
            b = Fraction(rng.randint(1, 5))
            a = b + denominator * rng.randint(1, 3)
        else:
            denominator = rng.choice((2, 3, 4))
            numerators = [
                n for n in range(1, 9)
                if Fraction(n, denominator).denominator == denominator
            ]
            a = Fraction(rng.choice(numerators), denominator)
            b = Fraction(rng.randint(1, 5))
            solution = Fraction(denominator * rng.choice((-3, -2, -1, 1, 2, 3)))

        # Choose a constant only after fixing the solution. Filtering keeps
        # both sides meaningful and avoids trivially vanishing constants.
        constants = [
            Fraction(c) for c in range(1, 13)
            if (a - b) * solution + c != 0
        ]
        c = rng.choice(constants)
        d = (a - b) * solution + c
        problem = equation(a, c, b, d)
        difference = a - b
        right_value = d - c
        solution_string = rational_text(solution)

        steps = (
            Content(
                "Subtract {}x from both sides and collect the x terms.".format(
                    "(" + rational_text(b) + ")" if b < 0 else rational_text(b)
                ),
                linear_expression(difference, c, True)
                + " = " + rational_tex(d),
            ),
            Content(
                "Subtract {} from both sides.".format(rational_text(c)),
                linear_expression(difference, 0, True)
                + " = " + rational_tex(right_value),
            ),
            Content(
                "Divide both sides by {}.".format(rational_text(difference)),
                "x = " + rational_tex(solution),
            ),
            Content(
                "Check: substituting x = {} gives {} on each side.".format(
                    solution_string, rational_text(a * solution + c)
                )
            ),
        )
        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=Content(
                "Solve for x: " + problem.text,
                problem.math_tex,
                display_text="Solve for x:",
            ),
            answer={"kind": "variable_values", "values": {"x": solution_string}},
            answer_display=Content(
                "x = " + solution_string, "x = " + rational_tex(solution)
            ),
            worked_solution=steps,
            marks=3 if difficulty < 4 else 4,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=6 if difficulty < 4 else 8),
            parameters={
                "a": rational_text(a), "b": rational_text(b),
                "c": rational_text(c), "d": rational_text(d),
            },
        )
        self.validate(question)
        return question

    def validate(self, question):
        """Check the emitted problem and answer, not the generation RNG."""
        if isinstance(question.parameters, dict) and "context" in question.parameters:
            from .linear_contexts import validate as validate_worded
            return validate_worded(self, question)
        if question.difficulty in (3, 4):
            from .linear_harder_forms import validate
            return validate(self, question)
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        require(question.difficulty in (1, 2, 3, 4), "Invalid difficulty")
        a, b, c, d = (
            Fraction(question.parameters[key]) for key in ("a", "b", "c", "d")
        )
        require(
            isinstance(question.answer, dict)
            and question.answer.get("kind") == "variable_values"
            and isinstance(question.answer.get("values"), dict)
            and set(question.answer["values"]) == {"x"},
            "Unexpected answer shape",
        )
        answer_text = question.answer["values"]["x"]
        solution = Fraction(answer_text)
        require(answer_text == rational_text(solution), "Answer is not canonical")
        require(a != 0 and b != 0 and a != b, "Degenerate equation")
        require(c != 0 and d != 0, "Unintended zero constant")
        require(a * solution + c == b * solution + d, "Answer fails substitution")
        require(c.denominator == d.denominator == 1, "Unexpected fractional constant")
        require(max(abs(c), abs(d)) <= 150, "Constants outside intended bounds")
        expected = equation(a, c, b, d)
        require(question.prompt.text == "Solve for x: " + expected.text, "Prompt mismatch")
        require(question.prompt.math_tex == expected.math_tex, "Math prompt mismatch")
        require(
            question.answer_display.math_tex == "x = " + rational_tex(solution),
            "Displayed answer mismatch",
        )
        if question.difficulty == 1:
            require(all(v > 0 for v in (a, b, c, d, solution)), "Expected positive values")
            require(all(v.denominator == 1 for v in (a, b, solution)), "Expected integers")
        elif question.difficulty == 2:
            require(a * b < 0 and solution < 0, "Expected signed structure")
            require(all(v.denominator == 1 for v in (a, b, solution)), "Expected integers")
        elif question.difficulty == 3:
            require(a.denominator == b.denominator == 1, "Expected integer coefficients")
            require(2 <= solution.denominator <= 5, "Expected a simple fractional answer")
        else:
            require(2 <= a.denominator <= 4, "Expected a fractional coefficient")
            require(b.denominator == solution.denominator == 1, "Expected integer b and x")
        return True

    def validate_independently(self, question):
        """Use SymPy to solve the emitted equation independently."""
        if isinstance(question.parameters, dict) and "context" in question.parameters:
            from .linear_contexts import validate_independently as independent_worded
            return independent_worded(question)
        if question.difficulty in (3, 4):
            from .linear_harder_forms import validate_independently
            return validate_independently(question)
        import sympy

        symbol = sympy.Symbol("x")
        a, b, c, d = (
            sympy.Rational(question.parameters[key])
            for key in ("a", "b", "c", "d")
        )
        solutions = sympy.solve(a * symbol + c - b * symbol - d, symbol)
        expected = sympy.Rational(question.answer["values"]["x"])
        require(solutions == [expected], "Independent SymPy solution disagrees")
        return True