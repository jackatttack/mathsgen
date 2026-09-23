"""Ordered transformations with independent affine-matrix verification."""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)
from .reflections import reflect, line_text
from .rotations import rotate, rotation_text
from .translations import translate, displacement_text, points_text, separated


INFO = GeneratorInfo(
    id="geometry.transformations.combined",
    version=1,
    topic="geometry",
    subtopic="transformations",
    title="Combined transformations",
    difficulty_descriptions={
        1: "Apply two successive translations.",
        2: "Apply a reflection and a translation in the stated order.",
        3: "Apply a rotation followed by a reflection or translation.",
        4: "Compare two transformations applied in opposite orders.",
    },
    tags=("geometry", "transformations", "combined", "order", "coordinates"),
)


def operation_text(operation):
    kind, data = operation["kind"], operation["data"]
    if kind == "translation":
        return "translate " + displacement_text(data)
    if kind == "reflection":
        return "reflect in the line " + line_text(data)
    return "rotate " + rotation_text(data)


def apply_operation(vertices, operation):
    functions = {
        "translation": translate,
        "reflection": reflect,
        "rotation": rotate,
    }
    return functions[operation["kind"]](vertices, operation["data"])


def make_operation(rng, kind):
    if kind == "translation":
        data = [rng.choice((-4, -3, -2, 2, 3, 4)) for axis in (0, 1)]
    elif kind == "reflection":
        data = rng.choice(
            [{"axis": axis, "offset": offset}
             for axis in ("x", "y") for offset in (-2, -1, 0, 1, 2)]
            + [{"axis": "diagonal", "offset": slope} for slope in (-1, 1)]
        )
    else:
        data = {
            "centre": [rng.randint(-2, 2), rng.randint(-2, 2)],
            "turns": rng.choice((1, 2, 3)),
        }
    return {"kind": kind, "data": data}


def check_operation(operation):
    require(
        isinstance(operation, dict) and set(operation) == {"kind", "data"},
        "Invalid operation",
    )
    kind, data = operation["kind"], operation["data"]
    require(kind in ("translation", "reflection", "rotation"), "Unknown operation")
    if kind == "translation":
        require(
            isinstance(data, list) and len(data) == 2
            and all(type(value) is int and value in (-4, -3, -2, 2, 3, 4)
                    for value in data),
            "Invalid displacement",
        )
    elif kind == "reflection":
        require(
            isinstance(data, dict) and set(data) == {"axis", "offset"}
            and type(data["offset"]) is int,
            "Invalid mirror line",
        )
        require(
            (data["axis"] in ("x", "y") and -2 <= data["offset"] <= 2)
            or (data["axis"] == "diagonal" and data["offset"] in (-1, 1)),
            "Unsupported mirror line",
        )
    else:
        require(
            isinstance(data, dict) and set(data) == {"centre", "turns"}
            and type(data["turns"]) is int and data["turns"] in (1, 2, 3),
            "Invalid rotation",
        )
        require(
            isinstance(data["centre"], list) and len(data["centre"]) == 2
            and all(type(value) is int and -2 <= value <= 2 for value in data["centre"]),
            "Invalid rotation centre",
        )


def states_for(vertices, operations):
    middle = apply_operation(vertices, operations[0])
    final = apply_operation(middle, operations[1])
    return middle, final


def plot_for(parameters, teacher):
    source = parameters["object"]
    curves = [{"segments": [source + [source[0]]], "dashed": False}]
    if teacher:
        final = parameters["final"]
        curves.append({"segments": [final + [final[0]]], "dashed": True})
    return {
        "kind": "plot", "version": 1,
        "x_range": [-10, 10], "y_range": [-10, 10],
        "x_step": 2, "y_step": 2, "minor_divisions": 2,
        "equal_units": True, "curves": curves, "points": [],
        "x_label": "x", "y_label": "y",
    }


def presentation(parameters, level):
    first, second = parameters["operations"]
    lead = (
        "Start with the solid triangle. First, {}. Then, {}. "
        "Draw the final image on the grid."
    ).format(operation_text(first), operation_text(second))
    if level == 4:
        lead += (
            " Now start again with the original triangle and apply the two "
            "transformations in the reverse order. Give the final vertex "
            "coordinates for this reverse order. Does changing the order "
            "give the same final triangle?"
        )
    return Content(
        lead + " Original vertices, in boundary order: "
        + points_text(parameters["object"]) + ".",
        display_text=lead,
    )


