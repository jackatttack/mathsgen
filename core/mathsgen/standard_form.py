"""Standard form conversion built from exact significant digits and powers of ten.

Both directions (write in standard form / write as an ordinary number) share
one class and the same forms, two per level:
  1  convert (large)           | context (a large quantity in a sentence)
  2  convert (small)           | context (a small quantity in a sentence)
  3  convert (internal zero)   | non_standard (e.g. 40.5 x 10^3, the common slip)
  4  convert (four s.f.)       | order (mixed standard and ordinary numbers)
Numbers are digit strings and integer exponents throughout; no floats.
"""
from fractions import Fraction

from .core import Content, GeneratorInfo, LayoutHint, Question, make_context, require


# ------------------------------------------------------------ editable knobs

# Allowed standard-form exponents per difficulty level. Level 3 and level 4
# each offer both directions so place value must be read, not assumed.
EXPONENT_RANGES = {
    1: ((3, 6),),
    2: ((-5, -2),),
    3: ((-5, -2), (3, 6)),
    4: ((-8, -6), (7, 9)),
}
FORMS = {1: ("convert", "context"), 2: ("convert", "context"),
         3: ("convert", "non_standard"), 4: ("convert", "order")}
SHIFTS = (-2, -1, 1, 2)          # how far a non-standard mantissa is off
ORDER_ITEMS = 4
ORDER_EXPONENTS = (-5, 6)

# (sentence containing the value, sentence pointing to the value shown below,
#  lowest and highest realistic power of ten for that quantity)
LARGE_CONTEXTS = (
    ("A reservoir holds {} litres of water.",
     "The number of litres of water in a reservoir is shown below.", 5, 6),
    ("A city has a population of {}.",
     "The population of a city is shown below.", 4, 6),
    ("A satellite travels {} km in a year.",
     "The distance, in km, that a satellite travels in a year is shown below.", 5, 6),
    ("A factory makes {} bottles a year.",
     "The number of bottles a factory makes in a year is shown below.", 3, 6),
)
SMALL_CONTEXTS = (
    ("The width of a bacterium is {} mm.",
     "The width of a bacterium, in millimetres, is shown below.", -4, -3),
    ("The mass of a grain of sand is {} g.",
     "The mass of a grain of sand, in grams, is shown below.", -4, -2),
    ("The length of a virus is {} mm.",
     "The length of a virus, in millimetres, is shown below.", -5, -4),
    ("A dust particle has a diameter of {} mm.",
     "The diameter of a dust particle, in millimetres, is shown below.", -4, -2),
)
GROUP_FROM_DIGITS = 5   # integer parts this long are spaced in threes

ANSWER_KINDS = {"from_decimal": "standard_form", "to_decimal": "decimal"}


# ------------------------------------------------------------ exact place value

def make_digits(rng, difficulty):
    """Significant digits with no leading or trailing zero, so the mantissa is canonical."""
    if difficulty <= 2:
        length = rng.choice((2, 3))
        return "".join(str(rng.randint(1, 9)) for _ in range(length))
    if difficulty == 3:
        return str(rng.randint(1, 9)) + "0" + str(rng.randint(1, 9))
    # One internal zero is the common case; a double zero is deliberately
    # rarer because it produces a single repetitive d00d shape.
    spare = str(rng.randint(1, 9))
    middle = rng.choice(("0" + spare, spare + "0", "0" + spare, spare + "0", "00"))
    return str(rng.randint(1, 9)) + middle + str(rng.randint(1, 9))


def ordinary_text(digits, exponent):
    """Shift the digit string by place value, without floats or a decimal context."""
    shift = exponent - (len(digits) - 1)
    if shift >= 0:
        return digits + "0" * shift
    places = -shift
    if places >= len(digits):
        return "0." + "0" * (places - len(digits)) + digits
    return digits[:len(digits) - places] + "." + digits[len(digits) - places:]


def standard_form_text(digits, exponent, tex=False):
    mantissa = digits[0] + ("." + digits[1:] if len(digits) > 1 else "")
    return shown_text(mantissa, exponent, tex)


