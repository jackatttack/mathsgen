"""Terminating fractions and decimals using exact arithmetic, two forms per level.

  1  convert (familiar denominators)   | reverse: decimal -> simplest fraction
  2  convert (hundredths/thousandths)  | order two fractions and a decimal
  3  convert (improper)                | from a mixed number
  4  convert (negative improper)       | a fraction minus a decimal, as a decimal
"""
from fractions import Fraction
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)


INFO = GeneratorInfo(
    id="number.fdp.fraction_to_decimal",
    version=2,
    topic="number",
    subtopic="fdp_conversion",
    title="Convert between fractions and decimals",
    difficulty_descriptions={
        1: "Familiar fractions to decimals, or decimals back to simplest fractions.",
        2: "Hundredths and thousandths, or order fractions and decimals.",
        3: "Improper fractions or mixed numbers to decimals.",
        4: "Negative improper fractions, or a fraction minus a decimal.",
    },
    tags=("fractions", "decimals", "conversion"),
)

# ------------------------------------------------------------ editable knobs

DENOMINATORS = {
    1: (2, 4, 5, 10),
    2: (8, 20, 25, 40, 50, 125),
    3: (4, 8, 20, 25, 40),
    4: (8, 16, 25, 40, 125),
}
FORMS = {1: ("convert", "reverse"), 2: ("convert", "order"),
         3: ("convert", "mixed"), 4: ("convert", "difference")}
ORDER_ITEMS = 3
DIFFERENCE_DECIMALS = [Fraction(n, 100) for n in range(5, 100, 5)]


# ------------------------------------------------------------ exact decimals

def terminating_decimal(value):
    """Long division without floats, rounding or a decimal context."""
    value = Fraction(value)
    numerator, denominator = abs(value.numerator), value.denominator
    whole, remainder = divmod(numerator, denominator)
    digits = []
    seen = set()
    while remainder:
        if remainder in seen:
            raise ValueError("This fraction has a recurring decimal.")
        seen.add(remainder)
        digit, remainder = divmod(remainder * 10, denominator)
        digits.append(str(digit))
    sign = "-" if value < 0 else ""
    return sign + str(whole) + ("." + "".join(digits) if digits else "")


def make_prompt(value):
    """The original convert prompt (kept for callers that build it directly)."""
    return Content(
        "Write {} as an exact decimal.".format(rational_text(value)),
        rational_tex(value),
        display_text="Write this fraction as an exact decimal.",
    )


def mixed_text(value, tex=False):
    whole, rest = divmod(value.numerator, value.denominator)
    part = Fraction(rest, value.denominator)
    if tex:
        return r"{}\frac{{{}}}{{{}}}".format(whole, part.numerator, part.denominator)
    return "{} {}".format(whole, rational_text(part))


def item_text(item, tex=False):
    style, text = item
    value = Fraction(text)
    if style == "decimal":
        return terminating_decimal(value)
    return rational_tex(value) if tex else rational_text(value)


# ------------------------------------------------------------ forms

def prompt_for(p):
    form = p["form"]
    if form == "convert":
        return make_prompt(Fraction(p["fraction"]))
    if form == "reverse":
        decimal = terminating_decimal(Fraction(p["fraction"]))
        return Content("Write {} as a fraction in its simplest form.".format(decimal))
    if form == "order":
        items = p["items"]
        return Content(
            "Write these numbers in order of size, starting with the smallest: {}.".format(
                ", ".join(item_text(item) for item in items)),
            r",\quad ".join(item_text(item, True) for item in items),
            display_text="Write these numbers in order of size, starting with the smallest.",
        )
    if form == "mixed":
        value = Fraction(p["fraction"])
        return Content("Write {} as an exact decimal.".format(mixed_text(value)),
                       mixed_text(value, True),
                       display_text="Write this mixed number as an exact decimal.")
    fraction, decimal = Fraction(p["fraction"]), Fraction(p["decimal"])
    shown = terminating_decimal(decimal)
    return Content(
        "Work out {} - {}. Give your answer as a decimal.".format(rational_text(fraction), shown),
        rational_tex(fraction) + " - " + shown,
        display_text="Work out the following. Give your answer as a decimal.",
    )


def answer_for(p):
    form = p["form"]
    if form == "reverse":
        value = Fraction(p["fraction"])
        return ({"kind": "rational", "value": rational_text(value)},
                Content(rational_text(value), rational_tex(value)))
    if form == "order":
        items = sorted(p["items"], key=lambda item: Fraction(item[1]))
        texts = [item_text(item) for item in items]
        return ({"kind": "ordered", "items": texts},
                Content(", ".join(texts), r",\quad ".join(item_text(i, True) for i in items)))
    if form == "difference":
        value = Fraction(p["fraction"]) - Fraction(p["decimal"])
    else:
        value = Fraction(p["fraction"])
    decimal = terminating_decimal(value)
    return {"kind": "decimal", "value": decimal}, Content(decimal, decimal)


