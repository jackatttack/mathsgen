"""Exact translations, inverse construction and displacement identification."""
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)


INFO = GeneratorInfo(
    id="geometry.transformations.translation",
    version=2,
    topic="geometry",
    subtopic="transformations",
    title="Translations on coordinate grids",
    difficulty_descriptions={
        1: "Draw a horizontal or vertical translation.",
        2: "Draw a translation with horizontal and vertical components.",
        3: "Recover the original triangle from its translated image.",
        4: "Identify the horizontal and vertical displacement between shapes.",
    },
    tags=("geometry", "transformations", "translation", "coordinates"),
)


def displacement_text(vector):
    parts = []
    horizontal, vertical = vector
    if horizontal:
        parts.append("{} units {}".format(
            abs(horizontal), "right" if horizontal > 0 else "left",
        ))
    if vertical:
        parts.append("{} units {}".format(
            abs(vertical), "up" if vertical > 0 else "down",
        ))
    return " and ".join(parts)


def points_text(vertices):
    return ", ".join("({}, {})".format(*point) for point in vertices)


def translate(vertices, vector):
    return [[x + vector[0], y + vector[1]] for x, y in vertices]


def separated(first, second):
    return any(
        max(point[axis] for point in first) < min(point[axis] for point in second)
        or max(point[axis] for point in second) < min(point[axis] for point in first)
        for axis in (0, 1)
    )


def plot_for(parameters, level, teacher):
    if level == 3:
        given, result = parameters["image"], parameters["object"]
    else:
        given, result = parameters["object"], parameters["image"]
    curves = [{"segments": [given + [given[0]]], "dashed": False}]
    if teacher or level == 4:
        curves.append({"segments": [result + [result[0]]], "dashed": True})
    return {
        "kind": "plot", "version": 1,
        "x_range": [-10, 10], "y_range": [-10, 10],
        "x_step": 2, "y_step": 2, "minor_divisions": 2,
        "equal_units": True, "curves": curves, "points": [],
        "x_label": "x", "y_label": "y",
    }


def presentation(parameters, level):
    displacement = displacement_text(parameters["vector"])
    if level == 4:
        lead = (
            "Describe fully the translation that maps the solid triangle "
            "onto the dashed triangle. State how far it moves horizontally "
            "and vertically, including the directions."
        )
    elif level == 3:
        lead = (
            "A triangle is translated {} to produce the solid triangle shown. "
            "Draw the original triangle on the grid."
        ).format(displacement)
    else:
        lead = (
            "Translate the solid triangle {}. Draw the image on the grid."
        ).format(displacement)
    if level == 3:
        fallback = (
            " Image vertices, in boundary order: "
            + points_text(parameters["image"]) + "."
        )
    else:
        fallback = (
            " Object vertices, in boundary order: "
            + points_text(parameters["object"]) + "."
        )
        if level == 4:
            fallback += (
                " Corresponding image vertices: "
                + points_text(parameters["image"]) + "."
            )
    return Content(lead + fallback, display_text=lead)


def answer_for(parameters, level):
    if level == 4:
        return (
            {"kind": "translation", "vector": parameters["vector"][:]},
            Content("Translation: " + displacement_text(parameters["vector"]) + "."),
        )
    original = level == 3
    vertices = parameters["object" if original else "image"]
    return (
        {
            "kind": "polygon_vertices",
            "vertices": [point[:] for point in vertices],
        },
        Content(
            ("Original" if original else "Image")
            + " vertices: " + points_text(vertices)
            + ". The required triangle is dashed in the answer graph."
        ),
    )


