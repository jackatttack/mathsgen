"""IB AI SL logarithmic scales and models: pH, decibels and password entropy.

Answers needing a power of ten are given in the form a × 10^k, as IB
papers ask. Logarithms use mpmath at 30 digits; the independent check
uses math.log10 and powers of ten.
"""
from fractions import Fraction

import mpmath

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from .. import rich_blocks as rb
from . import common as ib
from . import distributions as dist


# --- Editable pools ---------------------------------------------------------
SUBSTANCES = (("lemon juice", "2.2"), ("vinegar", "2.8"), ("orange juice", "3.5"),
              ("tomato juice", "4.3"), ("coffee", "5"), ("rainwater", "5.6"),
              ("milk", "6.6"), ("sea water", "8.1"), ("baking soda solution", "9"))
PH_VALUES = tuple("{}.{}".format(w, t) for w in range(1, 13) for t in range(10))
SOUND_LEVELS = tuple(range(30, 121, 5))
ENTROPY_CONSTANT = Fraction(301, 1000)
GUESSES = (500, 1000, 2000, 5000, 20000, 50000, 100000, 250000)
ENTROPIES = tuple(range(10, 61, 2))


# ------------------------------------------------------------ mathematics

def log10(value):
    with mpmath.workdps(dist.PRECISION):
        return dist.fraction(mpmath.log10(dist.mp(value)))


def ten_to(power):
    with mpmath.workdps(dist.PRECISION):
        return dist.fraction(mpmath.power(10, dist.mp(power)))


def scientific(mantissa, exponent):
    """(plain, TeX) for m × 10^k."""
    return ("{} × 10^{}".format(mantissa, exponent),
            "{}\\times10^{{{}}}".format(mantissa, exponent))


# ------------------------------------------------------------ generator

