"""Round to decimal places or significant figures using exact digit strings.

Values are held as an integer of significant digits plus a decimal exponent,
so every rounding decision is made on digits rather than on a float. Halfway
cases are constructed deliberately at the harder levels, since rounding half
up is exactly where students go wrong.

Both generators have two forms per level:
  1  round | context (a measured quantity)
  2  round | calculate (a product or quotient, then round)
  3  round | two_accuracies (one number, two roundings)
  4  round | share (money to the nearest penny; decimal places)
             fraction (a fraction to significant figures)
The helpers above the classes (decimal_text, round_half_up, ...) are used
across the project and keep their names and behaviour.
"""
from fractions import Fraction
from math import gcd

from .core import Content, GeneratorInfo, LayoutHint, Question, make_context, require
from .standard_form import grouped


DECIMAL_PLACES = "decimal_places"
SIGNIFICANT_FIGURES = "significant_figures"


# ------------------------------------------------------------ shared exact helpers

def decimal_text(value):
    """Exact plain text for a rational with a terminating decimal."""
    value = Fraction(value)
    negative = value < 0
    value = abs(value)
    whole = value.numerator // value.denominator
    remainder = value - whole
    digits = ""
    while remainder:
        remainder *= 10
        digit = remainder.numerator // remainder.denominator
        digits += str(digit)
        remainder -= digit
        require(len(digits) <= 12, "Decimal does not terminate within bounds")
    return ("-" if negative else "") + str(whole) + ("." + digits if digits else "")


def terminates(value):
    """Whether a rational has a terminating decimal expansion.

    Only denominators built from 2s and 5s terminate, so anything else
    cannot be written exactly as a decimal and must be rounded instead.
    """
    denominator = Fraction(value).denominator
    for prime in (2, 5):
        while denominator % prime == 0:
            denominator //= prime
    return denominator == 1


def round_half_up(value, places):
    """Round to a number of decimal places, halves going away from zero.

    The magnitude is rounded and the sign restored afterwards, so -3.15 to
    one decimal place gives -3.2. Rounding the signed value directly would
    instead give -3.1, because floor division carries halves towards
    positive infinity. Away from zero is the convention taught at GCSE and
    the one the independent decimal check applies.
    """
    value = Fraction(value)
    sign = -1 if value < 0 else 1
    scale = Fraction(10) ** places
    scaled = abs(value) * scale
    whole = scaled.numerator // scaled.denominator
    if scaled - whole >= Fraction(1, 2):
        whole += 1
    return sign * Fraction(whole, 1) / scale


def significant_exponent(value):
    """The power of ten of the leading significant digit."""
    value = abs(Fraction(value))
    require(value != 0, "Zero has no significant figures")
    exponent = 0
    while value >= 10:
        value /= 10
        exponent += 1
    while value < 1:
        value *= 10
        exponent -= 1
    return exponent


def round_significant(value, figures):
    """Round to a number of significant figures, halves going away from zero."""
    places = figures - 1 - significant_exponent(value)
    return round_half_up(value, places)


def fixed_text(value, places):
    """Text padded to exactly the requested number of decimal places."""
    text = decimal_text(value)
    if places <= 0:
        return text
    whole, _, digits = text.partition(".")
    return whole + "." + digits.ljust(places, "0")


def significant_text(value, figures):
    """Text showing exactly the requested number of significant figures."""
    exponent = significant_exponent(value)
    places = figures - 1 - exponent
    if places <= 0:
        return decimal_text(value)
    return fixed_text(value, places)


def unit_phrase(amount, mode):
    unit = "decimal place" if mode == DECIMAL_PLACES else "significant figure"
    return "{} {}{}".format(amount, unit, "" if amount == 1 else "s")


def make_prompt(value, amount, mode):
    return Content("Round {} to {}.".format(decimal_text(Fraction(value)),
                                            unit_phrase(amount, mode)))


# ------------------------------------------------------------ forms

