"""Speed, density and pressure: the three compound measures and their rearrangements.

Each measure is one quantity divided by another, so a single formula table
drives all three and difficulty changes what the question asks rather than
which measure appears. Level 1 finds the compound measure, level 2 rearranges
for one of the two base quantities, level 3 requires a unit conversion before
or after the calculation, and level 4 is a two-stage journey where the average
speed is total distance over total time, not the average of two speeds.

That last point is the intended misconception: averaging two speeds gives a
different answer whenever the two stages take different times.

All values are exact rationals and every displayed quantity terminates as a
decimal, so no question needs rounding.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .rounding import decimal_text, terminates


# --- The three measures ---------------------------------------------------
# Each entry names the compound quantity, the quantity divided, the quantity
# divided by, and the unit each is stated in. The relationship is always
# compound = numerator / denominator.
MEASURES = {
    "speed": {
        "compound": ("speed", "km/h"),
        "numerator": ("distance", "km"),
        "denominator": ("time", "hours"),
        "subject": "a car",
    },
    "density": {
        "compound": ("density", "g/cm³"),
        "numerator": ("mass", "g"),
        "denominator": ("volume", "cm³"),
        "subject": "a block of metal",
    },
    "pressure": {
        "compound": ("pressure", "N/m²"),
        "numerator": ("force", "N"),
        "denominator": ("area", "m²"),
        "subject": "a crate resting on the floor",
    },
}

# --- Editable difficulty bounds -------------------------------------------
DENOMINATORS = {
    "speed": (2, 3, 4, 5, 6, 8),
    "density": (2, 4, 5, 8, 10, 20),
    "pressure": (2, 4, 5, 6, 8, 10),
}

COMPOUND_VALUES = {
    "speed": (30, 40, 45, 50, 60, 70, 80, 90),
    "density": (Fraction(2), Fraction(5), Fraction(8), Fraction(15, 2),
                Fraction(19, 2), Fraction(27, 4)),
    "pressure": (25, 40, 50, 75, 120, 150, 200),
}

# Level 3 conversions. Each states the quantity affected, how it is written
# in the question, and the exact multiplier that converts it to the unit the
# formula expects.
CONVERSIONS = {
    "speed_minutes": {
        "measure": "speed", "quantity": "denominator",
        "stated_unit": "minutes", "multiplier": Fraction(1, 60),
    },
    "speed_metres": {
        "measure": "speed", "quantity": "numerator",
        "stated_unit": "m", "multiplier": Fraction(1, 1000),
    },
    "density_kilograms": {
        "measure": "density", "quantity": "numerator",
        "stated_unit": "kg", "multiplier": Fraction(1000),
    },
    "pressure_centimetres": {
        "measure": "pressure", "quantity": "denominator",
        "stated_unit": "cm²", "multiplier": Fraction(1, 10000),
    },
}

STAGE_SPEEDS = (30, 40, 45, 50, 60, 70, 80, 90)
STAGE_TIMES = (Fraction(1), Fraction(2), Fraction(3), Fraction(1, 2),
               Fraction(3, 2), Fraction(5, 2))


INFO = GeneratorInfo(
    id="ratio.compound_measures.rates", version=2,
    topic="ratio", subtopic="compound_measures",
    title="Speed, density and pressure",
    difficulty_descriptions={
        1: "Find a speed, density or pressure from the two quantities given.",
        2: "Rearrange the formula to find one of the two base quantities.",
        3: "Convert a unit before or after calculating.",
        4: "Find the average speed of a journey made in two stages.",
    },
    tags=("compound measures", "speed", "density", "pressure", "rates", "exact"),
)


def quantity(value, unit):
    """Write an exact value with its unit, as a decimal rather than a fraction."""
    return "{} {}".format(decimal_text(Fraction(value)), unit)


def article(word):
    """The indefinite article for a following word, by its first letter."""
    return "an" if word[0] in "aeiou" else "a"


def stage_text(index):
    return ("first", "second")[index]


# Speed needs its own sentences: a car travels a distance and takes a time,
# it does not "have" them. Density and pressure read correctly with the
# generic possessive template, so only speed is special-cased here.
PRESSURE_SENTENCES = {
    "compound": (
        "A crate exerts a force of {numerator} on a floor area of "
        "{denominator}. Find the pressure."
    ),
    "find_numerator": (
        "A crate rests on a floor area of {denominator}, exerting a pressure "
        "of {compound}. Find the force."
    ),
    "find_denominator": (
        "A crate exerts a force of {numerator} and a pressure of {compound}. "
        "Find the area it rests on."
    ),
    "convert": (
        "A crate exerts a force of {numerator} on a floor area of "
        "{denominator}. Find the pressure in {compound_unit}."
    ),
}

SPEED_SENTENCES = {
    "compound": "A car travels {numerator} in {denominator}. Find its average speed.",
    "find_numerator": (
        "A car travels for {denominator} at an average speed of {compound}. "
        "Find the distance travelled."
    ),
    "find_denominator": (
        "A car travels {numerator} at an average speed of {compound}. "
        "Find the time taken."
    ),
    "convert": (
        "A car travels {numerator} in {denominator}. "
        "Find its average speed in {compound_unit}."
    ),
}


def presentation(parameters):
    form = parameters["form"]

    if form == "average_speed":
        pieces = []
        for index, (speed, time) in enumerate(zip(
            parameters["speeds"], parameters["times"]
        )):
            pieces.append(
                "the {} stage at {} for {}".format(
                    stage_text(index),
                    quantity(Fraction(speed), "km/h"),
                    quantity(Fraction(time), "hours"),
                )
            )
        return Content(
            "A journey is made in two stages: {} and {}. "
            "Find the average speed for the whole journey.".format(*pieces)
        )

    measure = MEASURES[parameters["measure"]]
    compound_name, compound_unit = measure["compound"]
    numerator_name, numerator_unit = measure["numerator"]
    denominator_name, denominator_unit = measure["denominator"]

    # Density is the only measure a subject genuinely "has", so it keeps the
    # generic possessive template; speed and pressure have their own.
    sentences = {
        "speed": SPEED_SENTENCES, "pressure": PRESSURE_SENTENCES,
    }.get(parameters["measure"])
    is_speed = sentences is not None

    if form == "convert":
        conversion = CONVERSIONS[parameters["conversion"]]
        stated_unit = conversion["stated_unit"]
        if conversion["quantity"] == "numerator":
            numerator_unit = stated_unit
        else:
            denominator_unit = stated_unit
        numerator_written = quantity(Fraction(parameters["numerator"]), numerator_unit)
        denominator_written = quantity(
            Fraction(parameters["denominator"]), denominator_unit
        )
        if is_speed:
            return Content(sentences["convert"].format(
                numerator=numerator_written, denominator=denominator_written,
                compound_unit=compound_unit,
            ))
        return Content(
            "{} has {} {} of {} and {} {} of {}. Find its {} in {}.".format(
                measure["subject"].capitalize(),
                article(numerator_name), numerator_name, numerator_written,
                article(denominator_name), denominator_name, denominator_written,
                compound_name, compound_unit,
            )
        )

    if form == "compound":
        numerator_written = quantity(Fraction(parameters["numerator"]), numerator_unit)
        denominator_written = quantity(
            Fraction(parameters["denominator"]), denominator_unit
        )
        if is_speed:
            return Content(sentences["compound"].format(
                numerator=numerator_written, denominator=denominator_written,
            ))
        return Content(
            "{} has {} {} of {} and {} {} of {}. Find its {}.".format(
                measure["subject"].capitalize(),
                article(numerator_name), numerator_name, numerator_written,
                article(denominator_name), denominator_name, denominator_written,
                compound_name,
            )
        )

    # Rearranged: the compound measure and one base quantity are given.
    if parameters["unknown"] == "numerator":
        known_name, known_unit = denominator_name, denominator_unit
        known = parameters["denominator"]
        wanted = numerator_name
    else:
        known_name, known_unit = numerator_name, numerator_unit
        known = parameters["numerator"]
        wanted = denominator_name

    if is_speed:
        sentence = sentences[
            "find_numerator" if parameters["unknown"] == "numerator"
            else "find_denominator"
        ]
        return Content(sentence.format(
            compound=quantity(Fraction(parameters["compound"]), compound_unit),
            numerator=quantity(Fraction(parameters["numerator"]), numerator_unit),
            denominator=quantity(Fraction(parameters["denominator"]), denominator_unit),
        ))

    return Content(
        "{} has {} {} of {} and {} {} of {}. Find its {}.".format(
            measure["subject"].capitalize(),
            article(compound_name), compound_name,
            quantity(Fraction(parameters["compound"]), compound_unit),
            article(known_name), known_name, quantity(Fraction(known), known_unit),
            wanted,
        )
    )


def answer_for(parameters):
    form = parameters["form"]

    if form == "average_speed":
        distance = sum(
            Fraction(speed) * Fraction(time)
            for speed, time in zip(parameters["speeds"], parameters["times"])
        )
        total_time = sum(Fraction(time) for time in parameters["times"])
        value, unit = distance / total_time, "km/h"
    else:
        measure = MEASURES[parameters["measure"]]
        if form == "compound":
            value = Fraction(parameters["numerator"]) / Fraction(
                parameters["denominator"]
            )
            unit = measure["compound"][1]
        elif form == "convert":
            conversion = CONVERSIONS[parameters["conversion"]]
            numerator = Fraction(parameters["numerator"])
            denominator = Fraction(parameters["denominator"])
            # Convert the stated quantity into the unit the formula expects.
            if conversion["quantity"] == "numerator":
                numerator *= conversion["multiplier"]
            else:
                denominator *= conversion["multiplier"]
            value = numerator / denominator
            unit = measure["compound"][1]
        elif parameters["unknown"] == "numerator":
            value = Fraction(parameters["compound"]) * Fraction(
                parameters["denominator"]
            )
            unit = measure["numerator"][1]
        else:
            value = Fraction(parameters["numerator"]) / Fraction(
                parameters["compound"]
            )
            unit = measure["denominator"][1]

    answer = {
        "kind": "measured_quantity",
        "value": rational_text(value),
        "unit": unit,
    }
    return answer, Content(quantity(value, unit))


class CompoundMeasures:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        builders = {
            1: self.make_compound, 2: self.make_rearranged,
            3: self.make_conversion, 4: self.make_average_speed,
        }
        parameters = builders[difficulty](rng)

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

    def make_compound(self, rng):
        """Build from the answer outwards, so the result is a sensible value."""
        measure = rng.choice(sorted(MEASURES))
        compound = Fraction(rng.choice(COMPOUND_VALUES[measure]))
        denominator = Fraction(rng.choice(DENOMINATORS[measure]))
        return {
            "form": "compound", "measure": measure,
            "numerator": rational_text(compound * denominator),
            "denominator": rational_text(denominator),
        }

    def make_rearranged(self, rng):
        measure = rng.choice(sorted(MEASURES))
        compound = Fraction(rng.choice(COMPOUND_VALUES[measure]))
        denominator = Fraction(rng.choice(DENOMINATORS[measure]))
        return {
            "form": "rearranged", "measure": measure,
            "unknown": rng.choice(("numerator", "denominator")),
            "compound": rational_text(compound),
            "numerator": rational_text(compound * denominator),
            "denominator": rational_text(denominator),
        }

    def make_conversion(self, rng):
        for attempt in range(200):
            name = rng.choice(sorted(CONVERSIONS))
            conversion = CONVERSIONS[name]
            measure = conversion["measure"]
            compound = Fraction(rng.choice(COMPOUND_VALUES[measure]))
            denominator = Fraction(rng.choice(DENOMINATORS[measure]))
            numerator = compound * denominator

            # Undo the conversion to find the value as the question states it.
            if conversion["quantity"] == "numerator":
                numerator = numerator / conversion["multiplier"]
            else:
                denominator = denominator / conversion["multiplier"]

            if not (terminates(numerator) and terminates(denominator)):
                continue
            if numerator <= 0 or denominator <= 0:
                continue
            return {
                "form": "convert", "measure": measure, "conversion": name,
                "numerator": rational_text(numerator),
                "denominator": rational_text(denominator),
            }
        raise ValueError("Could not construct a suitable conversion question")

    def make_average_speed(self, rng):
        """Two stages with different speeds, so averaging the speeds is wrong."""
        for attempt in range(200):
            speeds = rng.sample(STAGE_SPEEDS, 2)
            times = [rng.choice(STAGE_TIMES), rng.choice(STAGE_TIMES)]

            # Test the average before building the question: an average that
            # does not terminate cannot be displayed as an exact decimal, and
            # total distance over total time often recurs with these times.
            distance = sum(Fraction(speed) * time
                           for speed, time in zip(speeds, times))
            average = distance / sum(times)
            naive = (Fraction(speeds[0]) + Fraction(speeds[1])) / 2
            # The whole point of the question is that these differ.
            if average == naive or not terminates(average):
                continue

            return {
                "form": "average_speed",
                "speeds": [rational_text(Fraction(value)) for value in speeds],
                "times": [rational_text(value) for value in times],
            }
        raise ValueError("Could not construct a suitable journey")

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")

        parameters = question.parameters
        expected_form = {1: "compound", 2: "rearranged",
                         3: "convert", 4: "average_speed"}[level]
        require(parameters.get("form") == expected_form,
                "Form does not match difficulty")

        self.check_structure(parameters, level)

        answer, display = answer_for(parameters)
        value = Fraction(answer["value"])
        require(value > 0, "Answer must be positive")
        require(terminates(value), "Answer is not an exact decimal")
        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Display mismatch")
        require(question.prompt == presentation(parameters), "Prompt mismatch")
        require(question.visual_assets("questions") == ()
                and question.visual_assets("answers") == (),
                "This family uses no visual assets")
        return True

    def check_structure(self, parameters, level):
        if level == 4:
            require(set(parameters) == {"form", "speeds", "times"},
                    "Unexpected parameters")
            speeds = [Fraction(value) for value in parameters["speeds"]]
            times = [Fraction(value) for value in parameters["times"]]
            require(len(speeds) == 2 and len(times) == 2, "Expected two stages")
            require(speeds[0] != speeds[1],
                    "Two equal speeds make the average trivial")
            require(all(value > 0 for value in speeds + times),
                    "Stage values must be positive")
            require(all(value in [Fraction(v) for v in STAGE_SPEEDS]
                        for value in speeds), "Speed outside difficulty bounds")
            require(all(value in STAGE_TIMES for value in times),
                    "Time outside difficulty bounds")

            answer, _ = answer_for(parameters)
            naive = (speeds[0] + speeds[1]) / 2
            require(Fraction(answer["value"]) != naive,
                    "Average speed coincides with the average of the speeds")
            return

        measure = parameters.get("measure")
        require(measure in MEASURES, "Unknown measure")

        if level == 3:
            require(set(parameters) == {
                "form", "measure", "conversion", "numerator", "denominator",
            }, "Unexpected parameters")
            name = parameters["conversion"]
            require(name in CONVERSIONS, "Unknown conversion")
            require(CONVERSIONS[name]["measure"] == measure,
                    "Conversion does not belong to this measure")
        elif level == 2:
            require(set(parameters) == {
                "form", "measure", "unknown", "compound", "numerator", "denominator",
            }, "Unexpected parameters")
            require(parameters["unknown"] in ("numerator", "denominator"),
                    "Unknown quantity not recognised")
            # The three stated values must be consistent with each other.
            compound = Fraction(parameters["compound"])
            numerator = Fraction(parameters["numerator"])
            denominator = Fraction(parameters["denominator"])
            require(numerator == compound * denominator,
                    "Stated quantities are inconsistent")
        else:
            require(set(parameters) == {
                "form", "measure", "numerator", "denominator",
            }, "Unexpected parameters")

        for name in ("numerator", "denominator"):
            value = Fraction(parameters[name])
            require(parameters[name] == rational_text(value),
                    "Non-canonical quantity")
            require(value > 0, "Quantity must be positive")
            require(terminates(value), "Quantity is not an exact decimal")

    def validate_independently(self, question):
        """Rebuild the relationship from its definition rather than reusing it."""
        import sympy

        parameters = question.parameters
        submitted = sympy.Rational(question.answer["value"])

        if parameters["form"] == "average_speed":
            speeds = [sympy.Rational(value) for value in parameters["speeds"]]
            times = [sympy.Rational(value) for value in parameters["times"]]
            # Average speed is total distance over total time, by definition.
            total_distance = sum(speed * time for speed, time in zip(speeds, times))
            total_time = sum(times)
            require(sympy.simplify(submitted - total_distance / total_time) == 0,
                    "Independent average speed disagrees")
            require(question.answer["unit"] == "km/h", "Independent unit disagrees")
            return True

        measure = MEASURES[parameters["measure"]]
        numerator = sympy.Rational(parameters["numerator"])
        denominator = sympy.Rational(parameters["denominator"])

        if parameters["form"] == "convert":
            conversion = CONVERSIONS[parameters["conversion"]]
            multiplier = sympy.Rational(conversion["multiplier"])
            if conversion["quantity"] == "numerator":
                numerator *= multiplier
            else:
                denominator *= multiplier

        if parameters["form"] == "rearranged":
            compound = sympy.Rational(parameters["compound"])
            # Check the stated trio satisfies the defining relationship, then
            # confirm the submitted value is the quantity actually asked for.
            require(sympy.simplify(compound * denominator - numerator) == 0,
                    "Stated quantities do not satisfy the relationship")
            if parameters["unknown"] == "numerator":
                expected, unit = numerator, measure["numerator"][1]
            else:
                expected, unit = denominator, measure["denominator"][1]
        else:
            expected = numerator / denominator
            unit = measure["compound"][1]

        require(sympy.simplify(submitted - expected) == 0,
                "Independent compound measure disagrees")
        require(question.answer["unit"] == unit, "Independent unit disagrees")
        return True