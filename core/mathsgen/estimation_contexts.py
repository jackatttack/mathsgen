"""Worded contexts for number.estimation.product and number.estimation.quotient.

Each story rounds both given values to one significant figure and calculates
with the rounded values, exactly like the bare family. Stories are levelled
to match the bare levels: whole numbers, larger numbers, decimals, then a
value below one.

check() uses rounding.round_significant; solve() rounds independently in
SymPy by locating the leading power of ten.
"""
from fractions import Fraction

from .core import Content, rational_text, require
from . import worded
from .worded import Context, quantity
from .rounding import decimal_text, round_significant, terminates


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {1: 0.35, 2: 0.4, 3: 0.5, 4: 0.5}
MARKS = {1: 2, 2: 2, 3: 2, 4: 3}
WORKING_LINES = {1: 3, 2: 3, 3: 3, 4: 4}
ESTIMATE_LIMIT = 100000

# story: (level, text with {a} and {b}, unit, a bounds, b bounds, b is money)
# bounds are (low, high, places): values low/10^places to high/10^places.
STORIES = {
    "product": {
        "boxes": (1, "A lorry carries {a} boxes. Each box weighs {b} kg. "
                     "Estimate the total mass of the boxes.", "kg",
                  (11, 99, 0), (11, 499, 0), False),
        "stadium": (2, "A stadium sells {a} tickets at £{b} each. "
                       "Estimate the total money taken.", "£",
                    (1001, 9999, 0), (11, 99, 0), False),
        "shop": (3, "A shop sells {a} T-shirts at £{b} each. "
                    "Estimate the total money taken.", "£",
                 (11, 99, 0), (501, 4999, 2), True),
        "tap": (4, "A tap leaks {b} litres of water every hour. "
                   "Estimate how much water leaks in {a} hours.", "litres",
                (101, 999, 0), (11, 99, 2), False),
    },
    "quotient": {
        "share": (1, "A school raises £{a}. The money is shared equally between {b} "
                     "classes. Estimate how much each class receives.", "£",
                  (101, 999, 0), (11, 99, 0), False),
        "coaches": (2, "{a} people are going on a trip. Each coach holds {b} people. "
                       "Estimate the number of coaches needed.", "coaches",
                    (1001, 9999, 0), (11, 99, 0), False),
        "fuel": (3, "A car travels {a} miles using {b} litres of fuel. Estimate the "
                    "number of miles the car travels per litre.", "miles per litre",
                 (1001, 9999, 1), (101, 999, 1), False),
        "ribbon": (4, "A ribbon {a} m long is cut into pieces that are each {b} m long. "
                      "Estimate the number of pieces.", "pieces",
                   (101, 999, 1), (11, 99, 2), False),
    },
}


def value_from(rng, bounds):
    low, high, places = bounds
    return Fraction(rng.randint(low, high), 10 ** places)


def within(value, bounds):
    low, high, places = bounds
    scaled = value * 10 ** places
    return scaled.denominator == 1 and low <= scaled <= high


def shown(value, money):
    if money:
        pence = int(value * 100)
        return "{}.{:02d}".format(pence // 100, pence % 100)
    return decimal_text(value)


def tidy(estimate):
    if not terminates(estimate):
        return False
    if abs(estimate) < 10:
        return (estimate * 10).denominator == 1
    return estimate.denominator == 1


def estimate_of(operation, a, b):
    first, second = round_significant(a, 1), round_significant(b, 1)
    require(first != 0 and second != 0, "Rounded values must be nonzero")
    return first * second if operation == "product" else first / second


def estimate_answer(estimate, unit):
    return quantity(estimate, unit)


def estimate_display(estimate, unit):
    if unit == "£":
        return Content("£" + decimal_text(estimate))
    return Content("{} {}".format(decimal_text(estimate), unit))


def make_contexts(operation):
    def build(rng, name):
        _, _, _, a_bounds, b_bounds, _ = STORIES[operation][name]
        return {"context": name, "a": rational_text(value_from(rng, a_bounds)),
                "b": rational_text(value_from(rng, b_bounds))}

    def check(p):
        story = STORIES[operation][p["context"]]
        _, _, _, a_bounds, b_bounds, _ = story
        values = []
        for key, bounds in (("a", a_bounds), ("b", b_bounds)):
            require(isinstance(p[key], str), "Values stored as text")
            value = Fraction(p[key])
            require(p[key] == rational_text(value) and within(value, bounds), "Value bounds")
            values.append(value)
        require(any(round_significant(v, 1) != v for v in values),
                "At least one value must change when rounded")
        estimate = estimate_of(operation, *values)
        require(tidy(estimate) and 0 < estimate <= ESTIMATE_LIMIT, "Estimate must be tidy")
        return estimate

    def parts(p):
        estimate = check(p)
        _, text, unit, _, _, money = STORIES[operation][p["context"]]
        prompt = text.format(a=shown(Fraction(p["a"]), False), b=shown(Fraction(p["b"]), money))
        return {"prompt": Content(prompt), "answer": estimate_answer(estimate, unit),
                "answer_display": estimate_display(estimate, unit)}

    def solve(p, sympy):
        def one_figure(value):
            value = sympy.Rational(value)
            power = 0
            while value >= sympy.Integer(10) ** (power + 1):
                power += 1
            while value < sympy.Integer(10) ** power:
                power -= 1
            scale = sympy.Integer(10) ** power
            return sympy.floor(value / scale + sympy.Rational(1, 2)) * scale

        first, second = one_figure(p["a"]), one_figure(p["b"])
        estimate = first * second if operation == "product" else first / second
        return estimate_answer(estimate, STORIES[operation][p["context"]][2])

    return {
        name: Context(story[0], frozenset({"context", "a", "b"}),
                      (lambda rng, name=name: build(rng, name)), check, parts, solve)
        for name, story in STORIES[operation].items()
    }


CONTEXTS_BY_OPERATION = {operation: make_contexts(operation) for operation in STORIES}


def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS_BY_OPERATION[generator.operation],
                           MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS_BY_OPERATION[generator.operation],
                           MARKS, WORKING_LINES)


def validate_independently(generator, q):
    import sympy
    spec = CONTEXTS_BY_OPERATION[generator.operation][q.parameters["context"]]
    require(spec.solve(q.parameters, sympy) == q.answer, "Independent estimate disagrees")
    return True