def check_fraction(text, level):
    value = Fraction(text)
    require(text == rational_text(value), "Unreduced input")
    require(value.denominator in DENOMINATORS[level], "Unexpected denominator")
    return value


def check_parameters(p, level):
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(form in FORMS[level], "Unexpected form for this level")
    keys = {"convert": {"fraction"}, "reverse": {"fraction"}, "mixed": {"fraction"},
            "order": {"items"}, "difference": {"fraction", "decimal"}}[form]
    require(set(p) == keys | {"form"}, "Unexpected parameters")
    if form == "order":
        items = p["items"]
        require(isinstance(items, list) and len(items) == ORDER_ITEMS, "Expected three items")
        values = []
        for item in items:
            require(isinstance(item, list) and len(item) == 2
                    and item[0] in ("fraction", "decimal"), "Invalid item")
            value = check_fraction(item[1], level)
            require(0 < value < 1, "Items must be proper fractions")
            values.append(value)
        require(len(set(values)) == ORDER_ITEMS, "Items must differ")
        require({item[0] for item in items} == {"fraction", "decimal"},
                "Mix fractions and decimals")
        return
    value = check_fraction(p["fraction"], level)
    if form == "difference":
        require(0 < value < 1, "Expected a proper fraction")
        decimal = Fraction(p["decimal"])
        require(p["decimal"] == rational_text(decimal) and decimal in DIFFERENCE_DECIMALS,
                "Decimal outside bounds")
        require(value > decimal, "Keep the fraction larger so the answer is positive")
        places = len(terminating_decimal(value - decimal).partition(".")[2])
        require(1 <= places <= 4, "Unexpected decimal precision")
        return
    if level <= 2:
        require(0 < value < 1, "Expected a proper positive fraction")
    elif level == 3:
        require(1 < value < 5, "Expected an improper positive fraction")
    else:
        require(-5 < value < -1, "Expected a negative improper fraction")
    places = len(terminating_decimal(value).partition(".")[2])
    require(1 <= places <= (2 if level == 1 else 4), "Unexpected decimal precision")


def proper(rng, level):
    denominator = rng.choice(DENOMINATORS[level])
    numerator = rng.choice([n for n in range(1, denominator) if gcd(n, denominator) == 1])
    return Fraction(numerator, denominator)


def draw(rng, level):
    form = rng.choice(FORMS[level])
    if form == "order":
        items = [[style, rational_text(proper(rng, level))]
                 for style in ("fraction", "fraction", "decimal")]
        rng.shuffle(items)
        return {"form": form, "items": items}
    if form == "difference":
        return {"form": form, "fraction": rational_text(proper(rng, level)),
                "decimal": rational_text(rng.choice(DIFFERENCE_DECIMALS))}
    denominator = rng.choice(DENOMINATORS[level])
    candidates = range(1, denominator) if level <= 2 else range(denominator + 1, 5 * denominator)
    numerator = rng.choice([n for n in candidates if gcd(n, denominator) == 1])
    if level == 4:
        numerator = -numerator
    return {"form": form, "fraction": rational_text(Fraction(numerator, denominator))}


# ------------------------------------------------------------ generator

class FractionToDecimal:
    info = INFO

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
            raise ValueError("Could not construct a fraction-decimal question")
        answer, display = answer_for(p)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(p),
            answer=answer, answer_display=display, worked_solution=(),
            marks=1 if difficulty == 1 else 2, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=3), parameters=p,
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in DENOMINATORS, "Invalid difficulty")
        check_parameters(question.parameters, level)
        answer, display = answer_for(question.parameters)
        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Displayed answer mismatch")
        require(question.prompt == prompt_for(question.parameters), "Prompt mismatch")
        return True

    def validate_independently(self, question):
        """Compare exact symbolic rationals; re-sort orderings from the shown values."""
        import sympy

        p, answer = question.parameters, question.answer
        form = p["form"]
        if form == "order":
            shown = [item_text(item) for item in p["items"]]
            require(answer["items"] == sorted(shown, key=sympy.Rational),
                    "Independent ordering disagrees")
            return True
        expected = sympy.Rational(p["fraction"])
        if form == "difference":
            expected -= sympy.Rational(p["decimal"])
        require(expected == sympy.Rational(answer["value"]),
                "Independent conversion disagrees")
        return True