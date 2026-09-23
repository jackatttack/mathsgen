"""Estimate the mean from grouped frequency data.

Grouped data has lost the original values, so the mean can only be
estimated: each class is represented by its midpoint, and the estimate is
the total of midpoint times frequency divided by the total frequency.
Saying "estimate" is not a hedge, it is the mathematics, and every prompt
here says so.

The table asset is the same {"kind": "table"} specification the discrete
frequency-mean family uses, so both render identically.

Difficulty follows the task: estimate the mean, then estimate it with
unequal class widths, then identify the modal class and the class holding
the median as well, then recover a missing frequency from a stated
estimate.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .rounding import decimal_text, terminates


INFO = GeneratorInfo(
    id="data.mean.grouped_estimate", version=1,
    topic="data", subtopic="mean",
    title="Estimate the mean from grouped data",
    difficulty_descriptions={
        1: "Estimate the mean from equal class widths.",
        2: "Estimate the mean when the class widths differ.",
        3: "Identify the modal class and the class containing the median.",
        4: "Find a missing frequency from a stated estimated mean.",
    },
    tags=("mean", "grouped data", "midpoints", "estimate", "modal class"),
)

CONTEXTS = (
    ("the masses of some parcels", "Mass (kg)"),
    ("the times taken to finish a task", "Time (minutes)"),
    ("the heights of some plants", "Height (cm)"),
    ("the marks scored in a test", "Mark"),
)


def midpoint(low, high):
    """The value that represents a class, halfway across it."""
    return Fraction(low + high, 2)


def classes_of(p):
    """Pair consecutive boundaries into classes with their frequencies."""
    boundaries = p["boundaries"]
    frequencies = p["frequencies"]
    require(len(boundaries) == len(frequencies) + 1,
            "Each class needs a lower and an upper boundary")
    return [
        (boundaries[index], boundaries[index + 1], frequencies[index])
        for index in range(len(frequencies))
    ]


def estimated_mean(p, frequencies=None):
    """Total of midpoint times frequency, over the total frequency."""
    groups = classes_of(p)
    if frequencies is not None:
        groups = [
            (low, high, frequencies[index])
            for index, (low, high, _) in enumerate(groups)
        ]
    total = sum(frequency for _, _, frequency in groups)
    require(total > 0, "There must be some data")
    weighted = sum(
        midpoint(low, high) * frequency for low, high, frequency in groups
    )
    return Fraction(weighted, total)


def modal_class(p):
    """The class with the highest frequency."""
    groups = classes_of(p)
    highest = max(frequency for _, _, frequency in groups)
    matching = [index for index, (_, _, f) in enumerate(groups) if f == highest]
    require(len(matching) == 1, "The modal class must be unique")
    return matching[0]


def median_class(p):
    """The class containing the middle value of the data."""
    groups = classes_of(p)
    total = sum(frequency for _, _, frequency in groups)
    # The median is the value at position (total + 1) / 2 when ordered.
    position = Fraction(total + 1, 2)
    running = 0
    for index, (_, _, frequency) in enumerate(groups):
        running += frequency
        if running >= position:
            return index
    raise ValueError("The median position falls outside the data")


def class_text(low, high):
    """Write a class in inequality notation.

    "20 to 30" does not say which class a value of exactly 30 belongs to.
    The convention used here puts the boundary in the upper class, so the
    classes partition the data without overlapping.
    """
    return "{} < x <= {}".format(low, high)


def table_for(p, hide=None):
    """The frequency table, optionally with one frequency left blank."""
    _, label = CONTEXTS[p["context"]]
    rows = []
    for index, (low, high, frequency) in enumerate(classes_of(p)):
        shown = "?" if index == hide else str(frequency)
        rows.append([class_text(low, high), shown])
    return {
        "kind": "table", "version": 1,
        "headers": [label, "Frequency"],
        "rows": rows,
    }


def table_text(p, hide=None):
    """The same table in prose, since the CLI cannot show the drawing."""
    pieces = []
    for index, (low, high, frequency) in enumerate(classes_of(p)):
        shown = "?" if index == hide else str(frequency)
        pieces.append("{}: {}".format(class_text(low, high), shown))
    return "; ".join(pieces)


def presentation(p):
    context_text, _ = CONTEXTS[p["context"]]
    form = p["form"]

    if form == "missing":
        hidden = p["hidden"]
        instruction = (
            "The grouped frequency table shows {}. The estimated mean is {}. "
            "Find the missing frequency."
        ).format(context_text, decimal_text(Fraction(p["stated_mean"])))
        fallback = "{} Class: frequency — {}.".format(
            instruction, table_text(p, hide=hidden)
        )
        return (
            Content(fallback, display_text=instruction),
            (table_for(p, hide=hidden),),
        )

    if form == "classes":
        instruction = (
            "The grouped frequency table shows {}. Write down the modal "
            "class, and the class containing the median."
        ).format(context_text)
    else:
        instruction = (
            "The grouped frequency table shows {}. Estimate the mean."
        ).format(context_text)

    fallback = "{} Class: frequency — {}.".format(instruction, table_text(p))
    return Content(fallback, display_text=instruction), (table_for(p),)


def answer_for(p):
    form = p["form"]

    if form == "classes":
        groups = classes_of(p)
        modal = modal_class(p)
        median = median_class(p)
        answer = {
            "kind": "grouped_classes",
            "modal": class_text(groups[modal][0], groups[modal][1]),
            "median": class_text(groups[median][0], groups[median][1]),
        }
        display = Content(
            "Modal class {}; median class {}".format(
                answer["modal"], answer["median"]
            )
        )
        return answer, display

    if form == "missing":
        value = p["frequencies"][p["hidden"]]
        answer = {"kind": "integer", "value": value}
        return answer, Content(str(value))

    mean = estimated_mean(p)
    answer = {"kind": "estimated_mean", "value": rational_text(mean)}
    return answer, Content(decimal_text(mean))


class GroupedMean:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng

        for attempt in range(400):
            p = self.make_table(rng, difficulty)
            if self.acceptable(p, difficulty):
                break
        else:
            raise ValueError("Could not construct a suitable table")

        prompt, visuals = presentation(p)
        answer, display = answer_for(p)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=3 if difficulty <= 2 else 4, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=5),
            parameters=p, question_visuals=visuals,
        )
        self.validate(question)
        return question

    def make_table(self, rng, difficulty):
        context_index = rng.randrange(len(CONTEXTS))
        count = rng.choice((4, 5))

        if difficulty == 2:
            # Unequal widths, so midpoints are not evenly spaced.
            boundaries = [rng.choice((0, 10, 20))]
            for _ in range(count):
                boundaries.append(boundaries[-1] + rng.choice((5, 10, 20)))
        else:
            width = rng.choice((5, 10, 20))
            start = rng.choice((0, 10, 20))
            boundaries = [start + width * index for index in range(count + 1)]

        frequencies = [rng.randint(1, 12) for _ in range(count)]

        form = {
            1: "estimate", 2: "estimate", 3: "classes", 4: "missing",
        }[difficulty]
        p = {
            "form": form, "context": context_index,
            "boundaries": boundaries, "frequencies": frequencies,
        }
        if form == "missing":
            p["hidden"] = rng.randrange(count)
            p["stated_mean"] = rational_text(estimated_mean(p))
        return p

    def acceptable(self, p, difficulty):
        """Whether the table gives a clean question at this level."""
        groups = classes_of(p)
        if any(low >= high for low, high, _ in groups):
            return False
        if sum(frequency for _, _, frequency in groups) < 10:
            return False

        # Class widths decide the level, so they are tested here rather
        # than only in validation: level 2 can otherwise draw the same
        # width for every class by chance.
        widths = [high - low for low, high, _ in groups]
        if difficulty == 2 and len(set(widths)) == 1:
            return False
        if difficulty != 2 and len(set(widths)) != 1:
            return False

        if p["form"] == "classes":
            # Both the modal and the median class must be unique and, to be
            # worth asking, they should not be the same class.
            frequencies = [f for _, _, f in groups]
            highest = max(frequencies)
            if frequencies.count(highest) != 1:
                return False
            if modal_class(p) == median_class(p):
                return False
            return True

        mean = estimated_mean(p)
        if not terminates(mean):
            return False

        if p["form"] == "missing":
            # The missing frequency must be recoverable, which needs the
            # hidden class's midpoint to differ from the mean: otherwise
            # any frequency there gives the same estimate.
            low, high, _ = groups[p["hidden"]]
            if midpoint(low, high) == mean:
                return False
            if p["frequencies"][p["hidden"]] < 1:
                return False
        return True

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid level")
        require(q.settings == {}, "Unsupported settings")

        p = q.parameters
        expected = {
            1: "estimate", 2: "estimate", 3: "classes", 4: "missing",
        }[level]
        require(p["form"] == expected, "Form does not match difficulty")
        require(p["context"] in range(len(CONTEXTS)), "Unknown context")

        boundaries = p["boundaries"]
        frequencies = p["frequencies"]
        require(isinstance(boundaries, list) and 5 <= len(boundaries) <= 6,
                "Expected four or five classes")
        require(all(type(value) is int for value in boundaries),
                "Boundaries must be integers")
        require(all(a < b for a, b in zip(boundaries, boundaries[1:])),
                "Boundaries must increase")
        require(len(frequencies) == len(boundaries) - 1,
                "Each class needs a frequency")
        require(all(type(value) is int and value >= 1 for value in frequencies),
                "Frequencies must be positive integers")

        widths = [b - a for a, b in zip(boundaries, boundaries[1:])]
        if level == 2:
            require(len(set(widths)) > 1, "Level 2 uses unequal class widths")
        elif level == 1:
            require(len(set(widths)) == 1, "Level 1 uses equal class widths")

        require(self.acceptable(p, level), "Table does not meet its own bounds")

        if level == 4:
            require(p["hidden"] in range(len(frequencies)),
                    "Invalid hidden class")
            stated = Fraction(p["stated_mean"])
            require(p["stated_mean"] == rational_text(stated),
                    "Non-canonical stated mean")
            require(stated == estimated_mean(p),
                    "The stated mean does not match the table")

        answer, display = answer_for(p)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Display mismatch")
        prompt, visuals = presentation(p)
        require(q.prompt == prompt, "Prompt mismatch")
        require(q.visual_assets("questions") == visuals, "Table mismatch")
        require(q.visual_assets("answers") == (), "Unexpected answer visuals")
        return True

    def validate_independently(self, q):
        """Rebuild the estimate by expanding the table into a list.

        Writing out each midpoint as many times as its frequency and taking
        an ordinary mean is what the grouped calculation stands in for, so
        it checks the weighted sum without repeating it. The median class
        is confirmed from the same expanded list.
        """
        p = q.parameters
        groups = classes_of(p)

        expanded = []
        for low, high, frequency in groups:
            expanded.extend([midpoint(low, high)] * frequency)
        require(expanded, "There must be some data")

        if p["form"] == "classes":
            # Count how many values fall in each class by position in the
            # ordered list, rather than matching the median's value to a
            # midpoint: two classes can produce the same midpoint, and a
            # median falling between two values has no midpoint of its own.
            ordered = sorted(expanded)
            total = len(ordered)
            position = Fraction(total + 1, 2)

            running = 0
            median_index = None
            for index, (_, _, frequency) in enumerate(groups):
                running += frequency
                if median_index is None and running >= position:
                    median_index = index
            require(median_index is not None,
                    "The median position falls outside the data")
            low, high, _ = groups[median_index]
            require(q.answer["median"] == class_text(low, high),
                    "Independent median class disagrees")

            highest = max(frequency for _, _, frequency in groups)
            modal_indices = [
                index for index, (_, _, f) in enumerate(groups) if f == highest
            ]
            require(len(modal_indices) == 1, "The modal class is not unique")
            low, high, _ = groups[modal_indices[0]]
            require(q.answer["modal"] == class_text(low, high),
                    "Independent modal class disagrees")
            return True

        mean = Fraction(sum(expanded), len(expanded))

        if p["form"] == "missing":
            # Rebuild with the stated frequency and confirm the estimate
            # returns to the value the question gave.
            stated = Fraction(p["stated_mean"])
            require(mean == stated,
                    "Independent expansion disagrees with the stated mean")
            require(q.answer["value"] == p["frequencies"][p["hidden"]],
                    "The stated missing frequency is not the one removed")
            return True

        require(Fraction(q.answer["value"]) == mean,
                "Independent expanded mean disagrees")
        return True