SHARE_PEOPLE = (3, 6, 7, 9, 11, 12)
FRACTION_DENOMINATORS = (3, 6, 7, 9, 11, 12, 13)
DP_CONTEXTS = ("The length of a table is {} m.", "A bottle holds {} litres of water.",
               "A runner's time for a race is {} seconds.")
SF_CONTEXTS = ("A stadium holds {} people.", "A town has {} households.",
               "A car costs £{}.")
FORM_KEYS = {
    "round": {"digits", "exponent", "amount"},
    "context": {"digits", "exponent", "amount", "context"},
    "two_accuracies": {"digits", "exponent", "amounts"},
    "calculate": {"a", "b", "op", "amount"},
    "share": {"total", "people"},
    "fraction": {"numerator", "denominator", "amount"},
}


def number_from(pair):
    digits, exponent = pair
    return Fraction(digits) * Fraction(10) ** exponent


class Rounding:
    """Shared exact rounding; each mode is registered separately."""

    # -------------------------------------------------------- values
    def value_of(self, p):
        form = p["form"]
        if form == "calculate":
            a, b = number_from(p["a"]), number_from(p["b"])
            return a * b if p["op"] == "×" else a / b
        if form == "share":
            return Fraction(p["total"], p["people"])
        if form == "fraction":
            return Fraction(p["numerator"], p["denominator"])
        return Fraction(p["digits"]) * Fraction(10) ** p["exponent"]

    def amounts_of(self, p):
        if p["form"] == "two_accuracies":
            return list(p["amounts"])
        if p["form"] == "share":
            return [2]
        return [p["amount"]]

    # -------------------------------------------------------- drawing
    def draw(self, rng, level):
        form = rng.choice(self.forms[level])
        p = {"form": form}
        if form in ("round", "context", "two_accuracies"):
            digits, exponent, amount = self.make_value(rng, level)
            p.update(digits=digits, exponent=exponent)
            if form == "two_accuracies":
                p["amounts"] = sorted(rng.sample((1, 2, 3), 2))
            else:
                p["amount"] = amount
            if form == "context":
                p["context"] = rng.randrange(len(self.contexts))
        elif form == "calculate":
            p.update(a=[rng.randint(11, 99), -1], b=[rng.randint(101, 999), -2],
                     op=rng.choice(("×", "÷")),
                     amount=rng.choice((1, 2) if self.mode == DECIMAL_PLACES else (2, 3)))
        elif form == "share":
            p.update(total=rng.randint(10, 300), people=rng.choice(SHARE_PEOPLE))
        else:
            denominator = rng.choice(FRACTION_DENOMINATORS)
            numerator = rng.choice([n for n in range(1, denominator)
                                    if gcd(n, denominator) == 1])
            p.update(numerator=numerator, denominator=denominator, amount=rng.choice((2, 3)))
        return p

    # -------------------------------------------------------- checking
    def check_digits(self, p, level, amounts, structural):
        digits, exponent = p["digits"], p["exponent"]
        require(all(type(item) is int for item in (digits, exponent)),
                "Expected integer parameters")
        require(digits > 0, "Expected positive significant digits")
        require(str(digits)[-1] != "0", "Trailing zero makes the value non-canonical")
        # Stripping trailing zeros into the exponent can push it either way,
        # so these bounds cover the canonical form rather than the raw draw.
        require(-7 <= exponent <= 5, "Exponent outside bounds")
        value = self.value_of(p)
        for amount in amounts:
            if structural:
                self.check_structure(value, digits, amount, level)
            elif self.mode == SIGNIFICANT_FIGURES:
                require(amount <= len(str(digits)),
                        "Cannot round to more significant figures than the value has")

    def check_parameters(self, p, level):
        require(isinstance(p, dict), "Parameters must be a dictionary")
        form = p.get("form")
        require(form in self.forms[level], "Unexpected form for this level")
        require(set(p) == FORM_KEYS[form] | {"form"}, "Unexpected parameters")
        if form in ("round", "context"):
            require(type(p["amount"]) is int and 1 <= p["amount"] <= 4,
                    "Rounding amount outside bounds")
            self.check_digits(p, level, [p["amount"]], structural=True)
            if form == "context":
                require(p["context"] in range(len(self.contexts)), "Invalid context")
        elif form == "two_accuracies":
            amounts = p["amounts"]
            require(isinstance(amounts, list) and len(amounts) == 2
                    and all(type(a) is int and 1 <= a <= 3 for a in amounts)
                    and amounts[0] < amounts[1], "Two different accuracies required")
            self.check_digits(p, level, amounts, structural=False)
            if self.mode == SIGNIFICANT_FIGURES and level == 3:
                require(self.value_of(p) < Fraction(1, 10),
                        "Expected a value below a tenth, so significant figures start later")
        elif form == "calculate":
            for pair, low, high, exponent in ((p["a"], 11, 99, -1), (p["b"], 101, 999, -2)):
                require(isinstance(pair, list) and len(pair) == 2 and type(pair[0]) is int
                        and low <= pair[0] <= high and pair[1] == exponent,
                        "Operand outside bounds")
            require(p["op"] in ("×", "÷"), "Unknown operation")
            allowed = (1, 2) if self.mode == DECIMAL_PLACES else (2, 3)
            require(p["amount"] in allowed, "Rounding amount outside bounds")
        elif form == "share":
            require(type(p["total"]) is int and 10 <= p["total"] <= 300
                    and p["people"] in SHARE_PEOPLE, "Share outside bounds")
        else:
            n, d = p["numerator"], p["denominator"]
            require(d in FRACTION_DENOMINATORS and type(n) is int and 1 <= n < d
                    and gcd(n, d) == 1, "Fraction outside bounds")
            require(not terminates(Fraction(n, d)), "Use a fraction that does not terminate")
            require(p["amount"] in (2, 3), "Rounding amount outside bounds")
        value = self.value_of(p)
        for amount in self.amounts_of(p):
            rounded = self.apply(value, amount)
            require(rounded != value, "The value is already rounded, so nothing is tested")
            require(rounded != 0, "Rounding to zero is not a useful question")

    # -------------------------------------------------------- presentation
    def prompt_for(self, p):
        form, value = p["form"], self.value_of(p)
        shown = grouped(decimal_text(value)) if form in (
            "round", "context", "two_accuracies") else None
        if form == "round":
            return Content("Round {} to {}.".format(shown, unit_phrase(p["amount"], self.mode)))
        if form == "context":
            return Content(self.contexts[p["context"]].format(shown)
                           + " Round this to {}.".format(unit_phrase(p["amount"], self.mode)))
        if form == "two_accuracies":
            first, second = p["amounts"]
            return Content("Round {} to (a) {} (b) {}.".format(
                shown, unit_phrase(first, self.mode), unit_phrase(second, self.mode)))
        if form == "calculate":
            a, b = decimal_text(number_from(p["a"])), decimal_text(number_from(p["b"]))
            return Content("Work out {} {} {}. Give your answer to {}.".format(
                a, p["op"], b, unit_phrase(p["amount"], self.mode)))
        if form == "share":
            return Content("£{} is shared equally between {} people. How much does each "
                           "person get, to the nearest penny?".format(p["total"], p["people"]))
        n, d = p["numerator"], p["denominator"]
        return Content(
            "Write {}/{} correct to {}.".format(n, d, unit_phrase(p["amount"], self.mode)),
            r"\frac{" + str(n) + "}{" + str(d) + "}",
            display_text="Write this fraction correct to {}.".format(
                unit_phrase(p["amount"], self.mode)),
        )

    def answer_for(self, p):
        value = self.value_of(p)
        if p["form"] == "two_accuracies":
            rounded = [self.apply(value, amount) for amount in p["amounts"]]
            displays = [self.display(r, a) for r, a in zip(rounded, p["amounts"])]
            answer = {"kind": "rounded_pair", "values": [decimal_text(r) for r in rounded],
                      "displays": displays, "amounts": list(p["amounts"])}
            text = "(a) {} (b) {}".format(*(grouped(d) for d in displays))
            return answer, Content(text, text)
        amount = self.amounts_of(p)[0]
        if p["form"] == "share":
            rounded = round_half_up(value, 2)
            display = fixed_text(rounded, 2)
            answer = {"kind": "rounded_value", "value": decimal_text(rounded),
                      "display": display, "amount": 2}
            return answer, Content("£" + display, "£" + display)
        rounded = self.apply(value, amount)
        display = self.display(rounded, amount)
        answer = {"kind": "rounded_value", "value": decimal_text(rounded),
                  "display": display, "amount": amount}
        return answer, Content(grouped(display), grouped(display))

    # -------------------------------------------------------- flow
    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        for attempt in range(500):
            p = self.draw(rng, difficulty)
            try:
                self.check_parameters(p, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a suitable rounding question")
        answer, display = self.answer_for(p)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=self.prompt_for(p),
            answer=answer, answer_display=display, worked_solution=(),
            marks=1 if difficulty <= 2 and p["form"] in ("round", "context") else 2,
            tags=self.info.tags, layout_hint=LayoutHint(working_lines=3), parameters=p,
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in (1, 2, 3, 4), "Invalid difficulty")
        p = question.parameters
        self.check_parameters(p, level)
        answer, display = self.answer_for(p)
        require(question.answer == answer, "Incorrect rounded answer")
        require(question.answer_display == display, "Displayed answer mismatch")
        require(question.prompt == self.prompt_for(p), "Prompt mismatch")
        return True

    def validate_independently(self, question):
        """Round with the decimal module rather than the construction path.

        Decimal quantize does the rounding here, so nothing in this check
        shares code with round_half_up or round_significant. Significant
        figures are expressed as a decimal place count derived from the
        value's own exponent, which quantize can then apply directly.
        """
        from decimal import ROUND_HALF_UP, Decimal, localcontext

        p = question.parameters
        form = p["form"]
        with localcontext() as context:
            context.prec = 40
            if form == "calculate":
                a = Decimal(p["a"][0]).scaleb(p["a"][1])
                b = Decimal(p["b"][0]).scaleb(p["b"][1])
                value = a * b if p["op"] == "×" else a / b
            elif form == "share":
                value = Decimal(p["total"]) / Decimal(p["people"])
            elif form == "fraction":
                value = Decimal(p["numerator"]) / Decimal(p["denominator"])
            else:
                value = Decimal(p["digits"]).scaleb(p["exponent"])
            expected = []
            for amount in self.amounts_of(p):
                if self.mode == DECIMAL_PLACES or form == "share":
                    places = amount
                else:
                    # adjusted() gives the exponent of the leading digit, so
                    # this converts a significant-figure count into places.
                    places = amount - 1 - value.adjusted()
                expected.append(value.quantize(Decimal(1).scaleb(-places),
                                               rounding=ROUND_HALF_UP))
        answer = question.answer
        submitted = answer["values"] if answer["kind"] == "rounded_pair" else [answer["value"]]
        require([Fraction(str(e)) for e in expected] == [Fraction(s) for s in submitted],
                "Independent rounding disagrees")
        return True


