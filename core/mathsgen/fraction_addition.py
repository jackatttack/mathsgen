"""Exact fraction addition with deliberate denominator relationships."""
from fractions import Fraction
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)


INFO = GeneratorInfo(
    id="number.fractions.addition",
    version=2,
    topic="number",
    subtopic="fraction_operations",
    title="Add two fractions",
    difficulty_descriptions={
        1: "Proper positive fractions with the same denominator.",
        2: "One denominator divides the other; or the fraction left after two parts.",
        3: "Different coprime denominators; or the fraction left, in context.",
        4: "Signed improper fractions; or how many are left from a stated total.",
    },
    tags=("fractions", "addition", "common_denominator"),
)


def raw_fraction_tex(numerator, denominator):
    """Show an intermediate fraction without automatically simplifying it."""
    sign = "-" if numerator < 0 else ""
    return sign + r"\frac{" + str(abs(numerator)) + "}{" + str(denominator) + "}"


def sum_text(left, right, tex=False):
    formatter = rational_tex if tex else rational_text
    right_text = formatter(right)
    if right < 0:
        right_text = (
            r"\left(" + right_text + r"\right)"
            if tex else "(" + right_text + ")"
        )
    return formatter(left) + " + " + right_text


class FractionAddition:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        from . import fraction_contexts as worded_forms
        if rng.random() < worded_forms.CONTEXT_SHARE.get(difficulty, 0.0):
            return worded_forms.generate(self, context)

        if difficulty == 1:
            first_denominator = second_denominator = rng.randint(3, 12)
        elif difficulty == 2:
            first_denominator = rng.choice((2, 3, 4, 5, 6))
            second_denominator = first_denominator * rng.choice((2, 3))
        elif difficulty == 3:
            pairs = [
                (a, b) for a in range(2, 10) for b in range(a + 1, 13)
                if gcd(a, b) == 1 and a * b <= 72
            ]
            first_denominator, second_denominator = rng.choice(pairs)
        else:
            first_denominator, second_denominator = rng.choice(
                ((3, 4), (4, 5), (3, 5), (5, 6), (4, 7))
            )

        def numerator(denominator, improper=False):
            candidates = range(denominator + 1, 3 * denominator) if improper else range(1, denominator)
            return rng.choice([value for value in candidates if gcd(value, denominator) == 1])

        left = Fraction(numerator(first_denominator, difficulty == 4), first_denominator)
        right = Fraction(numerator(second_denominator, difficulty == 4), second_denominator)
        if difficulty == 4:
            right = -right
        elif difficulty in (2, 3) and rng.choice((False, True)):
            left, right = right, left

        common = left.denominator * right.denominator // gcd(left.denominator, right.denominator)
        first_scaled = left.numerator * (common // left.denominator)
        second_scaled = right.numerator * (common // right.denominator)
        result = left + right
        combined = first_scaled + second_scaled
        equivalent_right = raw_fraction_tex(second_scaled, common)
        if second_scaled < 0:
            equivalent_right = r"\left(" + equivalent_right + r"\right)"
        equivalent_sum = raw_fraction_tex(first_scaled, common) + " + " + equivalent_right
        steps = [
            Content("Use the lowest common denominator, {}.".format(common)),
            Content("Write equivalent fractions.", equivalent_sum),
            Content(
                "Add the numerators and keep the denominator.",
                raw_fraction_tex(combined, common),
            ),
            Content(
                "Simplify the result." if gcd(abs(combined), common) > 1
                else "The result is already in simplest form.",
                rational_tex(result),
            ),
        ]
        instruction = "Work out the following. Give your answer in simplest form."
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
                instruction + " " + sum_text(left, right),
                sum_text(left, right, True),
                display_text=instruction,
            ),
            answer={"kind": "rational", "value": rational_text(result)},
            answer_display=Content(rational_text(result), rational_tex(result)),
            worked_solution=tuple(steps),
            marks=2 if difficulty <= 2 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=5),
            parameters={"left": rational_text(left), "right": rational_text(right)},
        )
        self.validate(question)
        return question

    def validate(self, question):
        from .worded import is_worded
        if is_worded(question):
            from .fraction_contexts import validate as validate_worded
            return validate_worded(self, question)
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in (1, 2, 3, 4), "Invalid difficulty")
        left = Fraction(question.parameters["left"])
        right = Fraction(question.parameters["right"])
        result = Fraction(question.answer["value"])
        require(result == left + right, "Incorrect sum")
        require(question.answer["value"] == rational_text(result), "Answer is not simplified")
        require(left.denominator > 1 and right.denominator > 1, "Unintended integer operand")
        common = left.denominator * right.denominator // gcd(left.denominator, right.denominator)
        require(common <= 72, "Common denominator outside bounds")
        if level < 4:
            require(0 < left < 1 and 0 < right < 1, "Expected proper positive operands")
        if level == 1:
            require(left.denominator == right.denominator, "Expected equal denominators")
        elif level == 2:
            smaller, larger = sorted((left.denominator, right.denominator))
            require(larger > smaller and larger % smaller == 0, "Expected nested denominators")
        elif level == 3:
            require(
                left.denominator != right.denominator
                and gcd(left.denominator, right.denominator) == 1,
                "Expected different coprime denominators",
            )
        else:
            require(1 < left < 3 and -3 < right < -1, "Expected signed improper operands")
            require(result != 0, "Unintended complete cancellation")
        instruction = "Work out the following. Give your answer in simplest form."
        require(question.prompt.text == instruction + " " + sum_text(left, right), "Prompt mismatch")
        require(question.prompt.math_tex == sum_text(left, right, True), "Math prompt mismatch")
        require(question.answer_display.text == rational_text(result), "Displayed answer mismatch")
        require(question.answer_display.math_tex == rational_tex(result), "Math answer mismatch")
        return True

    def validate_independently(self, question):
        """Use SymPy rationals to check the emitted operands and answer."""
        from .worded import is_worded
        if is_worded(question):
            from .fraction_contexts import validate_independently as independent_worded
            return independent_worded(self, question)
        import sympy

        left = sympy.Rational(question.parameters["left"])
        right = sympy.Rational(question.parameters["right"])
        answer = sympy.Rational(question.answer["value"])
        require(sympy.cancel(left + right - answer) == 0, "Independent sum disagrees")
        return True