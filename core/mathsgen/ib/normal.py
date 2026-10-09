"""IB AI SL normal distribution: probabilities, inverse normal, finding the
standard deviation, expected numbers, and normal feeding into binomial.

Thresholds are mean + z * sd for z in tenths, rounded to the context's
step, so values look like real measurements.
"""
from fractions import Fraction
from math import comb

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from ..rounding import decimal_text, round_half_up
from . import common as ib
from . import distributions as dist


def tenths(low, high, step=1):
    return tuple(decimal_text(Fraction(v, 10)) for v in range(low, high + 1, step))


# --- Editable pools ---------------------------------------------------------
CONTEXTS = {
    "heights": {"opening": "The heights of adult women in a city", "item": "woman",
                "items": "women", "quantity": "height", "unit": "cm",
                "means": tenths(1600, 1720, 5), "sds": tenths(50, 80), "step": 1},
    "delivery": {"opening": "The delivery times of parcels sent by a courier", "item": "parcel",
                 "items": "parcels", "quantity": "delivery time", "unit": "hours",
                 "means": tenths(400, 720, 10), "sds": tenths(60, 140, 10), "step": 1},
    "apples": {"opening": "The masses of apples from an orchard", "item": "apple",
               "items": "apples", "quantity": "mass", "unit": "g",
               "means": tenths(1400, 2000, 50), "sds": tenths(100, 250, 10), "step": 5},
    "speeds": {"opening": "The speeds of cars passing a speed camera", "item": "car",
               "items": "cars", "quantity": "speed", "unit": "km/h",
               "means": tenths(550, 750), "sds": tenths(40, 90), "step": 1},
    "batteries": {"opening": "The lifetimes of a brand of battery", "item": "battery",
                  "items": "batteries", "quantity": "lifetime", "unit": "hours",
                  "means": tenths(4000, 6000, 100), "sds": tenths(200, 600, 50), "step": 10},
}
SIDES = {"below": "less than", "above": "more than"}
PERCENTS = ("10", "15", "20", "25", "30", "35", "40", "60", "65", "70", "75", "80", "85", "90")
SD_MULTIPLES = ("1", "1.5", "2", "2.5")
TOTALS = (200, 250, 400, 500, 800, 1000, 1200)
SAMPLE_SIZES = tuple(range(5, 13))


# ------------------------------------------------------------ helpers

def threshold(rng, mean, sd, step):
    """A measurement-like value about -2.2 to 2.2 standard deviations from the mean."""
    z = Fraction(rng.randint(-22, 22), 10)
    raw = Fraction(mean) + z * Fraction(sd)
    return decimal_text(round_half_up(raw / step, 0) * step)


def require_threshold(text, mean, sd, step):
    require(isinstance(text, str), "Threshold must be text")
    value = Fraction(text)
    require((value / step).denominator == 1, "Threshold off the step")
    require(value != Fraction(mean) and abs(value - Fraction(mean)) <= 3 * Fraction(sd),
            "Threshold outside three standard deviations")
    return value


def probability(side, x, mean, sd):
    below = dist.normal_cdf(x, mean, sd)
    return below if side == "below" else 1 - below


def require_sensible(value, low=Fraction(1, 100), high=Fraction(99, 100)):
    require(low <= value <= high, "Probability too extreme")


# ------------------------------------------------------------ generator