class RoundDecimalPlaces(Rounding):
    mode = DECIMAL_PLACES
    forms = {1: ("round", "context"), 2: ("round", "calculate"),
             3: ("round", "two_accuracies"), 4: ("round", "share")}
    contexts = DP_CONTEXTS
    info = GeneratorInfo(
        id="number.rounding.decimal_places", version=2, topic="number",
        subtopic="rounding", title="Round to a number of decimal places",
        difficulty_descriptions={
            1: "Round to one decimal place, bare or in a context.",
            2: "Round to two or three places, or calculate and then round.",
            3: "A digit of 5 forces rounding up, or round one number two ways.",
            4: "Rounding carries into the next place, or share money to the penny.",
        },
        tags=("rounding", "decimals", "accuracy"),
    )

    @staticmethod
    def apply(value, amount):
        return round_half_up(value, amount)

    @staticmethod
    def display(value, amount):
        return fixed_text(value, amount)

    def make_value(self, rng, difficulty):
        if difficulty == 1:
            amount = 1
            digits = rng.randint(100, 9999)
        elif difficulty == 2:
            amount = rng.choice((2, 3))
            digits = rng.randint(10000, 999999)
        elif difficulty == 3:
            amount = rng.choice((1, 2))
            # A trailing 5 exactly at the cut sits on the halfway boundary.
            leading = rng.randint(10, 999)
            digits = int(str(leading) + "5")
        else:
            amount = rng.choice((1, 2))
            # A run of nines before the cut makes rounding carry.
            leading = rng.randint(1, 99)
            digits = int(str(leading) + "9" * rng.choice((1, 2)) + str(rng.randint(5, 9)))
        exponent = -(len(str(digits)) - rng.randint(1, 2))
        # Trailing zeros are stripped into the exponent so the stored digits
        # are canonical: 4820 with exponent -2 and 482 with exponent -1 are
        # the same value, and only one of them should be storable.
        while digits % 10 == 0:
            digits //= 10
            exponent += 1
        return digits, exponent, amount

    def check_structure(self, value, digits, amount, level):
        if level == 1:
            require(amount == 1, "Expected one decimal place")
        elif level == 2:
            require(amount in (2, 3), "Expected two or three decimal places")
        else:
            require(amount in (1, 2), "Expected one or two decimal places")


