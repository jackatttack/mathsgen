"""IB AI SL trapezoidal rule, with exact areas and percentage error.

Level 1 uses a measured data table. Levels 2 to 4 use a polynomial model
of a hill or dune cross-section, either a x (b - x) or a x^2 (b - x),
chosen so every table value terminates and the peak height is sensible.

Areas come from exact polynomial integration; the independent check uses
SymPy for the integral and numpy.trapz for the estimates.
"""
from fractions import Fraction

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from ..rounding import decimal_text, terminates
from .. import rich_blocks as rb
from . import common as ib


# --- Editable pools ---------------------------------------------------------
H_CHOICES = (1, 2, 5, 10)
# form -> (opening sentence, x label, y label, what the area is called)
DATA_FORMS = {
    "river": ("A surveyor measures the depth of a river at equal intervals across its width.",
              "Distance from bank", "Depth", "the cross-sectional area of the river"),
    "lawn": ("The width of a lawn is measured at equal intervals along its length.",
             "Distance along lawn", "Width", "the area of the lawn"),
}
# context -> (sentence leading into the model, unit)
MODELS = {
    "hill": ("The cross-section of a scale model of a hill is modelled by", "cm"),
    "dune": ("The cross-section of a sand dune is modelled by", "m"),
}
SHAPES = ("hump", "hill")
B_VALUES = (4, 6, 8, 10, 12, 20, 30, 40, 60)
N_VALUES = (4, 5, 6)
DOUBLING_N_VALUES = (2, 3, 4)
PEAK_RANGE = (2, 30)
A_TEXTS = {decimal_text(a): a for a in sorted(
    {Fraction(m, 10 ** k) for k in range(0, 5) for m in (1, 2, 4, 5)})}


# ------------------------------------------------------------ mathematics

def coefficients(shape, a, b):
    """Ascending coefficients: a x (b - x) or a x^2 (b - x)."""
    if shape == "hump":
        return [0, a * b, -a]
    return [0, 0, a * b, -a]


def peak(shape, a, b):
    """Greatest height on 0 <= x <= b (at b/2 or 2b/3)."""
    if shape == "hump":
        return a * b * b / 4
    return 4 * a * b ** 3 / 27


def evaluate(coefficients_list, x):
    return sum(c * x ** power for power, c in enumerate(coefficients_list))


def trapezium(heights, h):
    return Fraction(h) / 2 * (heights[0] + heights[-1] + 2 * sum(heights[1:-1]))


def exact_area(coefficients_list, b):
    return sum(Fraction(c) * Fraction(b) ** (power + 1) / (power + 1)
               for power, c in enumerate(coefficients_list))


def heights_at(coefficients_list, b, n):
    h = Fraction(b, n)
    return [evaluate(coefficients_list, h * i) for i in range(n + 1)]


def model_text(coefficients_list):
    """(plain, TeX) for y = ..., in ascending powers as IB writes models."""
    plain, tex = [], []
    for power, c in enumerate(coefficients_list):
        if c == 0:
            continue
        size = abs(Fraction(c))
        number = "" if size == 1 and power else decimal_text(size)
        if power == 0:
            plain_x = tex_x = ""
        elif power == 1:
            plain_x = tex_x = "x"
        else:
            plain_x, tex_x = "x^{}".format(power), "x^{" + str(power) + "}"
        if plain:
            sign = " - " if c < 0 else " + "
        else:
            sign = "-" if c < 0 else ""
        plain.append(sign + number + plain_x)
        tex.append(sign + number + tex_x)
    return "y = " + "".join(plain), "y = " + "".join(tex)


def has_places(value, places):
    return (Fraction(value) * 10 ** places).denominator == 1


# ------------------------------------------------------------ generator