def answer_for(parameters, level):
    answer = {
        "kind": "combined_transformation",
        "intermediate": [point[:] for point in parameters["intermediate"]],
        "final": [point[:] for point in parameters["final"]],
    }
    text = (
        "After the first transformation: "
        + points_text(parameters["intermediate"])
        + ". Final vertices: " + points_text(parameters["final"])
        + ". The final image for the stated order is dashed in the answer graph."
    )
    if level == 4:
        answer["reverse_intermediate"] = [
            point[:] for point in parameters["reverse_intermediate"]
        ]
        answer["reverse_final"] = [point[:] for point in parameters["reverse_final"]]
        answer["same"] = False
        text += (
            " Reverse order final vertices: "
            + points_text(parameters["reverse_final"])
            + ". No: changing the order gives a different final triangle."
        )
    return answer, Content(text)


def affine_matrix(operation):
    """Independent homogeneous matrix, derived from geometric definitions."""
    check_operation(operation)
    kind, data = operation["kind"], operation["data"]
    if kind == "translation":
        return [[1, 0, data[0]], [0, 1, data[1]], [0, 0, 1]]
    if kind == "rotation":
        cosine, sine = {1: (0, 1), 2: (-1, 0), 3: (0, -1)}[data["turns"]]
        cx, cy = data["centre"]
        return [
            [cosine, -sine, cx - cosine * cx + sine * cy],
            [sine, cosine, cy - sine * cx - cosine * cy],
            [0, 0, 1],
        ]
    # Reflection in a*x+b*y=c: subtract twice the signed normal projection.
    if data["axis"] == "x":
        a, b, c = 1, 0, data["offset"]
    elif data["axis"] == "y":
        a, b, c = 0, 1, data["offset"]
    else:
        a, b, c = -data["offset"], 1, 0
    scale = Fraction(2, a * a + b * b)
    return [
        [1 - scale * a * a, -scale * a * b, scale * a * c],
        [-scale * a * b, 1 - scale * b * b, scale * b * c],
        [0, 0, 1],
    ]


def matrix_product(left, right):
    return [
        [sum(left[row][k] * right[k][column] for k in range(3))
         for column in range(3)]
        for row in range(3)
    ]


def matrix_image(matrix, vertices):
    return [
        [sum(matrix[row][k] * (point + [1])[k] for k in range(3))
         for row in range(2)]
        for point in vertices
    ]


