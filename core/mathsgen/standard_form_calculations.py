"""Multiply, divide, add and subtract numbers written in standard form.

Difficulty follows the reasoning required rather than the size of the
numbers: level 1 multiplies without renormalising, level 2 divides, level 3
produces a mantissa outside 1 to 10 so the answer must be renormalised, and
level 4 adds or subtracts, which requires a common index first.

Mantissas are stored as digit strings, exactly as the conversion family
stores them, so every value is an exact rational and never a float.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)
from .standard_form import exact_value, standard_form_text


OPERATION_SYMBOLS = {
    "multiply": ("×", r"\times"),
    "divide": ("÷", r"\div"),
    "add": ("+", "+"),
    "subtract": ("-", "-"),
}

OPERATIONS = {1: "multiply", 2: "divide", 3: ("multiply", "divide"),
              4: ("add", "subtract")}


INFO = GeneratorInfo(
    id="number.standard_form.calculations", version=2,
    topic="number", subtopic="standard_form",
    title="Calculations in standard form",
    difficulty_descriptions={
        1: "Multiply in standard form; or lengths, distances and masses in context.",
        2: "Divide in standard form; or population density and rates in context.",
        3: "Multiply or divide, then renormalise; bare or in context.",
        4: "Add or subtract with matched powers; or distances and cargo masses.",
    },
    tags=("standard form", "indices", "calculation", "exact"),
)


def normalise(value):
    """Return the canonical digit string and exponent of a positive rational."""
    require(value > 0, "Standard form here covers positive numbers only")
    exponent = 0
    while value >= 10:
        value /= 10
        exponent += 1
    while value < 1:
        value *= 10
        exponent -= 1
    # The mantissa is exact, so its digits terminate; express it as digits.
    digits = ""
    remainder = value
    while remainder != 0 and len(digits) < 12:
        whole = int(remainder)
        digits += str(whole)
        remainder = (remainder - whole) * 10
    require(remainder == 0, "Mantissa does not terminate")
    return digits, exponent


def presentation(parameters):
    first = standard_form_text(parameters["first_digits"], parameters["first_exponent"])
    second = standard_form_text(
        parameters["second_digits"], parameters["second_exponent"]
    )
    plain_symbol, tex_symbol = OPERATION_SYMBOLS[parameters["operation"]]
    first_tex = standard_form_text(
        parameters["first_digits"], parameters["first_exponent"], True
    )
    second_tex = standard_form_text(
        parameters["second_digits"], parameters["second_exponent"], True
    )
    instruction = (
        "Work out the following, giving your answer in standard form."
    )
    plain = "({}) {} ({})".format(first, plain_symbol, second)
    maths = r"\left(" + first_tex + r"\right) " + tex_symbol + r" \left(" + second_tex + r"\right)"
    return Content(instruction + " " + plain, maths, display_text=instruction)


def combine(parameters):
    """Evaluate the displayed calculation exactly as a rational number."""
    first = exact_value(parameters["first_digits"], parameters["first_exponent"])
    second = exact_value(parameters["second_digits"], parameters["second_exponent"])
    operation = parameters["operation"]
    if operation == "multiply":
        return first * second
    if operation == "divide":
        return first / second
    if operation == "add":
        return first + second
    return first - second


def renormalisation_needed(parameters):
    """Whether the raw mantissa result falls outside 1 to 10.

    This is the single authoritative test: construction rejects a
    calculation whose behaviour does not match its level, and validation
    checks the same condition afterwards.
    """
    first = Fraction(int(parameters["first_digits"]),
                     10 ** (len(parameters["first_digits"]) - 1))
    second = Fraction(int(parameters["second_digits"]),
                      10 ** (len(parameters["second_digits"]) - 1))
    raw = first * second if parameters["operation"] == "multiply" else first / second
    return not (1 <= raw < 10)


def answer_for(parameters):
    digits, exponent = normalise(combine(parameters))
    answer = {
        "kind": "standard_form", "digits": digits, "exponent": exponent,
    }
    display = Content(
        standard_form_text(digits, exponent),
        standard_form_text(digits, exponent, True),
    )
    return answer, display


class StandardFormCalculations:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        from . import standard_form_contexts as worded_forms
        if rng.random() < worded_forms.CONTEXT_SHARE.get(difficulty, 0.0):
            return worded_forms.generate(self, context)

        for attempt in range(500):
            parameters = self.make_calculation(rng, difficulty)
            value = combine(parameters)
            if value <= 0:
                continue
            try:
                digits, exponent = normalise(value)
            except ValueError:
                continue
            if len(digits) > 4 or abs(exponent) > 12:
                continue
            if (difficulty != 4
                    and renormalisation_needed(parameters) != (difficulty == 3)):
                continue
            break
        else:
            raise ValueError("Could not construct a suitable calculation")

        prompt = presentation(parameters)
        answer, display = answer_for(parameters)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=2 if difficulty <= 2 else 3, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=3 if difficulty <= 2 else 4),
            parameters=parameters,
        )
        self.validate(question)
        return question

    def make_calculation(self, rng, difficulty):
        operations = OPERATIONS[difficulty]
        operation = operations if type(operations) is str else rng.choice(operations)
        if difficulty == 4:
            # A shared digit count keeps the subtraction from collapsing to
            # very few significant figures once the indices are matched.
            gap = rng.randint(1, 2)
            exponent = rng.randint(-6, 8 - gap)
            first = self.make_digits(rng, 2)
            second = self.make_digits(rng, 2)
            parameters = {
                "operation": operation,
                "first_digits": first, "first_exponent": exponent + gap,
                "second_digits": second, "second_exponent": exponent,
            }
            return parameters
        first_exponent = rng.randint(-6, 8)
        second_exponent = rng.randint(-6, 8)
        # Level 3 keeps both mantissas at two digits, so renormalising sits
        # on top of a genuine mantissa calculation rather than replacing it.
        lengths = (2, 2) if difficulty == 3 else (
            rng.choice((1, 2)), rng.choice((1, 2))
        )
        first = self.make_digits(rng, lengths[0])
        second = self.make_digits(rng, lengths[1])
        return {
            "operation": operation,
            "first_digits": first, "first_exponent": first_exponent,
            "second_digits": second, "second_exponent": second_exponent,
        }

    @staticmethod
    def make_digits(rng, length):
        """A canonical mantissa: no leading zero and no trailing zero."""
        if length == 1:
            return str(rng.randint(1, 9))
        return str(rng.randint(1, 9)) + str(rng.randint(1, 9))

    def validate(self, question):
        from .worded import is_worded
        if is_worded(question):
            from .standard_form_contexts import validate as validate_worded
            return validate_worded(self, question)
        require(isinstance(question.answer, dict)
                and question.answer.get("kind") == "standard_form", "Unexpected answer shape")
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")

        parameters = question.parameters
        require(set(parameters) == {
            "operation", "first_digits", "first_exponent",
            "second_digits", "second_exponent",
        }, "Unexpected parameters")

        expected = OPERATIONS[level]
        allowed = (expected,) if type(expected) is str else expected
        require(parameters["operation"] in allowed,
                "Operation does not match difficulty")

        for name in ("first_digits", "second_digits"):
            digits = parameters[name]
            require(type(digits) is str and 1 <= len(digits) <= 2 and digits.isdigit(),
                    "Invalid mantissa digits")
            require(level != 3 or len(digits) == 2,
                    "Level 3 requires two-digit mantissas")
            require(digits[0] != "0" and digits[-1] != "0", "Non-canonical mantissa")
        for name in ("first_exponent", "second_exponent"):
            require(type(parameters[name]) is int and -6 <= parameters[name] <= 8,
                    "Exponent outside difficulty bounds")

        answer, display = answer_for(parameters)
        self.check_structure(parameters, answer, level)
        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Display mismatch")
        require(question.prompt == presentation(parameters), "Prompt mismatch")
        require(question.visual_assets("questions") == ()
                and question.visual_assets("answers") == (),
                "This family uses no visual assets")
        return True

    def check_structure(self, parameters, answer, level):
        digits = answer["digits"]
        require(1 <= len(digits) <= 4, "Answer mantissa is too long")
        require(abs(answer["exponent"]) <= 12, "Answer exponent outside bounds")

        if level == 4:
            gap = parameters["first_exponent"] - parameters["second_exponent"]
            require(gap in (1, 2), "Addition requires a small index difference")
            return

        # Levels 1 and 2 must not need renormalising; level 3 must need it.
        require(renormalisation_needed(parameters) == (level == 3),
                "Renormalisation requirement does not match this level")

    def validate_independently(self, question):
        """Rebuild both operands and the answer symbolically and compare."""
        from .worded import is_worded
        if is_worded(question):
            from .standard_form_contexts import validate_independently as independent_worded
            return independent_worded(question)
        import sympy

        parameters = question.parameters

        def value(digits, exponent):
            return sympy.Rational(int(digits), 10 ** (len(digits) - 1)) * (
                sympy.Integer(10) ** exponent
            )

        first = value(parameters["first_digits"], parameters["first_exponent"])
        second = value(parameters["second_digits"], parameters["second_exponent"])
        operation = parameters["operation"]
        if operation == "multiply":
            expected = first * second
        elif operation == "divide":
            expected = first / second
        elif operation == "add":
            expected = first + second
        else:
            expected = first - second

        submitted = value(question.answer["digits"], question.answer["exponent"])
        require(sympy.simplify(submitted - expected) == 0,
                "Independent calculation disagrees")

        # The stated answer must genuinely be in standard form.
        mantissa = sympy.Rational(
            int(question.answer["digits"]), 10 ** (len(question.answer["digits"]) - 1)
        )
        require(1 <= mantissa < 10, "Answer is not in standard form")
        return True