"""Place value and decimal calculation, for the opening of Foundation papers.

Numbers are exact Fractions whose denominators are powers of ten, shown as
plain decimals. The independent check recomputes everything with Python's
decimal module from the displayed text, and reads digit values from the digit
string itself.
"""
from decimal import Decimal, getcontext
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


INFO = GeneratorInfo(
    id="number.place_value.decimals", version=1,
    topic="number", subtopic="place_value",
    title="Place value and decimal calculations",
    difficulty_descriptions={
        1: "Write the value of a digit, or order decimals.",
        2: "Multiply or divide by 10, 100 or 1000, or add and subtract decimals.",
        3: "Multiply decimals, or divide by a decimal.",
        4: "Use a given multiplication fact, or do a long multiplication.",
    },
    tags=("number", "place value", "decimals"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("digit_value", "order"),
    2: ("power_of_ten", "add_subtract"),
    3: ("decimal_product", "decimal_quotient"),
    4: ("given_fact", "long_multiplication"),
}
MARKS = {1: 1, 2: 1, 3: 2, 4: 3}
WORKING_LINES = {1: 2, 2: 3, 3: 4, 4: 6}
getcontext().prec = 40

KEYS = {
    "digit_value": {"thousandths", "place"},
    "order": {"values"},
    "power_of_ten": {"thousandths", "power", "operation"},
    "add_subtract": {"first", "second", "operation"},
    "decimal_product": {"first", "first_places", "second", "second_places"},
    "decimal_quotient": {"divisor_tenths", "quotient"},
    "given_fact": {"first", "second", "first_shift", "second_shift", "ask"},
    "long_multiplication": {"first", "second"},
}


# ------------------------------------------------------------ notation

def decimal_text(value):
    """Exact decimal text for a Fraction whose denominator divides a power of ten."""
    value = Fraction(value)
    text = format((Decimal(value.numerator) / Decimal(value.denominator)).normalize(), "f")
    return text


def scaled(n, places):
    return Fraction(n, 10 ** places)


# ------------------------------------------------------------ mathematics

def digit_at(value, place):
    """The digit of value in the 10^place column."""
    return int(Fraction(value) / Fraction(10) ** place) % 10


def results(par):
    form = par["form"]
    if form == "digit_value":
        value = scaled(par["thousandths"], 3)
        return digit_at(value, par["place"]) * Fraction(10) ** par["place"]
    if form == "order":
        return sorted(scaled(v, 3) for v in par["values"])
    if form == "power_of_ten":
        value = scaled(par["thousandths"], 3)
        factor = Fraction(10) ** par["power"]
        return value * factor if par["operation"] == "times" else value / factor
    if form == "add_subtract":
        a, b = scaled(par["first"], 2), scaled(par["second"], 2)
        return a + b if par["operation"] == "add" else a - b
    if form == "decimal_product":
        return scaled(par["first"], par["first_places"]) * scaled(par["second"], par["second_places"])
    if form == "decimal_quotient":
        return Fraction(par["quotient"])
    if form == "given_fact":
        a, b = par["first"], par["second"]
        if par["ask"] == "product":
            return scaled(a, par["first_shift"]) * scaled(b, par["second_shift"])
        return Fraction(a * b) / scaled(b, par["second_shift"])
    return Fraction(par["first"] * par["second"])


def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    form = par.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(par) == KEYS[form] | {"form"}, "Unexpected parameters")
    if form == "digit_value":
        require(type(par["thousandths"]) is int and 1000 <= par["thousandths"] <= 9999999,
                "Number outside bounds")
        require(par["place"] in range(-3, 4), "Place outside bounds")
        value = scaled(par["thousandths"], 3)
        require(value >= Fraction(10) ** par["place"] or par["place"] < 0, "Place beyond the number")
        digit = digit_at(value, par["place"])
        require(digit != 0, "The digit must not be zero")
        require(decimal_text(value).count(str(digit)) == 1, "The digit must appear once")
        require(len(decimal_text(value).split(".")[-1]) >= -par["place"] if par["place"] < 0 else True,
                "Digit must be shown")
    elif form == "order":
        values = par["values"]
        require(isinstance(values, list) and len(values) == 5 and len(set(values)) == 5
                and all(type(v) is int and 1 <= v <= 9999 for v in values), "Five values needed")
        require(len({decimal_text(scaled(v, 3)).split(".")[0] for v in values}) == 1,
                "Values must share their whole-number part")
    elif form == "power_of_ten":
        require(type(par["thousandths"]) is int and 1 <= par["thousandths"] <= 99999
                and par["thousandths"] % 10 != 0, "Number outside bounds")
        require(par["power"] in (1, 2, 3) and par["operation"] in ("times", "divide"),
                "Unexpected operation")
    elif form == "add_subtract":
        require(all(type(par[k]) is int and 100 <= par[k] <= 99999 for k in ("first", "second")),
                "Numbers outside bounds")
        require(par["operation"] in ("add", "subtract"), "Unexpected operation")
        if par["operation"] == "subtract":
            require(par["first"] > par["second"], "Subtraction must stay positive")
        require(par["first"] % 10 or par["second"] % 10, "Needs a hundredths digit")
    elif form == "decimal_product":
        require(all(type(par[k]) is int for k in KEYS[form]), "Integer parameters required")
        require(2 <= par["first"] <= 99 and 2 <= par["second"] <= 99, "Digits outside bounds")
        require(par["first"] % 10 and par["second"] % 10, "No trailing zeros")
        require(par["first_places"] in (1, 2) and par["second_places"] in (0, 1, 2)
                and par["first_places"] + par["second_places"] <= 3, "Places outside bounds")
    elif form == "decimal_quotient":
        require(type(par["divisor_tenths"]) is int and par["divisor_tenths"] in range(2, 26)
                and par["divisor_tenths"] % 10 != 0, "Divisor outside bounds")
        require(type(par["quotient"]) is int and 3 <= par["quotient"] <= 90, "Quotient outside bounds")
    elif form == "given_fact":
        require(all(type(par[k]) is int for k in ("first", "second", "first_shift", "second_shift")),
                "Integer parameters required")
        require(12 <= par["first"] <= 98 and 12 <= par["second"] <= 98
                and par["first"] % 10 and par["second"] % 10, "Factors outside bounds")
        require(par["first_shift"] in (0, 1, 2) and par["second_shift"] in (0, 1, 2)
                and par["first_shift"] + par["second_shift"] >= 1, "Shifts outside bounds")
        require(par["ask"] in ("product", "quotient"), "Unexpected question")
        if par["ask"] == "quotient":
            require(par["second_shift"] >= 1, "Divide by a decimal")
    else:
        require(type(par["first"]) is int and type(par["second"]) is int
                and 102 <= par["first"] <= 998 and 12 <= par["second"] <= 98
                and par["first"] % 10 and par["second"] % 10, "Factors outside bounds")


