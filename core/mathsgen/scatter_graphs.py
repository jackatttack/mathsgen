"""Scatter graphs: correlation, outliers, lines of best fit and estimates.

Data are a true line plus stored integer noise, so every point is an exact
integer and fully reproducible from the parameters. Answers follow mark-scheme
style ranges: readings from a drawn line accept a quarter of an axis step;
estimates from the student's own line accept 10% of the axis span around the
least-squares value. Correlation questions use only data with |r| > 0.8 or
|r| < 0.3, never an ambiguous middle.
"""
import math
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


INFO = GeneratorInfo(
    id="data.scatter.graphs", version=1,
    topic="data", subtopic="scatter_graphs",
    title="Scatter graphs: correlation, outliers and lines of best fit",
    difficulty_descriptions={
        1: "Describe the type of correlation, or identify the outlier.",
        2: "Read an estimate from a given line of best fit.",
        3: "Draw a line of best fit to estimate, or describe the relationship in context.",
        4: "Judge an estimate outside the data, or estimate after ignoring an outlier.",
    },
    tags=("statistics", "scatter graphs", "correlation"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("correlation", "outlier"),
    2: ("read_y", "read_x"),
    3: ("estimate", "describe"),
    4: ("reliability", "outlier_estimate"),
}
CONTEXTS = (
    {"x_label": "Hours of revision", "y_label": "Test mark", "x_axis": (0, 12, 2),
     "y_axis": (0, 100, 10), "x_span": (1, 11), "slopes": (5, 6, 7), "intercepts": (15, 30),
     "noise": 6, "x_noun": "number of hours of revision", "y_noun": "test mark",
     "opening": "The scatter graph shows the number of hours some students spent revising "
                "and their test marks."},
    {"x_label": "Temperature (°C)", "y_label": "Hot drinks sold", "x_axis": (0, 35, 5),
     "y_axis": (0, 80, 10), "x_span": (5, 30), "slopes": (-2, -1), "intercepts": (65, 78),
     "noise": 5, "x_noun": "temperature", "y_noun": "number of hot drinks sold",
     "opening": "The scatter graph shows the temperature and the number of hot drinks sold "
                "by a café on some days."},
    {"x_label": "Age of car (years)", "y_label": "Value (£1000s)", "x_axis": (0, 12, 2),
     "y_axis": (0, 24, 4), "x_span": (1, 10), "slopes": (-2,), "intercepts": (20, 22),
     "noise": 2, "x_noun": "age of the car", "y_noun": "value of the car",
     "opening": "The scatter graph shows the age and the value of some cars."},
    {"x_label": "Height (cm)", "y_label": "Arm span (cm)", "x_axis": (140, 200, 10),
     "y_axis": (140, 200, 10), "x_span": (150, 190), "slopes": (1,), "intercepts": (-4, 4),
     "noise": 4, "x_noun": "height", "y_noun": "arm span",
     "opening": "The scatter graph shows the heights and arm spans of some people."},
    {"x_label": "Shoe size", "y_label": "Test mark", "x_axis": (0, 12, 2),
     "y_axis": (0, 100, 10), "x_span": (3, 11), "slopes": (0,), "intercepts": (40, 60),
     "noise": 25, "x_noun": "shoe size", "y_noun": "test mark",
     "opening": "The scatter graph shows the shoe sizes and test marks of some students."},
)
STRONG_CONTEXTS = (0, 1, 2, 3)
POINTS = (8, 12)            # how many points, inclusive
OUTLIER_FACTOR = 4          # an outlier sits at least this many noise-widths off the line
MARKS = {1: 1, 2: 2, 3: 2, 4: 3}
WORKING_LINES = {1: 2, 2: 3, 3: 3, 4: 5}

BASE_KEYS = {"context", "xs", "noise", "slope", "intercept"}
KEYS = {
    "correlation": BASE_KEYS,
    "outlier": BASE_KEYS | {"shift"},
    "read_y": BASE_KEYS | {"target"},
    "read_x": BASE_KEYS | {"target"},
    "estimate": BASE_KEYS | {"target"},
    "describe": BASE_KEYS,
    "reliability": BASE_KEYS | {"target"},
    "outlier_estimate": BASE_KEYS | {"shift", "target"},
}


# ------------------------------------------------------------ mathematics

def points(par):
    shift_at = len(par["xs"]) // 2
    out = []
    for i, (x, e) in enumerate(zip(par["xs"], par["noise"])):
        y = par["slope"] * x + par["intercept"] + e
        if i == shift_at and "shift" in par:
            y += par["shift"]
        out.append((x, y))
    return out


def fitted(data):
    """Least-squares (slope, intercept) as Fractions, from centred sums."""
    n = len(data)
    mx = Fraction(sum(x for x, _ in data), n)
    my = Fraction(sum(y for _, y in data), n)
    sxx = sum((x - mx) ** 2 for x, _ in data)
    sxy = sum((x - mx) * (y - my) for x, y in data)
    slope = sxy / sxx
    return slope, my - slope * mx


def correlation(data):
    n = len(data)
    mx = sum(x for x, _ in data) / n
    my = sum(y for _, y in data) / n
    sxx = sum((x - mx) ** 2 for x, _ in data)
    syy = sum((y - my) ** 2 for _, y in data)
    sxy = sum((x - mx) * (y - my) for x, y in data)
    return sxy / math.sqrt(sxx * syy) if sxx and syy else 0.0


def kind_of(r):
    return "positive" if r > 0 else "negative"


def fit_data(par):
    data = points(par)
    if par["form"] == "outlier_estimate":
        data = [p for i, p in enumerate(data) if i != len(data) // 2]
    return data


def estimate(par):
    """(value, tolerance) for estimate forms."""
    ctx = CONTEXTS[par["context"]]
    if par["form"] == "read_y":
        return Fraction(par["slope"] * par["target"] + par["intercept"]), Fraction(ctx["y_axis"][2], 4)
    if par["form"] == "read_x":
        return Fraction(par["target"] - par["intercept"], par["slope"]), Fraction(ctx["x_axis"][2], 4)
    slope, intercept = fitted(fit_data(par))
    span = ctx["y_axis"][1] - ctx["y_axis"][0]
    return slope * par["target"] + intercept, Fraction(span, 10)


def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    form = par.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(par) == KEYS[form] | {"form"}, "Unexpected parameters")
    require(par["context"] in range(len(CONTEXTS)), "Unknown context")
    if form != "correlation":
        require(par["context"] in STRONG_CONTEXTS, "This form needs a correlated context")
    ctx = CONTEXTS[par["context"]]
    xs, noise = par["xs"], par["noise"]
    require(isinstance(xs, list) and isinstance(noise, list) and len(xs) == len(noise)
            and POINTS[0] <= len(xs) <= POINTS[1], "Unexpected data size")
    require(all(type(v) is int for v in xs + noise), "Integer data required")
    require(xs == sorted(set(xs)) and ctx["x_span"][0] <= xs[0] and xs[-1] <= ctx["x_span"][1],
            "x values must be distinct and inside the context span")
    require(all(abs(e) <= ctx["noise"] for e in noise), "Noise outside bounds")
    require(par["slope"] in ctx["slopes"], "Unexpected slope")
    require(ctx["intercepts"][0] <= par["intercept"] <= ctx["intercepts"][1],
            "Unexpected intercept")
    low_y, high_y = ctx["y_axis"][0], ctx["y_axis"][1]
    require(all(low_y < y < high_y for _, y in points(par)), "Point outside the grid")

    r = correlation(points(par))
    if form == "correlation":
        require(abs(r) > 0.8 or abs(r) < 0.3, "Correlation is ambiguous")
    else:
        require(abs(correlation(fit_data(par) if "shift" in par else points(par))) > 0.8,
                "Correlation too weak")
    if "shift" in par:
        require(type(par["shift"]) is int and abs(par["shift"]) >= OUTLIER_FACTOR * ctx["noise"],
                "Outlier not clear enough")
    if "target" in par:
        require(type(par["target"]) is int, "Integer target required")
        value, _ = estimate(par)
        if form == "read_x":
            require(ctx["x_axis"][0] < value < ctx["x_axis"][1], "Reading off the grid")
        else:
            require(low_y < value < high_y, "Estimate off the grid")
        inside = xs[0] <= par["target"] <= xs[-1]
        if form == "reliability":
            require(not inside and ctx["x_axis"][0] <= par["target"] <= ctx["x_axis"][1]
                    and min(abs(par["target"] - xs[0]), abs(par["target"] - xs[-1]))
                    >= ctx["x_axis"][2] / 2, "Target must lie clearly outside the data")
        elif form != "read_x":
            require(inside, "Target must lie within the data")


# ------------------------------------------------------------ presentation

def plot(par, teacher=False):
    ctx = CONTEXTS[par["context"]]
    x0, x1, xs = ctx["x_axis"]
    y0, y1, ys = ctx["y_axis"]
    visual = {
        "kind": "plot", "version": 1, "x_range": [x0, x1], "y_range": [y0, y1],
        "x_step": xs, "y_step": ys, "minor_divisions": 2, "equal_units": False,
        "x_label": ctx["x_label"], "y_label": ctx["y_label"],
        "points": [[x, y] for x, y in points(par)], "curves": [],
    }
    if par["form"] in ("read_y", "read_x"):
        visual["curves"].append({"segments": [[
            [x0, float(par["slope"] * x0 + par["intercept"])],
            [x1, float(par["slope"] * x1 + par["intercept"])]]]})
    if teacher and par["form"] not in ("read_y", "read_x"):
        slope, intercept = fitted(fit_data(par))
        visual["curves"].append({"segments": [[[x0, float(slope * x0 + intercept)],
                                               [x1, float(slope * x1 + intercept)]]],
                                 "dashed": True})
    if not visual["curves"]:
        del visual["curves"]
    return visual


def prompt_for(par):
    ctx = CONTEXTS[par["context"]]
    form = par["form"]
    listing = "Data (x, y): " + ", ".join("({}, {})".format(x, y) for x, y in points(par)) + "."
    opening = ctx["opening"]
    if form == "correlation":
        task = "Describe the type of correlation shown."
    elif form == "outlier":
        task = "One of the points is an outlier. Write down its coordinates."
    elif form == "read_y":
        task = ("A line of best fit has been drawn. Use it to estimate the {} when the {} is "
                "{}.".format(ctx["y_noun"], ctx["x_noun"], par["target"]))
    elif form == "read_x":
        task = ("A line of best fit has been drawn. Use it to estimate the {} when the {} is "
                "{}.".format(ctx["x_noun"], ctx["y_noun"], par["target"]))
    elif form == "estimate":
        task = ("Draw a line of best fit and use it to estimate the {} when the {} is {}."
                .format(ctx["y_noun"], ctx["x_noun"], par["target"]))
    elif form == "describe":
        task = "Describe the relationship between the {} and the {}.".format(
            ctx["x_noun"], ctx["y_noun"])
    elif form == "reliability":
        task = ("(a) Draw a line of best fit and use it to estimate the {} when the {} is {}. "
                "(b) Explain whether your estimate is reliable.".format(
                    ctx["y_noun"], ctx["x_noun"], par["target"]))
    else:
        task = ("One point is an outlier. Ignoring the outlier, draw a line of best fit and "
                "estimate the {} when the {} is {}.".format(ctx["y_noun"], ctx["x_noun"],
                                                            par["target"]))
    instruction = opening + " " + task
    return Content(instruction + " " + listing, display_text=instruction)


def one_place(value):
    """A decimal to 1 d.p., or a whole number when the value is exact."""
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else "{:.1f}".format(float(value))


def range_text(value, tolerance):
    return "about {} (accept {} to {})".format(
        one_place(value), one_place(value - tolerance), one_place(value + tolerance))


def answer_for(par):
    form = par["form"]
    ctx = CONTEXTS[par["context"]]
    if form == "correlation":
        r = correlation(points(par))
        word = "none" if abs(r) < 0.3 else kind_of(r)
        return ({"kind": "choice", "value": word},
                Content("No correlation" if word == "none" else word.title() + " correlation"))
    if form == "outlier":
        x, y = points(par)[len(par["xs"]) // 2]
        return {"kind": "point", "x": str(x), "y": str(y)}, Content("({}, {})".format(x, y))
    if form == "describe":
        word = kind_of(correlation(points(par)))
        trend = "higher" if word == "positive" else "lower"
        return ({"kind": "choice", "value": word},
                Content("{} correlation: the greater the {}, the {} the {} tends to be.".format(
                    word.title(), ctx["x_noun"], trend, ctx["y_noun"])))
    value, tolerance = estimate(par)
    answer = {"kind": "estimate", "value": rational_text(value),
              "low": rational_text(value - tolerance), "high": rational_text(value + tolerance)}
    text = range_text(value, tolerance)
    if form == "reliability":
        answer["reliable"] = "no"
        text += ("; not reliable, because {} is outside the range of the data "
                 "(extrapolation).".format(par["target"]))
    return answer, Content(text)


def draw_parameters(rng, form):
    if form == "correlation":
        # Choose the correlation type first so positive, negative and none are balanced.
        wanted = rng.choice((1, -1, 0))
        context = rng.choice([i for i, c in enumerate(CONTEXTS)
                              if (c["slopes"][0] > 0) - (c["slopes"][0] < 0) == wanted])
    else:
        context = rng.choice(STRONG_CONTEXTS)
    ctx = CONTEXTS[context]
    count = rng.randint(*POINTS)
    span = list(range(ctx["x_span"][0], ctx["x_span"][1] + 1))
    xs = sorted(rng.sample(span, min(count, len(span))))
    par = {"form": form, "context": context, "xs": xs,
           "noise": [rng.randint(-ctx["noise"], ctx["noise"]) for _ in xs],
           "slope": rng.choice(ctx["slopes"]),
           "intercept": rng.randint(*ctx["intercepts"])}
    if form in ("outlier", "outlier_estimate"):
        size = rng.randint(OUTLIER_FACTOR * ctx["noise"], OUTLIER_FACTOR * ctx["noise"] + 10)
        par["shift"] = size * rng.choice((-1, 1))
    if form in ("read_y", "estimate", "outlier_estimate"):
        par["target"] = rng.randint(xs[0], xs[-1])
    elif form == "read_x":
        par["target"] = rng.randrange(ctx["y_axis"][0] + ctx["y_axis"][2],
                                      ctx["y_axis"][1], ctx["y_axis"][2])
    elif form == "reliability":
        x0, x1, _ = ctx["x_axis"]
        par["target"] = rng.choice([x0, x1])
    return par


# ------------------------------------------------------------ generator

class ScatterGraphs:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        form = rng.choice(FORMS[difficulty])
        for attempt in range(3000):
            par = draw_parameters(rng, form)
            try:
                check_parameters(par, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a scatter graph question")
        answer, display = answer_for(par)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(par),
            answer=answer, answer_display=display, worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=WORKING_LINES[difficulty]),
            parameters=par, question_visuals=(plot(par),),
            answer_visuals=(plot(par, teacher=True),),
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        require(type(q.difficulty) is int and q.difficulty in (1, 2, 3, 4), "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        check_parameters(q.parameters, q.difficulty)
        answer, display = answer_for(q.parameters)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Answer display mismatch")
        require(q.prompt == prompt_for(q.parameters), "Prompt mismatch")
        require(q.visual_assets("questions") == (plot(q.parameters),), "Graph mismatch")
        require(q.visual_assets("answers") == (plot(q.parameters, teacher=True),),
                "Answer graph mismatch")
        return True

    def validate_independently(self, q):
        """Raw-sums least squares, float correlation and a direct residual check."""
        par, answer = q.parameters, q.answer
        form = par.get("form")
        shift_at = len(par["xs"]) // 2
        data = []
        for i, x in enumerate(par["xs"]):
            y = par["slope"] * x + par["intercept"] + par["noise"][i]
            if i == shift_at and "shift" in par:
                y += par["shift"]
            data.append((x, y))
        n = len(data)
        sx, sy = sum(x for x, _ in data), sum(y for _, y in data)
        sxy = sum(x * y for x, y in data)
        sxx, syy = sum(x * x for x, _ in data), sum(y * y for _, y in data)
        r = (n * sxy - sx * sy) / math.sqrt((n * sxx - sx * sx) * (n * syy - sy * sy))

        if form in ("correlation", "describe"):
            expected = "none" if abs(r) < 0.3 else ("positive" if r > 0 else "negative")
            require(answer["value"] == expected, "Independent correlation disagrees")
            return True
        if form == "outlier":
            x, y = int(answer["x"]), int(answer["y"])
            residual = abs(y - (par["slope"] * x + par["intercept"]))
            others = [abs(yy - (par["slope"] * xx + par["intercept"]))
                      for i, (xx, yy) in enumerate(data) if i != shift_at]
            require((x, y) in data and residual > max(others), "Stated point is not the outlier")
            return True
        value = Fraction(answer["value"])
        if form == "read_y":
            expected = Fraction(par["slope"] * par["target"] + par["intercept"])
        elif form == "read_x":
            expected = Fraction(par["target"] - par["intercept"], par["slope"])
        else:
            if form == "outlier_estimate":
                data = [p for i, p in enumerate(data) if i != shift_at]
                n = len(data)
                sx, sy = sum(x for x, _ in data), sum(y for _, y in data)
                sxy = sum(x * y for x, y in data)
                sxx = sum(x * x for x, _ in data)
            slope = Fraction(n * sxy - sx * sy, n * sxx - sx * sx)
            expected = slope * par["target"] + Fraction(sy - slope * sx, n)
        require(value == expected, "Independent estimate disagrees")
        require(Fraction(answer["low"]) < value < Fraction(answer["high"]), "Range must contain the value")
        return True