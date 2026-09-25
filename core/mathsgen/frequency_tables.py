"""Frequency tables: averages, grouped estimates and reverse problems.

Version 3 of data.mean.frequency_table. It replaces frequency_mean.py and
frequency_mean_forms.py, and absorbs data.mean.grouped_estimate,
data.mean.frequency_missing_value and data.mean.missing_frequency
(docs/CONSOLIDATION_PLAN.txt, 2026-09-25).

Levels
    1  Discrete table: find two or three of the mean, median, mode and range.
    2  Grouped table: estimate the mean, and find the modal class and/or the
       class containing the median.
    3  Discrete reverse: find a missing frequency or a missing end value from
       the stated mean, then an average or the range of the completed table.
    4  One of: a missing frequency in a grouped table from its estimated mean
       (then a class); the mean of one group and of two groups combined; or
       the table mean, then one extra value that moves it.

Stored parameters always hold the complete table; the prompt hides one cell
for reverse forms and states the mean computed from the full data, so every
stated fact comes from the same exact source.
"""
from fractions import Fraction

from .core import Content, GeneratorInfo, rational_text, require
from .family import GeneratorFamily
from .median_range import decimal_text, independent_measure, parse_values


INFO = GeneratorInfo(
    id="data.mean.frequency_table",
    version=3,
    topic="data",
    subtopic="mean",
    title="Frequency tables: averages, grouped data and reverse problems",
    difficulty_descriptions={
        1: "Find two or three of the mean, median, mode and range from a frequency table.",
        2: "Estimate the mean of grouped data and find the modal or median class.",
        3: "Find a missing frequency or value from the mean, then another measure.",
        4: "Grouped missing frequency, combined groups, or an extra value that moves the mean.",
    },
    tags=("mean", "median", "mode", "range", "frequency_table", "grouped data", "reverse"),
)


# ---------------------------------------------------------------------------
# Editable settings
# ---------------------------------------------------------------------------

# Discrete contexts: (what the table shows, value heading, lowest value,
# highest value, one item, several items).
DISCRETE_CONTEXTS = (
    ("the numbers of goals scored in some football matches", "Goals", 0, 6,
     "match", "matches"),
    ("the numbers of pets owned by some students", "Pets", 0, 5,
     "student", "students"),
    ("the numbers of people in some cars", "People", 1, 5, "car", "cars"),
    ("the numbers of books some students read last month", "Books", 0, 8,
     "student", "students"),
    ("the numbers of siblings some students have", "Siblings", 0, 5,
     "student", "students"),
)
DISCRETE_ROWS = (4, 5, 6)
DISCRETE_FREQUENCY = (1, 12)

# Grouped contexts: (what the table shows, class heading).
GROUPED_CONTEXTS = (
    ("the masses of some parcels", "Mass (kg)"),
    ("the times taken to finish a task", "Time (minutes)"),
    ("the heights of some plants", "Height (cm)"),
    ("the marks scored in a test", "Mark"),
)
GROUPED_CLASSES = (4, 5)
GROUPED_WIDTHS = (5, 10, 20)
GROUPED_STARTS = (0, 10, 20)
GROUPED_FREQUENCY = (1, 12)
UNEQUAL_WIDTH_SHARE = 0.4

# Every table has at least this many observations.
MINIMUM_TOTAL = 10

# Which forms each level may use; one is chosen per question.
LEVEL_FORMS = {
    1: ("discrete",),
    2: ("grouped",),
    3: ("missing_frequency", "missing_value"),
    4: ("grouped_missing", "combined", "new_observation"),
}


# ---------------------------------------------------------------------------
# Fixed wording and structure
# ---------------------------------------------------------------------------

MEASURES = ("mean", "median", "mode", "range")
MEASURE_TASKS = {
    "mean": "Work out the mean.",
    "median": "Find the median.",
    "mode": "Write down the mode.",
    "range": "Work out the range.",
}
CLASS_TASKS = {
    "mean": "Work out an estimate for the mean.",
    "modal": "Write down the modal class.",
    "median": "Find the class that contains the median.",
}
CLASS_LABELS = {"modal": "Modal class", "median": "Median class"}
LETTERS = "abcd"
ATTEMPTS = 2000

