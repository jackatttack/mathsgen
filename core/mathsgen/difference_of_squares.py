"""Factorise a difference of two squares, including a common factor first.

Every expression is built from its factors, so the squares are exact by
construction: a leading square, an optional common factor, and either a
square number or a second squared letter.
"""
from math import gcd

from .core import Content, GeneratorInfo, LayoutHint, Question, make_context, require


INFO = GeneratorInfo(
    id="algebra.factorising.difference_of_squares",
    version=1,
    topic="algebra",
    subtopic="factorising",
    title="Factorise a difference of two squares",
    difficulty_descriptions={
        1: "A squared letter minus a square number.",
        2: "A squared coefficient minus a square number.",
        3: "A difference of squares in two letters.",
        4: "A common factor to take out before factorising.",
    },
    tags=("algebra", "factorising", "difference_of_squares"),
)

LETTER_PAIRS = (("x", "y"), ("a", "b"), ("p", "q"))
# Never perfect squares: a square common factor could be absorbed into the
# brackets, leaving the fully factorised form ambiguous.
COMMON_FACTORS = (2, 3, 5, 6, 7)


def square_text(coefficient, letter, tex=False):
    """A squared term such as 9x^2, or a bare square number when no letter."""
    if letter is None:
        return str(coefficient)
    body = ("" if coefficient == 1 else str(coefficient)) + letter
    return body + ("^{2}" if tex else "^2")


def linear_text(coefficient, letter):
    """One bracket entry: 3x, x, or a bare number."""
    if letter is None:
        return str(coefficient)
    return ("" if coefficient == 1 else str(coefficient)) + letter


def expression_text(factor, first, second, letters, tex=False):
    """The expression as presented, before any factorising."""
    lead = square_text(factor * first * first, letters[0], tex)
    tail = square_text(factor * second * second, letters[1], tex)
    return lead + " - " + tail


def factorised_text(factor, first, second, letters, tex=False):
    """The complete answer, with the common factor outside when present."""
    left = linear_text(first, letters[0])
    right = linear_text(second, letters[1])
    outside = "" if factor == 1 else str(factor)
    if tex:
        return (outside + r"\left(" + left + " + " + right + r"\right)"
                + r"\left(" + left + " - " + right + r"\right)")
    return outside + "(" + left + " + " + right + ")(" + left + " - " + right + ")"


def make_prompt(factor, first, second, letters):
    instruction = "Factorise fully."
    plain = expression_text(factor, first, second, letters)
    maths = expression_text(factor, first, second, letters, True)
    return Content(instruction + " " + plain, maths, display_text=instruction)


class DifferenceOfSquares:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        first_letter, second_letter = rng.choice(LETTER_PAIRS)
        letters = (first_letter, None)
        factor = 1

        for attempt in range(500):
            if difficulty == 1:
                first, second = 1, rng.randint(2, 12)
            elif difficulty == 2:
                first, second = rng.randint(2, 6), rng.randint(2, 12)
            elif difficulty == 3:
                letters = (first_letter, second_letter)
                first, second = rng.randint(1, 6), rng.randint(1, 6)
                if (first, second) == (1, 1):
                    continue
            else:
                factor = rng.choice(COMMON_FACTORS)
                first, second = rng.randint(1, 3), rng.randint(2, 7)
            if gcd(first, second) == 1:
                break
        else:
            raise ValueError("Could not construct a suitable difference of squares")

        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=make_prompt(factor, first, second, letters),
            answer={
                "kind": "factorised_difference",
                "common_factor": factor,
                "first": first,
                "second": second,
                "letters": list(letters),
            },
            answer_display=Content(
                factorised_text(factor, first, second, letters),
                factorised_text(factor, first, second, letters, True),
            ),
            worked_solution=(),
            marks=1 if difficulty == 1 else (2 if difficulty <= 3 else 3),
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=4),
            parameters={
                "common_factor": factor,
                "first": first,
                "second": second,
                "letters": list(letters),
            },
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in (1, 2, 3, 4), "Invalid difficulty")
        factor = question.parameters["common_factor"]
        first = question.parameters["first"]
        second = question.parameters["second"]
        letters = tuple(question.parameters["letters"])
        require(all(type(value) is int for value in (factor, first, second)),
                "Expected integer construction values")
        require(first >= 1 and second >= 1 and factor >= 1, "Expected positive values")
        require(gcd(first, second) == 1,
                "A shared factor would leave the answer not fully factorised")
        require(letters[0] in [pair[0] for pair in LETTER_PAIRS], "Unexpected first letter")

        if level == 3:
            require(letters in LETTER_PAIRS, "Expected a matching letter pair")
            require((first, second) != (1, 1), "Expected a coefficient on one square")
        else:
            require(letters[1] is None, "Expected a square number")
        if level <= 3:
            require(factor == 1, "Unexpected common factor")
        if level == 1:
            require(first == 1, "Expected a plain squared letter")
            require(2 <= second <= 12, "Square root outside bounds")
        elif level == 2:
            require(2 <= first <= 6 and 2 <= second <= 12, "Coefficient outside bounds")
        elif level == 4:
            require(factor in COMMON_FACTORS, "Expected a non-square common factor")
            require(1 <= first <= 3 and 2 <= second <= 7, "Coefficient outside bounds")

        lead = factor * first * first
        tail = factor * second * second
        require(lead <= 600 and tail <= 600, "Coefficient outside bounds")
        require(question.answer == {
            "kind": "factorised_difference",
            "common_factor": factor, "first": first, "second": second,
            "letters": list(letters),
        }, "Non-canonical answer")
        require(question.prompt == make_prompt(factor, first, second, letters),
                "Prompt mismatch")
        require(question.answer_display == Content(
            factorised_text(factor, first, second, letters),
            factorised_text(factor, first, second, letters, True),
        ), "Displayed answer mismatch")
        return True

    def validate_independently(self, question):
        """Expand the submitted factors, then confirm the factorisation is complete."""
        import sympy

        factor = question.answer["common_factor"]
        first = question.answer["first"]
        second = question.answer["second"]
        letters = question.answer["letters"]
        left = sympy.Symbol(letters[0])
        right = sympy.Symbol(letters[1]) if letters[1] else sympy.Integer(1)

        expression = (factor * (first * left) ** 2) - (factor * (second * right) ** 2)
        submitted = factor * (first * left + second * right) * (first * left - second * right)
        require(sympy.expand(expression - submitted) == 0, "Independent expansion disagrees")

        # A remaining numerical content would mean the answer is not fully
        # factorised, so the common factor must account for all of it.
        content = sympy.Poly(expression, *[s for s in (left, right) if s.is_Symbol]).content()
        require(int(content) == factor, "Independent full-factorisation check disagrees")
        return True