"""Averages and range: mean, median, mode and range, forwards and in reverse.

Version 2 of data.averages.median_range. Version 1 only asked for the median
and range of a listed data set. This version covers all four measures, asks
for several in each question, and levels up to reverse problems where the
measures are given and the numbers must be found.

Levels
    1  Find two measures of a short list of whole numbers.
    2  Find three or all four measures, always including the mean. Lists are
       longer and may have an even count, negative numbers or decimals.
    3  Two cards are face down. Use the mean and one other fact to find
       them, then find a measure that was not given.
    4  Every number is hidden. Find them all from the mean, the range and
       the median (and the mode for four or five numbers).

Reverse questions are only emitted when exactly one set of positive whole
numbers fits the facts. validate() proves this by searching every set with
the right total; validate_independently() repeats the proof with SymPy's
partition generator and the standard library's statistics functions.
"""
from fractions import Fraction

from .core import Content, GeneratorInfo, rational_text, require
from .family import GeneratorFamily


INFO = GeneratorInfo(
    id="data.averages.median_range",
    version=2,
    topic="data",
    subtopic="averages",
    title="Averages and range: mean, median, mode and range",
    difficulty_descriptions={
        1: "Find two of the mean, median, mode and range of a short list of whole numbers.",
        2: "Find three or four measures including the mean; even counts, negatives or decimals.",
        3: "Find two face-down cards from the mean and one other fact, then another measure.",
        4: "Find every number from the mean, range, median and mode.",
    },
    tags=("averages", "mean", "median", "mode", "range", "reverse"),
)


# ---------------------------------------------------------------------------
# Editable settings
# ---------------------------------------------------------------------------

MEASURES = ("mean", "median", "mode", "range")

# Level 1: short lists with an odd count, so the median is a listed value.
LEVEL_1_COUNTS = (5, 7)
LEVEL_1_BOUNDS = (1, 20)
LEVEL_1_MEASURES_ASKED = 2

# Level 2 forms: (lowest, highest, scale). Decimal values are counted in
# tenths, so (1, 99, 10) means 0.1 to 9.9 with no whole numbers.
LEVEL_2_COUNTS = (6, 7, 8, 9)
LEVEL_2_FORMS = {
    "whole": (1, 40, 1),
    "signed": (-15, 15, 1),
    "decimal": (1, 99, 10),
}

# Level 3: total number of cards (two of them face down) and card values.
LEVEL_3_COUNTS = (5, 6, 7)
LEVEL_3_BOUNDS = (1, 20)
LEVEL_3_SECOND_FACTS = ("median", "mode", "range")

# Level 4 forms: how many numbers are hidden and which facts are given.
LEVEL_4_FORMS = {
    "three": (3, ("mean", "median", "range")),
    "four": (4, ("mean", "median", "mode", "range")),
    "five": (5, ("mean", "median", "mode", "range")),
}
LEVEL_4_BOUNDS = (1, 12)

# Optional real-world lead-ins for whole-number lists at levels 1 and 2.
# Every lead-in must suit whole numbers from 1 to 40.
CONTEXTS = (
    "The numbers of minutes {count} students spent on homework last night were",
    "The scores of {count} students in a quiz marked out of 40 were",
    "The numbers of pages {count} students read yesterday were",
    "The numbers of text messages {count} friends sent on Saturday were",
)
CONTEXT_SHARE = 0.5


# ---------------------------------------------------------------------------
# Fixed wording and limits
# ---------------------------------------------------------------------------

COUNT_WORDS = {
    2: "two", 3: "three", 4: "four", 5: "five",
    6: "six", 7: "seven", 8: "eight", 9: "nine",
}
LETTERS = "abcd"

# Reverse levels reject many candidate sets because they have more than one
# solution, so generation is allowed plenty of attempts.
ATTEMPTS = 3000

FORWARD_KEYS = {"form", "values", "asked", "context"}
FACE_DOWN_KEYS = {"form", "known", "hidden", "facts", "asked"}
ALL_HIDDEN_KEYS = {"form", "numbers", "facts"}


