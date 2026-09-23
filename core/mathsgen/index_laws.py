"""Divide powers and raise a power to a power, with exact rational indices.

Both laws share one construction and one validation path. Each registered
class supplies its own index construction and its own difficulty rules,
because dividing subtracts indices while raising multiplies them.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)
from .index_product import power


VARIABLES = ("x", "y", "a", "b", "t")


def quotient_prompt(variable, exponents):
    instruction = (
        "For {} > 0, simplify the following as a single power of {}."
    ).format(variable, variable)
    plain = power(variable, exponents[0]) + " / " + power(variable, exponents[1])
    maths = (r"\frac{" + power(variable, exponents[0], True)
             + "}{" + power(variable, exponents[1], True) + "}")
    return Content(instruction + " " + plain, maths, display_text=instruction)


def power_prompt(variable, exponents):
    instruction = (
        "For {} > 0, simplify the following as a single power of {}."
    ).format(variable, variable)
    plain = "(" + power(variable, exponents[0]) + ")^(" + rational_text(exponents[1]) + ")"
    maths = (r"\left(" + power(variable, exponents[0], True)
             + r"\right)^{" + rational_tex(exponents[1]) + "}")
    return Content(instruction + " " + plain, maths, display_text=instruction)


class IndexLaw:
    """Shared construction; each law has its own registered class."""

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        variable = rng.choice(VARIABLES)

        for attempt in range(500):
            exponents = self.make_exponents(rng, difficulty)
            result = self.combine(exponents)
            if result != 0 and abs(result) <= 36:
                break
        else:
            raise ValueError("Could not construct a suitable pair of indices")

        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=self.make_prompt(variable, exponents),
            answer={
                "kind": "power",
                "base": variable,
                "exponent": rational_text(result),
            },
            answer_display=Content(
                power(variable, result), power(variable, result, True),
            ),
            worked_solution=(),
            marks=1 if difficulty <= 2 else 2,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=3),
            parameters={
                "variable": variable,
                "exponents": [rational_text(value) for value in exponents],
            },
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in (1, 2, 3, 4), "Invalid difficulty")
        variable = question.parameters["variable"]
        require(variable in VARIABLES, "Invalid variable")
        stored = question.parameters["exponents"]
        exponents = [Fraction(value) for value in stored]
        require(len(exponents) == 2, "Expected exactly two indices")
        require(stored == [rational_text(value) for value in exponents],
                "Non-canonical indices")
        require(all(value != 0 for value in exponents), "Unexpected zero index")

        self.check_structure(exponents, level)

        result = self.combine(exponents)
        require(result != 0, "Unintended complete cancellation")
        require(abs(result) <= 36, "Resulting index outside bounds")
        require(question.answer == {
            "kind": "power", "base": variable, "exponent": rational_text(result),
        }, "Incorrect answer")
        require(question.prompt == self.make_prompt(variable, exponents), "Prompt mismatch")
        require(question.answer_display == Content(
            power(variable, result), power(variable, result, True),
        ), "Displayed answer mismatch")
        return True

    def validate_independently(self, question):
        """Check symbolic equivalence over the positive-base domain."""
        import sympy

        variable = sympy.Symbol(question.parameters["variable"], positive=True)
        first, second = [
            sympy.Rational(value) for value in question.parameters["exponents"]
        ]
        if self.law == "quotient":
            expression = variable ** first / variable ** second
        else:
            expression = (variable ** first) ** second
        submitted = variable ** sympy.Rational(question.answer["exponent"])
        require(sympy.simplify(expression / submitted) == 1,
                "Independent symbolic simplification disagrees")
        return True


class IndexQuotient(IndexLaw):
    law = "quotient"
    info = GeneratorInfo(
        id="number.indices.quotient", version=1, topic="number",
        subtopic="indices", title="Divide powers with the same base",
        difficulty_descriptions={
            1: "Positive integer indices giving a positive result.",
            2: "Positive integer indices giving a negative result.",
            3: "One negative index.",
            4: "Fractional indices with different denominators.",
        },
        tags=("indices", "division", "exact"),
    )

    @staticmethod
    def combine(exponents):
        return exponents[0] - exponents[1]

    make_prompt = staticmethod(quotient_prompt)

    def make_exponents(self, rng, difficulty):
        if difficulty == 1:
            second = rng.randint(2, 7)
            return [Fraction(rng.randint(second + 1, 12)), Fraction(second)]
        if difficulty == 2:
            first = rng.randint(2, 7)
            return [Fraction(first), Fraction(rng.randint(first + 1, 12))]
        if difficulty == 3:
            positive = Fraction(rng.randint(2, 9))
            negative = Fraction(-rng.randint(2, 9))
            pair = [positive, negative]
            rng.shuffle(pair)
            return pair
        exponents = []
        for denominator in rng.sample((2, 3, 4, 5), 2):
            numerator = rng.choice([
                value for value in range(1, 3 * denominator)
                if Fraction(value, denominator).denominator == denominator
            ])
            exponents.append(Fraction(numerator, denominator))
        return exponents

    def check_structure(self, exponents, level):
        if level in (1, 2):
            require(all(value.denominator == 1 for value in exponents),
                    "Expected integer indices")
            require(all(2 <= value <= 12 for value in exponents),
                    "Index outside bounds")
            ordered = exponents[0] > exponents[1]
            require(ordered == (level == 1), "Incorrect result sign for this level")
        elif level == 3:
            require(all(value.denominator == 1 for value in exponents),
                    "Expected integer indices")
            require(all(2 <= abs(value) <= 9 for value in exponents),
                    "Index outside bounds")
            require(exponents[0] * exponents[1] < 0, "Expected mixed signs")
        else:
            require(all(2 <= value.denominator <= 5 for value in exponents),
                    "Expected fractional indices")
            require(exponents[0].denominator != exponents[1].denominator,
                    "Expected different denominators")


class IndexPower(IndexLaw):
    law = "power"
    info = GeneratorInfo(
        id="number.indices.power_of_power", version=1, topic="number",
        subtopic="indices", title="Raise a power to a power",
        difficulty_descriptions={
            1: "Positive integer indices.",
            2: "A negative outer index.",
            3: "A negative inner index.",
            4: "A fractional inner index with an integer outer index.",
        },
        tags=("indices", "powers", "exact"),
    )

    @staticmethod
    def combine(exponents):
        return exponents[0] * exponents[1]

    make_prompt = staticmethod(power_prompt)

    def make_exponents(self, rng, difficulty):
        if difficulty == 1:
            return [Fraction(rng.randint(2, 6)), Fraction(rng.randint(2, 5))]
        if difficulty == 2:
            return [Fraction(rng.randint(2, 6)), Fraction(-rng.randint(2, 5))]
        if difficulty == 3:
            return [Fraction(-rng.randint(2, 6)), Fraction(rng.randint(2, 5))]
        denominator = rng.choice((2, 3, 4, 5))
        numerator = rng.choice([
            value for value in range(1, 3 * denominator)
            if Fraction(value, denominator).denominator == denominator
        ])
        return [Fraction(numerator, denominator), Fraction(rng.randint(2, 6))]

    def check_structure(self, exponents, level):
        inner, outer = exponents
        if level <= 3:
            require(all(value.denominator == 1 for value in exponents),
                    "Expected integer indices")
            require(2 <= abs(inner) <= 6 and 2 <= abs(outer) <= 5,
                    "Index outside bounds")
            require((inner < 0) == (level == 3), "Incorrect inner sign for this level")
            require((outer < 0) == (level == 2), "Incorrect outer sign for this level")
        else:
            require(2 <= inner.denominator <= 5, "Expected a fractional inner index")
            require(outer.denominator == 1 and 2 <= outer <= 6,
                    "Expected a positive integer outer index")