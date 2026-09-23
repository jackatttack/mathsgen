"""Mixed numbers: converting both ways, then the four operations.

A mixed number is stored as a whole part and a proper fraction, never as a
float, and every answer is returned in lowest terms as a mixed number when
it is improper.

Difficulty follows the process: converting between forms, then adding and
subtracting over a common denominator, then over different denominators,
then multiplying and dividing, which require converting to improper
fractions first.

Subtractions are constructed to give a positive result, and the harder ones
deliberately require borrowing from the whole part, which is where students
most often go wrong.

The independent check inverts the operation rather than repeating it: an
addition is verified by subtracting one part back off the answer, and a
multiplication by dividing. This needs no symbolic algebra, so the family
stays fast at bulk-check sizes.
"""
from fractions import Fraction
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


INFO = GeneratorInfo(
    id="number.fractions.mixed_numbers", version=2,
    topic="number", subtopic="fraction_operations",
    title="Mixed numbers and improper fractions",
    difficulty_descriptions={
        1: "Convert between mixed numbers and improper fractions.",
        2: "Add or subtract with the same denominator; or distances and ribbon.",
        3: "Add or subtract with different denominators; or distances and ribbon.",
        4: "Multiply or divide mixed numbers; or paint coverage.",
    },
    tags=("fractions", "mixed numbers", "improper fractions", "arithmetic"),
)

# The division sign is written out rather than as a slash: "4 1/2 / 1 1/2"
# cannot be read, because the slash already separates numerator from
# denominator. Multiplication uses the same reasoning over a bare "x",
# which would be mistaken for the unknown.
OPERATION_SYMBOLS = {
    "add": ("+", "+"),
    "subtract": ("-", "-"),
    "multiply": ("\u00d7", r"\times"),
    "divide": ("\u00f7", r"\div"),
}


def to_mixed(value):
    """Split a positive rational into a whole part and a proper fraction."""
    value = Fraction(value)
    require(value >= 0, "This family uses positive quantities only")
    whole = value.numerator // value.denominator
    remainder = value - whole
    return whole, remainder.numerator, remainder.denominator


def mixed_text(value, tex=False):
    """Write a rational as a mixed number, or plainly when it is not one."""
    whole, numerator, denominator = to_mixed(value)
    if numerator == 0:
        return str(whole)
    fraction = (
        r"\frac{" + str(numerator) + "}{" + str(denominator) + "}" if tex
        else "{}/{}".format(numerator, denominator)
    )
    if whole == 0:
        return fraction
    return "{} {}".format(whole, fraction) if not tex else str(whole) + fraction


def improper_text(value, tex=False):
    value = Fraction(value)
    if tex:
        return r"\frac{" + str(value.numerator) + "}{" + str(value.denominator) + "}"
    return "{}/{}".format(value.numerator, value.denominator)


def operate(first, second, operation):
    if operation == "add":
        return first + second
    if operation == "subtract":
        return first - second
    if operation == "multiply":
        return first * second
    return first / second


def presentation(p):
    form = p["form"]

    if form == "to_improper":
        value = Fraction(p["value"])
        instruction = "Write this mixed number as an improper fraction."
        return Content(
            instruction + " " + mixed_text(value),
            mixed_text(value, True), display_text=instruction,
        )

    if form == "to_mixed":
        value = Fraction(p["value"])
        instruction = "Write this improper fraction as a mixed number."
        return Content(
            instruction + " " + improper_text(value),
            improper_text(value, True), display_text=instruction,
        )

    first = Fraction(p["first"])
    second = Fraction(p["second"])
    symbol, tex_symbol = OPERATION_SYMBOLS[p["operation"]]
    # The answer is sometimes a whole number, so the instruction asks for
    # the simplest form rather than promising a mixed number.
    instruction = (
        "Work out the following. Give your answer in its simplest form."
    )
    plain = "{} {} {}".format(mixed_text(first), symbol, mixed_text(second))
    maths = "{} {} {}".format(
        mixed_text(first, True), tex_symbol, mixed_text(second, True)
    )
    return Content(instruction + " " + plain, maths, display_text=instruction)