def shown_text(mantissa, exponent, tex=False):
    if tex:
        return mantissa + r" \times 10^{" + str(exponent) + "}"
    return mantissa + " × 10^" + str(exponent)


def exact_value(digits, exponent):
    """The number itself, as an exact rational product of a power of ten."""
    return Fraction(int(digits)) * Fraction(10) ** (exponent - len(digits) + 1)


def mantissa_value(digits):
    return Fraction(int(digits), 10 ** (len(digits) - 1))


def grouped(text):
    """UK exam style: space long integer parts in threes (20 060 000)."""
    whole, _, rest = text.partition(".")
    if len(whole) < GROUP_FROM_DIGITS:
        return text
    head = len(whole) % 3 or 3
    parts = [whole[:head]] + [whole[i:i + 3] for i in range(head, len(whole), 3)]
    return " ".join(parts) + ("." + rest if rest else "")


def parse_number(text):
    """Read a displayed number back: plain (possibly spaced) decimal, or 'm × 10^e'."""
    if "×" in text:
        mantissa, power = text.split("× 10^")
        return Fraction(mantissa.strip()) * Fraction(10) ** int(power)
    return Fraction(text.replace(" ", ""))


# ------------------------------------------------------------ forms

def item_text(item, tex=False):
    digits, exponent, style = item
    if style == "standard":
        return standard_form_text(digits, exponent, tex)
    return grouped(ordinary_text(digits, exponent))


def ordered_items(items):
    return sorted(items, key=lambda item: exact_value(item[0], item[1]))


def make_prompt(p, direction):
    form = p["form"]
    if form == "order":
        items = p["items"]
        text = "Write these numbers in order of size, starting with the smallest: {}.".format(
            ", ".join(item_text(item) for item in items))
        tex = r",\quad ".join(item_text(item, True) for item in items)
        return Content(text, tex, display_text=(
            "Write these numbers in order of size, starting with the smallest."))
    digits, exponent = p["digits"], p["exponent"]
    if form == "non_standard":
        mantissa = ordinary_text(digits, p["shift"])
        shown = exponent - p["shift"]
        if direction == "from_decimal":
            lead = "This number is not in standard form. Write it in standard form."
            text = "{} is not in standard form. Write it in standard form.".format(
                shown_text(mantissa, shown))
        else:
            lead = "Write this number as an ordinary number."
            text = "Write {} as an ordinary number.".format(shown_text(mantissa, shown))
        return Content(text, shown_text(mantissa, shown, True), display_text=lead)
    if form == "context":
        with_value, pointing = (LARGE_CONTEXTS if exponent > 0 else SMALL_CONTEXTS)[
            p["context"]][:2]
        if direction == "from_decimal":
            return Content(with_value.format(grouped(ordinary_text(digits, exponent)))
                           + " Write this number in standard form.")
        lead = pointing + " Write this as an ordinary number."
        return Content(with_value.format(standard_form_text(digits, exponent))
                       + " Write this as an ordinary number.",
                       standard_form_text(digits, exponent, True), display_text=lead)
    if direction == "from_decimal":
        return Content("Write {} in standard form.".format(
            grouped(ordinary_text(digits, exponent))))
    return Content(
        "Write {} as an ordinary number.".format(standard_form_text(digits, exponent)),
        standard_form_text(digits, exponent, True),
        display_text="Write this number as an ordinary number.",
    )


def answer_for(p, direction):
    if p["form"] == "order":
        items = ordered_items(p["items"])
        answer = {"kind": "ordered", "items": [item_text(item) for item in items]}
        return answer, Content(", ".join(answer["items"]),
                               r",\quad ".join(item_text(item, True) for item in items))
    digits, exponent = p["digits"], p["exponent"]
    if direction == "from_decimal":
        return ({"kind": "standard_form", "digits": digits, "exponent": exponent},
                Content(standard_form_text(digits, exponent),
                        standard_form_text(digits, exponent, True)))
    ordinary = ordinary_text(digits, exponent)
    spaced = grouped(ordinary)
    return {"kind": "decimal", "value": ordinary}, Content(spaced, spaced)


