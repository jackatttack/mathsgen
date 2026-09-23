"""Construct missing-value questions around an exact target mean."""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


INFO = GeneratorInfo(
    id="data.mean.missing_value",
    version=1,
    topic="data",
    subtopic="mean",
    title="Find a missing value from the mean",
    difficulty_descriptions={
        1: "Positive integer observations with an integer mean.",
        2: "Positive and negative integer observations.",
        3: "Integer observations with a non-integer mean ending in .5.",
        4: "Decimal observations and a decimal mean.",
    },
    tags=("averages", "mean", "missing_value"),
)


def decimal_text(value):
    """Exact formatting for this family's integers and tenths."""
    value = Fraction(value)
    scaled = value * 10
    require(scaled.denominator == 1, "Expected an integer or exact tenth")
    number = abs(scaled.numerator)
    sign = "-" if scaled < 0 else ""
    whole, tenth = divmod(number, 10)
    return sign + str(whole) + ("." + str(tenth) if tenth else "")


def make_prompt(observations, mean):
    displayed = [
        "x" if value is None else decimal_text(Fraction(value))
        for value in observations
    ]
    return Content(
        "The mean of the numbers {} is {}. Find x.".format(
            ", ".join(displayed), decimal_text(mean)
        )
    )


class MissingMean:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        scale = 10 if difficulty == 4 else 1
        if difficulty == 1:
            count = rng.choice((4, 5))
            mean = Fraction(rng.randint(12, 24))
            lower, upper = 1, 40
        elif difficulty == 2:
            count = rng.choice((4, 5, 6))
            mean = Fraction(rng.randint(-5, 5))
            lower, upper = -25, 25
        elif difficulty == 3:
            count = rng.choice((4, 6))
            mean = Fraction(2 * rng.randint(12, 23) + 1, 2)
            lower, upper = 1, 40
        else:
            count = rng.choice((4, 5))
            mean = Fraction(rng.choice([
                value for value in range(21, 60) if value % 10
            ]), 10)
            lower, upper = 1, 80

        target_sum = mean * count * scale
        require(target_sum.denominator == 1, "Target total must fit the data precision")

        # Generate all but the balancing value, then derive that value from
        # the exact total. Reject out-of-range or unhelpfully uniform sets.
        for attempt in range(500):
            units = [rng.randint(lower, upper) for _ in range(count - 1)]
            units.append(target_sum.numerator - sum(units))
            if not lower <= units[-1] <= upper or len(set(units)) < 3:
                continue
            if difficulty == 2 and not (min(units) < 0 < max(units)):
                continue
            rng.shuffle(units)
            missing_index = rng.randrange(count)
            if difficulty == 4:
                if units[missing_index] % 10 == 0:
                    continue
                if not any(value % 10 for index, value in enumerate(units) if index != missing_index):
                    continue
            result = Fraction(units[missing_index], scale)
            observations = [
                None if index == missing_index else rational_text(Fraction(value, scale))
                for index, value in enumerate(units)
            ]
            break
        else:
            raise ValueError("Could not construct a suitable data set")

        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=make_prompt(observations, mean),
            answer={"kind": "rational", "value": rational_text(result)},
            answer_display=Content("x = " + decimal_text(result)),
            worked_solution=(),
            marks=2 if difficulty == 1 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=5),
            parameters={"observations": observations, "mean": rational_text(mean)},
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in (1, 2, 3, 4), "Invalid difficulty")
        observations = question.parameters["observations"]
        mean = Fraction(question.parameters["mean"])
        result = Fraction(question.answer["value"])
        require(observations.count(None) == 1, "Exactly one missing observation required")
        require(4 <= len(observations) <= 6, "Data set size outside bounds")
        values = [result if value is None else Fraction(value) for value in observations]
        require(len(set(values)) >= 3, "Insufficient data variation")
        require(sum(values) / len(values) == mean, "Mean does not match")
        require(question.answer["value"] == rational_text(result), "Non-canonical answer")
        if level in (1, 3):
            require(all(value.denominator == 1 and 1 <= value <= 40 for value in values),
                    "Expected positive integer data")
            require(mean.denominator == (1 if level == 1 else 2), "Mean precision mismatch")
        elif level == 2:
            require(all(value.denominator == 1 and -25 <= value <= 25 for value in values),
                    "Expected bounded integer data")
            require(min(values) < 0 < max(values), "Expected both signs")
            require(mean.denominator == 1, "Expected integer mean")
        else:
            require(all((value * 10).denominator == 1 and 0 < value <= 8 for value in values),
                    "Expected bounded decimal data")
            require(mean.denominator != 1 and result.denominator != 1,
                    "Missing decimal demand")
            require(any(value is not None and Fraction(value).denominator != 1
                        for value in observations), "Known observations need decimals")
        require(question.prompt == make_prompt(observations, mean), "Prompt mismatch")
        require(question.answer_display.text == "x = " + decimal_text(result),
                "Displayed answer mismatch")
        return True

    def validate_independently(self, question):
        import sympy

        x = sympy.Symbol("x")
        observations = question.parameters["observations"]
        total = sum(x if value is None else sympy.Rational(value) for value in observations)
        solutions = sympy.solve(
            total / len(observations) - sympy.Rational(question.parameters["mean"]), x
        )
        require(solutions == [sympy.Rational(question.answer["value"])],
                "Independent missing-mean solution disagrees")
        return True