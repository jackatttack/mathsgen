"""IB AI SL exponential models.

Level 1 V(t) = A b^t growth or decay; level 2 half-life; level 3 find b
from two measurements; level 4 limited growth n(t) = L - c 2^(-kt), with
k found from a measurement. Powers and logarithms use mpmath at 30 digits;
the independent check solves by bisection instead.
"""
from fractions import Fraction

import mpmath

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from .. import rich_blocks as rb
from . import common as ib
from . import distributions as dist


# --- Editable pools ---------------------------------------------------------
GROWTH = {
    "car": {"intro": "The value, V dollars, of a car t years after it is bought is modelled by",
            "symbol": "V", "bases": ("0.8", "0.82", "0.85", "0.88", "0.9"),
            "starts": tuple(range(15000, 45001, 500)), "time": "years",
            "first": "the value of the car when it is bought", "step": 500},
    "town": {"intro": "The population, P, of a town t years after 2020 is modelled by",
             "symbol": "P", "bases": ("1.02", "1.025", "1.03", "1.04", "1.05"),
             "starts": tuple(range(5000, 40001, 500)), "time": "years",
             "first": "the population in 2020", "step": 500},
    "bacteria": {"intro": "The number, N, of bacteria in a culture t hours after it is started "
                          "is modelled by", "symbol": "N", "bases": ("1.2", "1.25", "1.3", "1.4", "1.5"),
                 "starts": tuple(range(100, 2001, 50)), "time": "hours",
                 "first": "the number of bacteria at the start", "step": 100},
}
HALF_LIFE = {
    "drug": {"intro": "A patient is given {} mg of a drug. The amount in the bloodstream halves "
                      "every {} hours.", "unit": "mg", "time": "hours",
             "amounts": tuple(range(100, 801, 50)), "half_lives": (2, 3, 4, 5, 6, 8)},
    "isotope": {"intro": "A sample contains {} g of a radioactive isotope with a half-life of "
                         "{} days.", "unit": "g", "time": "days",
                "amounts": tuple(range(20, 201, 10)), "half_lives": (5, 8, 12, 15, 20, 30)},
}
FITTED = {
    "rabbits": {"intro": "A population of rabbits is modelled by N(t) = A b^t, where t is the "
                         "time in years. Initially there are {} rabbits; after {} years there "
                         "are {}.", "time": "years", "starts": tuple(range(20, 201, 10))},
    "downloads": {"intro": "Weekly downloads of an app are modelled by N(t) = A b^t, where t is "
                           "the number of weeks after launch. In the launch week there are {} "
                           "downloads; {} weeks later there are {}.", "time": "weeks",
                  "starts": tuple(range(200, 2001, 100))},
}
LIMITED = {
    "influenza": {"intro": "The number of students, n, who have had influenza t days after the "
                           "start of term is modelled by", "time": "days", "people": "students",
                  "limits": tuple(range(200, 601, 50))},
    "rumour": {"intro": "The number of people, n, who have heard a rumour t hours after it "
                        "starts is modelled by", "time": "hours", "people": "people",
               "limits": tuple(range(500, 3001, 100))},
}


# ------------------------------------------------------------ mathematics

def power(base, exponent):
    with mpmath.workdps(dist.PRECISION):
        return dist.fraction(mpmath.power(dist.mp(base), dist.mp(exponent)))


def solve_power(base, ratio):
    """x with base^x = ratio."""
    with mpmath.workdps(dist.PRECISION):
        return dist.fraction(mpmath.log(dist.mp(ratio)) / mpmath.log(dist.mp(base)))


def limited_k(p):
    """k with L - c 2^(-k t1) = n1."""
    with mpmath.workdps(dist.PRECISION):
        share = dist.mp(Fraction(p["limit"] - p["measured"], p["gap"]))
        return dist.fraction(-mpmath.log(share, 2) / p["after"])


def limited_time(p, k, target):
    with mpmath.workdps(dist.PRECISION):
        share = dist.mp(Fraction(p["limit"] - target, p["gap"]))
        return dist.fraction(-mpmath.log(share, 2) / dist.mp(k))


def model_runs(symbol, start, base):
    text = "{}(t) = {}({})^t".format(symbol, start, base)
    tex = "{}(t)={}({})^{{t}}".format(symbol, start, base)
    return rb.maths(tex, text)


# ------------------------------------------------------------ generator

