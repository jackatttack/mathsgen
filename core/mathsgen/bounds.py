"""Error bounds for rounded measurements, including a compound measure.

A measurement rounded to a given accuracy lies within half that accuracy of
its stated value, so every bound here is an exact rational: the stated value
plus or minus half the rounding unit. Level 4 combines two measurements,
where the upper bound of a quotient needs the greatest numerator over the
least denominator.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .rounding import (
    decimal_text, fixed_text, round_significant, significant_text,
)


# A compound bound is a quotient, which rarely terminates as a decimal, so
# its exact value is stored as a rational and displayed rounded, exactly as
# an exam question would ask.
COMPOUND_FIGURES = 3


INFO = GeneratorInfo(
    id="number.bounds.measurement",
    version=2,
    topic="number",
    subtopic="bounds",
    title="Find the bounds of a measurement",
    difficulty_descriptions={
        1: "Bounds of a single measurement rounded to the nearest whole unit.",
        2: "Bounds of a measurement rounded to a decimal place.",
        3: "Bounds of the sum or difference of two measurements.",
        4: "Bounds of a speed or density calculated from two measurements.",
    },
    tags=("bounds", "accuracy", "measurement", "compound_measures"),
)

# Each accuracy is the rounding unit, so the bound is half of it.
ACCURACIES = {
    1: (Fraction(1), Fraction(10), Fraction(100)),
    2: (Fraction(1, 10), Fraction(1, 100)),
    3: (Fraction(1), Fraction(1, 10)),
    4: (Fraction(1), Fraction(1, 10)),
}

ACCURACY_NAMES = {
    Fraction(100): "the nearest 100",
    Fraction(10): "the nearest 10",
    Fraction(1): "the nearest whole number",
    Fraction(1, 10): "1 decimal place",
    Fraction(1, 100): "2 decimal places",
}

QUANTITIES = {
    "length": ("cm", "The length of a rod"),
    "mass": ("g", "The mass of a block"),
    "distance": ("m", "The distance travelled"),
    "time": ("s", "The time taken"),
    "volume": ("cm³", "The volume of a block"),
}

COMPOUND = {
    "speed": {
        "top": "distance", "bottom": "time", "unit": "m/s",
        "question": "Calculate the upper bound of the average speed.",
    },
    "density": {
        "top": "mass", "bottom": "volume", "unit": "g/cm³",
        "question": "Calculate the upper bound of the density.",
    },
}


def half_unit(accuracy):
    return Fraction(accuracy, 2)


def lower_bound(value, accuracy):
    return Fraction(value) - half_unit(accuracy)


def upper_bound(value, accuracy):
    return Fraction(value) + half_unit(accuracy)


def measurement_text(value, unit, accuracy):
    """State a measurement at its stated accuracy.

    A value of 4 measured to 1 decimal place is written 4.0, because the
    trailing zero is what conveys the accuracy to the reader.
    """
    places = 0
    unit_size = Fraction(accuracy)
    while unit_size < 1:
        unit_size *= 10
        places += 1
    return "{} {}, correct to {}".format(
        fixed_text(Fraction(value), places), unit, ACCURACY_NAMES[accuracy]
    )


def single_prompt(value, unit, accuracy, description):
    return Content(
        "{} is {}. Write down the lower bound and the upper bound.".format(
            description, measurement_text(value, unit, accuracy)
        )
    )


def combined_prompt(values, units, accuracies, descriptions, operation):
    parts = [
        "{} is {}".format(description, measurement_text(value, unit, accuracy))
        for description, value, unit, accuracy
        in zip(descriptions, values, units, accuracies)
    ]
    wording = "sum" if operation == "sum" else "difference"
    return Content(
        "{}. Find the upper bound of the {} of the two measurements.".format(
            ". ".join(parts), wording
        )
    )


def compound_prompt(values, units, accuracies, descriptions, measure):
    parts = [
        "{} is {}".format(description, measurement_text(value, unit, accuracy))
        for description, value, unit, accuracy
        in zip(descriptions, values, units, accuracies)
    ]
    return Content(
        ". ".join(parts) + ". " + COMPOUND[measure]["question"]
        + " Give your answer to {} significant figures.".format(COMPOUND_FIGURES)
    )


def compound_answer_text(upper, unit):
    rounded = round_significant(upper, COMPOUND_FIGURES)
    return "upper bound = {} {}".format(
        significant_text(rounded, COMPOUND_FIGURES), unit
    )


def answer_text(lower, upper, unit):
    if lower is None:
        return "upper bound = {} {}".format(decimal_text(upper), unit)
    return "lower bound = {} {}, upper bound = {} {}".format(
        decimal_text(lower), unit, decimal_text(upper), unit
    )


class MeasurementBounds:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        accuracy = rng.choice(ACCURACIES[difficulty])

        if difficulty <= 2:
            quantity = rng.choice(("length", "mass"))
            unit, description = QUANTITIES[quantity]
            steps = rng.randint(3, 60)
            value = accuracy * steps
            lower = lower_bound(value, accuracy)
            upper = upper_bound(value, accuracy)
            parameters = {
                "values": [decimal_text(value)],
                "accuracies": [decimal_text(accuracy)],
                "quantities": [quantity],
            }
            prompt = single_prompt(value, unit, accuracy, description)
            display = answer_text(lower, upper, unit)
            answer = {
                "kind": "bounds",
                "lower": decimal_text(lower),
                "upper": decimal_text(upper),
                "unit": unit,
            }
        elif difficulty == 3:
            quantity = rng.choice(("length", "mass"))
            unit, description = QUANTITIES[quantity]
            operation = rng.choice(("sum", "difference"))
            first = accuracy * rng.randint(20, 90)
            second = accuracy * rng.randint(3, 19)
            values = [first, second]
            accuracies = [accuracy, accuracy]
            descriptions = ["The first measurement", "The second measurement"]
            if operation == "sum":
                upper = upper_bound(first, accuracy) + upper_bound(second, accuracy)
            else:
                # The greatest difference takes the largest first value and
                # the smallest second value.
                upper = upper_bound(first, accuracy) - lower_bound(second, accuracy)
            lower = None
            parameters = {
                "values": [decimal_text(value) for value in values],
                "accuracies": [decimal_text(item) for item in accuracies],
                "quantities": [quantity, quantity],
                "operation": operation,
            }
            prompt = combined_prompt(values, [unit, unit], accuracies, descriptions, operation)
            display = answer_text(None, upper, unit)
            answer = {"kind": "bound", "upper": decimal_text(upper), "unit": unit}
        else:
            measure = rng.choice(tuple(COMPOUND))
            top_quantity = COMPOUND[measure]["top"]
            bottom_quantity = COMPOUND[measure]["bottom"]
            top_unit, top_description = QUANTITIES[top_quantity]
            bottom_unit, bottom_description = QUANTITIES[bottom_quantity]
            second_accuracy = rng.choice(ACCURACIES[4])
            # Keep the result physically plausible: a speed a person or
            # vehicle could have, a density near that of a real material.
            # An absurd value distracts from the method being tested.
            plausible = (
                (Fraction(1), Fraction(30)) if measure == "speed"
                else (Fraction(1), Fraction(20))
            )
            for attempt in range(500):
                top = accuracy * rng.randint(40, 200)
                bottom = second_accuracy * rng.randint(5, 40)
                if bottom <= half_unit(second_accuracy):
                    continue
                upper = upper_bound(top, accuracy) / lower_bound(bottom, second_accuracy)
                if plausible[0] <= upper <= plausible[1]:
                    break
            else:
                raise ValueError("Could not construct a plausible compound measure")
            lower = None
            parameters = {
                "values": [decimal_text(top), decimal_text(bottom)],
                "accuracies": [decimal_text(accuracy), decimal_text(second_accuracy)],
                "quantities": [top_quantity, bottom_quantity],
                "measure": measure,
            }
            prompt = compound_prompt(
                [top, bottom], [top_unit, bottom_unit],
                [accuracy, second_accuracy],
                [top_description, bottom_description], measure,
            )
            unit = COMPOUND[measure]["unit"]
            display = compound_answer_text(upper, unit)
            answer = {
                "kind": "bound_rounded",
                "upper": rational_text(upper),
                "rounded": rational_text(round_significant(upper, COMPOUND_FIGURES)),
                "figures": COMPOUND_FIGURES,
                "unit": unit,
            }

        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=prompt,
            answer=answer,
            answer_display=Content(display),
            worked_solution=(),
            marks=2 if difficulty <= 2 else (3 if difficulty == 3 else 4),
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=4 if difficulty <= 2 else 7),
            parameters=parameters,
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in ACCURACIES, "Invalid difficulty")
        values = [Fraction(value) for value in question.parameters["values"]]
        accuracies = [Fraction(value) for value in question.parameters["accuracies"]]
        quantities = question.parameters["quantities"]
        require(len(values) == len(accuracies) == len(quantities) == (1 if level <= 2 else 2),
                "Unexpected measurement count")
        require(all(value > 0 for value in values), "Expected positive measurements")
        require(all(quantity in QUANTITIES for quantity in quantities), "Unknown quantity")
        for value, accuracy in zip(values, accuracies):
            require(accuracy in ACCURACY_NAMES, "Unexpected accuracy")
            require(accuracy in ACCURACIES[level], "Accuracy outside difficulty rules")
            require((value / accuracy).denominator == 1,
                    "A measurement must be a whole number of rounding units")
            require(value > half_unit(accuracy),
                    "The lower bound must stay positive")

        if level <= 2:
            unit, description = QUANTITIES[quantities[0]]
            lower = lower_bound(values[0], accuracies[0])
            upper = upper_bound(values[0], accuracies[0])
            require(question.answer["kind"] == "bounds", "Unexpected answer kind")
            require(question.answer["lower"] == decimal_text(lower), "Incorrect lower bound")
            require(question.answer["upper"] == decimal_text(upper), "Incorrect upper bound")
            require(upper - lower == accuracies[0], "Bound width must equal the accuracy")
            expected_prompt = single_prompt(values[0], unit, accuracies[0], description)
            expected_display = answer_text(lower, upper, unit)
        elif level == 3:
            operation = question.parameters["operation"]
            require(operation in ("sum", "difference"), "Unknown operation")
            require(accuracies[0] == accuracies[1], "Expected a shared accuracy")
            require(values[0] > values[1], "Expected a positive difference")
            unit, _ = QUANTITIES[quantities[0]]
            if operation == "sum":
                upper = upper_bound(values[0], accuracies[0]) + upper_bound(values[1], accuracies[1])
            else:
                upper = upper_bound(values[0], accuracies[0]) - lower_bound(values[1], accuracies[1])
            require(question.answer["kind"] == "bound", "Unexpected answer kind")
            require(question.answer["upper"] == decimal_text(upper), "Incorrect upper bound")
            expected_prompt = combined_prompt(
                values, [unit, unit], accuracies,
                ["The first measurement", "The second measurement"], operation,
            )
            expected_display = answer_text(None, upper, unit)
        else:
            measure = question.parameters["measure"]
            require(measure in COMPOUND, "Unknown compound measure")
            require(quantities[0] == COMPOUND[measure]["top"], "Unexpected numerator quantity")
            require(quantities[1] == COMPOUND[measure]["bottom"], "Unexpected denominator quantity")
            upper = upper_bound(values[0], accuracies[0]) / lower_bound(values[1], accuracies[1])
            require(question.answer["kind"] == "bound_rounded", "Unexpected answer kind")
            require(question.answer["upper"] == rational_text(upper),
                    "Incorrect exact upper bound")
            require(question.answer["figures"] == COMPOUND_FIGURES,
                    "Unexpected rounding accuracy")
            require(question.answer["rounded"]
                    == rational_text(round_significant(upper, COMPOUND_FIGURES)),
                    "Incorrect rounded upper bound")
            limit = Fraction(30) if measure == "speed" else Fraction(20)
            require(1 <= upper <= limit,
                    "Compound result is not a physically plausible value")
            unit = COMPOUND[measure]["unit"]
            top_unit, top_description = QUANTITIES[quantities[0]]
            bottom_unit, bottom_description = QUANTITIES[quantities[1]]
            expected_prompt = compound_prompt(
                values, [top_unit, bottom_unit], accuracies,
                [top_description, bottom_description], measure,
            )
            expected_display = compound_answer_text(upper, unit)

        require(question.answer["unit"] == unit, "Unexpected unit")
        require(question.prompt == expected_prompt, "Prompt mismatch")
        require(question.answer_display == Content(expected_display),
                "Displayed answer mismatch")
        return True

    def validate_independently(self, question):
        """Search the bound interval numerically instead of reusing the formulae.

        Sampling the extremes of each interval and taking the greatest result
        confirms which combination actually maximises the quantity, rather
        than trusting the rule that a quotient needs the least denominator.
        """
        import sympy

        values = [sympy.Rational(value) for value in question.parameters["values"]]
        accuracies = [sympy.Rational(value) for value in question.parameters["accuracies"]]
        intervals = [
            (value - accuracy / 2, value + accuracy / 2)
            for value, accuracy in zip(values, accuracies)
        ]
        level = question.difficulty

        if level <= 2:
            require(sympy.Rational(question.answer["lower"]) == intervals[0][0],
                    "Independent lower bound disagrees")
            candidates = [intervals[0][1]]
        elif level == 3:
            operation = question.parameters["operation"]
            candidates = [
                first + second if operation == "sum" else first - second
                for first in intervals[0] for second in intervals[1]
            ]
        else:
            require(intervals[1][0] > 0, "Independent denominator interval includes zero")
            candidates = [
                first / second for first in intervals[0] for second in intervals[1]
            ]

        require(sympy.Rational(question.answer["upper"]) == max(candidates),
                "Independent upper bound disagrees")
        if question.answer["kind"] == "bound_rounded":
            figures = question.answer["figures"]
            exact = max(candidates)
            rounded = sympy.Rational(question.answer["rounded"])
            # The rounded answer must be the closest value at this accuracy,
            # so nothing nearer to the exact bound can exist on that scale.
            scale = sympy.Integer(10) ** (figures - 1 - sympy.floor(sympy.log(exact, 10)))
            require(rounded * scale == sympy.floor(rounded * scale),
                    "Rounded answer is not at the stated accuracy")
            require(abs(exact - rounded) <= sympy.Rational(1, 2) / scale,
                    "Rounded answer is not the nearest value at this accuracy")
        return True