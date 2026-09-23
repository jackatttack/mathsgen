"""Error intervals written in inequality notation.

A measurement rounded to a stated accuracy lies within half a unit of that
accuracy either side, so 8.3 to one decimal place means 8.25 <= x < 8.35.
The upper bound is strict and the lower is not, which is the part students
most often get wrong and the part this family always shows.

The existing bounds family covers upper bounds of sums and quotients; this
one covers stating the interval itself, which it does not.

Difficulty follows the accuracy stated: whole units, then decimal places,
then significant figures, then a truncated rather than rounded value.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .rounding import decimal_text


CONTEXTS = (
    ("The length of a rod", "cm"),
    ("The mass of a parcel", "kg"),
    ("The time taken", "seconds"),
    ("The capacity of a jug", "litres"),
)

# Accuracies per level, as (description, half-width of the interval).
ACCURACIES = {
    1: (("the nearest whole number", Fraction(1, 2)),
        ("the nearest 10", Fraction(5)),
        ("the nearest 100", Fraction(50))),
    2: (("1 decimal place", Fraction(1, 20)),
        ("2 decimal places", Fraction(1, 200))),
    3: (("1 significant figure", None),
        ("2 significant figures", None),
        ("3 significant figures", None)),
}


INFO = GeneratorInfo(
    id="number.bounds.error_intervals", version=1,
    topic="number", subtopic="bounds",
    title="Error intervals in inequality notation",
    difficulty_descriptions={
        1: "State the error interval for a value rounded to whole units.",
        2: "State the error interval for a value rounded to decimal places.",
        3: "State the error interval for a value rounded to significant figures.",
        4: "State the error interval for a truncated value.",
    },
    tags=("bounds", "error intervals", "inequalities", "accuracy"),
)


def significant_half_width(value, figures):
    """Half the place value of the last significant digit.

    Worked out by finding which power of ten that digit occupies, rather
    than by string manipulation, so the value stays exact.
    """
    value = Fraction(value)
    require(value > 0, "Significant figures need a positive value")
    magnitude = 0
    scaled = value
    while scaled >= 10:
        scaled /= 10
        magnitude += 1
    while scaled < 1:
        scaled *= 10
        magnitude -= 1
    place = magnitude - figures + 1
    return Fraction(10) ** place / 2


def half_width(p):
    """The distance from the stated value to each end of the interval."""
    if p["form"] == "truncated":
        # A truncated value has lost everything below its last digit, so the
        # interval runs from the value up to one whole unit above it.
        return None
    if p["accuracy_kind"] == "significant":
        return significant_half_width(Fraction(p["value"]), p["figures"])
    return Fraction(p["half_width"])


def interval_for(p):
    """The inclusive lower bound and the exclusive upper bound."""
    value = Fraction(p["value"])
    if p["form"] == "truncated":
        return value, value + Fraction(p["unit"])
    width = half_width(p)
    return value - width, value + width


def interval_text(lower, upper, tex=False):
    symbol = r"\leq" if tex else "<="
    return "{} {} x < {}".format(
        decimal_text(lower), symbol, decimal_text(upper)
    )


def presentation(p):
    context, unit = CONTEXTS[p["context"]]
    stated = decimal_text(Fraction(p["value"]))

    if p["form"] == "truncated":
        instruction = (
            "{} is {} {}, truncated to {}. Write down the error interval "
            "for the value, using x."
        ).format(context, stated, unit, p["accuracy"])
    else:
        instruction = (
            "{} is {} {}, correct to {}. Write down the error interval "
            "for the value, using x."
        ).format(context, stated, unit, p["accuracy"])
    return Content(instruction, display_text=instruction)


def answer_for(p):
    lower, upper = interval_for(p)
    answer = {
        "kind": "error_interval",
        "lower": rational_text(lower),
        "upper": rational_text(upper),
    }
    display = Content(
        interval_text(lower, upper), interval_text(lower, upper, True)
    )
    return answer, display


class ErrorIntervals:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        p = self.make_measurement(rng, difficulty)

        prompt = presentation(p)
        answer, display = answer_for(p)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=2, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=2),
            parameters=p,
        )
        self.validate(question)
        return question

    def make_measurement(self, rng, difficulty):
        context_index = rng.randrange(len(CONTEXTS))

        if difficulty == 1:
            accuracy, width = rng.choice(ACCURACIES[1])
            # The value must be a multiple of the accuracy, or it could not
            # have been the result of that rounding.
            step = int(2 * width)
            value = Fraction(step * rng.randint(2, 40))
            return {
                "form": "rounded", "accuracy_kind": "unit",
                "context": context_index, "accuracy": accuracy,
                "value": rational_text(value),
                "half_width": rational_text(width),
            }

        if difficulty == 2:
            accuracy, width = rng.choice(ACCURACIES[2])
            places = 1 if "1 decimal" in accuracy else 2
            scale = 10 ** places
            value = Fraction(rng.randint(2 * scale, 60 * scale), scale)
            return {
                "form": "rounded", "accuracy_kind": "decimal",
                "context": context_index, "accuracy": accuracy,
                "value": rational_text(value),
                "half_width": rational_text(width),
            }

        if difficulty == 3:
            accuracy, _ = rng.choice(ACCURACIES[3])
            figures = int(accuracy[0])
            # Build a value with exactly this many significant digits.
            digits = rng.randint(10 ** (figures - 1), 10 ** figures - 1)
            exponent = rng.choice((-2, -1, 0, 1))
            value = Fraction(digits) * Fraction(10) ** exponent
            return {
                "form": "rounded", "accuracy_kind": "significant",
                "context": context_index, "accuracy": accuracy,
                "figures": figures, "value": rational_text(value),
            }

        # Truncation: the interval starts at the value itself.
        unit = rng.choice((Fraction(1), Fraction(1, 10), Fraction(1, 100)))
        accuracy = {
            Fraction(1): "the nearest whole number",
            Fraction(1, 10): "1 decimal place",
            Fraction(1, 100): "2 decimal places",
        }[unit]
        steps = int(1 / unit)
        value = Fraction(rng.randint(2 * steps, 60 * steps), steps)
        return {
            "form": "truncated", "accuracy_kind": "truncated",
            "context": context_index, "accuracy": accuracy,
            "value": rational_text(value), "unit": rational_text(unit),
        }

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid level")
        require(q.settings == {}, "Unsupported settings")

        p = q.parameters
        require(p["context"] in range(len(CONTEXTS)), "Unknown context")
        value = Fraction(p["value"])
        require(p["value"] == rational_text(value), "Non-canonical value")
        require(value > 0, "Measurement must be positive")

        expected_kind = {
            1: "unit", 2: "decimal", 3: "significant", 4: "truncated",
        }[level]
        require(p["accuracy_kind"] == expected_kind,
                "Accuracy does not match difficulty")
        require(p["form"] == ("truncated" if level == 4 else "rounded"),
                "Form does not match difficulty")

        lower, upper = interval_for(p)
        require(lower < upper, "Interval must increase")
        require(lower >= 0, "A measurement cannot have a negative lower bound")

        if level == 4:
            require(lower == value, "A truncated value is its own lower bound")
        else:
            # The stated value must sit exactly at the centre of the interval.
            require(value - lower == upper - value,
                    "Rounded value should be the midpoint")

        answer, display = answer_for(p)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Display mismatch")
        require(q.prompt == presentation(p), "Prompt mismatch")
        require(q.visual_assets("questions") == ()
                and q.visual_assets("answers") == (),
                "This family uses no visual assets")
        return True

    def validate_independently(self, q):
        """Check the interval by testing what actually rounds to the value.

        Rather than reusing the half-width, this tests the endpoints
        themselves: the lower bound must round or truncate back to the
        stated value, and the upper bound must not.
        """
        import sympy

        p = q.parameters
        value = sympy.Rational(p["value"])
        lower = sympy.Rational(q.answer["lower"])
        upper = sympy.Rational(q.answer["upper"])

        if p["form"] == "truncated":
            unit = sympy.Rational(p["unit"])
            # Truncation keeps whole multiples of the unit below the value.
            require(sympy.floor(lower / unit) * unit == value,
                    "The lower bound does not truncate to the stated value")
            require(upper - lower == unit,
                    "A truncated interval spans exactly one unit")
            return True

        if p["accuracy_kind"] == "significant":
            width = significant_half_width(Fraction(p["value"]), p["figures"])
        else:
            width = Fraction(p["half_width"])
        unit = sympy.Rational(2 * width)

        # Rounding to this accuracy means dividing by the unit, rounding to
        # the nearest whole number, and multiplying back.
        def rounds_to(candidate):
            return sympy.floor(candidate / unit + sympy.Rational(1, 2)) * unit

        require(rounds_to(lower) == value,
                "The lower bound does not round to the stated value")
        require(rounds_to(upper) != value,
                "The upper bound should fall outside the interval")
        # Just inside the upper bound must still round back.
        inside = upper - unit / 1000
        require(rounds_to(inside) == value,
                "A value just below the upper bound should round back")
        return True