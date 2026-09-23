"""L-shaped compound areas with varied orientation and a two-step reverse task."""
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)
from . import figures


INFO = GeneratorInfo(
    id="geometry.area.compound_rectangles", version=2,
    topic="geometry", subtopic="area",
    title="Area of compound rectilinear shapes",
    difficulty_descriptions={
        1: "Add two rectangles using a shown dividing line.",
        2: "Subtract a rectangular cut-out from an enclosing rectangle.",
        3: "Infer unlabelled dimensions before calculating the area.",
        4: "Find a missing length from the given compound area.",
    },
    tags=("geometry", "area", "compound_shapes", "reverse"),
)


def dimensions(given, level, missing=None):
    """Recover outer width/height and top-right cut-out width/height."""
    if level == 1:
        width = given["W"]
        return width, given["t"] + given["h"], width - given["s"], given["h"]
    if level == 2:
        return given["W"], given["H"], given["w"], given["h"]
    if level == 3:
        return given["W"], given["H"], given["W"] - given["s"], given["H"] - given["t"]
    return given["W"], given["H"], given["w"], missing


def presentation(given, level, orientation=None, task="missing"):
    # Lengths are stated; orientation never changes the mathematics.
    if orientation is None:
        orientation = [0, False]
    points = [[60, 35], [290, 35], [290, 100],
              [170, 100], [170, 190], [60, 190]]
    nodes = [{"type": "polygon", "points": points, "shade": True}]
    positions = {
        "W": [175, 15], "H": [30, 112], "w": [230, 120],
        "h": [194, 153], "s": [115, 210], "t": [316, 67],
    }
    descriptions = {
        "W": "outer edge W", "H": "perpendicular outer edge H",
        "w": "inner edge parallel to W", "h": "inner edge parallel to H",
        "s": "remaining outer edge parallel to W",
        "t": "remaining outer edge parallel to H",
    }
    if level == 1:
        instruction = (
            "Calculate the shaded area. The dashed line divides the shape "
            "into two rectangles. All corners are right angles."
        )
        nodes.append({"type": "line", "points": [[60, 100], [170, 100]], "dashed": True})
    elif level == 4:
        if task == "inner_trim":
            instruction = (
                "The shaded area is {} square centimetres. Find the total "
                "length of the two perpendicular inner edges of the cut-out. "
                "All corners are right angles."
            ).format(given["area"])
        else:
            instruction = (
                "The shaded area is {} square centimetres. Find the inner "
                "step length x. All corners are right angles."
            ).format(given["area"])
    else:
        instruction = "Calculate the shaded area. All corners are right angles."
    fallback = []
    for key, value in given.items():
        if key == "area":
            continue
        nodes.append({"type": "label", "point": positions[key], "text": str(value) + " cm"})
        fallback.append("{} = {} cm".format(descriptions[key], value))
    if level == 4:
        nodes.append({"type": "label", "point": positions["h"], "text": "x"})
    # Explain the topology in the CLI, where the diagram is unavailable.
    plain = (
        instruction + " The shape is a rectangle with a rectangular "
        "cut-out at one corner. " + "; ".join(fallback) + "."
    )
    scene = {
        "kind": "scene", "version": 1, "width": 360, "height": 230,
        "caption": "Not drawn accurately", "nodes": nodes,
    }
    return Content(plain, display_text=instruction), figures.orient_scene(
        scene, orientation)


def answer_content(result, level, task="missing"):
    if level == 4 and task == "inner_trim":
        return Content("Two inner edges: {} cm".format(result),
                       str(result) + r"\ \mathrm{cm}")
    if level == 4:
        return Content("x = {} cm".format(result),
                       r"x = " + str(result) + r"\ \mathrm{cm}")
    return Content("{} cm^2".format(result),
                   str(result) + r"\ \mathrm{cm}^{2}")


