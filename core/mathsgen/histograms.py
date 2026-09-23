"""Histograms with frequency density, where class widths are not all equal.

The area of a bar represents frequency, so the height is frequency divided
by class width. When every class has the same width the heights happen to be
proportional to the frequencies, which is why students who only meet equal
widths later read unequal-width bars as frequencies. Every level above the
first uses unequal widths deliberately.

Difficulty follows the task: level 1 reads a frequency off an equal-width
histogram, level 2 computes the densities and draws the bars, level 3 reads a
frequency back from an unequal-width histogram, and level 4 estimates the
frequency in part of a class or totals several classes.

Frequencies and boundaries are integers and every density is an exact
rational, so no question depends on a rounded height.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .rounding import decimal_text, terminates


# --- Editable difficulty bounds -------------------------------------------
CONTEXTS = (
    ("the masses of some parcels", "Mass (kg)", "Frequency density"),
    ("the times taken to finish a task", "Time (minutes)", "Frequency density"),
    ("the heights of some plants", "Height (cm)", "Frequency density"),
)

# Class boundaries are built from these widths, so every density terminates.
EQUAL_WIDTHS = (5, 10, 20)
UNEQUAL_WIDTHS = (5, 10, 20, 40)


INFO = GeneratorInfo(
    id="data.spread.histograms", version=1,
    topic="data", subtopic="histograms",
    title="Histograms and frequency density",
    difficulty_descriptions={
        1: "Read a frequency from a histogram with equal class widths.",
        2: "Calculate frequency densities and draw the histogram.",
        3: "Find a frequency from a histogram with unequal class widths.",
        4: "Estimate the frequency in part of a class, or across several classes.",
    },
    tags=("data", "histograms", "frequency density", "grouped data"),
)


def density(frequency, width):
    """Frequency density is frequency per unit of class width."""
    return Fraction(frequency, width)


def classes_from(boundaries, frequencies):
    """Pair consecutive boundaries with their frequencies."""
    require(len(boundaries) == len(frequencies) + 1,
            "Each class needs a lower and an upper boundary")
    return [
        (boundaries[index], boundaries[index + 1], frequencies[index])
        for index in range(len(frequencies))
    ]


def histogram_asset(parameters, drawn=True):
    """Build the plot specification, or a blank grid at the same scale."""
    boundaries = parameters["boundaries"]
    frequencies = parameters["frequencies"]
    _, x_label, y_label = context_for(parameters)

    bars = []
    highest = Fraction(0)
    for low, high, frequency in classes_from(boundaries, frequencies):
        value = density(frequency, high - low)
        highest = max(highest, value)
        bars.append({
            "left": low, "right": high, "height": float(value),
        })

    # Round the axis up to a whole step above the tallest bar.
    step = parameters["y_step"]
    top = float(-((-highest) // Fraction(str(step))) * Fraction(str(step)))
    asset = {
        "kind": "plot", "version": 1,
        "x_range": [boundaries[0], boundaries[-1]],
        "y_range": [0, top],
        "x_step": parameters["x_step"], "y_step": step,
        "x_label": x_label, "y_label": y_label,
        # Five minor divisions put a gridline every fifth of a major step, so
        # a density such as 2.2 sits on a line rather than between two.
        "minor_divisions": 5,
    }
    if drawn:
        asset["bars"] = bars
    return asset


def context_for(parameters):
    return CONTEXTS[parameters["context"]]


def class_text(low, high):
    return "{} to {}".format(low, high)


def table_text(parameters, omit=None):
    """State the classes in prose, since the CLI cannot show the drawing."""
    pieces = []
    for index, (low, high, frequency) in enumerate(
        classes_from(parameters["boundaries"], parameters["frequencies"])
    ):
        if index == omit:
            continue
        pieces.append("{}: frequency {}".format(class_text(low, high), frequency))
    return "; ".join(pieces)


def presentation(parameters):
    form = parameters["form"]
    context_text, _, _ = context_for(parameters)
    boundaries = parameters["boundaries"]
    frequencies = parameters["frequencies"]

    if form == "draw":
        instruction = (
            "The table shows {}. Calculate the frequency density for each "
            "class and draw the histogram."
        ).format(context_text)
        fallback = instruction + " " + table_text(parameters)
        blank = histogram_asset(parameters, drawn=False)
        drawn = histogram_asset(parameters)
        return Content(fallback, display_text=fallback), (blank,), (drawn,)

    if form in ("read_equal", "read_unequal", "part_class"):
        target = parameters["target"]
        low, high, _ = classes_from(boundaries, frequencies)[target]

    if form in ("read_equal", "read_unequal"):
        instruction = (
            "The histogram shows {}. Find the frequency for the class {}."
        ).format(context_text, class_text(low, high))
        # The fallback states the densities the student would read off.
        densities = "; ".join(
            "{}: frequency density {}".format(
                class_text(a, b), decimal_text(density(f, b - a))
            )
            for a, b, f in classes_from(boundaries, frequencies)
        )
        fallback = "{} The histogram shows {}.".format(instruction, densities)
        return (
            Content(fallback, display_text=instruction),
            (histogram_asset(parameters),), (),
        )

    if form == "part_class":
        cut = parameters["cut"]
        instruction = (
            "The histogram shows {}. Estimate how many values lie between "
            "{} and {}."
        ).format(context_text, low, cut)
    else:
        first, last = parameters["span"]
        low_edge = boundaries[first]
        high_edge = boundaries[last + 1]
        instruction = (
            "The histogram shows {}. Find the total frequency for values "
            "between {} and {}."
        ).format(context_text, low_edge, high_edge)

    densities = "; ".join(
        "{}: frequency density {}".format(
            class_text(a, b), decimal_text(density(f, b - a))
        )
        for a, b, f in classes_from(boundaries, frequencies)
    )
    fallback = "{} The histogram shows {}.".format(instruction, densities)
    return (
        Content(fallback, display_text=instruction),
        (histogram_asset(parameters),), (),
    )


def answer_for(parameters):
    form = parameters["form"]
    boundaries = parameters["boundaries"]
    frequencies = parameters["frequencies"]

    if form == "draw":
        densities = [
            rational_text(density(frequency, high - low))
            for low, high, frequency in classes_from(boundaries, frequencies)
        ]
        answer = {"kind": "frequency_densities", "values": densities}
        display = Content("; ".join(
            "{}: {}".format(class_text(low, high), decimal_text(Fraction(value)))
            for (low, high, _), value in zip(
                classes_from(boundaries, frequencies), densities
            )
        ))
        return answer, display

    if form == "part_class":
        target = parameters["target"]
        low, high, frequency = classes_from(boundaries, frequencies)[target]
        cut = parameters["cut"]
        # A part of a class is estimated by assuming an even spread within it.
        value = density(frequency, high - low) * (cut - low)
        answer = {"kind": "frequency", "value": rational_text(value)}
        return answer, Content(decimal_text(value))

    if form == "total":
        first, last = parameters["span"]
        value = Fraction(sum(frequencies[first:last + 1]))
        answer = {"kind": "frequency", "value": rational_text(value)}
        return answer, Content(decimal_text(value))

    target = parameters["target"]
    value = Fraction(frequencies[target])
    answer = {"kind": "frequency", "value": rational_text(value)}
    return answer, Content(decimal_text(value))


class Histograms:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        builders = {
            1: self.make_equal, 2: self.make_draw,
            3: self.make_unequal, 4: self.make_estimate,
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
            layout_hint=LayoutHint(working_lines=2 if difficulty == 1 else 3),
            parameters=parameters, question_visuals=student,
            answer_visuals=teacher,
        )
        self.validate(question)
        return question

    def make_boundaries(self, rng, widths):
        """Build class boundaries from a starting value and chosen widths."""
        start = rng.choice((0, 10, 20))
        boundaries = [start]
        for width in widths:
            boundaries.append(boundaries[-1] + width)
        return boundaries

    def make_frequencies(self, rng, boundaries):
        """Frequencies whose densities are exact and not all identical."""
        for attempt in range(200):
            frequencies = []
            for index in range(len(boundaries) - 1):
                width = boundaries[index + 1] - boundaries[index]
                # A multiple of a fifth of the width keeps the density tidy.
                step = max(1, width // 5)
                frequencies.append(step * rng.randint(2, 12))
            densities = [
                density(frequency, boundaries[index + 1] - boundaries[index])
                for index, frequency in enumerate(frequencies)
            ]
            if len(set(densities)) == 1:
                continue
            if not all(terminates(value) for value in densities):
                continue
            return frequencies
        raise ValueError("Could not construct suitable frequencies")

    def scale_for(self, boundaries, frequencies):
        """Choose axis steps that suit the boundaries and the tallest bar."""
        widths = [
            boundaries[index + 1] - boundaries[index]
            for index in range(len(boundaries) - 1)
        ]
        x_step = min(widths)
        highest = max(
            density(frequency, boundaries[index + 1] - boundaries[index])
            for index, frequency in enumerate(frequencies)
        )
        for candidate in (Fraction(1, 2), Fraction(1), Fraction(2), Fraction(5)):
            if highest / candidate <= 8:
                return x_step, float(candidate)
        return x_step, 10.0

    def build(self, rng, widths, form, **extra):
        boundaries = self.make_boundaries(rng, widths)
        frequencies = self.make_frequencies(rng, boundaries)
        x_step, y_step = self.scale_for(boundaries, frequencies)
        parameters = {
            "form": form, "context": rng.randrange(len(CONTEXTS)),
            "boundaries": boundaries, "frequencies": frequencies,
            "x_step": x_step, "y_step": y_step,
        }
        parameters.update(extra)
        return parameters

    def make_equal(self, rng):
        width = rng.choice(EQUAL_WIDTHS)
        count = rng.randint(3, 4)
        parameters = self.build(rng, [width] * count, "read_equal")
        parameters["target"] = rng.randrange(count)
        return parameters

    def make_draw(self, rng):
        widths = self.uneven_widths(rng, rng.randint(3, 4))
        return self.build(rng, widths, "draw")

    def make_unequal(self, rng):
        count = rng.randint(3, 4)
        widths = self.uneven_widths(rng, count)
        parameters = self.build(rng, widths, "read_unequal")
        # Ask about a class whose width is not the smallest, so the answer
        # is not simply the bar height.
        wider = [index for index, width in enumerate(widths) if width != min(widths)]
        parameters["target"] = rng.choice(wider)
        return parameters

    def make_estimate(self, rng):
        count = rng.randint(3, 4)
        widths = self.uneven_widths(rng, count)
        if rng.choice((True, False)):
            parameters = self.build(rng, widths, "part_class")
            # Test candidate cuts rather than reasoning about which divide
            # exactly: the estimate is frequency times the fraction of the
            # class below the cut, and only some cuts leave that whole.
            candidates = []
            for target in range(count):
                low = parameters["boundaries"][target]
                high = parameters["boundaries"][target + 1]
                frequency = parameters["frequencies"][target]
                for cut in range(low + 1, high):
                    estimate = Fraction(frequency * (cut - low), high - low)
                    if estimate.denominator == 1:
                        candidates.append((target, cut))
            if not candidates:
                # No exact part-class question exists for this data; a total
                # across whole classes always works instead.
                first = rng.randrange(count - 1)
                parameters["form"] = "total"
                parameters["span"] = [first, rng.randint(first + 1, count - 1)]
                return parameters
            target, cut = rng.choice(candidates)
            parameters["target"] = target
            parameters["cut"] = cut
            return parameters
        parameters = self.build(rng, widths, "total")
        first = rng.randrange(count - 1)
        last = rng.randint(first + 1, count - 1)
        parameters["span"] = [first, last]
        return parameters

    @staticmethod
    def uneven_widths(rng, count):
        """Widths that are not all the same, so density genuinely matters."""
        for attempt in range(200):
            widths = [rng.choice(UNEQUAL_WIDTHS) for _ in range(count)]
            if len(set(widths)) > 1:
                return widths
        raise ValueError("Could not construct unequal class widths")

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")

        parameters = question.parameters
        expected = {
            1: ("read_equal",), 2: ("draw",), 3: ("read_unequal",),
            4: ("part_class", "total"),
        }[level]
        require(parameters.get("form") in expected,
                "Form does not match difficulty")

        boundaries = parameters["boundaries"]
        frequencies = parameters["frequencies"]
        require(isinstance(boundaries, list) and 4 <= len(boundaries) <= 5,
                "Expected three or four classes")
        require(all(type(value) is int for value in boundaries),
                "Boundaries must be integers")
        require(all(a < b for a, b in zip(boundaries, boundaries[1:])),
                "Boundaries must increase")
        require(len(frequencies) == len(boundaries) - 1,
                "Each class needs a frequency")
        require(all(type(value) is int and value > 0 for value in frequencies),
                "Frequencies must be positive integers")
        require(parameters["context"] in range(len(CONTEXTS)), "Unknown context")

        widths = [b - a for a, b in zip(boundaries, boundaries[1:])]
        if parameters["form"] == "read_equal":
            require(len(set(widths)) == 1, "Level 1 uses equal class widths")
        else:
            require(len(set(widths)) > 1, "This level needs unequal class widths")

        densities = [
            density(frequency, width)
            for frequency, width in zip(frequencies, widths)
        ]
        require(all(terminates(value) for value in densities),
                "Frequency density is not an exact decimal")
        require(len(set(densities)) > 1, "Every bar has the same height")

        self.check_form(parameters, widths)

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

    def check_form(self, parameters, widths):
        form = parameters["form"]
        count = len(widths)

        if form == "draw":
            require(set(parameters) == {
                "form", "context", "boundaries", "frequencies", "x_step", "y_step",
            }, "Unexpected parameters")
            return

        if form == "total":
            first, last = parameters["span"]
            require(0 <= first < last < count, "Invalid class span")
            return

        target = parameters["target"]
        require(type(target) is int and 0 <= target < count, "Invalid target class")

        if form == "read_unequal":
            require(widths[target] != min(widths),
                    "Target class should not be the narrowest")

        if form == "part_class":
            boundaries = parameters["boundaries"]
            cut = parameters["cut"]
            require(boundaries[target] < cut < boundaries[target + 1],
                    "Cut must fall inside the target class")
            estimate = (density(parameters["frequencies"][target], widths[target])
                        * (cut - boundaries[target]))
            require(estimate == int(estimate), "Part-class estimate is not whole")

    def validate_independently(self, question):
        """Rebuild frequencies as bar areas, which is what the histogram means."""
        parameters = question.parameters
        boundaries = parameters["boundaries"]
        frequencies = parameters["frequencies"]
        widths = [b - a for a, b in zip(boundaries, boundaries[1:])]

        # Recover each frequency from the drawn bar: area equals height times
        # width, which must return the frequency the question was built from.
        asset = histogram_asset(parameters)
        if "bars" in asset:
            for index, bar in enumerate(asset["bars"]):
                area = Fraction(str(bar["height"])) * (bar["right"] - bar["left"])
                require(area == frequencies[index],
                        "Drawn bar area does not match its frequency")

        form = parameters["form"]
        submitted = question.answer

        if form == "draw":
            expected = [
                rational_text(Fraction(frequency, width))
                for frequency, width in zip(frequencies, widths)
            ]
            require(submitted["values"] == expected,
                    "Independent frequency densities disagree")
            return True

        value = Fraction(submitted["value"])

        if form == "total":
            first, last = parameters["span"]
            total = Fraction(0)
            for index in range(first, last + 1):
                total += Fraction(frequencies[index])
            require(value == total, "Independent total disagrees")
            return True

        target = parameters["target"]
        if form == "part_class":
            cut = parameters["cut"]
            proportion = Fraction(cut - boundaries[target], widths[target])
            require(value == proportion * frequencies[target],
                    "Independent part-class estimate disagrees")
            return True

        require(value == frequencies[target], "Independent frequency disagrees")
        return True