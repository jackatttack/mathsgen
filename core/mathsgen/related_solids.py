"""Volume relationships leading to linear, quadratic and cubic equations."""
import math
from copy import deepcopy
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question,
    make_context, rational_text, require,
)
from .prism_volume import scene_for


INFO = GeneratorInfo(
    id="problem_solving.related_solids.volume",
    version=2,
    topic="problem_solving",
    subtopic="related_solids",
    title="Related solids: volumes and algebra",
    difficulty_descriptions={
        1: "Form a linear equation from related cuboid volumes.",
        2: "Use two algebraic dimensions to form a quadratic equation.",
        3: "Find a cylinder radius from a cylinder or sphere volume relationship.",
        4: "Find a sphere radius from a cylinder or cuboid volume relationship.",
    },
    tags=("problem solving", "volume", "algebra", "ratio", "percentage", "solids"),
)

RELATIONS = (
    ("equal", "1"),
    ("multiple", "2"), ("multiple", "3"),
    ("percentage", "50"), ("percentage", "75"),
    ("percentage", "125"), ("percentage", "150"),
    ("ratio", "2/5"), ("ratio", "3/2"), ("ratio", "4/3"),
)


def relation_factor(relation):
    style, value = relation
    return Fraction(value) / 100 if style == "percentage" else Fraction(value)


def relation_text(relation):
    style, value = relation
    if style == "equal":
        return "The two solids have equal volumes."
    if style == "multiple":
        return "The volume of B is {} times the volume of A.".format(value)
    if style == "percentage":
        return "The volume of B is {}% of the volume of A.".format(value)
    factor = Fraction(value)
    return "The ratio of the volume of A to the volume of B is {}:{}.".format(
        factor.denominator, factor.numerator,
    )


def known_coefficient(solid):
    d = solid["dimensions"]
    if solid["shape"] == "cuboid":
        return Fraction(d[0] * d[1] * d[2])
    if solid["shape"] == "cylinder":
        return Fraction(d[0] ** 2 * d[1])
    return Fraction(4, 3) * d[0] ** 3


def uses_pi(shape):
    return shape in ("cylinder", "sphere")


def target_polynomial(target):
    """Coefficients of x, x squared and x cubed, before any pi factor."""
    model, d = target["model"], target["dimensions"]
    if model == "linear":
        # Cuboid dimensions: fixed width, fixed height, x + offset.
        return [Fraction(d[0] * d[1] * d[2]), Fraction(d[0] * d[1]), Fraction(0), Fraction(0)]
    if model == "quadratic":
        # Cuboid dimensions: x, x + offset, fixed length.
        return [Fraction(0), Fraction(d[0] * d[1]), Fraction(d[1]), Fraction(0)]
    if model == "cylinder":
        return [Fraction(0), Fraction(0), Fraction(d[0]), Fraction(0)]
    return [Fraction(0), Fraction(0), Fraction(0), Fraction(4, 3)]


def target_shape(target):
    return "cuboid" if target["model"] in ("linear", "quadratic") else target["model"]


def numeric_rhs(parameters):
    rhs = relation_factor(parameters["relation"]) * known_coefficient(parameters["known"])
    if uses_pi(parameters["known"]["shape"]):
        rhs = float(rhs) * math.pi
    if uses_pi(target_shape(parameters["target"])):
        rhs = float(rhs) / math.pi
    return float(rhs)


def positive_root(parameters):
    coefficients = target_polynomial(parameters["target"])
    rhs = numeric_rhs(parameters)
    constant, linear, quadratic, cubic = map(float, coefficients)
    if cubic:
        return (rhs / cubic) ** (1.0 / 3.0)
    if quadratic:
        # Stable positive root of a*x*x+b*x-rhs=0.
        return 2 * rhs / (linear + math.sqrt(linear * linear + 4 * quadratic * rhs))
    return (rhs - constant) / linear


def exact_term(value, pi=False):
    text = rational_text(value)
    return "(" + text + ")*pi" if pi else text


def equation_text(parameters):
    model, d = parameters["target"]["model"], parameters["target"]["dimensions"]
    if model == "linear":
        left = "{}(x + {})".format(d[0] * d[1], d[2])
    elif model == "quadratic":
        left = "{}x(x + {})".format(d[1], d[0])
    elif model == "cylinder":
        left = "{}*pi*x^2".format(d[0])
    else:
        left = "(4/3)*pi*x^3"
    rhs = relation_factor(parameters["relation"]) * known_coefficient(parameters["known"])
    return left + " = " + exact_term(rhs, uses_pi(parameters["known"]["shape"]))


