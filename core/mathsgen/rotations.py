"""Exact quarter-turn rotations, construction and identification."""
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)


INFO = GeneratorInfo(
    id="geometry.transformations.rotation",
    version=1,
    topic="geometry",
    subtopic="transformations",
    title="Rotations on coordinate grids",
    difficulty_descriptions={
        1: "Draw a clockwise or anticlockwise quarter-turn about the origin.",
        2: "Draw a quarter-turn about a non-origin centre.",
        3: "Draw a half-turn about a non-origin centre.",
        4: "Describe a rotation fully, including its centre.",
    },
    tags=("geometry", "transformations", "rotation", "coordinates"),
)


def allowed_turns(level):
    return (1, 3) if level in (1, 2) else ((2,) if level == 3 else (1, 2, 3))


def rotation_text(rotation):
    turns = rotation["turns"]
    angle = {
        1: "90 degrees anticlockwise",
        2: "180 degrees",
        3: "90 degrees clockwise",
    }[turns]
    return "{} about centre ({}, {})".format(angle, *rotation["centre"])


def rotate(vertices, rotation):
    """Apply one exact anticlockwise quarter-turn at a time."""
    cx, cy = rotation["centre"]
    image = []
    for x, y in vertices:
        dx, dy = x - cx, y - cy
        for turn in range(rotation["turns"]):
            dx, dy = -dy, dx
        image.append([cx + dx, cy + dy])
    return image


def points_text(vertices):
    return ", ".join("({}, {})".format(*point) for point in vertices)


def separated(first, second):
    return any(
        max(point[axis] for point in first) < min(point[axis] for point in second)
        or max(point[axis] for point in second) < min(point[axis] for point in first)
        for axis in (0, 1)
    )


def plot_for(parameters, level, completed):
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
        "kind": "plot", "version": 1,
        "x_range": [-10, 10], "y_range": [-10, 10],
        "x_step": 2, "y_step": 2, "minor_divisions": 2,
        "equal_units": True,
        "curves": curves,
        "points": (
            [parameters["rotation"]["centre"]]
            if level != 4 or completed else []
        ),
        "x_label": "x", "y_label": "y",
    }


