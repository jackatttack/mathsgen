"""Simple interest, where the interest is the same every year.

Compound interest is already covered by number.percentages.compound_change.
Simple interest is a separate family, not a level of it: the interest is
calculated on the original amount every year, never on the running total,
and the misconception is treating one as the other. The two are examined
together precisely because students confuse them.

Difficulty follows the unknown: the interest, then the total, then the rate
or the time recovered from the interest, then a comparison against compound
interest over the same period.
"""
from fractions import Fraction
from math import floor

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .reverse_percentage import money, rate_text
from .compound_interest import stated_money, to_nearest_penny


INFO = GeneratorInfo(
    id="number.percentages.simple_interest", version=1,
    topic="number", subtopic="interest",
    title="Simple interest",
    difficulty_descriptions={
        1: "Find the total interest earned over several years.",
        2: "Find the final balance after several years.",
        3: "Find the rate or the number of years from the interest earned.",
        4: "Compare simple interest with compound interest.",
    },
    tags=("percentages", "simple interest", "money", "exact"),
)

# --- Editable difficulty bounds -------------------------------------------
PRINCIPAL_POUNDS = (400, 500, 800, 1000, 1200, 1500, 2000, 2500, 3000, 5000)
RATES = {
    1: (2, 3, 4, 5, 10),
    2: (2, 3, 4, 5, 6, 8),
    3: (2, 4, 5, 8, 10),
    4: (5, 10, 20),
}
YEARS = {1: (3, 4, 5), 2: (2, 3, 4), 3: (3, 4, 5, 6), 4: (2, 3)}

ACCOUNTS = (
    ("invests", "in an account paying simple interest"),
    ("puts", "into a savings account paying simple interest"),
)


def yearly_interest(principal_pence, rate):
    """The same amount every year: a percentage of the ORIGINAL sum."""
    return Fraction(principal_pence) * Fraction(rate, 100)


def total_interest(p):
    return yearly_interest(p["principal_pence"], Fraction(p["rate"])) * p["years"]


def compound_total(p):
    """The balance the same money would reach under compound interest."""
    # The rate is stored as canonical text, so it is converted before use:
    # Fraction(text, 100) is invalid, since the two-argument form needs
    # numbers on both sides.
    multiplier = 1 + Fraction(p["rate"]) / 100
    return Fraction(p["principal_pence"]) * multiplier ** p["years"]


def answer_value(p):
    form = p["form"]
    if form == "interest":
        return total_interest(p)
    if form == "balance":
        return Fraction(p["principal_pence"]) + total_interest(p)
    if form == "rate":
        return Fraction(p["rate"])
    if form == "years":
        return Fraction(p["years"])
    # The difference between compound and simple over the same period.
    simple = Fraction(p["principal_pence"]) + total_interest(p)
    return compound_total(p) - simple


def presentation(p):
    principal = stated_money(p["principal_pence"])
    rate = rate_text(Fraction(p["rate"]))
    verb, place = ACCOUNTS[p["context"]]
    form = p["form"]

    if form == "interest":
        return Content(
            "A person {} {} {} at {}% per year. Find the total interest "
            "earned after {} years.".format(
                verb, principal, place, rate, p["years"]
            )
        )
    if form == "balance":
        return Content(
            "A person {} {} {} at {}% per year. Find the balance after "
            "{} years.".format(verb, principal, place, rate, p["years"])
        )
    # A sum stated inside a question drops ".00", as a teacher would write
    # it; the ANSWER keeps its pence, since a money answer is written to
    # the penny.
    if form == "rate":
        return Content(
            "A person {} {} {}. After {} years the total interest earned is "
            "{}. Find the annual rate of interest.".format(
                verb, principal, place, p["years"],
                stated_money(to_nearest_penny(total_interest(p))),
            )
        )
    if form == "years":
        return Content(
            "A person {} {} {} at {}% per year. The total interest earned is "
            "{}. Find the number of years.".format(
                verb, principal, place, rate,
                stated_money(to_nearest_penny(total_interest(p))),
            )
        )
    return Content(
        "A person has {} to invest for {} years. One account pays {}% simple "
        "interest per year; another pays {}% compound interest per year. "
        "Find how much more the compound account is worth at the end.".format(
            principal, p["years"], rate, rate
        )
    )


