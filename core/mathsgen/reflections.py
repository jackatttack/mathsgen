"""Reflection construction and identification with exact integer geometry."""
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)


INFO = GeneratorInfo(
    id="geometry.transformations.reflection",
    version=1,
    topic="geometry",
    subtopic="transformations",
    title="Reflections on coordinate grids",
    difficulty_descriptions={
        1: "Reflect a triangle in the x-axis or y-axis.",
        2: "Reflect a triangle in a shifted horizontal or vertical line.",
        3: "Reflect a triangle in y = x or y = -x.",
        4: "Identify the mirror line from an object and its image.",
    },
    tags=("geometry", "transformations", "reflection", "coordinates"),
)


def allowed_lines(level):
    """Represent a mirror line by its equation family and integer constant."""
    axes = [
        {"axis": axis, "offset": 0}
        for axis in ("x", "y")
    ]
    shifted = [
        {"axis": axis, "offset": offset}
        for axis in ("x", "y")
        for offset in (-3, -2, -1, 1, 2, 3)
    ]
    diagonals = [
        {"axis": "diagonal", "offset": slope}
        for slope in (-1, 1)
    ]
    return {
        1: axes,
        2: shifted,
        3: diagonals,
        4: axes + shifted + diagonals,
    }[level]


def line_text(line):
    if line["axis"] == "diagonal":
        return "y = x" if line["offset"] == 1 else "y = -x"
    return "{} = {}".format(line["axis"], line["offset"])


def reflect(vertices, line):
    axis, offset = line["axis"], line["offset"]
    if axis == "x":
        return [[2 * offset - x, y] for x, y in vertices]
    if axis == "y":
        return [[x, 2 * offset - y] for x, y in vertices]
    return [[offset * y, offset * x] for x, y in vertices]


def points_text(vertices):
    return ", ".join("({}, {})".format(x, y) for x, y in vertices)


def double_area(vertices):
    return abs(sum(
        first[0] * second[1] - second[0] * first[1]
        for first, second in zip(vertices, vertices[1:] + vertices[:1])
    ))


def separated(first, second):
    """Keep object and image bounding boxes apart for readable identification."""
    return any(
        max(point[axis] for point in first)
        < min(point[axis] for point in second)
        or max(point[axis] for point in second)
        < min(point[axis] for point in first)
        for axis in (0, 1)
    )


def plot_for(parameters, completed):
    curves = [{
        "segments": [parameters["object"] + [parameters["object"][0]]],
        "dashed": False,
    }]
    if completed:
        curves.append({
            "segments": [parameters["image"] + [parameters["image"][0]]],
            "dashed": True,
        })
    return {
        "kind": "plot",
        "version": 1,
        "x_range": [-10, 10],
        "y_range": [-10, 10],
        "x_step": 2,
        "y_step": 2,
        "minor_divisions": 2,
        "equal_units": True,
        "curves": curves,
        "points": [],
        "x_label": "x",
        "y_label": "y",
    }


def presentation(parameters, level):
    if level == 4:
        lead = (
            "The solid triangle is reflected onto the dashed triangle. "
            "Write the equation of the mirror line."
        )
    else:
        lead = (
            "Reflect the solid triangle in the line {}. "
            "Draw the image on the grid."
        ).format(line_text(parameters["line"]))
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
        line = dict(parameters["line"])
        return (
            {"kind": "mirror_line", "line": line},
            Content("Mirror line: " + line_text(line) + "."),
        )
    return (
        {
            "kind": "polygon_vertices",
            "vertices": [point[:] for point in parameters["image"]],
        },
        Content(
            "Image vertices: " + points_text(parameters["image"])
            + ". The answer graph shows the image dashed."
        ),
    )


