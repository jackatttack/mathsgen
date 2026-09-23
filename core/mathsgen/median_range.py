"""Median and range from a listed data set, using exact rational arithmetic."""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


INFO = GeneratorInfo(
    id="data.averages.median_range",
    version=1,
    topic="data",
    subtopic="averages",
    title="Find the median and the range",
    difficulty_descriptions={
        1: "An odd number of positive integers, so the median is a listed value.",
        2: "An even number of positive integers, so the median lies between two values.",
        3: "Positive and negative integers with an even count.",
        4: "Values in tenths with an even count.",
    },
    tags=("averages", "median", "range"),
)

# Level 4 bounds are expressed in tenths; every other level counts in units.
COUNTS = {1: (5, 7), 2: (6, 8), 3: (6, 8), 4: (6, 8)}
BOUNDS = {1: (1, 40), 2: (1, 40), 3: (-20, 20), 4: (11, 89)}


def decimal_text(value):
    """Exact formatting for this family's integers, tenths and hundredths."""
    value = Fraction(value)
    scaled = value * 100
    require(scaled.denominator == 1, "Expected at most two decimal places")
    sign = "-" if scaled < 0 else ""
    whole, remainder = divmod(abs(scaled.numerator), 100)
    return sign + str(whole) + (
        "." + str(remainder).zfill(2).rstrip("0") if remainder else ""
    )


def median_value(values):
    """The middle value, or the midpoint of the two middle values."""
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def make_prompt(values):
    listed = ", ".join(decimal_text(Fraction(value)) for value in values)
    return Content("Find the median and the range of these numbers: " + listed + ".")


def answer_text(median, spread):
    return "median = {}, range = {}".format(decimal_text(median), decimal_text(spread))


class MedianAndRange:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        count = rng.choice(COUNTS[difficulty])
        lower, upper = BOUNDS[difficulty]
        scale = 10 if difficulty == 4 else 1
        if difficulty == 4:
            # Excluding whole tenths keeps every listed value a decimal.
            pool = [units for units in range(lower, upper + 1) if units % 10]
        else:
            pool = list(range(lower, upper + 1))

        for attempt in range(500):
            units = rng.sample(pool, count)
            if difficulty == 3 and not (min(units) < 0 < max(units)):
                continue
            break
        else:
            raise ValueError("Could not construct a suitable data set")

        values = [Fraction(unit, scale) for unit in units]
        stored = [rational_text(value) for value in values]
        median = median_value(values)
        spread = max(values) - min(values)

        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=make_prompt(stored),
            answer={
                "kind": "median_range",
                "median": rational_text(median),
                "range": rational_text(spread),
            },
            answer_display=Content(answer_text(median, spread)),
            worked_solution=(),
            marks=2 if difficulty == 1 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=4),
            parameters={"values": stored},
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in COUNTS, "Invalid difficulty")
        stored = question.parameters["values"]
        values = [Fraction(value) for value in stored]
        require(len(values) in COUNTS[level], "Unexpected data set size")
        require(len(set(values)) == len(values), "Repeated value")
        require(stored == [rational_text(value) for value in values], "Non-canonical stored data")

        lower, upper = BOUNDS[level]
        scale = 10 if level == 4 else 1
        require(all(Fraction(lower, scale) <= value <= Fraction(upper, scale) for value in values),
                "Value outside bounds")
        if level == 4:
            require(all((value * 10).denominator == 1 and value.denominator != 1
                        for value in values), "Expected values in tenths")
        else:
            require(all(value.denominator == 1 for value in values), "Expected integer data")
        if level == 1:
            require(len(values) % 2 == 1, "Expected an odd count")
        else:
            require(len(values) % 2 == 0, "Expected an even count")
        if level == 3:
            require(min(values) < 0 < max(values), "Expected both signs")

        median = median_value(values)
        spread = max(values) - min(values)
        require((median * 100).denominator == 1, "Unexpected median precision")
        require(spread > 0, "Expected a positive range")
        if level == 1:
            require(median in values, "An odd count should give a listed median")
        require(question.answer["kind"] == "median_range", "Unexpected answer kind")
        require(question.answer["median"] == rational_text(median), "Incorrect median")
        require(question.answer["range"] == rational_text(spread), "Incorrect range")
        require(question.prompt == make_prompt(stored), "Prompt mismatch")
        require(question.answer_display == Content(answer_text(median, spread)),
                "Displayed answer mismatch")
        return True

    def validate_independently(self, question):
        """Use the standard library median and SymPy extremes, not the construction."""
        import statistics

        import sympy

        values = [Fraction(value) for value in question.parameters["values"]]
        require(statistics.median(values) == Fraction(question.answer["median"]),
                "Independent median disagrees")
        rationals = [sympy.Rational(value) for value in question.parameters["values"]]
        spread = sympy.Max(*rationals) - sympy.Min(*rationals)
        require(spread == sympy.Rational(question.answer["range"]),
                "Independent range disagrees")
        return True