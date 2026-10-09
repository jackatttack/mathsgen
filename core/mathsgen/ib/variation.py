"""IB AI SL direct and inverse variation: y = k x^n with n = 1, -1, 2, -2.

The level fixes the power. One measured pair gives k exactly; the other
parts use the equation forwards and backwards. Level 4 also asks for the
effect of doubling x, which is 2^n.
"""
from fractions import Fraction

import mpmath

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from . import common as ib
from . import distributions as dist


# --- Editable pools ---------------------------------------------------------
# power -> {context: details}. "pairs" are (x1 choices, x2 choices).
CONTEXTS = {
    1: {
        "painting": {"stem": "The area, A m^2, of wall a team can paint in a day varies directly "
                             "with the number of painters, n.", "y": "A", "x": "n",
                     "y_unit": "m^2", "x_unit": "painters", "x_values": tuple(range(2, 13)),
                     "per_unit": tuple(range(8, 31, 2)), "discrete": True},
        "fuel": {"stem": "The cost, C dollars, of fuel varies directly with the volume, V litres, "
                         "bought.", "y": "C", "x": "V", "y_unit": "dollars", "x_unit": "litres",
                 "x_values": tuple(range(10, 81, 5)), "per_unit": ("1.4", "1.55", "1.6", "1.75", "1.9")},
    },
    -1: {
        "builders": {"stem": "The time, t hours, taken to build a wall varies inversely with the "
                             "number of builders, b.", "y": "t", "x": "b", "y_unit": "hours",
                     "x_unit": "builders", "x_values": tuple(range(2, 13)),
                     "per_unit": tuple(range(24, 121, 12)), "discrete": True},
        "speed": {"stem": "The time, T minutes, for a journey varies inversely with the average "
                          "speed, v km/h.", "y": "T", "x": "v", "y_unit": "minutes",
                  "x_unit": "km/h", "x_values": tuple(range(30, 121, 10)),
                  "per_unit": tuple(range(1200, 4801, 300))},
    },
    2: {
        "stopping": {"stem": "The stopping distance, d metres, of a car varies directly with the "
                             "square of its speed, v km/h.", "y": "d", "x": "v", "y_unit": "m",
                     "x_unit": "km/h", "x_values": tuple(range(30, 121, 10)),
                     "per_unit": ("0.004", "0.005", "0.0045", "0.006")},
        "logo": {"stem": "The area, A cm^2, of a printed logo varies directly with the square of "
                         "its width, w cm.", "y": "A", "x": "w", "y_unit": "cm^2", "x_unit": "cm",
                 "x_values": tuple(range(4, 21)), "per_unit": ("0.6", "0.75", "0.8", "1.2")},
    },
    -2: {
        "light": {"stem": "The intensity, I, of light from a lamp varies inversely with the square "
                          "of the distance, d m, from the lamp.", "y": "I", "x": "d", "y_unit": "lux",
                  "x_unit": "m", "x_values": tuple(range(1, 9)),
                  "per_unit": tuple(range(200, 1601, 100))},
        "smoothies": {"stem": "The number, n, of smoothies a shop sells each day varies inversely "
                              "with the square of the price, x pesos.", "y": "n", "x": "x",
                      "y_unit": "smoothies", "x_unit": "pesos", "x_values": tuple(range(10, 61, 5)),
                      "per_unit": tuple(range(20000, 80001, 5000))},
    },
}
LEVEL_POWER = {1: 1, 2: -1, 3: 2, 4: -2}


# ------------------------------------------------------------ mathematics

def value_at(k, power, x):
    return Fraction(k) * Fraction(x) ** power


def solve_for_x(k, power, y):
    """Positive x with k x^power = y (exact for powers 1 and -1)."""
    k, y = Fraction(k), Fraction(y)
    if power == 1:
        return y / k
    if power == -1:
        return k / y
    with mpmath.workdps(dist.PRECISION):
        return dist.fraction(mpmath.power(dist.mp(Fraction(y) / Fraction(k)), mpmath.mpf(1) / power))


def equation_text(c, k, power):
    number = ib.nice(k) if ib.nice(k) == ib.exact_or_fraction(k) else ib.sf3(k)
    if power == 1:
        return "{} = {}{}".format(c["y"], number, c["x"])
    if power == 2:
        return "{} = {}{}^2".format(c["y"], number, c["x"])
    if power == -1:
        return "{} = {}/{}".format(c["y"], number, c["x"])
    return "{} = {}/{}^2".format(c["y"], number, c["x"])


# ------------------------------------------------------------ generator