class TrapezoidalRule(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.calculus.trapezoidal_rule",
        version=1,
        topic=ib.TOPIC,
        subtopic="integration",
        title="Trapezoidal rule and percentage error",
        difficulty_descriptions={
            1: "Estimate an area from a table of measurements.",
            2: "Complete a table from a model, then estimate the area.",
            3: "Estimate, write and evaluate the exact integral, then the percentage error.",
            4: "Estimate with n and 2n intervals, integrate, and compare percentage errors.",
        },
        tags=ib.BASE_TAGS + ("trapezoidal_rule", "integration", "percentage_error"),
    )
    keys = {
        1: {"form", "h", "depths"},
        2: {"context", "shape", "a", "b", "n", "blanks"},
        3: {"context", "shape", "a", "b", "n"},
        4: {"context", "shape", "a", "b", "n"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        if level == 1:
            form = rng.choice(tuple(DATA_FORMS))
            n = rng.randint(4, 6)
            if form == "river":
                tenths = [0] + [rng.randint(5, 80) for _ in range(n - 1)] + [0]
            else:
                tenths = [rng.randint(20, 150) for _ in range(n + 1)]
            return {"form": form, "h": rng.choice(H_CHOICES),
                    "depths": [decimal_text(Fraction(t, 10)) for t in tenths]}
        shape, b = rng.choice(SHAPES), rng.choice(B_VALUES)
        n = rng.choice(N_VALUES if level < 4 else DOUBLING_N_VALUES)
        fitting = [text for text, a in A_TEXTS.items()
                   if PEAK_RANGE[0] <= peak(shape, a, b) <= PEAK_RANGE[1]]
        p = {"context": rng.choice(tuple(MODELS)), "shape": shape,
             "a": rng.choice(fitting) if fitting else "1", "b": b, "n": n}
        if level == 2:
            p["blanks"] = sorted(rng.sample(range(1, n), 2))
        return p

    def check_rules(self, p, level):
        if level == 1:
            require(p["form"] in DATA_FORMS, "Unknown data form")
            require(p["h"] in H_CHOICES, "Width outside pool")
            depths = p["depths"]
            require(isinstance(depths, list) and 5 <= len(depths) <= 7, "Table length outside rules")
            require(all(isinstance(d, str) for d in depths), "Heights must be text")
            values = [Fraction(d) for d in depths]
            require(all(has_places(v, 1) and 0 <= v <= 15 for v in values), "Heights outside rules")
            if p["form"] == "river":
                require(values[0] == 0 == values[-1], "A river is zero deep at each bank")
                require(all(v > 0 for v in values[1:-1]), "Interior depths must be positive")
            else:
                require(all(v > 0 for v in values), "Widths must be positive")
            return
        require(p["context"] in MODELS, "Unknown context")
        require(p["shape"] in SHAPES, "Unknown shape")
        require(p["a"] in A_TEXTS, "Coefficient outside pool")
        require(p["b"] in B_VALUES, "Width outside pool")
        require(p["n"] in (N_VALUES if level < 4 else DOUBLING_N_VALUES), "Intervals outside pool")
        require(p["b"] % p["n"] == 0, "Intervals must have whole-number width")
        a = A_TEXTS[p["a"]]
        require(PEAK_RANGE[0] <= peak(p["shape"], a, p["b"]) <= PEAK_RANGE[1], "Peak outside range")
        coefficients_list = coefficients(p["shape"], a, p["b"])
        heights = heights_at(coefficients_list, p["b"], p["n"])
        require(all(has_places(v, 3) for v in heights), "Table values need at most 3 dp")
        if level == 2:
            blanks = p["blanks"]
            require(isinstance(blanks, list) and len(blanks) == 2, "Two blanks expected")
            require(all(type(i) is int and 1 <= i <= p["n"] - 1 for i in blanks)
                    and blanks[0] < blanks[1], "Blanks outside rules")
            # A symmetric model gives mirrored blanks the same value: too easy.
            require(heights[blanks[0]] != heights[blanks[1]], "Blank values must differ")
        if level == 4:
            require(terminates(Fraction(p["b"], 2 * p["n"])), "Half width must terminate")
        if level >= 3:
            estimate = trapezium(heights, Fraction(p["b"], p["n"]))
            require(estimate != exact_area(coefficients_list, p["b"]), "Estimate is exact")

    def parts(self, p, level):
        if level == 1:
            opening, x_label, y_label, area_name = DATA_FORMS[p["form"]]
            heights = [Fraction(d) for d in p["depths"]]
            positions = [p["h"] * i for i in range(len(heights))]
            estimate = trapezium(heights, p["h"])
            context = [
                opening,
                "{} (m): {}".format(x_label, ", ".join(str(x) for x in positions)),
                "{} (m): {}".format(y_label, ", ".join(p["depths"])),
            ]
            return ib.assemble(context, [
                ib.part("a", "Use the trapezoidal rule to estimate {}.".format(area_name), 2,
                        ib.nice(estimate) + " m^2", estimate),
            ])

        opening, unit = MODELS[p["context"]]
        a, b, n = A_TEXTS[p["a"]], p["b"], p["n"]
        coefficients_list = coefficients(p["shape"], a, b)
        plain_model, tex_model = model_text(coefficients_list)
        context = [[
            rb.text(opening + " "), rb.maths(tex_model, plain_model),
            rb.text(", for x from 0 to {}, where x and y are measured in {}.".format(b, unit)),
        ]]
        squared = " " + unit + "^2"
        h = Fraction(b, n)
        heights = heights_at(coefficients_list, b, n)
        estimate = trapezium(heights, h)
        area = exact_area(coefficients_list, b)

        if level in (2, 3):
            shown_heights = [ib.exact_text(v) for v in heights]
            if level == 2:
                for letter, index in zip(("p", "q"), p["blanks"]):
                    shown_heights[index] = letter
            context.append("x ({}): {}".format(unit, ", ".join(
                ib.exact_text(h * i) for i in range(n + 1))))
            context.append("y ({}): {}".format(unit, ", ".join(shown_heights)))

        if level == 2:
            first, second = p["blanks"]
            return ib.assemble(context, [
                ib.part("a", "Find the value of p.", 1, "p = " + ib.exact_text(heights[first]),
                        heights[first]),
                ib.part("b", "Find the value of q.", 1, "q = " + ib.exact_text(heights[second]),
                        heights[second]),
                ib.part("c", "Use the trapezoidal rule with the values in the table to estimate "
                        "the area of the cross-section.", 2, ib.nice(estimate) + squared, estimate),
            ])

        if level == 3:
            error = abs(estimate - area) / area * 100
            integral = "Area = integral from 0 to {} of ({}) dx".format(b, plain_model[4:])
            return ib.assemble(context, [
                ib.part("a", "Use the trapezoidal rule with the values in the table to estimate "
                        "the area of the cross-section.", 2, ib.nice(estimate) + squared, estimate),
                ib.part("b", "Write down an integral that gives the exact area of the "
                        "cross-section.", 1, integral),
                ib.part("c", "Find the area of the cross-section.", 2,
                        ib.nice(area) + squared, area),
                ib.part("d", "Find the percentage error in your estimate from part (a).", 2,
                        ib.sf3(error) + "%", error),
            ])

        doubled = trapezium(heights_at(coefficients_list, b, 2 * n), Fraction(b, 2 * n))
        error_n = abs(estimate - area) / area * 100
        error_2n = abs(doubled - area) / area * 100
        better = 2 * n if error_2n < error_n else n
        return ib.assemble(context, [
            ib.part("a", "Use the trapezoidal rule with {} intervals of equal width to estimate "
                    "the area of the cross-section.".format(n), 2, ib.nice(estimate) + squared,
                    estimate),
            ib.part("b", "Repeat part (a) using {} intervals of equal width.".format(2 * n), 2,
                    ib.nice(doubled) + squared, doubled),
            ib.part("c", "Use integration to find the area of the cross-section.", 2,
                    ib.nice(area) + squared, area),
            ib.part("d", "Find the percentage error in each of your estimates.", 2,
                    "{}% ({} intervals) and {}% ({} intervals)".format(
                        ib.sf3(error_n), n, ib.sf3(error_2n), 2 * n), error_n),
            ib.part("e", "State which estimate is more accurate.", 1,
                    "The estimate with {} intervals".format(better)),
        ])

    def validate_independently(self, question):
        """SymPy for the exact area; numpy.trapz for every estimate."""
        import numpy
        import sympy
        p, level = question.parameters, question.difficulty
        values, shown = ib.answer_values(question), ib.answer_shown(question)
        if level == 1:
            heights = [float(Fraction(d)) for d in p["depths"]]
            positions = [p["h"] * i for i in range(len(heights))]
            require(ib.close(values["a"], float(numpy.trapz(heights, positions))),
                    "Independent estimate failed")
            return True

        x = sympy.Symbol("x")
        a, b, n = sympy.Rational(p["a"]), p["b"], p["n"]
        model = a * x * (b - x) if p["shape"] == "hump" else a * x ** 2 * (b - x)
        area = float(sympy.integrate(model, (x, 0, b)))

        def estimate(intervals):
            positions = [b * i / intervals for i in range(intervals + 1)]
            heights = [float(model.subs(x, sympy.Rational(b * i, intervals)))
                       for i in range(intervals + 1)]
            return float(numpy.trapz(heights, positions))

        if level == 2:
            first, second = p["blanks"]
            require(sympy.Rational(values["a"]) == model.subs(x, sympy.Rational(b * first, n))
                    and sympy.Rational(values["b"]) == model.subs(x, sympy.Rational(b * second, n)),
                    "Independent table values failed")
            require(ib.close(values["c"], estimate(n)), "Independent estimate failed")
            return True

        rough = estimate(n)
        require(ib.close(values["a"], rough), "Independent estimate failed")
        if level == 3:
            require(ib.close(values["c"], area), "Independent area failed")
            require(ib.close(values["d"], abs(rough - area) / area * 100, 1e-7),
                    "Independent percentage error failed")
            return True
        finer = estimate(2 * n)
        require(ib.close(values["b"], finer) and ib.close(values["c"], area),
                "Independent doubled estimate or area failed")
        require(ib.close(values["d"], abs(rough - area) / area * 100, 1e-7),
                "Independent percentage error failed")
        better = 2 * n if abs(finer - area) < abs(rough - area) else n
        require(shown["e"] == "The estimate with {} intervals".format(better),
                "Independent comparison failed")
        return True