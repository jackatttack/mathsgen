"""Venn shading and notation, using the four-region renderer.

Region order: A only, A and B, B only, neither.
"""
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)
from .venn_diagrams import venn_asset


INFO = GeneratorInfo(
    id="probability.venn.notation",
    version=1,
    topic="probability",
    subtopic="venn_diagrams",
    title="Venn diagrams: shading and notation",
    difficulty_descriptions={
        1: "Shade a set or its complement.",
        2: "Shade intersections, unions and exclusive regions.",
        3: "Shade combined regions and complements.",
        4: "Write set notation for a shaded region.",
    },
    tags=("probability", "venn", "sets", "notation", "shading"),
)


# Key -> (plain text, PDF maths, region indices).
NOTATION = {
    "A": ("A", "A", (0, 1)),
    "B": ("B", "B", (1, 2)),
    "not_A": ("A'", r"A^{\prime}", (2, 3)),
    "not_B": ("B'", r"B^{\prime}", (0, 3)),
    "both": ("A intersection B", r"A\cap B", (1,)),
    "either": ("A union B", r"A\cup B", (0, 1, 2)),
    "A_only": ("A intersection B'", r"A\cap B^{\prime}", (0,)),
    "B_only": ("A' intersection B", r"A^{\prime}\cap B", (2,)),
    "neither": (
        "(A union B)'", r"(A\cup B)^{\prime}", (3,),
    ),
    "not_both": (
        "(A intersection B)'", r"(A\cap B)^{\prime}", (0, 2, 3),
    ),
    "not_A_or_B": (
        "A' union B", r"A^{\prime}\cup B", (1, 2, 3),
    ),
    "A_or_not_B": (
        "A union B'", r"A\cup B^{\prime}", (0, 1, 3),
    ),
    "exactly_one": (
        "(A intersection B') union (A' intersection B)",
        r"(A\cap B^{\prime})\cup(A^{\prime}\cap B)",
        (0, 2),
    ),
    "both_or_neither": (
        "(A intersection B) union (A' intersection B')",
        r"(A\cap B)\cup(A^{\prime}\cap B^{\prime})",
        (1, 3),
    ),
}

LEVEL_KEYS = {
    1: ("A", "B", "not_A", "not_B"),
    2: ("both", "either", "A_only", "B_only"),
    3: (
        "neither", "not_both", "not_A_or_B",
        "A_or_not_B", "exactly_one", "both_or_neither",
    ),
    4: tuple(NOTATION),
}


def independent_regions(key):
    """Compute membership using set algebra, not stored region indices."""
    universal = {0, 1, 2, 3}
    a = {0, 1}
    b = {1, 2}

    expressions = {
        "A": a,
        "B": b,
        "not_A": universal - a,
        "not_B": universal - b,
        "both": a & b,
        "either": a | b,
        "A_only": a - b,
        "B_only": b - a,
        "neither": universal - (a | b),
        "not_both": universal - (a & b),
        "not_A_or_B": (universal - a) | b,
        "A_or_not_B": a | (universal - b),
        "exactly_one": (a - b) | (b - a),
        "both_or_neither": (a & b) | (universal - (a | b)),
    }
    return sorted(expressions[key])


def prompt_for(parameters):
    key = parameters["key"]
    plain, tex, _ = NOTATION[key]

    if parameters["direction"] == "shade":
        return Content(
            "Shade the region represented by " + plain + ".",
            tex,
            display_text="Shade the region represented by:",
        )

    return Content(
        "Write one set expression for the shaded region. "
        "Use A, B and any necessary union, intersection or complement symbols."
    )


def answer_for(parameters):
    key = parameters["key"]
    direction = parameters["direction"]
    plain, tex, regions = NOTATION[key]

    if direction == "shade":
        return (
            {"kind": "regions", "value": list(regions)},
            Content("Correct shading shown on the answer diagram."),
        )

    return (
        {
            "kind": "set_notation",
            "value": key,
            "regions": list(regions),
        },
        Content(plain, tex),
    )


def diagrams_for(parameters):
    regions = NOTATION[parameters["key"]][2]
    shaded = venn_asset(shaded=regions)

    if parameters["direction"] == "name":
        return shaded, shaded

    return venn_asset(), shaded


class VennNotation:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")

        direction = "name" if difficulty == 4 else "shade"
        key = context.rng.choice(LEVEL_KEYS[difficulty])
        parameters = {"direction": direction, "key": key}

        answer, answer_display = answer_for(parameters)
        student, teacher = diagrams_for(parameters)

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
            marks=1 if difficulty <= 2 else 2,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=1),
            parameters=parameters,
            question_visuals=(student,),
            answer_visuals=(teacher,),
        )

        self.validate(question)
        return question

    def validate(self, question):
        require(
            question.generator_id == self.info.id
            and question.generator_version == self.info.version,
            "Generator identity mismatch",
        )
        level = question.difficulty
        require(
            type(level) is int and level in LEVEL_KEYS,
            "Invalid difficulty",
        )
        require(question.settings == {}, "Unsupported settings")

        parameters = question.parameters
        require(
            type(parameters) is dict
            and set(parameters) == {"direction", "key"},
            "Invalid notation parameters",
        )

        direction = "name" if level == 4 else "shade"
        require(
            parameters["direction"] == direction,
            "Incorrect question direction",
        )
        require(
            parameters["key"] in LEVEL_KEYS[level],
            "Notation is outside its difficulty level",
        )

        answer, display = answer_for(parameters)
        student, teacher = diagrams_for(parameters)

        require(question.answer == answer, "Incorrect region answer")
        require(question.answer_display == display, "Incorrect answer display")
        require(question.prompt == prompt_for(parameters), "Incorrect prompt")
        require(
            question.visual_assets("questions") == (student,),
            "Incorrect student diagram",
        )
        require(
            question.visual_assets("answers") == (teacher,),
            "Incorrect answer diagram",
        )
        return True

    def validate_independently(self, question):
        key = question.parameters["key"]
        actual = independent_regions(key)
        require(
            list(NOTATION[key][2]) == actual,
            "Stored region selection disagrees with set algebra",
        )

        answer = question.answer
        selected = (
            answer["regions"]
            if question.parameters["direction"] == "name"
            else answer["value"]
        )
        require(selected == actual, "Answer disagrees with set algebra")

        student = question.visual_assets("questions")[0]
        teacher = question.visual_assets("answers")[0]

        require(
            teacher["shaded"] == actual,
            "Teacher shading disagrees with set algebra",
        )
        require(
            student["shaded"] == (
                actual if question.parameters["direction"] == "name" else []
            ),
            "Student shading disagrees with question direction",
        )
        return True