"""Zero, negative and fractional indices evaluated as exact rational values.

Difficulty follows the meaning of the index rather than the size of the
numbers: an index of zero or one, then a negative index as a reciprocal,
then a unit fraction as a root, then a fractional index whose numerator
does real work and may also be negative.

Every base is chosen as a perfect power of the relevant root, so each
answer is exactly rational and no rounding is ever involved.
"""
from fractions import Fraction
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)


# --- Editable difficulty bounds -------------------------------------------
# Each mapping keeps the printed base and the exact answer at a size a
# student can reasonably handle without a calculator.
UNIT_INDICES = (0, 1)
UNIT_BASES = (2, 25)
NEGATIVE_BASES = {2: 12, 3: 10, 4: 7}
ROOT_BASES = {2: 12, 3: 6, 4: 4, 5: 3}
FRACTIONAL_ROOTS = {2: 9, 3: 5, 4: 3}
FRACTIONAL_NUMERATORS = (2, 3)


INFO = GeneratorInfo(
    id="number.indices.rules", version=2,
    topic="number", subtopic="indices",
    title="Zero, negative and fractional indices",
    difficulty_descriptions={
        1: "Indices of zero and one.",
        2: "Negative integer indices as reciprocals.",
        3: "Find a root or compare two unit fractional powers.",
        4: "Evaluate a fractional power or combine it with a negative power.",
    },
    tags=("indices", "powers", "roots", "reciprocals", "exact"),
)


def integer_root(base, index):
    """Return the exact integer root, refusing anything that is not exact."""
    estimate = round(base ** (1.0 / index))
    for candidate in (estimate - 1, estimate, estimate + 1):
        if candidate > 0 and candidate ** index == base:
            return candidate
    raise ValueError("Base is not a perfect power for this index")


def exact_value(base, exponent):
    """Evaluate the power exactly, via the root then the numerator."""
    exponent = Fraction(exponent)
    root = integer_root(base, exponent.denominator)
    magnitude = Fraction(root) ** abs(exponent.numerator)
    return magnitude if exponent.numerator >= 0 else 1 / magnitude


def power_text(base, exponent, tex=False):
    if tex:
        return "{}^{{{}}}".format(base, rational_tex(exponent))
    written = rational_text(exponent)
    if exponent < 0 or exponent.denominator != 1:
        written = "(" + written + ")"
    return "{}^{}".format(base, written)


def presentation(parameters):
    base = parameters["base"]
    exponent = Fraction(parameters["exponent"])
    instruction = "Work out the exact value of this power."
    return Content(
        instruction + " " + power_text(base, exponent),
        power_text(base, exponent, True),
        display_text=instruction,
    )


def answer_for(parameters):
    value = exact_value(parameters["base"], Fraction(parameters["exponent"]))
    answer = {"kind": "exact_value", "value": rational_text(value)}
    display = Content(rational_text(value), rational_tex(value))
    return answer, display


class IndexRules:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        if difficulty in (3, 4) and rng.random() < 0.5:
            from .index_rule_forms import generate
            return generate(
                self, context,
                "compare_roots" if difficulty == 3 else "combined_powers",
            )
        base, exponent = self.make_power(rng, difficulty)
        parameters = {"base": base, "exponent": rational_text(exponent)}

        prompt = presentation(parameters)
        answer, display = answer_for(parameters)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=1 if difficulty == 1 else 2 if difficulty <= 3 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=2 if difficulty <= 2 else 3),
            parameters=parameters,
        )
        self.validate(question)
        return question

    def make_power(self, rng, difficulty):
        if difficulty == 1:
            return rng.randint(*UNIT_BASES), Fraction(rng.choice(UNIT_INDICES))
        if difficulty == 2:
            magnitude = rng.choice(sorted(NEGATIVE_BASES))
            return rng.randint(2, NEGATIVE_BASES[magnitude]), Fraction(-magnitude)
        if difficulty == 3:
            denominator = rng.choice(sorted(ROOT_BASES))
            root = rng.randint(2, ROOT_BASES[denominator])
            return root ** denominator, Fraction(1, denominator)
        denominator = rng.choice(sorted(FRACTIONAL_ROOTS))
        numerator = rng.choice(
            [value for value in FRACTIONAL_NUMERATORS if gcd(value, denominator) == 1]
        )
        root = rng.randint(2, FRACTIONAL_ROOTS[denominator])
        sign = rng.choice((1, -1))
        return root ** denominator, Fraction(sign * numerator, denominator)

    def validate(self, question):
        if isinstance(question.parameters, dict) and "form" in question.parameters:
            from .index_rule_forms import validate
            return validate(self, question)
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")

        parameters = question.parameters
        require(set(parameters) == {"base", "exponent"}, "Unexpected parameters")
        base = parameters["base"]
        require(type(base) is int and base >= 2, "Base must be an integer above one")
        exponent = Fraction(parameters["exponent"])
        require(parameters["exponent"] == rational_text(exponent),
                "Non-canonical exponent")

        self.check_structure(base, exponent, level)

        answer, display = answer_for(parameters)
        value = Fraction(answer["value"])
        require(value > 0, "Answer must be positive")
        require(value.numerator <= 1000 and value.denominator <= 20736,
                "Answer outside difficulty bounds")
        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Display mismatch")
        require(question.prompt == presentation(parameters), "Prompt mismatch")
        require(question.visual_assets("questions") == ()
                and question.visual_assets("answers") == (),
                "This family uses no visual assets")
        return True

    def check_structure(self, base, exponent, level):
        if level == 1:
            require(exponent.denominator == 1 and exponent.numerator in UNIT_INDICES,
                    "Expected an index of zero or one")
            require(UNIT_BASES[0] <= base <= UNIT_BASES[1], "Base outside bounds")
        elif level == 2:
            require(exponent.denominator == 1 and exponent < 0,
                    "Expected a negative integer index")
            magnitude = -exponent.numerator
            require(magnitude in NEGATIVE_BASES, "Index outside bounds")
            require(2 <= base <= NEGATIVE_BASES[magnitude], "Base outside bounds")
        elif level == 3:
            require(exponent.numerator == 1 and exponent.denominator in ROOT_BASES,
                    "Expected a unit fractional index")
            root = integer_root(base, exponent.denominator)
            require(2 <= root <= ROOT_BASES[exponent.denominator],
                    "Root outside bounds")
        else:
            require(exponent.denominator in FRACTIONAL_ROOTS,
                    "Expected a fractional index")
            require(abs(exponent.numerator) in FRACTIONAL_NUMERATORS,
                    "Expected a numerator above one")
            root = integer_root(base, exponent.denominator)
            require(2 <= root <= FRACTIONAL_ROOTS[exponent.denominator],
                    "Root outside bounds")

    def validate_independently(self, question):
        """Let SymPy evaluate the power directly, without the root helper."""
        if isinstance(question.parameters, dict) and "form" in question.parameters:
            from .index_rule_forms import validate_independently
            return validate_independently(question)
        import sympy

        base = sympy.Integer(question.parameters["base"])
        exponent = sympy.Rational(question.parameters["exponent"])
        value = sympy.simplify(base ** exponent)
        require(value.is_rational, "Independent evaluation is not rational")
        require(value == sympy.Rational(question.answer["value"]),
                "Independent evaluation disagrees")
        return True