# ---------------------------------------------------------------------------
# The four measures (exact Fractions throughout)
# ---------------------------------------------------------------------------

def mean_value(values):
    return sum(values, Fraction(0)) / len(values)


def median_value(values):
    """The middle value, or the midpoint of the two middle values."""
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def mode_value(values):
    """The single most common value, or None when there is no unique mode."""
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    highest = max(counts.values())
    modes = [value for value, times in counts.items() if times == highest]
    if highest < 2 or len(modes) != 1:
        return None
    return modes[0]


def range_value(values):
    return max(values) - min(values)


MEASURE_FUNCTIONS = {
    "mean": mean_value,
    "median": median_value,
    "mode": mode_value,
    "range": range_value,
}


def measure_value(name, values):
    return MEASURE_FUNCTIONS[name](values)


def fact_values(values, facts):
    """Exact values of the named measures; every one must exist."""
    found = {name: measure_value(name, values) for name in facts}
    require(all(value is not None for value in found.values()),
            "A stated measure does not exist for this data")
    return found


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def decimal_text(value):
    """Exact formatting for this family's integers, tenths and hundredths."""
    value = Fraction(value)
    scaled = value * 100
    require(scaled.denominator == 1, "Expected at most two decimal places")
    sign = "-" if scaled < 0 else ""
    whole, remainder = divmod(abs(scaled.numerator), 100)
    return sign + str(whole) + (
        "." + str(remainder).zfill(2).rstrip("0") if remainder else ""
    )


def join_with_and(items):
    items = list(items)
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def parse_values(stored):
    """Stored rational_text values back to Fractions, insisting on canonical text."""
    require(isinstance(stored, list) and stored, "Expected a list of values")
    require(all(isinstance(item, str) for item in stored), "Values must be stored as text")
    values = [Fraction(item) for item in stored]
    require(stored == [rational_text(value) for value in values],
            "Non-canonical stored values")
    return values


# ---------------------------------------------------------------------------
# Reverse problems: search for every set that fits the facts
# ---------------------------------------------------------------------------

