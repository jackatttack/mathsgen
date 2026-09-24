"""Basic probability: complements, probability tables, sample spaces and expectation.

Probabilities are held in exact hundredths or Fractions. Tables use four
spinner colours; sample spaces use two fair dice or spinners. Every
probability asked for lies strictly between 0 and 1.
"""
import math
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


INFO = GeneratorInfo(
    id="probability.basics.events", version=1,
    topic="probability", subtopic="basic_events",
    title="Basic probability: complements, tables and sample spaces",
    difficulty_descriptions={
        1: "Find the probability that an event does not happen.",
        2: "Find a missing probability in a table, or the probability of A or B.",
        3: "Use a sample space for two dice or spinners, or estimate a frequency.",
        4: "Solve for x in a probability table, then estimate a frequency.",
    },
    tags=("probability", "sample space", "expected frequency"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("complement_decimal", "complement_fraction"),
    2: ("missing", "either"),
    3: ("sample_space", "expected"),
    4: ("algebraic", "algebraic_expected"),
}
CONTEXTS = (
    ("it will rain tomorrow", "it will not rain tomorrow"),
    ("a train arrives late", "the train does not arrive late"),
    ("Sam wins a game of chess", "Sam does not win the game"),
    ("a seed grows into a plant", "the seed does not grow"),
)
COLOURS = ("red", "blue", "green", "yellow")
SIDES = ((6, 6), (4, 5), (4, 6), (5, 5), (3, 6))
EVENTS = ("sum_equals", "sum_greater", "product_even", "same")
TRIALS = (50, 60, 80, 100, 120, 150, 200, 250, 300, 400, 500)
MULTIPLIERS = (2, 3)
MARKS = {1: 1, 2: 2, 3: 2, 4: 3}
WORKING_LINES = {1: 2, 2: 3, 3: 4, 4: 6}

KEYS = {
    "complement_decimal": {"context", "hundredths"},
    "complement_fraction": {"context", "numerator", "denominator"},
    "missing": {"values", "missing_index"},
    "either": {"values", "pair"},
    "sample_space": {"sides", "event", "target"},
    "expected": {"values", "index", "trials"},
    "algebraic": {"known", "multiplier"},
    "algebraic_expected": {"known", "multiplier", "trials"},
}


# ------------------------------------------------------------ helpers

def decimal_text(hundredths):
    text = "{}.{:02d}".format(hundredths // 100, hundredths % 100)
    return text.rstrip("0").rstrip(".") if "." in text else text


def listing(values):
    return ", ".join("{} {}".format(colour, decimal_text(value))
                     for colour, value in zip(COLOURS, values))


def is_hundredths_list(values, size):
    return (isinstance(values, list) and len(values) == size
            and all(type(v) is int and v % 5 == 0 and 5 <= v <= 90 for v in values))


def outcomes(sides):
    a, b = sides
    return [(x, y) for x in range(1, a + 1) for y in range(1, b + 1)]


def event_holds(event, target, x, y):
    if event == "sum_equals":
        return x + y == target
    if event == "sum_greater":
        return x + y > target
    if event == "product_even":
        return (x * y) % 2 == 0
    return x == y


def unknown_x(par):
    """x from known + x + k x = 1, in hundredths."""
    rest = 100 - sum(par["known"])
    return Fraction(rest, 1 + par["multiplier"])


# ------------------------------------------------------------ checks

def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    form = par.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(par) == KEYS[form] | {"form"}, "Unexpected parameters")

    if form == "complement_decimal":
        require(par["context"] in range(len(CONTEXTS)), "Unknown context")
        require(type(par["hundredths"]) is int and 5 <= par["hundredths"] <= 95,
                "Probability outside bounds")
    elif form == "complement_fraction":
        require(par["context"] in range(len(CONTEXTS)), "Unknown context")
        n, d = par["numerator"], par["denominator"]
        require(type(n) is int and type(d) is int and 3 <= d <= 12 and 0 < n < d
                and math.gcd(n, d) == 1, "Fraction outside bounds")
    elif form == "missing":
        require(is_hundredths_list(par["values"], 3), "Probabilities outside bounds")
        require(par["missing_index"] in range(4), "Unknown missing colour")
        require(100 - sum(par["values"]) >= 5, "Missing probability must be positive")
    elif form in ("either", "expected"):
        require(is_hundredths_list(par["values"], 4) and sum(par["values"]) == 100,
                "Table must total 1")
        if form == "either":
            pair = par["pair"]
            require(isinstance(pair, list) and len(pair) == 2 and pair[0] < pair[1]
                    and all(i in range(4) for i in pair), "Unexpected pair")
        else:
            require(par["index"] in range(4) and par["trials"] in TRIALS, "Unexpected spin")
            require(par["trials"] * par["values"][par["index"]] % 100 == 0,
                    "Expected count must be whole")
    elif form == "sample_space":
        sides = par["sides"]
        require(isinstance(sides, list) and tuple(sides) in SIDES, "Unexpected dice")
        require(par["event"] in EVENTS and type(par["target"]) is int, "Unexpected event")
        if par["event"] == "same":
            require(sides[0] == sides[1] and par["target"] == 0, "Same score needs equal dice")
        elif par["event"] == "product_even":
            require(par["target"] == 0, "No target for an even product")
        else:
            require(2 <= par["target"] <= sides[0] + sides[1], "Target outside bounds")
        count = sum(event_holds(par["event"], par["target"], x, y) for x, y in outcomes(sides))
        require(0 < count < len(outcomes(sides)), "Probability must be between 0 and 1")
    else:
        require(is_hundredths_list(par["known"], 2), "Probabilities outside bounds")
        require(par["multiplier"] in MULTIPLIERS, "Unexpected multiplier")
        x = unknown_x(par)
        require(x.denominator == 1 and x >= 5, "x must be a positive whole number of hundredths")
        if form == "algebraic_expected":
            require(par["trials"] in TRIALS, "Unexpected number of spins")
            require(par["trials"] * par["multiplier"] * int(x) % 100 == 0,
                    "Expected count must be whole")


# ------------------------------------------------------------ wording and answers

def full_values(par):
    """All four hundredths values for a missing or algebraic table."""
    if par["form"] == "missing":
        values = list(par["values"])
        values.insert(par["missing_index"], 100 - sum(values))
        return values
    x = int(unknown_x(par))
    return [par["known"][0], x, par["multiplier"] * x, par["known"][1]]


def prompt_for(par):
    form = par["form"]
    if form in ("complement_decimal", "complement_fraction"):
        event, complement = CONTEXTS[par["context"]]
        if form == "complement_decimal":
            probability = decimal_text(par["hundredths"])
        else:
            probability = "{}/{}".format(par["numerator"], par["denominator"])
        text = ("The probability that {} is {}. Work out the probability that {}."
                .format(event, probability, complement))
    elif form == "missing":
        index = par["missing_index"]
        known = [(colour, value) for colour, value in
                 zip([c for i, c in enumerate(COLOURS) if i != index], par["values"])]
        text = ("A spinner can land on red, blue, green or yellow. The probability that it "
                "lands on {} is {}, on {} is {} and on {} is {}. Work out the probability that "
                "the spinner lands on {}.").format(
            known[0][0], decimal_text(known[0][1]), known[1][0], decimal_text(known[1][1]),
            known[2][0], decimal_text(known[2][1]), COLOURS[index])
    elif form == "either":
        first, second = (COLOURS[i] for i in par["pair"])
        text = ("A spinner can land on red, blue, green or yellow. The probabilities are: {}. "
                "Work out the probability that the spinner lands on {} or {}.").format(
            listing(par["values"]), first, second)
    elif form == "expected":
        text = ("A biased spinner can land on red, blue, green or yellow. The probabilities "
                "are: {}. The spinner is spun {} times. Work out an estimate for the number "
                "of times it lands on {}.").format(
            listing(par["values"]), par["trials"], COLOURS[par["index"]])
    elif form == "sample_space":
        a, b = par["sides"]
        if a == b == 6:
            setup = "Two fair six-sided dice are rolled."
            noun = "dice"
        else:
            setup = ("Two fair spinners are spun. One is numbered 1 to {} and the other is "
                     "numbered 1 to {}.".format(a, b))
            noun = "spinners"
        event, target = par["event"], par["target"]
        if event == "sum_equals":
            task = "the total of the two scores is {}".format(target)
        elif event == "sum_greater":
            task = "the total of the two scores is greater than {}".format(target)
        elif event == "product_even":
            task = "the product of the two scores is an even number"
        else:
            task = "both {} show the same score".format(noun)
        text = "{} Work out the probability that {}.".format(setup, task)
    else:
        k = par["multiplier"]
        text = ("A biased spinner can land on red, blue, green or yellow. P(red) = {}, "
                "P(blue) = x, P(green) = {}x and P(yellow) = {}.").format(
            decimal_text(par["known"][0]), k, decimal_text(par["known"][1]))
        if form == "algebraic":
            text += " Work out the value of x."
        else:
            text += (" The spinner is spun {} times. Work out an estimate for the number of "
                     "times it lands on green.".format(par["trials"]))
    return Content(text)


def answer_for(par):
    form = par["form"]
    if form == "complement_decimal":
        value = Fraction(100 - par["hundredths"], 100)
        return ({"kind": "probability", "value": rational_text(value)},
                Content(decimal_text(100 - par["hundredths"])))
    if form == "complement_fraction":
        value = 1 - Fraction(par["numerator"], par["denominator"])
        return {"kind": "probability", "value": rational_text(value)}, Content(rational_text(value))
    if form == "missing":
        missing = 100 - sum(par["values"])
        return ({"kind": "probability", "value": rational_text(Fraction(missing, 100))},
                Content(decimal_text(missing)))
    if form == "either":
        total = sum(par["values"][i] for i in par["pair"])
        return ({"kind": "probability", "value": rational_text(Fraction(total, 100))},
                Content(decimal_text(total)))
    if form == "expected":
        count = par["trials"] * par["values"][par["index"]] // 100
        return ({"kind": "quantity", "value": str(count)},
                Content("{} x {} = {}".format(par["trials"],
                                              decimal_text(par["values"][par["index"]]), count)))
    if form == "sample_space":
        space = outcomes(par["sides"])
        count = sum(event_holds(par["event"], par["target"], x, y) for x, y in space)
        value = Fraction(count, len(space))
        return ({"kind": "probability", "value": rational_text(value)},
                Content("{}/{} = {}".format(count, len(space), rational_text(value))
                        if value.denominator != len(space) else rational_text(value)))
    x = int(unknown_x(par))
    if form == "algebraic":
        return ({"kind": "probability", "value": rational_text(Fraction(x, 100))},
                Content("x = " + decimal_text(x)))
    green = par["multiplier"] * x
    count = par["trials"] * green // 100
    return ({"kind": "quantity", "value": str(count), "x": rational_text(Fraction(x, 100))},
            Content("x = {}, so P(green) = {} and {} x {} = {}".format(
                decimal_text(x), decimal_text(green), par["trials"], decimal_text(green), count)))


def draw_parameters(rng, form):
    par = {"form": form}
    if form == "complement_decimal":
        par.update(context=rng.randrange(len(CONTEXTS)), hundredths=rng.randint(5, 95))
    elif form == "complement_fraction":
        d = rng.randint(3, 12)
        par.update(context=rng.randrange(len(CONTEXTS)), numerator=rng.randint(1, d - 1),
                   denominator=d)
    elif form == "missing":
        par.update(values=[rng.randrange(5, 45, 5) for _ in range(3)],
                   missing_index=rng.randrange(4))
    elif form in ("either", "expected"):
        values = [rng.randrange(5, 50, 5) for _ in range(3)]
        values.append(100 - sum(values))
        par["values"] = values
        if form == "either":
            par["pair"] = sorted(rng.sample(range(4), 2))
        else:
            par.update(index=rng.randrange(4), trials=rng.choice(TRIALS))
    elif form == "sample_space":
        sides = list(rng.choice(SIDES))
        event = rng.choice(EVENTS)
        target = rng.randint(3, sides[0] + sides[1] - 1) if event in ("sum_equals",
                                                                       "sum_greater") else 0
        par.update(sides=sides, event=event, target=target)
    else:
        par.update(known=[rng.randrange(5, 50, 5) for _ in range(2)],
                   multiplier=rng.choice(MULTIPLIERS))
        if form == "algebraic_expected":
            par["trials"] = rng.choice(TRIALS)
    return par


# ------------------------------------------------------------ generator

class BasicProbability:
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
            raise ValueError("Could not construct a basic probability question")
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
        """Complements and table totals by addition; sample spaces by closed-form
        counting; algebraic answers substituted back so the table totals 1."""
        par, answer = q.parameters, q.answer
        form = par.get("form")
        if form == "complement_decimal":
            require(Fraction(answer["value"]) + Fraction(par["hundredths"], 100) == 1,
                    "Complement does not total 1")
        elif form == "complement_fraction":
            require(Fraction(answer["value"]) + Fraction(par["numerator"], par["denominator"]) == 1,
                    "Complement does not total 1")
        elif form == "missing":
            require(Fraction(answer["value"]) + Fraction(sum(par["values"]), 100) == 1,
                    "Table does not total 1")
        elif form == "either":
            require(Fraction(answer["value"]) == sum(Fraction(par["values"][i], 100)
                                                     for i in par["pair"]),
                    "Either probability disagrees")
        elif form == "expected":
            require(Fraction(answer["value"]) == par["trials"] * Fraction(
                par["values"][par["index"]], 100), "Expected count disagrees")
        elif form == "sample_space":
            a, b = par["sides"]
            event, target = par["event"], par["target"]
            if event == "sum_equals":
                count = max(0, min(a, target - 1) - max(1, target - b) + 1)
            elif event == "sum_greater":
                count = a * b - sum(max(0, min(a, s - 1) - max(1, s - b) + 1)
                                    for s in range(2, target + 1))
            elif event == "product_even":
                count = a * b - ((a + 1) // 2) * ((b + 1) // 2)
            else:
                count = min(a, b)
            require(Fraction(answer["value"]) == Fraction(count, a * b),
                    "Independent sample-space count disagrees")
        else:
            x = Fraction(answer["x"] if form == "algebraic_expected" else answer["value"])
            total = (Fraction(par["known"][0], 100) + x + par["multiplier"] * x
                     + Fraction(par["known"][1], 100))
            require(total == 1, "Substituted x does not make the table total 1")
            if form == "algebraic_expected":
                require(Fraction(answer["value"]) == par["trials"] * par["multiplier"] * x,
                        "Expected count disagrees")
        return True