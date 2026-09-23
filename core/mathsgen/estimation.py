"""Estimation by rounding each value to one significant figure.

The estimate is the exact result of the rounded calculation, so both the
rounded values and the estimate itself are exact rationals. The true value
is never asked for: the skill is choosing sensible approximations and
working with them, not calculating precisely.
"""
from fractions import Fraction

from .core import Content, GeneratorInfo, LayoutHint, Question, make_context, require
from .rounding import decimal_text, round_significant, terminates


OPERATIONS = {
    "product": {"symbol": "×", "tex": r"\times"},
    "quotient": {"symbol": "÷", "tex": r"\div"},
}


def rounded_values(values):
    return [round_significant(Fraction(value), 1) for value in values]


def estimate_for(values, operation):
    """The estimate: round first, then calculate with the rounded values."""
    first, second = rounded_values(values)
    if operation == "product":
        return first * second
    require(second != 0, "Cannot divide by a rounded value of zero")
    return first / second


def expression_text(values, operation, tex=False):
    symbol = OPERATIONS[operation]["tex" if tex else "symbol"]
    return "{} {} {}".format(
        decimal_text(Fraction(values[0])), symbol, decimal_text(Fraction(values[1]))
    )


def make_prompt(values, operation):
    instruction = (
        "Estimate the value of the following by rounding each number to "
        "one significant figure."
    )
    return Content(
        instruction + " " + expression_text(values, operation),
        expression_text(values, operation, True),
        display_text=instruction,
    )


class Estimation:
    """Shared construction; each operation is registered separately."""

    @staticmethod
    def estimate_limit(difficulty):
        return 100000

    @staticmethod
    def tidy(estimate):
        """Whether the estimate is a value a person would actually state.

        An estimate exists to be quotable, so 0.375 fails the purpose even
        though it is exact: a division that lands there is better replaced.
        A single decimal place is allowed below ten, where 0.8 reads
        naturally, but anything larger must be a whole number: 112.5 is no
        more quotable than 0.375.
        """
        if not terminates(estimate):
            return False
        if abs(estimate) < 10:
            return (estimate * 10).denominator == 1
        return estimate.denominator == 1

    def make_values(self, rng, difficulty):
        """The pair of values, so a level can constrain them jointly.

        Level 4 needs one value below one, which cannot be guaranteed while
        each value is drawn independently.
        """
        return [self.make_value(rng, difficulty) for _ in range(2)]

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        from . import estimation_contexts as worded_forms
        if rng.random() < worded_forms.CONTEXT_SHARE.get(difficulty, 0.0):
            return worded_forms.generate(self, context)

        for attempt in range(500):
            values = self.make_values(rng, difficulty)
            first, second = rounded_values(values)
            if second == 0 or first == 0:
                continue
            # A value already at one significant figure would make the
            # rounding step invisible, so at least one must actually change.
            if all(round_significant(Fraction(value), 1) == Fraction(value)
                   for value in values):
                continue
            estimate = estimate_for(values, self.operation)
            if not self.tidy(estimate):
                continue
            if 0 < abs(estimate) <= self.estimate_limit(difficulty):
                break
        else:
            raise ValueError("Could not construct a suitable estimation")

        estimate = estimate_for(values, self.operation)
        first, second = rounded_values(values)
        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=make_prompt(values, self.operation),
            answer={
                "kind": "estimate",
                "value": decimal_text(estimate),
                "rounded": [decimal_text(first), decimal_text(second)],
            },
            answer_display=Content(decimal_text(estimate), decimal_text(estimate)),
            worked_solution=(),
            marks=2 if difficulty <= 2 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=4),
            parameters={"values": [decimal_text(Fraction(value)) for value in values]},
        )
        self.validate(question)
        return question

    def validate(self, question):
        from .worded import is_worded
        if is_worded(question):
            from .estimation_contexts import validate as validate_worded
            return validate_worded(self, question)
        require(isinstance(question.answer, dict) and question.answer.get("kind") == "estimate",
                "Unexpected answer shape")
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in (1, 2, 3, 4), "Invalid difficulty")
        values = [Fraction(value) for value in question.parameters["values"]]
        require(len(values) == 2, "Expected two values")
        require(all(value > 0 for value in values), "Expected positive values")
        require(question.parameters["values"] == [decimal_text(value) for value in values],
                "Non-canonical stored values")

        first, second = rounded_values(values)
        require(first != 0 and second != 0, "A rounded value collapsed to zero")
        require(any(round_significant(value, 1) != value for value in values),
                "Both values are already at one significant figure")
        self.check_structure(values, level)

        estimate = estimate_for(values, self.operation)
        require(0 < abs(estimate) <= self.estimate_limit(level), "Estimate outside bounds")
        require(self.tidy(estimate), "The estimate is not a value worth estimating")
        require(question.answer["value"] == decimal_text(estimate), "Incorrect estimate")
        require(question.answer["rounded"] == [decimal_text(first), decimal_text(second)],
                "Incorrect rounded values")
        require(question.prompt == make_prompt(values, self.operation), "Prompt mismatch")
        require(question.answer_display == Content(
            decimal_text(estimate), decimal_text(estimate),
        ), "Displayed answer mismatch")
        return True

    def validate_independently(self, question):
        from .worded import is_worded
        if is_worded(question):
            from .estimation_contexts import validate_independently as independent_worded
            return independent_worded(self, question)
        return self.validate_bare_independently(question)

    def validate_bare_independently(self, question):
        """Round with the decimal module, then calculate, in that order.

        Rounding before calculating is the whole point of the method, so
        this check reproduces that sequence rather than the construction's
        own helpers.
        """
        from decimal import ROUND_HALF_UP, Decimal, localcontext

        import sympy

        with localcontext() as context:
            context.prec = 40
            rounded = []
            for text in question.parameters["values"]:
                value = Decimal(text)
                places = -value.adjusted()
                rounded.append(
                    value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
                )

        expected = [sympy.Rational(str(value)) for value in rounded]
        require([str(value) for value in question.answer["rounded"]]
                == [decimal_text(Fraction(str(value))) for value in rounded],
                "Independent rounding disagrees")
        if self.operation == "product":
            result = expected[0] * expected[1]
        else:
            require(expected[1] != 0, "Independent divisor is zero")
            result = expected[0] / expected[1]
        require(sympy.Rational(question.answer["value"]) == result,
                "Independent estimate disagrees")
        return True


