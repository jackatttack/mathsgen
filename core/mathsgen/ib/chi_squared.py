"""IB AI SL chi-squared tests: independence (levels 1 to 3) and goodness
of fit (level 4).

Observed tables are drawn from row and column weights with an optional
association, so some tests reject H0 and some do not. Every expected
frequency is at least 5, as IB requires. Results near the critical value
or near the significance level are rejected, so a conclusion never hangs
on rounding. The statistic is an exact Fraction; the p-value uses mpmath.
"""
from fractions import Fraction

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from . import common as ib
from . import distributions as dist


# --- Editable pools ---------------------------------------------------------
INDEPENDENCE = {
    "peppers": {"intro": "A farmer sorts {} peppers by colour and size.",
                "row": ("Colour", ("Red", "Green", "Yellow")),
                "column": ("Size", ("Small", "Medium", "Large")), "pair": "colour and size"},
    "transport": {"intro": "A school asks {} students for their year group and how they usually "
                           "travel to school.",
                  "row": ("Year group", ("Year 9", "Year 10", "Year 11")),
                  "column": ("Travel", ("Walk", "Bus", "Car")),
                  "pair": "year group and method of travel"},
    "drinks": {"intro": "A café records the age group and drink choice of {} customers.",
               "row": ("Age group", ("Under 30", "30 to 50", "Over 50")),
               "column": ("Drink", ("Coffee", "Tea", "Juice")),
               "pair": "age group and choice of drink"},
    "sport": {"intro": "{} students from two schools are asked for their favourite sport.",
              "row": ("School", ("School A", "School B")),
              "column": ("Sport", ("Football", "Tennis", "Swimming", "Basketball")),
              "pair": "school and favourite sport"},
    "pets": {"intro": "{} adults are asked where they live and which pet they prefer.",
             "row": ("Home", ("City", "Countryside")), "column": ("Pet", ("Cat", "Dog")),
             "pair": "where people live and preferred pet"},
}
GOODNESS = {
    "die": {"label": "Score", "categories": ("1", "2", "3", "4", "5", "6"),
            "claims": ((1, 1, 1, 1, 1, 1),), "multipliers": tuple(range(10, 31, 5))},
    "flowers": {"label": "Colour", "categories": ("Red", "Yellow", "White"),
                "claims": ((1, 2, 2), (2, 3, 5), (1, 1, 2), (3, 4, 5)),
                "multipliers": tuple(range(10, 31))},
    "devices": {"label": "Device", "categories": ("Phone", "Laptop", "Tablet", "Other"),
                "claims": ((45, 30, 15, 10), (50, 25, 15, 10), (40, 35, 15, 10)),
                "multipliers": (2, 3, 4)},
}
# Upper 1%, 5% and 10% points of chi-squared, by degrees of freedom.
CRITICAL = {
    "5": {1: "3.841", 2: "5.991", 3: "7.815", 4: "9.488", 5: "11.070", 6: "12.592"},
}
ALPHAS = ("1", "5", "10")
# Relative noise on each cell. The smallest still gives a natural-looking
# table; larger ones create a real association.
EFFECTS = (0.1, 0.12, 0.15, 0.25, 0.35, 0.5)
# Tables fitting the null hypothesis this well look artificial.
MOST_PERFECT_P = Fraction(95, 100)


# ------------------------------------------------------------ mathematics

def expected_table(counts):
    rows = [sum(row) for row in counts]
    columns = [sum(column) for column in zip(*counts)]
    total = sum(rows)
    return [[Fraction(r * c, total) for c in columns] for r in rows]


def statistic(observed, expected):
    return sum((Fraction(o) - e) ** 2 / e for o, e in zip(observed, expected))


def flatten(table):
    return [value for row in table for value in row]


def goodness_expected(p):
    claim = GOODNESS[p["context"]]["claims"][p["claim"]]
    total = sum(p["counts"])
    return [Fraction(total * weight, sum(claim)) for weight in claim]


def claim_text(p):
    claim = GOODNESS[p["context"]]["claims"][p["claim"]]
    if p["context"] == "flowers":
        return ":".join(str(w) for w in claim)
    if p["context"] == "devices":
        shares = ["{}%".format(w) for w in claim]
        return ", ".join(shares[:-1]) + " and " + shares[-1]
    return ""