def presentation(parameters, level):
    if level == 4:
        lead = (
            "Describe fully the single rotation that maps the solid triangle "
            "onto the dashed triangle. Give the angle, direction where needed, "
            "and centre."
        )
    else:
        lead = (
            "Rotate the solid triangle {} (centre marked by a cross). "
            "Draw the image on the grid."
        ).format(rotation_text(parameters["rotation"]))
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
        rotation = parameters["rotation"]
        return (
            {
                "kind": "rotation",
                "rotation": {
                    "centre": rotation["centre"][:],
                    "turns": rotation["turns"],
                },
            },
            Content(
                "Rotation: " + rotation_text(rotation)
                + ". Equivalent angle/direction descriptions are accepted."
            ),
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


def check_rotation(rotation, level):
    require(
        isinstance(rotation, dict) and set(rotation) == {"centre", "turns"},
        "Invalid rotation data",
    )
    require(
        type(rotation["turns"]) is int and rotation["turns"] in allowed_turns(level),
        "Invalid angle for this level",
    )
    centre = rotation["centre"]
    require(
        isinstance(centre, list) and len(centre) == 2
        and all(type(value) is int and -3 <= value <= 3 for value in centre),
        "Invalid centre",
    )
    if level == 1:
        require(centre == [0, 0], "Level 1 requires the origin")
    elif level in (2, 3):
        require(centre != [0, 0], "This level requires a non-origin centre")


class Rotations:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        centres = [
            [x, y] for x in range(-3, 4) for y in range(-3, 4)
            if difficulty == 4 or (x, y) != (0, 0)
        ]
        rotation = {
            "centre": [0, 0] if difficulty == 1 else rng.choice(centres),
            "turns": rng.choice(allowed_turns(difficulty)),
        }
        for attempt in range(500):
            x, y = rng.randint(-7, 7), rng.randint(-7, 7)
            horizontal, vertical = rng.sample((2, 3, 4), 2)
            horizontal *= rng.choice((-1, 1))
            vertical *= rng.choice((-1, 1))
            vertices = [[x, y], [x + horizontal, y], [x, y + vertical]]
            image = rotate(vertices, rotation)
            cx, cy = rotation["centre"]
            centre_outside = not (
                min(point[0] for point in vertices) <= cx <= max(point[0] for point in vertices)
                and min(point[1] for point in vertices) <= cy <= max(point[1] for point in vertices)
            )
            if (
                all(-9 <= value <= 9 for point in vertices + image for value in point)
                and separated(vertices, image)
                and centre_outside
            ):
                break
        else:
            raise ValueError("Could not construct a readable rotation")

        parameters = {"rotation": rotation, "object": vertices, "image": image}
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
            marks=3 if difficulty == 4 else 2,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=0),
            parameters=parameters,
            question_visuals=(plot_for(parameters, difficulty, difficulty == 4),),
            answer_visuals=(plot_for(parameters, difficulty, True),),
        )
        # Identification questions show both triangles but must hide the centre.
        if difficulty == 4:
            student_plot = plot_for(parameters, difficulty, True)
            student_plot["points"] = []
            from dataclasses import replace
            question = replace(question, question_visuals=(student_plot,))
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
            set(parameters) == {"rotation", "object", "image"},
            "Unexpected parameters",
        )
        check_rotation(parameters["rotation"], level)
        for name in ("object", "image"):
            vertices = parameters[name]
            require(
                isinstance(vertices, list) and len(vertices) == 3
                and all(
                    isinstance(point, list) and len(point) == 2
                    and all(type(value) is int and -9 <= value <= 9 for value in point)
                    for point in vertices
                ),
                "Invalid triangle or insufficient grid margin",
            )
        source = parameters["object"]
        horizontal = source[1][0] - source[0][0]
        vertical = source[2][1] - source[0][1]
        require(
            source[1][1] == source[0][1] and source[2][0] == source[0][0]
            and abs(horizontal) in (2, 3, 4)
            and abs(vertical) in (2, 3, 4)
            and abs(horizontal) != abs(vertical),
            "Expected a scalene right triangle",
        )
        require(
            parameters["image"] == rotate(source, parameters["rotation"]),
            "Incorrect image",
        )
        require(separated(source, parameters["image"]), "Triangles overlap")
        answer, display = answer_for(parameters, level)
        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Answer display mismatch")
        require(question.prompt == presentation(parameters, level), "Prompt mismatch")
        student = plot_for(parameters, level, level == 4)
        if level == 4:
            student["points"] = []
        require(question.visual_assets("questions") == (student,), "Student graph mismatch")
        require(
            question.visual_assets("answers") == (plot_for(parameters, level, True),),
            "Answer graph mismatch",
        )
        return True

    def validate_independently(self, question):
        """Use lengths, dot products and signed cross products to check the angle.

        Equal radii plus the specified dot/cross products uniquely determine
        each image vector, without applying the iterative rotation routine.
        """
        parameters = question.parameters
        if question.difficulty == 4:
            require(question.answer.get("kind") == "rotation", "Wrong answer kind")
            rotation = question.answer["rotation"]
            image = parameters["image"]
        else:
            require(question.answer.get("kind") == "polygon_vertices", "Wrong answer kind")
            rotation = parameters["rotation"]
            image = question.answer["vertices"]
        check_rotation(rotation, question.difficulty)
        require(
            isinstance(image, list) and len(image) == 3
            and all(
                isinstance(point, list) and len(point) == 2
                and all(type(value) is int for value in point)
                for point in image
            ),
            "Invalid image vertices",
        )
        cx, cy = rotation["centre"]
        turns = rotation["turns"]
        cosine, sine = {1: (0, 1), 2: (-1, 0), 3: (0, -1)}[turns]
        for source, target in zip(parameters["object"], image):
            x, y = source[0] - cx, source[1] - cy
            u, v = target[0] - cx, target[1] - cy
            radius_squared = x * x + y * y
            require(u * u + v * v == radius_squared, "Radius changed")
            require(x * u + y * v == cosine * radius_squared, "Wrong rotation angle")
            require(x * v - y * u == sine * radius_squared, "Wrong rotation direction")
        return True