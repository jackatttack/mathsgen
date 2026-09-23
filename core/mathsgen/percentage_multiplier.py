"""Percentage change expressed as a decimal multiplier, in both directions.

A percentage increase or decrease is applied by multiplying: a 4% increase
is a multiplier of 1.04, and a 17% decrease is 0.83. FindMultiplier asks for
the multiplier; InterpretMultiplier asks what a multiplier represents. Both
share the forms below (two per level). Every value is an exact rational, so
no float rounding enters the arithmetic.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .rounding import decimal_text


# ------------------------------------------------------------ editable knobs

# Whole percentages at the easier levels, then halves, then the values
# above 100% where the multiplier passes 2 and students often falter.
PERCENTAGES = {
    1: tuple(Fraction(value) for value in (4, 5, 10, 12, 20, 25, 30, 40, 50)),
    2: tuple(Fraction(value) for value in (3, 7, 13, 17, 23, 36, 48, 62, 85, 91)),
    3: tuple(Fraction(value, 2) for value in (5, 15, 25, 45, 75, 125, 155)),
    4: tuple(Fraction(value) for value in (
        110, 125, 140, 175, 200, 250, 88, 92, 95, 96,
    )),
}
# Level 4 pairs each value with the direction it can have (above 100% can
# only be an increase), which keeps the draw even.
LEVEL_FOUR_DIRECTIONS = {
    Fraction(110): ("increase",), Fraction(125): ("increase",),
    Fraction(140): ("increase",), Fraction(175): ("increase",),
    Fraction(200): ("increase",), Fraction(250): ("increase",),
    Fraction(88): ("decrease",), Fraction(92): ("decrease",),
    Fraction(95): ("decrease",), Fraction(96): ("decrease",),
}
FIND_FORMS = {1: ("direct", "context"), 2: ("direct", "apply"),
              3: ("direct", "repeated"), 4: ("direct", "compound")}
INTERPRET_FORMS = {1: ("direct", "context"), 2: ("direct", "apply_reverse"),
                   3: ("direct", "repeated"), 4: ("direct", "compound")}
REPEATED_PERCENTAGES = tuple(Fraction(v) for v in (5, 10, 15, 20, 25, 30, 40, 50))
COMPOUND_PERCENTAGES = tuple(Fraction(v) for v in (2, 3, 4, 5, 10, 20, 30))
FIND_CONTEXTS = ("A shop's prices {change}.", "A town's population {change}.",
                 "The value of a painting {change}.")
INTERPRET_CONTEXTS = ("The number of visitors to a museum is multiplied by {m}.",
                      "A company multiplies all its prices by {m}.")


# ------------------------------------------------------------ exact values

def multiplier_for(percentage, direction):
    """The exact multiplier: 1 plus or minus the percentage as a fraction."""
    change = Fraction(percentage, 100)
    return 1 + change if direction == "increase" else 1 - change


def change_of(multiplier):
    """(percentage, direction) described by a multiplier other than 1."""
    return abs(multiplier - 1) * 100, ("increase" if multiplier > 1 else "decrease")


def percentage_text(percentage):
    return decimal_text(Fraction(percentage)) + "%"


def change_text(percentage, direction):
    return "{} {}".format(percentage_text(percentage), direction)


def money_text(value):
    """Exact pounds and pence without floats."""
    pence = Fraction(value) * 100
    require(pence.denominator == 1, "Money must be whole pence")
    pence = int(pence)
    return "£{}.{:02d}".format(pence // 100, pence % 100)


def overall_multiplier(p):
    form = p["form"]
    if form == "repeated":
        return (multiplier_for(Fraction(p["first"][0]), p["first"][1])
                * multiplier_for(Fraction(p["second"][0]), p["second"][1]))
    base = multiplier_for(Fraction(p["percentage"]), p["direction"])
    return base ** p["years"] if form == "compound" else base


# ------------------------------------------------------------ prompts and answers

def prompt_for(p, asks):
    form = p["form"]
    m = overall_multiplier(p)
    if form == "direct":
        if asks == "multiplier":
            return Content("Write down the single decimal multiplier for a {}.".format(
                change_text(Fraction(p["percentage"]), p["direction"])))
        return Content("A quantity is multiplied by {}. Describe the percentage change "
                       "this represents.".format(decimal_text(m)))
    if form == "context":
        if asks == "multiplier":
            change = "{}s by {}".format(p["direction"], percentage_text(Fraction(p["percentage"])))
            return Content(FIND_CONTEXTS[p["context"]].format(change=change)
                           + " Write down the single decimal multiplier for this change.")
        return Content(INTERPRET_CONTEXTS[p["context"]].format(m=decimal_text(m))
                       + " Describe the percentage change.")
    if form == "apply":
        return Content("Use a single multiplier to {} £{} by {}.".format(
            p["direction"], p["amount"], percentage_text(Fraction(p["percentage"]))))
    if form == "apply_reverse":
        return Content("A price was multiplied by {} and is now {}. What was the price "
                       "before the change?".format(decimal_text(m),
                                                   money_text(p["amount"] * m)))
    if form == "repeated":
        (a, first), (b, second) = p["first"], p["second"]
        if asks == "multiplier":
            return Content("A value has a {} followed by a {}. Write down the single decimal "
                           "multiplier for the overall change.".format(
                               change_text(Fraction(a), first), change_text(Fraction(b), second)))
        return Content("A value is multiplied by {} and then by {}. Describe the overall "
                       "percentage change.".format(
                           decimal_text(multiplier_for(Fraction(a), first)),
                           decimal_text(multiplier_for(Fraction(b), second))))
    years = p["years"]
    if asks == "multiplier":
        return Content("A value {}s by {} every year for {} years. Write down the single "
                       "decimal multiplier for the whole {} years.".format(
                           p["direction"], percentage_text(Fraction(p["percentage"])),
                           years, years))
    return Content("A value is multiplied by {} every year for {} years. Describe the "
                   "overall percentage change.".format(
                       decimal_text(multiplier_for(Fraction(p["percentage"]), p["direction"])),
                       years))


def answer_for(p, asks):
    form = p["form"]
    m = overall_multiplier(p)
    if form == "apply":
        value = p["amount"] * m
        return {"kind": "money", "value": rational_text(value)}, Content(money_text(value))
    if form == "apply_reverse":
        return ({"kind": "money", "value": rational_text(Fraction(p["amount"]))},
                Content(money_text(p["amount"])))
    percentage, direction = change_of(m)
    answer = {"multiplier": rational_text(m), "percentage": rational_text(percentage),
              "direction": direction}
    if asks == "multiplier":
        return dict(answer, kind="multiplier"), Content(decimal_text(m))
    return dict(answer, kind="percentage_change"), Content(change_text(percentage, direction))


def check_change(percentage_text_value, direction, pool):
    percentage = Fraction(percentage_text_value)
    require(percentage_text_value == rational_text(percentage) and percentage in pool,
            "Percentage outside difficulty rules")
    require(direction in ("increase", "decrease"), "Unknown direction")
    require(not (direction == "decrease" and percentage >= 100),
            "A decrease of 100% or more has no sensible multiplier")
    return percentage


def check_parameters(p, level, forms):
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(form in forms[level], "Unexpected form for this level")
    keys = {"direct": {"percentage", "direction"},
            "context": {"percentage", "direction", "context"},
            "apply": {"percentage", "direction", "amount"},
            "apply_reverse": {"percentage", "direction", "amount"},
            "repeated": {"first", "second"},
            "compound": {"percentage", "direction", "years"}}[form]
    require(set(p) == keys | {"form"}, "Unexpected parameters")
    if form == "repeated":
        for step in (p["first"], p["second"]):
            require(isinstance(step, list) and len(step) == 2, "Invalid step")
            check_change(step[0], step[1], REPEATED_PERCENTAGES)
        require(overall_multiplier(p) != 1, "The overall change must not be zero")
    elif form == "compound":
        check_change(p["percentage"], p["direction"], COMPOUND_PERCENTAGES)
        require(p["years"] in (2, 3), "Two or three years only")
    else:
        percentage = check_change(p["percentage"], p["direction"], PERCENTAGES[level])
        if level == 4:
            require(p["direction"] in LEVEL_FOUR_DIRECTIONS[percentage],
                    "Percentage paired with the wrong direction for this level")
    if form == "context":
        contexts = FIND_CONTEXTS if forms is FIND_FORMS else INTERPRET_CONTEXTS
        require(p["context"] in range(len(contexts)), "Invalid context")
    if form in ("apply", "apply_reverse"):
        require(type(p["amount"]) is int and 50 <= p["amount"] <= 900 and p["amount"] % 10 == 0,
                "Amount outside bounds")
        require((p["amount"] * overall_multiplier(p) * 100).denominator == 1,
                "Money must be whole pence")
    m = overall_multiplier(p)
    require(m > 0 and m != 1, "Multiplier must be positive and not 1")
    require((m * 10 ** 6).denominator == 1, "Multiplier must be an exact decimal")
    # Overall changes stay readable: at most two decimal places of a percent.
    require((change_of(m)[0] * 100).denominator == 1,
            "Overall percentage needs more than two decimal places")


def draw(rng, level, forms):
    form = rng.choice(forms[level])
    if form == "repeated":
        return {"form": form,
                "first": [rational_text(rng.choice(REPEATED_PERCENTAGES)),
                          rng.choice(("increase", "decrease"))],
                "second": [rational_text(rng.choice(REPEATED_PERCENTAGES)),
                           rng.choice(("increase", "decrease"))]}
    if form == "compound":
        return {"form": form, "percentage": rational_text(rng.choice(COMPOUND_PERCENTAGES)),
                "direction": rng.choice(("increase", "decrease")), "years": rng.choice((2, 3))}
    percentage = rng.choice(PERCENTAGES[level])
    if level == 4:
        direction = rng.choice(LEVEL_FOUR_DIRECTIONS[percentage])
    else:
        direction = rng.choice(("increase", "decrease"))
    p = {"form": form, "percentage": rational_text(percentage), "direction": direction}
    if form == "context":
        contexts = FIND_CONTEXTS if forms is FIND_FORMS else INTERPRET_CONTEXTS
        p["context"] = rng.randrange(len(contexts))
    if form in ("apply", "apply_reverse"):
        p["amount"] = 10 * rng.randint(5, 90)
    return p


# ------------------------------------------------------------ generators

class PercentageMultiplier:
    """Shared construction; each direction of the question is registered separately."""

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        for attempt in range(300):
            p = draw(rng, difficulty, self.forms)
            try:
                check_parameters(p, difficulty, self.forms)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a multiplier question")
        answer, display = answer_for(p, self.asks)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(p, self.asks),
            answer=answer, answer_display=display, worked_solution=(),
            marks=1 if difficulty <= 2 and p["form"] in ("direct", "context") else 2,
            tags=self.info.tags, layout_hint=LayoutHint(working_lines=3), parameters=p,
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in PERCENTAGES, "Invalid difficulty")
        p = question.parameters
        check_parameters(p, level, self.forms)
        answer, display = answer_for(p, self.asks)
        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Displayed answer mismatch")
        require(question.prompt == prompt_for(p, self.asks), "Prompt mismatch")
        return True

    def validate_independently(self, question):
        """Measure the change on a test amount; recompute money from the percentage."""
        import sympy

        p, answer = question.parameters, question.answer
        if answer["kind"] == "money":
            sign = 1 if p["direction"] == "increase" else -1
            factor = 1 + sign * sympy.Rational(p["percentage"]) / 100
            if p["form"] == "apply":
                expected = p["amount"] * factor
            else:
                # The new price is shown; undo the change to recover the original.
                expected = (p["amount"] * factor) / factor
            require(sympy.Rational(answer["value"]) == expected, "Independent money check disagrees")
            return True
        multiplier = sympy.Rational(answer["multiplier"])
        percentage = sympy.Rational(answer["percentage"])
        amount = sympy.Integer(400)
        difference = amount * multiplier - amount
        require(abs(difference) * 100 / amount == percentage,
                "Independent percentage change disagrees")
        require((difference > 0) == (answer["direction"] == "increase"),
                "Direction disagrees with the effect")
        steps = {"repeated": [p.get("first"), p.get("second")]}.get(p["form"])
        if steps:
            product = sympy.Integer(1)
            for value, direction in steps:
                product *= 1 + (1 if direction == "increase" else -1) * sympy.Rational(value) / 100
            require(product == multiplier, "Successive changes disagree")
        if p["form"] == "compound":
            yearly = 1 + (1 if p["direction"] == "increase" else -1) * sympy.Rational(p["percentage"]) / 100
            require(yearly ** p["years"] == multiplier, "Compound multiplier disagrees")
        return True


class FindMultiplier(PercentageMultiplier):
    asks = "multiplier"
    forms = FIND_FORMS
    info = GeneratorInfo(
        id="number.percentages.multiplier", version=2, topic="number",
        subtopic="percentage_change", title="Find and use the multiplier for a percentage change",
        difficulty_descriptions={
            1: "Familiar percentages, bare or in a context.",
            2: "Less familiar percentages, or apply the multiplier to an amount.",
            3: "Percentages with a half, or one multiplier for two successive changes.",
            4: "Changes above 100% or near 100%, or a compound multiplier over years.",
        },
        tags=("percentages", "multiplier", "percentage_change"),
    )


class InterpretMultiplier(PercentageMultiplier):
    asks = "change"
    forms = INTERPRET_FORMS
    info = GeneratorInfo(
        id="number.percentages.interpret_multiplier", version=2, topic="number",
        subtopic="percentage_change",
        title="Interpret a decimal multiplier as a percentage change",
        difficulty_descriptions={
            1: "Familiar multipliers, bare or in a context.",
            2: "Less familiar multipliers, or undo one to find an original price.",
            3: "Multipliers with a half, or the overall change from two multipliers.",
            4: "Multipliers above two or near zero, or the overall change over years.",
        },
        tags=("percentages", "multiplier", "percentage_change", "interpretation"),
    )