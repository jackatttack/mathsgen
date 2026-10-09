"""IB AI SL descriptive statistics.

Level 1 range, mean and standard deviation; level 2 the effect of adding,
subtracting, multiplying or a percentage change; level 3 grouped data;
level 4 quartiles and an outlier test.

Standard deviation is the population value (sigma), as the GDC gives it.
Quartiles follow the GDC method: for odd n the median is left out of both
halves. Means and variances are exact Fractions.
"""
from fractions import Fraction

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from .. import rich_blocks as rb
from . import common as ib
from . import distributions as dist


# --- Editable pools ---------------------------------------------------------
CONTEXTS = {
    "chairs": {"intro": "The prices, in dollars, of {} garden chairs in a shop are:",
               "noun": "price", "unit": "dollars", "range": (40, 260)},
    "commute": {"intro": "The times, in minutes, that {} students take to travel to school are:",
                "noun": "time", "unit": "minutes", "range": (5, 60)},
    "scores": {"intro": "The scores of {} students in a test marked out of 80 are:",
               "noun": "score", "unit": "marks", "range": (20, 80)},
    "tomatoes": {"intro": "The masses, in grams, of {} tomatoes from a greenhouse are:",
                 "noun": "mass", "unit": "g", "range": (60, 140)},
}
CHANGES = {
    "add": ("increased by {} {}", ("5", "10", "15", "20")),
    "subtract": ("decreased by {} {}", ("2", "4", "5")),
    "multiply": ("multiplied by {}", ("0.8", "1.5", "2", "3")),
    "percent": ("increased by {}%", ("5", "10", "20", "25")),
}
GROUPED = {
    "heights": {"intro": "The heights, h cm, of {} students are recorded below.", "symbol": "h",
                "boundaries": ((140, 160, 170, 180, 190, 210), (150, 160, 170, 180, 190, 200),
                               (145, 155, 165, 175, 185, 195))},
    "waiting": {"intro": "The times, t minutes, that {} customers wait at a bank are recorded "
                         "below.", "symbol": "t",
                "boundaries": ((0, 5, 10, 15, 20, 30), (0, 10, 20, 30, 40, 60),
                               (0, 2, 4, 6, 8, 10))},
}
SIZES = tuple(range(8, 13))
QUARTILE_SIZES = tuple(range(11, 16))


# ------------------------------------------------------------ mathematics

def mean(values):
    return Fraction(sum(values), len(values))


def population_variance(values):
    centre = mean(values)
    return sum((v - centre) ** 2 for v in values) / len(values)


def median_of(ordered):
    n = len(ordered)
    middle = n // 2
    if n % 2:
        return Fraction(ordered[middle])
    return Fraction(ordered[middle - 1] + ordered[middle], 2)