class Reflections:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        line = dict(rng.choice(allowed_lines(difficulty)))

        for attempt in range(500):
            x, y = rng.randint(-7, 5), rng.randint(-7, 5)
            horizontal, vertical = rng.sample((2, 3, 4), 2)
            horizontal *= rng.choice((-1, 1))
            vertical *= rng.choice((-1, 1))
            vertices = [
                [x, y], [x + horizontal, y], [x, y + vertical],
            ]
            image = reflect(vertices, line)
            if (
                all(-9 <= value <= 9 for point in vertices + image for value in point)
                and separated(vertices, image)
            ):
                break
        else:
            raise ValueError("Could not construct a readable reflection")

        parameters = {"line": line, "object": vertices, "image": image}
        answer, display = answer_for(parameters, difficulty)
        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=presentation(parameters, difficulty),
            answer=answer,
            answer_display=display,
            worked_solution=(),
            marks=2,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=0),
            parameters=parameters,
            question_visuals=(plot_for(parameters, difficulty == 4),),
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
        parameters = question.parameters
        require(
            set(parameters) == {"line", "object", "image"},
            "Unexpected parameters",
        )
        line = parameters["line"]
        require(
            isinstance(line, dict)
            and set(line) == {"axis", "offset"}
            and type(line["offset"]) is int
            and line in allowed_lines(level),
            "Unsupported mirror line for this level",
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
                "Invalid triangle coordinates or grid margin",
            )
            require(double_area(vertices) > 0, "Degenerate triangle")

        source = parameters["object"]
        horizontal = source[1][0] - source[0][0]
        vertical = source[2][1] - source[0][1]
        require(
            source[1][1] == source[0][1]
            and source[2][0] == source[0][0]
            and abs(horizontal) in (2, 3, 4)
            and abs(vertical) in (2, 3, 4)
            and abs(horizontal) != abs(vertical),
            "Object must be a scalene right triangle",
        )
        require(
            separated(source, parameters["image"]),
            "Object and image must be visually separated",
        )
        require(
            parameters["image"] == reflect(source, line),
            "Incorrect reflected image",
        )
        answer, display = answer_for(parameters, level)
        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Answer display mismatch")
        require(question.prompt == presentation(parameters, level), "Prompt mismatch")
        require(
            question.visual_assets("questions") == (plot_for(parameters, level == 4),),
            "Student graph mismatch",
        )
        require(
            question.visual_assets("answers") == (plot_for(parameters, True),),
            "Answer graph mismatch",
        )
        return True

    def validate_independently(self, question):
        """Check perpendicular-bisector conditions, not coordinate swap formulas.

        For the line a*x + b*y = c, each source/image midpoint lies on
        the line and its displacement is parallel to the line's normal.
        Together these conditions determine the reflected point uniquely.
        """
        parameters = question.parameters
        if question.difficulty == 4:
            require(question.answer.get("kind") == "mirror_line", "Wrong answer kind")
            line = question.answer["line"]
            image = parameters["image"]
        else:
            require(
                question.answer.get("kind") == "polygon_vertices",
                "Wrong answer kind",
            )
            line = parameters["line"]
            image = question.answer["vertices"]

        require(
            isinstance(line, dict)
            and set(line) == {"axis", "offset"}
            and type(line["offset"]) is int
            and line in allowed_lines(question.difficulty),
            "Invalid mirror-line answer",
        )
        if line["axis"] == "x":
            a, b, c = 1, 0, line["offset"]
        elif line["axis"] == "y":
            a, b, c = 0, 1, line["offset"]
        else:
            a, b, c = -line["offset"], 1, 0

        source = parameters["object"]
        require(
            isinstance(image, list) and len(image) == len(source)
            and all(
                isinstance(point, list) and len(point) == 2
                and all(type(value) is int for value in point)
                for point in image
            ),
            "Invalid image vertices",
        )
        for (x, y), (u, v) in zip(source, image):
            require(
                a * (x + u) + b * (y + v) == 2 * c,
                "Mirror line does not bisect the source-image segment",
            )
            require(
                b * (u - x) - a * (v - y) == 0,
                "Source-image segment is not perpendicular to the mirror line",
            )
        require(double_area(source) == double_area(image), "Area changed")
        require(source != image, "Identity reflection is excluded")
        return True