class NormalDistribution(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.statistics.normal_distribution",
        version=1,
        topic=ib.TOPIC,
        subtopic="statistics_and_probability",
        title="Normal distribution",
        difficulty_descriptions={
            1: "One-tail and between-two-values probabilities.",
            2: "A probability, then inverse normal from a percentage.",
            3: "Find the standard deviation from a value k sd above the mean, then expected numbers.",
            4: "A normal probability used in a binomial: exactly r, then at least one.",
        },
        tags=ib.BASE_TAGS + ("normal_distribution", "inverse_normal", "probability"),
    )
    keys = {
        1: {"context", "mean", "sd", "side", "x", "lo", "hi"},
        2: {"context", "mean", "sd", "lo", "hi", "percent", "side"},
        3: {"context", "mean", "sd_multiple", "value", "x", "total"},
        4: {"context", "mean", "sd", "side", "x", "n", "r"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        name = rng.choice(tuple(CONTEXTS))
        c = CONTEXTS[name]
        mean, sd = rng.choice(c["means"]), rng.choice(c["sds"])
        p = {"context": name, "mean": mean}
        if level in (1, 2):
            low, high = sorted((threshold(rng, mean, sd, c["step"]),
                                threshold(rng, mean, sd, c["step"])), key=Fraction)
            p.update(sd=sd, lo=low, hi=high, side=rng.choice(tuple(SIDES)))
            if level == 1:
                p["x"] = threshold(rng, mean, sd, c["step"])
            else:
                p["percent"] = rng.choice(PERCENTS)
        elif level == 3:
            multiple = rng.choice(SD_MULTIPLES)
            p.update(sd_multiple=multiple,
                     value=decimal_text(Fraction(mean) + Fraction(multiple) * Fraction(sd)),
                     x=threshold(rng, mean, sd, c["step"]), total=rng.choice(TOTALS))
        else:
            n = rng.choice(SAMPLE_SIZES)
            p.update(sd=sd, side=rng.choice(tuple(SIDES)),
                     x=threshold(rng, mean, sd, c["step"]), n=n, r=rng.randint(1, n - 1))
        return p

    def check_rules(self, p, level):
        require(p["context"] in CONTEXTS, "Unknown context")
        c = CONTEXTS[p["context"]]
        require(p["mean"] in c["means"], "Mean outside pool")
        if level == 3:
            require(p["sd_multiple"] in SD_MULTIPLES, "Multiple outside pool")
            sd = (Fraction(p["value"]) - Fraction(p["mean"])) / Fraction(p["sd_multiple"])
            require(decimal_text(sd) in c["sds"], "Standard deviation outside pool")
            x = require_threshold(p["x"], p["mean"], sd, c["step"])
            require(p["total"] in TOTALS, "Total outside pool")
            require_sensible(probability("above", x, p["mean"], sd), Fraction(5, 100), Fraction(95, 100))
            return
        require(p["sd"] in c["sds"], "Standard deviation outside pool")
        require(p["side"] in SIDES, "Unknown side")
        if level in (1, 2):
            low = require_threshold(p["lo"], p["mean"], p["sd"], c["step"])
            high = require_threshold(p["hi"], p["mean"], p["sd"], c["step"])
            require(high - low >= Fraction(p["sd"]) / 2, "Interval too narrow")
            between = dist.normal_cdf(high, p["mean"], p["sd"]) - dist.normal_cdf(low, p["mean"], p["sd"])
            require_sensible(between, Fraction(5, 100))
        if level == 1:
            x = require_threshold(p["x"], p["mean"], p["sd"], c["step"])
            require_sensible(probability(p["side"], x, p["mean"], p["sd"]))
        elif level == 2:
            require(p["percent"] in PERCENTS, "Percentage outside pool")
        elif level == 4:
            x = require_threshold(p["x"], p["mean"], p["sd"], c["step"])
            require_sensible(probability(p["side"], x, p["mean"], p["sd"]),
                             Fraction(10, 100), Fraction(90, 100))
            require(p["n"] in SAMPLE_SIZES, "Sample size outside pool")
            ib.require_int(p["r"], 1, p["n"] - 1, "r outside bounds")

    def parts(self, p, level):
        c = CONTEXTS[p["context"]]
        unit, quantity = c["unit"], c["quantity"]

        def has(side, x):
            return "a {} of {} {} {}".format(quantity, SIDES[side], x, unit)

        if level == 3:
            sd = (Fraction(p["value"]) - Fraction(p["mean"])) / Fraction(p["sd_multiple"])
            above = probability("above", p["x"], p["mean"], sd)
            expected = p["total"] * above
            plural = "" if p["sd_multiple"] == "1" else "s"
            context = ["{} are normally distributed with mean {} {}.".format(
                c["opening"], p["mean"], unit)]
            return ib.assemble(context, [
                ib.part("a", "A {} of {} {} is {} standard deviation{} above the mean. Find the "
                        "standard deviation.".format(quantity, p["value"], unit, p["sd_multiple"],
                                                     plural), 2,
                        "{} {}".format(ib.nice(sd), unit), sd),
                ib.part("b", "Find the probability that a randomly chosen {} has {}.".format(
                    c["item"], has("above", p["x"])), 2, ib.sf3(above), above),
                ib.part("c", "{} {} are chosen at random. Find the expected number of them with "
                        "{}.".format(p["total"], c["items"], has("above", p["x"])), 2,
                        ib.sf3(expected), expected),
            ])

        context = ["{} are normally distributed with mean {} {} and standard deviation {} "
                   "{}.".format(c["opening"], p["mean"], unit, p["sd"], unit)]
        def between_part(label):
            between = (dist.normal_cdf(p["hi"], p["mean"], p["sd"])
                       - dist.normal_cdf(p["lo"], p["mean"], p["sd"]))
            return ib.part(
                label, "Find the probability that a randomly chosen {} has a {} between {} {} "
                "and {} {}.".format(c["item"], quantity, p["lo"], unit, p["hi"], unit), 2,
                ib.sf3(between), between)

        if level == 1:
            single = probability(p["side"], p["x"], p["mean"], p["sd"])
            return ib.assemble(context, [
                ib.part("a", "Find the probability that a randomly chosen {} has {}.".format(
                    c["item"], has(p["side"], p["x"])), 2, ib.sf3(single), single),
                between_part("b"),
            ])
        if level == 2:
            share = Fraction(p["percent"]) / 100
            below = share if p["side"] == "below" else 1 - share
            k = dist.inverse_normal(below, p["mean"], p["sd"])
            return ib.assemble(context, [
                between_part("a"),
                ib.part("b", "{}% of {} have a {} {} k {}. Find k.".format(
                    p["percent"], c["items"], quantity, SIDES[p["side"]], unit), 2,
                    "k = {} {}".format(ib.sf3(k), unit), k),
            ])

        event = probability(p["side"], p["x"], p["mean"], p["sd"])
        exactly = comb(p["n"], p["r"]) * event ** p["r"] * (1 - event) ** (p["n"] - p["r"])
        at_least_one = 1 - (1 - event) ** p["n"]
        return ib.assemble(context, [
            ib.part("a", "Find the probability that a randomly chosen {} has {}.".format(
                c["item"], has(p["side"], p["x"])), 2, ib.sf3(event), event),
            ib.part("b", "{} {} are chosen at random. Find the probability that exactly {} of "
                    "them have {}.".format(p["n"], c["items"], p["r"], has(p["side"], p["x"])), 3,
                    ib.sf3(exactly), exactly),
            ib.part("c", "Find the probability that at least one of them has {}.".format(
                has(p["side"], p["x"])), 2, ib.sf3(at_least_one), at_least_one),
        ])

    def validate_independently(self, question):
        """Integrate the normal density; bisect for inverse normal."""
        p, level = question.parameters, question.difficulty
        values = ib.answer_values(question)
        mean = float(Fraction(p["mean"]))

        def chance(side, x, sd):
            below = dist.normal_cdf_by_integration(float(Fraction(x)), mean, sd)
            return below if side == "below" else 1 - below

        if level == 3:
            sd = (float(Fraction(p["value"])) - mean) / float(Fraction(p["sd_multiple"]))
            require(ib.close(values["a"], sd), "Independent sd failed")
            above = chance("above", p["x"], sd)
            require(ib.close(values["b"], above, 1e-8), "Independent probability failed")
            require(ib.close(values["c"], p["total"] * above, 1e-8), "Independent expectation failed")
            return True
        sd = float(Fraction(p["sd"]))
        if level in (1, 2):
            between = chance("below", p["hi"], sd) - chance("below", p["lo"], sd)
            require(ib.close(values["b" if level == 1 else "a"], between, 1e-8),
                    "Independent interval failed")
        if level == 1:
            require(ib.close(values["a"], chance(p["side"], p["x"], sd), 1e-8),
                    "Independent tail failed")
        if level == 2:
            share = float(Fraction(p["percent"])) / 100
            target = share if p["side"] == "below" else 1 - share
            low, high = mean - 6 * sd, mean + 6 * sd
            for _ in range(80):
                middle = (low + high) / 2
                if dist.normal_cdf_by_integration(middle, mean, sd) < target:
                    low = middle
                else:
                    high = middle
            require(ib.close(values["b"], (low + high) / 2, 1e-7), "Independent inverse failed")
        if level == 4:
            event = chance(p["side"], p["x"], sd)
            n, r = p["n"], p["r"]
            exactly = 1.0
            for k in range(r):
                exactly *= (n - k) / (k + 1)
            exactly *= event ** r * (1 - event) ** (n - r)
            require(ib.close(values["a"], event, 1e-8) and ib.close(values["b"], exactly, 1e-7)
                    and ib.close(values["c"], 1 - (1 - event) ** n, 1e-8),
                    "Independent binomial step failed")
        return True