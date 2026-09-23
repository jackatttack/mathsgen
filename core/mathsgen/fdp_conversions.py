"""Convert between fractions, decimals and percentages in every direction.

The existing number.fdp.fraction_to_decimal family covers one direction.
This family covers all six, and ends with equivalent triples where two of
the three forms are missing.

Every value is an exact rational whose decimal terminates, so no question
depends on rounding. A percentage is the value multiplied by one hundred,
and a fraction is always written in its lowest terms.

Difficulty follows how familiar the value is: the common conversions a
student should know by heart, then eighths and twentieths, then values
above one and percentages containing a half, then the triple.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .rounding import decimal_text, terminates


INFO = GeneratorInfo(
    id="number.fdp.conversions", version=2,
    topic="number", subtopic="fdp_conversion",
    title="Convert between fractions, decimals and percentages",
    difficulty_descriptions={
        1: "Convert between the common equivalences.",
        2: "Convert less familiar eighths, twentieths and fiftieths.",
        3: "Convert values above one, or percentages containing a half.",
        4: "Complete an equivalent fraction, decimal and percentage.",
    },
    tags=("fractions", "decimals", "percentages", "conversion"),
)

# --- Editable value pools -------------------------------------------------
# Every value terminates as a decimal, which the validator re-checks.
VALUES = {
    1: (
        Fraction(1, 2), Fraction(1, 4), Fraction(3, 4), Fraction(1, 5),
        Fraction(2, 5), Fraction(3, 5), Fraction(4, 5), Fraction(1, 10),
        Fraction(3, 10), Fraction(7, 10), Fraction(9, 10), Fraction(1, 100),
    ),
    2: (
        Fraction(1, 8), Fraction(3, 8), Fraction(5, 8), Fraction(7, 8),
        Fraction(3, 20), Fraction(9, 20), Fraction(13, 20), Fraction(17, 20),
        Fraction(7, 25), Fraction(19, 25), Fraction(17, 50), Fraction(31, 50),
    ),
    3: (
        Fraction(5, 4), Fraction(7, 5), Fraction(9, 8), Fraction(11, 10),
        Fraction(3, 2), Fraction(13, 8), Fraction(1, 16), Fraction(3, 16),
        Fraction(5, 16), Fraction(1, 40), Fraction(7, 40), Fraction(9, 40),
    ),
    4: (
        Fraction(1, 8), Fraction(3, 8), Fraction(3, 20), Fraction(9, 20),
        Fraction(7, 25), Fraction(17, 50), Fraction(1, 4), Fraction(3, 5),
        Fraction(5, 8), Fraction(13, 20), Fraction(3, 4), Fraction(7, 10),
    ),
}

DIRECTIONS = (
    "fraction_to_decimal", "fraction_to_percentage",
    "decimal_to_fraction", "decimal_to_percentage",
    "percentage_to_fraction", "percentage_to_decimal",
)

FORM_NAMES = {
    "fraction": "fraction", "decimal": "decimal", "percentage": "percentage",
}


def fraction_text(value, tex=False):
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    if tex:
        return r"\frac{" + str(value.numerator) + "}{" + str(value.denominator) + "}"
    return "{}/{}".format(value.numerator, value.denominator)


def percentage_text(value):
    return decimal_text(Fraction(value) * 100) + "%"


def written(value, form, tex=False):
    """Write a value in one of the three forms."""
    if form == "fraction":
        return fraction_text(value, tex)
    if form == "decimal":
        return decimal_text(Fraction(value))
    return percentage_text(value)


def source_and_target(direction):
    first, _, second = direction.partition("_to_")
    return first, second


def presentation(p):
    value = Fraction(p["value"])

    if p["form"] == "triple":
        given = p["given"]
        missing = [form for form in ("fraction", "decimal", "percentage")
                   if form != given]
        instruction = (
            "A fraction, a decimal and a percentage are equivalent. "
            "The {} is {}. Write down the equivalent {} and {}."
        ).format(
            FORM_NAMES[given], written(value, given),
            FORM_NAMES[missing[0]], FORM_NAMES[missing[1]],
        )
        if "fraction" in missing:
            instruction += " Give the fraction in its simplest form."
        return Content(instruction, display_text=instruction)

    source, target = source_and_target(p["direction"])
    instruction = "Write this {} as a {}.".format(
        FORM_NAMES[source], FORM_NAMES[target]
    )
    if target == "fraction":
        instruction += " Give your answer in its simplest form."
    stated = written(value, source)
    # Always typeset the given value. The PDF shows display_text plus this
    # line, so an empty math_tex hid decimals and percentages entirely.
    if source == "fraction":
        tex = written(value, source, True)
    elif source == "percentage":
        tex = decimal_text(value * 100) + r"\%"
    else:
        tex = stated
    return Content(instruction + " " + stated, tex, display_text=instruction)


def answer_for(p):
    value = Fraction(p["value"])

    if p["form"] == "triple":
        missing = [form for form in ("fraction", "decimal", "percentage")
                   if form != p["given"]]
        answer = {
            "kind": "equivalent_forms",
            "values": {form: written(value, form) for form in missing},
        }
        display = Content("; ".join(
            "{} = {}".format(FORM_NAMES[form], written(value, form))
            for form in missing
        ))
        return answer, display

    _, target = source_and_target(p["direction"])
    answer = {"kind": "converted_value", "form": target,
              "value": written(value, target)}
    return answer, Content(
        written(value, target),
        written(value, target, True) if target == "fraction" else "",
    )


class FDPConversions:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        value = rng.choice(VALUES[difficulty])

        if difficulty == 4:
            p = {
                "form": "triple", "value": rational_text(value),
                "given": rng.choice(("fraction", "decimal", "percentage")),
            }
        else:
            p = {
                "form": "conversion", "value": rational_text(value),
                "direction": rng.choice(DIRECTIONS),
            }

        prompt = presentation(p)
        answer, display = answer_for(p)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=1 if difficulty == 1 else 2 if difficulty <= 3 else 3,
            tags=self.info.tags, layout_hint=LayoutHint(working_lines=2),
            parameters=p,
        )
        self.validate(question)
        return question

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid level")
        require(q.settings == {}, "Unsupported settings")

        p = q.parameters
        value = Fraction(p["value"])
        require(p["value"] == rational_text(value), "Non-canonical value")
        require(value > 0, "Value must be positive")
        require(terminates(value), "Value does not terminate as a decimal")
        require(value in VALUES[level], "Value outside this level's pool")

        if level == 4:
            require(p["form"] == "triple", "Level 4 states an equivalent triple")
            require(set(p) == {"form", "value", "given"}, "Unexpected parameters")
            require(p["given"] in ("fraction", "decimal", "percentage"),
                    "Unknown given form")
        else:
            require(p["form"] == "conversion", "Form does not match difficulty")
            require(set(p) == {"form", "value", "direction"},
                    "Unexpected parameters")
            require(p["direction"] in DIRECTIONS, "Unknown direction")
            source, target = source_and_target(p["direction"])
            require(source != target, "A conversion needs two different forms")

        # A fraction answer must be in lowest terms, which Fraction
        # guarantees, and the percentage must not need rounding.
        require(terminates(value * 100), "Percentage does not terminate")

        answer, display = answer_for(p)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Display mismatch")
        require(q.prompt == presentation(p), "Prompt mismatch")
        require(q.visual_assets("questions") == ()
                and q.visual_assets("answers") == (),
                "This family uses no visual assets")
        return True

    def validate_independently(self, q):
        """Rebuild the value from the written answer, by a different route.

        Each stated form is parsed back into a rational and compared with
        the original, so a wrong conversion shows up as a value that does
        not return. Parsing the text also checks the notation itself: a
        fraction that is not in lowest terms, or a decimal with the point
        misplaced, fails to return the original value.
        """
        p = q.parameters
        original = Fraction(p["value"])

        def parse(text, form):
            if form == "fraction":
                if "/" in text:
                    top, _, bottom = text.partition("/")
                    parsed = Fraction(int(top), int(bottom))
                    require(parsed == Fraction(parsed.numerator, parsed.denominator),
                            "Fraction is not in lowest terms")
                    require(int(bottom) == parsed.denominator,
                            "Fraction is not in lowest terms")
                    return parsed
                return Fraction(int(text))
            if form == "decimal":
                whole, _, decimals = text.partition(".")
                scale = 10 ** len(decimals) if decimals else 1
                digits = int(whole + decimals) if decimals else int(whole)
                return Fraction(digits, scale)
            require(text.endswith("%"), "A percentage must carry its sign")
            body = text[:-1]
            whole, _, decimals = body.partition(".")
            scale = 10 ** len(decimals) if decimals else 1
            digits = int(whole + decimals) if decimals else int(whole)
            return Fraction(digits, scale * 100)

        if p["form"] == "triple":
            for form, text in q.answer["values"].items():
                require(parse(text, form) == original,
                        "A stated form does not equal the original value")
            require(len(q.answer["values"]) == 2,
                    "Two forms should be missing")
            require(p["given"] not in q.answer["values"],
                    "The given form should not be asked for")
            return True

        _, target = source_and_target(p["direction"])
        require(parse(q.answer["value"], target) == original,
                "The converted value does not equal the original")
        return True