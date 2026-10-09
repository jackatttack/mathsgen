"""IB AI SL sinusoidal models h(t) = a cos(bt) + d, with b in degrees.

Every context starts at a maximum when t = 0 (a high tide, a car at the
top of a wheel), so a = (max - min)/2 > 0, d = (max + min)/2 and
b = 360 / period. Times come from inverse cosine in degrees (mpmath);
the independent check scans and bisects with radians instead.
"""
from fractions import Fraction

import mpmath

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from .. import rich_blocks as rb
from . import common as ib
from . import distributions as dist


# --- Editable pools ---------------------------------------------------------
WHEEL_TOPS = tuple(range(40, 121, 5))
WHEEL_BOTTOMS = (1, 1.5, 2, 2.5, 3, 4, 5)
WHEEL_PERIODS = (10, 12, 15, 18, 20, 24, 30, 36, 40)      # minutes; each divides 360
TIDE_HIGHS = tuple(range(12, 21))
TIDE_LOWS = (2, 2.5, 3, 3.5, 4, 4.5, 5, 6)
TIDE_HALVES = tuple(range(360, 401, 5))                   # minutes from high to low tide


# ------------------------------------------------------------ mathematics

def model(p):
    """(a, b, d, period) for the context."""
    high, low = Fraction(p["high"]), Fraction(p["low"])
    period = Fraction(p["period"])
    return (high - low) / 2, Fraction(360) / period, (high + low) / 2, period


def height(p, t):
    a, b, d, _ = model(p)
    with mpmath.workdps(dist.PRECISION):
        return dist.fraction(dist.mp(a) * mpmath.cos(mpmath.radians(dist.mp(b) * dist.mp(t)))
                             + dist.mp(d))


def first_time(p, level_value):
    """First t > 0 with h(t) = level_value (falling from the maximum)."""
    a, b, d, _ = model(p)
    with mpmath.workdps(dist.PRECISION):
        angle = mpmath.degrees(mpmath.acos((dist.mp(level_value) - dist.mp(d)) / dist.mp(a)))
        return dist.fraction(angle / dist.mp(b))


def equation_runs(a, b, d):
    text = "h(t) = {} cos({}t) + {}".format(ib.nice(a), ib.nice(b), ib.nice(d))
    tex = "h(t)={}\\cos({}t)+{}".format(ib.nice(a), ib.nice(b), ib.nice(d))
    return rb.maths(tex, text)


def text(value):
    return ib.exact_text(Fraction(value))


# ------------------------------------------------------------ generator

