"""IB AI SL binomial distribution in context.

Probabilities are exact Fractions from n choose r; the independent check
builds the distribution with the recurrence P(r + 1) = P(r) (n - r) p /
((r + 1)(1 - p)) in floats instead.
"""
from fractions import Fraction
from math import comb

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from ..rounding import decimal_text
from . import common as ib


# --- Editable pools ---------------------------------------------------------
CONTEXTS = {
    "chocolates": {"probabilities": ("1/20", "1/25", "1/40", "1/50"), "noun": "chocolates",
                   "plural_verb": "are flawed", "single_verb": "is flawed",
                   "sizes": tuple(range(10, 31))},
    "seeds": {"probabilities": ("0.7", "0.75", "0.8", "0.85", "0.9"), "noun": "seeds",
              "plural_verb": "germinate", "single_verb": "germinates",
              "sizes": tuple(range(8, 21))},
    "bulbs": {"probabilities": ("0.02", "0.03", "0.04", "0.05", "0.08"), "noun": "bulbs",
              "plural_verb": "are faulty", "single_verb": "is faulty",
              "sizes": tuple(range(10, 41))},
    "throws": {"probabilities": ("0.35", "0.4", "0.45", "0.55", "0.6", "0.65"),
               "noun": "throws", "plural_verb": "score", "single_verb": "scores",
               "sizes": tuple(range(6, 16))},
}
# Level 4 asks for the least sample with at least one success; that needs a
# small enough probability to be a real question.
LEAST_N_CONTEXTS = ("chocolates", "bulbs", "throws")
KINDS = {"more_than": "more than", "at_most": "at most", "at_least": "at least"}
THRESHOLDS = ("0.8", "0.9", "0.95", "0.99")


# ------------------------------------------------------------ mathematics

def pmf(n, p, r):
    return comb(n, r) * p ** r * (1 - p) ** (n - r)


def cumulative(n, p, kind, r):
    if kind == "exactly":
        return pmf(n, p, r)
    if kind == "at_most":
        return sum(pmf(n, p, k) for k in range(0, r + 1))
    if kind == "at_least":
        return sum(pmf(n, p, k) for k in range(r, n + 1))
    return sum(pmf(n, p, k) for k in range(r + 1, n + 1))


def least_sample(p, threshold):
    """Fewest trials with P(at least one) greater than threshold."""
    n = 1
    while 1 - (1 - p) ** n <= threshold:
        n += 1
        require(n <= 400, "Sample size out of reach")
    return n


def opening(context, name, probability, n):
    p = Fraction(probability)
    if context == "chocolates":
        return ("On average, one in {} of the chocolates made by a small shop is flawed, "
                "independently of all the others. A box contains {} chocolates.".format(
                    p.denominator, n))
    if context == "seeds":
        return ("The probability that a seed of a certain plant germinates is {}, independently "
                "of other seeds. {} plants {} of these seeds.".format(probability, name, n))
    if context == "bulbs":
        return ("{}% of the light bulbs made by a factory are faulty, independently of each "
                "other. A pack contains {} bulbs.".format(decimal_text(p * 100), n))
    return ("{} scores with {}% of free throws, independently of each other. {} takes {} free "
            "throws.".format(name, decimal_text(p * 100), name, n))


# ------------------------------------------------------------ generator

