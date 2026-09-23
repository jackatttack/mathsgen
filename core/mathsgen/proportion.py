"""Direct and inverse proportion, constructed from an exact constant.

Both relationships are "find the constant, then use it", so one class holds
the shared construction and each registered class supplies its own equation
and wording. The constant is chosen first and the given pair derived from
it, so every value in the question and its answer is exact.
"""
from fractions import Fraction
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


from .rounding import decimal_text, terminates


def lcm(first, second):
    return first // gcd(first, second) * second


# Each context names the two quantities and their units, so the wording
# stays concrete rather than reading as bare letters. The two relationships
# need different contexts: distance against time really is direct, so using
# it for inverse proportion would describe something physically backwards.
DIRECT_CONTEXTS = (
    {"first": "the cost", "second": "the number of items",
     "first_unit": "pounds", "second_unit": ""},
    {"first": "the mass", "second": "the volume",
     "first_unit": "grams", "second_unit": "cm³"},
    {"first": "the distance", "second": "the time",
     "first_unit": "metres", "second_unit": "seconds"},
)

INVERSE_CONTEXTS = (
    {"first": "the time taken", "second": "the number of workers",
     "first_unit": "hours", "second_unit": ""},
    {"first": "the journey time", "second": "the average speed",
     "first_unit": "hours", "second_unit": "km/h"},
    {"first": "the pressure", "second": "the volume",
     "first_unit": "pascals", "second_unit": "cm³"},
)

CONTEXTS = DIRECT_CONTEXTS + INVERSE_CONTEXTS

POWERS = {1: 1, 2: 1, 3: 2, 4: 2}





UNIT_SINGULARS = {
    "pounds": "pound", "grams": "gram", "metres": "metre",
    "seconds": "second", "hours": "hour", "pascals": "pascal",
}


def quantity_text(value, unit):
    """A value with its unit, made singular when the value is exactly one."""
    text = decimal_text(Fraction(value))
    if not unit:
        return text
    if Fraction(value) == 1:
        unit = UNIT_SINGULARS.get(unit, unit)
    return text + " " + unit


def relation_text(relationship, power, context):
    """The stated relationship, built from the context nouns directly.

    The nouns are inserted by formatting rather than by substituting into a
    template, because a replace would also strike letters inside words:
    swapping y for a noun turns "directly" into "directl<noun>".
    """
    second = context["second"]
    subject = second if power == 1 else "the square of " + second
    manner = "directly" if relationship == "direct" else "inversely"
    return "{} is {} proportional to {}".format(context["first"], manner, subject)


def sentence_case(text):
    return text[0].upper() + text[1:] if text else text


def make_prompt(relationship, power, given, target, context):
    return Content(
        "{}. When {} is {}, {} is {}. Find {} when {} is {}.".format(
            sentence_case(relation_text(relationship, power, context)),
            context["second"], quantity_text(given[1], context["second_unit"]),
            context["first"], quantity_text(given[0], context["first_unit"]),
            context["first"], context["second"],
            quantity_text(target, context["second_unit"]),
        )
    )


class Proportion:
    """Shared construction; each relationship is registered separately."""

    def choose_context(self, rng, difficulty):
        return rng.choice(self.contexts)

    @staticmethod
    def pick_values(rng, difficulty):
        """The given and target values of the second quantity."""
        given = rng.randint(2, 9)
        target = rng.choice([value for value in range(2, 13) if value != given])
        return given, target

    @staticmethod
    def pick_constant(rng, difficulty, given, target, power):
        return rng.randint(2, 60)

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        wording = self.choose_context(rng, difficulty)
        power = POWERS[difficulty]

        for attempt in range(500):
            given_second, target_second = self.pick_values(rng, difficulty)
            constant = self.pick_constant(rng, difficulty, given_second, target_second, power)
            given_first = self.apply(constant, given_second, power)
            result = self.apply(constant, target_second, power)
            if given_first == result:
                continue
            if self.acceptable(given_first, result, difficulty):
                break
        else:
            raise ValueError("Could not construct a suitable proportion question")

        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=make_prompt(
                self.relationship, power,
                (given_first, given_second), target_second, wording,
            ),
            answer={
                "kind": "proportion",
                "constant": rational_text(Fraction(constant)),
                "value": rational_text(Fraction(result)),
                "unit": wording["first_unit"],
            },
            answer_display=Content(
                quantity_text(result, wording["first_unit"])
            ),
            worked_solution=(),
            marks=3 if difficulty <= 2 else 4,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=6),
            parameters={
                "constant": rational_text(Fraction(constant)),
                "given": [rational_text(Fraction(given_first)),
                          rational_text(Fraction(given_second))],
                "target": rational_text(Fraction(target_second)),
                "power": power,
                "context": wording,
            },
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in POWERS, "Invalid difficulty")
        constant = Fraction(question.parameters["constant"])
        given = [Fraction(value) for value in question.parameters["given"]]
        target = Fraction(question.parameters["target"])
        power = question.parameters["power"]
        wording = question.parameters["context"]
        require(power == POWERS[level], "Power does not match the difficulty")
        require(wording in self.contexts,
                "Context does not suit this relationship")
        require(power == 1 or wording["second"] != "the number of workers",
                "Workers against time is not a square relationship")
        require(constant > 0 and all(value > 0 for value in given) and target > 0,
                "Expected positive quantities")
        require(target != given[1], "The target repeats the given value")

        require(given[0] == self.apply(constant, given[1], power),
                "The given pair does not satisfy the relationship")
        result = self.apply(constant, target, power)
        require(result != given[0], "The answer repeats the given value")
        require(self.acceptable(given[0], result, level), "Values outside difficulty rules")
        require(question.answer["value"] == rational_text(result), "Incorrect result")
        require(question.answer["constant"] == rational_text(constant), "Incorrect constant")
        require(question.answer["unit"] == wording["first_unit"], "Unexpected unit")
        require(question.prompt == make_prompt(
            self.relationship, power, (given[0], given[1]), target, wording,
        ), "Prompt mismatch")
        require(question.answer_display == Content(
            quantity_text(result, wording["first_unit"])
        ), "Displayed answer mismatch")
        return True

    def validate_independently(self, question):
        """Recover the constant from the given pair by solving, then reapply it."""
        import sympy

        given = [sympy.Rational(value) for value in question.parameters["given"]]
        target = sympy.Rational(question.parameters["target"])
        power = question.parameters["power"]
        k = sympy.Symbol("k", positive=True)

        if self.relationship == "direct":
            equation = sympy.Eq(given[0], k * given[1] ** power)
        else:
            equation = sympy.Eq(given[0], k / given[1] ** power)
        solutions = sympy.solve(equation, k)
        require(len(solutions) == 1, "Expected exactly one constant")
        constant = solutions[0]
        require(constant == sympy.Rational(question.answer["constant"]),
                "Independent constant disagrees")

        if self.relationship == "direct":
            expected = constant * target ** power
        else:
            expected = constant / target ** power
        require(expected == sympy.Rational(question.answer["value"]),
                "Independent proportion result disagrees")
        return True