class SinusoidalModels(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.functions.sinusoidal",
        version=1,
        topic=ib.TOPIC,
        subtopic="functions",
        title="Sinusoidal models",
        difficulty_descriptions={
            1: "Amplitude, period, maximum and minimum from h(t) = a cos(bt) + d.",
            2: "Ferris wheel: find a, d and b, then a height.",
            3: "Tides: a, d, period and b, then the first time the depth reaches a value.",
            4: "Find the model, then the time in each cycle spent above a level.",
        },
        tags=ib.BASE_TAGS + ("trigonometric_models", "sinusoidal", "periodic"),
    )
    keys = {
        1: {"high", "low", "period"},
        2: {"high", "low", "period", "at"},
        3: {"high", "low", "period", "level"},
        4: {"context", "high", "low", "period", "level", "at"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def wheel(self, rng):
        return {"high": rng.choice(WHEEL_TOPS), "low": text(rng.choice(WHEEL_BOTTOMS)),
                "period": rng.choice(WHEEL_PERIODS)}

    def tide(self, rng):
        return {"high": rng.choice(TIDE_HIGHS), "low": text(rng.choice(TIDE_LOWS)),
                "period": 2 * rng.choice(TIDE_HALVES)}

    def candidate(self, level, rng):
        if level in (1, 2):
            p = self.wheel(rng)
            if level == 2:
                p["at"] = rng.randint(1, p["period"] - 1)
            return p
        if level == 3:
            p = self.tide(rng)
        else:
            context = rng.choice(("wheel", "tide"))
            p = dict(self.wheel(rng) if context == "wheel" else self.tide(rng), context=context)
            p["at"] = rng.randint(1, p["period"] - 1)
        high, low = Fraction(p["high"]), Fraction(p["low"])
        p["level"] = text(low + (high - low) * Fraction(rng.randint(15, 85), 100))
        return p

    def check_rules(self, p, level):
        context = p.get("context", "tide" if level == 3 else "wheel")
        if level == 4:
            require(context in ("wheel", "tide"), "Unknown context")
        if context == "wheel":
            require(p["high"] in WHEEL_TOPS and Fraction(p["low"]) in [Fraction(v) for v in WHEEL_BOTTOMS],
                    "Wheel outside pools")
            require(p["period"] in WHEEL_PERIODS, "Period outside pool")
        else:
            require(p["high"] in TIDE_HIGHS and Fraction(p["low"]) in [Fraction(v) for v in TIDE_LOWS],
                    "Tide outside pools")
            require(type(p["period"]) is int and p["period"] // 2 in TIDE_HALVES
                    and p["period"] % 2 == 0, "Period outside pool")
        require(isinstance(p["low"], str), "Low value must be text")
        if "at" in p:
            ib.require_int(p["at"], 1, p["period"] - 1, "Time outside one period")
        if "level" in p:
            require(isinstance(p["level"], str), "Level must be text")
            value = Fraction(p["level"])
            high, low = Fraction(p["high"]), Fraction(p["low"])
            require(low < value < high and value != (high + low) / 2, "Level outside the range")
            require((value * 100).denominator == 1, "Level needs at most 2 dp")

    def parts(self, p, level):
        a, b, d, period = model(p)
        if level == 1:
            context = [[rb.text("The height, h metres, of a car on a Ferris wheel t minutes after "
                                "it passes the top is modelled by "), equation_runs(a, b, d),
                        rb.text(", where the angle is measured in degrees.")]]
            return ib.assemble(context, [
                ib.part("a", "Write down the amplitude of the model.", 1, ib.nice(a), a),
                ib.part("b", "Find the time taken for one revolution.", 2,
                        "{} minutes".format(ib.nice(period)), period),
                ib.part("c", "Write down the maximum and minimum heights of the car.", 2,
                        "maximum {} m, minimum {} m".format(ib.nice(d + a), ib.nice(d - a)), d + a),
            ])
        form = [rb.text("This is modelled by "), rb.maths("h(t)=a\\cos(bt)+d", "h(t) = a cos(bt) + d"),
                rb.text(", where b is in degrees.")]
        wheel = level == 2 or p.get("context") == "wheel"
        if wheel:
            context = ["A Ferris wheel turns at a constant speed. The top of the wheel is {} m above "
                       "the ground and the bottom is {} m above the ground. One revolution takes {} "
                       "minutes. A car passes the top when t = 0, where t is in minutes.".format(
                           p["high"], p["low"], p["period"]), form]
        else:
            context = ["At t = 0 minutes there is a high tide in a harbour, with depth {} m. The "
                       "next low tide is {} minutes later, with depth {} m.".format(
                           p["high"], p["period"] // 2, p["low"]), form]
        if level == 2:
            later = height(p, p["at"])
            return ib.assemble(context, [
                ib.part("a", "Find the value of a.", 1, "a = " + ib.nice(a), a),
                ib.part("b", "Find the value of d.", 1, "d = " + ib.nice(d), d),
                ib.part("c", "Find the value of b.", 2, "b = " + ib.nice(b), b),
                ib.part("d", "Find the height of the car {} minutes after it passes the top.".format(
                    p["at"]), 2, "{} m".format(ib.sf3(later)), later),
            ])
        reached = first_time(p, p["level"])
        if level == 3:
            return ib.assemble(context, [
                ib.part("a", "Find the value of a.", 1, "a = " + ib.nice(a), a),
                ib.part("b", "Find the value of d.", 1, "d = " + ib.nice(d), d),
                ib.part("c", "Find the period of the model, in minutes.", 1, ib.nice(period), period),
                ib.part("d", "Find the value of b.", 2, "b = " + ib.sf3(b), b),
                ib.part("e", "Find the first time after t = 0 at which the depth is {} m.".format(
                    p["level"]), 3, "{} minutes".format(ib.sf3(reached)), reached),
            ])
        above = 2 * reached
        noun = "height" if wheel else "depth"
        later = height(p, p["at"])
        return ib.assemble(context, [
            ib.part("a", "Find the values of a and d.", 2,
                    "a = {}, d = {}".format(ib.nice(a), ib.nice(d)), a),
            ib.part("b", "Find the value of b.", 2, "b = " + ib.sf3(b), b),
            ib.part("c", "Find the {} when t = {}.".format(noun, p["at"]), 2,
                    "{} m".format(ib.sf3(later)), later),
            ib.part("d", "Find the length of time in each cycle for which the {} is more than "
                    "{} m.".format(noun, p["level"]), 3, "{} minutes".format(ib.sf3(above)), above),
        ])

    def validate_independently(self, question):
        """Evaluate with math.cos in radians; find crossings by bisection."""
        import math
        p, level = question.parameters, question.difficulty
        values = ib.answer_values(question)
        high, low = float(Fraction(p["high"])), float(Fraction(p["low"]))
        period = float(p["period"])
        h = lambda t: (high - low) / 2 * math.cos(2 * math.pi * t / period) + (high + low) / 2
        if level == 1:
            require(ib.close(values["a"], (high - low) / 2) and ib.close(values["b"], period)
                    and ib.close(values["c"], high), "Independent features failed")
            return True
        if level == 2:
            require(ib.close(values["c"], 360 / period), "Independent b failed")
            require(ib.close(values["d"], h(p["at"])), "Independent height failed")
            return True
        target = float(Fraction(p["level"]))
        low_t, high_t = 0.0, period / 2
        for _ in range(200):
            middle = (low_t + high_t) / 2
            if h(middle) > target:
                low_t = middle
            else:
                high_t = middle
        crossing = (low_t + high_t) / 2
        if level == 3:
            require(ib.close(values["e"], crossing, 1e-8), "Independent crossing failed")
        else:
            above = sum(1 for i in range(200000) if h(i * period / 200000) > target) * period / 200000
            require(abs(float(Fraction(values["d"])) - above) < period / 1000, "Independent duration failed")
            require(ib.close(values["c"], h(p["at"])), "Independent height failed")
        return True