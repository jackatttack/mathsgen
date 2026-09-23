"""Construct cumulative frequency tables and graphs from grouped data.

Students complete a running-total column before plotting at upper class
boundaries. Graph-based readings use straight-line interpolation between
the plotted points, so the model answers are reproducible estimates.

The original frequencies are the source of mathematical truth. Student
and teacher drawings are separate visual specifications.
"""
from fractions import Fraction
from itertools import product

from .core import (
    Content, GeneratorInfo, LayoutHint, Question,
    make_context, rational_text, require,
)


# --- Editable teaching choices ------------------------------------------

CONTEXTS = (
    ("the times taken to complete a race", "Time (minutes)", "minutes"),
    ("the heights of a group of plants", "Height (cm)", "cm"),
    ("the masses of some parcels", "Mass (kg)", "kg"),
    ("the lengths of some fish", "Length (cm)", "cm"),
)

CLASS_WIDTH = 10
CLASS_COUNT = 4
GRAPH_TOTAL = 80
GRAPH_FREQUENCIES = (10, 20, 30, 40)

INFO = GeneratorInfo(
    id="data.cumulative_frequency.construction",
    version=1,
    topic="data",
    subtopic="cumulative_frequency",
    title="Construct cumulative frequency graphs",
    difficulty_descriptions={
        1: "Complete a cumulative frequency table.",
        2: "Complete the table and draw a cumulative frequency graph.",
        3: "Construct the graph and estimate the quartiles and IQR.",
        4: "Construct the graph and answer a percentage or threshold question.",
    },
    tags=(
        "data", "cumulative frequency", "grouped data",
        "graphs", "quartiles", "interquartile range",
    ),
)

FORMS = {
    1: "table",
    2: "graph",
    3: "iqr",
    4: "interpret",
}


# --- Mathematical model --------------------------------------------------

def cumulative_totals(frequencies):
    """Return the running totals without altering the original frequencies."""
    total = 0
    results = []
    for frequency in frequencies:
        total += frequency
        results.append(total)
    return results


def graph_points(boundaries, frequencies):
    """Include the zero-frequency point at the first lower boundary."""
    return [[boundaries[0], 0]] + [
        [boundaries[index + 1], total]
        for index, total in enumerate(cumulative_totals(frequencies))
    ]


def value_at_frequency(boundaries, frequencies, target):
    """Interpolate within the class containing a cumulative target.

    This is an estimate for grouped observations, not an exact individual
    data value. Fraction arithmetic avoids rounding during generation.
    """
    previous = 0
    for index, frequency in enumerate(frequencies):
        current = previous + frequency
        if previous <= target <= current:
            return (
                Fraction(boundaries[index])
                + Fraction(
                    (target - previous)
                    * (boundaries[index + 1] - boundaries[index]),
                    frequency,
                )
            )
        previous = current
    raise ValueError("Cumulative target is outside the distribution")


def quartile_values(boundaries, frequencies):
    total = sum(frequencies)
    return [
        value_at_frequency(boundaries, frequencies, Fraction(total * part, 4))
        for part in (1, 2, 3)
    ]


def usable_graph_frequencies():
    """Find varied distributions with readable, integral quartile estimates."""
    boundaries = [CLASS_WIDTH * index for index in range(CLASS_COUNT + 1)]
    candidates = []
    for frequencies in product(GRAPH_FREQUENCIES, repeat=CLASS_COUNT):
        if sum(frequencies) != GRAPH_TOTAL:
            continue
        if len(set(frequencies)) == 1:
            continue
        quartiles = quartile_values(boundaries, frequencies)
        if all(value.denominator == 1 for value in quartiles):
            candidates.append(frequencies)
    return tuple(candidates)


GRAPH_DATASETS = usable_graph_frequencies()


# --- Student and teacher presentation -----------------------------------

def class_rows(parameters, completed):
    boundaries = parameters["boundaries"]
    frequencies = parameters["frequencies"]
    totals = cumulative_totals(frequencies)
    return [
        [
            "{} to {}".format(boundaries[index], boundaries[index + 1]),
            str(frequency),
            str(totals[index]) if completed else "",
        ]
        for index, frequency in enumerate(frequencies)
    ]