def answer_for(parameters):
    return {
        "kind": "related_solid_dimension",
        "x_1dp": format(positive_root(parameters), ".1f"),
        "unit": "cm",
        "equation": equation_text(parameters),
    }


def display_for(answer, parameters=None):
    fallback = (
        "One valid equation: {}. Positive solution: x = {} cm "
        "(to 1 decimal place). Equivalent equations are accepted."
    ).format(answer["equation"], answer["x_1dp"])
    if parameters is None:
        return Content(fallback)
    from .related_solids_typography import answer_blocks
    return Content(fallback, blocks=answer_blocks(parameters, answer))


def presentation(parameters):
    known, target = parameters["known"], parameters["target"]
    shape, d = known["shape"], known["dimensions"]
    if shape == "cuboid":
        text = "Solid A is a cuboid with dimensions {} cm, {} cm and {} cm. ".format(*d)
    elif shape == "cylinder":
        text = "Solid A is a cylinder with radius {} cm and perpendicular height {} cm. ".format(*d)
    else:
        text = "Solid A is a sphere with radius {} cm. ".format(d[0])
    model, d = target["model"], target["dimensions"]
    if model == "linear":
        text += "Solid B is a cuboid with dimensions {} cm, {} cm and (x + {}) cm. ".format(*d)
    elif model == "quadratic":
        text += "Solid B is a cuboid with dimensions x cm, (x + {}) cm and {} cm. ".format(*d)
    elif model == "cylinder":
        text += "Solid B is a cylinder with radius x cm and perpendicular height {} cm. ".format(d[0])
    else:
        text += "Solid B is a sphere with radius x cm. "
    text += relation_text(parameters["relation"])
    text += " Form an equation in x and solve it. Given that x > 0, give x to 1 decimal place."
    if shape == "sphere" or model == "sphere":
        text += " The volume of a sphere is (4/3)pi*r^3."
    from .related_solids_typography import question_blocks
    return Content(
        text, blocks=question_blocks(parameters, relation_text(parameters["relation"])),
    )


def solid_scene(shape):
    if shape != "sphere":
        return scene_for(shape)
    return {
        "kind": "scene", "version": 1, "width": 360, "height": 250,
        "caption": "Not drawn accurately",
        "nodes": [
            {"type": "circle", "center": [180, 125], "radius": 75},
            {"type": "polygon", "points": [
                [180 + 75 * math.cos(2 * math.pi * i / 48),
                 125 + 20 * math.sin(2 * math.pi * i / 48)]
                for i in range(48)
            ]},
            {"type": "line", "points": [[180, 125], [255, 125]]},
            {"type": "circle", "center": [180, 125], "radius": 1.6, "shade": True},
        ],
    }


def diagram_for(parameters):
    """Two fixed schematic solids; dimensions are supplied in the prose."""
    nodes = []
    for offset, shape in (
        (0, parameters["known"]["shape"]),
        (360, target_shape(parameters["target"])),
    ):
        for original in solid_scene(shape)["nodes"]:
            node = deepcopy(original)
            if "points" in node:
                node["points"] = [[x + offset, y] for x, y in node["points"]]
            for key in ("center", "vertex", "first", "second"):
                if key in node:
                    node[key][0] += offset
            nodes.append(node)
    return {
        "kind": "scene", "version": 1, "width": 720, "height": 250,
        "caption": "Solid A (left); solid B (right). Not drawn accurately.",
        "nodes": nodes,
    }


def check_parameters(p, level):
    require(set(p) == {"known", "target", "relation"}, "Unexpected parameters")
    require(tuple(p["relation"]) in RELATIONS, "Unsupported relationship")
    known, target = p["known"], p["target"]
    require(set(known) == {"shape", "dimensions"}, "Invalid known solid")
    require(set(target) == {"model", "dimensions"}, "Invalid target solid")
    model = {1: "linear", 2: "quadratic", 3: "cylinder", 4: "sphere"}[level]
    require(target["model"] == model, "Wrong task for level")
    allowed = {1: ("cuboid",), 2: ("cuboid",),
               3: ("cylinder", "sphere"), 4: ("cylinder", "cuboid")}[level]
    require(known["shape"] in allowed, "Wrong reference solid")
    counts = {"cuboid": 3, "cylinder": 2, "sphere": 1}
    require(
        isinstance(known["dimensions"], list)
        and len(known["dimensions"]) == counts[known["shape"]]
        and all(type(v) is int and 3 <= v <= 12 for v in known["dimensions"]),
        "Invalid reference dimensions",
    )
    require(
        isinstance(target["dimensions"], list)
        and len(target["dimensions"]) == {1: 3, 2: 2, 3: 1, 4: 0}[level]
        and all(type(v) is int and 2 <= v <= 8 for v in target["dimensions"]),
        "Invalid target dimensions",
    )
    root = positive_root(p)
    require(1 <= root <= 20, "Positive solution outside intended bounds")
    # Avoid floating-point-sensitive rounding boundaries.
    require(abs(root * 10 - (math.floor(root * 10) + 0.5)) > 0.00001,
            "Solution too close to rounding boundary")