def check_digits(digits, exponent, level):
    require(type(digits) is str and digits.isdigit(), "Significant digits must be text digits")
    require(type(exponent) is int, "Exponent must be an integer")
    require(digits[0] != "0" and digits[-1] != "0", "Mantissa is not canonical")
    require(any(low <= exponent <= high for low, high in EXPONENT_RANGES[level]),
            "Exponent outside level bounds")
    if level <= 2:
        require(len(digits) in (2, 3), "Expected two or three significant figures")
        require("0" not in digits, "Unexpected zero digit")
    elif level == 3:
        require(len(digits) == 3 and digits[1] == "0", "Expected a single internal zero")
    else:
        require(len(digits) == 4, "Expected four significant figures")
        require("0" in digits[1:3], "Expected an internal zero")
    value = exact_value(digits, exponent)
    require(value > 0 and Fraction(ordinary_text(digits, exponent)) == value,
            "Place-value shift disagrees with the power of ten")
    require(1 <= mantissa_value(digits) < 10, "Mantissa outside standard form")


def check_parameters(p, level):
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(form in FORMS[level], "Unexpected form for this level")
    if form == "order":
        require(set(p) == {"form", "items"}, "Unexpected parameters")
        items = p["items"]
        require(isinstance(items, list) and len(items) == ORDER_ITEMS, "Expected four items")
        for item in items:
            require(isinstance(item, list) and len(item) == 3, "Invalid item")
            digits, exponent, style = item
            require(type(digits) is str and digits.isdigit() and len(digits) in (2, 3)
                    and "0" not in digits, "Item digits outside bounds")
            require(type(exponent) is int
                    and ORDER_EXPONENTS[0] <= exponent <= ORDER_EXPONENTS[1],
                    "Item exponent outside bounds")
            require(style in ("standard", "ordinary"), "Invalid item style")
        values = [exact_value(d, e) for d, e, _ in items]
        require(len(set(values)) == ORDER_ITEMS, "Items must differ in value")
        styles = {style for _, _, style in items}
        require(styles == {"standard", "ordinary"}, "Mix standard and ordinary numbers")
        require(len({d for d, _, _ in items}) < ORDER_ITEMS,
                "Include two items with the same digits")
        return
    keys = {"form", "digits", "exponent"}
    if form == "context":
        keys.add("context")
    if form == "non_standard":
        keys.add("shift")
    require(set(p) == keys, "Unexpected parameters")
    check_digits(p["digits"], p["exponent"], level)
    if form == "context":
        contexts = LARGE_CONTEXTS if p["exponent"] > 0 else SMALL_CONTEXTS
        require(type(p["context"]) is int and 0 <= p["context"] < len(contexts),
                "Invalid context")
        low, high = contexts[p["context"]][2:]
        require(low <= p["exponent"] <= high, "Unrealistic size for this context")
    if form == "non_standard":
        require(p["shift"] in SHIFTS, "Invalid non-standard shift")


def draw(rng, level):
    form = rng.choice(FORMS[level])
    if form == "order":
        base = "".join(str(rng.randint(1, 9)) for _ in range(rng.choice((2, 3))))
        first, second = rng.sample(range(ORDER_EXPONENTS[0], ORDER_EXPONENTS[1] + 1), 2)
        items = [[base, first, "standard"], [base, second, "ordinary"]]
        while len(items) < ORDER_ITEMS:
            digits = "".join(str(rng.randint(1, 9)) for _ in range(rng.choice((2, 3))))
            exponent = rng.randint(*ORDER_EXPONENTS)
            items.append([digits, exponent, rng.choice(("standard", "ordinary"))])
        rng.shuffle(items)
        return {"form": form, "items": items}
    digits = make_digits(rng, level)
    low, high = rng.choice(EXPONENT_RANGES[level])
    p = {"form": form, "digits": digits, "exponent": rng.randint(low, high)}
    if form == "context":
        # Pick the context first, then a power of ten that is realistic for it.
        contexts = LARGE_CONTEXTS if low > 0 else SMALL_CONTEXTS
        p["context"] = rng.randrange(len(contexts))
        context_low, context_high = contexts[p["context"]][2:]
        p["exponent"] = rng.randint(max(low, context_low), min(high, context_high))
    if form == "non_standard":
        p["shift"] = rng.choice(SHIFTS)
    return p