class DirectProportion(Proportion):
    relationship = "direct"
    contexts = DIRECT_CONTEXTS
    info = GeneratorInfo(
        id="ratio.proportion.direct", version=2, topic="ratio",
        subtopic="proportion", title="Direct proportion",
        difficulty_descriptions={
            1: "A whole-number constant with a whole-number answer.",
            2: "A larger constant, still with exact values.",
            3: "Proportional to the square of the second quantity.",
            4: "Proportional to a square, with a larger constant.",
        },
        tags=("proportion", "direct", "constant_of_proportionality"),
    )

    @staticmethod
    def apply(constant, value, power):
        return Fraction(constant) * Fraction(value) ** power

    @staticmethod
    def acceptable(given_first, result, difficulty):
        limit = 400 if difficulty <= 2 else 4000
        return (given_first.denominator == 1 and result.denominator == 1
                and given_first <= limit and result <= limit)


class InverseProportion(Proportion):
    relationship = "inverse"
    contexts = INVERSE_CONTEXTS

    def choose_context(self, rng, difficulty):
        """Workers against time is a linear inverse relationship.

        Doubling the workers halves the time; it does not quarter it. So
        that context is excluded from the squared levels, where only the
        genuinely square relationships remain.
        """
        if POWERS[difficulty] == 1:
            return rng.choice(self.contexts)
        return rng.choice([
            wording for wording in self.contexts
            if wording["second"] != "the number of workers"
        ])

    @staticmethod
    def pick_values(rng, difficulty):
        if difficulty == 3:
            # Whole-number answers on both sides need a constant divisible by
            # both squares, so keep the values small enough that a multiple of
            # their lowest common multiple stays within sensible bounds.
            given = rng.randint(2, 6)
            target = rng.choice([value for value in range(2, 7) if value != given])
            return given, target
        return Proportion.pick_values(rng, difficulty)

    @staticmethod
    def pick_constant(rng, difficulty, given, target, power):
        """Build the constant from the values, rather than searching for one.

        An inverse question needs k divided by each value to come out
        exactly, so k is chosen as a multiple of the lowest common multiple
        of those divisors. Searching randomly for such a k succeeds too
        rarely at the squared level to be reliable.
        """
        if difficulty in (1, 3):
            step = lcm(given ** power, target ** power)
            highest = max(1, 400 // step)
            return step * rng.randint(1, min(highest, 12))
        return Proportion.pick_constant(rng, difficulty, given, target, power)
    info = GeneratorInfo(
        id="ratio.proportion.inverse", version=2, topic="ratio",
        subtopic="proportion", title="Inverse proportion",
        difficulty_descriptions={
            1: "A whole-number constant with a whole-number answer.",
            2: "An answer that is an exact fraction.",
            3: "Inversely proportional to the square of the second quantity.",
            4: "Inversely proportional to a square, with an exact fractional answer.",
        },
        tags=("proportion", "inverse", "constant_of_proportionality"),
    )

    @staticmethod
    def apply(constant, value, power):
        return Fraction(constant) / Fraction(value) ** power

    @staticmethod
    def acceptable(given_first, result, difficulty):
        if difficulty in (1, 3):
            # Whole-number answers at the easier level of each power.
            return (given_first.denominator == 1 and result.denominator == 1
                    and result <= 400)
        # The harder levels deliberately admit exact fractional answers, but
        # only ones that terminate as decimals: a denominator whose only
        # prime factors are 2 and 5. A third would recur and could not be
        # written exactly.
        return (terminates(given_first) and terminates(result)
                and given_first.denominator <= 20 and result.denominator <= 20
                and result <= 400)