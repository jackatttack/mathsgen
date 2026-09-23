"""Compound interest and depreciation, with exact money arithmetic.

Difficulty follows the reasoning required: level 1 finds a grown amount,
level 2 finds a depreciated value, level 3 asks for the total interest or
total loss rather than the final figure, and level 4 asks how many complete
years pass before the value crosses a stated threshold.

Money is held as an exact rational number of pence for every intermediate
year and rounded only once, when the final answer is displayed. This is the
standard convention: rounding each year in turn would give a different and
incorrect figure.
"""
from fractions import Fraction
from math import floor

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .reverse_percentage import money, rate_text


def stated_money(pence):
    """Write a stated sum, dropping ".00" from a whole number of pounds.

    Answers keep their pence, since a money answer is written to the penny,
    but a question states a round sum the way a teacher would write it.
    """
    return "£{}".format(pence // 100) if pence % 100 == 0 else money(pence)


# --- Editable difficulty bounds -------------------------------------------
# Rates are percentages per year. Halves appear from level 3, where the
# arithmetic is no longer the point of the question.
RATES = {
    1: (2, 3, 4, 5, 8, 10),
    2: (10, 12, 15, 20, 25),
    3: (3, 4, 5, Fraction(5, 2), Fraction(15, 2), 12, 15),
    4: (5, 10, 15, 20, 25),
}

YEARS = {1: (2, 3), 2: (2, 3), 3: (3, 4, 5)}

# Principals are round sums a question would realistically state.
PRINCIPAL_POUNDS = (500, 800, 1000, 1200, 1500, 2000, 2500, 3000, 4000, 5000)
DEPRECIATING_POUNDS = (6000, 8000, 9000, 10000, 12000, 15000, 18000, 20000)

GROWTH_CONTEXTS = (
    ("invests", "in a savings account", "the value of the investment"),
    ("puts", "into an account", "the amount in the account"),
)
DECAY_CONTEXTS = (
    ("car", "depreciates"),
    ("van", "depreciates"),
    ("machine", "loses value"),
)

# Thresholds are stated as round sums, tried from coarsest to finest.
THRESHOLD_STEPS = (100000, 50000, 10000)


INFO = GeneratorInfo(
    id="number.percentages.compound_change", version=1,
    topic="number", subtopic="compound_change",
    title="Compound interest and depreciation",
    difficulty_descriptions={
        1: "Find the value of an investment after compound interest.",
        2: "Find the value of an item after depreciation.",
        3: "Find the total interest earned or the total loss in value.",
        4: "Find how many complete years before a value crosses a threshold.",
    },
    tags=("percentages", "compound interest", "depreciation", "money", "exact"),
)


def multiplier_for(rate, direction):
    """The exact yearly multiplier for a percentage rate."""
    change = Fraction(rate, 100)
    return 1 + change if direction == "increase" else 1 - change


def amount_after(principal_pence, rate, direction, years):
    """The exact value in pence after whole years of compound change."""
    return Fraction(principal_pence) * multiplier_for(rate, direction) ** years


def to_nearest_penny(pence):
    """Round an exact quantity of pence to the nearest whole penny."""
    return floor(Fraction(pence) + Fraction(1, 2))


def presentation(parameters):
    principal = parameters["principal_pence"]
    rate = Fraction(parameters["rate"])
    direction = parameters["direction"]
    form = parameters["form"]

    if form == "threshold":
        threshold = stated_money(parameters["threshold_pence"])
        if direction == "increase":
            return Content(
                "An investment of {} grows by {}% compound interest each year. "
                "After how many complete years will it first be worth more "
                "than {}?".format(stated_money(principal), rate_text(rate), threshold)
            )
        item, verb = DECAY_CONTEXTS[parameters["context"]]
        return Content(
            "A {} worth {} {} by {}% each year. After how many complete years "
            "will it first be worth less than {}?".format(
                item, stated_money(principal), verb, rate_text(rate), threshold
            )
        )

    years = parameters["years"]
    rounding = " Give your answer to the nearest penny."

    if direction == "increase":
        verb, place, subject = GROWTH_CONTEXTS[parameters["context"]]
        if form == "total_change":
            return Content(
                "A person {} {} {} paying {}% compound interest each year. "
                "Find the total interest earned after {} years.{}".format(
                    verb, stated_money(principal), place, rate_text(rate),
                    years, rounding
                )
            )
        return Content(
            "A person {} {} {} paying {}% compound interest each year. "
            "Find {} after {} years.{}".format(
                verb, stated_money(principal), place, rate_text(rate),
                subject, years, rounding
            )
        )

    item, decay_verb = DECAY_CONTEXTS[parameters["context"]]
    if form == "total_change":
        return Content(
            "A {} is worth {}. It {} by {}% each year. Find the total loss in "
            "value after {} years.{}".format(
                item, stated_money(principal), decay_verb, rate_text(rate),
                years, rounding
            )
        )
    return Content(
        "A {} is worth {}. It {} by {}% each year. Find its value after "
        "{} years.{}".format(
            item, stated_money(principal), decay_verb, rate_text(rate),
            years, rounding
        )
    )


def first_crossing(parameters, limit=30):
    """The first whole year at which the value passes the threshold."""
    principal = parameters["principal_pence"]
    rate = Fraction(parameters["rate"])
    direction = parameters["direction"]
    threshold = parameters["threshold_pence"]
    for year in range(1, limit + 1):
        value = amount_after(principal, rate, direction, year)
        if direction == "increase" and value > threshold:
            return year
        if direction == "decrease" and value < threshold:
            return year
    raise ValueError("Threshold is never crossed within the supported range")


def answer_for(parameters):
    form = parameters["form"]

    if form == "threshold":
        years = first_crossing(parameters)
        answer = {"kind": "year_count", "years": years}
        return answer, Content("{} years".format(years))

    principal = parameters["principal_pence"]
    exact = amount_after(
        principal, Fraction(parameters["rate"]),
        parameters["direction"], parameters["years"],
    )
    if form == "total_change":
        # The change is the difference, so a loss is reported as a positive
        # amount of money lost rather than a negative value.
        exact = exact - principal if parameters["direction"] == "increase" else (
            principal - exact
        )

    pence = to_nearest_penny(exact)
    answer = {
        "kind": "money_pence", "pence": pence, "exact_pence": rational_text(exact),
    }
    return answer, Content(money(pence))


class CompoundChange:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        parameters = (self.make_threshold(rng) if difficulty == 4
                      else self.make_amount(rng, difficulty))

        prompt = presentation(parameters)
        answer, display = answer_for(parameters)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=3 if difficulty <= 2 else 4, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=4),
            parameters=parameters,
        )
        self.validate(question)
        return question

    def make_amount(self, rng, difficulty):
        direction = "increase" if difficulty == 1 else (
            "decrease" if difficulty == 2 else rng.choice(("increase", "decrease"))
        )
        pounds = (PRINCIPAL_POUNDS if direction == "increase"
                  else DEPRECIATING_POUNDS)
        return {
            "form": "total_change" if difficulty == 3 else "final_amount",
            "direction": direction,
            "principal_pence": rng.choice(pounds) * 100,
            "rate": rational_text(Fraction(rng.choice(RATES[difficulty]))),
            "years": rng.choice(YEARS[difficulty]),
            "context": rng.randrange(
                len(GROWTH_CONTEXTS if direction == "increase" else DECAY_CONTEXTS)
            ),
        }

    def make_threshold(self, rng):
        """Choose a round threshold that lies strictly between two years.

        Strict inequalities on both sides mean the answer is unambiguous: the
        value has not reached the threshold in the previous year and has
        passed it in the answer year.
        """
        for attempt in range(500):
            direction = rng.choice(("increase", "decrease"))
            pounds = (PRINCIPAL_POUNDS if direction == "increase"
                      else DEPRECIATING_POUNDS)
            principal = rng.choice(pounds) * 100
            rate = Fraction(rng.choice(RATES[4]))
            years = rng.randint(2, 6)

            before = amount_after(principal, rate, direction, years - 1)
            after = amount_after(principal, rate, direction, years)
            low, high = (before, after) if direction == "increase" else (after, before)

            for step in THRESHOLD_STEPS:
                first = floor(low / step) + 1
                last = -((-high) // step) - 1
                candidates = [value * step for value in range(first, last + 1)]
                candidates = [
                    value for value in candidates if low < value < high
                ]
                if candidates:
                    threshold = rng.choice(candidates)
                    parameters = {
                        "form": "threshold", "direction": direction,
                        "principal_pence": principal,
                        "rate": rational_text(rate),
                        "threshold_pence": threshold,
                        "context": rng.randrange(len(DECAY_CONTEXTS)),
                    }
                    if first_crossing(parameters) == years:
                        return parameters
                    break
        raise ValueError("Could not construct a suitable threshold question")

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")

        parameters = question.parameters
        expected_form = ("threshold" if level == 4
                         else "total_change" if level == 3 else "final_amount")
        require(parameters.get("form") == expected_form,
                "Form does not match difficulty")
        require(parameters["direction"] in ("increase", "decrease"),
                "Unknown direction")
        if level == 1:
            require(parameters["direction"] == "increase", "Expected growth")
        elif level == 2:
            require(parameters["direction"] == "decrease", "Expected depreciation")

        principal = parameters["principal_pence"]
        require(type(principal) is int and principal > 0
                and principal % 100 == 0, "Principal must be a whole pound amount")

        rate = Fraction(parameters["rate"])
        require(parameters["rate"] == rational_text(rate), "Non-canonical rate")
        require(rate in [Fraction(value) for value in RATES[level]],
                "Rate outside difficulty bounds")
        require(rate > 0, "Rate must be positive")

        if level == 4:
            require(set(parameters) == {
                "form", "direction", "principal_pence", "rate",
                "threshold_pence", "context",
            }, "Unexpected parameters")
            self.check_threshold(parameters)
        else:
            require(set(parameters) == {
                "form", "direction", "principal_pence", "rate", "years", "context",
            }, "Unexpected parameters")
            require(parameters["years"] in YEARS[level],
                    "Year count outside difficulty bounds")

        contexts = (GROWTH_CONTEXTS if parameters["direction"] == "increase"
                    and level != 4 else DECAY_CONTEXTS)
        require(type(parameters["context"]) is int
                and 0 <= parameters["context"] < len(contexts),
                "Context index out of range")

        answer, display = answer_for(parameters)
        if level != 4:
            require(answer["pence"] > 0, "Answer must be a positive amount")
        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Display mismatch")
        require(question.prompt == presentation(parameters), "Prompt mismatch")
        require(question.visual_assets("questions") == ()
                and question.visual_assets("answers") == (),
                "This family uses no visual assets")
        return True

    def check_threshold(self, parameters):
        threshold = parameters["threshold_pence"]
        require(type(threshold) is int and threshold > 0,
                "Threshold must be a positive amount")
        require(threshold % 1000 == 0, "Threshold should be a round sum")
        years = first_crossing(parameters)
        require(2 <= years <= 6, "Crossing year outside difficulty bounds")

        # The year before must genuinely not have crossed, so the answer is
        # unambiguous rather than resting on a rounded comparison.
        before = amount_after(
            parameters["principal_pence"], Fraction(parameters["rate"]),
            parameters["direction"], years - 1,
        )
        if parameters["direction"] == "increase":
            require(before < threshold, "Threshold already passed a year earlier")
            require(parameters["principal_pence"] < threshold,
                    "Threshold is below the starting amount")
        else:
            require(before > threshold, "Threshold already passed a year earlier")
            require(parameters["principal_pence"] > threshold,
                    "Threshold is above the starting value")

    def validate_independently(self, question):
        """Rebuild the value year by year rather than using a single power."""
        import sympy

        parameters = question.parameters
        principal = sympy.Integer(parameters["principal_pence"])
        rate = sympy.Rational(parameters["rate"])
        multiplier = (1 + rate / 100 if parameters["direction"] == "increase"
                      else 1 - rate / 100)

        def value_after(years):
            # Exact rational arithmetic throughout: no float approximation,
            # and no rounding until the final answer is displayed.
            value = principal
            for _ in range(years):
                value *= multiplier
            return value

        if parameters["form"] == "threshold":
            threshold = sympy.Integer(parameters["threshold_pence"])
            submitted = question.answer["years"]
            require(type(submitted) is int and submitted >= 1,
                    "Year count must be a positive integer")
            for year in range(1, submitted):
                value = value_after(year)
                crossed = (value > threshold
                           if parameters["direction"] == "increase"
                           else value < threshold)
                require(not crossed, "An earlier year already crossed the threshold")
            final = value_after(submitted)
            crossed = (final > threshold if parameters["direction"] == "increase"
                       else final < threshold)
            require(crossed, "The stated year does not cross the threshold")
            return True

        exact = value_after(parameters["years"])
        if parameters["form"] == "total_change":
            exact = (exact - principal if parameters["direction"] == "increase"
                     else principal - exact)
        require(sympy.simplify(exact - sympy.Rational(
            question.answer["exact_pence"]
        )) == 0, "Independent compound calculation disagrees")

        # Check the rounding separately: the stated pence must be within half
        # a penny of the exact value.
        difference = sympy.Rational(question.answer["pence"]) - exact
        require(abs(difference) <= sympy.Rational(1, 2),
                "Answer is not rounded to the nearest penny")
        return True