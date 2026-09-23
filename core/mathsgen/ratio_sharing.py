"""Constrained ratio sharing with exact amounts and explicit units."""
from fractions import Fraction
from functools import reduce
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


INFO = GeneratorInfo(
    id="ratio.sharing",
    version=3,
    topic="ratio",
    subtopic="sharing",
    title="Share a total in a given ratio",
    difficulty_descriptions={
        1: "Share a whole-number quantity between two people.",
        2: "Share between three people; or find a total from the difference between shares.",
        3: "Share money with exact pennies; or work from one known share.",
        4: "Share a length in metres; or find a starting amount after the ratio changes.",
    },
    tags=("ratio", "sharing", "proportion"),
)


def decimal_text(value, places=2):
    """Format an exact terminating decimal without converting through float."""
    value = Fraction(value)
    scaled = value * 10 ** places
    require(scaled.denominator == 1, "Amount cannot be shown at requested precision")
    sign = "-" if scaled < 0 else ""
    digits = str(abs(scaled.numerator)).zfill(places + 1)
    return sign + digits[:-places] + "." + digits[-places:]


def amount_text(value, unit):
    if unit == "GBP":
        return "£" + decimal_text(value)
    return rational_text(value) + " " + unit


def prompt_text(ratio, total, unit):
    ratio_text = " : ".join(str(part) for part in ratio)
    if unit == "counters":
        people = "A and B" if len(ratio) == 2 else "A, B and C"
        return (
            "{} counters are shared between {} in the ratio {}. "
            "How many counters does each person receive?"
        ).format(rational_text(total), people, ratio_text)
    if unit == "GBP":
        return (
            "{} is shared between A, B and C in the ratio {}. "
            "How much money does each person receive?"
        ).format(amount_text(total, unit), ratio_text)
    return (
        "A ribbon {} m long is cut into three pieces, A, B and C, "
        "whose lengths are in the ratio {}. "
        "Find the length of each piece in centimetres."
    ).format(decimal_text(Fraction(total, 100)), ratio_text)