class BinomialDistribution(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.statistics.binomial",
        version=1,
        topic=ib.TOPIC,
        subtopic="statistics_and_probability",
        title="Binomial distribution",
        difficulty_descriptions={
            1: "Probability of exactly r successes.",
            2: "Exactly r, then more than, at most or at least r.",
            3: "A cumulative probability, the expected number and the variance.",
            4: "More than r, the least sample size for at least one, and above the mean.",
        },
        tags=ib.BASE_TAGS + ("binomial", "probability", "expected_value"),
    )
    keys = {
        1: {"context", "name", "probability", "n", "r"},
        2: {"context", "name", "probability", "n", "r", "kind", "r2"},
        3: {"context", "name", "probability", "n", "kind", "r"},
        4: {"context", "name", "probability", "n", "r", "threshold"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        context = rng.choice(LEAST_N_CONTEXTS if level == 4 else tuple(CONTEXTS))
        c = CONTEXTS[context]
        n = rng.choice(c["sizes"])
        p = {"context": context, "name": rng.choice(ib.NAMES),
             "probability": rng.choice(c["probabilities"]), "n": n, "r": rng.randint(0, n // 2)}
        if level == 2:
            p.update(kind=rng.choice(tuple(KINDS)), r2=rng.randint(1, n - 1))
        elif level == 3:
            p["kind"] = rng.choice(("at_most", "at_least"))
        elif level == 4:
            p["threshold"] = rng.choice(THRESHOLDS)
        return p

    def check_rules(self, p, level):
        require(p["context"] in CONTEXTS, "Unknown context")
        c = CONTEXTS[p["context"]]
        require(p["name"] in ib.NAMES, "Unknown name")
        require(p["probability"] in c["probabilities"], "Probability outside pool")
        require(p["n"] in c["sizes"], "Sample size outside pool")
        n, chance = p["n"], Fraction(p["probability"])
        ib.require_int(p["r"], 0, n, "r outside bounds")
        sensible = lambda value: Fraction(1, 1000) <= value <= Fraction(999, 1000)
        if level in (1, 2):
            require(sensible(pmf(n, chance, p["r"])), "Probability too extreme")
        if level == 2:
            require(p["kind"] in KINDS, "Unknown kind")
            ib.require_int(p["r2"], 1, n - 1, "r2 outside bounds")
            require(p["r2"] != p["r"], "Parts must use different values")
            require(sensible(cumulative(n, chance, p["kind"], p["r2"])), "Probability too extreme")
        if level == 3:
            require(p["kind"] in ("at_most", "at_least"), "Unknown kind")
            require(sensible(cumulative(n, chance, p["kind"], p["r"])), "Probability too extreme")
        if level == 4:
            require(p["context"] in LEAST_N_CONTEXTS, "Context unsuitable for level 4")
            require(p["threshold"] in THRESHOLDS, "Threshold outside pool")
            require(sensible(cumulative(n, chance, "more_than", p["r"])), "Probability too extreme")
            require(2 <= least_sample(chance, Fraction(p["threshold"])) <= 300,
                    "Least sample outside bounds")
            mean = n * chance
            require(sensible(sum(pmf(n, chance, k) for k in range(n + 1) if k > mean)),
                    "Probability too extreme")

    def parts(self, p, level):
        c = CONTEXTS[p["context"]]
        n, chance = p["n"], Fraction(p["probability"])
        context = [opening(p["context"], p["name"], p["probability"], n)]

        def task(kind, r):
            how = "exactly {}".format(r) if kind == "exactly" else "{} {}".format(KINDS[kind], r)
            return "Find the probability that {} of the {} {}.".format(how, c["noun"], c["plural_verb"])

        def probability_part(label, kind, r, marks=2):
            value = cumulative(n, chance, kind, r)
            return ib.part(label, task(kind, r), marks, ib.sf3(value), value)

        if level == 1:
            return ib.assemble(context, [probability_part("a", "exactly", p["r"])])
        if level == 2:
            return ib.assemble(context, [probability_part("a", "exactly", p["r"]),
                                         probability_part("b", p["kind"], p["r2"])])
        if level == 3:
            mean, variance = n * chance, n * chance * (1 - chance)
            return ib.assemble(context, [
                probability_part("a", p["kind"], p["r"]),
                ib.part("b", "Find the expected number of {} that {}.".format(
                    c["noun"], c["plural_verb"]), 1, ib.nice(mean), mean),
                ib.part("c", "Find the variance of the number of {} that {}.".format(
                    c["noun"], c["plural_verb"]), 1, ib.nice(variance), variance),
            ])
        least = least_sample(chance, Fraction(p["threshold"]))
        mean = n * chance
        above_mean = sum(pmf(n, chance, k) for k in range(n + 1) if k > mean)
        return ib.assemble(context, [
            probability_part("a", "more_than", p["r"]),
            ib.part("b", "Find the least number of {} needed for the probability that at least "
                    "one {} to be greater than {}.".format(c["noun"], c["single_verb"],
                                                          p["threshold"]), 3,
                    "{} {}".format(least, c["noun"]), least),
            ib.part("c", "For the original {} {}, find the probability that the number that {} "
                    "is greater than the mean.".format(n, c["noun"], c["plural_verb"]), 2,
                    ib.sf3(above_mean), above_mean),
        ])

    def validate_independently(self, question):
        """Build the distribution by recurrence in floats; count trials with logarithms."""
        import math
        p, level = question.parameters, question.difficulty
        values = ib.answer_values(question)
        n, chance = p["n"], float(Fraction(p["probability"]))
        table = [(1 - chance) ** n]
        for r in range(n):
            table.append(table[-1] * (n - r) * chance / ((r + 1) * (1 - chance)))
        pick = {
            "exactly": lambda r: table[r],
            "at_most": lambda r: sum(table[:r + 1]),
            "at_least": lambda r: sum(table[r:]),
            "more_than": lambda r: sum(table[r + 1:]),
        }
        if level == 1:
            require(ib.close(values["a"], pick["exactly"](p["r"]), 1e-8), "Independent pmf failed")
        elif level == 2:
            require(ib.close(values["a"], pick["exactly"](p["r"]), 1e-8)
                    and ib.close(values["b"], pick[p["kind"]](p["r2"]), 1e-8),
                    "Independent probabilities failed")
        elif level == 3:
            require(ib.close(values["a"], pick[p["kind"]](p["r"]), 1e-8), "Independent cumulative failed")
            require(ib.close(values["b"], n * chance) and ib.close(values["c"], n * chance * (1 - chance)),
                    "Independent mean or variance failed")
        else:
            require(ib.close(values["a"], pick["more_than"](p["r"]), 1e-8), "Independent tail failed")
            least = math.floor(math.log(1 - float(Fraction(p["threshold"]))) / math.log(1 - chance)) + 1
            require(Fraction(values["b"]) == least, "Independent least sample failed")
            above = sum(value for k, value in enumerate(table) if k > n * chance)
            require(ib.close(values["c"], above, 1e-8), "Independent above-mean failed")
        return True