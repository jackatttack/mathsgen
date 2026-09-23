"""Constrained products of powers with exact integer and fractional indices."""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)


def power(variable, exponent, tex=False):
    if tex:
        return variable + "^{" + rational_tex(exponent) + "}"
    return variable + "^(" + rational_text(exponent) + ")"


def prompt(variable, exponents):
    instruction = (
        "For {} > 0, simplify the following as a single power of {}."
    ).format(variable, variable)
    plain = " * ".join(power(variable, value) for value in exponents)
    maths = r" \times ".join(
        power(variable, value, True) for value in exponents
    )
    return Content(
        instruction + " " + plain,
        maths,
        display_text=instruction,
    )


class IndexProduct:
    info = GeneratorInfo(
        id="number.indices.product",
        version=1,
        topic="number",
        subtopic="indices",
        title="Multiply powers with the same base",
        difficulty_descriptions={
            1: "Two powers with positive integer indices.",
            2: "Three powers with positive integer indices.",
            3: "Positive and negative integer indices.",
            4: "Fractional indices with different denominators.",
        },
        tags=("indices", "multiplication", "exact"),
    )

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        variable = rng.choice(("x", "y", "a", "b", "t"))

        if difficulty in (1, 2):
            count = 2 if difficulty == 1 else 3
            exponents = [
                Fraction(rng.randint(2, 9)) for _ in range(count)
            ]
        elif difficulty == 3:
            positive = rng.randint(2, 9)
            candidates = [n for n in range(2, 10) if n != positive]
            negative = rng.choice(candidates)
            exponents = [Fraction(positive), Fraction(-negative)]
            rng.shuffle(exponents)
        else:
            exponents = []
            for denominator in rng.sample((2, 3, 4, 5), 2):
                candidates = [
                    n for n in range(1, denominator)
                    if Fraction(n, denominator).denominator == denominator
                ]
                numerator = rng.choice(candidates)
                exponents.append(Fraction(numerator, denominator))
            if rng.choice((False, True)):
                exponents[1] = -exponents[1]

        result = sum(exponents, Fraction(0))
        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=prompt(variable, exponents),
            answer={
                "kind": "power",
                "base": variable,
                "exponent": rational_text(result),
            },
            answer_display=Content(
                power(variable, result),
                power(variable, result, True),
            ),
            worked_solution=(),
            marks=2 if difficulty >= 3 else 1,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=3),
            parameters={
                "variable": variable,
                "exponents": [rational_text(e) for e in exponents],
            },
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(not question.settings, "Unexpected settings")
        variable = question.parameters["variable"]
        require(variable in ("x", "y", "a", "b", "t"), "Invalid variable")

        stored = question.parameters["exponents"]
        exponents = [Fraction(value) for value in stored]
        canonical = [rational_text(value) for value in exponents]
        require(stored == canonical, "Noncanonical exponents")
        expected_count = 3 if level == 2 else 2
        require(len(exponents) == expected_count, "Wrong factor count")

        if level in (1, 2):
            for value in exponents:
                require(value.denominator == 1, "Expected integer index")
                require(2 <= value <= 9, "Index outside bounds")
        elif level == 3:
            for value in exponents:
                require(value.denominator == 1, "Expected integer index")
                require(2 <= abs(value) <= 9, "Index outside bounds")
            require(exponents[0] * exponents[1] < 0, "Expected mixed signs")
        else:
            for value in exponents:
                require(2 <= value.denominator <= 5, "Denominator outside bounds")
                require(0 < abs(value) < 1, "Expected proper fraction")
            require(
                exponents[0].denominator != exponents[1].denominator,
                "Expected different denominators",
            )
            require(exponents[0] > 0, "Expected positive first index")

        result = sum(exponents, Fraction(0))
        require(result != 0, "Unintended complete cancellation")
        expected_answer = {
            "kind": "power",
            "base": variable,
            "exponent": rational_text(result),
        }
        require(question.answer == expected_answer, "Incorrect answer")
        require(question.prompt == prompt(variable, exponents), "Prompt mismatch")
        expected_display = Content(
            power(variable, result),
            power(variable, result, True),
        )
        require(question.answer_display == expected_display, "Display mismatch")
        return True

    def validate_independently(self, question):
        """Check symbolic equivalence over the positive-base domain."""
        import sympy

        variable = sympy.Symbol(
            question.parameters["variable"], positive=True
        )
        product = sympy.prod(
            variable ** sympy.Rational(value)
            for value in question.parameters["exponents"]
        )
        submitted = variable ** sympy.Rational(question.answer["exponent"])
        require(
            sympy.simplify(product / submitted) == 1,
            "Independent symbolic product disagrees",
        )
        return True