class LogarithmicScales(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.number.logarithms",
        version=1,
        topic=ib.TOPIC,
        subtopic="number_and_algebra",
        title="Logarithmic scales and models",
        difficulty_descriptions={
            1: "pH from a concentration, and a concentration from a pH.",
            2: "pH, then how many times stronger one acid is than another.",
            3: "Decibels: level from intensity, intensity in a × 10^k form, intensity ratios.",
            4: "Password entropy: solve, rearrange to an exponential, standard form, interpret.",
        },
        tags=ib.BASE_TAGS + ("logarithms", "exponentials", "standard_form"),
    )
    keys = {
        1: {"mantissa", "exponent", "ph"},
        2: {"mantissa", "exponent", "first", "second"},
        3: {"mantissa", "exponent", "level", "louder", "quieter"},
        4: {"guesses", "entropy"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        if level in (1, 2):
            p = {"mantissa": rng.randint(1, 9), "exponent": rng.randint(2, 9)}
            if level == 1:
                p["ph"] = rng.choice(PH_VALUES)
            else:
                first, second = sorted(rng.sample(range(len(SUBSTANCES)), 2))
                p.update(first=first, second=second)
            return p
        if level == 3:
            louder, quieter = sorted(rng.sample(SOUND_LEVELS, 2), reverse=True)
            return {"mantissa": rng.randint(1, 9), "exponent": rng.randint(3, 9),
                    "level": rng.choice(SOUND_LEVELS), "louder": louder, "quieter": quieter}
        return {"guesses": rng.choice(GUESSES), "entropy": rng.choice(ENTROPIES)}

    def check_rules(self, p, level):
        if level == 4:
            require(p["guesses"] in GUESSES and p["entropy"] in ENTROPIES, "Values outside pools")
            return
        ib.require_int(p["mantissa"], 1, 9, "Mantissa outside bounds")
        ib.require_int(p["exponent"], 2, 9, "Exponent outside bounds")
        if level == 1:
            require(p["ph"] in PH_VALUES, "pH outside pool")
        elif level == 2:
            ib.require_int(p["first"], 0, len(SUBSTANCES) - 1, "Unknown substance")
            ib.require_int(p["second"], 0, len(SUBSTANCES) - 1, "Unknown substance")
            require(p["first"] < p["second"], "First must be the stronger acid")
        else:
            require(p["exponent"] >= 3, "Exponent outside bounds")
            require(p["level"] in SOUND_LEVELS and p["louder"] in SOUND_LEVELS
                    and p["quieter"] in SOUND_LEVELS and p["louder"] > p["quieter"],
                    "Sound levels outside rules")

    def parts(self, p, level):
        if level in (1, 2):
            concentration = Fraction(p["mantissa"], 10 ** p["exponent"])
            ph = -log10(concentration)
            plain, tex = scientific(p["mantissa"], -p["exponent"])
            context = [[rb.text("The pH of a solution is given by "),
                        rb.maths("\\mathrm{pH}=-\\log_{10}[\\mathrm{H}^{+}]", "pH = -log10[H+]"),
                        rb.text(", where [H+] is the hydrogen-ion concentration in moles per litre.")]]
            first_part = ib.part("a", [rb.text("Find the pH when [H+] = "), rb.maths(tex, plain),
                                       rb.text(".")], 2, ib.sf3(ph), ph)
            if level == 1:
                back = ten_to(-Fraction(p["ph"]))
                return ib.assemble(context, [
                    first_part,
                    ib.part("b", "Find [H+] when the pH is {}. Give your answer in the form a × 10^k, "
                            "where 1 <= a < 10 and k is an integer.".format(p["ph"]), 2,
                            ib.standard_form(back), back),
                ])
            (strong, strong_ph), (weak, weak_ph) = SUBSTANCES[p["first"]], SUBSTANCES[p["second"]]
            ratio = ten_to(Fraction(weak_ph) - Fraction(strong_ph))
            return ib.assemble(context, [
                first_part,
                ib.part("b", "{} has a pH of {} and {} has a pH of {}. Find how many times greater "
                        "the hydrogen-ion concentration of {} is than that of {}.".format(
                            strong.capitalize(), strong_ph, weak, weak_ph, strong, weak), 3,
                        ib.sf3(ratio), ratio),
            ])
        if level == 3:
            intensity = Fraction(p["mantissa"], 10 ** p["exponent"])
            loudness = 10 * log10(intensity * 10 ** 12)
            back = ten_to(Fraction(p["level"], 10) - 12)
            ratio = ten_to(Fraction(p["louder"] - p["quieter"], 10))
            plain, tex = scientific(p["mantissa"], -p["exponent"])
            context = [[rb.text("The loudness of a sound, L decibels, is given by "),
                        rb.maths("L=10\\log_{10}\\left(\\frac{I}{10^{-12}}\\right)",
                                 "L = 10 log10(I / 10^-12)"),
                        rb.text(", where I is the intensity of the sound in W/m^2.")]]
            return ib.assemble(context, [
                ib.part("a", [rb.text("Find the loudness of a sound with intensity "),
                              rb.maths(tex, plain), rb.text(" W/m^2.")], 2,
                        "{} dB".format(ib.sf3(loudness)), loudness),
                ib.part("b", "Find the intensity of a sound of {} dB. Give your answer in the form "
                        "a × 10^k, where 1 <= a < 10 and k is an integer.".format(p["level"]), 2,
                        ib.standard_form(back) + " W/m^2", back),
                ib.part("c", "Find how many times more intense a sound of {} dB is than a sound of "
                        "{} dB.".format(p["louder"], p["quieter"]), 2, ib.sf3(ratio), ratio),
            ])
        entropy = log10(p["guesses"]) / ENTROPY_CONSTANT
        guesses = ten_to(ENTROPY_CONSTANT * p["entropy"])
        context = [[rb.text("The entropy of a password, p bits, and the number of guesses, G, "
                            "needed to find it satisfy "),
                    rb.maths("0.301p=\\log_{10}G", "0.301p = log10(G)"), rb.text(".")]]
        return ib.assemble(context, [
            ib.part("a", "Find p for a password that needs {} guesses.".format(p["guesses"]), 2,
                    "p = " + ib.sf3(entropy), entropy),
            ib.part("b", "Write G as a function of p.", 1, "G = 10^(0.301p)"),
            ib.part("c", "Find G when p = {}. Give your answer in the form a × 10^k, where "
                    "1 <= a < 10 and k is an integer.".format(p["entropy"]), 3,
                    ib.standard_form(guesses), guesses),
            ib.part("d", "The graph of G against p passes through (0, 1). Explain what this means "
                    "for passwords.", 1,
                    "A password with an entropy of 0 bits needs only one guess."),
        ])

    def validate_independently(self, question):
        """math.log10 and powers of ten in floats."""
        import math
        p, level = question.parameters, question.difficulty
        values = ib.answer_values(question)
        if level in (1, 2):
            concentration = p["mantissa"] * 10.0 ** -p["exponent"]
            require(ib.close(values["a"], -math.log10(concentration)), "Independent pH failed")
            if level == 1:
                require(ib.close(values["b"], 10 ** -float(Fraction(p["ph"]))), "Independent [H+] failed")
            else:
                difference = float(Fraction(SUBSTANCES[p["second"]][1]) - Fraction(SUBSTANCES[p["first"]][1]))
                require(ib.close(values["b"], 10 ** difference), "Independent ratio failed")
        elif level == 3:
            intensity = p["mantissa"] * 10.0 ** -p["exponent"]
            require(ib.close(values["a"], 10 * math.log10(intensity / 1e-12)), "Independent loudness failed")
            require(ib.close(values["b"], 1e-12 * 10 ** (p["level"] / 10)), "Independent intensity failed")
            require(ib.close(values["c"], 10 ** ((p["louder"] - p["quieter"]) / 10)), "Independent ratio failed")
        else:
            require(ib.close(values["a"], math.log10(p["guesses"]) / 0.301), "Independent entropy failed")
            require(ib.close(values["c"], 10 ** (0.301 * p["entropy"]), 1e-8), "Independent guesses failed")
        return True