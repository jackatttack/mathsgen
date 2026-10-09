"""IB AI SL two-sample t-test (pooled, equal population variances).

The tail comes from the wording: "higher than" gives H1: mu_A > mu_B,
"lower than" gives <, "different from" gives two tails. Samples are drawn
around a centre with an optional true shift, so some tests reject H0 and
some do not; p-values within 0.005 of the significance level are rejected.
"""
from fractions import Fraction

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from ..rounding import decimal_text
from . import common as ib
from . import distributions as dist


# --- Editable pools ---------------------------------------------------------
CONTEXTS = {
    "revision": {"group_a": "students who revise with music",
                 "group_b": "students who revise in silence",
                 "label_a": "Music", "label_b": "Silence", "measure": "test score", "unit": "",
                 "centres": tuple(range(55, 81)), "spreads": tuple(range(6, 13)), "places": 0},
    "fertiliser": {"group_a": "plants given a new fertiliser",
                   "group_b": "plants given no fertiliser",
                   "label_a": "Fertiliser", "label_b": "No fertiliser", "measure": "height",
                   "unit": "cm", "centres": tuple(range(20, 36)), "spreads": (2, 3, 4, 5),
                   "places": 1},
    "reaction": {"group_a": "drivers who slept for 8 hours",
                 "group_b": "drivers who slept for 4 hours",
                 "label_a": "8 hours", "label_b": "4 hours", "measure": "reaction time",
                 "unit": "ms", "centres": tuple(range(220, 321, 5)),
                 "spreads": tuple(range(15, 41, 5)), "places": 0},
    "memory": {"group_a": "bilingual adults", "group_b": "monolingual adults",
               "label_a": "Bilingual", "label_b": "Monolingual", "measure": "memory test score",
               "unit": "", "centres": tuple(range(80, 93)), "spreads": (2, 3, 4, 5), "places": 0},
}
DIRECTIONS = {"greater": "higher than", "less": "lower than", "different": "different from"}
SYMBOLS = {"greater": "mu_A > mu_B", "less": "mu_A < mu_B", "different": "mu_A is not equal to mu_B"}
ALPHAS = ("1", "5", "10")
SHIFTS = (0, 0.5, 1, 1.5)
SIZES = tuple(range(6, 11))


# ------------------------------------------------------------ mathematics

def sample_summary(texts):
    values = [Fraction(v) for v in texts]
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    return n, mean, variance


def t_statistic(a_texts, b_texts):
    na, ma, va = sample_summary(a_texts)
    nb, mb, vb = sample_summary(b_texts)
    pooled = ((na - 1) * va + (nb - 1) * vb) / (na + nb - 2)
    error = dist.square_root(pooled * (Fraction(1, na) + Fraction(1, nb)))
    return (ma - mb) / error, na + nb - 2


def p_value(t, df, direction):
    below = dist.t_cdf(t, df)
    if direction == "greater":
        return 1 - below
    if direction == "less":
        return below
    return 2 * (1 - dist.t_cdf(abs(t), df))


def draw(rng, centre, spread, count, places):
    scale = 10 ** places
    return [decimal_text(Fraction(round(rng.gauss(centre, spread) * scale), scale))
            for _ in range(count)]


def hypotheses(c, direction):
    return ("H0: mu_A = mu_B. H1: {}, where mu_A and mu_B are the mean {}s of {} and "
            "{}.".format(SYMBOLS[direction], c["measure"], c["group_a"], c["group_b"]))


def conclusion(c, direction, value, alpha):
    level = Fraction(alpha) / 100
    reject = value < level
    claim = "the mean {} of {} is {} that of {}".format(
        c["measure"], c["group_a"], DIRECTIONS[direction], c["group_b"])
    if reject:
        return "Reject H0, since p = {} < {}. There is evidence at the {}% level that {}.".format(
            ib.sf3(value), ib.exact_text(level), alpha, claim)
    return ("Do not reject H0, since p = {} > {}. There is insufficient evidence at the {}% "
            "level that {}.".format(ib.sf3(value), ib.exact_text(level), alpha, claim))