def goodness_hypotheses(p):
    if p["context"] == "die":
        return "H0: the die is fair. H1: the die is not fair."
    if p["context"] == "flowers":
        ratio = claim_text(p)
        return ("H0: the colours are in the ratio {0}. H1: the colours are not in the ratio "
                "{0}.".format(ratio))
    return ("H0: the website's claimed percentages are correct. H1: the claimed percentages "
            "are not correct.")


def conclusion(reject, reason, evidence):
    if reject:
        return "Reject H0, since {}. There is evidence that {}.".format(reason, evidence)
    return "Do not reject H0, since {}. There is insufficient evidence that {}.".format(
        reason, evidence)


def table_lines(title, column_labels, row_labels, rows):
    lines = [" | ".join([title] + list(column_labels))]
    for label, row in zip(row_labels, rows):
        lines.append(" | ".join([label] + [str(v) for v in row]))
    return lines


# ------------------------------------------------------------ generator

class ChiSquaredTests(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.statistics.chi_squared",
        version=1,
        topic=ib.TOPIC,
        subtopic="statistics_and_probability",
        title="Chi-squared tests",
        difficulty_descriptions={
            1: "Independence: hypotheses, one expected frequency and degrees of freedom.",
            2: "Independence test at 5% using a given critical value.",
            3: "Independence test using the p-value at 1%, 5% or 10%.",
            4: "Goodness of fit: expected frequencies, statistic, p-value and conclusion.",
        },
        tags=ib.BASE_TAGS + ("chi_squared", "hypothesis_testing", "independence",
                             "goodness_of_fit"),
    )
    keys = {
        1: {"context", "counts", "cell"},
        2: {"context", "counts"},
        3: {"context", "counts", "alpha"},
        4: {"context", "claim", "counts"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        effect = rng.choice(EFFECTS)
        if level == 4:
            context = rng.choice(tuple(GOODNESS))
            g = GOODNESS[context]
            claim_index = rng.randrange(len(g["claims"]))
            claim = g["claims"][claim_index]
            total = sum(claim) * rng.choice(g["multipliers"])
            counts = [max(1, round(total * w / sum(claim) * (1 + effect * rng.uniform(-1, 1))))
                      for w in claim]
            counts[-1] += total - sum(counts)
            return {"context": context, "claim": claim_index, "counts": counts}
        context = rng.choice(tuple(INDEPENDENCE))
        c = INDEPENDENCE[context]
        rows, columns = len(c["row"][1]), len(c["column"][1])
        size = rng.randint(120, 400)
        row_weights = [rng.randint(2, 5) for _ in range(rows)]
        column_weights = [rng.randint(2, 5) for _ in range(columns)]
        counts = [[max(1, round(size * rw / sum(row_weights) * cw / sum(column_weights)
                                * (1 + effect * rng.uniform(-1, 1))))
                   for cw in column_weights] for rw in row_weights]
        p = {"context": context, "counts": counts}
        if level == 1:
            p["cell"] = [rng.randrange(rows), rng.randrange(columns)]
        elif level == 3:
            p["alpha"] = rng.choice(ALPHAS)
        return p

    def check_rules(self, p, level):
        if level == 4:
            require(p["context"] in GOODNESS, "Unknown context")
            g = GOODNESS[p["context"]]
            require(type(p["claim"]) is int and 0 <= p["claim"] < len(g["claims"]), "Unknown claim")
            counts = p["counts"]
            require(isinstance(counts, list) and len(counts) == len(g["categories"]),
                    "Counts do not match the categories")
            require(all(type(v) is int and 1 <= v <= 1000 for v in counts), "Counts outside rules")
            expected = goodness_expected(p)
            require(sum(counts) % sum(g["claims"][p["claim"]]) == 0, "Total must give whole expectations")
            require(all(e >= 5 for e in expected), "Expected frequencies below 5")
            value = dist.chi_squared_upper(statistic(counts, expected), len(counts) - 1)
            require(value <= MOST_PERFECT_P, "Observed counts fit too perfectly")
            require(abs(value - Fraction(5, 100)) >= Fraction(5, 1000), "p-value too near 5%")
            return
        require(p["context"] in INDEPENDENCE, "Unknown context")
        c = INDEPENDENCE[p["context"]]
        rows, columns = len(c["row"][1]), len(c["column"][1])
        counts = p["counts"]
        require(isinstance(counts, list) and len(counts) == rows
                and all(isinstance(row, list) and len(row) == columns for row in counts),
                "Table shape does not match the context")
        require(all(type(v) is int and 1 <= v <= 400 for v in flatten(counts)), "Counts outside rules")
        expected = expected_table(counts)
        require(all(e >= 5 for e in flatten(expected)), "Expected frequencies below 5")
        value = statistic(flatten(counts), flatten(expected))
        df = (rows - 1) * (columns - 1)
        require(dist.chi_squared_upper(value, df) <= MOST_PERFECT_P, "Table fits too perfectly")
        if level == 1:
            cell = p["cell"]
            require(isinstance(cell, list) and len(cell) == 2
                    and type(cell[0]) is int and 0 <= cell[0] < rows
                    and type(cell[1]) is int and 0 <= cell[1] < columns, "Cell outside table")
        elif level == 2:
            critical = Fraction(CRITICAL["5"][df])
            require(abs(value - critical) >= Fraction(1, 4), "Statistic too near the critical value")
        else:
            require(p["alpha"] in ALPHAS, "Significance level outside pool")
            upper = dist.chi_squared_upper(value, df)
            require(abs(upper - Fraction(p["alpha"]) / 100) >= Fraction(5, 1000),
                    "p-value too near the significance level")

    def parts(self, p, level):
        if level == 4:
            return self.goodness_parts(p)
        c = INDEPENDENCE[p["context"]]
        (row_title, row_labels), (column_title, column_labels) = c["row"], c["column"]
        counts = p["counts"]
        total = sum(flatten(counts))
        expected = expected_table(counts)
        df = (len(row_labels) - 1) * (len(column_labels) - 1)
        value = statistic(flatten(counts), flatten(expected))
        context = [c["intro"].format(total)]
        context += table_lines(row_title + " / " + column_title, column_labels, row_labels, counts)
        hypotheses = "H0: {0} are independent. H1: {0} are not independent.".format(c["pair"])
        evidence = "{} are not independent".format(c["pair"])
        hypothesis_part = ib.part("a", "State the null and alternative hypotheses for a test of "
                                  "whether {} are independent.".format(c["pair"]),
                                  1 if level != 2 else 2, hypotheses)

        if level == 1:
            i, j = p["cell"]
            cell = expected[i][j]
            return ib.assemble(context, [
                hypothesis_part,
                ib.part("b", "Find the expected frequency for {} and {}.".format(
                    row_labels[i], column_labels[j]), 2, ib.nice(cell), cell),
                ib.part("c", "Write down the number of degrees of freedom.", 1, str(df), df),
            ])
        if level == 2:
            critical = CRITICAL["5"][df]
            reject = value > Fraction(critical)
            reason = "{} {} {}".format(ib.sf3(value), ">" if reject else "<", critical)
            return ib.assemble(context, [
                hypothesis_part,
                ib.part("b", "The test is carried out at the 5% significance level. Find the "
                        "chi-squared statistic.", 2, ib.sf3(value), value),
                ib.part("c", "The critical value is {}. State the conclusion of the test, giving "
                        "a reason.".format(critical), 2, conclusion(reject, reason, evidence)),
            ])
        upper = dist.chi_squared_upper(value, df)
        alpha = Fraction(p["alpha"]) / 100
        reject = upper < alpha
        reason = "p = {} {} {}".format(ib.sf3(upper), "<" if reject else ">", ib.exact_text(alpha))
        return ib.assemble(context, [
            hypothesis_part,
            ib.part("b", "Write down the number of degrees of freedom.", 1, str(df), df),
            ib.part("c", "Find the chi-squared statistic and the p-value.", 3,
                    "chi-squared = {}, p = {}".format(ib.sf3(value), ib.sf3(upper)), upper),
            ib.part("d", "State the conclusion of the test at the {}% significance level, "
                    "giving a reason.".format(p["alpha"]), 2, conclusion(reject, reason, evidence)),
        ])

    def goodness_parts(self, p):
        g = GOODNESS[p["context"]]
        counts = p["counts"]
        total = sum(counts)
        expected = goodness_expected(p)
        df = len(counts) - 1
        value = statistic(counts, expected)
        upper = dist.chi_squared_upper(value, df)
        reject = upper < Fraction(5, 100)
        if p["context"] == "die":
            intro = "A die is rolled {} times to test whether it is fair.".format(total)
            evidence = "the die is not fair"
        elif p["context"] == "flowers":
            intro = ("A seed company claims that its mixed packets grow red, yellow and white "
                     "flowers in the ratio {}. {} flowers are grown from these packets.".format(
                         claim_text(p), total))
            evidence = "the colours are not in the claimed ratio"
        else:
            intro = ("A website claims that its visitors use a phone, a laptop, a tablet or "
                     "another device in the percentages {}. The devices of {} visitors are "
                     "recorded.".format(claim_text(p), total))
            evidence = "the claimed percentages are not correct"
        context = [intro] + table_lines(g["label"], g["categories"], ["Observed"], [counts])
        reason = "p = {} {} 0.05".format(ib.sf3(upper), "<" if reject else ">")
        return ib.assemble(context, [
            ib.part("a", "State the null and alternative hypotheses for a chi-squared goodness of "
                    "fit test.", 1, goodness_hypotheses(p)),
            ib.part("b", "Find the expected frequencies.", 2,
                    ", ".join("{} {}".format(label, ib.nice(e))
                              for label, e in zip(g["categories"], expected)), expected[0]),
            ib.part("c", "Write down the number of degrees of freedom.", 1, str(df), df),
            ib.part("d", "Find the chi-squared statistic and the p-value.", 3,
                    "chi-squared = {}, p = {}".format(ib.sf3(value), ib.sf3(upper)), upper),
            ib.part("e", "State the conclusion of the test at the 5% significance level, giving "
                    "a reason.", 2, conclusion(reject, reason, evidence)),
        ])

    def validate_independently(self, question):
        """Use sum(O^2/E) - N and integrate the chi-squared density."""
        p, level = question.parameters, question.difficulty
        values, shown = ib.answer_values(question), ib.answer_shown(question)
        if level == 4:
            counts = p["counts"]
            claim = GOODNESS[p["context"]]["claims"][p["claim"]]
            total = float(sum(counts))
            expected = [total * w / sum(claim) for w in claim]
            df = len(counts) - 1
            require(ib.close(values["b"], expected[0]), "Independent expectation failed")
            label = "d"
        else:
            counts = p["counts"]
            rows = [sum(r) for r in counts]
            columns = [sum(c) for c in zip(*counts)]
            total = float(sum(rows))
            expected = [rows[i] * columns[j] / total for i in range(len(rows))
                        for j in range(len(columns))]
            counts = flatten(counts)
            df = (len(rows) - 1) * (len(columns) - 1)
            if level == 1:
                i, j = p["cell"]
                require(ib.close(values["b"], rows[i] * columns[j] / total), "Independent cell failed")
                require(Fraction(values["c"]) == df, "Independent df failed")
                return True
            label = "b" if level == 2 else "c"
        value = sum(o * o / e for o, e in zip(counts, expected)) - total
        if level == 2:
            require(ib.close(values["b"], value, 1e-8), "Independent statistic failed")
            # The table's critical value really is the upper 5% point.
            critical = float(CRITICAL["5"][df])
            require(abs(dist.chi_squared_upper_by_integration(critical, df) - 0.05) < 5e-5,
                    "Critical value table wrong")
            require(shown["c"].startswith("Reject") == (value > critical), "Independent conclusion failed")
            return True
        upper = dist.chi_squared_upper_by_integration(value, df)
        require(ib.close(values[label], upper, 1e-6), "Independent p-value failed")
        alpha = 0.05 if level == 4 else float(Fraction(p["alpha"])) / 100
        final = "e" if level == 4 else "d"
        require(shown[final].startswith("Reject") == (upper < alpha), "Independent conclusion failed")
        return True