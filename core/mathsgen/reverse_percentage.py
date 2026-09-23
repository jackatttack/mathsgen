"""Reverse percentages constructed from exact prices in whole pence."""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


RATES = {
    1: (10, 20, 25, 50),
    2: (5, 12, 15, 18, 30),
    3: (Fraction(5, 2), Fraction(15, 2), Fraction(25, 2)),
    4: (8, 12, 15, 18, 24, 35),
}


def money(pence):
    require(type(pence) is int and pence >= 0, "Expected nonnegative whole pence")
    return "£{}.{:02d}".format(pence // 100, pence % 100)


def rate_text(rate):
    rate = Fraction(rate)
    if rate.denominator == 1:
        return str(rate.numerator)
    require(rate.denominator == 2, "Unsupported percentage display")
    return "{}.5".format(rate.numerator // 2)


def prompt_for(rate, direction, given_pence, change_only):
    action = "increased" if direction == 1 else "reduced"
    if change_only:
        change = "increase" if direction == 1 else "reduction"
        text = (
            "The price of an item is {} by {}%. The {} amounts to {}. "
            "Find the original price."
        ).format(action, rate_text(rate), change, money(given_pence))
    else:
        text = (
            "The price of an item is {} by {}%. Its new price is {}. "
            "Find the original price."
        ).format(action, rate_text(rate), money(given_pence))
    return Content(text)


class ReversePercentage:
    info = GeneratorInfo(
        id="number.percentages.reverse",
        version=2,
        topic="number",
        subtopic="percentages",
        title="Find an original price from a percentage change",
        difficulty_descriptions={
            1: "Recover an original price after a familiar percentage discount.",
            2: "Recover an original price after a percentage increase.",
            3: "Reverse a change with a fractional percentage; or VAT and pay-rise contexts.",
            4: "Recover the original from the change alone; or undo two successive changes.",
        },
        tags=("percentages", "reverse", "money"),
    )

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        from . import reverse_contexts as worded_forms
        if rng.random() < worded_forms.CONTEXT_SHARE.get(difficulty, 0.0):
            return worded_forms.generate(self, context)
        rate = Fraction(rng.choice(RATES[difficulty]))
        direction = -1 if difficulty == 1 else (
            1 if difficulty == 2 else rng.choice((-1, 1))
        )
        # Whole-pound originals; only retain exact whole-penny changes.
        candidates = [
            pounds * 100 for pounds in range(12, 401)
            if (Fraction(pounds) * rate).denominator == 1
        ]
        original = rng.choice(candidates)
        change = Fraction(original) * rate / 100
        require(change.denominator == 1, "Construction produced fractional pence")
        change_only = difficulty == 4
        given = int(change) if change_only else original + direction * int(change)
        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=prompt_for(rate, direction, given, change_only),
            answer={"kind": "money", "currency": "GBP", "pence": original},
            answer_display=Content(money(original)),
            worked_solution=(),
            marks=3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=5),
            parameters={
                "percentage": rational_text(rate),
                "direction": direction,
                "given_pence": given,
                "change_only": change_only,
            },
        )
        self.validate(question)
        return question

    def validate(self, question):
        from .worded import is_worded
        if is_worded(question):
            from .reverse_contexts import validate as validate_worded
            return validate_worded(self, question)
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in RATES, "Invalid difficulty")
        require(not question.settings, "Unexpected settings")
        parameters = question.parameters
        rate = Fraction(parameters["percentage"])
        require(parameters["percentage"] == rational_text(rate), "Noncanonical rate")
        require(rate in RATES[level], "Rate outside difficulty rules")
        direction = parameters["direction"]
        require(type(direction) is int and direction in (-1, 1), "Invalid direction")
        if level == 1:
            require(direction == -1, "Expected discount")
        elif level == 2:
            require(direction == 1, "Expected increase")
        change_only = parameters["change_only"]
        require(type(change_only) is bool and change_only == (level == 4),
                "Incorrect problem structure")
        require(isinstance(question.answer, dict) and question.answer.get("kind") == "money",
                "Unexpected answer shape")
        original = question.answer["pence"]
        require(type(original) is int and 1200 <= original <= 40000,
                "Original price outside bounds")
        require(original % 100 == 0, "Expected whole-pound original")
        require(question.answer == {
            "kind": "money", "currency": "GBP", "pence": original,
        }, "Invalid money answer")
        given = parameters["given_pence"]
        require(type(given) is int and given > 0, "Invalid given price")
        change = Fraction(original) * rate / 100
        require(change.denominator == 1, "Unintended rounding")
        expected = change if change_only else original + direction * change
        require(given == expected, "Original price fails forward check")
        require(question.prompt == prompt_for(rate, direction, given, change_only),
                "Prompt mismatch")
        require(question.answer_display == Content(money(original)), "Answer display mismatch")
        return True

    def validate_independently(self, question):
        """Recover the original by dividing the supplied value by its multiplier."""
        from .worded import is_worded
        if is_worded(question):
            from .reverse_contexts import validate_independently as independent_worded
            return independent_worded(question)
        from decimal import Decimal, localcontext

        parameters = question.parameters
        with localcontext() as context:
            context.prec = 40
            percentage = Decimal(rate_text(Fraction(parameters["percentage"])))
            multiplier = percentage / Decimal(100)
            if not parameters["change_only"]:
                multiplier = Decimal(1) + parameters["direction"] * multiplier
            recovered = Decimal(parameters["given_pence"]) / multiplier
            require(recovered == Decimal(question.answer["pence"]),
                    "Independent reverse calculation disagrees")
        return True