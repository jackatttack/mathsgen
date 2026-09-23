"""Complete two-set Venn diagrams from sufficient frequency information.

Region order: A only, both, B only, neither.

Questions are generated from a complete positive-integer region model.
An independent Fraction-based linear solver reconstructs all four regions
using only the clues shown to the student, and checks uniqueness.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .venn_diagrams import venn_asset


INFO = GeneratorInfo(
    id="probability.venn.completion",
    version=1,
    topic="probability",
    subtopic="venn_diagrams",
    title="Venn diagrams: missing values and problem solving",
    difficulty_descriptions={
        1: "Find one missing region using the universal-set total.",
        2: "Complete all four regions using set totals and one known region.",
        3: "Complete all regions from indirect information about exactly one or at least one set.",
        4: "Reconstruct the diagram from a conditional probability, then find a reverse conditional probability.",
    },
    tags=(
        "probability", "venn", "missing_values", "sets",
        "problem_solving", "conditional_probability",
    ),
)

REGION_NAMES = (
    "A only", "both A and B", "B only", "neither",
)

VARIANTS = {
    1: ("missing_0", "missing_1", "missing_2", "missing_3"),
    2: ("both", "neither"),
    3: ("exactly_one", "union"),
    4: ("given_A", "given_B"),
}

# All equations use the variable order [A only, both, B only, neither].
COEFFICIENTS = {
    "total": (1, 1, 1, 1),
    "A": (1, 1, 0, 0),
    "B": (0, 1, 1, 0),
    "both": (0, 1, 0, 0),
    "neither": (0, 0, 0, 1),
    "exactly_one": (1, 0, 1, 0),
    "union": (1, 1, 1, 0),
    "region_0": (1, 0, 0, 0),
    "region_1": (0, 1, 0, 0),
    "region_2": (0, 0, 1, 0),
    "region_3": (0, 0, 0, 1),
}


def calculate_clues(counts, level, variant):
    """Create the information that will actually appear in the question."""
    a_only, both, b_only, neither = counts
    total = sum(counts)
    a_total = a_only + both
    b_total = both + b_only

    if level == 1:
        missing = int(variant[-1])
        clues = {"total": total}
        for index, value in enumerate(counts):
            if index != missing:
                clues["region_" + str(index)] = value
        return clues

    clues = {
        "total": total,
        "A": a_total,
        "B": b_total,
    }

    if level == 2:
        clues[variant] = both if variant == "both" else neither

    elif level == 3:
        clues[variant] = (
            a_only + b_only
            if variant == "exactly_one"
            else a_only + both + b_only
        )

    elif level == 4:
        if variant == "given_A":
            clues["conditional"] = rational_text(Fraction(both, a_total))
        else:
            clues["conditional"] = rational_text(Fraction(both, b_total))

    return clues


def rows_from_clues(clues, variant):
    """Convert student-facing information into exact linear equations."""
    rows = []

    for name, value in clues.items():
        if name == "conditional":
            ratio = Fraction(value)
            require(0 < ratio < 1, "Conditional clue must be nontrivial")
            if variant == "given_A":
                # both / (A only + both) = ratio
                coefficients = (-ratio, 1 - ratio, 0, 0)
            else:
                # both / (both + B only) = ratio
                coefficients = (0, 1 - ratio, -ratio, 0)
            rows.append((coefficients, Fraction(0)))
        else:
            require(name in COEFFICIENTS, "Unknown Venn clue")
            rows.append((COEFFICIENTS[name], Fraction(value)))

    return rows


def solve_unique(rows):
    """Solve the supplied four-region system by exact Gaussian elimination.

    Return None unless there is exactly one solution. Generation does not
    call this function; it exists to audit the resulting student question.
    """
    require(len(rows) >= 4, "Insufficient Venn equations")
    matrix = [
        [Fraction(value) for value in coefficients] + [Fraction(rhs)]
        for coefficients, rhs in rows
    ]
    require(
        all(len(row) == 5 for row in matrix),
        "Expected four Venn variables",
    )

    pivot_columns = []
    pivot_row = 0

    for column in range(4):
        candidate = next(
            (
                index for index in range(pivot_row, len(matrix))
                if matrix[index][column] != 0
            ),
            None,
        )
        if candidate is None:
            continue

        matrix[pivot_row], matrix[candidate] = (
            matrix[candidate], matrix[pivot_row]
        )
        pivot = matrix[pivot_row][column]
        matrix[pivot_row] = [
            value / pivot for value in matrix[pivot_row]
        ]

        for index in range(len(matrix)):
            if index == pivot_row:
                continue
            multiplier = matrix[index][column]
            if multiplier:
                matrix[index] = [
                    value - multiplier * leading
                    for value, leading in zip(
                        matrix[index], matrix[pivot_row]
                    )
                ]

        pivot_columns.append(column)
        pivot_row += 1

    require(
        all(
            any(row[column] != 0 for column in range(4))
            or row[4] == 0
            for row in matrix
        ),
        "Inconsistent Venn clues",
    )
    require(
        len(pivot_columns) == 4,
        "Venn clues do not determine all four regions uniquely",
    )

    result = [Fraction(0)] * 4
    for index, column in enumerate(pivot_columns):
        result[column] = matrix[index][4]

    require(
        all(value.denominator == 1 and value >= 0 for value in result),
        "Venn clues do not give nonnegative integer frequencies",
    )
    return [int(value) for value in result]


def conditional_result(counts, variant):
    a_only, both, b_only, _ = counts
    if variant == "given_A":
        # A reverse question: given B, find P(A).
        return Fraction(both, both + b_only)
    # Given A, find P(B).
    return Fraction(both, a_only + both)


def prompt_for(parameters):
    level = parameters["level"]
    variant = parameters["variant"]
    clues = parameters["clues"]

    if level == 1:
        return Content(
            "The Venn diagram shows {} people altogether. "
            "Complete the missing region.".format(clues["total"])
        )

    text = (
        "A group contains {} people. "
        "{} belong to A and {} belong to B. "
    ).format(clues["total"], clues["A"], clues["B"])

    if level == 2:
        if variant == "both":
            text += "{} belong to both A and B. ".format(clues["both"])
        else:
            text += "{} belong to neither A nor B. ".format(
                clues["neither"]
            )

    elif level == 3:
        if variant == "exactly_one":
            text += (
                "{} belong to exactly one of A or B. "
            ).format(clues["exactly_one"])
        else:
            text += (
                "{} belong to at least one of A or B. "
            ).format(clues["union"])

    elif level == 4:
        if variant == "given_A":
            text += (
                "Of those who belong to A, the probability that a "
                "randomly selected person also belongs to B is {}. "
            ).format(clues["conditional"])
        else:
            text += (
                "Of those who belong to B, the probability that a "
                "randomly selected person also belongs to A is {}. "
            ).format(clues["conditional"])

    text += "Complete all four regions of the Venn diagram."

    if level == 4:
        if variant == "given_A":
            text += (
                " Given that a person belongs to B, find the "
                "probability that they also belong to A."
            )
        else:
            text += (
                " Given that a person belongs to A, find the "
                "probability that they also belong to B."
            )
        text += " Give the probability as a fraction in simplest form."

    return Content(text)


def answer_for(parameters):
    counts = parameters["counts"]
    variant = parameters["variant"]
    level = parameters["level"]

    answer = {
        "kind": "venn_completion",
        "regions": list(counts),
    }

    display = (
        "A only = {}; both = {}; B only = {}; neither = {}."
    ).format(*counts)

    if level == 4:
        probability = conditional_result(counts, variant)
        answer["conditional"] = rational_text(probability)
        display += " Reverse conditional probability = {}.".format(
            rational_text(probability)
        )

    return answer, Content(display)


def diagrams_for(parameters):
    counts = parameters["counts"]
    level = parameters["level"]
    variant = parameters["variant"]

    if level == 1:
        missing = (int(variant[-1]),)
    else:
        missing = (0, 1, 2, 3)

    return (
        venn_asset(values=counts, missing=missing),
        venn_asset(values=counts),
    )


class VennCompletion:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")

        rng = context.rng
        counts = [rng.randint(2, 12) for _ in range(4)]
        variant = rng.choice(VARIANTS[difficulty])

        parameters = {
            "level": difficulty,
            "variant": variant,
            "counts": counts,
            "clues": calculate_clues(counts, difficulty, variant),
        }

        answer, display = answer_for(parameters)
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
            answer_display=display,
            worked_solution=(),
            marks={1: 1, 2: 4, 3: 5, 4: 6}[difficulty],
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=2 if difficulty < 4 else 4),
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
            "Venn completion generator/version mismatch",
        )
        level = question.difficulty
        require(
            type(level) is int and level in VARIANTS,
            "Invalid completion difficulty",
        )
        require(question.settings == {}, "Unsupported settings")

        parameters = question.parameters
        require(
            type(parameters) is dict
            and set(parameters) == {"level", "variant", "counts", "clues"},
            "Incorrect completion parameters",
        )
        require(parameters["level"] == level, "Incorrect parameter level")
        variant = parameters["variant"]
        require(
            variant in VARIANTS[level],
            "Completion variant outside its difficulty",
        )

        counts = parameters["counts"]
        require(
            isinstance(counts, list)
            and len(counts) == 4
            and all(type(value) is int and 2 <= value <= 12
                    for value in counts),
            "Invalid generated Venn counts",
        )

        require(
            parameters["clues"] == calculate_clues(counts, level, variant),
            "Clues disagree with the generated regions",
        )

        answer, display = answer_for(parameters)
        student, teacher = diagrams_for(parameters)

        require(question.answer == answer, "Incorrect completion answer")
        require(
            question.answer_display == display,
            "Incorrect completion answer display",
        )
        require(
            question.prompt == prompt_for(parameters),
            "Incorrect completion question wording",
        )
        require(
            question.visual_assets("questions") == (student,)
            and question.visual_assets("answers") == (teacher,),
            "Completion diagram disagrees with its answer",
        )
        return True

    def validate_independently(self, question):
        """Reconstruct the full diagram using only student-facing clues."""
        parameters = question.parameters
        clues = parameters["clues"]
        level = question.difficulty
        variant = parameters["variant"]

        reconstructed = solve_unique(rows_from_clues(clues, variant))

        require(
            reconstructed == parameters["counts"],
            "Student clues reconstruct a different Venn diagram",
        )
        require(
            reconstructed == question.answer["regions"],
            "Answer regions disagree with independently solved clues",
        )

        student = question.visual_assets("questions")[0]
        teacher = question.visual_assets("answers")[0]

        require(
            teacher["values"] == reconstructed
            and student["values"] == reconstructed,
            "Diagram values disagree with independently solved clues",
        )

        expected_missing = (
            [int(variant[-1])]
            if level == 1 else [0, 1, 2, 3]
        )
        require(
            student["missing"] == expected_missing
            and teacher["missing"] == [],
            "Missing region presentation is incorrect",
        )

        if level == 4:
            a_only, both, b_only, _ = reconstructed

            # Independent event counting within the group in the question.
            if variant == "given_A":
                eligible = ["A_only"] * a_only + ["both"] * both
                reverse_group = (
                    ["both"] * both + ["B_only"] * b_only
                )
            else:
                eligible = ["both"] * both + ["B_only"] * b_only
                reverse_group = (
                    ["A_only"] * a_only + ["both"] * both
                )

            require(eligible and reverse_group, "Empty conditional group")
            given = Fraction(
                eligible.count("both"), len(eligible)
            )
            reverse = Fraction(
                reverse_group.count("both"), len(reverse_group)
            )

            require(
                given == Fraction(clues["conditional"]),
                "Conditional clue disagrees with enumerated people",
            )
            require(
                question.answer["conditional"] == rational_text(reverse),
                "Reverse conditional probability is incorrect",
            )

        return True