def frequency_table(parameters, completed):
    """A blank student column or the fully completed teacher table."""
    axis = CONTEXTS[parameters["context"]][1]
    short_axis = axis.replace("minutes", "min")
    return {
        "kind": "table",
        "version": 1,
        "headers": [short_axis, "Freq.", "Cum. freq."],
        "weights": [1.3, 1.1, 1.4],
        "rows": class_rows(parameters, completed),
    }


def frequency_graph(parameters, completed):
    """Reuse the existing coordinate-plot renderer without new plot code."""
    boundaries = parameters["boundaries"]
    frequencies = parameters["frequencies"]
    total = sum(frequencies)

    asset = {
        "kind": "plot",
        "version": 1,
        "x_range": [boundaries[0], boundaries[-1]],
        "y_range": [0, total],
        "x_step": CLASS_WIDTH,
        "y_step": 10,
        "minor_divisions": 2,
        "x_label": CONTEXTS[parameters["context"]][1],
        "y_label": "Cumulative frequency",
    }

    if completed:
        points = graph_points(boundaries, frequencies)
        asset["points"] = points
        asset["curves"] = [{"segments": [points]}]

    return asset


def reading_instruction(parameters):
    unit = CONTEXTS[parameters["context"]][2]

    if parameters["form"] == "iqr":
        return (
            "Use your graph to estimate the lower quartile, median "
            "and upper quartile. Calculate the interquartile range."
        )

    if parameters["form"] == "interpret":
        if parameters["reading"] == "above":
            return (
                "Using your graph, estimate how many observations "
                "exceed {} {}."
            ).format(parameters["cut"], unit)

        measurement = CONTEXTS[parameters["context"]][1].split(" (")[0].lower()
        return (
            "Using your graph, estimate the {} exceeded by "
            "{}% of the observations."
        ).format(measurement, parameters["percent"])

    return ""


def presentation(parameters):
    """Return the prompt, student assets and complete teacher assets."""
    context_text = CONTEXTS[parameters["context"]][0]
    instruction = (
        "The table shows {}. Complete the cumulative frequency column."
    ).format(context_text)

    if parameters["form"] != "table":
        instruction += " Plot this cumulative frequency graph."
        extra = reading_instruction(parameters)
        if extra:
            instruction += " " + extra

    # A plain-text CLI fallback includes the data in the visual table.
    rows = class_rows(parameters, completed=False)
    fallback = instruction + " " + "; ".join(
        "{}: frequency {}".format(row[0], row[1])
        for row in rows
    )

    student = [frequency_table(parameters, completed=False)]
    teacher = [frequency_table(parameters, completed=True)]

    if parameters["form"] != "table":
        student.append(frequency_graph(parameters, completed=False))
        teacher.append(frequency_graph(parameters, completed=True))

    return (
        Content(fallback, display_text=instruction),
        tuple(student),
        tuple(teacher),
    )


# --- Structured answers --------------------------------------------------