# ------------------------------------------------------------ generators

class StandardFormQuestion:
    """Shared exact place-value construction; each direction is registered separately."""

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        for attempt in range(200):
            p = draw(rng, difficulty)
            try:
                check_parameters(p, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a standard-form question")
        answer, display = answer_for(p, self.direction)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=make_prompt(p, self.direction),
            answer=answer, answer_display=display, worked_solution=(),
            marks=1 if difficulty <= 2 else 2, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=3), parameters=p,
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in EXPONENT_RANGES, "Invalid difficulty")
        p = question.parameters
        check_parameters(p, level)
        answer, display = answer_for(p, self.direction)
        require(question.answer == answer, "Incorrect answer")
        require(question.prompt == make_prompt(p, self.direction), "Prompt mismatch")
        require(question.answer_display == display, "Displayed answer mismatch")
        return True

    def validate_independently(self, question):
        """Recover the exponent from the definition; read displayed numbers back."""
        import sympy

        p = question.parameters
        if p["form"] == "order":
            shown = [item_text(item) for item in p["items"]]
            expected = sorted(shown, key=parse_number)
            require(question.answer["items"] == expected, "Independent ordering disagrees")
            return True
        digits, exponent = p["digits"], p["exponent"]
        value = sympy.Rational(ordinary_text(digits, exponent))
        require(value > 0, "Independent value is not positive")
        mantissa, derived = value, 0
        while mantissa >= 10:
            mantissa /= 10
            derived += 1
        while mantissa < 1:
            mantissa *= 10
            derived -= 1
        require(derived == exponent, "Independent exponent disagrees")
        require(mantissa == sympy.Rational(int(digits), 10 ** (len(digits) - 1)),
                "Independent mantissa disagrees")
        if p["form"] == "non_standard":
            shown = sympy.Rational(ordinary_text(digits, p["shift"]))
            shown *= sympy.Integer(10) ** (exponent - p["shift"])
            require(shown == value, "The non-standard number is a different value")
        if self.direction == "from_decimal":
            submitted = question.answer["digits"]
            answer_value = sympy.Rational(int(submitted), 10 ** (len(submitted) - 1))
            answer_value *= sympy.Integer(10) ** question.answer["exponent"]
        else:
            answer_value = sympy.Rational(question.answer["value"])
        require(answer_value == value, "Independent answer value disagrees")
        return True


class WriteInStandardForm(StandardFormQuestion):
    direction = "from_decimal"
    info = GeneratorInfo(
        id="number.standard_form.from_decimal", version=3, topic="number",
        subtopic="standard_form", title="Write a number in standard form",
        difficulty_descriptions={
            1: "Large numbers, bare or in a context.",
            2: "Small numbers needing a negative power, bare or in a context.",
            3: "Internal zeros, or correct a number that is not in standard form.",
            4: "Four significant figures, or order mixed standard and ordinary numbers.",
        },
        tags=("standard_form", "indices", "place_value"),
    )


class WriteAsOrdinaryNumber(StandardFormQuestion):
    direction = "to_decimal"
    info = GeneratorInfo(
        id="number.standard_form.to_decimal", version=3, topic="number",
        subtopic="standard_form", title="Write a standard-form number as an ordinary number",
        difficulty_descriptions={
            1: "Positive powers, bare or in a context.",
            2: "Negative powers needing leading zeros, bare or in a context.",
            3: "Internal zeros, or a number written with a non-standard mantissa.",
            4: "Four significant figures, or order mixed standard and ordinary numbers.",
        },
        tags=("standard_form", "indices", "place_value"),
    )