class RelatedSolidVolumes:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        for attempt in range(500):
            shape = rng.choice({
                1: ("cuboid",), 2: ("cuboid",),
                3: ("cylinder", "sphere"), 4: ("cylinder", "cuboid"),
            }[difficulty])
            known = {
                "shape": shape,
                "dimensions": [rng.randint(3, 12) for _ in range(
                    {"cuboid": 3, "cylinder": 2, "sphere": 1}[shape])],
            }
            target = {
                "model": {1: "linear", 2: "quadratic", 3: "cylinder", 4: "sphere"}[difficulty],
                "dimensions": [rng.randint(2, 8) for _ in range(
                    {1: 3, 2: 2, 3: 1, 4: 0}[difficulty])],
            }
            p = {"known": known, "target": target, "relation": list(rng.choice(RELATIONS))}
            root = positive_root(p)
            if 1 <= root <= 20 and abs(root * 10 - (math.floor(root * 10) + 0.5)) > 0.00001:
                break
        else:
            raise ValueError("Could not construct a suitable positive solution")
        answer = answer_for(p)
        question = Question(
            id=context.identity, generator_id=self.info.id, generator_version=self.info.version,
            topic=self.info.topic, subtopic=self.info.subtopic, difficulty=difficulty,
            seed=seed, settings=context.settings, prompt=presentation(p),
            answer=answer, answer_display=display_for(answer, p), worked_solution=(),
            marks=5, tags=self.info.tags, layout_hint=LayoutHint(working_lines=6),
            parameters=p, question_visuals=(diagram_for(p),),
        )
        self.validate(question)
        return question

    def validate(self, q):
        require(q.generator_id == self.info.id and q.generator_version == self.info.version,
                "Generator/version mismatch")
        require(type(q.difficulty) is int and q.difficulty in (1, 2, 3, 4), "Invalid level")
        require(q.settings == {}, "Unsupported settings")
        check_parameters(q.parameters, q.difficulty)
        require(q.answer == answer_for(q.parameters), "Incorrect answer")
        require(q.prompt == presentation(q.parameters), "Prompt mismatch")
        require(q.answer_display == display_for(q.answer, q.parameters), "Answer display mismatch")
        require(q.visual_assets("questions") == (diagram_for(q.parameters),), "Diagram mismatch")
        return True

    def validate_independently(self, q):
        """Bracket the true solution using original solid volumes, not root formulas."""
        p = q.parameters
        d, shape = p["known"]["dimensions"], p["known"]["shape"]
        if shape == "cuboid":
            volume_a = math.prod(d)
        elif shape == "cylinder":
            diameter = 2 * d[0]
            volume_a = math.pi * diameter * diameter * d[1] / 4
        else:
            diameter = 2 * d[0]
            volume_a = math.pi * diameter ** 3 / 6
        style, value = p["relation"]
        if style == "percentage":
            ratio = float(Fraction(value)) / 100
        elif style == "ratio":
            numerator, denominator = map(int, value.split("/"))
            ratio = numerator / denominator
        else:
            ratio = float(value)
        target_volume = volume_a * ratio

        def actual_volume(x):
            model, sizes = p["target"]["model"], p["target"]["dimensions"]
            if model == "linear":
                return sizes[0] * sizes[1] * (x + sizes[2])
            if model == "quadratic":
                return x * (x + sizes[0]) * sizes[1]
            if model == "cylinder":
                return math.pi * (2 * x) ** 2 * sizes[0] / 4
            return math.pi * (2 * x) ** 3 / 6

        # All models are strictly increasing for x > 0, so this interval
        # proves both the rounded answer and uniqueness in the physical domain.
        text = q.answer["x_1dp"]
        claimed = float(text)
        require(text == format(claimed, ".1f") and claimed > 0, "Invalid rounded length")
        require(
            actual_volume(claimed - 0.05) < target_volume
            < actual_volume(claimed + 0.05),
            "Rounded solution does not bracket the volume relationship",
        )
        require(q.answer["unit"] == "cm", "Wrong unit")
        return True