def answer_for(parameters):
    totals = cumulative_totals(parameters["frequencies"])
    answer = {
        "kind": "cumulative_frequency",
        "totals": totals,
    }

    display = "Cumulative frequencies: " + ", ".join(
        str(value) for value in totals
    )

    if parameters["form"] != "table":
        answer["points"] = graph_points(
            parameters["boundaries"], parameters["frequencies"]
        )
        display += ". Plot the points shown in the completed graph."

    if parameters["form"] == "iqr":
        lower, median, upper = quartile_values(
            parameters["boundaries"], parameters["frequencies"]
        )
        spread = upper - lower
        answer["quartiles"] = [
            rational_text(value) for value in (lower, median, upper)
        ]
        answer["iqr"] = rational_text(spread)
        display += (
            " Estimated lower quartile: {}; median: {}; "
            "upper quartile: {}; IQR: {}."
        ).format(
            rational_text(lower), rational_text(median),
            rational_text(upper), rational_text(spread),
        )

    if parameters["form"] == "interpret":
        reading = parameters["reading"]
        answer["reading"] = reading

        if reading == "above":
            boundaries = parameters["boundaries"]
            cut = parameters["cut"]
            index = next(
                index for index in range(len(boundaries) - 1)
                if boundaries[index] < cut < boundaries[index + 1]
            )
            before = sum(parameters["frequencies"][:index])
            within = Fraction(
                parameters["frequencies"][index]
                * (cut - boundaries[index]),
                boundaries[index + 1] - boundaries[index],
            )
            estimate = Fraction(sum(parameters["frequencies"])) - before - within
            answer["value"] = rational_text(estimate)
            display += " Estimated number above {}: {}.".format(
                cut, rational_text(estimate)
            )
        else:
            total = sum(parameters["frequencies"])
            target = Fraction(total * (100 - parameters["percent"]), 100)
            estimate = value_at_frequency(
                parameters["boundaries"], parameters["frequencies"], target
            )
            answer["value"] = rational_text(estimate)
            display += " Estimated value exceeded by {}%: {} {}.".format(
                parameters["percent"], rational_text(estimate),
                CONTEXTS[parameters["context"]][2],
            )

    return answer, Content(display)


# --- Generator -----------------------------------------------------------