FORM_KEYS = {
    "discrete": {"form", "context", "values", "frequencies", "asked"},
    "grouped": {"form", "context", "boundaries", "frequencies", "asked"},
    "missing_frequency": {"form", "context", "values", "frequencies", "missing", "follow_up"},
    "missing_value": {"form", "context", "values", "frequencies", "missing", "follow_up"},
    "grouped_missing": {"form", "context", "boundaries", "frequencies", "missing", "follow_up"},
    "combined": {"form", "context", "values", "first", "second"},
    "new_observation": {"form", "context", "values", "frequencies", "new_value"},
}


# ---------------------------------------------------------------------------
# Measures from a discrete table (values ascending, exact Fractions)
# ---------------------------------------------------------------------------

def two_places(value):
    return (Fraction(value) * 100).denominator == 1


def table_mean(values, frequencies):
    total = sum(frequencies)
    return sum((value * frequency for value, frequency in zip(values, frequencies)),
               Fraction(0)) / total


def value_at(values, frequencies, position):
    """The value in 1-based position of the ordered data."""
    running = 0
    for value, frequency in zip(values, frequencies):
        running += frequency
        if running >= position:
            return value
    raise ValueError("Position beyond the data")


def table_median(values, frequencies):
    total = sum(frequencies)
    if total % 2:
        return value_at(values, frequencies, (total + 1) // 2)
    return (value_at(values, frequencies, total // 2)
            + value_at(values, frequencies, total // 2 + 1)) / 2


def table_mode(values, frequencies):
    """The value with the single highest frequency, or None when tied."""
    highest = max(frequencies)
    modal = [value for value, frequency in zip(values, frequencies) if frequency == highest]
    return modal[0] if len(modal) == 1 else None


def table_range(values, frequencies):
    present = [value for value, frequency in zip(values, frequencies) if frequency > 0]
    return max(present) - min(present)


TABLE_MEASURES = {
    "mean": table_mean,
    "median": table_median,
    "mode": table_mode,
    "range": table_range,
}


# ---------------------------------------------------------------------------
# Grouped data
# ---------------------------------------------------------------------------

def midpoint(low, high):
    """The value that represents a class, halfway across it."""
    return Fraction(low + high, 2)


def grouped_estimate(boundaries, frequencies):
    """Total of midpoint times frequency, over the total frequency."""
    weighted = sum(
        (midpoint(boundaries[index], boundaries[index + 1]) * frequency
         for index, frequency in enumerate(frequencies)),
        Fraction(0),
    )
    return weighted / sum(frequencies)


def modal_class(frequencies):
    highest = max(frequencies)
    matching = [index for index, frequency in enumerate(frequencies) if frequency == highest]
    return matching[0] if len(matching) == 1 else None


def class_at(frequencies, position):
    running = 0
    for index, frequency in enumerate(frequencies):
        running += frequency
        if running >= position:
            return index
    raise ValueError("Position beyond the data")


def median_class(frequencies):
    """The class holding the median, or None when the two middle values
    fall in different classes (the question would then be ambiguous)."""
    total = sum(frequencies)
    lower = class_at(frequencies, (total + 1) // 2)
    upper = class_at(frequencies, total // 2 + 1)
    return lower if lower == upper else None


def class_text(boundaries, index):
    """Inequality notation; a boundary value belongs to the lower class."""
    return "{} < x <= {}".format(boundaries[index], boundaries[index + 1])


GROUPED_FINDERS = {"modal": modal_class, "median": median_class}


# ---------------------------------------------------------------------------
# Tables and prompts
# ---------------------------------------------------------------------------

def discrete_table(context, values, frequencies, hide_value=None, hide_frequency=None):
    heading = DISCRETE_CONTEXTS[context][1]
    rows = []
    for index, (value, frequency) in enumerate(zip(values, frequencies)):
        rows.append([
            "x" if index == hide_value else decimal_text(value),
            "f" if index == hide_frequency else str(frequency),
        ])
    return {"kind": "table", "version": 1, "headers": [heading, "Frequency"], "rows": rows}


def grouped_table(context, boundaries, frequencies, hide_frequency=None):
    heading = GROUPED_CONTEXTS[context][1]
    rows = [
        [class_text(boundaries, index), "f" if index == hide_frequency else str(frequency)]
        for index, frequency in enumerate(frequencies)
    ]
    return {"kind": "table", "version": 1, "headers": [heading, "Frequency"], "rows": rows}


def table_prompt(instruction, table):
    """A complete CLI fallback; the PDF shows the instruction beside the drawn table."""
    rows_text = "; ".join(", ".join(row) for row in table["rows"])
    fallback = "{} Table ({}): {}.".format(instruction, ", ".join(table["headers"]), rows_text)
    return Content(fallback, display_text=instruction)


def lettered(tasks):
    return " ".join("({}) {}".format(letter, task) for letter, task in zip(LETTERS, tasks))


def assemble(instruction, table, answer, display, marks, working_lines):
    return {
        "prompt": table_prompt(instruction, table),
        "answer": answer,
        "answer_display": Content(display),
        "marks": marks,
        "working_lines": working_lines,
        "question_visuals": [table],
    }


# ---------------------------------------------------------------------------
# Structural checks shared by several forms
# ---------------------------------------------------------------------------

def checked_context(index, contexts):
    require(type(index) is int and 0 <= index < len(contexts), "Unknown context")
    return contexts[index]


def checked_counts(raw, bounds, name):
    lowest, highest = bounds
    require(isinstance(raw, list) and raw, "Expected a list of " + name)
    require(all(type(item) is int and lowest <= item <= highest for item in raw),
            name.capitalize() + " outside bounds")
    return raw


def checked_discrete(p, key="frequencies"):
    """Sorted whole-number values within the context's range, with frequencies."""
    context = checked_context(p["context"], DISCRETE_CONTEXTS)
    low, high = context[2], context[3]
    values = parse_values(p["values"])
    frequencies = checked_counts(p[key], DISCRETE_FREQUENCY, "frequencies")
    require(len(values) == len(frequencies), "Each value needs a frequency")
    require(min(DISCRETE_ROWS) <= len(values) <= max(DISCRETE_ROWS), "Unexpected number of rows")
    require(all(value.denominator == 1 and low <= value <= high for value in values),
            "Value outside the context's range")
    require(all(a < b for a, b in zip(values, values[1:])), "Values must increase")
    require(sum(frequencies) >= MINIMUM_TOTAL, "Too little data")
    return values, frequencies


def checked_grouped(p):
    checked_context(p["context"], GROUPED_CONTEXTS)
    boundaries = p["boundaries"]
    require(isinstance(boundaries, list) and all(type(value) is int for value in boundaries),
            "Boundaries must be whole numbers")
    require(len(boundaries) - 1 in GROUPED_CLASSES, "Unexpected number of classes")
    require(boundaries[0] in GROUPED_STARTS, "Unexpected first boundary")
    widths = [b - a for a, b in zip(boundaries, boundaries[1:])]
    require(all(width in GROUPED_WIDTHS for width in widths), "Unexpected class width")
    frequencies = checked_counts(p["frequencies"], GROUPED_FREQUENCY, "frequencies")
    require(len(frequencies) == len(boundaries) - 1, "Each class needs a frequency")
    require(sum(frequencies) >= MINIMUM_TOTAL, "Too little data")
    return boundaries, frequencies


def checked_index(index, length):
    require(type(index) is int and 0 <= index < length, "Invalid missing row")
    return index


# ---------------------------------------------------------------------------
# Independent checking helpers (statistics module and SymPy)
# ---------------------------------------------------------------------------

def expand(values, frequencies):
    data = []
    for value, frequency in zip(values, frequencies):
        data.extend([value] * frequency)
    return data


def to_sympy(value):
    import sympy
    value = Fraction(value)
    return sympy.Rational(value.numerator, value.denominator)


def independent_mean(data):
    import statistics
    return Fraction(statistics.mean(data))


def independent_class(name, frequencies):
    """Modal or median class index from the expanded list of class labels."""
    import statistics
    labels = expand(list(range(len(frequencies))), frequencies)
    if name == "modal":
        modes = statistics.multimode(labels)
        require(len(modes) == 1, "Independent check found no single modal class")
        return modes[0]
    middle = len(labels) // 2
    if len(labels) % 2:
        return labels[middle]
    require(labels[middle - 1] == labels[middle],
            "Independent check found the median between two classes")
    return labels[middle]


def solve_single(equation, symbol):
    import sympy
    solutions = sympy.solve(equation, symbol)
    require(len(solutions) == 1, "Expected exactly one solution")
    return solutions[0]


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class FrequencyTables(GeneratorFamily):
    """Frequency tables from simple averages to reverse and combined problems."""
    info = INFO

    def expected_keys(self, parameters, level):
        return FORM_KEYS.get(parameters.get("form"), set())

    # -- build --------------------------------------------------------------

    def build(self, level, rng):
        form = rng.choice(LEVEL_FORMS[level])
        builder = self.builders()[form]
        checker = self.checkers()[form]
        for attempt in range(ATTEMPTS):
            parameters = builder(rng)
            try:
                checker(parameters)
            except ValueError:
                continue
            return parameters
        raise ValueError("Could not construct a suitable frequency table ({})".format(form))

    def builders(self):
        return {
            "discrete": self.build_discrete,
            "grouped": self.build_grouped,
            "missing_frequency": self.build_missing_frequency,
            "missing_value": self.build_missing_value,
            "grouped_missing": self.build_grouped_missing,
            "combined": self.build_combined,
            "new_observation": self.build_new_observation,
        }

    def random_discrete(self, rng):
        context = rng.randrange(len(DISCRETE_CONTEXTS))
        low, high = DISCRETE_CONTEXTS[context][2], DISCRETE_CONTEXTS[context][3]
        count = min(rng.choice(DISCRETE_ROWS), high - low + 1)
        values = sorted(rng.sample(range(low, high + 1), count))
        frequencies = [rng.randint(*DISCRETE_FREQUENCY) for _ in values]
        return context, [rational_text(Fraction(value)) for value in values], frequencies

    def random_grouped(self, rng):
        context = rng.randrange(len(GROUPED_CONTEXTS))
        count = rng.choice(GROUPED_CLASSES)
        if rng.random() < UNEQUAL_WIDTH_SHARE:
            widths = [rng.choice(GROUPED_WIDTHS) for _ in range(count)]
        else:
            widths = [rng.choice(GROUPED_WIDTHS)] * count
        boundaries = [rng.choice(GROUPED_STARTS)]
        for width in widths:
            boundaries.append(boundaries[-1] + width)
        frequencies = [rng.randint(*GROUPED_FREQUENCY) for _ in range(count)]
        return context, boundaries, frequencies

    def build_discrete(self, rng):
        context, values, frequencies = self.random_discrete(rng)
        asked = rng.sample(MEASURES, rng.choice((2, 3)))
        return {"form": "discrete", "context": context, "values": values,
                "frequencies": frequencies, "asked": asked}

    def build_grouped(self, rng):
        context, boundaries, frequencies = self.random_grouped(rng)
        asked = ["mean"] + rng.sample(("modal", "median"), rng.choice((1, 2)))
        return {"form": "grouped", "context": context, "boundaries": boundaries,
                "frequencies": frequencies, "asked": asked}

    def build_missing_frequency(self, rng):
        context, values, frequencies = self.random_discrete(rng)
        return {"form": "missing_frequency", "context": context, "values": values,
                "frequencies": frequencies, "missing": rng.randrange(len(values)),
                "follow_up": rng.choice(("median", "mode"))}

    def build_missing_value(self, rng):
        context, values, frequencies = self.random_discrete(rng)
        return {"form": "missing_value", "context": context, "values": values,
                "frequencies": frequencies, "missing": rng.choice((0, len(values) - 1)),
                "follow_up": rng.choice(("median", "mode", "range"))}

    def build_grouped_missing(self, rng):
        context, boundaries, frequencies = self.random_grouped(rng)
        return {"form": "grouped_missing", "context": context, "boundaries": boundaries,
                "frequencies": frequencies, "missing": rng.randrange(len(frequencies)),
                "follow_up": rng.choice(("modal", "median"))}

    def build_combined(self, rng):
        context, values, first = self.random_discrete(rng)
        second = [rng.randint(*DISCRETE_FREQUENCY) for _ in values]
        return {"form": "combined", "context": context, "values": values,
                "first": first, "second": second}

    def build_new_observation(self, rng):
        context, values, frequencies = self.random_discrete(rng)
        low, high = DISCRETE_CONTEXTS[context][2], DISCRETE_CONTEXTS[context][3]
        return {"form": "new_observation", "context": context, "values": values,
                "frequencies": frequencies, "new_value": rng.randint(low, high)}

    # -- rules --------------------------------------------------------------

    def check_rules(self, parameters, level):
        form = parameters["form"]
        require(form in LEVEL_FORMS[level], "Form does not belong to this level")
        self.checkers()[form](parameters)

    def checkers(self):
        return {
            "discrete": self.check_discrete,
            "grouped": self.check_grouped,
            "missing_frequency": self.check_missing_frequency,
            "missing_value": self.check_missing_value,
            "grouped_missing": self.check_grouped_missing,
            "combined": self.check_combined,
            "new_observation": self.check_new_observation,
        }

    def check_discrete(self, p):
        values, frequencies = checked_discrete(p)
        asked = p["asked"]
        require(isinstance(asked, list) and len(asked) in (2, 3)
                and len(set(asked)) == len(asked) and all(name in MEASURES for name in asked),
                "Unexpected measures")
        if "mean" in asked:
            mean = table_mean(values, frequencies)
            require(two_places(mean), "Mean needs at most two decimal places")
            require(mean != sum(values, Fraction(0)) / len(values),
                    "The unweighted mean would also be right")
        if "mode" in asked:
            require(table_mode(values, frequencies) is not None, "Expected a single mode")

    def check_grouped(self, p):
        boundaries, frequencies = checked_grouped(p)
        asked = p["asked"]
        require(isinstance(asked, list) and len(asked) in (2, 3) and asked[0] == "mean"
                and len(set(asked)) == len(asked)
                and all(name in GROUPED_FINDERS for name in asked[1:]),
                "Unexpected grouped tasks")
        require(two_places(grouped_estimate(boundaries, frequencies)),
                "Estimated mean needs at most two decimal places")
        for name in asked[1:]:
            require(GROUPED_FINDERS[name](frequencies) is not None,
                    "The {} class is not uniquely defined".format(name))
        if len(asked) == 3:
            require(modal_class(frequencies) != median_class(frequencies),
                    "Modal and median classes should differ when both are asked")

    def check_missing_frequency(self, p):
        values, frequencies = checked_discrete(p)
        missing = checked_index(p["missing"], len(values))
        mean = table_mean(values, frequencies)
        require(two_places(mean), "Mean needs at most two decimal places")
        require(values[missing] != mean, "The mean would not determine the missing frequency")
        require(p["follow_up"] in ("median", "mode"), "Unexpected follow-up")
        require(TABLE_MEASURES[p["follow_up"]](values, frequencies) is not None,
                "Follow-up measure does not exist")

    def check_missing_value(self, p):
        values, frequencies = checked_discrete(p)
        missing = checked_index(p["missing"], len(values))
        require(missing in (0, len(values) - 1), "The missing value must be the first or last row")
        # A gap of one next to the missing value would give the answer away.
        if missing == 0:
            require(values[1] - values[0] >= 2, "Missing value is guessable from the table")
        else:
            require(values[-1] - values[-2] >= 2, "Missing value is guessable from the table")
        require(two_places(table_mean(values, frequencies)), "Mean needs at most two decimal places")
        require(p["follow_up"] in ("median", "mode", "range"), "Unexpected follow-up")
        require(TABLE_MEASURES[p["follow_up"]](values, frequencies) is not None,
                "Follow-up measure does not exist")

    def check_grouped_missing(self, p):
        boundaries, frequencies = checked_grouped(p)
        missing = checked_index(p["missing"], len(frequencies))
        estimate = grouped_estimate(boundaries, frequencies)
        require(two_places(estimate), "Estimated mean needs at most two decimal places")
        require(midpoint(boundaries[missing], boundaries[missing + 1]) != estimate,
                "The estimate would not determine the missing frequency")
        require(p["follow_up"] in GROUPED_FINDERS, "Unexpected follow-up")
        require(GROUPED_FINDERS[p["follow_up"]](frequencies) is not None,
                "Follow-up class is not uniquely defined")

    def check_combined(self, p):
        values, first = checked_discrete(p, "first")
        _, second = checked_discrete(p, "second")
        both = [a + b for a, b in zip(first, second)]
        first_mean = table_mean(values, first)
        require(two_places(first_mean) and two_places(table_mean(values, both)),
                "Means need at most two decimal places")
        require(first_mean != table_mean(values, second), "The groups need different means")

    def check_new_observation(self, p):
        values, frequencies = checked_discrete(p)
        context = DISCRETE_CONTEXTS[p["context"]]
        new_value = p["new_value"]
        require(type(new_value) is int and context[2] <= new_value <= context[3],
                "New value outside the context's range")
        old_mean = table_mean(values, frequencies)
        new_mean = self.moved_mean(values, frequencies, new_value)
        require(two_places(old_mean) and two_places(new_mean),
                "Means need at most two decimal places")
        require(new_mean != old_mean, "The new value must change the mean")

    @staticmethod
    def moved_mean(values, frequencies, new_value):
        total = sum(frequencies)
        return (table_mean(values, frequencies) * total + new_value) / (total + 1)

    # -- displayed parts ----------------------------------------------------

    def parts(self, p, level):
        return {
            "discrete": self.parts_discrete,
            "grouped": self.parts_grouped,
            "missing_frequency": self.parts_missing_frequency,
            "missing_value": self.parts_missing_value,
            "grouped_missing": self.parts_grouped_missing,
            "combined": self.parts_combined,
            "new_observation": self.parts_new_observation,
        }[p["form"]](p)

    def parts_discrete(self, p):
        description = DISCRETE_CONTEXTS[p["context"]][0]
        values = [Fraction(value) for value in p["values"]]
        frequencies = p["frequencies"]
        asked = p["asked"]
        table = discrete_table(p["context"], values, frequencies)
        instruction = "The table shows {}. {}".format(
            description, lettered(MEASURE_TASKS[name] for name in asked))
        results = [(name, TABLE_MEASURES[name](values, frequencies)) for name in asked]
        answer = {"kind": "frequency_table"}
        for name, value in results:
            answer[name] = rational_text(value)
        display = " ".join("({}) {} = {}.".format(letter, name.capitalize(), decimal_text(value))
                           for letter, (name, value) in zip(LETTERS, results))
        marks = len(asked) + (1 if "mean" in asked else 0)
        return assemble(instruction, table, answer, display, marks, 6)

    def parts_grouped(self, p):
        description = GROUPED_CONTEXTS[p["context"]][0]
        boundaries, frequencies = p["boundaries"], p["frequencies"]
        asked = p["asked"]
        table = grouped_table(p["context"], boundaries, frequencies)
        instruction = "The table shows {}. {}".format(
            description, lettered(CLASS_TASKS[name] for name in asked))
        estimate = grouped_estimate(boundaries, frequencies)
        answer = {"kind": "frequency_table", "mean": rational_text(estimate)}
        pieces = ["(a) Estimated mean = {}.".format(decimal_text(estimate))]
        for letter, name in zip(LETTERS[1:], asked[1:]):
            answer[name] = class_text(boundaries, GROUPED_FINDERS[name](frequencies))
            pieces.append("({}) {}: {}.".format(letter, CLASS_LABELS[name], answer[name]))
        return assemble(instruction, table, answer, " ".join(pieces), 3 + len(asked) - 1, 6)

    def parts_missing_frequency(self, p):
        description = DISCRETE_CONTEXTS[p["context"]][0]
        values = [Fraction(value) for value in p["values"]]
        frequencies, missing, follow_up = p["frequencies"], p["missing"], p["follow_up"]
        table = discrete_table(p["context"], values, frequencies, hide_frequency=missing)
        instruction = (
            "The table shows {}. One frequency, f, is missing. The mean is {}. "
            "(a) Find f. (b) {}"
        ).format(description, decimal_text(table_mean(values, frequencies)),
                 MEASURE_TASKS[follow_up])
        extra = TABLE_MEASURES[follow_up](values, frequencies)
        answer = {"kind": "frequency_table",
                  "missing": rational_text(Fraction(frequencies[missing])),
                  follow_up: rational_text(extra)}
        display = "(a) f = {}. (b) {} = {}.".format(
            frequencies[missing], follow_up.capitalize(), decimal_text(extra))
        return assemble(instruction, table, answer, display, 5, 7)

    def parts_missing_value(self, p):
        description = DISCRETE_CONTEXTS[p["context"]][0]
        values = [Fraction(value) for value in p["values"]]
        frequencies, missing, follow_up = p["frequencies"], p["missing"], p["follow_up"]
        table = discrete_table(p["context"], values, frequencies, hide_value=missing)
        instruction = (
            "The table shows {}. One value, x, is missing. The mean is {}. "
            "(a) Find x. (b) {}"
        ).format(description, decimal_text(table_mean(values, frequencies)),
                 MEASURE_TASKS[follow_up])
        extra = TABLE_MEASURES[follow_up](values, frequencies)
        answer = {"kind": "frequency_table",
                  "missing": rational_text(values[missing]),
                  follow_up: rational_text(extra)}
        display = "(a) x = {}. (b) {} = {}.".format(
            decimal_text(values[missing]), follow_up.capitalize(), decimal_text(extra))
        return assemble(instruction, table, answer, display, 5, 7)

    def parts_grouped_missing(self, p):
        description = GROUPED_CONTEXTS[p["context"]][0]
        boundaries, frequencies = p["boundaries"], p["frequencies"]
        missing, follow_up = p["missing"], p["follow_up"]
        table = grouped_table(p["context"], boundaries, frequencies, hide_frequency=missing)
        instruction = (
            "The table shows {}. One frequency, f, is missing. An estimate for the "
            "mean is {}. (a) Find f. (b) {}"
        ).format(description, decimal_text(grouped_estimate(boundaries, frequencies)),
                 CLASS_TASKS[follow_up])
        found = class_text(boundaries, GROUPED_FINDERS[follow_up](frequencies))
        answer = {"kind": "frequency_table",
                  "missing": rational_text(Fraction(frequencies[missing])),
                  follow_up: found}
        display = "(a) f = {}. (b) {}: {}.".format(
            frequencies[missing], CLASS_LABELS[follow_up], found)
        return assemble(instruction, table, answer, display, 5, 8)

    def parts_combined(self, p):
        description, heading = DISCRETE_CONTEXTS[p["context"]][:2]
        values = [Fraction(value) for value in p["values"]]
        first, second = p["first"], p["second"]
        both = [a + b for a, b in zip(first, second)]
        table = {
            "kind": "table", "version": 1,
            "headers": [heading, "Group A", "Group B"],
            "rows": [[decimal_text(value), str(a), str(b)]
                     for value, a, b in zip(values, first, second)],
        }
        instruction = (
            "The table shows {}, split into two groups, A and B. "
            "(a) Work out the mean for group A. "
            "(b) Work out the mean for both groups together."
        ).format(description)
        first_mean, both_mean = table_mean(values, first), table_mean(values, both)
        answer = {"kind": "frequency_table", "first_mean": rational_text(first_mean),
                  "combined_mean": rational_text(both_mean)}
        display = "(a) Group A mean = {}. (b) Combined mean = {}.".format(
            decimal_text(first_mean), decimal_text(both_mean))
        return assemble(instruction, table, answer, display, 5, 8)

    def parts_new_observation(self, p):
        description, _, _, _, single, plural = DISCRETE_CONTEXTS[p["context"]]
        values = [Fraction(value) for value in p["values"]]
        frequencies, new_value = p["frequencies"], p["new_value"]
        table = discrete_table(p["context"], values, frequencies)
        old_mean = table_mean(values, frequencies)
        new_mean = self.moved_mean(values, frequencies, new_value)
        instruction = (
            "The table shows {}. (a) Work out the mean. One more {} is then recorded, "
            "and the mean of all {} {} becomes {}. (b) Find the value for the new {}."
        ).format(description, single, sum(frequencies) + 1, plural,
                 decimal_text(new_mean), single)
        answer = {"kind": "frequency_table", "mean": rational_text(old_mean),
                  "new_value": rational_text(Fraction(new_value))}
        display = "(a) Mean = {}. (b) The new {} has value {}.".format(
            decimal_text(old_mean), single, new_value)
        return assemble(instruction, table, answer, display, 5, 8)

    # -- independent check --------------------------------------------------

    def validate_independently(self, question):
        """Expand tables into raw data for the statistics module, and solve
        reverse forms with SymPy from the facts the prompt states."""
        import sympy

        p = question.parameters
        answer = question.answer
        form = p["form"]

        if form == "discrete":
            data = expand([Fraction(v) for v in p["values"]], p["frequencies"])
            for name in p["asked"]:
                require(Fraction(answer[name]) == independent_measure(name, data),
                        "Independent {} disagrees".format(name))
            return True

        if form in ("grouped", "grouped_missing"):
            boundaries, frequencies = p["boundaries"], p["frequencies"]
            mids = [midpoint(a, b) for a, b in zip(boundaries, boundaries[1:])]
            stated = independent_mean(expand(mids, frequencies))
            if form == "grouped":
                require(Fraction(answer["mean"]) == stated, "Independent estimate disagrees")
                tasks = p["asked"][1:]
            else:
                f = sympy.Symbol("f")
                counts = [f if i == p["missing"] else sympy.Integer(n)
                          for i, n in enumerate(frequencies)]
                equation = sympy.Eq(sum(to_sympy(m) * n for m, n in zip(mids, counts)),
                                    to_sympy(stated) * sum(counts))
                require(solve_single(equation, f) == to_sympy(answer["missing"]),
                        "Independent missing frequency disagrees")
                tasks = [p["follow_up"]]
            for name in tasks:
                index = independent_class(name, frequencies)
                require(answer[name] == class_text(boundaries, index),
                        "Independent {} class disagrees".format(name))
            return True

        values = [Fraction(v) for v in p["values"]]

        if form == "combined":
            first = expand(values, p["first"])
            second = expand(values, p["second"])
            require(Fraction(answer["first_mean"]) == independent_mean(first),
                    "Independent group A mean disagrees")
            require(Fraction(answer["combined_mean"]) == independent_mean(first + second),
                    "Independent combined mean disagrees")
            return True

        data = expand(values, p["frequencies"])
        stated = independent_mean(data)

        if form == "new_observation":
            require(Fraction(answer["mean"]) == stated, "Independent mean disagrees")
            new_mean = independent_mean(data + [Fraction(p["new_value"])])
            x = sympy.Symbol("x")
            equation = sympy.Eq((sum(to_sympy(v) for v in data) + x) / (len(data) + 1),
                                to_sympy(new_mean))
            require(solve_single(equation, x) == to_sympy(answer["new_value"]),
                    "Independent new value disagrees")
            return True

        missing = p["missing"]
        if form == "missing_frequency":
            f = sympy.Symbol("f")
            counts = [f if i == missing else sympy.Integer(n)
                      for i, n in enumerate(p["frequencies"])]
            equation = sympy.Eq(sum(to_sympy(v) * n for v, n in zip(values, counts)),
                                to_sympy(stated) * sum(counts))
            require(solve_single(equation, f) == to_sympy(answer["missing"]),
                    "Independent missing frequency disagrees")
        else:
            x = sympy.Symbol("x")
            shown = [x if i == missing else to_sympy(v) for i, v in enumerate(values)]
            equation = sympy.Eq(sum(v * n for v, n in zip(shown, p["frequencies"])),
                                to_sympy(stated) * sum(p["frequencies"]))
            require(solve_single(equation, x) == to_sympy(answer["missing"]),
                    "Independent missing value disagrees")
        follow_up = p["follow_up"]
        require(Fraction(answer[follow_up]) == independent_measure(follow_up, data),
                "Independent follow-up {} disagrees".format(follow_up))
        return True