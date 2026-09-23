"""Exact enlargements on full square coordinate grids with equal physical units."""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)

FACTORS = {
    1: ("2", "3"),
    2: ("1/2", "1/3"),
    3: ("-2", "-3", "-1/2"),
    4: ("2", "3", "1/2", "1/3", "-2", "-3", "-1/2"),
}
TEMPLATES = (
    ((2, -1), (4, -1), (3, 1)),
    ((2, -1), (4, -1), (4, 1), (2, 1)),
)

INFO = GeneratorInfo(
    id="geometry.transformations.enlargement", version=2,
    topic="geometry", subtopic="transformations",
    title="Enlargements on coordinate grids",
    difficulty_descriptions={
        1: "Draw an enlargement with a positive integer scale factor.",
        2: "Draw a reduction with a positive fractional scale factor.",
        3: "Draw an enlargement with a negative scale factor.",
        4: "Find the signed scale factor from an object and its image.",
    },
    tags=("geometry", "transformations", "enlargement", "coordinates"),
)


def transform(vertices, centre, factor):
    result = []
    for point in vertices:
        mapped = [
            Fraction(c) + factor * (v - c)
            for v, c in zip(point, centre)
        ]
        require(all(v.denominator == 1 for v in mapped),
                "Image must lie on integer grid intersections")
        result.append([v.numerator for v in mapped])
    return result


def points_text(points):
    return ", ".join("({}, {})".format(*point) for point in points)


def plot_for(p, completed):
    cx, cy = p["centre"]
    curves = [{
        "segments": [p["object"] + [p["object"][0]]],
        "dashed": False,
    }]
    if completed:
        curves.append({
            "segments": [p["image"] + [p["image"][0]]],
            "dashed": True,
        })
    return {
        "kind": "plot", "version": 1,
        "x_range": [cx - 14, cx + 14],
        "y_range": [cy - 14, cy + 14],
        "x_step": 4, "y_step": 4,
        "minor_divisions": 4,
        "equal_units": True,
        "curves": curves, "points": [p["centre"]],
        "x_label": "x", "y_label": "y",
    }


def presentation(p, level):
    centre = "({}, {})".format(*p["centre"])
    if level == 4:
        lead = (
            "The solid shape maps to the dashed shape by an enlargement "
            "with centre {} (marked by a cross). Find the scale factor."
        ).format(centre)
    else:
        lead = (
            "Enlarge the solid shape by scale factor {} with centre {} "
            "(marked by a cross). Draw the image on the grid."
        ).format(p["factor"], centre)
    fallback = " Object vertices, in boundary order: " + points_text(p["object"]) + "."
    if level == 4:
        fallback += " Corresponding image vertices: " + points_text(p["image"]) + "."
    return Content(lead + fallback, display_text=lead)


def answer_for(p, level):
    if level == 4:
        return (
            {"kind": "rational", "value": p["factor"]},
            Content("Scale factor = " + p["factor"]),
        )
    return (
        {"kind": "polygon_vertices", "vertices": p["image"]},
        Content("Image vertices: " + points_text(p["image"]) + "."),
    )


def double_area(points):
    return abs(sum(
        a[0] * b[1] - b[0] * a[1]
        for a, b in zip(points, points[1:] + points[:1])
    ))


class Enlargements:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        factor_text = rng.choice(FACTORS[difficulty])
        factor = Fraction(factor_text)
        centre = [rng.randint(-2, 2), rng.randint(-2, 2)]
        template = rng.choice(TEMPLATES)
        sx, sy = rng.choice((-1, 1)), rng.choice((-1, 1))
        denominator = factor.denominator
        vertices = [
            [centre[0] + sx * x * denominator,
             centre[1] + sy * y * denominator]
            for x, y in template
        ]
        p = {
            "centre": centre, "factor": factor_text, "object": vertices,
            "image": transform(vertices, centre, factor),
        }
        answer, display = answer_for(p, difficulty)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=presentation(p, difficulty),
            answer=answer, answer_display=display, worked_solution=(),
            marks=2 if difficulty == 4 else 3, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=0),
            parameters=p,
            question_visuals=(plot_for(p, difficulty == 4),),
            answer_visuals=(plot_for(p, True),),
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in FACTORS, "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        p = q.parameters
        require(set(p) == {"centre", "factor", "object", "image"},
                "Unexpected parameters")
        require(p["factor"] in FACTORS[level], "Wrong scale factor for level")
        centre = p["centre"]
        require(isinstance(centre, list) and len(centre) == 2
                and all(type(c) is int and -2 <= c <= 2 for c in centre),
                "Invalid centre")
        for key in ("object", "image"):
            points = p[key]
            require(isinstance(points, list) and len(points) in (3, 4)
                    and all(isinstance(v, list) and len(v) == 2
                            and all(type(c) is int for c in v) for v in points),
                    "Invalid polygon coordinates")
            require(len({tuple(v) for v in points}) == len(points)
                    and double_area(points) > 0, "Degenerate polygon")
            require(all(abs(x - centre[0]) <= 12 and abs(y - centre[1]) <= 3
                        for x, y in points), "Insufficient grid margin")
        factor = Fraction(p["factor"])
        allowed_objects = [
            [[centre[0] + sx * x * factor.denominator,
              centre[1] + sy * y * factor.denominator] for x, y in template]
            for template in TEMPLATES for sx in (-1, 1) for sy in (-1, 1)
        ]
        require(p["object"] in allowed_objects, "Unsupported object structure")
        require(p["image"] == transform(p["object"], centre, factor),
                "Incorrect image")
        answer, display = answer_for(p, level)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Answer display mismatch")
        require(q.prompt == presentation(p, level), "Prompt mismatch")
        require(q.visual_assets("questions") == (plot_for(p, level == 4),),
                "Student graph mismatch")
        require(q.visual_assets("answers") == (plot_for(p, True),),
                "Answer graph mismatch")
        return True

    def validate_independently(self, q):
        """Recover the signed factor from coordinate differences at every vertex."""
        p = q.parameters
        if q.difficulty == 4:
            image = p["image"]
            claimed_factor = Fraction(q.answer["value"])
        else:
            image = q.answer["vertices"]
            claimed_factor = Fraction(p["factor"])
        require(len(image) == len(p["object"]), "Missing image vertices")
        recovered = set()
        for source, target in zip(p["object"], image):
            require(len(target) == 2, "Invalid image vertex")
            for s, t, c in zip(source, target, p["centre"]):
                if s == c:
                    require(t == c, "Coordinate on central axis moved off it")
                else:
                    recovered.add(Fraction(t - c, s - c))
        require(recovered == {claimed_factor}, "Signed scale factor disagrees")
        require(Fraction(double_area(image), double_area(p["object"]))
                == claimed_factor ** 2, "Area scaling disagrees")
        return True