class RatioSharing:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        from . import ratio_contexts as worded_forms
        if rng.random() < worded_forms.CONTEXT_SHARE.get(difficulty, 0.0):
            return worded_forms.generate(self, context)
        size = 2 if difficulty == 1 else 3

        # Distinct parts avoid equal-share shortcuts. Reduce once to ensure
        # the displayed ratio is in simplest form.
        raw = rng.sample(list(range(1, 10)), size)
        common = reduce(gcd, raw)
        ratio = tuple(part // common for part in raw)

        if difficulty <= 2:
            unit = "counters"
            one_part = Fraction(rng.randint(3, 15))
        elif difficulty == 3:
            unit = "GBP"
            # Constrain the choice before sampling: every possible selection
            # must respect the same total bound enforced by validation.
            allowed_pence = [
                pence for pence in (125, 175, 225, 275, 325, 375)
                if Fraction(pence, 100) * sum(ratio) <= 80
            ]
            require(bool(allowed_pence), "No valid monetary share for this ratio")
            one_part = Fraction(rng.choice(allowed_pence), 100)
        else:
            unit = "cm"
            # Odd lengths and an odd ratio total guarantee a non-integer
            # number of metres, making conversion a real part of the task.
            if sum(ratio) % 2 == 0:
                ratio = (2, 3, 4)
                ratio = tuple(rng.sample(list(ratio), len(ratio)))
            one_part = Fraction(rng.choice((15, 25, 35, 45, 55)))

        total = one_part * sum(ratio)
        shares = tuple(one_part * part for part in ratio)
        labels = tuple("ABC"[:size])
        answer_text = "; ".join(
            "{}: {}".format(label, amount_text(value, unit))
            for label, value in zip(labels, shares)
        )
        steps = []
        if difficulty == 4:
            steps.append(Content(
                "Convert metres to centimetres: {} × 100 = {} cm.".format(
                    decimal_text(total / 100), rational_text(total)
                )
            ))
        steps.extend((
            Content("Total ratio parts: {} = {}.".format(
                " + ".join(str(part) for part in ratio), sum(ratio)
            )),
            Content("One part is {} ÷ {} = {}.".format(
                amount_text(total, unit), sum(ratio), amount_text(one_part, unit)
            )),
            Content("Multiply one part by each ratio number: " + answer_text + "."),
            Content("Check: the shares add to {}.".format(amount_text(total, unit))),
        ))
        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=Content(prompt_text(ratio, total, unit)),
            answer={
                "kind": "labelled_quantities",
                "unit": unit,
                "values": {
                    label: rational_text(value)
                    for label, value in zip(labels, shares)
                },
            },
            answer_display=Content(answer_text),
            worked_solution=tuple(steps),
            marks=3 if difficulty < 4 else 4,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=6 if difficulty < 4 else 8),
            parameters={
                "ratio": list(ratio), "total": rational_text(total), "unit": unit,
            },
        )
        self.validate(question)
        return question

    def validate(self, question):
        from .worded import is_worded
        if is_worded(question):
            from .ratio_contexts import validate as validate_worded
            return validate_worded(self, question)
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in (1, 2, 3, 4), "Invalid difficulty")
        ratio = question.parameters["ratio"]
        total = Fraction(question.parameters["total"])
        unit = question.parameters["unit"]
        size = 2 if level == 1 else 3
        require(len(ratio) == size, "Incorrect number of ratio parts")
        require(all(type(part) is int and 1 <= part <= 9 for part in ratio), "Invalid ratio")
        require(len(set(ratio)) == size, "Repeated ratio parts")
        require(reduce(gcd, ratio) == 1, "Ratio is not simplified")
        labels = tuple("ABC"[:size])
        require(
            isinstance(question.answer, dict)
            and question.answer.get("kind") == "labelled_quantities"
            and isinstance(question.answer.get("values"), dict),
            "Unexpected answer shape",
        )
        require(set(question.answer["values"]) == set(labels), "Incorrect answer labels")
        shares = [Fraction(question.answer["values"][label]) for label in labels]
        require(all(value > 0 for value in shares), "Non-positive share")
        require(sum(shares) == total, "Shares do not sum to the total")
        require(
            len({share / part for share, part in zip(shares, ratio)}) == 1,
            "Shares do not follow the ratio",
        )
        require(question.answer["unit"] == unit, "Answer unit mismatch")
        require(question.prompt.text == prompt_text(ratio, total, unit), "Prompt mismatch")
        expected_display = "; ".join(
            "{}: {}".format(label, amount_text(value, unit))
            for label, value in zip(labels, shares)
        )
        require(question.answer_display.text == expected_display, "Displayed answer mismatch")
        for label, value in zip(labels, shares):
            require(
                question.answer["values"][label] == rational_text(value),
                "Non-canonical answer",
            )
        if level <= 2:
            require(unit == "counters", "Expected counters")
            require(all(value.denominator == 1 for value in shares), "Fractional counters")
            require(3 <= shares[0] / ratio[0] <= 15, "Unit share outside bounds")
        elif level == 3:
            require(unit == "GBP", "Expected money")
            require(all((value * 100).denominator == 1 for value in shares), "Fractional penny")
            require(any(value.denominator != 1 for value in shares), "Missing decimal demand")
            require(total <= 80, "Money total outside bounds")
        else:
            require(unit == "cm", "Expected centimetres")
            require(all(value.denominator == 1 for value in shares), "Unexpected fractional cm")
            require((total / 100).denominator != 1, "Missing conversion demand")
            require(total <= 1500, "Length outside bounds")
        return True

    def validate_independently(self, question):
        """Solve conservation and proportionality as a linear system."""
        from .worded import is_worded
        if is_worded(question):
            from .ratio_contexts import validate_independently as independent_worded
            return independent_worded(question)
        import sympy

        ratio = question.parameters["ratio"]
        size = len(ratio)
        rows = [[1] * size]
        for index in range(1, size):
            row = [0] * size
            row[0] = -ratio[index]
            row[index] = ratio[0]
            rows.append(row)
        matrix = sympy.Matrix(rows)
        target = sympy.Matrix(
            [sympy.Rational(question.parameters["total"])] + [0] * (size - 1)
        )
        solved = matrix.inv() * target
        submitted = [
            sympy.Rational(question.answer["values"][label])
            for label in "ABC"[:size]
        ]
        require(list(solved) == submitted, "Independent ratio solution disagrees")
        return True