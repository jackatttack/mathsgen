"""Area and volume unit conversion, where the length factor is squared or cubed.

The intended misconception is applying the length factor once: a student who
converts 3 m to 300 cm and then claims 3 m-squared is 300 cm-squared has used
100 rather than 100 squared.

Levels 1 to 3 apply a squared or cubed length factor. Level 4 changes the
knowledge required rather than the arithmetic: capacity units relate to
volume by 1 litre = 1000 cubic centimetres, which is not a power of a length
factor at all. Reversing a conversion is deliberately NOT used as a level,
because the relationship is symmetric and a reversed prompt is the same task.

All conversions use exact integer factors, so every answer is exact.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .rounding import decimal_text


# --- Editable unit table --------------------------------------------------
# Each entry states the larger unit, the smaller unit, and how many of the
# smaller lengths make one larger length. The area and volume factors are
# this number squared and cubed, which is the whole point of the topic.
LENGTH_STEPS = {
    "m_cm": ("m", "cm", 100),
    "cm_mm": ("cm", "mm", 10),
}

AREA_STEPS = ("m_cm", "cm_mm")
VOLUME_STEPS = ("m_cm", "cm_mm")

DIMENSION_NAMES = {2: "area", 3: "volume"}

# --- Capacity relationships (level 4) -------------------------------------
# Each case states the unit the question gives, the unit the answer needs,
# and the exact multiplier from the first to the second.
CAPACITY_CASES = {
    "cm3_to_litres": (("cm", 3), ("litres", 0), Fraction(1, 1000)),
    "litres_to_cm3": (("litres", 0), ("cm", 3), Fraction(1000)),
    "m3_to_litres": (("m", 3), ("litres", 0), Fraction(1000)),
    "litres_to_m3": (("litres", 0), ("m", 3), Fraction(1, 1000)),
}


INFO = GeneratorInfo(
    id="number.units.area_volume", version=2,
    topic="number", subtopic="unit_conversion",
    title="Convert area, volume and capacity units",
    difficulty_descriptions={
        1: "Convert an area to a smaller unit.",
        2: "Convert an area to a larger unit.",
        3: "Convert a volume, where the factor is cubed.",
        4: "Convert between volume and capacity units.",
    },
    tags=("units", "conversion", "area", "volume", "capacity", "exact"),
)


def unit_text(unit, dimension, tex=False):
    """Write a unit, using a plain word when it carries no dimension."""
    if dimension == 0:
        return unit
    if tex:
        return unit + "^{" + str(dimension) + "}"
    # Real superscript characters render in PDF prose and the CLI alike.
    return unit + {2: "²", 3: "³"}[dimension]


def quantity_text(value, unit, dimension, tex=False):
    """Write a quantity as a decimal, since a measurement is not a fraction."""
    return "{} {}".format(decimal_text(Fraction(value)), unit_text(unit, dimension, tex))


def factor_for(parameters):
    """The exact multiplier between the two units at this dimension."""
    step = LENGTH_STEPS[parameters["step"]]
    return Fraction(step[2]) ** parameters["dimension"]


def units_for(parameters):
    """Return the source and destination units in the stated direction."""
    larger, smaller, _ = LENGTH_STEPS[parameters["step"]]
    if parameters["direction"] == "to_smaller":
        return larger, smaller
    return smaller, larger


def presentation(parameters):
    value = Fraction(parameters["value"])

    if parameters["form"] == "capacity":
        (source, source_dimension), (destination, destination_dimension), _ = (
            CAPACITY_CASES[parameters["case"]]
        )
        instruction = (
            "A container holds {}. Write this in {}."
        ).format(
            quantity_text(value, source, source_dimension),
            unit_text(destination, destination_dimension),
        )
        return Content(instruction, display_text=instruction)

    source, destination = units_for(parameters)
    dimension = parameters["dimension"]
    name = DIMENSION_NAMES[dimension]
    instruction = (
        "A shape has {} {} of {}. Convert this {} to {}."
    ).format(
        "an" if name[0] in "aeiou" else "a", name,
        quantity_text(value, source, dimension),
        name, unit_text(destination, dimension),
    )
    return Content(instruction, display_text=instruction)


def answer_for(parameters):
    value = Fraction(parameters["value"])

    if parameters["form"] == "capacity":
        _, (unit, dimension), multiplier = CAPACITY_CASES[parameters["case"]]
        result = value * multiplier
    else:
        _, destination = units_for(parameters)
        dimension = parameters["dimension"]
        factor = factor_for(parameters)
        # More of a smaller unit fits into the same shape, so multiply going
        # down and divide going up.
        result = (value * factor if parameters["direction"] == "to_smaller"
                  else value / factor)
        unit = destination

    answer = {
        "kind": "converted_quantity",
        "value": rational_text(result),
        "unit": unit,
        "dimension": dimension,
    }
    display = Content(
        quantity_text(result, unit, dimension),
        quantity_text(result, unit, dimension, True),
    )
    return answer, display


def terminating(value):
    """Whether an exact rational can be written as a finite decimal."""
    denominator = Fraction(value).denominator
    for prime in (2, 5):
        while denominator % prime == 0:
            denominator //= prime
    return denominator == 1


class AreaVolumeConversion:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        parameters = (self.make_capacity(rng) if difficulty == 4
                      else self.make_power(rng, difficulty))

        prompt = presentation(parameters)
        answer, display = answer_for(parameters)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=2 if difficulty <= 2 else 3, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=3),
            parameters=parameters,
        )
        self.validate(question)
        return question

    def make_power(self, rng, difficulty):
        dimension = 3 if difficulty == 3 else 2
        steps = VOLUME_STEPS if dimension == 3 else AREA_STEPS
        step = rng.choice(steps)

        if difficulty == 1:
            direction = "to_smaller"
        elif difficulty == 2:
            direction = "to_larger"
        else:
            direction = rng.choice(("to_smaller", "to_larger"))

        if direction == "to_smaller":
            value = Fraction(rng.choice((
                Fraction(rng.randint(2, 40)),
                Fraction(rng.randint(5, 95), 10),
            )))
        else:
            # Start from a whole number of the larger unit, so the answer is
            # a sensible quantity rather than a long decimal.
            factor = Fraction(LENGTH_STEPS[step][2]) ** dimension
            value = factor * rng.randint(2, 40)

        return {
            "form": "power", "step": step, "dimension": dimension,
            "direction": direction, "value": rational_text(value),
        }

    def make_capacity(self, rng):
        """Choose a capacity case and a value that converts to an exact decimal."""
        case = rng.choice(sorted(CAPACITY_CASES))
        if case == "cm3_to_litres":
            value = Fraction(500 * rng.randint(3, 40))
        elif case == "litres_to_cm3":
            value = Fraction(rng.randint(5, 95), 10)
        elif case == "m3_to_litres":
            value = Fraction(rng.randint(5, 95), 100)
        else:
            value = Fraction(50 * rng.randint(2, 40))
        return {"form": "capacity", "case": case, "value": rational_text(value)}

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")

        parameters = question.parameters
        form = "capacity" if level == 4 else "power"
        require(parameters.get("form") == form, "Form does not match difficulty")

        if form == "capacity":
            require(set(parameters) == {"form", "case", "value"},
                    "Unexpected parameters")
            require(parameters["case"] in CAPACITY_CASES, "Unknown capacity case")
        else:
            require(set(parameters) == {
                "form", "step", "dimension", "direction", "value",
            }, "Unexpected parameters")
            require(parameters["step"] in LENGTH_STEPS, "Unknown unit step")
            require(parameters["direction"] in ("to_smaller", "to_larger"),
                    "Unknown direction")
            dimension = parameters["dimension"]
            require(dimension == (3 if level == 3 else 2),
                    "Dimension does not match difficulty")
            require(parameters["step"] in (
                VOLUME_STEPS if dimension == 3 else AREA_STEPS
            ), "Unit step not available at this dimension")
            if level == 1:
                require(parameters["direction"] == "to_smaller",
                        "Expected a downward conversion")
            elif level == 2:
                require(parameters["direction"] == "to_larger",
                        "Expected an upward conversion")

        value = Fraction(parameters["value"])
        require(parameters["value"] == rational_text(value), "Non-canonical value")
        require(value > 0, "Quantity must be positive")

        answer, display = answer_for(parameters)
        result = Fraction(answer["value"])
        require(result > 0, "Converted quantity must be positive")
        # Both the stated quantity and the answer must be sensible to write
        # down: exact, and not an awkward recurring decimal.
        for quantity in (value, result):
            require(terminating(quantity), "Quantity is not an exact decimal")
        require(result.numerator <= 10 ** 9, "Converted quantity is too large")

        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Display mismatch")
        require(question.prompt == presentation(parameters), "Prompt mismatch")
        require(question.visual_assets("questions") == ()
                and question.visual_assets("answers") == (),
                "This family uses no visual assets")
        return True

    def validate_independently(self, question):
        """Convert through a common base rather than reusing the stored factor."""
        import sympy

        parameters = question.parameters
        stated = sympy.Rational(parameters["value"])
        submitted = sympy.Rational(question.answer["value"])

        if parameters["form"] == "capacity":
            # Express both sides in cubic centimetres, the shared base unit.
            in_cubic_centimetres = {
                ("cm", 3): sympy.Integer(1),
                ("litres", 0): sympy.Integer(1000),
                ("m", 3): sympy.Integer(1000000),
            }
            source, destination, _ = CAPACITY_CASES[parameters["case"]]
            expected_base = stated * in_cubic_centimetres[source]
            submitted_base = submitted * in_cubic_centimetres[destination]
            require(sympy.simplify(submitted_base - expected_base) == 0,
                    "Independent capacity conversion disagrees")
            require((question.answer["unit"], question.answer["dimension"])
                    == destination, "Independent unit disagrees")
            return True

        larger, smaller, length_factor = LENGTH_STEPS[parameters["step"]]
        dimension = parameters["dimension"]

        # Apply the length factor once per dimension rather than using a
        # precomputed area or volume factor.
        factor = sympy.Integer(1)
        for _ in range(dimension):
            factor *= sympy.Integer(length_factor)

        if parameters["direction"] == "to_smaller":
            expected, expected_unit = stated * factor, smaller
        else:
            expected, expected_unit = stated / factor, larger

        require(sympy.simplify(submitted - expected) == 0,
                "Independent conversion disagrees")
        require(question.answer["unit"] == expected_unit,
                "Independent unit disagrees")
        require(question.answer["dimension"] == dimension,
                "Independent dimension disagrees")
        return True