# ------------------------------------------------------------ generator

class TwoSampleTTest(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.statistics.t_test",
        version=1,
        topic=ib.TOPIC,
        subtopic="statistics_and_probability",
        title="Two-sample t-test",
        difficulty_descriptions={
            1: "Hypotheses from the wording and a conclusion from a given p-value.",
            2: "Two-tailed test from data: hypotheses, p-value and conclusion.",
            3: "One-tailed test from data, at 1%, 5% or 10%, and the normality assumption.",
            4: "Sample means, hypotheses, t-statistic and p-value, and conclusion.",
        },
        tags=ib.BASE_TAGS + ("t_test", "hypothesis_testing"),
    )
    keys = {
        1: {"context", "name", "direction", "alpha", "p"},
        2: {"context", "name", "a", "b"},
        3: {"context", "name", "direction", "alpha", "a", "b"},
        4: {"context", "name", "direction", "alpha", "a", "b"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        context = rng.choice(tuple(CONTEXTS))
        p = {"context": context, "name": rng.choice(ib.NAMES)}
        if level != 2:
            p["direction"] = rng.choice(("greater", "less") if level == 3 else tuple(DIRECTIONS))
            p["alpha"] = rng.choice(ALPHAS)
        if level == 1:
            if rng.random() < 0.5:
                p["p"] = decimal_text(Fraction(rng.randint(1, 99), 10000))
            else:
                p["p"] = decimal_text(Fraction(rng.randint(12, 400), 1000))
            return p
        c = CONTEXTS[context]
        centre, spread = rng.choice(c["centres"]), rng.choice(c["spreads"])
        shift = rng.choice(SHIFTS) * spread * rng.choice((-1, 1))
        p["a"] = draw(rng, centre + shift, spread, rng.choice(SIZES), c["places"])
        p["b"] = draw(rng, centre, spread, rng.choice(SIZES), c["places"])
        return p

    def check_rules(self, p, level):
        require(p["context"] in CONTEXTS, "Unknown context")
        require(p["name"] in ib.NAMES, "Unknown name")
        c = CONTEXTS[p["context"]]
        direction, alpha = "different", "5"
        if level != 2:
            allowed = ("greater", "less") if level == 3 else tuple(DIRECTIONS)
            require(p["direction"] in allowed, "Direction outside rules")
            require(p["alpha"] in ALPHAS, "Significance level outside pool")
            direction, alpha = p["direction"], p["alpha"]
        if level == 1:
            require(isinstance(p["p"], str), "p-value must be text")
            value = Fraction(p["p"])
            require(Fraction(1, 10000) <= value <= Fraction(2, 5), "p-value outside range")
            require(abs(value - Fraction(alpha) / 100) >= Fraction(5, 1000), "p-value too near alpha")
            return
        for key in ("a", "b"):
            sample = p[key]
            require(isinstance(sample, list) and len(sample) in SIZES, "Sample size outside rules")
            require(all(isinstance(v, str) for v in sample), "Values must be text")
            values = [Fraction(v) for v in sample]
            require(all(v > 0 and (v * 10 ** c["places"]).denominator == 1 for v in values),
                    "Values outside rules")
            require(len(set(values)) > 1, "A sample needs spread")
        t, df = t_statistic(p["a"], p["b"])
        value = p_value(t, df, direction)
        require(abs(value - Fraction(alpha) / 100) >= Fraction(5, 1000), "p-value too near alpha")
        require(value >= Fraction(1, 100000), "p-value too small to be interesting")
        if direction != "different":
            # Samples should lean the way the claim does, as in real IB questions.
            require(value <= Fraction(1, 2), "Samples contradict the claimed direction")

    def parts(self, p, level):
        c = CONTEXTS[p["context"]]
        direction = "different" if level == 2 else p["direction"]
        alpha = "5" if level == 2 else p["alpha"]
        belief = "{} believes that the mean {} of {} is {} that of {}.".format(
            p["name"], c["measure"], c["group_a"], DIRECTIONS[direction], c["group_b"])
        hypothesis_part = ib.part("a", "State the null and alternative hypotheses.", 2,
                                  hypotheses(c, direction))
        if level == 1:
            context = [belief, "{} collects data from random samples and carries out a two-sample "
                       "t-test at the {}% significance level, assuming equal population "
                       "variances. The p-value is {}.".format(p["name"], alpha, p["p"])]
            return ib.assemble(context, [
                hypothesis_part,
                ib.part("b", "State the conclusion of the test, giving a reason.", 2,
                        conclusion(c, direction, Fraction(p["p"]), alpha)),
            ])

        unit = " ({})".format(c["unit"]) if c["unit"] else ""
        t, df = t_statistic(p["a"], p["b"])
        value = p_value(t, df, direction)
        assumption = ("Assume the populations are normally distributed with equal variances."
                      if level != 3 else "Assume the populations have equal variances.")
        context = [
            belief,
            "{} takes a random sample from each group and records each {}{}.".format(
                p["name"], c["measure"], unit),
            "{}: {}".format(c["label_a"], ", ".join(p["a"])),
            "{}: {}".format(c["label_b"], ", ".join(p["b"])),
            "{} carries out a two-sample t-test at the {}% significance level. {}".format(
                p["name"], alpha, assumption),
        ]
        p_part = ib.part("b", "Find the p-value for this test.", 2, "p = " + ib.sf3(value), value)
        decide = lambda label: ib.part(label, "State the conclusion of the test, giving a reason.",
                                       2, conclusion(c, direction, value, alpha))
        if level == 2:
            return ib.assemble(context, [hypothesis_part, p_part, decide("c")])
        if level == 3:
            return ib.assemble(context, [
                hypothesis_part, p_part, decide("c"),
                ib.part("d", "State one further assumption needed for this test.", 1,
                        "Both populations are normally distributed."),
            ])
        _, mean_a, _ = sample_summary(p["a"])
        _, mean_b, _ = sample_summary(p["b"])
        return ib.assemble(context, [
            ib.part("a", "Find the mean of each sample.", 2, "{}: {}; {}: {}".format(
                c["label_a"], ib.nice(mean_a), c["label_b"], ib.nice(mean_b)), mean_a),
            ib.part("b", "State the null and alternative hypotheses.", 2, hypotheses(c, direction)),
            ib.part("c", "Find the t-statistic and the p-value.", 3,
                    "t = {}, p = {}".format(ib.sf3(t), ib.sf3(value)), value),
            decide("d"),
        ])

    def validate_independently(self, question):
        """statistics.mean/variance, a float t, and the integrated t density."""
        import math
        import statistics
        p, level = question.parameters, question.difficulty
        values, shown = ib.answer_values(question), ib.answer_shown(question)
        direction = "different" if level == 2 else p["direction"]
        alpha = 0.05 if level == 2 else float(Fraction(p["alpha"])) / 100
        if level == 1:
            reject = float(Fraction(p["p"])) < alpha
            require(shown["b"].startswith("Reject") == reject, "Independent conclusion failed")
            return True
        a = [float(Fraction(v)) for v in p["a"]]
        b = [float(Fraction(v)) for v in p["b"]]
        df = len(a) + len(b) - 2
        pooled = ((len(a) - 1) * statistics.variance(a) + (len(b) - 1) * statistics.variance(b)) / df
        t = (statistics.mean(a) - statistics.mean(b)) / math.sqrt(pooled * (1 / len(a) + 1 / len(b)))
        if direction == "greater":
            value = dist.t_upper_by_integration(t, df)
        elif direction == "less":
            value = 1 - dist.t_upper_by_integration(t, df)
        else:
            value = 2 * dist.t_upper_by_integration(abs(t), df)
        label, final = ("c", "d") if level == 4 else ("b", "c")
        require(ib.close(values[label], value, 1e-6), "Independent p-value failed")
        require(shown[final].startswith("Reject") == (value < alpha), "Independent conclusion failed")
        if level == 4:
            require(ib.close(values["a"], statistics.mean(a)), "Independent mean failed")
        return True