"""IB AI SL bivariate statistics: Pearson's r, the regression line of y on
x, Spearman's rank correlation with tied ranks, and when an estimate from
the line is valid.

Data follow y = intercept + slope * x + noise. Every statistic is exact
except the square root in r, which uses mpmath. Strength descriptions use
the guide printed in the question, and values within 0.005 of a band
boundary are rejected so the description never depends on rounding.
"""
from fractions import Fraction

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from ..rounding import decimal_text
from . import common as ib
from . import distributions as dist


# --- Editable pools ---------------------------------------------------------
CONTEXTS = {
    "revision": {"x": "Hours of revision", "y": "Test score", "x_unit": "hour", "y_unit": "marks",
                 "x_values": tuple(range(1, 21)), "slope": (2, 4), "intercept": (20, 40),
                 "noise": 6, "places": 0, "y_noun": "test score", "x_noun": "revision"},
    "ice_cream": {"x": "Temperature (°C)", "y": "Ice creams sold", "x_unit": "°C",
                  "y_unit": "ice creams", "x_values": tuple(range(12, 35)), "slope": (5, 12),
                  "intercept": (-60, 10), "noise": 18, "places": 0, "y_noun": "number of ice creams sold",
                  "x_noun": "temperature"},
    "cars": {"x": "Age of car (years)", "y": "Value ($1000s)", "x_unit": "year",
             "y_unit": "thousand dollars", "x_values": tuple(range(1, 13)),
             "slope": (-3, -1), "intercept": (25, 40), "noise": 2, "places": 1, "y_noun": "value", "x_noun": "age"},
    "apartments": {"x": "Distance from centre (km)", "y": "Price ($ millions)", "x_unit": "km",
                   "y_unit": "million dollars", "x_values": tuple(range(2, 25)),
                   "slope": (-0.12, -0.05), "intercept": (2, 3), "noise": 0.15, "places": 2,
                   "y_noun": "price", "x_noun": "distance from the centre"},
    "arm_span": {"x": "Height (cm)", "y": "Arm span (cm)", "x_unit": "cm", "y_unit": "cm",
                 "x_values": tuple(range(150, 191)), "slope": (0.9, 1.1), "intercept": (-10, 10),
                 "noise": 4, "places": 0, "y_noun": "arm span", "x_noun": "height"},
}
# Strength guide printed in the question (as in a recent IB paper).
GUIDE = ((Fraction(0), "very weak"), (Fraction(2, 10), "weak"), (Fraction(4, 10), "moderate"),
         (Fraction(6, 10), "strong"), (Fraction(8, 10), "very strong"))
GUIDE_TEXT = ("Guide for |r|: 0 to 0.199 very weak; 0.2 to 0.399 weak; 0.4 to 0.599 moderate; "
              "0.6 to 0.799 strong; 0.8 to 1 very strong.")
SIZES = tuple(range(6, 10))
NAMES_FOR_ESTIMATES = ib.NAMES


# ------------------------------------------------------------ mathematics

def as_numbers(texts):
    return [Fraction(t) for t in texts]