# ------------------------------------------------------------ wording

def prompt_for(par):
    form = par["form"]
    if form == "digit_value":
        value = scaled(par["thousandths"], 3)
        text = "Write down the value of the {} in {}.".format(
            digit_at(value, par["place"]), decimal_text(value))
    elif form == "order":
        text = "Write these numbers in order of size. Start with the smallest. {}".format(
            "   ".join(decimal_text(scaled(v, 3)) for v in par["values"]))
    elif form == "power_of_ten":
        symbol = "x" if par["operation"] == "times" else "÷"
        text = "Work out {} {} {}.".format(decimal_text(scaled(par["thousandths"], 3)), symbol,
                                           10 ** par["power"])
    elif form == "add_subtract":
        symbol = "+" if par["operation"] == "add" else "-"
        text = "Work out {} {} {}.".format(decimal_text(scaled(par["first"], 2)), symbol,
                                           decimal_text(scaled(par["second"], 2)))
    elif form == "decimal_product":
        text = "Work out {} x {}.".format(decimal_text(scaled(par["first"], par["first_places"])),
                                          decimal_text(scaled(par["second"], par["second_places"])))
    elif form == "decimal_quotient":
        divisor = scaled(par["divisor_tenths"], 1)
        text = "Work out {} ÷ {}.".format(decimal_text(divisor * par["quotient"]),
                                          decimal_text(divisor))
    elif form == "given_fact":
        a, b = par["first"], par["second"]
        fact = "{} x {} = {}.".format(a, b, a * b)
        if par["ask"] == "product":
            task = "Work out {} x {}.".format(decimal_text(scaled(a, par["first_shift"])),
                                              decimal_text(scaled(b, par["second_shift"])))
        else:
            task = "Work out {} ÷ {}.".format(a * b, decimal_text(scaled(b, par["second_shift"])))
        text = "Using {} {}".format(fact, task)
    else:
        text = "Work out {} x {}.".format(par["first"], par["second"])
    return Content(text)


def answer_for(par):
    value = results(par)
    if par["form"] == "order":
        shown = ", ".join(decimal_text(v) for v in value)
        return {"kind": "ordered", "values": [rational_text(v) for v in value]}, Content(shown)
    return {"kind": "decimal", "value": rational_text(value)}, Content(decimal_text(value))


