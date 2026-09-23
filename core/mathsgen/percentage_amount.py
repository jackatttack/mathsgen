"""Choose percentages and target answers, then construct suitable amounts."""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)


INFO = GeneratorInfo(
    id="number.percentages.of_amount",
    version=2,
    topic="number",
    subtopic="percentages",
    title="Find a percentage of an amount",
    difficulty_descriptions={
        1: "Familiar percentages; or the amount taken off in a sale.",
        2: "Whole-number percentages; or a new price after an increase or decrease.",
        3: "Decimal percentages; or compare a percentage discount with a money discount.",
        4: "Fractional percentages; or successive changes and a percentage of a percentage.",
    },
    tags=("percentages", "percentage_of_amount"),
)


PERCENTAGES = {
    1: (Fraction(10), Fraction(20), Fraction(25), Fraction(50), Fraction(75)),
    2: tuple(Fraction(value) for value in (13, 17, 23, 37, 62, 85)),
    3: tuple(Fraction(value, 2) for value in (5, 15, 25, 35)),
    4: (Fraction(1, 2), Fraction(3, 4), Fraction(5, 4), Fraction(7, 4)),
}


def percentage_text(value, level):
    if level == 3:
        # This level deliberately uses halves, rendered exactly as decimals.
        return "{}.5".format(value.numerator // 2)
    return rational_text(value)


def prompt_for(percentage, amount, level):
    display = percentage_text(percentage, level)
    plain_percentage = "(" + display + ")" if level == 4 else display
    tex_percentage = rational_tex(percentage) if level == 4 else display
    return Content(
        "Calculate {}% of {}.".format(plain_percentage, amount),
        tex_percentage + r"\%\ \mathrm{of}\ " + str(amount),
        display_text="Calculate:",
    )


class PercentageAmount:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        from . import percentage_contexts as worded_forms
        if rng.random() < worded_forms.CONTEXT_SHARE.get(difficulty, 0.0):
            return worded_forms.generate(self, context)
        percentage = rng.choice(PERCENTAGES[difficulty])

        # Work backwards from an integer answer. Filter before selection,
        # ensuring both the question amount and its answer are sensible.
        maximum = 600 if difficulty == 1 else 2400
        candidates = []
        for answer in range(2, 181):
            amount = Fraction(answer * 100, 1) / percentage
            if amount.denominator == 1 and 20 <= amount <= maximum and amount != 100:
                candidates.append((answer, amount.numerator))
        require(bool(candidates), "No valid amount for this percentage")
        result, amount = rng.choice(candidates)
        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=prompt_for(percentage, amount, difficulty),
            answer={"kind": "rational", "value": str(result)},
            answer_display=Content(str(result), str(result)),
            worked_solution=(),
            marks=2 if difficulty < 4 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=4),
            parameters={
                "percentage": rational_text(percentage),
                "amount": amount,
            },
        )
        self.validate(question)
        return question

    def validate(self, question):
        from .worded import is_worded
        if is_worded(question):
            from .percentage_contexts import validate as validate_worded
            return validate_worded(self, question)
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in PERCENTAGES, "Invalid difficulty")
        percentage = Fraction(question.parameters["percentage"])
        amount = question.parameters["amount"]
        result = Fraction(question.answer["value"])
        require(percentage in PERCENTAGES[level], "Percentage outside difficulty rules")
        require(type(amount) is int, "Amount must be an integer")
        require(20 <= amount <= (600 if level == 1 else 2400), "Amount outside bounds")
        require(amount != 100, "Avoid the direct percent-to-number shortcut")
        require(result.denominator == 1 and 2 <= result <= 180, "Answer outside bounds")
        require(result * 100 == amount * percentage, "Incorrect percentage answer")
        require(question.answer["value"] == rational_text(result), "Non-canonical answer")
        require(question.prompt == prompt_for(percentage, amount, level), "Prompt mismatch")
        require(question.answer_display.text == rational_text(result), "Displayed answer mismatch")
        require(question.answer_display.math_tex == rational_tex(result), "Math answer mismatch")
        return True

    def validate_independently(self, question):
        """Check the emitted problem with independent symbolic arithmetic."""
        from .worded import is_worded
        if is_worded(question):
            from .percentage_contexts import validate_independently as independent_worded
            return independent_worded(question)
        import sympy

        percentage = sympy.Rational(question.parameters["percentage"])
        amount = sympy.Integer(question.parameters["amount"])
        expected = sympy.Rational(question.answer["value"])
        require(amount * percentage / 100 == expected, "Independent percentage check failed")
        return True