def sums(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return mx, my, sxx, syy, sxy


def pearson(xs, ys):
    _, _, sxx, syy, sxy = sums(xs, ys)
    return sxy / dist.square_root(sxx * syy)


def regression(xs, ys):
    """(gradient, intercept) of the least-squares line of y on x, exactly."""
    mx, my, sxx, _, sxy = sums(xs, ys)
    gradient = sxy / sxx
    return gradient, my - gradient * mx


def ranks(values):
    """Rank 1 for the largest value; tied values share the mean of their ranks."""
    ordered = sorted(values, reverse=True)
    result = []
    for value in values:
        first = ordered.index(value) + 1
        count = ordered.count(value)
        result.append(Fraction(2 * first + count - 1, 2))
    return result


def strength(r):
    size = abs(r)
    label = GUIDE[0][1]
    for start, name in GUIDE:
        if size >= start:
            label = name
    return label


def near_boundary(r):
    return any(abs(abs(r) - start) < Fraction(5, 1000) for start, _ in GUIDE[1:])


def line_text(gradient, intercept):
    sign = "-" if intercept < 0 else "+"
    return "y = {}x {} {}".format(ib.sf3(gradient), sign, ib.sf3(abs(intercept)))


def rank_text(value):
    return decimal_text(value)


# ------------------------------------------------------------ generator

class Correlation(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.statistics.correlation",
        version=1,
        topic=ib.TOPIC,
        subtopic="statistics_and_probability",
        title="Correlation and regression",
        difficulty_descriptions={
            1: "Pearson's r and a description of the correlation.",
            2: "Regression line, an estimate, and the gradient in context.",
            3: "Spearman's rank correlation with tied ranks, interpreted in context.",
            4: "r, the line, interpolation against extrapolation, and validity.",
        },
        tags=ib.BASE_TAGS + ("correlation", "regression", "pearson", "spearman"),
    )
    keys = {
        1: {"context", "x", "y"},
        2: {"context", "x", "y", "estimate_x"},
        3: {"context", "x", "y"},
        4: {"context", "name", "x", "y", "estimate_x", "outside_x"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        name = rng.choice(tuple(CONTEXTS))
        c = CONTEXTS[name]
        xs = sorted(rng.sample(c["x_values"], rng.choice(SIZES)))
        slope = rng.uniform(*c["slope"])
        intercept = rng.uniform(*c["intercept"])
        noise = c["noise"] * (2.5 if level == 3 else rng.choice((0.5, 1, 1.5, 2.5)))
        places = c["places"] if level != 3 else min(c["places"], 0) - (1 if c["noise"] >= 10 else 0)
        scale = 10 ** max(places, 0)
        ys = []
        for x in xs:
            y = intercept + slope * x + rng.gauss(0, noise)
            if places < 0:
                y = round(y / 10) * 10
                ys.append(str(int(y)))
            else:
                ys.append(decimal_text(Fraction(round(y * scale), scale)))
        p = {"context": name, "x": [str(x) for x in xs], "y": ys}
        if level in (2, 4):
            inside = [x for x in range(xs[0] + 1, xs[-1]) if x not in xs]
            p["estimate_x"] = str(rng.choice(inside)) if inside else str(xs[0])
        if level == 4:
            p["name"] = rng.choice(ib.NAMES)
            gap = max(2, (xs[-1] - xs[0]) // 2)
            p["outside_x"] = str(xs[-1] + rng.randint(gap, 2 * gap))
        return p

    def check_rules(self, p, level):
        require(p["context"] in CONTEXTS, "Unknown context")
        c = CONTEXTS[p["context"]]
        for key in ("x", "y"):
            require(isinstance(p[key], list) and len(p[key]) in SIZES
                    and all(isinstance(v, str) for v in p[key]), "Data outside rules")
        require(len(p["x"]) == len(p["y"]), "Columns differ in length")
        xs, ys = as_numbers(p["x"]), as_numbers(p["y"])
        require(all(x in c["x_values"] for x in xs) and len(set(xs)) == len(xs)
                and xs == sorted(xs), "x values outside rules")
        require(all(y > 0 for y in ys) and len(set(ys)) > 2, "y values outside rules")
        r = pearson(xs, ys)
        require(not near_boundary(r), "r too near a guide boundary")
        if level == 3:
            require(len(set(ys)) < len(ys), "Level 3 needs a tie in y")
            rs = pearson(ranks(xs), ranks(ys))
            require(not near_boundary(rs) and abs(rs) >= Fraction(2, 10), "r_s outside rules")
        else:
            require(abs(r) >= Fraction(6, 10), "Correlation too weak for this level")
        if level in (2, 4):
            estimate = Fraction(p["estimate_x"])
            require(xs[0] < estimate < xs[-1] and estimate not in xs, "Estimate must interpolate")
            gradient, intercept = regression(xs, ys)
            require(gradient * estimate + intercept > 0, "Estimate must be positive")
        if level == 4:
            require(p["name"] in ib.NAMES, "Unknown name")
            require(Fraction(p["outside_x"]) > xs[-1] + 1, "Second estimate must extrapolate")
            require(abs(r) >= Fraction(8, 10), "Level 4 needs very strong correlation")

    def parts(self, p, level):
        c = CONTEXTS[p["context"]]
        xs, ys = as_numbers(p["x"]), as_numbers(p["y"])
        context = ["The table shows {} pairs of data.".format(len(xs)),
                   "{}: {}".format(c["x"], ", ".join(p["x"])),
                   "{}: {}".format(c["y"], ", ".join(p["y"]))]
        r = pearson(xs, ys)
        direction = "positive" if r > 0 else "negative"
        if level == 1:
            context.append(GUIDE_TEXT)
            return ib.assemble(context, [
                ib.part("a", "Find Pearson's product-moment correlation coefficient, r.", 2,
                        "r = " + ib.sf3(r), r),
                ib.part("b", "Use the guide to describe the correlation.", 2,
                        "{} {}".format(strength(r).capitalize(), direction)),
            ])
        gradient, intercept = regression(xs, ys)
        if level == 2:
            estimate_x = Fraction(p["estimate_x"])
            estimate = gradient * estimate_x + intercept
            change = "increases" if gradient > 0 else "decreases"
            meaning = "For each extra {} of {}, the {} {} by about {} {}.".format(
                c["x_unit"], c["x_noun"], c["y_noun"], change,
                ib.sf3(abs(gradient)), c["y_unit"])
            return ib.assemble(context, [
                ib.part("a", "Find the equation of the regression line of y on x.", 2,
                        line_text(gradient, intercept), gradient),
                ib.part("b", "Use your line to estimate y when x = {}.".format(p["estimate_x"]), 2,
                        ib.sf3(estimate), estimate),
                ib.part("c", "Interpret the gradient of the line in context.", 1, meaning),
            ])
        if level == 3:
            x_ranks, y_ranks = ranks(xs), ranks(ys)
            rs = pearson(x_ranks, y_ranks)
            context.append("The largest value of each variable is given rank 1.")
            context.append(GUIDE_TEXT)
            rs_direction = "positive" if rs > 0 else "negative"
            meaning = "{} {} correlation: {} tends to {} as {} increases.".format(
                strength(rs).capitalize(), rs_direction, c["y_noun"],
                "increase" if rs > 0 else "decrease", c["x_noun"])
            return ib.assemble(context, [
                ib.part("a", "Write down the ranks of the y values.", 2,
                        ", ".join(rank_text(v) for v in y_ranks)),
                ib.part("b", "Find Spearman's rank correlation coefficient, r_s.", 2,
                        "r_s = " + ib.sf3(rs), rs),
                ib.part("c", "Use the guide to describe the correlation, and interpret it in "
                        "context.", 2, meaning),
            ])
        estimate_x = Fraction(p["estimate_x"])
        estimate = gradient * estimate_x + intercept
        low, high = p["x"][0], p["x"][-1]
        return ib.assemble(context, [
            ib.part("a", "Find Pearson's product-moment correlation coefficient, r.", 1,
                    "r = " + ib.sf3(r), r),
            ib.part("b", "Find the equation of the regression line of y on x.", 2,
                    line_text(gradient, intercept), gradient),
            ib.part("c", "Use your line to estimate y when x = {}.".format(p["estimate_x"]), 2,
                    ib.sf3(estimate), estimate),
            ib.part("d", "Give two reasons why your estimate in part (c) is valid.", 2,
                    "|r| = {} shows very strong correlation, and x = {} lies within the data "
                    "range ({} to {}), so this is interpolation.".format(
                        ib.sf3(abs(r)), p["estimate_x"], low, high)),
            ib.part("e", "{} uses the line to estimate y when x = {}. Explain why this estimate "
                    "may not be valid.".format(p["name"], p["outside_x"]), 1,
                    "x = {} is outside the data range ({} to {}), so this is "
                    "extrapolation.".format(p["outside_x"], low, high)),
        ])

    def validate_independently(self, question):
        """numpy.corrcoef and numpy.polyfit; ranks by sorting positions."""
        import numpy
        p, level = question.parameters, question.difficulty
        values, shown = ib.answer_values(question), ib.answer_shown(question)
        xs = [float(Fraction(v)) for v in p["x"]]
        ys = [float(Fraction(v)) for v in p["y"]]
        r = float(numpy.corrcoef(xs, ys)[0, 1])
        gradient, intercept = numpy.polyfit(xs, ys, 1)
        if level in (1, 4):
            require(ib.close(values["a"], r, 1e-8), "Independent r failed")
        if level == 1:
            require(shown["b"].endswith("positive" if r > 0 else "negative"),
                    "Independent direction failed")
        if level in (2, 4):
            label, estimate_label = ("a", "b") if level == 2 else ("b", "c")
            require(ib.close(values[label], float(gradient), 1e-8), "Independent gradient failed")
            estimate = gradient * float(Fraction(p["estimate_x"])) + intercept
            require(ib.close(values[estimate_label], float(estimate), 1e-8),
                    "Independent estimate failed")
        if level == 3:
            def positional_ranks(data):
                order = sorted(range(len(data)), key=lambda i: -data[i])
                result = [0.0] * len(data)
                i = 0
                while i < len(order):
                    j = i
                    while j + 1 < len(order) and data[order[j + 1]] == data[order[i]]:
                        j += 1
                    for k in range(i, j + 1):
                        result[order[k]] = (i + j) / 2 + 1
                    i = j + 1
                return result
            rx, ry = positional_ranks(xs), positional_ranks(ys)
            rs = float(numpy.corrcoef(rx, ry)[0, 1])
            require(ib.close(values["b"], rs, 1e-8), "Independent r_s failed")
            require(shown["a"] == ", ".join(decimal_text(Fraction(v).limit_denominator(2))
                                            for v in ry), "Independent ranks failed")
        return True