def answer_value(p):
    if p["form"] == "to_improper":
        return Fraction(p["value"])
    if p["form"] == "to_mixed":
        return Fraction(p["value"])
    return operate(Fraction(p["first"]), Fraction(p["second"]), p["operation"])


def answer_for(p):
    value = answer_value(p)
    form = p["form"]

    if form == "to_improper":
        answer = {"kind": "improper_fraction", "value": rational_text(value)}
        return answer, Content(improper_text(value), improper_text(value, True))

    answer = {"kind": "mixed_number", "value": rational_text(value)}
    return answer, Content(mixed_text(value), mixed_text(value, True))


class MixedNumbers:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        from . import fraction_contexts as worded_forms
        if rng.random() < worded_forms.CONTEXT_SHARE.get(difficulty, 0.0):
            return worded_forms.generate(self, context)

        if difficulty == 1:
            whole = rng.randint(1, 6)
            denominator = rng.choice((2, 3, 4, 5, 6, 8))
            numerator = rng.choice([
                value for value in range(1, denominator)
                if gcd(value, denominator) == 1
            ])
            value = whole + Fraction(numerator, denominator)
            p = {
                "form": rng.choice(("to_improper", "to_mixed")),
                "value": rational_text(value),
            }
        elif difficulty in (2, 3):
            p = self.make_sum(rng, difficulty)
        else:
            p = self.make_product(rng)

        prompt = presentation(p)
        answer, display = answer_for(p)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=2 if difficulty <= 2 else 3, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=4),
            parameters=p,
        )
        self.validate(question)
        return question

    def make_sum(self, rng, difficulty):
        """An addition or subtraction with a positive mixed-number answer."""
        for attempt in range(300):
            operation = rng.choice(("add", "subtract"))
            if difficulty == 2:
                denominator = rng.choice((3, 4, 5, 6, 8))
                denominators = (denominator, denominator)
            else:
                denominators = rng.choice((
                    (2, 3), (3, 4), (4, 6), (2, 5), (3, 5), (4, 5), (6, 8),
                ))
            # Numerators coprime with their denominator, so Fraction does
            # not silently reduce 2/4 to 1/2 and change the denominator the
            # question actually displays.
            numerators = [
                rng.choice([
                    value for value in range(1, bottom)
                    if gcd(value, bottom) == 1
                ])
                for bottom in denominators
            ]
            first = rng.randint(1, 5) + Fraction(numerators[0], denominators[0])
            second = rng.randint(1, 4) + Fraction(numerators[1], denominators[1])
            if operation == "subtract" and first <= second:
                continue
            result = operate(first, second, operation)
            if result <= 0 or result > 12:
                continue
            # A subtraction is only worth setting if it needs borrowing or
            # at least does not resolve part by part trivially.
            if operation == "subtract" and difficulty == 3:
                if (first - int(first)) >= (second - int(second)):
                    continue
            return {
                "form": "operation", "operation": operation,
                "first": rational_text(first), "second": rational_text(second),
            }
        raise ValueError("Could not construct a suitable sum")

    def make_product(self, rng):
        """A multiplication or division with a manageable exact answer."""
        for attempt in range(300):
            operation = rng.choice(("multiply", "divide"))
            first_denominator = rng.choice((2, 3, 4, 5))
            second_denominator = rng.choice((2, 3, 4, 5))
            first = rng.randint(1, 4) + Fraction(
                rng.randint(1, first_denominator - 1), first_denominator
            )
            second = rng.randint(1, 3) + Fraction(
                rng.randint(1, second_denominator - 1), second_denominator
            )
            result = operate(first, second, operation)
            if result <= 0 or result > 20:
                continue
            if result.denominator > 24:
                continue
            return {
                "form": "operation", "operation": operation,
                "first": rational_text(first), "second": rational_text(second),
            }
        raise ValueError("Could not construct a suitable product")

    def validate(self, q):
        from .worded import is_worded
        if is_worded(q):
            from .fraction_contexts import validate as validate_worded
            return validate_worded(self, q)
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid level")
        require(q.settings == {}, "Unsupported settings")

        p = q.parameters
        if level == 1:
            require(p["form"] in ("to_improper", "to_mixed"),
                    "Level 1 converts between forms")
            require(set(p) == {"form", "value"}, "Unexpected parameters")
            value = Fraction(p["value"])
            require(p["value"] == rational_text(value), "Non-canonical value")
            require(value > 1, "A conversion needs a whole part")
            require(value.denominator > 1, "A conversion needs a fraction part")
            require(value.denominator <= 8, "Denominator outside bounds")
        else:
            require(p["form"] == "operation", "Form does not match difficulty")
            require(set(p) == {"form", "operation", "first", "second"},
                    "Unexpected parameters")
            expected = {
                2: ("add", "subtract"), 3: ("add", "subtract"),
                4: ("multiply", "divide"),
            }[level]
            require(p["operation"] in expected,
                    "Operation does not match difficulty")

            first = Fraction(p["first"])
            second = Fraction(p["second"])
            for value, text in ((first, p["first"]), (second, p["second"])):
                require(text == rational_text(value), "Non-canonical operand")
                require(value > 1, "Both operands should be mixed numbers")
                require(value.denominator > 1, "Operands need a fraction part")

            if level == 2:
                require(first.denominator == second.denominator,
                        "Level 2 uses a common denominator")
            elif level == 3:
                require(first.denominator != second.denominator,
                        "Level 3 uses different denominators")

            result = answer_value(p)
            require(result > 0, "The answer must be positive")
            require(result <= 20, "The answer is outside bounds")

        answer, display = answer_for(p)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Display mismatch")
        require(q.prompt == presentation(p), "Prompt mismatch")
        require(q.visual_assets("questions") == ()
                and q.visual_assets("answers") == (),
                "This family uses no visual assets")
        return True

    def validate_independently(self, q):
        """Invert the operation rather than repeating it.

        An addition is checked by subtracting one operand back off the
        answer, a multiplication by dividing. A conversion is checked by
        rebuilding the value from the whole and fractional parts the answer
        would be written with. None of this repeats the forward arithmetic,
        and it needs no symbolic algebra, so the check stays fast.
        """
        from .worded import is_worded
        if is_worded(q):
            from .fraction_contexts import validate_independently as independent_worded
            return independent_worded(self, q)
        p = q.parameters
        stated = Fraction(q.answer["value"])

        if p["form"] in ("to_improper", "to_mixed"):
            original = Fraction(p["value"])
            require(stated == original, "The converted value changed")
            # Rebuild from the parts the student would write.
            whole, numerator, denominator = to_mixed(stated)
            rebuilt = whole + Fraction(numerator, denominator)
            require(rebuilt == original, "Mixed-number parts do not rebuild")
            require(numerator < denominator,
                    "The fractional part is not proper")
            require(gcd(numerator, denominator) == 1,
                    "The fractional part is not in lowest terms")
            return True

        first = Fraction(p["first"])
        second = Fraction(p["second"])
        operation = p["operation"]

        if operation == "add":
            require(stated - second == first,
                    "Subtracting the second operand does not recover the first")
        elif operation == "subtract":
            require(stated + second == first,
                    "Adding the second operand does not recover the first")
        elif operation == "multiply":
            require(second != 0 and stated / second == first,
                    "Dividing by the second operand does not recover the first")
        else:
            require(stated * second == first,
                    "Multiplying by the second operand does not recover the first")

        whole, numerator, denominator = to_mixed(stated)
        if numerator:
            require(gcd(numerator, denominator) == 1,
                    "The answer is not in lowest terms")
            require(numerator < denominator, "The answer is not proper")
        return True