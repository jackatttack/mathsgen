"""Expand two linear brackets into a quadratic, using exact integer coefficients."""
from math import gcd

from .core import Content, GeneratorInfo, LayoutHint, Question, make_context, require


INFO = GeneratorInfo(
    id="algebra.expanding.double_brackets",
    version=1,
    topic="algebra",
    subtopic="expanding",
    title="Expand and simplify two brackets",
    difficulty_descriptions={
        1: "Two brackets with positive constants.",
        2: "Two brackets where at least one constant is negative.",
        3: "A squared bracket, written as a product.",
        4: "A leading coefficient greater than one in the first bracket.",
    },
    tags=("algebra", "expanding", "brackets", "quadratics"),
)


def linear_text(coefficient, constant, tex=False):
    """One bracket, written without a redundant coefficient of one."""
    lead = ("" if coefficient == 1 else str(coefficient)) + "x"
    sign = " - " if constant < 0 else " + "
    body = lead + sign + str(abs(constant))
    return r"\left(" + body + r"\right)" if tex else "(" + body + ")"


def polynomial(coefficients, tex=False):
    """Format a quadratic from its coefficients, highest power first."""
    pieces = []
    for value, degree in zip(coefficients, (2, 1, 0)):
        if value == 0:
            continue
        magnitude = abs(value)
        if degree == 0:
            body = str(magnitude)
        else:
            body = "" if magnitude == 1 else str(magnitude)
            body += "x"
            if degree == 2:
                body += "^{2}" if tex else "^2"
        if pieces:
            pieces.append((" - " if value < 0 else " + ") + body)
        else:
            pieces.append(("-" if value < 0 else "") + body)
    return "".join(pieces) or "0"


def expand(first, second):
    """Multiply two linear factors, each given as (coefficient, constant)."""
    lead = first[0] * second[0]
    middle = first[0] * second[1] + first[1] * second[0]
    constant = first[1] * second[1]
    return [lead, middle, constant]


def make_prompt(first, second):
    instruction = "Expand and simplify."
    plain = linear_text(*first) + linear_text(*second)
    maths = linear_text(*first, tex=True) + linear_text(*second, tex=True)
    return Content(instruction + " " + plain, maths, display_text=instruction)


class ExpandDoubleBrackets:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        constants = [value for value in range(-9, 10) if value != 0]

        # Reject an expansion whose x term vanishes. A difference of two
        # squares such as (x + 5)(x - 5) is a distinct archetype and belongs
        # in its own generator, not as an accident of this one.
        for attempt in range(500):
            if difficulty == 1:
                first = (1, rng.randint(1, 9))
                second = (1, rng.randint(1, 9))
            elif difficulty == 2:
                first = (1, rng.choice(constants))
                second = (1, rng.choice(constants))
                if first[1] > 0 and second[1] > 0:
                    second = (1, -second[1])
                if first == second:
                    continue
            elif difficulty == 3:
                first = second = (1, rng.choice(constants))
            else:
                first = (rng.randint(2, 5), rng.choice(constants))
                second = (1, rng.choice(constants))
                # A bracket such as (2x + 4) hides a common factor students
                # are not being asked to notice here.
                if gcd(first[0], abs(first[1])) != 1:
                    continue
            coefficients = expand(first, second)
            if coefficients[1] != 0:
                break
        else:
            raise ValueError("Could not construct a suitable expansion")
        answer_text = polynomial(coefficients)
        answer_tex = polynomial(coefficients, True)

        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=make_prompt(first, second),
            answer={"kind": "polynomial", "coefficients": coefficients},
            answer_display=Content(answer_text, answer_tex),
            worked_solution=(),
            marks=2 if difficulty <= 2 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=5),
            parameters={"first": list(first), "second": list(second)},
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in (1, 2, 3, 4), "Invalid difficulty")
        first = question.parameters["first"]
        second = question.parameters["second"]
        require(len(first) == len(second) == 2, "Expected two linear factors")
        require(all(type(value) is int for value in first + second), "Expected integers")
        require(first[1] != 0 and second[1] != 0, "Unintended single-term bracket")
        require(all(abs(value) <= 9 for value in (first[1], second[1])),
                "Constant outside bounds")
        require(second[0] == 1, "Second bracket must be monic")

        coefficients = question.answer["coefficients"]
        require(coefficients == expand(tuple(first), tuple(second)), "Incorrect expansion")
        require(coefficients[1] != 0, "Expected a surviving x term")
        require(abs(coefficients[2]) <= 81, "Constant term outside bounds")

        if level <= 3:
            require(first[0] == 1, "Expected a monic first bracket")
        if level == 1:
            require(first[1] > 0 and second[1] > 0, "Expected positive constants")
        elif level == 2:
            require(min(first[1], second[1]) < 0, "Expected a negative constant")
            require(first != second, "Unexpected repeated bracket")
        elif level == 3:
            require(first == second, "Expected a squared bracket")
        else:
            require(2 <= first[0] <= 5, "Leading coefficient outside bounds")
            require(gcd(first[0], abs(first[1])) == 1,
                    "First bracket has an unintended common factor")

        require(question.prompt == make_prompt(tuple(first), tuple(second)), "Prompt mismatch")
        require(question.answer_display == Content(
            polynomial(coefficients), polynomial(coefficients, True),
        ), "Displayed answer mismatch")
        return True

    def validate_independently(self, question):
        """Expand symbolically rather than reusing the construction arithmetic."""
        import sympy

        x = sympy.Symbol("x")
        first = question.parameters["first"]
        second = question.parameters["second"]
        product = sympy.expand((first[0] * x + first[1]) * (second[0] * x + second[1]))
        submitted = sum(
            coefficient * x ** power
            for coefficient, power in zip(question.answer["coefficients"], (2, 1, 0))
        )
        require(sympy.expand(product - submitted) == 0, "Independent expansion disagrees")
        return True