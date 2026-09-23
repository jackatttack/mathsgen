"""Two-stage probability-tree questions with student and teacher diagrams.

The exact probability model is independent of the vector renderer.
Students receive a partly completed tree; answer sheets show all branches.

Level 1: ordered outcomes with replacement.
Level 2: ordered outcomes without replacement.
Level 3: either-order outcomes without replacement.
Level 4: at least one colour, or conditional probability.

All probabilities are exact Fractions. Diagram labels may independently
use equivalent terminating decimals or simplified fractions.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question,
    make_context, rational_text, rational_tex, require,
)
from .probability_tree_diagrams import (
    branch_probabilities, tree_scene,
)


# --- Teaching configuration ----------------------------------------------

COUNTER_COUNTS = tuple(range(2, 10))
COLOURS = ("red", "blue")

INFO = GeneratorInfo(
    id="probability.trees.two_stage",
    version=1,
    topic="probability",
    subtopic="probability_trees",
    title="Probability tree diagrams",
    difficulty_descriptions={
        1: "Complete a tree and calculate an ordered outcome with replacement.",
        2: "Complete a tree and calculate an ordered outcome without replacement.",
        3: "Complete a tree and calculate either-order outcomes.",
        4: "Use a tree for at-least-one or conditional probability.",
    },
    tags=(
        "probability", "tree diagrams", "independent events",
        "dependent events", "conditional probability",
    ),
)

EVENT_BY_LEVEL = {
    1: ("ordered",),
    2: ("ordered",),
    3: ("one_each",),
    4: ("at_least_one", "conditional"),
}


# --- Mathematical model --------------------------------------------------

def path_probability(first, second, red, blue, replacement):
    """Multiply the correct first and conditional second branches."""
    counts = {"red": red, "blue": blue}
    total = red + blue

    first_probability = Fraction(counts[first], total)

    remaining = total if replacement else total - 1
    second_count = counts[second]

    if not replacement and first == second:
        second_count -= 1

    second_probability = Fraction(second_count, remaining)

    return first_probability * second_probability


def event_probability(parameters):
    """Calculate the requested event from its mutually exclusive paths."""
    red = parameters["red"]
    blue = parameters["blue"]
    replacement = parameters["replacement"]
    event = parameters["event"]
    target = parameters["target"]

    def path(first, second):
        return path_probability(
            first, second, red, blue, replacement
        )

    if event == "ordered":
        return path(target[0], target[1])

    if event == "one_each":
        return path("red", "blue") + path("blue", "red")

    if event == "at_least_one":
        other = "blue" if target == "red" else "red"
        return Fraction(1) - path(other, other)

    if event == "conditional":
        # Given that at least one counter is the target colour,
        # find the probability that both are that colour.
        other = "blue" if target == "red" else "red"

        both = path(target, target)
        at_least_one = Fraction(1) - path(other, other)

        require(at_least_one > 0, "Conditional event has zero probability")
        return both / at_least_one

    raise ValueError("Unknown probability-tree event")


def event_description(parameters):
    event = parameters["event"]
    target = parameters["target"]

    if event == "ordered":
        return (
            "the first counter is {} and the second counter is {}"
        ).format(*target)

    if event == "one_each":
        return "one counter is red and the other is blue, in either order"

    if event == "at_least_one":
        return "at least one counter is {}".format(target)

    if event == "conditional":
        return (
            "both counters are {}, given that at least one is {}"
        ).format(target, target)

    raise ValueError("Unknown event")


# --- Student presentation ------------------------------------------------

def prompt_for(parameters):
    red = parameters["red"]
    blue = parameters["blue"]
    replacement = parameters["replacement"]

    instruction = (
        "A bag contains {} red counters and {} blue counters. "
    ).format(red, blue)

    if replacement:
        instruction += (
            "A counter is chosen at random, its colour is recorded, "
            "and it is replaced. The bag is mixed and a second "
            "counter is chosen at random. "
        )
    else:
        instruction += (
            "Two counters are chosen at random, one after the other, "
            "without replacement. "
        )

    instruction += (
        "Complete the missing probabilities on the tree diagram. "
        "Find the probability that {}. "
        "Give your answer as a fraction in its simplest form."
    ).format(event_description(parameters))

    return Content(instruction)


def answer_for(parameters):
    value = event_probability(parameters)

    return (
        {"kind": "rational", "value": rational_text(value)},
        Content(rational_text(value), rational_tex(value)),
    )


def diagram_for(parameters, student):
    return tree_scene(
        red=parameters["red"],
        blue=parameters["blue"],
        replacement=parameters["replacement"],
        student=student,
    )


# --- Generator -----------------------------------------------------------

class ProbabilityTrees:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)

        require(
            not context.settings,
            "This generator accepts no settings",
        )

        rng = context.rng

        red = rng.choice(COUNTER_COUNTS)
        blue = rng.choice(COUNTER_COUNTS)

        replacement = difficulty == 1
        event = rng.choice(EVENT_BY_LEVEL[difficulty])

        if event == "ordered":
            target = [rng.choice(COLOURS), rng.choice(COLOURS)]
        elif event == "one_each":
            target = "red_blue"
        else:
            target = rng.choice(COLOURS)

        parameters = {
            "red": red,
            "blue": blue,
            "replacement": replacement,
            "event": event,
            "target": target,
        }

        answer, answer_display = answer_for(parameters)

        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=prompt_for(parameters),
            answer=answer,
            answer_display=answer_display,
            worked_solution=(),
            marks={1: 3, 2: 4, 3: 5, 4: 5}[difficulty],
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=3),
            parameters=parameters,
            question_visuals=(diagram_for(parameters, student=True),),
            answer_visuals=(diagram_for(parameters, student=False),),
        )

        self.validate(question)
        return question

    def validate(self, question):
        require(
            question.generator_id == self.info.id,
            "Generator mismatch",
        )
        require(
            question.generator_version == self.info.version,
            "Generator version mismatch",
        )

        level = question.difficulty

        require(
            type(level) is int and level in EVENT_BY_LEVEL,
            "Invalid difficulty",
        )
        require(question.settings == {}, "Unsupported settings")

        p = question.parameters

        require(
            set(p) == {
                "red", "blue", "replacement", "event", "target"
            },
            "Unexpected parameters",
        )

        for colour in COLOURS:
            require(
                type(p[colour]) is int
                and p[colour] in COUNTER_COUNTS,
                "Counter count outside teaching bounds",
            )

        require(
            type(p["replacement"]) is bool
            and p["replacement"] == (level == 1),
            "Incorrect replacement rule",
        )

        require(
            p["event"] in EVENT_BY_LEVEL[level],
            "Event does not match difficulty",
        )

        event = p["event"]
        target = p["target"]

        if event == "ordered":
            require(
                isinstance(target, list)
                and len(target) == 2
                and all(colour in COLOURS for colour in target),
                "Invalid ordered outcome",
            )

        elif event == "one_each":
            require(target == "red_blue", "Invalid either-order target")

        else:
            require(
                target in COLOURS,
                "Invalid named colour",
            )

        answer, display = answer_for(p)

        require(question.answer == answer, "Incorrect probability")
        require(
            question.answer_display == display,
            "Answer display mismatch",
        )

        require(
            question.prompt == prompt_for(p),
            "Question wording mismatch",
        )

        require(
            question.visual_assets("questions")
            == (diagram_for(p, student=True),),
            "Student tree mismatch",
        )

        require(
            question.visual_assets("answers")
            == (diagram_for(p, student=False),),
            "Completed tree mismatch",
        )

        return True

    def validate_independently(self, question):
        """Enumerate individually labelled counters and count the event.

        This does not use the algebraic path_probability calculation.
        It independently checks both the event answer and branch values.
        """
        p = question.parameters

        counters = (
            ["red"] * p["red"]
            + ["blue"] * p["blue"]
        )

        outcomes = []

        for first_index, first in enumerate(counters):
            for second_index, second in enumerate(counters):
                if (
                    not p["replacement"]
                    and first_index == second_index
                ):
                    continue

                outcomes.append((first, second))

        require(outcomes, "No possible counter outcomes")

        event = p["event"]
        target = p["target"]

        def matches(first, second):
            if event == "ordered":
                return first == target[0] and second == target[1]

            if event == "one_each":
                return first != second

            if event == "at_least_one":
                return first == target or second == target

            if event == "conditional":
                return first == target and second == target

            raise ValueError("Unknown event")

        if event == "conditional":
            possible = [
                outcome for outcome in outcomes
                if target in outcome
            ]
        else:
            possible = outcomes

        successful = sum(
            1 for first, second in possible
            if matches(first, second)
        )

        expected = Fraction(successful, len(possible))

        require(
            Fraction(question.answer["value"]) == expected,
            "Independent event probability disagrees",
        )

        require(
            question.answer["value"] == rational_text(expected),
            "Probability is not simplified",
        )

        # Independently recover each tree branch from the sample space.
        first_red = sum(first == "red" for first, _ in outcomes)
        first_blue = sum(first == "blue" for first, _ in outcomes)

        red_first = [
            second for first, second in outcomes
            if first == "red"
        ]
        blue_first = [
            second for first, second in outcomes
            if first == "blue"
        ]

        expected_branches = (
            Fraction(first_red, len(outcomes)),
            Fraction(first_blue, len(outcomes)),
            Fraction(red_first.count("red"), len(red_first)),
            Fraction(red_first.count("blue"), len(red_first)),
            Fraction(blue_first.count("red"), len(blue_first)),
            Fraction(blue_first.count("blue"), len(blue_first)),
        )

        actual_branches = branch_probabilities(
            p["red"], p["blue"], p["replacement"]
        )

        require(
            actual_branches == expected_branches,
            "Tree branches disagree with independent enumeration",
        )

        return True