class CombinedTransformations:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        for attempt in range(2000):
            if difficulty == 1:
                kinds = ["translation", "translation"]
            elif difficulty == 2:
                kinds = ["reflection", "translation"]
                rng.shuffle(kinds)
            elif difficulty == 3:
                kinds = ["rotation", rng.choice(("reflection", "translation"))]
            else:
                kinds = [rng.choice(("reflection", "rotation")), "translation"]
                rng.shuffle(kinds)
            operations = [make_operation(rng, kind) for kind in kinds]
            x, y = rng.randint(-6, 6), rng.randint(-6, 6)
            horizontal, vertical = rng.sample((2, 3, 4), 2)
            horizontal *= rng.choice((-1, 1))
            vertical *= rng.choice((-1, 1))
            source = [[x, y], [x + horizontal, y], [x, y + vertical]]
            middle, final = states_for(source, operations)
            parameters = {
                "object": source, "operations": operations,
                "intermediate": middle, "final": final,
            }
            shapes = [source, middle, final]
            if difficulty == 4:
                reverse_middle, reverse_final = states_for(source, operations[::-1])
                parameters["reverse_intermediate"] = reverse_middle
                parameters["reverse_final"] = reverse_final
                shapes += [reverse_middle, reverse_final]
                if not separated(final, reverse_final):
                    continue
            if not all(
                -9 <= value <= 9
                for shape in shapes for point in shape for value in point
            ):
                continue
            if not separated(source, final):
                continue
            if middle == source or final == middle:
                continue
            break
        else:
            raise ValueError("Could not construct bounded combined transformations")

        answer, display = answer_for(parameters, difficulty)
        question = Question(
            id=context.identity,
            generator_id=self.info.id, generator_version=self.info.version,
            topic=self.info.topic, subtopic=self.info.subtopic,
            difficulty=difficulty, seed=seed, settings=context.settings,
            prompt=presentation(parameters, difficulty),
            answer=answer, answer_display=display, worked_solution=(),
            marks=5 if difficulty == 4 else 3, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=2 if difficulty == 4 else 0),
            parameters=parameters,
            question_visuals=(plot_for(parameters, False),),
            answer_visuals=(plot_for(parameters, True),),
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")
        p = question.parameters
        shape_names = ["object", "intermediate", "final"]
        if level == 4:
            shape_names += ["reverse_intermediate", "reverse_final"]
        require(set(p) == set(shape_names + ["operations"]), "Unexpected parameters")
        operations = p["operations"]
        require(isinstance(operations, list) and len(operations) == 2, "Need two operations")
        for operation in operations:
            check_operation(operation)
        kinds = [operation["kind"] for operation in operations]
        if level == 1:
            require(kinds == ["translation", "translation"], "Wrong level 1 structure")
        elif level == 2:
            require(sorted(kinds) == ["reflection", "translation"], "Wrong level 2 structure")
        elif level == 3:
            require(
                kinds[0] == "rotation" and kinds[1] in ("reflection", "translation"),
                "Wrong level 3 structure",
            )
        else:
            require(
                kinds.count("translation") == 1
                and any(kind in ("reflection", "rotation") for kind in kinds),
                "Wrong level 4 structure",
            )
        for name in shape_names:
            vertices = p[name]
            require(
                isinstance(vertices, list) and len(vertices) == 3
                and all(
                    isinstance(point, list) and len(point) == 2
                    and all(type(value) is int and -9 <= value <= 9 for value in point)
                    for point in vertices
                ),
                "Invalid triangle or insufficient grid margin",
            )
        source = p["object"]
        horizontal = source[1][0] - source[0][0]
        vertical = source[2][1] - source[0][1]
        require(
            source[1][1] == source[0][1] and source[2][0] == source[0][0]
            and abs(horizontal) in (2, 3, 4) and abs(vertical) in (2, 3, 4)
            and abs(horizontal) != abs(vertical),
            "Expected a scalene right triangle",
        )
        require(
            states_for(source, operations) == (p["intermediate"], p["final"]),
            "Incorrect transformation sequence",
        )
        require(separated(source, p["final"]), "Original and final overlap")
        require(
            p["intermediate"] != source and p["final"] != p["intermediate"],
            "An operation leaves the triangle unchanged",
        )
        if level == 4:
            require(
                states_for(source, operations[::-1])
                == (p["reverse_intermediate"], p["reverse_final"]),
                "Incorrect reverse sequence",
            )
            require(separated(p["final"], p["reverse_final"]), "Order must change the result")
        answer, display = answer_for(p, level)
        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Answer display mismatch")
        require(question.prompt == presentation(p, level), "Prompt mismatch")
        require(question.visual_assets("questions") == (plot_for(p, False),), "Student graph mismatch")
        require(question.visual_assets("answers") == (plot_for(p, True),), "Answer graph mismatch")
        return True

    def validate_independently(self, question):
        """Compose affine matrices directly, independently of sequential geometry."""
        p, answer = question.parameters, question.answer
        require(answer.get("kind") == "combined_transformation", "Wrong answer kind")
        first, second = [affine_matrix(operation) for operation in p["operations"]]
        expected = {
            "intermediate": matrix_image(first, p["object"]),
            "final": matrix_image(matrix_product(second, first), p["object"]),
        }
        if question.difficulty == 4:
            expected["reverse_intermediate"] = matrix_image(second, p["object"])
            expected["reverse_final"] = matrix_image(matrix_product(first, second), p["object"])
            same = {tuple(point) for point in expected["final"]} == {
                tuple(point) for point in expected["reverse_final"]
            }
            require(not same and answer.get("same") is False, "Incorrect order comparison")
        for name, vertices in expected.items():
            require(p[name] == vertices, "Stored geometry disagrees with affine check")
            require(answer.get(name) == vertices, "Answer disagrees with affine check")
        return True