"""Two draws from a counter collection, with explicit replacement rules."""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)


COLOURS = ("red", "blue", "green", "yellow", "purple")
EVENTS = {1: "same", 2: "ordered", 3: "either_order", 4: "at_least_one"}


def metadata(replacement):
    suffix = "with_replacement" if replacement else "without_replacement"
    title = "Two counters " + ("with replacement" if replacement else "without replacement")
    return GeneratorInfo(
        id="probability.two_draws." + suffix,
        version=1,
        topic="probability",
        subtopic="two_draws",
        title=title,
        difficulty_descriptions={
            1: "Both counters have a specified colour.",
            2: "Two specified colours in a specified order.",
            3: "One of each of two specified colours, in either order.",
            4: "At least one counter has a specified colour.",
        },
        tags=("probability", "two_events", suffix),
    )


def probability(counts, targets, event, replacement):
    total = sum(counts.values())
    decrement = 0 if replacement else 1
    denominator = total * (total - decrement)
    first = counts[targets[0]]
    if event == "same":
        return Fraction(first * (first - decrement), denominator)
    if event in ("ordered", "either_order"):
        numerator = first * counts[targets[1]]
        if event == "either_order":
            numerator *= 2
        return Fraction(numerator, denominator)
    if event == "at_least_one":
        other = total - first
        return 1 - Fraction(other * (other - decrement), denominator)
    raise ValueError("Unknown two-draw event")


def prompt_for(parameters, replacement):
    counts = parameters["counts"]
    targets = parameters["targets"]
    event = parameters["event"]
    pieces = ["{} {} counters".format(count, colour) for colour, count in counts.items()]
    text = "A bag contains " + ", ".join(pieces[:-1]) + " and " + pieces[-1] + ". "
    if replacement:
        text += (
            "One counter is chosen at random, its colour is recorded, and it is "
            "replaced. The bag is mixed and a second counter is chosen at random. "
        )
    else:
        text += (
            "Two counters are chosen at random, one after the other, "
            "without replacement. "
        )
    if event == "same":
        text += "Find the probability that both counters are {}.".format(targets[0])
    elif event == "ordered":
        text += "Find the probability that the first counter is {} and the second is {}.".format(*targets)
    elif event == "either_order":
        text += "Find the probability of choosing one {} counter and one {} counter, in either order.".format(*targets)
    else:
        text += "Find the probability that at least one of the two counters is {}.".format(targets[0])
    return Content(text + " Give your answer as a fraction in simplest form.")


class TwoCounterDraws:
    """Shared mechanics; each replacement rule has its own registered class."""

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        colours = rng.sample(list(COLOURS), 3)
        counts = {colour: rng.randint(2, 9) for colour in colours}
        event = EVENTS[difficulty]
        targets = rng.sample(colours, 2 if difficulty in (2, 3) else 1)
        parameters = {"counts": counts, "targets": targets, "event": event}
        result = probability(counts, targets, event, self.replacement)
        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=prompt_for(parameters, self.replacement),
            answer={"kind": "rational", "value": rational_text(result)},
            answer_display=Content(rational_text(result), rational_tex(result)),
            worked_solution=(),
            marks=2 if difficulty <= 2 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=6),
            parameters=parameters,
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        require(question.difficulty in EVENTS, "Invalid difficulty")
        parameters = question.parameters
        counts, targets, event = (
            parameters["counts"], parameters["targets"], parameters["event"]
        )
        require(len(counts) == 3 and set(counts) <= set(COLOURS), "Invalid colours")
        require(all(type(n) is int and 2 <= n <= 9 for n in counts.values()), "Invalid counts")
        require(event == EVENTS[question.difficulty], "Wrong event for difficulty")
        size = 2 if question.difficulty in (2, 3) else 1
        require(len(targets) == size and len(set(targets)) == size, "Invalid event targets")
        require(set(targets) <= set(counts), "Target colour absent from bag")
        result = Fraction(question.answer["value"])
        require(0 < result < 1, "Trivial or invalid probability")
        require(result == probability(counts, targets, event, self.replacement), "Incorrect answer")
        require(question.answer["value"] == rational_text(result), "Answer is not simplified")
        require(question.prompt == prompt_for(parameters, self.replacement), "Prompt mismatch")
        require(question.answer_display.text == rational_text(result), "Displayed answer mismatch")
        require(question.answer_display.math_tex == rational_tex(result), "Math answer mismatch")
        return True

    def validate_independently(self, question):
        """Enumerate pairs of individually labelled counters.

        Without replacement the same individual counter cannot appear twice.
        With replacement every ordered pair is possible, including repeats.
        """
        parameters = question.parameters
        counters = [
            colour for colour, count in parameters["counts"].items()
            for _ in range(count)
        ]
        targets, event = parameters["targets"], parameters["event"]
        successful = total = 0
        for first_index, first in enumerate(counters):
            for second_index, second in enumerate(counters):
                if not self.replacement and first_index == second_index:
                    continue
                total += 1
                if event == "same":
                    matches = first == second == targets[0]
                elif event == "ordered":
                    matches = first == targets[0] and second == targets[1]
                elif event == "either_order":
                    matches = (
                        (first == targets[0] and second == targets[1])
                        or (first == targets[1] and second == targets[0])
                    )
                else:
                    matches = first == targets[0] or second == targets[0]
                successful += int(matches)
        require(Fraction(successful, total) == Fraction(question.answer["value"]),
                "Independent labelled-counter enumeration disagrees")
        return True


class WithReplacement(TwoCounterDraws):
    replacement = True
    info = metadata(True)


class WithoutReplacement(TwoCounterDraws):
    replacement = False
    info = metadata(False)