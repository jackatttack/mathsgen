"""Fraction multiplication and division with deliberate cancellation structure."""
from fractions import Fraction
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)


DENOMINATORS = (2, 3, 4, 5, 6, 7, 8, 9)
SYMBOLS = {"multiply": ("×", r"\times"), "divide": ("÷", r"\div")}
INSTRUCTION = "Work out the following. Give your answer in simplest form."


def effective_right(right, operation):
    """Dividing by a fraction is multiplying by its reciprocal."""
    return right if operation == "multiply" else 1 / right


def cancels(left, right, operation):
    """Whether a common factor can be cancelled before multiplying out."""
    other = effective_right(right, operation)
    return (gcd(abs(left.numerator), other.denominator) > 1
            or gcd(abs(other.numerator), left.denominator) > 1)


def expression_text(left, right, operation, tex=False):
    formatter = rational_tex if tex else rational_text
    symbol = SYMBOLS[operation][1 if tex else 0]
    right_text = formatter(right)
    if right < 0:
        right_text = (
            r"\left(" + right_text + r"\right)" if tex else "(" + right_text + ")"
        )
    return formatter(left) + " " + symbol + " " + right_text


def proper_fraction(rng):
    """A positive fraction below one, already in simplest form."""
    denominator = rng.choice(DENOMINATORS)
    numerator = rng.choice([
        value for value in range(1, denominator) if gcd(value, denominator) == 1
    ])
    return Fraction(numerator, denominator)


def improper_fraction(rng):
    """A positive fraction above one, already in simplest form."""
    denominator = rng.choice(DENOMINATORS)
    numerator = rng.choice([
        value for value in range(denominator + 1, 4 * denominator)
        if gcd(value, denominator) == 1
    ])
    return Fraction(numerator, denominator)


class FractionProduct:
    """Shared exact construction; each operation is registered separately."""

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        from . import fraction_contexts as worded_forms
        if rng.random() < worded_forms.CONTEXT_SHARE.get(difficulty, 0.0):
            return worded_forms.generate(self, context)

        if difficulty <= 2:
            # Level 1 must multiply straight across; level 2 must cancel first.
            for attempt in range(500):
                left, right = proper_fraction(rng), proper_fraction(rng)
                if cancels(left, right, self.operation) == (difficulty == 2):
                    break
            else:
                raise ValueError("Could not construct the requested cancellation")
        elif difficulty == 3:
            whole = Fraction(rng.randint(2, 12))
            fraction = proper_fraction(rng)
            left, right = (
                (whole, fraction) if rng.choice((False, True)) else (fraction, whole)
            )
        else:
            left, right = improper_fraction(rng), improper_fraction(rng)
            if rng.choice((False, True)):
                left = -left
            else:
                right = -right

        result = left * right if self.operation == "multiply" else left / right
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
                INSTRUCTION + " " + expression_text(left, right, self.operation),
                expression_text(left, right, self.operation, True),
                display_text=INSTRUCTION,
            ),
            answer={"kind": "rational", "value": rational_text(result)},
            answer_display=Content(rational_text(result), rational_tex(result)),
            worked_solution=(),
            marks=2 if difficulty <= 2 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=4),
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
        require(left != 0 and right != 0, "Zero operand")
        expected = left * right if self.operation == "multiply" else left / right
        require(result == expected, "Incorrect result")
        require(question.answer["value"] == rational_text(result), "Answer is not simplified")
        require(abs(result) <= self.result_bound, "Result outside bounds")

        if level <= 2:
            require(0 < left < 1 and 0 < right < 1, "Expected proper positive operands")
            require(left.denominator in DENOMINATORS and right.denominator in DENOMINATORS,
                    "Denominator outside bounds")
            require(cancels(left, right, self.operation) == (level == 2),
                    "Incorrect cancellation structure")
        elif level == 3:
            whole = left if left.denominator == 1 else right
            fraction = right if left.denominator == 1 else left
            require((left.denominator == 1) != (right.denominator == 1),
                    "Expected exactly one whole-number operand")
            require(2 <= whole <= 12, "Whole number outside bounds")
            require(0 < fraction < 1 and fraction.denominator in DENOMINATORS,
                    "Expected a proper positive fraction")
        else:
            require((left < 0) != (right < 0), "Expected exactly one negative operand")
            require(1 < abs(left) < 4 and 1 < abs(right) < 4, "Expected improper operands")
            require(left.denominator in DENOMINATORS and right.denominator in DENOMINATORS,
                    "Denominator outside bounds")

        expected_text = expression_text(left, right, self.operation)
        expected_tex = expression_text(left, right, self.operation, True)
        require(question.prompt == Content(
            INSTRUCTION + " " + expected_text, expected_tex, display_text=INSTRUCTION,
        ), "Prompt mismatch")
        require(question.answer_display == Content(rational_text(result), rational_tex(result)),
                "Displayed answer mismatch")
        return True

    def validate_independently(self, question):
        """Recompute with SymPy rationals from the emitted operands."""
        from .worded import is_worded
        if is_worded(question):
            from .fraction_contexts import validate_independently as independent_worded
            return independent_worded(self, question)
        import sympy

        left = sympy.Rational(question.parameters["left"])
        right = sympy.Rational(question.parameters["right"])
        answer = sympy.Rational(question.answer["value"])
        expected = left * right if self.operation == "multiply" else left / right
        require(sympy.cancel(expected - answer) == 0, "Independent result disagrees")
        return True


class FractionMultiplication(FractionProduct):
    operation = "multiply"
    # Multiplying by a proper fraction shrinks the result.
    result_bound = 20
    info = GeneratorInfo(
        id="number.fractions.multiplication", version=2, topic="number",
        subtopic="fraction_operations", title="Multiply two fractions",
        difficulty_descriptions={
            1: "Proper fractions that multiply straight across.",
            2: "Proper fractions that cancel first; or a fraction of a fraction.",
            3: "A whole number times a proper fraction; or repeated batches.",
            4: "Signed improper fractions; or the area of a rug with mixed-number sides.",
        },
        tags=("fractions", "multiplication", "cancelling"),
    )


class FractionDivision(FractionProduct):
    operation = "divide"
    # Dividing by a proper fraction grows the result: 12 divided by 1/9 is 108.
    # That is a deliberate part of the topic, so this bound is deliberately looser.
    result_bound = 120
    info = GeneratorInfo(
        id="number.fractions.division", version=2, topic="number",
        subtopic="fraction_operations", title="Divide two fractions",
        difficulty_descriptions={
            1: "Proper fractions with no cancelling after inverting.",
            2: "Proper fractions that cancel after inverting; or sharing equally.",
            3: "A whole number and a proper fraction; or how many pieces fit.",
            4: "Signed improper fractions; or shelves cut from a mixed-length plank.",
        },
        tags=("fractions", "division", "reciprocal"),
    )