def draw_parameters(rng, form):
    par = {"form": form}
    if form == "digit_value":
        par.update(thousandths=rng.randint(1000, 9999999), place=rng.randint(-3, 3))
    elif form == "order":
        whole = rng.randint(0, 9)
        digits = rng.sample(range(1, 10), 3)
        pool = {whole * 1000 + digits[0] * 100, whole * 1000 + digits[0] * 100 + digits[1] * 10,
                whole * 1000 + digits[1] * 100 + digits[0] * 10,
                whole * 1000 + digits[0] * 100 + digits[1],
                whole * 1000 + digits[1] * 100 + digits[2] * 10 + digits[0],
                whole * 1000 + digits[0] * 10 + digits[1], whole * 1000 + digits[2] * 100}
        values = sorted(v for v in pool if v > 0)
        rng.shuffle(values)
        par["values"] = values[:5]
    elif form == "power_of_ten":
        par.update(thousandths=rng.randint(1, 99999), power=rng.randint(1, 3),
                   operation=rng.choice(("times", "divide")))
    elif form == "add_subtract":
        par.update(first=rng.randint(100, 99999), second=rng.randint(100, 99999),
                   operation=rng.choice(("add", "subtract")))
    elif form == "decimal_product":
        par.update(first=rng.randint(2, 99), first_places=rng.choice((1, 2)),
                   second=rng.randint(2, 99), second_places=rng.choice((0, 1, 2)))
    elif form == "decimal_quotient":
        par.update(divisor_tenths=rng.randint(2, 25), quotient=rng.randint(3, 90))
    elif form == "given_fact":
        par.update(first=rng.randint(12, 98), second=rng.randint(12, 98),
                   first_shift=rng.choice((0, 1, 2)), second_shift=rng.choice((0, 1, 2)),
                   ask=rng.choice(("product", "quotient")))
    else:
        par.update(first=rng.randint(102, 998), second=rng.randint(12, 98))
    return par


# ------------------------------------------------------------ generator

class PlaceValue:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        form = rng.choice(FORMS[difficulty])
        for attempt in range(2000):
            par = draw_parameters(rng, form)
            try:
                check_parameters(par, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a place value question")
        answer, display = answer_for(par)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(par),
            answer=answer, answer_display=display, worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=WORKING_LINES[difficulty]),
            parameters=par,
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        require(type(q.difficulty) is int and q.difficulty in (1, 2, 3, 4), "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        check_parameters(q.parameters, q.difficulty)
        answer, display = answer_for(q.parameters)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Answer display mismatch")
        require(q.prompt == prompt_for(q.parameters), "Prompt mismatch")
        return True

    def validate_independently(self, q):
        """Recompute from the displayed numbers with the decimal module."""
        par, answer = q.parameters, q.answer
        form = par["form"]
        words = q.prompt.text.replace("÷", " / ").replace(" x ", " * ").split()
        numbers = []
        for word in words:
            cleaned = word.strip(".,")
            try:
                numbers.append(Decimal(cleaned))
            except Exception:
                continue
        if form == "order":
            stated = [Decimal(Fraction(v).numerator) / Decimal(Fraction(v).denominator)
                      for v in answer["values"]]
            require(stated == sorted(numbers[-5:]), "Order disagrees")
            return True
        stated = Fraction(answer["value"])
        stated_decimal = Decimal(stated.numerator) / Decimal(stated.denominator)
        if form == "digit_value":
            digit, number = numbers[0], numbers[1]
            text = format(number, "f")
            whole, _, fraction = text.partition(".")
            if par["place"] >= 0:
                position = len(whole) - 1 - par["place"]
                require(whole[position] == str(digit), "Digit is not in that column")
            else:
                require(fraction[-par["place"] - 1] == str(digit), "Digit is not in that column")
            expected = digit * Decimal(10) ** par["place"]
        elif form == "given_fact":
            a, b = numbers[-2], numbers[-1]
            expected = a * b if par["ask"] == "product" else a / b
        else:
            a, b = numbers[-2], numbers[-1]
            if form == "power_of_ten":
                expected = a * b if par["operation"] == "times" else a / b
            elif form == "add_subtract":
                expected = a + b if par["operation"] == "add" else a - b
            elif form == "decimal_quotient":
                expected = a / b
            else:
                expected = a * b
        require(stated_decimal == expected, "Independent decimal calculation disagrees")
        return True