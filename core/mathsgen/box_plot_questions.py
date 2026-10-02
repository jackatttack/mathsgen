"""Box plots: reading, drawing, comparing, interpreting and working backwards.

The renderer in boxplots.py draws a five-number summary on a shared scale,
and a group whose values are None leaves an empty row at the same scale,
which is exactly the drawing space a construction question needs.

Levels and forms (version 2):
  1  read a statistic; the percentage less than, greater than or between
     quartiles (25, 50, 75%); how many values lie there when the total is known
  2  find the five-number summary of 7, 11 or 15 values and draw the plot
  3  the difference between two plots; compare two distributions in words;
     estimate the percentage below or above a value halfway into a section
  4  recover a missing value from a range or IQR; draw a box plot from a
     cumulative frequency graph

Each section of a box plot holds a quarter of the data. The halfway
questions (12.5%, 37.5%, 62.5%, 87.5%) assume values are spread evenly
within a section, so those prompts always say "estimate".

Raw data is integer and sample sizes place quartiles exactly with the
(n+1)/4 position method taught in the UK, so nothing is interpolated.
Cumulative frequency graphs come from the datasets whose quartile readings
are whole numbers.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)
from .cumulative_frequency import GRAPH_DATASETS, graph_points, quartile_values


# --- Editable teaching choices -------------------------------------------------
# Sizes where (n+1) divides by 4, so quartiles land exactly on data values.
EXACT_SIZES = (7, 11, 15)

# (description, axis label, plural noun used in questions)
CONTEXTS = (
    ("the heights of some plants", "Height (cm)", "heights"),
    ("the times taken to finish a puzzle", "Time (minutes)", "times"),
    ("the marks scored in a test", "Mark", "marks"),
    ("the masses of some parcels", "Mass (kg)", "masses"),
)

COMPARISON_GROUPS = (
    ("Class A", "Class B"),
    ("Monday", "Friday"),
    ("Machine 1", "Machine 2"),
)

# What a read or difference question can ask for.
READINGS = ("median", "range", "interquartile range", "lower quartile")

# Totals for "how many" questions; each divides exactly into quarters.
COUNT_TOTALS = (40, 60, 80, 100, 120, 200)

# Region of the data: (side, summary position, quarters of the data inside).
# Summary positions: 1 lower quartile, 2 median, 3 upper quartile.
REGIONS = {
    "below_lower": ("below", 1, 1),
    "below_median": ("below", 2, 2),
    "below_upper": ("below", 3, 3),
    "above_lower": ("above", 1, 3),
    "above_median": ("above", 2, 2),
    "above_upper": ("above", 3, 1),
    "between": ("between", None, 2),
}

# Cumulative frequency to box plot: class layout and how far the stated
# smallest and largest values sit inside the outer class boundaries.
CF_CLASS_WIDTH = 10
CF_STARTS = (0, 10, 20)
EXTREME_OFFSETS = (1, 2, 3, 4)

FORMS = {
    1: ("read", "percent", "count"),
    2: ("construct",),
    3: ("compare", "statements", "estimate"),
    4: ("backwards", "from_cf"),
}

MARKS = {
    "read": 2, "percent": 1, "count": 2,
    "construct": 3,
    "compare": 3, "statements": 2, "estimate": 2,
    "backwards": 3, "from_cf": 4,
}

WORKING_LINES = {
    "read": 2, "percent": 1, "count": 2,
    "construct": 2,
    "compare": 3, "statements": 4, "estimate": 2,
    "backwards": 3, "from_cf": 2,
}


# --- Internal: parameter contracts ------------------------------------------------
PLOT_KEYS = {"form", "context", "step", "group", "summary", "bounds"}
EXPECTED_KEYS = {
    "read": PLOT_KEYS | {"reading"},
    "percent": PLOT_KEYS | {"region"},
    "count": PLOT_KEYS | {"region", "total"},
    "estimate": PLOT_KEYS | {"section", "direction"},
    "construct": {"form", "context", "step", "group", "values", "bounds"},
    "compare": {"form", "context", "step", "groups", "summaries", "bounds", "reading"},
    "statements": {"form", "context", "step", "groups", "summaries", "bounds"},
    "backwards": {"form", "context", "summary", "missing", "reading"},
    "from_cf": {"form", "context", "step", "boundaries", "frequencies",
                "minimum", "maximum"},
}

SUMMARY_NAMES = ("minimum", "lower quartile", "median", "upper quartile", "maximum")


INFO = GeneratorInfo(
    id="data.spread.box_plots", version=2,
    topic="data", subtopic="box_plots",
    title="Box plots and the five-number summary",
    difficulty_descriptions={
        1: "Read a box plot: a statistic, the percentage in a region, or how many values.",
        2: "Find the five-number summary of 7, 11 or 15 values and draw the box plot.",
        3: "Compare two box plots, or estimate the percentage below a value within a section.",
        4: "Find a missing value, or draw a box plot from a cumulative frequency graph.",
    },
    tags=("data", "box plots", "median", "quartiles", "spread", "cumulative frequency"),
)


# --- Mathematical model -------------------------------------------------------------

def five_number_summary(values):
    """Minimum, lower quartile, median, upper quartile and maximum.

    Positions follow the (n+1)/4 method. The caller guarantees a size where
    those positions are whole numbers, so no value is ever interpolated.
    """
    ordered = sorted(values)
    count = len(ordered)
    require(count >= 5, "A summary needs at least five values")
    require((count + 1) % 4 == 0, "Sample size must place quartiles exactly")
    quarter = (count + 1) // 4
    return [
        ordered[0],
        ordered[quarter - 1],
        ordered[2 * quarter - 1],
        ordered[3 * quarter - 1],
        ordered[-1],
    ]


def reading_value(summary, reading):
    """One statistic read from a five-number summary."""
    minimum, lower, median, upper, maximum = summary
    if reading == "median":
        return median
    if reading == "range":
        return maximum - minimum
    if reading == "interquartile range":
        return upper - lower
    require(reading == "lower quartile", "Unknown reading")
    return lower


def region_percent(region):
    return 25 * REGIONS[region][2]


def estimate_value(summary, section):
    """The value halfway into a section; sections are 0 (lower whisker) to 3."""
    return (summary[section] + summary[section + 1]) // 2


def estimate_percent(section, direction):
    """Assumes values are spread evenly within the section."""
    below = Fraction(25 * section) + Fraction(25, 2)
    return below if direction == "below" else 100 - below


def comparison_facts(parameters):
    """Which group has the higher median and which the smaller IQR."""
    first, second = parameters["summaries"]
    medians = (first[2], second[2])
    spreads = (first[3] - first[1], second[3] - second[1])
    higher = 0 if medians[0] > medians[1] else 1
    tighter = 0 if spreads[0] < spreads[1] else 1
    return medians, spreads, higher, tighter


def cf_summary(parameters):
    """Stated extremes with quartiles read from the cumulative frequency graph."""
    lower, median, upper = quartile_values(
        parameters["boundaries"], parameters["frequencies"]
    )
    require(all(value.denominator == 1 for value in (lower, median, upper)),
            "Graph quartiles must be whole numbers")
    return [parameters["minimum"], int(lower), int(median), int(upper),
            parameters["maximum"]]


def axis_for(values, step):
    """A tick range that contains the data and lands on whole steps."""
    low = (min(values) // step) * step
    high = -((-max(values)) // step) * step
    # Keep a clear margin so whiskers never touch the frame.
    return [low - step, high + step]


# --- Presentation -------------------------------------------------------------------

def percent_text(value):
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    require(value.denominator == 2, "Unsupported percentage")
    return "{}.5".format(value.numerator // 2)


def region_phrase(summary, region):
    side, position, _ = REGIONS[region]
    if side == "between":
        return "between {} and {}".format(summary[1], summary[3])
    word = "less than" if side == "below" else "greater than"
    return "{} {}".format(word, summary[position])


def box_plot_asset(groups, bounds, step, label):
    return {
        "kind": "boxplot", "version": 1,
        "range": bounds, "step": step, "label": label,
        "groups": groups,
    }


def cf_graph_asset(parameters, label):
    """The completed cumulative frequency graph students read from."""
    boundaries = parameters["boundaries"]
    frequencies = parameters["frequencies"]
    points = graph_points(boundaries, frequencies)
    return {
        "kind": "plot", "version": 1,
        "x_range": [boundaries[0], boundaries[-1]],
        "y_range": [0, sum(frequencies)],
        "x_step": CF_CLASS_WIDTH, "y_step": 10, "minor_divisions": 2,
        "x_label": label, "y_label": "Cumulative frequency",
        "points": points, "curves": [{"segments": [points]}],
    }


def summary_text(summary):
    return ", ".join(
        "{} {}".format(name, value) for name, value in zip(SUMMARY_NAMES, summary)
    )


def single_plot_instruction(parameters, description, noun):
    form = parameters["form"]
    summary = parameters["summary"]
    opening = "The box plot shows {}.".format(description)
    if form == "read":
        return "{} Find the {}.".format(opening, parameters["reading"])
    if form == "percent":
        return "{} What percentage of the {} are {}?".format(
            opening, noun, region_phrase(summary, parameters["region"])
        )
    if form == "count":
        return "{} The data has {} values. How many of the {} are {}?".format(
            opening, parameters["total"], noun,
            region_phrase(summary, parameters["region"]),
        )
    require(form == "estimate", "Unknown single-plot form")
    word = "less than" if parameters["direction"] == "below" else "greater than"
    return "{} Estimate the percentage of the {} that are {} {}.".format(
        opening, noun, word, estimate_value(summary, parameters["section"])
    )


def presentation(parameters):
    """Return the prompt, student visuals and teacher visuals."""
    form = parameters["form"]
    description, label, noun = CONTEXTS[parameters["context"]]

    if form in ("read", "percent", "count", "estimate"):
        summary = parameters["summary"]
        asset = box_plot_asset(
            [{"label": parameters["group"], "values": summary}],
            parameters["bounds"], parameters["step"], label,
        )
        instruction = single_plot_instruction(parameters, description, noun)
        # The CLI cannot show the plot, so the summary is stated in the
        # fallback text while the PDF shows the drawing alone.
        fallback = "{} The five-number summary is {}.".format(
            instruction, summary_text(summary)
        )
        return Content(fallback, display_text=instruction), (asset,), ()

    if form == "construct":
        values = parameters["values"]
        instruction = (
            "Here are {} values showing {}. Find the five-number summary "
            "and draw the box plot on the grid."
        ).format(len(values), description)
        listed = ", ".join(str(value) for value in values)
        blank = box_plot_asset(
            [{"label": parameters["group"], "values": None}],
            parameters["bounds"], parameters["step"], label,
        )
        answer_asset = box_plot_asset(
            [{"label": parameters["group"], "values": five_number_summary(values)}],
            parameters["bounds"], parameters["step"], label,
        )
        return (
            Content(instruction + " " + listed, display_text=instruction + " " + listed),
            (blank,), (answer_asset,),
        )

    if form in ("compare", "statements"):
        first, second = parameters["summaries"]
        names = parameters["groups"]
        asset = box_plot_asset(
            [{"label": names[0], "values": first},
             {"label": names[1], "values": second}],
            parameters["bounds"], parameters["step"], label,
        )
        if form == "compare":
            instruction = (
                "The box plots show {} for {} and {}. "
                "Find the difference between their {}s."
            ).format(description, names[0], names[1], parameters["reading"])
        else:
            instruction = (
                "The box plots show {} for {} and {}. Compare the distributions "
                "of the {}: make one comparison about the average and one about "
                "the spread."
            ).format(description, names[0], names[1], noun)
        fallback = "{} {} has {}. {} has {}.".format(
            instruction, names[0], summary_text(first), names[1], summary_text(second)
        )
        return Content(fallback, display_text=instruction), (asset,), ()

    if form == "from_cf":
        boundaries = parameters["boundaries"]
        bounds = [boundaries[0], boundaries[-1]]
        step = parameters["step"]
        instruction = (
            "The cumulative frequency graph shows {}. The smallest value is {} "
            "and the largest is {}. Use the graph to draw a box plot on the grid."
        ).format(description, parameters["minimum"], parameters["maximum"])
        listed = "; ".join(
            "({}, {})".format(x, y)
            for x, y in graph_points(boundaries, parameters["frequencies"])
        )
        blank = box_plot_asset(
            [{"label": "Group A", "values": None}], bounds, step, label
        )
        answer_asset = box_plot_asset(
            [{"label": "Group A", "values": cf_summary(parameters)}], bounds, step, label
        )
        return (
            Content(instruction + " The graph joins the points " + listed + ".",
                    display_text=instruction),
            (cf_graph_asset(parameters, label), blank), (answer_asset,),
        )

    # Working backwards: one value of the summary is unknown.
    require(form == "backwards", "Unknown form")
    summary = parameters["summary"]
    missing = parameters["missing"]
    stated = [
        "the {} is {}".format(name, value)
        for index, (name, value) in enumerate(zip(SUMMARY_NAMES, summary))
        if index != missing
    ]
    # Read as a sentence: the known values, then the statistic, then the ask.
    known = "{} and {}".format(", ".join(stated[:-1]), stated[-1])
    instruction = (
        "A box plot shows {}. For this data {}. "
        "The {} is {}. Find the {}."
    ).format(
        description, known, parameters["reading"],
        reading_value(summary, parameters["reading"]), SUMMARY_NAMES[missing],
    )
    return Content(instruction, display_text=instruction), (), ()


def answer_for(parameters):
    form = parameters["form"]
    noun = CONTEXTS[parameters["context"]][2]

    if form == "read":
        value = reading_value(parameters["summary"], parameters["reading"])
        answer = {"kind": "statistic", "name": parameters["reading"], "value": value}
        return answer, Content(str(value))

    if form == "percent":
        value = percent_text(region_percent(parameters["region"]))
        return {"kind": "percentage", "value": value}, Content(value + "%")

    if form == "count":
        value = parameters["total"] * REGIONS[parameters["region"]][2] // 4
        return {"kind": "count", "value": value}, Content(str(value))

    if form == "estimate":
        value = percent_text(
            estimate_percent(parameters["section"], parameters["direction"])
        )
        return {"kind": "percentage", "value": value}, Content(value + "%")

    if form == "construct":
        summary = five_number_summary(parameters["values"])
        answer = {"kind": "five_number_summary", "values": summary}
        return answer, Content(summary_text(summary))

    if form == "from_cf":
        summary = cf_summary(parameters)
        answer = {"kind": "five_number_summary", "values": summary}
        return answer, Content(summary_text(summary))

    if form == "compare":
        first, second = parameters["summaries"]
        reading = parameters["reading"]
        difference = abs(
            reading_value(first, reading) - reading_value(second, reading)
        )
        answer = {
            "kind": "statistic_difference", "name": reading, "value": difference,
        }
        return answer, Content(str(difference))

    if form == "statements":
        names = parameters["groups"]
        medians, spreads, higher, tighter = comparison_facts(parameters)
        answer = {
            "kind": "comparison",
            "higher_median": names[higher], "smaller_iqr": names[tighter],
            "medians": list(medians), "iqrs": list(spreads),
        }
        display = (
            "{} has the higher median ({} compared with {}), so on average its "
            "{} are higher. {} has the smaller interquartile range ({} compared "
            "with {}), so its {} are more consistent."
        ).format(
            names[higher], medians[higher], medians[1 - higher], noun,
            names[tighter], spreads[tighter], spreads[1 - tighter], noun,
        )
        return answer, Content(display)

    missing = parameters["missing"]
    value = parameters["summary"][missing]
    answer = {"kind": "statistic", "name": SUMMARY_NAMES[missing], "value": value}
    return answer, Content(str(value))


# --- Generator -----------------------------------------------------------------------

class BoxPlots:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        require(difficulty in FORMS, "Invalid difficulty")
        rng = context.rng
        form = rng.choice(FORMS[difficulty])
        builders = {
            "read": self.make_read, "percent": self.make_percent,
            "count": self.make_count, "construct": self.make_construct,
            "compare": self.make_compare, "statements": self.make_statements,
            "estimate": self.make_estimate, "backwards": self.make_backwards,
            "from_cf": self.make_from_cf,
        }
        parameters = builders[form](rng)

        prompt, student, teacher = presentation(parameters)
        answer, display = answer_for(parameters)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=MARKS[form], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=WORKING_LINES[form]),
            parameters=parameters, question_visuals=student,
            answer_visuals=teacher,
        )
        self.validate(question)
        return question

    # --- Builders: each returns the complete parameters for one form ---

    def make_values(self, rng, size, low, high):
        """Distinct integers, so the summary has no repeated quartiles."""
        return sorted(rng.sample(range(low, high + 1), size))

    def make_plot(self, rng, form):
        """A single drawn plot: shared by read, percent, count and estimate."""
        values = self.make_values(rng, rng.choice(EXACT_SIZES), 5, 60)
        return {
            "form": form, "context": rng.randrange(len(CONTEXTS)),
            "group": "Group A", "step": 10,
            "summary": five_number_summary(values),
            "bounds": axis_for(values, 10),
        }

    def make_read(self, rng):
        parameters = self.make_plot(rng, "read")
        parameters["reading"] = rng.choice(READINGS)
        return parameters

    def make_percent(self, rng):
        parameters = self.make_plot(rng, "percent")
        parameters["region"] = rng.choice(sorted(REGIONS))
        return parameters

    def make_count(self, rng):
        parameters = self.make_plot(rng, "count")
        parameters["region"] = rng.choice(sorted(REGIONS))
        parameters["total"] = rng.choice(COUNT_TOTALS)
        return parameters

    def make_estimate(self, rng):
        for attempt in range(200):
            parameters = self.make_plot(rng, "estimate")
            summary = parameters["summary"]
            # Only sections with a whole-number halfway value.
            sections = [
                section for section in range(4)
                if (summary[section + 1] - summary[section]) % 2 == 0
            ]
            if not sections:
                continue
            parameters["section"] = rng.choice(sections)
            parameters["direction"] = rng.choice(("below", "above"))
            return parameters
        raise ValueError("Could not construct an estimate question")

    def make_construct(self, rng):
        values = self.make_values(rng, rng.choice(EXACT_SIZES), 5, 60)
        return {
            "form": "construct", "context": rng.randrange(len(CONTEXTS)),
            "group": "Group A", "step": 10, "values": values,
            "bounds": axis_for(values, 10),
        }

    def make_pair(self, rng, form, accept):
        """Two plots on one scale, retried until accept(first, second) holds."""
        context = rng.randrange(len(CONTEXTS))
        names = list(rng.choice(COMPARISON_GROUPS))
        for attempt in range(200):
            first = five_number_summary(self.make_values(rng, 7, 5, 60))
            second = five_number_summary(self.make_values(rng, 7, 5, 60))
            extra = accept(first, second)
            if extra is None:
                continue
            parameters = {
                "form": form, "context": context, "groups": names, "step": 10,
                "summaries": [first, second],
                "bounds": axis_for(first + second, 10),
            }
            parameters.update(extra)
            return parameters
        raise ValueError("Could not construct a suitable comparison")

    def make_compare(self, rng):
        def accept(first, second):
            reading = rng.choice(READINGS)
            # A zero difference makes a comparison question pointless.
            if reading_value(first, reading) == reading_value(second, reading):
                return None
            return {"reading": reading}
        return self.make_pair(rng, "compare", accept)

    def make_statements(self, rng):
        def accept(first, second):
            # Both comparisons need a clear winner.
            if first[2] == second[2]:
                return None
            if first[3] - first[1] == second[3] - second[1]:
                return None
            return {}
        return self.make_pair(rng, "statements", accept)

    def make_backwards(self, rng):
        values = self.make_values(rng, 7, 5, 60)
        summary = five_number_summary(values)
        # The stated statistic must be one the missing value appears in:
        # the range spans minimum to maximum, the interquartile range spans
        # the two quartiles, and neither involves the other pair.
        choices = {
            0: ("range",),
            1: ("interquartile range",),
            3: ("interquartile range",),
            4: ("range",),
        }
        missing = rng.choice(sorted(choices))
        return {
            "form": "backwards", "context": rng.randrange(len(CONTEXTS)),
            "summary": summary, "missing": missing,
            "reading": rng.choice(choices[missing]),
        }

    def make_from_cf(self, rng):
        frequencies = list(rng.choice(GRAPH_DATASETS))
        start = rng.choice(CF_STARTS)
        boundaries = [
            start + CF_CLASS_WIDTH * index for index in range(len(frequencies) + 1)
        ]
        return {
            "form": "from_cf", "context": rng.randrange(len(CONTEXTS)),
            "step": CF_CLASS_WIDTH, "boundaries": boundaries,
            "frequencies": frequencies,
            "minimum": boundaries[0] + rng.choice(EXTREME_OFFSETS),
            "maximum": boundaries[-1] - rng.choice(EXTREME_OFFSETS),
        }

    # --- Validation ---

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in FORMS, "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")

        parameters = question.parameters
        form = parameters.get("form")
        require(form in FORMS[level], "Form does not match difficulty")
        require(set(parameters) == EXPECTED_KEYS[form], "Unexpected parameters")
        require(type(parameters["context"]) is int
                and 0 <= parameters["context"] < len(CONTEXTS), "Unknown context")
        if "step" in parameters:
            require(parameters["step"] == 10, "Unexpected scale step")

        self.check_structure(parameters)

        require(question.marks == MARKS[form], "Marks mismatch")
        answer, display = answer_for(parameters)
        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Display mismatch")
        prompt, student, teacher = presentation(parameters)
        require(question.prompt == prompt, "Prompt mismatch")
        require(question.visual_assets("questions") == student,
                "Student visual mismatch")
        require(question.visual_assets("answers") == teacher,
                "Answer visual mismatch")
        return True

    def check_structure(self, parameters):
        form = parameters["form"]

        def check_summary(summary):
            require(isinstance(summary, list) and len(summary) == 5,
                    "A summary needs five values")
            require(all(type(value) is int for value in summary),
                    "Summary values must be integers")
            require(all(a < b for a, b in zip(summary, summary[1:])),
                    "Summary values must be strictly increasing")

        if form in ("read", "percent", "count", "estimate"):
            summary = parameters["summary"]
            check_summary(summary)
            require(parameters["bounds"] == axis_for(summary, parameters["step"]),
                    "Unexpected drawn scale")
            if form == "read":
                require(parameters["reading"] in READINGS, "Unknown reading")
            elif form in ("percent", "count"):
                require(parameters["region"] in REGIONS, "Unknown region")
                if form == "count":
                    require(parameters["total"] in COUNT_TOTALS, "Unexpected total")
            else:
                section = parameters["section"]
                require(type(section) is int and 0 <= section <= 3, "Invalid section")
                require((summary[section + 1] - summary[section]) % 2 == 0,
                        "Halfway value is not a whole number")
                require(parameters["direction"] in ("below", "above"),
                        "Invalid direction")
            return

        if form == "construct":
            values = parameters["values"]
            require(isinstance(values, list) and len(values) in EXACT_SIZES,
                    "Unexpected sample size")
            require(all(type(value) is int for value in values),
                    "Data values must be integers")
            require(len(set(values)) == len(values), "Data values must be distinct")
            require(values == sorted(values), "Data should be stored in order")
            check_summary(five_number_summary(values))
            require(parameters["bounds"] == axis_for(values, parameters["step"]),
                    "Unexpected drawn scale")
            return

        if form in ("compare", "statements"):
            summaries = parameters["summaries"]
            require(isinstance(summaries, list) and len(summaries) == 2,
                    "A comparison needs two summaries")
            for summary in summaries:
                check_summary(summary)
            require(parameters["groups"] in [list(pair) for pair in COMPARISON_GROUPS],
                    "Unknown comparison groups")
            require(parameters["bounds"]
                    == axis_for(summaries[0] + summaries[1], parameters["step"]),
                    "Unexpected drawn scale")
            first, second = summaries
            if form == "compare":
                reading = parameters["reading"]
                require(reading in READINGS, "Unknown reading")
                require(reading_value(first, reading) != reading_value(second, reading),
                        "Comparison has no difference to find")
            else:
                require(first[2] != second[2], "Medians must differ")
                require(first[3] - first[1] != second[3] - second[1],
                        "Interquartile ranges must differ")
            return

        if form == "from_cf":
            boundaries = parameters["boundaries"]
            frequencies = parameters["frequencies"]
            require(isinstance(frequencies, list)
                    and tuple(frequencies) in GRAPH_DATASETS,
                    "Graph distribution violates teaching bounds")
            require(isinstance(boundaries, list)
                    and len(boundaries) == len(frequencies) + 1
                    and boundaries[0] in CF_STARTS
                    and all(right - left == CF_CLASS_WIDTH
                            for left, right in zip(boundaries, boundaries[1:])),
                    "Invalid class boundaries")
            require(parameters["minimum"] - boundaries[0] in EXTREME_OFFSETS,
                    "Smallest value outside the first class")
            require(boundaries[-1] - parameters["maximum"] in EXTREME_OFFSETS,
                    "Largest value outside the last class")
            check_summary(cf_summary(parameters))
            return

        require(form == "backwards", "Unknown form")
        check_summary(parameters["summary"])
        missing = parameters["missing"]
        require(missing in (0, 1, 3, 4), "Median cannot be recovered this way")
        reading = parameters["reading"]
        # The stated statistic must depend on the missing value.
        involved = {"range": (0, 4), "interquartile range": (1, 3)}
        require(reading in involved and missing in involved[reading],
                "Stated statistic does not involve the missing value")

    def validate_independently(self, question):
        """Recompute each answer from definitions, not from the helpers above."""
        parameters = question.parameters
        form = parameters["form"]
        answer = question.answer

        if form == "construct":
            ordered = sorted(parameters["values"])
            count = len(ordered)
            # Positions are counted from one, as a student would.
            lower_position = (count + 1) // 4
            median_position = (count + 1) // 2
            upper_position = 3 * (count + 1) // 4
            require(4 * lower_position == count + 1, "Quartile position is not exact")
            expected = [
                ordered[0], ordered[lower_position - 1],
                ordered[median_position - 1], ordered[upper_position - 1],
                ordered[-1],
            ]
            require(answer["values"] == expected,
                    "Independent five-number summary disagrees")
            return True

        if form == "from_cf":
            boundaries = parameters["boundaries"]
            points = [[boundaries[0], 0]]
            running = 0
            for index, frequency in enumerate(parameters["frequencies"]):
                running += frequency
                points.append([boundaries[index + 1], running])
            require(question.question_visuals[0]["points"] == points,
                    "Drawn graph disagrees with the frequencies")
            readings = []
            for target in (Fraction(running, 4), Fraction(running, 2),
                           Fraction(3 * running, 4)):
                for first, second in zip(points, points[1:]):
                    if first[1] <= target <= second[1]:
                        readings.append(
                            first[0] + (target - first[1]) * (second[0] - first[0])
                            / Fraction(second[1] - first[1])
                        )
                        break
                else:
                    raise ValueError("Quartile target missing from graph")
            expected = [parameters["minimum"]] + readings + [parameters["maximum"]]
            require([Fraction(value) for value in answer["values"]] == expected,
                    "Independent graph readings disagree")
            return True

        if form in ("compare", "statements"):
            first, second = parameters["summaries"]
            if form == "compare":
                reading = parameters["reading"]
                statistics = [
                    {"median": s[2], "range": s[4] - s[0],
                     "interquartile range": s[3] - s[1], "lower quartile": s[1]}
                    for s in (first, second)
                ]
                difference = abs(statistics[0][reading] - statistics[1][reading])
                require(answer["value"] == difference, "Independent comparison disagrees")
                return True
            names = parameters["groups"]
            higher = names[0] if first[2] > second[2] else names[1]
            tighter = names[0] if first[3] - first[1] < second[3] - second[1] else names[1]
            require(answer["higher_median"] == higher, "Independent median comparison disagrees")
            require(answer["smaller_iqr"] == tighter, "Independent spread comparison disagrees")
            return True

        summary = parameters["summary"]
        minimum, lower, median, upper, maximum = summary

        if form == "read":
            statistics = {
                "median": median, "range": maximum - minimum,
                "interquartile range": upper - lower, "lower quartile": lower,
            }
            require(answer["value"] == statistics[parameters["reading"]],
                    "Independent reading disagrees")
            return True

        if form in ("percent", "count"):
            side, position, _ = REGIONS[parameters["region"]]
            # Each quartile marks off one more quarter of the data.
            if side == "between":
                quarters = 3 - 1
            elif side == "below":
                quarters = position
            else:
                quarters = 4 - position
            if form == "percent":
                require(Fraction(answer["value"]) == 25 * quarters,
                        "Independent percentage disagrees")
            else:
                require(4 * answer["value"] == parameters["total"] * quarters,
                        "Independent count disagrees")
            return True

        if form == "estimate":
            section = parameters["section"]
            low, high = summary[section], summary[section + 1]
            value = Fraction(low + high, 2)
            # Straight-line share of the section's quarter below the value.
            below = 25 * section + 25 * (value - low) / (high - low)
            expected = below if parameters["direction"] == "below" else 100 - below
            require(Fraction(answer["value"]) == expected,
                    "Independent estimate disagrees")
            return True

        missing = parameters["missing"]
        require(answer["value"] == summary[missing],
                "Independent missing value disagrees")
        # The stated statistic must genuinely determine the missing value.
        if parameters["reading"] == "range":
            stated = maximum - minimum
            recovered = maximum - stated if missing == 0 else minimum + stated
        else:
            stated = upper - lower
            recovered = upper - stated if missing == 1 else lower + stated
        require(recovered == summary[missing],
                "Missing value is not recoverable from the stated statistic")
        return True