class ExponentialModels(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.functions.exponential_models",
        version=1,
        topic=ib.TOPIC,
        subtopic="functions",
        title="Exponential models",
        difficulty_descriptions={
            1: "Use V(t) = A b^t: the initial value, a later value and the time to reach a value.",
            2: "Half-life: amount remaining, time to fall to a value, percentage left.",
            3: "Find b from two measurements, then predict and solve.",
            4: "Limited growth n(t) = L - c 2^(-kt): find k, solve, and interpret the asymptote.",
        },
        tags=ib.BASE_TAGS + ("exponential_models", "half_life", "asymptotes"),
    )
    keys = {
        1: {"context", "start", "base", "at", "target"},
        2: {"context", "amount", "half_life", "at", "target", "later"},
        3: {"context", "start", "after", "measured", "at", "target"},
        4: {"context", "limit", "gap", "after", "measured", "target"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        if level == 1:
            name = rng.choice(tuple(GROWTH))
            c = GROWTH[name]
            start, base = rng.choice(c["starts"]), rng.choice(c["bases"])
            aim = start * float(Fraction(base)) ** rng.randint(4, 15)
            return {"context": name, "start": start, "base": base, "at": rng.randint(2, 12),
                    "target": int(round(aim / c["step"])) * c["step"]}
        if level == 2:
            name = rng.choice(tuple(HALF_LIFE))
            c = HALF_LIFE[name]
            amount, half = rng.choice(c["amounts"]), rng.choice(c["half_lives"])
            return {"context": name, "amount": amount, "half_life": half,
                    "at": rng.randint(1, 4 * half), "target": max(1, amount // rng.choice((3, 5, 8, 10))),
                    "later": rng.randint(1, 5 * half)}
        if level == 3:
            name = rng.choice(tuple(FITTED))
            start = rng.choice(FITTED[name]["starts"])
            after = rng.randint(2, 6)
            measured = int(start * rng.uniform(1.3, 3.0))
            return {"context": name, "start": start, "after": after, "measured": measured,
                    "at": after + rng.randint(2, 6), "target": int(measured * rng.uniform(2, 6))}
        name = rng.choice(tuple(LIMITED))
        limit = rng.choice(LIMITED[name]["limits"])
        gap = int(limit * rng.uniform(0.85, 0.98))
        after = rng.randint(3, 15)
        start = limit - gap
        measured = start + int((limit - start) * rng.uniform(0.3, 0.6))
        return {"context": name, "limit": limit, "gap": gap, "after": after, "measured": measured,
                "target": measured + int((limit - measured) * rng.uniform(0.3, 0.8))}

    def check_rules(self, p, level):
        if level == 1:
            require(p["context"] in GROWTH, "Unknown context")
            c = GROWTH[p["context"]]
            require(p["start"] in c["starts"] and p["base"] in c["bases"], "Model outside pools")
            ib.require_int(p["at"], 1, 15, "Time outside bounds")
            require(type(p["target"]) is int and p["target"] > 0 and p["target"] % c["step"] == 0,
                    "Target outside rules")
            time = solve_power(p["base"], Fraction(p["target"], p["start"]))
            require(1 <= time <= 40, "Time to target outside bounds")
        elif level == 2:
            require(p["context"] in HALF_LIFE, "Unknown context")
            c = HALF_LIFE[p["context"]]
            require(p["amount"] in c["amounts"] and p["half_life"] in c["half_lives"], "Values outside pools")
            ib.require_int(p["at"], 1, 200, "Time outside bounds")
            ib.require_int(p["later"], 1, 200, "Time outside bounds")
            require(p["at"] % p["half_life"] != 0, "Time should not be whole half-lives")
            require(type(p["target"]) is int and 0 < p["target"] < p["amount"] // 2, "Target outside rules")
        elif level == 3:
            require(p["context"] in FITTED, "Unknown context")
            require(p["start"] in FITTED[p["context"]]["starts"], "Start outside pool")
            ib.require_int(p["after"], 2, 6, "Time outside bounds")
            require(type(p["measured"]) is int and p["measured"] > p["start"], "Measurement outside rules")
            require(type(p["at"]) is int and p["after"] < p["at"] <= p["after"] + 6, "Prediction outside rules")
            require(type(p["target"]) is int and p["target"] > p["measured"], "Target outside rules")
        else:
            require(p["context"] in LIMITED, "Unknown context")
            require(p["limit"] in LIMITED[p["context"]]["limits"], "Limit outside pool")
            for key in ("gap", "after", "measured", "target"):
                require(type(p[key]) is int, "Values must be integers")
            start = p["limit"] - p["gap"]
            require(0 < start < p["measured"] < p["target"] < p["limit"], "Values out of order")
            require(3 <= p["after"] <= 15, "Time outside bounds")

    def parts(self, p, level):
        if level == 1:
            c = GROWTH[p["context"]]
            symbol = c["symbol"]
            context = [[rb.text(c["intro"] + " "), model_runs(symbol, p["start"], p["base"]),
                        rb.text(".")]]
            later = p["start"] * power(p["base"], p["at"])
            time = solve_power(p["base"], Fraction(p["target"], p["start"]))
            return ib.assemble(context, [
                ib.part("a", "Write down {}.".format(c["first"]), 1, str(p["start"]), p["start"]),
                ib.part("b", "Find {} when t = {}.".format(symbol, p["at"]), 2, ib.sf3(later), later),
                ib.part("c", "Find the value of t when {} = {}.".format(symbol, p["target"]), 2,
                        "{} {}".format(ib.sf3(time), c["time"]), time),
            ])
        if level == 2:
            c = HALF_LIFE[p["context"]]
            half = p["half_life"]
            remaining = p["amount"] * power(Fraction(1, 2), Fraction(p["at"], half))
            time = half * solve_power(Fraction(1, 2), Fraction(p["target"], p["amount"]))
            percent = 100 * power(Fraction(1, 2), Fraction(p["later"], half))
            context = [c["intro"].format(p["amount"], half)]
            return ib.assemble(context, [
                ib.part("a", "Find the amount remaining after {} {}.".format(p["at"], c["time"]), 2,
                        "{} {}".format(ib.sf3(remaining), c["unit"]), remaining),
                ib.part("b", "Find the time taken for the amount to fall to {} {}.".format(
                    p["target"], c["unit"]), 2, "{} {}".format(ib.sf3(time), c["time"]), time),
                ib.part("c", "Find the percentage of the original amount that remains after {} "
                        "{}.".format(p["later"], c["time"]), 2, ib.sf3(percent) + "%", percent),
            ])
        if level == 3:
            c = FITTED[p["context"]]
            base = power(Fraction(p["measured"], p["start"]), Fraction(1, p["after"]))
            predicted = p["start"] * power(base, p["at"])
            time = solve_power(base, Fraction(p["target"], p["start"]))
            context = [c["intro"].format(p["start"], p["after"], p["measured"])]
            return ib.assemble(context, [
                ib.part("a", "Write down the value of A, and find the value of b.", 3,
                        "A = {}, b = {}".format(p["start"], ib.sf3(base)), base),
                ib.part("b", "Use the model to predict N when t = {}.".format(p["at"]), 2,
                        ib.sf3(predicted), predicted),
                ib.part("c", "Find the value of t when N = {}.".format(p["target"]), 2,
                        "{} {}".format(ib.sf3(time), c["time"]), time),
            ])
        c = LIMITED[p["context"]]
        text = "n(t) = {} - {} × 2^(-kt)".format(p["limit"], p["gap"])
        tex = "n(t)={}-{}\\times2^{{-kt}}".format(p["limit"], p["gap"])
        context = [[rb.text(c["intro"] + " "), rb.maths(tex, text),
                    rb.text(", where k is a positive constant.")]]
        k = limited_k(p)
        time = limited_time(p, k, p["target"])
        start = p["limit"] - p["gap"]
        return ib.assemble(context, [
            ib.part("a", "Find n(0), and interpret it in context.", 2,
                    "{}: the number of {} at t = 0".format(start, c["people"]), start),
            ib.part("b", "After {} {}, n = {}. Find k.".format(p["after"], c["time"], p["measured"]),
                    2, "k = " + ib.sf3(k), k),
            ib.part("c", "Find the time when n = {}.".format(p["target"]), 2,
                    "{} {}".format(ib.sf3(time), c["time"]), time),
            ib.part("d", "Write down the equation of the horizontal asymptote of the graph of n, "
                    "and interpret it in context.", 2,
                    "n = {}: the number of {} approaches {} but never exceeds it.".format(
                        p["limit"], c["people"], p["limit"])),
        ])

    def validate_independently(self, question):
        """Evaluate with floats and solve every 'find t' by bisection."""
        import math
        p, level = question.parameters, question.difficulty
        values = ib.answer_values(question)

        def bisect(function, target, low, high):
            rising = function(high) > function(low)
            for _ in range(200):
                middle = (low + high) / 2
                if (function(middle) < target) == rising:
                    low = middle
                else:
                    high = middle
            return (low + high) / 2

        if level == 1:
            base = float(Fraction(p["base"]))
            model = lambda t: p["start"] * base ** t
            require(ib.close(values["b"], model(p["at"])), "Independent value failed")
            require(ib.close(values["c"], bisect(model, p["target"], 0, 100), 1e-7), "Independent time failed")
        elif level == 2:
            model = lambda t: p["amount"] * 0.5 ** (t / p["half_life"])
            require(ib.close(values["a"], model(p["at"])), "Independent amount failed")
            require(ib.close(values["b"], bisect(model, p["target"], 0, 500), 1e-7), "Independent time failed")
            require(ib.close(values["c"], 100 * model(p["later"]) / p["amount"]), "Independent percent failed")
        elif level == 3:
            base = math.exp(math.log(p["measured"] / p["start"]) / p["after"])
            model = lambda t: p["start"] * base ** t
            require(ib.close(values["a"], base), "Independent b failed")
            require(ib.close(values["b"], model(p["at"])), "Independent prediction failed")
            require(ib.close(values["c"], bisect(model, p["target"], 0, 200), 1e-7), "Independent time failed")
        else:
            measured = lambda k: p["limit"] - p["gap"] * 2 ** (-k * p["after"])
            k = bisect(measured, p["measured"], 1e-6, 10)
            require(ib.close(values["b"], k, 1e-7), "Independent k failed")
            model = lambda t: p["limit"] - p["gap"] * 2 ** (-k * t)
            require(ib.close(values["c"], bisect(model, p["target"], 0, 1000), 1e-6), "Independent time failed")
            require(Fraction(values["a"]) == p["limit"] - p["gap"], "Independent n(0) failed")
        return True