class EstimateProduct(Estimation):
    operation = "product"

    @staticmethod
    def estimate_limit(difficulty):
        """A product of rounded values grows with the size of the inputs.

        Two values in the ten thousands round to five-figure numbers, so
        their product runs to billions. The limit therefore scales with the
        level rather than being fixed.
        """
        if difficulty == 2:
            return 10 ** 10
        return 100000
    info = GeneratorInfo(
        id="number.estimation.product", version=2, topic="number",
        subtopic="estimation", title="Estimate a product",
        difficulty_descriptions={
            1: "Two-digit and three-digit whole numbers.",
            2: "Larger whole numbers.",
            3: "Numbers with one decimal place.",
            4: "One value below one, so its rounding shifts the place value.",
        },
        tags=("estimation", "rounding", "significant_figures"),
    )

    def make_value(self, rng, difficulty):
        if difficulty == 1:
            return Fraction(rng.randint(11, 899))
        if difficulty == 2:
            return Fraction(rng.randint(1100, 89999))
        return Fraction(rng.randint(11, 899), 10)

    def make_values(self, rng, difficulty):
        if difficulty != 4:
            return [self.make_value(rng, difficulty) for _ in range(2)]
        # One value below one, one ordinary, so the small value's rounding
        # is what shifts the place value of the answer.
        small = Fraction(rng.randint(11, 899), rng.choice((1000, 10000)))
        ordinary = Fraction(rng.randint(11, 899))
        pair = [small, ordinary]
        rng.shuffle(pair)
        return pair

    def check_structure(self, values, level):
        if level == 1:
            require(all(value.denominator == 1 and 11 <= value <= 899 for value in values),
                    "Expected bounded whole numbers")
        elif level == 2:
            require(all(value.denominator == 1 and 1100 <= value <= 89999 for value in values),
                    "Expected larger whole numbers")
        elif level == 3:
            require(all((value * 10).denominator == 1 for value in values),
                    "Expected one decimal place")
        else:
            require(any(value < 1 for value in values),
                    "Expected at least one value below one")
            require(any(value > 1 for value in values),
                    "Expected one ordinary value alongside the small one")


class EstimateQuotient(Estimation):
    operation = "quotient"
    info = GeneratorInfo(
        id="number.estimation.quotient", version=2, topic="number",
        subtopic="estimation", title="Estimate a quotient",
        difficulty_descriptions={
            1: "A whole-number estimate from two-digit and three-digit values.",
            2: "Larger whole numbers.",
            3: "Numbers with one decimal place.",
            4: "A divisor below one, so the estimate is larger than the dividend.",
        },
        tags=("estimation", "rounding", "significant_figures", "division"),
    )

    def make_value(self, rng, difficulty):
        if difficulty == 1:
            return Fraction(rng.randint(11, 899))
        if difficulty == 2:
            return Fraction(rng.randint(1100, 89999))
        return Fraction(rng.randint(11, 899), 10)

    def make_values(self, rng, difficulty):
        if difficulty != 4:
            return [self.make_value(rng, difficulty) for _ in range(2)]
        # A divisor below one makes the estimate larger than the dividend,
        # which is the point students most often get backwards. The divisor
        # is built around a leading digit that divides cleanly, since
        # dividing by 0.7 or 0.9 almost never gives a quotable estimate.
        leading = rng.choice((2, 4, 5, 8))
        scale = rng.choice((10, 100))
        offset = rng.randint(-4, 4)
        divisor = Fraction(leading * 10 + offset, scale * 10)
        dividend = Fraction(rng.randint(11, 899))
        return [dividend, divisor]

    def check_structure(self, values, level):
        if level == 1:
            require(all(value.denominator == 1 and 11 <= value <= 899 for value in values),
                    "Expected bounded whole numbers")
        elif level == 2:
            require(all(value.denominator == 1 and 1100 <= value <= 89999 for value in values),
                    "Expected larger whole numbers")
        elif level == 3:
            require(all((value * 10).denominator == 1 for value in values),
                    "Expected one decimal place")
        else:
            require(values[1] < 1 < values[0],
                    "Expected a divisor below one and a dividend above it")