def quartiles(values):
    """(Q1, median, Q3) by the GDC method."""
    ordered = sorted(values)
    n = len(ordered)
    return median_of(ordered[:n // 2]), median_of(ordered), median_of(ordered[(n + 1) // 2:])


def changed(centre, spread, change, amount):
    """(new mean, new sd) after every value is changed."""
    amount = Fraction(amount)
    if change == "add":
        return centre + amount, spread
    if change == "subtract":
        return centre - amount, spread
    factor = amount if change == "multiply" else 1 + amount / 100
    return centre * factor, spread * factor


def grouped_summary(boundaries, frequencies):
    midpoints = [Fraction(a + b, 2) for a, b in zip(boundaries, boundaries[1:])]
    total = sum(frequencies)
    centre = sum(m * f for m, f in zip(midpoints, frequencies)) / total
    variance = sum(f * (m - centre) ** 2 for m, f in zip(midpoints, frequencies)) / total
    return midpoints, centre, variance


def fences(values):
    low, _, high = quartiles(values)
    spread = high - low
    return low - Fraction(3, 2) * spread, high + Fraction(3, 2) * spread


def class_runs(symbol, low, high):
    return [rb.maths("{} \\leq {} < {}".format(low, symbol, high),
                     "{} <= {} < {}".format(low, symbol, high))]


# ------------------------------------------------------------ generator

class DescriptiveStatistics(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.statistics.descriptive",
        version=1,
        topic=ib.TOPIC,
        subtopic="statistics_and_probability",
        title="Descriptive statistics",
        difficulty_descriptions={
            1: "Range, mean and standard deviation of a data list.",
            2: "Mean and standard deviation, then the effect of changing every value.",
            3: "Grouped data: mid-interval value, estimated mean and sd, modal class.",
            4: "Median, quartiles and IQR, then an outlier test.",
        },
        tags=ib.BASE_TAGS + ("descriptive_statistics", "mean", "standard_deviation",
                             "quartiles", "outliers"),
    )
    keys = {
        1: {"context", "values"},
        2: {"context", "values", "change", "amount"},
        3: {"context", "boundaries", "frequencies", "class_index"},
        4: {"context", "values", "side"},
    }

    def build(self, level, rng):
        return ib.pick_valid(rng, lambda r: self.candidate(level, r),
                             lambda p: self.check_rules(p, level))

    def candidate(self, level, rng):
        if level == 3:
            context = rng.choice(tuple(GROUPED))
            boundaries = list(rng.choice(GROUPED[context]["boundaries"]))
            classes = len(boundaries) - 1
            peak = rng.randrange(classes)
            frequencies = [max(2, rng.randint(25, 70) - 12 * abs(i - peak) + rng.randint(-6, 6))
                           for i in range(classes)]
            return {"context": context, "boundaries": boundaries, "frequencies": frequencies,
                    "class_index": rng.randrange(classes)}
        context = rng.choice(tuple(CONTEXTS))
        low, high = CONTEXTS[context]["range"]
        size = rng.choice(QUARTILE_SIZES if level == 4 else SIZES)
        values = [rng.randint(low, high) for _ in range(size)]
        p = {"context": context, "values": values}
        if level == 2:
            change = rng.choice(tuple(CHANGES))
            p.update(change=change, amount=rng.choice(CHANGES[change][1]))
        elif level == 4:
            side = rng.choice(("high", "low"))
            ordered = sorted(values)
            spread = ordered[-3] - ordered[2]
            if rng.random() < 0.5:
                # Push one value well past a fence, so some answers are "yes".
                if side == "high":
                    values[values.index(max(values))] = ordered[-3] + 2 * spread + rng.randint(1, 10)
                else:
                    values[values.index(min(values))] = max(1, ordered[2] - 2 * spread - rng.randint(1, 10))
            p["side"] = side
        return p

    def check_rules(self, p, level):
        if level == 3:
            require(p["context"] in GROUPED, "Unknown context")
            boundaries = p["boundaries"]
            require(isinstance(boundaries, list)
                    and tuple(boundaries) in GROUPED[p["context"]]["boundaries"],
                    "Classes outside pool")
            frequencies = p["frequencies"]
            require(isinstance(frequencies, list) and len(frequencies) == len(boundaries) - 1
                    and all(type(f) is int and 1 <= f <= 100 for f in frequencies),
                    "Frequencies outside rules")
            require(frequencies.count(max(frequencies)) == 1, "Modal class must be unique")
            ib.require_int(p["class_index"], 0, len(frequencies) - 1, "Class outside table")
            return
        require(p["context"] in CONTEXTS, "Unknown context")
        values = p["values"]
        sizes = QUARTILE_SIZES if level == 4 else SIZES
        require(isinstance(values, list) and len(values) in sizes, "Data size outside rules")
        require(all(type(v) is int and v > 0 for v in values), "Values must be positive integers")
        if level != 4:
            low, high = CONTEXTS[p["context"]]["range"]
            require(all(low <= v <= high for v in values), "Values outside range")
        require(len(set(values)) >= len(values) - 3, "Too many repeated values")
        if level == 2:
            require(p["change"] in CHANGES and p["amount"] in CHANGES[p["change"]][1],
                    "Change outside pool")
            if p["change"] == "subtract":
                require(min(values) > Fraction(p["amount"]), "Values must stay positive")
        if level == 4:
            require(p["side"] in ("high", "low"), "Unknown side")
            low_fence, high_fence = fences(values)
            suspect = max(values) if p["side"] == "high" else min(values)
            fence = high_fence if p["side"] == "high" else low_fence
            require(abs(suspect - fence) >= 1, "Suspect value too near the fence")
            require(len(set(values)) == len(values) or True, "")

    def parts(self, p, level):
        if level == 3:
            return self.grouped_parts(p)
        c = CONTEXTS[p["context"]]
        values, unit = p["values"], c["unit"]
        context = [c["intro"].format(len(values)), ", ".join(str(v) for v in values)]
        centre = mean(values)
        spread = dist.square_root(population_variance(values))
        if level == 1:
            spread_range = max(values) - min(values)
            return ib.assemble(context, [
                ib.part("a", "Find the range.", 1, "{} {}".format(spread_range, unit), spread_range),
                ib.part("b", "Find the mean.", 2, "{} {}".format(ib.nice(centre), unit), centre),
                ib.part("c", "Find the standard deviation.", 2,
                        "{} {}".format(ib.sf3(spread), unit), spread),
            ])
        if level == 2:
            template, _ = CHANGES[p["change"]]
            how = (template.format(p["amount"], unit) if p["change"] in ("add", "subtract")
                   else template.format(p["amount"]))
            new_centre, new_spread = changed(centre, spread, p["change"], p["amount"])
            return ib.assemble(context, [
                ib.part("a", "Find the mean.", 1, ib.nice(centre), centre),
                ib.part("b", "Find the standard deviation.", 2, ib.sf3(spread), spread),
                ib.part("c", "Every {} is {}. Write down the new mean and the new standard "
                        "deviation.".format(c["noun"], how), 2,
                        "mean {}, standard deviation {}".format(ib.nice(new_centre), ib.sf3(new_spread)),
                        new_centre),
            ])
        q1, middle, q3 = quartiles(values)
        low_fence, high_fence = fences(values)
        suspect = max(values) if p["side"] == "high" else min(values)
        if p["side"] == "high":
            outlier = suspect > high_fence
            reason = "Q3 + 1.5 × IQR = {}, and {} {} {}".format(
                ib.nice(high_fence), suspect, ">" if outlier else "<", ib.nice(high_fence))
        else:
            outlier = suspect < low_fence
            reason = "Q1 - 1.5 × IQR = {}, and {} {} {}".format(
                ib.nice(low_fence), suspect, "<" if outlier else ">", ib.nice(low_fence))
        verdict = "{}: {}.".format("Yes, it is an outlier" if outlier else "No, it is not an outlier",
                                   reason)
        return ib.assemble(context, [
            ib.part("a", "Find the median.", 1, ib.nice(middle), middle),
            ib.part("b", "Find the lower quartile and the upper quartile.", 2,
                    "Q1 = {}, Q3 = {}".format(ib.nice(q1), ib.nice(q3)), q1),
            ib.part("c", "Find the interquartile range.", 1, ib.nice(q3 - q1), q3 - q1),
            ib.part("d", "Determine whether {} is an outlier. Justify your answer.".format(suspect),
                    2, verdict),
        ])

    def grouped_parts(self, p):
        g = GROUPED[p["context"]]
        boundaries, frequencies = p["boundaries"], p["frequencies"]
        midpoints, centre, variance = grouped_summary(boundaries, frequencies)
        context = [g["intro"].format(sum(frequencies))]
        for low, high, frequency in zip(boundaries, boundaries[1:], frequencies):
            context.append(class_runs(g["symbol"], low, high) + [rb.text(": {}".format(frequency))])
        index = p["class_index"]
        modal = frequencies.index(max(frequencies))
        spread = dist.square_root(variance)
        return ib.assemble(context, [
            ib.part("a", class_runs(g["symbol"], boundaries[index], boundaries[index + 1])
                    and [rb.text("Write down the mid-interval value of the class ")]
                    + class_runs(g["symbol"], boundaries[index], boundaries[index + 1])
                    + [rb.text(".")], 1, ib.nice(midpoints[index]), midpoints[index]),
            ib.part("b", "Estimate the mean.", 2, ib.nice(centre), centre),
            ib.part("c", "Estimate the standard deviation.", 2, ib.sf3(spread), spread),
            ib.part("d", "Write down the modal class.", 1, "{} <= {} < {}".format(
                boundaries[modal], g["symbol"], boundaries[modal + 1])),
        ])

    def validate_independently(self, question):
        """statistics for lists; weighted numpy for grouped data."""
        import statistics
        p, level = question.parameters, question.difficulty
        values, shown = ib.answer_values(question), ib.answer_shown(question)
        if level == 3:
            import numpy
            bounds = p["boundaries"]
            middles = [(a + b) / 2 for a, b in zip(bounds, bounds[1:])]
            centre = numpy.average(middles, weights=p["frequencies"])
            spread = numpy.sqrt(numpy.average((numpy.array(middles) - centre) ** 2,
                                              weights=p["frequencies"]))
            require(ib.close(values["a"], middles[p["class_index"]]), "Independent midpoint failed")
            require(ib.close(values["b"], float(centre)) and ib.close(values["c"], float(spread)),
                    "Independent grouped summary failed")
            return True
        data = p["values"]
        if level == 1:
            require(Fraction(values["a"]) == max(data) - min(data), "Independent range failed")
            require(ib.close(values["b"], statistics.mean(data))
                    and ib.close(values["c"], statistics.pstdev(data)), "Independent summary failed")
        elif level == 2:
            amount = float(Fraction(p["amount"]))
            if p["change"] == "add":
                moved = [v + amount for v in data]
            elif p["change"] == "subtract":
                moved = [v - amount for v in data]
            elif p["change"] == "multiply":
                moved = [v * amount for v in data]
            else:
                moved = [v * (1 + amount / 100) for v in data]
            require(ib.close(values["a"], statistics.mean(data))
                    and ib.close(values["b"], statistics.pstdev(data)), "Independent summary failed")
            require(ib.close(values["c"], statistics.mean(moved)), "Independent new mean failed")
            require(ib.sf3(Fraction(statistics.pstdev(moved)).limit_denominator(10 ** 9))
                    in shown["c"], "Independent new sd failed")
        else:
            ordered = sorted(data)
            n = len(ordered)
            q1 = statistics.median(ordered[:n // 2])
            q3 = statistics.median(ordered[n - n // 2:])
            require(ib.close(values["a"], statistics.median(data)), "Independent median failed")
            require(ib.close(values["b"], q1) and ib.close(values["c"], q3 - q1),
                    "Independent quartiles failed")
            iqr = q3 - q1
            if p["side"] == "high":
                outlier = max(data) > q3 + 1.5 * iqr
            else:
                outlier = min(data) < q1 - 1.5 * iqr
            require(shown["d"].startswith("Yes") == outlier, "Independent outlier test failed")
        return True