class Variation(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.functions.variation",
        version=1,
        topic=ib.TOPIC,
        subtopic="functions",
        title="Direct and inverse variation",
        difficulty_descriptions={
            1: "Direct variation y = kx: the equation, a value and the reverse.",
            2: "Inverse variation y = k/x: the equation, a value and the reverse.",
            3: "y = kx^2: the equation, a value and solving for x.",
            4: "y = k/x^2: the equation, values, and the effect of doubling x.",
        },
        tags=ib.BASE_TAGS + ("variation", "proportion", "power_models"),
    )
    keys = {level: {"context", "per_unit", "x1", "x2", "y3"} for level in (1, 2, 3, 4)}

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        power = LEVEL_POWER[level]
        name = rng.choice(tuple(CONTEXTS[power]))
        c = CONTEXTS[power][name]
        x1, x2 = rng.sample(c["x_values"], 2)
        per_unit = rng.choice(c["per_unit"])
        third = rng.choice([x for x in c["x_values"] if x not in (x1, x2)])
        exact = value_at(Fraction(per_unit), power, third)
        if c.get("discrete"):
            # A count (painters, builders) must come back as a whole number.
            y3 = ib.exact_or_fraction(exact)
        else:
            y3 = ib.sf3(exact * Fraction(rng.randint(85, 115), 100))
        return {"context": name, "per_unit": str(per_unit), "x1": x1, "x2": x2, "y3": y3}

    def check_rules(self, p, level):
        power = LEVEL_POWER[level]
        require(p["context"] in CONTEXTS[power], "Unknown context")
        c = CONTEXTS[power][p["context"]]
        require(p["per_unit"] in [str(v) for v in c["per_unit"]], "Constant outside pool")
        require(p["x1"] in c["x_values"] and p["x2"] in c["x_values"] and p["x1"] != p["x2"],
                "x values outside pool")
        require(isinstance(p["y3"], str) and Fraction(p["y3"]) > 0, "Third value outside rules")
        y1 = value_at(Fraction(p["per_unit"]), power, p["x1"])
        require((y1 * 1000).denominator == 1, "Measured value needs at most 3 dp")
        if c.get("discrete"):
            require("/" not in p["y3"], "Use a terminating value")
            x3 = solve_for_x(p["per_unit"], power, p["y3"])
            require(x3.denominator == 1 and x3 in c["x_values"] and x3 != p["x2"],
                    "A count must come back as a whole number")

    def parts(self, p, level):
        power = LEVEL_POWER[level]
        c = CONTEXTS[power][p["context"]]
        k = Fraction(p["per_unit"])
        y1 = value_at(k, power, p["x1"])
        y2 = value_at(k, power, p["x2"])
        x3 = solve_for_x(k, power, Fraction(p["y3"]))
        context = [c["stem"], "When {} = {}, {} = {}.".format(c["x"], p["x1"], c["y"], ib.exact_text(y1))]
        equation = ib.part("a", "Find an equation for {} in terms of {}.".format(c["y"], c["x"]), 2,
                           equation_text(c, k, power), k)
        forwards = ib.part("b", "Find {} when {} = {}.".format(c["y"], c["x"], p["x2"]),
                           1 if level < 3 else 2, "{} {}".format(ib.nice(y2), c["y_unit"]), y2)
        backwards = ib.part("c" if level < 4 else "d",
                            "Find {} when {} = {}.".format(c["x"], c["y"], p["y3"]), 2,
                            "{} {}".format(ib.nice(x3) if c.get("discrete") else ib.sf3(x3),
                                           c["x_unit"]), x3)
        if level < 4:
            return ib.assemble(context, [equation, forwards, backwards])
        return ib.assemble(context, [
            equation, forwards,
            ib.part("c", "Describe the effect on {} of doubling {}.".format(c["y"], c["x"]), 1,
                    "{} is divided by 4".format(c["y"])),
            backwards,
        ])

    def validate_independently(self, question):
        """Recover k from the measured pair; solve backwards with logarithms."""
        import math
        p, level = question.parameters, question.difficulty
        values = ib.answer_values(question)
        power = LEVEL_POWER[level]
        k = float(Fraction(p["per_unit"]))
        y1 = k * p["x1"] ** power
        recovered = y1 / p["x1"] ** power
        require(ib.close(values["a"], recovered), "Independent k failed")
        require(ib.close(values["b"], recovered * p["x2"] ** power), "Independent value failed")
        x3 = math.exp(math.log(float(Fraction(p["y3"])) / recovered) / power)
        require(ib.close(values["c" if level < 4 else "d"], x3, 1e-8), "Independent reverse failed")
        if level == 4:
            ratio = (recovered * (2 * p["x2"]) ** power) / (recovered * p["x2"] ** power)
            require(abs(ratio - 0.25) < 1e-12, "Doubling check failed")
        return True