def nondecreasing_sets(count, total, smallest, largest):
    """Every nondecreasing tuple of count whole numbers in [smallest, largest]
    with the given total."""
    if count == 0:
        if total == 0:
            yield ()
        return
    highest_first = min(largest, total // count)
    for first in range(smallest, highest_first + 1):
        rest_total = total - first
        if rest_total > (count - 1) * largest:
            continue
        for rest in nondecreasing_sets(count - 1, rest_total, first, largest):
            yield (first,) + rest


def candidate_hidden_sets(count, total, spread=None):
    """Candidate sets of positive whole numbers, smallest first.

    When the range is known and no other cards are showing, the smallest and
    largest hidden values differ by exactly spread, which cuts the search.
    """
    if spread is None:
        for values in nondecreasing_sets(count, total, 1, total):
            yield values
        return
    for low in range(1, total // count + 1):
        high = low + spread
        middle_total = total - low - high
        if count == 2:
            if middle_total == 0:
                yield (low, high)
            continue
        for middle in nondecreasing_sets(count - 2, middle_total, low, high):
            yield (low,) + middle + (high,)


def matching_hidden_sets(hidden_count, known, facts):
    """Every set of hidden positive whole numbers consistent with the facts.

    known is a list of Fractions already showing. facts maps measure names to
    exact values and must include the mean, which fixes the hidden total.
    Returns sorted lists of ints; a well-posed question gives exactly one.
    """
    total_count = hidden_count + len(known)
    hidden_total = facts["mean"] * total_count - sum(known, Fraction(0))
    if hidden_total.denominator != 1 or hidden_total < hidden_count:
        return []
    hidden_total = int(hidden_total)
    spread = int(facts["range"]) if (not known and "range" in facts) else None
    found = []
    for hidden in candidate_hidden_sets(hidden_count, hidden_total, spread):
        values = list(known) + [Fraction(value) for value in hidden]
        if all(measure_value(name, values) == value for name, value in facts.items()):
            found.append(list(hidden))
    return found


# ---------------------------------------------------------------------------
# Independent checking (standard library statistics and SymPy partitions)
# ---------------------------------------------------------------------------

# Cheapest filters first when checking candidate sets.
INDEPENDENT_CHECK_ORDER = ("range", "mode", "median", "mean")


def independent_measure(name, values):
    import statistics

    if name == "mean":
        return Fraction(statistics.mean(values))
    if name == "median":
        return Fraction(statistics.median(values))
    if name == "range":
        ordered = sorted(values)
        return ordered[-1] - ordered[0]
    modes = statistics.multimode(values)
    if len(modes) == 1 and values.count(modes[0]) > 1:
        return Fraction(modes[0])
    return None


def independent_solutions(hidden_count, known, stated):
    """Every hidden set that fits, found from SymPy's integer partitions."""
    from sympy.utilities.iterables import partitions

    total = stated["mean"] * (hidden_count + len(known)) - sum(known, Fraction(0))
    if total.denominator != 1 or total < hidden_count:
        return []
    names = sorted(stated, key=INDEPENDENT_CHECK_ORDER.index)
    solutions = []
    for part in partitions(int(total), m=hidden_count):
        if sum(part.values()) != hidden_count:
            continue
        hidden = sorted(Fraction(value) for value, times in part.items()
                        for _ in range(times))
        values = list(known) + hidden
        if all(independent_measure(name, values) == stated[name] for name in names):
            solutions.append(hidden)
    return sorted(solutions)


# ---------------------------------------------------------------------------
# Construction helpers
# ---------------------------------------------------------------------------

def data_with_one_mode(rng, count, pool):
    """count values from pool: all different except one value used twice."""
    distinct = rng.sample(pool, count - 1)
    values = distinct + [rng.choice(distinct)]
    rng.shuffle(values)
    return values


def choose_context(rng):
    if rng.random() < CONTEXT_SHARE:
        return rng.randrange(len(CONTEXTS))
    return -1


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class MedianAndRange(GeneratorFamily):
    """All four averages and range, forwards and in reverse.

    The class keeps its v1 name because the catalogue imports it.
    """
    info = INFO
    keys = {1: FORWARD_KEYS, 2: FORWARD_KEYS, 3: FACE_DOWN_KEYS, 4: ALL_HIDDEN_KEYS}

    # -- build --------------------------------------------------------------

    def build(self, level, rng):
        builder = {
            1: self.build_level_1,
            2: self.build_level_2,
            3: self.build_face_down,
        }.get(level)
        if level == 4:
            # Choose the form once, so forms that rarely give a uniquely
            # solvable set are not crowded out by forms that succeed easily.
            form = rng.choice(sorted(LEVEL_4_FORMS))

            def builder(rng):
                return self.build_all_hidden(rng, form)
        for attempt in range(ATTEMPTS):
            parameters = builder(rng)
            if parameters is not None:
                return parameters
        raise ValueError("Could not construct a suitable averages question")

    def build_level_1(self, rng):
        count = rng.choice(LEVEL_1_COUNTS)
        lower, upper = LEVEL_1_BOUNDS
        units = data_with_one_mode(rng, count, list(range(lower, upper + 1)))
        values = [Fraction(unit) for unit in units]
        asked = rng.sample(MEASURES, LEVEL_1_MEASURES_ASKED)
        if "mean" in asked and mean_value(values).denominator != 1:
            return None
        return {
            "form": "whole",
            "values": [rational_text(value) for value in values],
            "asked": asked,
            "context": choose_context(rng),
        }

    def build_level_2(self, rng):
        form = rng.choice(sorted(LEVEL_2_FORMS))
        lower, upper, scale = LEVEL_2_FORMS[form]
        pool = [unit for unit in range(lower, upper + 1) if scale == 1 or unit % scale]
        count = rng.choice(LEVEL_2_COUNTS)
        units = data_with_one_mode(rng, count, pool)
        values = [Fraction(unit, scale) for unit in units]
        if form == "signed" and not min(values) < 0 < max(values):
            return None
        if (mean_value(values) * 100).denominator != 1:
            return None
        others = rng.sample(("median", "mode", "range"), rng.choice((2, 3)))
        asked = ["mean"] + others
        rng.shuffle(asked)
        return {
            "form": form,
            "values": [rational_text(value) for value in values],
            "asked": asked,
            "context": choose_context(rng) if form == "whole" else -1,
        }

    def build_face_down(self, rng):
        count = rng.choice(LEVEL_3_COUNTS)
        lower, upper = LEVEL_3_BOUNDS
        units = [rng.randint(lower, upper) for _ in range(count)]
        values = [Fraction(unit) for unit in units]
        if mean_value(values).denominator != 1 or range_value(values) == 0:
            return None
        facts = ["mean", rng.choice(LEVEL_3_SECOND_FACTS)]
        stated = {name: measure_value(name, values) for name in facts}
        if any(value is None for value in stated.values()):
            return None
        unasked = [name for name in MEASURES
                   if name not in facts and measure_value(name, values) is not None]
        if not unasked:
            return None
        asked = [rng.choice(unasked)]
        positions = rng.sample(range(count), 2)
        hidden = sorted(units[index] for index in positions)
        known = [units[index] for index in range(count) if index not in positions]
        if matching_hidden_sets(2, [Fraction(value) for value in known], stated) != [hidden]:
            return None
        return {
            "form": "face_down",
            "known": [rational_text(Fraction(value)) for value in known],
            "hidden": [rational_text(Fraction(value)) for value in hidden],
            "facts": facts,
            "asked": asked,
        }

    def build_all_hidden(self, rng, form):
        count, facts = LEVEL_4_FORMS[form]
        lower, upper = LEVEL_4_BOUNDS
        units = sorted(rng.randint(lower, upper) for _ in range(count))
        values = [Fraction(unit) for unit in units]
        if (mean_value(values) * 2).denominator != 1 or range_value(values) == 0:
            return None
        stated = {name: measure_value(name, values) for name in facts}
        if any(value is None for value in stated.values()):
            return None
        if matching_hidden_sets(count, [], stated) != [units]:
            return None
        return {
            "form": form,
            "numbers": [rational_text(value) for value in values],
            "facts": list(facts),
        }

    # -- rules --------------------------------------------------------------

    def check_rules(self, parameters, level):
        if level in (1, 2):
            self.check_forward(parameters, level)
        elif level == 3:
            self.check_face_down(parameters)
        else:
            self.check_all_hidden(parameters)

    def check_forward(self, parameters, level):
        form = parameters["form"]
        allowed = ("whole",) if level == 1 else tuple(sorted(LEVEL_2_FORMS))
        require(form in allowed, "Unexpected form")
        values = parse_values(parameters["values"])
        counts = LEVEL_1_COUNTS if level == 1 else LEVEL_2_COUNTS
        require(len(values) in counts, "Unexpected data set size")
        if level == 1:
            lower, upper = LEVEL_1_BOUNDS
            scale = 1
        else:
            lower, upper, scale = LEVEL_2_FORMS[form]
        require(all(Fraction(lower, scale) <= value <= Fraction(upper, scale)
                    for value in values), "Value outside bounds")
        if scale == 1:
            require(all(value.denominator == 1 for value in values), "Expected whole numbers")
        else:
            require(all((value * scale).denominator == 1 and value.denominator != 1
                        for value in values), "Expected values in tenths")
        if form == "signed":
            require(min(values) < 0 < max(values), "Expected both signs")
        require(len(set(values)) == len(values) - 1, "Expected exactly one repeated value")
        require(mode_value(values) is not None, "Expected a single mode")

        asked = parameters["asked"]
        require(isinstance(asked, list) and len(set(asked)) == len(asked),
                "Repeated measure")
        require(all(name in MEASURES for name in asked), "Unknown measure")
        if level == 1:
            require(len(asked) == LEVEL_1_MEASURES_ASKED, "Level 1 asks for two measures")
            if "mean" in asked:
                require(mean_value(values).denominator == 1, "Level 1 mean must be whole")
        else:
            require(len(asked) in (3, 4) and "mean" in asked,
                    "Level 2 asks for the mean and at least two more measures")
            require((mean_value(values) * 100).denominator == 1,
                    "Mean needs at most two decimal places")

        context = parameters["context"]
        require(type(context) is int, "Context must be an integer")
        require(context == -1 or (form == "whole" and 0 <= context < len(CONTEXTS)),
                "Unexpected context")

    def check_face_down(self, parameters):
        require(parameters["form"] == "face_down", "Unexpected form")
        known = parse_values(parameters["known"])
        hidden = parse_values(parameters["hidden"])
        require(len(hidden) == 2 and hidden == sorted(hidden),
                "Expected two face-down cards in order")
        values = known + hidden
        require(len(values) in LEVEL_3_COUNTS, "Unexpected number of cards")
        lower, upper = LEVEL_3_BOUNDS
        require(all(value.denominator == 1 and lower <= value <= upper for value in values),
                "Card value outside bounds")
        facts = parameters["facts"]
        require(isinstance(facts, list) and len(facts) == 2 and facts[0] == "mean"
                and facts[1] in LEVEL_3_SECOND_FACTS, "Unexpected facts")
        stated = fact_values(values, facts)
        require(stated["mean"].denominator == 1, "Level 3 mean must be whole")
        asked = parameters["asked"]
        require(isinstance(asked, list) and len(asked) == 1 and asked[0] in MEASURES
                and asked[0] not in facts, "Unexpected follow-up measure")
        require(measure_value(asked[0], values) is not None,
                "Follow-up measure does not exist for this data")
        require(matching_hidden_sets(2, known, stated) == [[int(value) for value in hidden]],
                "Face-down cards are not uniquely determined")

    def check_all_hidden(self, parameters):
        form = parameters["form"]
        require(form in LEVEL_4_FORMS, "Unexpected form")
        count, facts = LEVEL_4_FORMS[form]
        require(parameters["facts"] == list(facts), "Unexpected facts")
        numbers = parse_values(parameters["numbers"])
        require(len(numbers) == count and numbers == sorted(numbers),
                "Expected the hidden numbers in order")
        lower, upper = LEVEL_4_BOUNDS
        require(all(value.denominator == 1 and lower <= value <= upper for value in numbers),
                "Hidden number outside bounds")
        require(range_value(numbers) > 0, "Expected a positive range")
        stated = fact_values(numbers, facts)
        require((stated["mean"] * 2).denominator == 1, "Mean must be whole or end in .5")
        require(matching_hidden_sets(count, [], stated) == [[int(value) for value in numbers]],
                "Hidden numbers are not uniquely determined")

    # -- displayed parts ----------------------------------------------------

    def parts(self, parameters, level):
        if level in (1, 2):
            return self.forward_parts(parameters, level)
        if level == 3:
            return self.face_down_parts(parameters)
        return self.all_hidden_parts(parameters)

    def forward_parts(self, parameters, level):
        values = [Fraction(value) for value in parameters["values"]]
        asked = parameters["asked"]
        word = COUNT_WORDS[len(values)]
        if parameters["context"] >= 0:
            lead = CONTEXTS[parameters["context"]].format(count=word)
        else:
            lead = "Here are {} numbers".format(word)
        listing = ", ".join(decimal_text(value) for value in values)
        tasks = " ".join("({}) Find the {}.".format(letter, name)
                         for letter, name in zip(LETTERS, asked))
        results = [(name, measure_value(name, values)) for name in asked]
        answer = {"kind": "averages"}
        for name, value in results:
            answer[name] = rational_text(value)
        display = " ".join("({}) {} = {}.".format(letter, name.capitalize(), decimal_text(value))
                           for letter, (name, value) in zip(LETTERS, results))
        return {
            "prompt": Content("{}: {}. {}".format(lead, listing, tasks)),
            "answer": answer,
            "answer_display": Content(display),
            "marks": 2 if level == 1 else len(asked),
            "working_lines": 4 if level == 1 else 6,
        }

    def face_down_parts(self, parameters):
        known = [Fraction(value) for value in parameters["known"]]
        hidden = [Fraction(value) for value in parameters["hidden"]]
        values = known + hidden
        total_word = COUNT_WORDS[len(values)]
        known_word = COUNT_WORDS[len(known)]
        second = parameters["facts"][1]
        follow_up = parameters["asked"][0]
        extra = measure_value(follow_up, values)
        prompt = Content(
            "{} cards each show a positive whole number. {} of the cards show {}. "
            "The other two cards are face down. "
            "The mean of all {} cards is {} and the {} is {}. "
            "(a) Find the numbers on the two face-down cards. "
            "(b) Find the {} of all {} cards.".format(
                total_word.capitalize(), known_word.capitalize(),
                ", ".join(decimal_text(value) for value in known),
                total_word, decimal_text(mean_value(values)),
                second, decimal_text(measure_value(second, values)),
                follow_up, total_word,
            )
        )
        answer = {
            "kind": "averages",
            "hidden": [rational_text(value) for value in hidden],
            follow_up: rational_text(extra),
        }
        display = "(a) The face-down cards are {} and {}. (b) {} = {}.".format(
            decimal_text(hidden[0]), decimal_text(hidden[1]),
            follow_up.capitalize(), decimal_text(extra),
        )
        return {
            "prompt": prompt,
            "answer": answer,
            "answer_display": Content(display),
            "marks": 4,
            "working_lines": 7,
        }

    def all_hidden_parts(self, parameters):
        numbers = [Fraction(value) for value in parameters["numbers"]]
        word = COUNT_WORDS[len(numbers)]
        descriptions = ["a {} of {}".format(name, decimal_text(measure_value(name, numbers)))
                        for name in parameters["facts"]]
        prompt = Content("{} positive whole numbers have {}. Find the {} numbers.".format(
            word.capitalize(), join_with_and(descriptions), word))
        display = "The numbers are {}.".format(
            join_with_and(decimal_text(value) for value in numbers))
        return {
            "prompt": prompt,
            "answer": {"kind": "averages", "numbers": list(parameters["numbers"])},
            "answer_display": Content(display),
            "marks": 3 if len(numbers) == 3 else 4,
            "working_lines": 8,
        }

    # -- independent check --------------------------------------------------

    def validate_independently(self, question):
        """Standard-library statistics and SymPy partitions, not this module's
        measures or search. Facts come from the parameters the prompt shows;
        the answer must be the only solution to them."""
        level = question.difficulty
        parameters = question.parameters
        answer = question.answer
        if level in (1, 2):
            values = [Fraction(value) for value in parameters["values"]]
            for name in parameters["asked"]:
                require(Fraction(answer[name]) == independent_measure(name, values),
                        "Independent {} disagrees".format(name))
            return True

        if level == 3:
            known = [Fraction(value) for value in parameters["known"]]
            shown = known + [Fraction(value) for value in parameters["hidden"]]
            claimed = sorted(Fraction(value) for value in answer["hidden"])
            hidden_count = 2
        else:
            known = []
            shown = [Fraction(value) for value in parameters["numbers"]]
            claimed = sorted(Fraction(value) for value in answer["numbers"])
            hidden_count = len(shown)
        stated = {name: independent_measure(name, shown) for name in parameters["facts"]}
        require(all(value is not None for value in stated.values()),
                "Independent check found a missing measure")
        require(independent_solutions(hidden_count, known, stated) == [claimed],
                "Independent search did not find exactly the stated answer")
        if level == 3:
            follow_up = parameters["asked"][0]
            require(Fraction(answer[follow_up]) == independent_measure(follow_up, shown),
                    "Independent follow-up measure disagrees")
        return True