"""Single-draw probability from explicitly modelled collections."""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)


INFO = GeneratorInfo(
    id="probability.selection.colours",
    version=1,
    topic="probability",
    subtopic="selection",
    title="Probability of selecting coloured counters",
    difficulty_descriptions={
        1: "Select one named colour.",
        2: "Select either of two mutually exclusive colours.",
        3: "Select neither of two named colours.",
        4: "Remove some counters before selecting either of two colours.",
    },
    tags=("probability", "selection", "complement", "mutually_exclusive"),
)

COLOURS = ("red", "blue", "green", "yellow", "purple", "orange")


def contents_text(counts):
    parts = ["{} {} counters".format(count, colour) for colour, count in counts.items()]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def make_prompt(parameters):
    counts = parameters["counts"]
    selected = parameters["selected"]
    text = "A bag contains " + contents_text(counts) + ". "
    removed = parameters["removed"]
    if removed:
        colour, count = next(iter(removed.items()))
        text += "{} {} counter{} {} removed. ".format(
            count, colour, "" if count == 1 else "s",
            "is" if count == 1 else "are",
        )
    text += "The bag is mixed and one counter is chosen at random. "
    if parameters["event"] == "exclude":
        event = "neither {} nor {}".format(*selected)
    elif len(selected) == 1:
        event = selected[0]
    else:
        event = "either {} or {}".format(*selected)
    return Content(
        text + "What is the probability that it is " + event
        + "? Give your answer as a fraction in simplest form."
    )


class SelectionProbability:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        colours = rng.sample(list(COLOURS), 3 if difficulty == 1 else 4)
        counts = {colour: rng.randint(2, 15) for colour in colours}
        selected = rng.sample(colours, 1 if difficulty == 1 else 2)
        event = "exclude" if difficulty == 3 else "include"
        removed = {}
        if difficulty == 4:
            colour = rng.choice(selected)
            removed[colour] = rng.randint(1, counts[colour] - 1)
        remaining = {
            colour: count - removed.get(colour, 0)
            for colour, count in counts.items()
        }
        total = sum(remaining.values())
        favourable = sum(
            count for colour, count in remaining.items()
            if (colour in selected) == (event == "include")
        )
        result = Fraction(favourable, total)
        parameters = {
            "counts": counts, "selected": selected,
            "event": event, "removed": removed,
        }
        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=make_prompt(parameters),
            answer={"kind": "rational", "value": rational_text(result)},
            answer_display=Content(rational_text(result), rational_tex(result)),
            worked_solution=(),
            marks=2 if difficulty < 4 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=4),
            parameters=parameters,
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in (1, 2, 3, 4), "Invalid difficulty")
        parameters = question.parameters
        counts = parameters["counts"]
        selected = parameters["selected"]
        removed = parameters["removed"]
        event = parameters["event"]
        require(len(counts) == (3 if level == 1 else 4), "Wrong collection size")
        require(set(counts) <= set(COLOURS), "Unknown colour")
        require(all(type(value) is int and 2 <= value <= 15 for value in counts.values()),
                "Counts outside bounds")
        require(len(selected) == (1 if level == 1 else 2), "Wrong event size")
        require(len(set(selected)) == len(selected) and set(selected) <= set(counts),
                "Invalid selected colours")
        require(event == ("exclude" if level == 3 else "include"), "Wrong event structure")
        if level == 4:
            require(len(removed) == 1 and set(removed) <= set(selected), "Invalid removal event")
            require(all(type(value) is int and 1 <= value < counts[colour]
                        for colour, value in removed.items()), "Invalid removal count")
        else:
            require(not removed, "Unexpected removal")
        remaining = {colour: count - removed.get(colour, 0) for colour, count in counts.items()}
        total = sum(remaining.values())
        selected_count = sum(remaining[colour] for colour in selected)
        favourable = total - selected_count if event == "exclude" else selected_count
        result = Fraction(question.answer["value"])
        require(0 < result < 1, "Trivial or invalid probability")
        require(result == Fraction(favourable, total), "Incorrect probability")
        require(question.answer["value"] == rational_text(result), "Answer is not simplified")
        require(question.prompt == make_prompt(parameters), "Prompt mismatch")
        require(question.answer_display.text == rational_text(result), "Displayed answer mismatch")
        require(question.answer_display.math_tex == rational_tex(result), "Math answer mismatch")
        return True

    def validate_independently(self, question):
        """Enumerate individual counters, remove them, then count the event."""
        parameters = question.parameters
        counters = [
            colour for colour, count in parameters["counts"].items()
            for _ in range(count)
        ]
        for colour, count in parameters["removed"].items():
            for _ in range(count):
                counters.remove(colour)
        outcomes = [colour in parameters["selected"] for colour in counters]
        if parameters["event"] == "exclude":
            outcomes = [not value for value in outcomes]
        expected = Fraction(sum(outcomes), len(outcomes))
        require(expected == Fraction(question.answer["value"]),
                "Enumerated counter probability disagrees")
        return True