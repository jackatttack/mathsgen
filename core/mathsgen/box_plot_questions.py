"""Box plots: reading them, drawing them, comparing them and working backwards.

The renderer in boxplots.py draws a five-number summary on a shared scale,
and a group whose values are None leaves an empty row at the same scale,
which is exactly the drawing space a construction question needs.

Difficulty follows the task: level 1 reads a drawn plot, level 2 builds the
summary from raw data and draws it, level 3 compares two distributions on one
scale, and level 4 recovers a missing value from a stated range or spread.

All data is integer, so every quartile is exact. Quartiles use the position
method taught in the UK: with n values the lower quartile sits at (n+1)/4.
Sample sizes are chosen so those positions are whole numbers and no
interpolation is ever required.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)


# --- Editable difficulty bounds -------------------------------------------
# Sizes where (n+1) divides by 4, so quartiles land exactly on data values.
EXACT_SIZES = (7, 11, 15)

CONTEXTS = (
    ("the heights of some plants", "Height (cm)"),
    ("the times taken to finish a puzzle", "Time (minutes)"),
    ("the marks scored in a test", "Mark"),
    ("the masses of some parcels", "Mass (kg)"),
)

COMPARISON_GROUPS = (
    ("Class A", "Class B"),
    ("Monday", "Friday"),
    ("Machine 1", "Machine 2"),
)

# What a level 1 or level 3 question can ask for.
READINGS = ("median", "range", "interquartile range", "lower quartile")


INFO = GeneratorInfo(
    id="data.spread.box_plots", version=1,
    topic="data", subtopic="box_plots",
    title="Box plots and the five-number summary",
    difficulty_descriptions={
        1: "Read the median, range or interquartile range from a box plot.",
        2: "Find the five-number summary from data and draw the box plot.",
        3: "Compare two box plots drawn on the same scale.",
        4: "Find a missing value from a stated range or interquartile range.",
    },
    tags=("data", "box plots", "median", "quartiles", "spread"),
)


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


def axis_for(values, step):
    """A tick range that contains the data and lands on whole steps."""
    low = (min(values) // step) * step
    high = -((-max(values)) // step) * step
    # Keep a clear margin so whiskers never touch the frame.
    return [low - step, high + step]


def box_plot_asset(groups, bounds, step, label):
    return {
        "kind": "boxplot", "version": 1,
        "range": bounds, "step": step, "label": label,
        "groups": groups,
    }


def summary_text(summary):
    names = ("minimum", "lower quartile", "median", "upper quartile", "maximum")
    return ", ".join(
        "{} {}".format(name, value) for name, value in zip(names, summary)
    )


def presentation(parameters):
    form = parameters["form"]
    label = parameters["label"]
    step = parameters["step"]

    if form == "read":
        summary = parameters["summary"]
        bounds = parameters["bounds"]
        asset = box_plot_asset(
            [{"label": parameters["group"], "values": summary}], bounds, step, label
        )
        instruction = "The box plot shows {}. Find the {}.".format(
            parameters["context"], parameters["reading"]
        )
        # The CLI cannot show the plot, so the summary is stated in the
        # fallback text while the PDF shows the drawing alone.
        fallback = "{} The five-number summary is {}.".format(
            instruction, summary_text(summary)
        )
        return Content(fallback, display_text=instruction), (asset,), ()

    if form == "construct":
        values = parameters["values"]
        bounds = parameters["bounds"]
        instruction = (
            "Here are {} values showing {}. Find the five-number summary "
            "and draw the box plot on the grid."
        ).format(len(values), parameters["context"])
        listed = ", ".join(str(value) for value in values)
        blank = box_plot_asset(
            [{"label": parameters["group"], "values": None}], bounds, step, label
        )
        answer_asset = box_plot_asset(
            [{"label": parameters["group"], "values": five_number_summary(values)}],
            bounds, step, label,
        )
        return (
            Content(instruction + " " + listed, display_text=instruction + " " + listed),
            (blank,), (answer_asset,),
        )

    if form == "compare":
        first, second = parameters["summaries"]
        names = parameters["groups"]
        bounds = parameters["bounds"]
        asset = box_plot_asset(
            [{"label": names[0], "values": first},
             {"label": names[1], "values": second}],
            bounds, step, label,
        )
        instruction = (
            "The box plots show {} for {} and {}. "
            "Find the difference between their {}s."
        ).format(parameters["context"], names[0], names[1], parameters["reading"])
        fallback = "{} {} has {}. {} has {}.".format(
            instruction, names[0], summary_text(first), names[1], summary_text(second)
        )
        return Content(fallback, display_text=instruction), (asset,), ()

    # Working backwards: one value of the summary is unknown.
    summary = parameters["summary"]
    missing = parameters["missing"]
    names = ("minimum", "lower quartile", "median", "upper quartile", "maximum")
    stated = [
        "the {} is {}".format(name, value)
        for index, (name, value) in enumerate(zip(names, summary))
        if index != missing
    ]
    # Read as a sentence: the known values, then the statistic, then the ask.
    known = "{} and {}".format(", ".join(stated[:-1]), stated[-1])
    instruction = (
        "A box plot shows {}. For this data {}. "
        "The {} is {}. Find the {}."
    ).format(
        parameters["context"], known, parameters["reading"],
        reading_value(summary, parameters["reading"]), names[missing],
    )
    return Content(instruction, display_text=instruction), (), ()


def answer_for(parameters):
    form = parameters["form"]

    if form == "read":
        value = reading_value(parameters["summary"], parameters["reading"])
        answer = {"kind": "statistic", "name": parameters["reading"], "value": value}
        return answer, Content(str(value))

    if form == "construct":
        summary = five_number_summary(parameters["values"])
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

    missing = parameters["missing"]
    value = parameters["summary"][missing]
    names = ("minimum", "lower quartile", "median", "upper quartile", "maximum")
    answer = {"kind": "statistic", "name": names[missing], "value": value}
    return answer, Content(str(value))


class BoxPlots:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        builders = {
            1: self.make_read, 2: self.make_construct,
            3: self.make_compare, 4: self.make_backwards,
        }
        parameters = builders[difficulty](rng)

        prompt, student, teacher = presentation(parameters)
        answer, display = answer_for(parameters)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=2 if difficulty == 1 else 3, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=2 if difficulty <= 2 else 3),
            parameters=parameters, question_visuals=student,
            answer_visuals=teacher,
        )
        self.validate(question)
        return question

    def make_values(self, rng, size, low, high):
        """Distinct integers, so the summary has no repeated quartiles."""
        return sorted(rng.sample(range(low, high + 1), size))

    def make_read(self, rng):
        context_text, label = rng.choice(CONTEXTS)
        values = self.make_values(rng, rng.choice(EXACT_SIZES), 5, 60)
        step = 10
        return {
            "form": "read", "context": context_text, "label": label,
            "group": "Group A", "step": step,
            "summary": five_number_summary(values),
            "bounds": axis_for(values, step),
            "reading": rng.choice(READINGS),
        }

    def make_construct(self, rng):
        context_text, label = rng.choice(CONTEXTS)
        # Seven values keep the list short enough to read and order by hand.
        values = self.make_values(rng, 7, 5, 60)
        step = 10
        return {
            "form": "construct", "context": context_text, "label": label,
            "group": "Group A", "step": step, "values": values,
            "bounds": axis_for(values, step),
        }

    def make_compare(self, rng):
        context_text, label = rng.choice(CONTEXTS)
        names = list(rng.choice(COMPARISON_GROUPS))
        step = 10
        for attempt in range(200):
            first = five_number_summary(self.make_values(rng, 7, 5, 60))
            second = five_number_summary(self.make_values(rng, 7, 5, 60))
            reading = rng.choice(READINGS)
            # A zero difference makes a comparison question pointless.
            if reading_value(first, reading) == reading_value(second, reading):
                continue
            return {
                "form": "compare", "context": context_text, "label": label,
                "groups": names, "step": step,
                "summaries": [first, second],
                "bounds": axis_for(first + second, step),
                "reading": reading,
            }
        raise ValueError("Could not construct a suitable comparison")

    def make_backwards(self, rng):
        context_text, label = rng.choice(CONTEXTS)
        values = self.make_values(rng, 7, 5, 60)
        summary = five_number_summary(values)
        # The stated statistic must involve the missing value, or the
        # question cannot be answered from what is given.
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
        reading = rng.choice(choices[missing])
        return {
            "form": "backwards", "context": context_text, "label": label,
            "step": 10, "summary": summary,
            "missing": missing, "reading": reading,
        }

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")

        parameters = question.parameters
        expected = {1: "read", 2: "construct", 3: "compare", 4: "backwards"}[level]
        require(parameters.get("form") == expected, "Form does not match difficulty")
        require(parameters["label"] in [label for _, label in CONTEXTS],
                "Unknown axis label")
        require(parameters["step"] > 0, "Step must be positive")

        self.check_structure(parameters, level)

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

    def check_structure(self, parameters, level):
        def check_summary(summary):
            require(isinstance(summary, list) and len(summary) == 5,
                    "A summary needs five values")
            require(all(type(value) is int for value in summary),
                    "Summary values must be integers")
            require(all(a < b for a, b in zip(summary, summary[1:])),
                    "Summary values must be strictly increasing")

        if level == 2:
            values = parameters["values"]
            require(isinstance(values, list) and len(values) in EXACT_SIZES,
                    "Unexpected sample size")
            require(all(type(value) is int for value in values),
                    "Data values must be integers")
            require(len(set(values)) == len(values), "Data values must be distinct")
            require(values == sorted(values), "Data should be stored in order")
            check_summary(five_number_summary(values))
            bounds = parameters["bounds"]
            require(bounds[0] <= min(values) and max(values) <= bounds[1],
                    "Data falls outside the drawn scale")
            return

        if level == 3:
            summaries = parameters["summaries"]
            require(isinstance(summaries, list) and len(summaries) == 2,
                    "A comparison needs two summaries")
            for summary in summaries:
                check_summary(summary)
            require(len(set(parameters["groups"])) == 2,
                    "Comparison groups must be distinct")
            reading = parameters["reading"]
            require(reading in READINGS, "Unknown reading")
            require(reading_value(summaries[0], reading)
                    != reading_value(summaries[1], reading),
                    "Comparison has no difference to find")
            bounds = parameters["bounds"]
            for summary in summaries:
                require(bounds[0] <= summary[0] and summary[4] <= bounds[1],
                        "A box plot falls outside the drawn scale")
            return

        check_summary(parameters["summary"])
        require(parameters["reading"] in READINGS, "Unknown reading")

        if level == 4:
            missing = parameters["missing"]
            require(missing in (0, 1, 3, 4), "Median cannot be recovered this way")
            reading = parameters["reading"]
            # The stated statistic must depend on the missing value.
            involved = {
                "range": (0, 4), "interquartile range": (1, 3),
            }
            require(reading in involved and missing in involved[reading],
                    "Stated statistic does not involve the missing value")
            return

        bounds = parameters["bounds"]
        summary = parameters["summary"]
        require(bounds[0] <= summary[0] and summary[4] <= bounds[1],
                "Box plot falls outside the drawn scale")

    def validate_independently(self, question):
        """Recompute quartiles by counting positions, not by reusing the helper."""
        parameters = question.parameters
        form = parameters["form"]

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
            require(question.answer["values"] == expected,
                    "Independent five-number summary disagrees")
            return True

        if form == "compare":
            first, second = parameters["summaries"]
            reading = parameters["reading"]
            difference = abs(
                reading_value(first, reading) - reading_value(second, reading)
            )
            require(question.answer["value"] == difference,
                    "Independent comparison disagrees")
            return True

        summary = parameters["summary"]
        minimum, lower, median, upper, maximum = summary
        # Rebuild each statistic from its definition rather than the helper.
        statistics = {
            "median": median,
            "range": maximum - minimum,
            "interquartile range": upper - lower,
            "lower quartile": lower,
        }

        if form == "read":
            expected = statistics[parameters["reading"]]
            require(question.answer["value"] == expected,
                    "Independent reading disagrees")
            return True

        missing = parameters["missing"]
        require(question.answer["value"] == summary[missing],
                "Independent missing value disagrees")
        # The stated statistic must genuinely determine the missing value.
        stated = statistics[parameters["reading"]]
        if parameters["reading"] == "range":
            recovered = (maximum - stated if missing == 0 else minimum + stated)
        else:
            recovered = (upper - stated if missing == 1 else lower + stated)
        require(recovered == summary[missing],
                "Missing value is not recoverable from the stated statistic")
        return True