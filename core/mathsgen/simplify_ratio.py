"""Ratio simplification with exact decimal and unit-conversion cases."""
from fractions import Fraction
from functools import reduce
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


INFO = GeneratorInfo(
    id="ratio.simplifying",
    version=2,
    topic="ratio",
    subtopic="simplifying",
    title="Simplify a ratio",
    difficulty_descriptions={
        1: "Simplify a two-part ratio; or write a ratio from a count.",
        2: "Simplify a three-part ratio; or a three-way count.",
        3: "Simplify a ratio with decimals; or convert between ratios and fractions.",
        4: "Convert cm and m first; or money, time, mass or capacity units.",
    },
    tags=("ratio", "simplifying", "common_factor", "units"),
)


def decimal_text(value):
    value = Fraction(value)
    scaled = value * 100
    require(scaled.denominator == 1, "Expected at most two decimal places")
    whole, remainder = divmod(scaled.numerator, 100)
    return str(whole) + (
        "." + str(remainder).zfill(2).rstrip("0") if remainder else ""
    )


def make_prompt(values, units):
    pieces = [
        decimal_text(Fraction(value)) + (" " + unit if unit else "")
        for value, unit in zip(values, units)
    ]
    tex_pieces = [
        decimal_text(Fraction(value)) + (r"\,\mathrm{" + unit + "}" if unit else "")
        for value, unit in zip(values, units)
    ]
    instruction = "Simplify this ratio. Give your answer using the smallest whole numbers."
    return Content(
        instruction + " " + " : ".join(pieces),
        r" : ".join(tex_pieces),
        display_text=instruction,
    )


class SimplifyRatio:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        from . import ratio_more_contexts as worded_forms
        if rng.random() < worded_forms.share(self, difficulty):
            return worded_forms.generate(self, context)
        size = 3 if difficulty == 2 else 2
        raw = rng.sample(list(range(1, 11)), size)
        common = reduce(gcd, raw)
        simplest = [value // common for value in raw]
        units = [""] * size

        if difficulty <= 2:
            multiplier = rng.randint(2, 12)
            values = [Fraction(value * multiplier) for value in simplest]
        elif difficulty == 3:
            multiplier = rng.choice((3, 7, 9, 11))
            values = [Fraction(value * multiplier, 10) for value in simplest]
        else:
            multiplier = rng.choice((25, 50, 75, 125))
            values = [
                Fraction(simplest[0] * multiplier),
                Fraction(simplest[1] * multiplier, 100),
            ]
            units = ["cm", "m"]
            if rng.choice((False, True)):
                values.reverse()
                units.reverse()
                simplest.reverse()

        stored = [rational_text(value) for value in values]
        result_text = " : ".join(str(value) for value in simplest)
        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=make_prompt(stored, units),
            answer={"kind": "ratio", "values": simplest},
            answer_display=Content(result_text, result_text),
            worked_solution=(),
            marks=2 if difficulty < 4 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=4),
            parameters={"values": stored, "units": units},
        )
        self.validate(question)
        return question

    def validate(self, question):
        from .worded import is_worded
        if is_worded(question):
            from .ratio_more_contexts import validate as validate_worded
            return validate_worded(self, question)
        require(isinstance(question.answer, dict) and question.answer.get("kind") == "ratio"
                and isinstance(question.answer.get("values"), list), "Unexpected answer shape")
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in (1, 2, 3, 4), "Invalid difficulty")
        stored = question.parameters["values"]
        units = question.parameters["units"]
        values = [Fraction(value) for value in stored]
        answer = question.answer["values"]
        size = 3 if level == 2 else 2
        require(len(values) == len(units) == len(answer) == size, "Ratio length mismatch")
        require(all(value > 0 for value in values), "Non-positive ratio part")
        require(all(type(value) is int and 1 <= value <= 10 for value in answer),
                "Answer must contain bounded positive integers")
        require(reduce(gcd, answer) == 1, "Answer is not in simplest form")
        if level <= 2:
            require(units == [""] * size, "Unexpected units")
            require(all(value.denominator == 1 and value <= 120 for value in values),
                    "Expected bounded integer ratio")
            require(reduce(gcd, [value.numerator for value in values]) > 1,
                    "Question already simplified")
        elif level == 3:
            require(units == [""] * size, "Unexpected units")
            require(any(value.denominator != 1 for value in values), "Missing decimal demand")
            require(all((value * 10).denominator == 1 and value <= 11 for value in values),
                    "Expected tenths")
        else:
            require(sorted(units) == ["cm", "m"], "Expected mixed length units")
            require(all((value * 100).denominator == 1 for value in values),
                    "Unintended precision")
        normalized = [
            value * (100 if unit == "m" else 1)
            for value, unit in zip(values, units)
        ]
        require(
            all(normalized[index] * answer[0] == normalized[0] * answer[index]
                for index in range(1, size)),
            "Answer is not proportional after conversion",
        )
        expected_text = " : ".join(str(value) for value in answer)
        require(question.prompt == make_prompt(stored, units), "Prompt mismatch")
        require(question.answer_display.text == expected_text, "Displayed answer mismatch")
        require(question.answer_display.math_tex == expected_text, "Math answer mismatch")
        return True

    def validate_independently(self, question):
        """Normalize with SymPy, clear denominators and find the integer GCD."""
        from .worded import is_worded
        if is_worded(question):
            from .ratio_more_contexts import validate_independently as independent_worded
            return independent_worded(self, question)
        import sympy

        values = [
            sympy.Rational(value) * (100 if unit == "m" else 1)
            for value, unit in zip(
                question.parameters["values"], question.parameters["units"]
            )
        ]
        denominator = sympy.ilcm(*[int(value.q) for value in values])
        integers = [int(value * denominator) for value in values]
        common = sympy.igcd(*integers)
        expected = [int(value // common) for value in integers]
        require(expected == question.answer["values"], "Independent simplification disagrees")
        return True