class Translations:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        components = (-7, -6, -5, -4, -3, -2, 2, 3, 4, 5, 6, 7)
        if difficulty == 1:
            vector = [rng.choice(components), 0]
            if rng.choice((False, True)):
                vector.reverse()
        else:
            vector = [rng.choice(components), rng.choice(components)]

        # At least one triangle dimension must be smaller than the movement
        # on that axis. This guarantees that separated placement is possible,
        # including a two-unit horizontal or vertical translation.
        leg_pairs = [
            (horizontal, vertical)
            for horizontal in (1, 2, 3, 4)
            for vertical in (1, 2, 3, 4)
            if horizontal != vertical
            and (
                horizontal < abs(vector[0])
                or vertical < abs(vector[1])
            )
        ]
        require(bool(leg_pairs), "No triangle dimensions fit this displacement")
        for attempt in range(500):
            x, y = rng.randint(-7, 7), rng.randint(-7, 7)
            horizontal, vertical = rng.choice(leg_pairs)
            horizontal *= rng.choice((-1, 1))
            vertical *= rng.choice((-1, 1))
            vertices = [[x, y], [x + horizontal, y], [x, y + vertical]]
            image = translate(vertices, vector)
            if (
                all(-9 <= value <= 9 for point in vertices + image for value in point)
                and separated(vertices, image)
            ):
                break
        else:
            raise ValueError("Could not construct a readable translation")

        parameters = {"vector": vector, "object": vertices, "image": image}
        answer, display = answer_for(parameters, difficulty)
        question = Question(
            id=context.identity,
            generator_id=self.info.id, generator_version=self.info.version,
            topic=self.info.topic, subtopic=self.info.subtopic,
            difficulty=difficulty, seed=seed, settings=context.settings,
            prompt=presentation(parameters, difficulty),
            answer=answer, answer_display=display, worked_solution=(),
            marks=2, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=0),
            parameters=parameters,
            question_visuals=(plot_for(parameters, difficulty, False),),
            answer_visuals=(plot_for(parameters, difficulty, True),),
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")
        parameters = question.parameters
        require(set(parameters) == {"vector", "object", "image"}, "Unexpected parameters")
        vector = parameters["vector"]
        require(
            isinstance(vector, list) and len(vector) == 2
            and all(
                type(value) is int and (value == 0 or 2 <= abs(value) <= 7)
                for value in vector
            ),
            "Invalid translation vector",
        )
        require(
            sum(value != 0 for value in vector) == (1 if level == 1 else 2),
            "Wrong displacement structure for level",
        )
        for name in ("object", "image"):
            vertices = parameters[name]
            require(
                isinstance(vertices, list) and len(vertices) == 3
                and all(
                    isinstance(point, list) and len(point) == 2
                    and all(type(value) is int and -9 <= value <= 9 for value in point)
                    for point in vertices
                ),
                "Invalid triangle or grid margin",
            )
        source = parameters["object"]
        horizontal = source[1][0] - source[0][0]
        vertical = source[2][1] - source[0][1]
        require(
            source[1][1] == source[0][1] and source[2][0] == source[0][0]
            and abs(horizontal) in (1, 2, 3, 4) and abs(vertical) in (1, 2, 3, 4)
            and abs(horizontal) != abs(vertical),
            "Expected a scalene right triangle",
        )
        require(parameters["image"] == translate(source, vector), "Incorrect image")
        require(separated(source, parameters["image"]), "Triangles overlap")
        answer, display = answer_for(parameters, level)
        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Answer display mismatch")
        require(question.prompt == presentation(parameters, level), "Prompt mismatch")
        require(
            question.visual_assets("questions") == (plot_for(parameters, level, False),),
            "Student graph mismatch",
        )
        require(
            question.visual_assets("answers") == (plot_for(parameters, level, True),),
            "Answer graph mismatch",
        )
        return True

    def validate_independently(self, question):
        """Recover displacement from corresponding vertices, including inverse tasks."""
        parameters = question.parameters
        level = question.difficulty
        if level == 4:
            require(question.answer.get("kind") == "translation", "Wrong answer kind")
            vector = question.answer["vector"]
            source, image = parameters["object"], parameters["image"]
        else:
            require(question.answer.get("kind") == "polygon_vertices", "Wrong answer kind")
            vector = parameters["vector"]
            if level == 3:
                source, image = question.answer["vertices"], parameters["image"]
            else:
                source, image = parameters["object"], question.answer["vertices"]
        require(
            isinstance(vector, list) and len(vector) == 2
            and all(type(value) is int for value in vector),
            "Invalid vector answer",
        )
        for vertices in (source, image):
            require(
                isinstance(vertices, list) and len(vertices) == 3
                and all(
                    isinstance(point, list) and len(point) == 2
                    and all(type(value) is int for value in point)
                    for point in vertices
                ),
                "Invalid vertex answer",
            )
        recovered = {
            (target[0] - original[0], target[1] - original[1])
            for original, target in zip(source, image)
        }
        require(recovered == {tuple(vector)}, "Displacements disagree")
        for first, second in ((0, 1), (1, 2), (2, 0)):
            require(
                [image[second][axis] - image[first][axis] for axis in (0, 1)]
                == [source[second][axis] - source[first][axis] for axis in (0, 1)],
                "Translation changed an edge vector",
            )
        return True