class CompoundRectangleArea:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        s, t, w, h = [rng.randint(3, 9) for _ in range(4)]
        width, height = s + w, t + h
        area = width * t + s * h
        if difficulty == 1:
            given = {"W": width, "t": t, "s": s, "h": h}
        elif difficulty == 2:
            given = {"W": width, "H": height, "w": w, "h": h}
        elif difficulty == 3:
            given = {"W": width, "H": height, "s": s, "t": t}
        else:
            given = {"W": width, "H": height, "w": w, "area": area}
        task = rng.choice(("missing", "inner_trim")) if difficulty == 4 else "area"
        result = (h + w if task == "inner_trim" else h) if difficulty == 4 else area
        parameters = {"given": given}
        if difficulty == 4:
            parameters["task"] = task
        parameters["orientation"] = figures.choose_orientation(
            rng, lambda orientation: presentation(
                given, difficulty, orientation, task)[1])
        prompt, visual = presentation(
            given, difficulty, parameters["orientation"], task)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt,
            answer={"kind": "length" if difficulty == 4 else "area",
                    "value": result, "unit": "cm" if difficulty == 4 else "cm^2"},
            answer_display=answer_content(result, difficulty, task),
            worked_solution=(), marks=5 if task == "inner_trim" else
            4 if difficulty == 4 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=5 if task == "inner_trim" else 4),
            parameters=parameters, question_visuals=(visual,),
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        parameters = q.parameters
        require(isinstance(parameters, dict)
                and set(parameters) == (
                    {"given", "orientation", "task"} if level == 4
                    else {"given", "orientation"}),
                "Unexpected question parameters")
        require(figures.valid_orientation(parameters["orientation"]),
                "Unknown orientation")
        task = parameters.get("task", "area")
        require(task in (("missing", "inner_trim") if level == 4
                         else ("area",)), "Unknown area task")
        given = parameters["given"]
        expected_keys = {
            1: {"W", "t", "s", "h"}, 2: {"W", "H", "w", "h"},
            3: {"W", "H", "s", "t"}, 4: {"W", "H", "w", "area"},
        }
        require(isinstance(given, dict) and set(given) == expected_keys[level],
                "Unexpected stated dimensions")
        require(all(type(v) is int and v > 0 for v in given.values()),
                "Dimensions and area must be positive integers")
        require(isinstance(q.answer, dict) and type(q.answer.get("value")) is int,
                "Invalid answer")
        result = q.answer["value"]
        require(result > 0, "Invalid answer")
        missing_length = result - given["w"] if task == "inner_trim" else result
        width, height, w, h = dimensions(given, level, missing_length)
        require(all(3 <= v <= 9 for v in (width - w, height - h, w, h)),
                "Shape dimensions outside construction bounds")
        area = width * height - w * h
        require(area == (given["area"] if level == 4 else result),
                "Incorrect compound area or missing length")
        if task == "inner_trim":
            require(result == w + h, "Incorrect combined inner-edge length")
        require(q.answer == {
            "kind": "length" if level == 4 else "area", "value": result,
            "unit": "cm" if level == 4 else "cm^2",
        }, "Answer kind or units mismatch")
        prompt, visual = presentation(
            given, level, parameters["orientation"], task)
        require(q.prompt == prompt, "Prompt mismatch")
        require(q.visual_assets("questions") == (visual,), "Diagram mismatch")
        require(not q.visual_assets("answers"), "Unexpected answer assets")
        require(q.answer_display == answer_content(result, level, task),
                "Display mismatch")
        require(q.marks == (5 if task == "inner_trim" else
                4 if level == 4 else 3), "Marks mismatch")
        return True

    def validate_independently(self, q):
        """Use the shoelace formula on the six vertices of the actual shape."""
        import sympy

        level = q.difficulty
        given = q.parameters["given"]
        unknown = sympy.Symbol("z")
        width, height, w, h = dimensions(given, level, unknown if level == 4 else None)
        vertices = [
            (0, 0), (width, 0), (width, height - h),
            (width - w, height - h), (width - w, height), (0, height),
        ]
        twice_area = sum(
            a[0] * b[1] - b[0] * a[1]
            for a, b in zip(vertices, vertices[1:] + vertices[:1])
        )
        area = sympy.expand(sympy.Rational(1, 2) * twice_area)
        if level == 4:
            coefficient = area.coeff(unknown)
            require(coefficient != 0, "Area does not determine the missing length")
            recovered = (sympy.Integer(given["area"]) - area.subs(unknown, 0)) / coefficient
            if q.parameters["task"] == "inner_trim":
                recovered += given["w"]
        else:
            recovered = area
        require(recovered == q.answer["value"], "Independent polygon calculation disagrees")
        return True