class CumulativeFrequencyConstruction:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        require(GRAPH_DATASETS, "No suitable graph distributions available")

        rng = context.rng
        start = rng.choice((0, 10, 20))
        boundaries = [
            start + CLASS_WIDTH * index
            for index in range(CLASS_COUNT + 1)
        ]

        if difficulty == 1:
            frequencies = [
                5 * rng.randint(2, 8) for _ in range(CLASS_COUNT)
            ]
        else:
            frequencies = list(rng.choice(GRAPH_DATASETS))

        parameters = {
            "form": FORMS[difficulty],
            "context": rng.randrange(len(CONTEXTS)),
            "boundaries": boundaries,
            "frequencies": frequencies,
        }

        if difficulty == 4:
            parameters["reading"] = rng.choice(("above", "percentile"))
            if parameters["reading"] == "above":
                index = rng.randrange(CLASS_COUNT)
                parameters["cut"] = boundaries[index] + CLASS_WIDTH // 2
            else:
                parameters["percent"] = rng.choice((25, 75))

        prompt, student, teacher = presentation(parameters)
        answer, display = answer_for(parameters)

        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=prompt,
            answer=answer,
            answer_display=display,
            worked_solution=(),
            marks={1: 2, 2: 4, 3: 6, 4: 6}[difficulty],
            tags=self.info.tags,
            layout_hint=LayoutHint(
                working_lines=2 if difficulty == 1 else 1
            ),
            parameters=parameters,
            question_visuals=student,
            answer_visuals=teacher,
        )

        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in FORMS, "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")

        p = question.parameters
        expected_keys = {"form", "context", "boundaries", "frequencies"}
        if level == 4:
            expected_keys.add("reading")
            expected_keys.add(
                "cut" if p.get("reading") == "above" else "percent"
            )

        require(set(p) == expected_keys, "Unexpected parameters")
        require(p["form"] == FORMS[level], "Wrong form for difficulty")
        require(
            type(p["context"]) is int
            and 0 <= p["context"] < len(CONTEXTS),
            "Unknown data context",
        )

        boundaries = p["boundaries"]
        frequencies = p["frequencies"]

        require(
            isinstance(boundaries, list)
            and len(boundaries) == CLASS_COUNT + 1
            and all(type(value) is int for value in boundaries),
            "Invalid class boundaries",
        )
        require(boundaries[0] in (0, 10, 20), "Invalid class start")
        require(
            all(
                right - left == CLASS_WIDTH
                for left, right in zip(boundaries, boundaries[1:])
            ),
            "Invalid class widths",
        )
        require(
            isinstance(frequencies, list)
            and len(frequencies) == CLASS_COUNT
            and all(type(value) is int and value > 0 for value in frequencies),
            "Invalid class frequencies",
        )

        if level == 1:
            require(
                all(value % 5 == 0 and 10 <= value <= 40
                    for value in frequencies),
                "Invalid introductory frequencies",
            )
        else:
            require(
                tuple(frequencies) in GRAPH_DATASETS,
                "Graph distribution violates teaching bounds",
            )

        if level == 4:
            require(p["reading"] in ("above", "percentile"),
                    "Unknown graph reading")
            if p["reading"] == "above":
                require(
                    type(p["cut"]) is int
                    and p["cut"] in [
                        left + CLASS_WIDTH // 2
                        for left in boundaries[:-1]
                    ],
                    "Invalid threshold",
                )
            else:
                require(
                    type(p["percent"]) is int
                    and p["percent"] in (25, 75),
                    "Invalid percentage",
                )

        answer, display = answer_for(p)
        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Answer display mismatch")

        prompt, student, teacher = presentation(p)
        require(question.prompt == prompt, "Prompt mismatch")
        require(question.visual_assets("questions") == student,
                "Student drawing mismatch")
        require(question.visual_assets("answers") == teacher,
                "Teacher drawing mismatch")
        return True

    def validate_independently(self, question):
        """Recount original frequencies and check graphical answer data.

        Reconstruct each cumulative value from a separate prefix sum.
        Quartile readings are checked by scanning the graph's coordinates.
        """
        p = question.parameters
        boundaries = p["boundaries"]
        frequencies = p["frequencies"]
        answer = question.answer

        counted = [
            sum(frequencies[:index + 1])
            for index in range(len(frequencies))
        ]
        require(answer["totals"] == counted,
                "Independent cumulative totals disagree")

        table = question.answer_visuals[0]
        require(
            [row[2] for row in table["rows"]]
            == [str(value) for value in counted],
            "Completed table disagrees with independent totals",
        )

        if question.difficulty == 1:
            return True

        points = [[boundaries[0], 0]] + [
            [boundaries[index + 1], counted[index]]
            for index in range(len(frequencies))
        ]
        require(answer["points"] == points,
                "Independent graph coordinates disagree")

        graph = question.answer_visuals[1]
        require(graph["points"] == points,
                "Teacher graph plots incorrect cumulative values")
        require(graph["curves"][0]["segments"] == [points],
                "Teacher graph does not connect the correct points")

        if question.difficulty == 3:
            readings = []
            for fraction in (Fraction(1, 4), Fraction(1, 2),
                             Fraction(3, 4)):
                target = counted[-1] * fraction
                for first, second in zip(points, points[1:]):
                    if first[1] <= target <= second[1]:
                        reading = (
                            Fraction(first[0])
                            + Fraction(target - first[1], second[1] - first[1])
                            * (second[0] - first[0])
                        )
                        readings.append(reading)
                        break
                else:
                    raise ValueError("Quartile target missing from graph")

            require(
                answer["quartiles"] == [
                    rational_text(value) for value in readings
                ],
                "Independent quartile readings disagree",
            )
            require(
                Fraction(answer["iqr"]) == readings[2] - readings[0],
                "Independent IQR disagrees",
            )

        if question.difficulty == 4:
            if p["reading"] == "above":
                index = next(
                    index for index, left in enumerate(boundaries[:-1])
                    if left < p["cut"] < boundaries[index + 1]
                )
                estimate = (
                    sum(frequencies[index + 1:])
                    + Fraction(frequencies[index], 2)
                )
            else:
                target = Fraction(
                    counted[-1] * (100 - p["percent"]), 100
                )
                estimate = None
                for first, second in zip(points, points[1:]):
                    if first[1] <= target <= second[1]:
                        estimate = (
                            Fraction(first[0])
                            + Fraction(target - first[1], second[1] - first[1])
                            * (second[0] - first[0])
                        )
                        break
                require(estimate is not None,
                        "Percentage target missing from graph")

            require(
                Fraction(answer["value"]) == estimate,
                "Independent graph interpretation disagrees",
            )

        return True