class RoundSignificantFigures(Rounding):
    mode = SIGNIFICANT_FIGURES
    forms = {1: ("round", "context"), 2: ("round", "calculate"),
             3: ("round", "two_accuracies"), 4: ("round", "fraction")}
    contexts = SF_CONTEXTS
    info = GeneratorInfo(
        id="number.rounding.significant_figures", version=2, topic="number",
        subtopic="rounding", title="Round to a number of significant figures",
        difficulty_descriptions={
            1: "Round a whole number to one or two figures, bare or in a context.",
            2: "Round a decimal to two or three figures, or calculate and then round.",
            3: "A leading-zero decimal, or round one number two ways.",
            4: "Rounding carries into an extra digit, or a fraction to significant figures.",
        },
        tags=("rounding", "significant_figures", "accuracy"),
    )

    @staticmethod
    def apply(value, amount):
        return round_significant(value, amount)

    @staticmethod
    def display(value, amount):
        return significant_text(value, amount)

    def make_value(self, rng, difficulty):
        if difficulty == 1:
            amount = rng.choice((1, 2))
            digits = rng.randint(100, 99999)
            exponent = 0
        elif difficulty == 2:
            amount = rng.choice((2, 3))
            digits = rng.randint(1000, 99999)
            exponent = -rng.randint(1, 3)
        elif difficulty == 3:
            amount = rng.choice((1, 2))
            digits = rng.randint(100, 9999)
            exponent = None
        else:
            amount = rng.choice((1, 2))
            leading = rng.randint(1, 9)
            digits = int(str(leading) + "9" * rng.choice((1, 2)) + str(rng.randint(5, 9)))
            exponent = -rng.randint(0, 3)
        # Strip trailing zeros into the exponent, so the stored digits are
        # canonical and the value itself is unchanged.
        while digits % 10 == 0:
            digits //= 10
            if exponent is not None:
                exponent += 1
        if exponent is None:
            # Level 3 needs a value below a tenth, so its leading significant
            # digit sits past the decimal point. That depends on how many
            # digits survive stripping, so the exponent is chosen here.
            exponent = -(len(str(digits)) + rng.randint(1, 2))
        return digits, exponent, amount

    def check_structure(self, value, digits, amount, level):
        require(amount <= len(str(digits)),
                "Cannot round to more significant figures than the value has")
        if level == 3:
            require(abs(value) < Fraction(1, 10),
                    "Expected a value below a tenth, so significant figures start later")
        elif level == 1:
            require(Fraction(value).denominator == 1, "Expected a whole number")