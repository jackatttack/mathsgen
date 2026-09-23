"""Read probabilities from two-set Venn diagrams.

Regions: 0=A only, 1=A and B, 2=B only, 3=neither.
All arithmetic uses exact fractions. An independent checker enumerates
individual members rather than repeating the region-sum calculation.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)
from .venn_diagrams import venn_asset
from .venn_notation import NOTATION, independent_regions


INFO = GeneratorInfo(
    id="probability.venn.probabilities",
    version=1,
    topic="probability",
    subtopic="venn_diagrams",
    title="Venn diagrams: calculating probabilities",
    difficulty_descriptions={
        1: "Find a set, its complement or neither event.",
        2: "Calculate intersections, unions and exclusive regions.",
        3: "Calculate probabilities from combined regions.",
        4: "Calculate conditional probabilities given membership of A or B.",
    },
    tags=("probability", "venn", "sets", "conditional_probability"),
)

LEVEL_KEYS = {
    1: ("A", "B", "not_A", "not_B", "neither"),
    2: ("both", "either", "A_only", "B_only"),
    3: (
        "not_both", "not_A_or_B", "A_or_not_B",
        "exactly_one", "both_or_neither",
    ),
    4: (
        "B_given_A", "not_B_given_A",
        "A_given_B", "not_A_given_B",
    ),
}

# Conditional event: (PDF notation, favourable regions, given regions).
CONDITIONAL = {
    "B_given_A": (r"P(B\mid A)", (1,), (0, 1)),
    "not_B_given_A": (
        r"P(B^{\prime}\mid A)", (0,), (0, 1),
    ),
    "A_given_B": (r"P(A\mid B)", (1,), (1, 2)),
    "not_A_given_B": (
        r"P(A^{\prime}\mid B)", (2,), (1, 2),
    ),
}

REGION_NAMES = (
    "A only", "A and B", "B only", "neither A nor B",
)


def event_regions(key):
    """Return favourable and conditional-universe region indices."""
    if key in CONDITIONAL:
        _, favourable, given = CONDITIONAL[key]
        return favourable, given

    require(key in NOTATION, "Unknown Venn probability event")
    return NOTATION[key][2], (0, 1, 2, 3)


def event_tex(key):
    if key in CONDITIONAL:
        return CONDITIONAL[key][0]
    return "P(" + NOTATION[key][1] + ")"


def event_text(key):
    if key in CONDITIONAL:
        labels = {
            "B_given_A": "B, given that the person is in A",
            "not_B_given_A": "not B, given that the person is in A",
            "A_given_B": "A, given that the person is in B",
            "not_A_given_B": "not A, given that the person is in B",
        }
        return "P(" + labels[key] + ")"

    return "P(" + NOTATION[key][0] + ")"


def probability_for(counts, key):
    favourable, given = event_regions(key)
    numerator = sum(counts[index] for index in favourable)
    denominator = sum(counts[index] for index in given)

    require(denominator > 0, "Conditional event has no members")
    return Fraction(numerator, denominator)


def prompt_for(parameters):
    total = sum(parameters["counts"])
    key = parameters["event"]
    return Content(
        "The Venn diagram shows {} people. "
        "One person is selected at random. Find {}. "
        "Give your answer as a fraction in its simplest form."
        .format(total, event_text(key)),
        event_tex(key),
        display_text=(
            "The Venn diagram shows {} people. One person is selected "
            "at random. Find the following probability. "
            "Give your answer as a fraction in its simplest form:"
        ).format(total),
    )


def answer_for(parameters):
    value = probability_for(
        parameters["counts"], parameters["event"]
    )
    return (
        {"kind": "rational", "value": rational_text(value)},
        Content(rational_text(value), rational_tex(value)),
    )


class VennProbability:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")

        rng = context.rng
        counts = [rng.randint(2, 15) for _ in range(4)]
        event = rng.choice(LEVEL_KEYS[difficulty])

        parameters = {"counts": counts, "event": event}
        answer, display = answer_for(parameters)
        diagram = venn_asset(values=counts)

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
            answer_display=display,
            worked_solution=(),
            marks={1: 1, 2: 2, 3: 3, 4: 3}[difficulty],
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=2),
            parameters=parameters,
            question_visuals=(diagram,),
            answer_visuals=(diagram,),
        )

        self.validate(question)
        return question

    def validate(self, question):
        require(
            question.generator_id == self.info.id
            and question.generator_version == self.info.version,
            "Venn probability generator/version mismatch",
        )
        level = question.difficulty
        require(
            type(level) is int and level in LEVEL_KEYS,
            "Invalid Venn probability difficulty",
        )
        require(question.settings == {}, "Unsupported settings")

        parameters = question.parameters
        require(
            type(parameters) is dict
            and set(parameters) == {"counts", "event"},
            "Invalid Venn probability parameters",
        )
        counts = parameters["counts"]
        require(
            isinstance(counts, list)
            and len(counts) == 4
            and all(type(value) is int and 2 <= value <= 15
                    for value in counts),
            "Invalid Venn frequency counts",
        )
        require(
            parameters["event"] in LEVEL_KEYS[level],
            "Probability event does not match difficulty",
        )

        answer, display = answer_for(parameters)
        require(question.answer == answer, "Incorrect Venn probability")
        require(
            question.answer_display == display,
            "Incorrect displayed probability",
        )
        require(
            question.prompt == prompt_for(parameters),
            "Incorrect probability prompt",
        )
        diagram = venn_asset(values=counts)
        require(
            question.visual_assets("questions") == (diagram,)
            and question.visual_assets("answers") == (diagram,),
            "Probability diagram disagrees with its counts",
        )
        return True

    def validate_independently(self, question):
        """Count individual people satisfying the requested event."""
        parameters = question.parameters
        counts = parameters["counts"]
        key = parameters["event"]

        # Independently derive ordinary set membership using set algebra.
        if key in CONDITIONAL:
            _, favourable_regions, given_regions = CONDITIONAL[key]
        else:
            favourable_regions = independent_regions(key)
            given_regions = range(4)

        people = [
            region
            for region, count in enumerate(counts)
            for _ in range(count)
        ]
        eligible = [
            region for region in people
            if region in given_regions
        ]
        require(eligible, "Empty conditional population")

        successful = sum(
            region in favourable_regions for region in eligible
        )
        expected = Fraction(successful, len(eligible))

        require(
            question.answer["kind"] == "rational"
            and question.answer["value"] == rational_text(expected),
            "Independent Venn probability check failed",
        )
        require(
            question.answer_display.text == rational_text(expected)
            and question.answer_display.math_tex == rational_tex(expected),
            "Independent Venn answer display disagrees",
        )
        return True