def answer_for(p):
    value = answer_value(p)
    form = p["form"]

    if form in ("rate",):
        answer = {"kind": "percentage", "value": rational_text(value)}
        return answer, Content("{}%".format(rate_text(value)))
    if form == "years":
        answer = {"kind": "integer", "value": int(value)}
        return answer, Content("{} years".format(int(value)))

    pence = to_nearest_penny(value)
    answer = {
        "kind": "money_pence", "pence": pence, "exact_pence": rational_text(value),
    }
    return answer, Content(money(pence))


class SimpleInterest:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng

        form = {
            1: "interest", 2: "balance", 4: "comparison",
        }.get(difficulty) or rng.choice(("rate", "years"))

        p = {
            "form": form,
            "context": rng.randrange(len(ACCOUNTS)),
            "principal_pence": rng.choice(PRINCIPAL_POUNDS) * 100,
            "rate": rational_text(Fraction(rng.choice(RATES[difficulty]))),
            "years": rng.choice(YEARS[difficulty]),
        }

        prompt = presentation(p)
        answer, display = answer_for(p)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=2 if difficulty <= 2 else 4 if difficulty == 4 else 3,
            tags=self.info.tags, layout_hint=LayoutHint(working_lines=4),
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
        require(set(p) == {
            "form", "context", "principal_pence", "rate", "years",
        }, "Unexpected parameters")

        expected = {
            1: ("interest",), 2: ("balance",),
            3: ("rate", "years"), 4: ("comparison",),
        }[level]
        require(p["form"] in expected, "Form does not match difficulty")
        require(p["context"] in range(len(ACCOUNTS)), "Unknown context")

        principal = p["principal_pence"]
        require(type(principal) is int and principal > 0
                and principal % 100 == 0, "Principal must be whole pounds")

        rate = Fraction(p["rate"])
        require(p["rate"] == rational_text(rate), "Non-canonical rate")
        require(rate in [Fraction(v) for v in RATES[level]],
                "Rate outside difficulty bounds")
        require(p["years"] in YEARS[level], "Years outside difficulty bounds")

        # Every yearly interest must be a whole number of pence, or the
        # question would state an amount that cannot be paid.
        yearly = yearly_interest(principal, rate)
        require(yearly.denominator == 1, "Yearly interest is not whole pence")

        answer, display = answer_for(p)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Display mismatch")
        require(q.prompt == presentation(p), "Prompt mismatch")
        require(q.visual_assets("questions") == ()
                and q.visual_assets("answers") == (),
                "This family uses no visual assets")

        if p["form"] == "comparison":
            # Compound must genuinely exceed simple, or there is nothing
            # to find.
            require(Fraction(answer["exact_pence"]) > 0,
                    "Compound interest should exceed simple interest")
        return True

    def validate_independently(self, q):
        """Add the interest year by year instead of multiplying.

        Simple interest adds the same amount each year, so summing those
        amounts is a different route from multiplying one year's interest
        by the number of years.
        """
        import sympy

        p = q.parameters
        principal = sympy.Rational(p["principal_pence"])
        rate = sympy.Rational(p["rate"])
        years = p["years"]

        running = sympy.Integer(0)
        for _ in range(years):
            running += principal * rate / 100
        expected_interest = running

        form = p["form"]
        if form == "interest":
            expected = expected_interest
        elif form == "balance":
            expected = principal + expected_interest
        elif form == "rate":
            require(sympy.Rational(q.answer["value"]) == rate,
                    "Independent rate disagrees")
            return True
        elif form == "years":
            require(q.answer["value"] == years,
                    "Independent year count disagrees")
            return True
        else:
            # Compound, accumulated year by year rather than as a power.
            balance = principal
            for _ in range(years):
                balance = balance * (1 + rate / 100)
            expected = balance - (principal + expected_interest)

        require(sympy.simplify(
            sympy.Rational(q.answer["exact_pence"]) - expected
        ) == 0, "Independent year-by-year total disagrees")
        difference = sympy.Rational(q.answer["pence"]) - expected
        require(abs(difference) <= sympy.Rational(1, 2),
                "Answer is not rounded to the nearest penny")
        return True