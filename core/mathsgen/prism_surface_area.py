"""Surface areas of prisms and cylinders drawn to true proportion, with linked forms.

Forms (two per level):
  1  cuboid / open_box                  closed cuboid; box without a lid
  2  triangle / cylinder                right triangular prism; closed cylinder
  3  triangle_pythagoras / open_cylinder find the hypotenuse first; one end only
  4  missing / cube                     recover a length; cube area -> edge -> volume
Solids are drawn by solid_figures. Cylinder areas are exact multiples of pi.
The independent check adds the faces of the net one by one.
"""
import math
from fractions import Fraction

from . import solid_figures
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .circle_measures import exact_root, pi_expression
from .rounding import decimal_text


INFO = GeneratorInfo(
    id="geometry.surface_area.prisms", version=4,
    topic="geometry", subtopic="surface_area",
    title="Surface area of prisms and cylinders",
    difficulty_descriptions={
        1: "Find the surface area of a closed cuboid or an open box.",
        2: "Find the surface area of a right triangular prism or a closed cylinder.",
        3: "Find a hypotenuse first, or leave one end off a cylinder.",
        4: "Recover a length from surface area, or a cube's volume from its area.",
    },
    tags=("geometry", "surface_area", "prisms", "cylinders", "reverse"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("cuboid", "open_box"),
    2: ("triangle", "cylinder"),
    3: ("triangle_pythagoras", "open_cylinder"),
    4: ("missing", "cube"),
}
TRIPLES = ((3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17), (9, 12, 15))
DIMENSIONS = {
    "cuboid": ("width", "height", "length"),
    "open_box": ("width", "height", "length"),
    "triangle": ("base", "height", "hypotenuse", "length"),
    "triangle_pythagoras": ("base", "height", "length"),
    "cylinder": ("radius", "length"),
    "open_cylinder": ("radius", "length"),
    "cube": (),
}
MISSING_SHAPES = ("cuboid", "triangle", "cylinder")
PI_SHAPES = ("cylinder", "open_cylinder")
WORDS = {"width": "width", "height": "height", "length": "length", "base": "base",
         "hypotenuse": "hypotenuse", "radius": "radius"}
MARKS = {1: 3, 2: 3, 3: 4, 4: 4}


# ------------------------------------------------------------ mathematics

def hypotenuse_of(d):
    if "hypotenuse" in d:
        return Fraction(d["hypotenuse"])
    return exact_root(Fraction(d["base"]) ** 2 + Fraction(d["height"]) ** 2)


def area_of(shape, d):
    """Total surface area (as a coefficient of pi for cylinders)."""
    if shape in ("cuboid", "open_box"):
        w, h, l = d["width"], d["height"], d["length"]
        closed = 2 * (w * h + w * l + h * l)
        return closed - w * l if shape == "open_box" else closed
    if shape in ("triangle", "triangle_pythagoras"):
        b, h = d["base"], d["height"]
        return b * h + (b + h + hypotenuse_of(d)) * d["length"]
    r = d["radius"]
    ends = 1 if shape == "open_cylinder" else 2
    return ends * r * r + 2 * r * d["length"]


def missing_length(p):
    shape, d, area = p["shape"], p["dims"], Fraction(p["area"])
    if shape == "cuboid":
        return (area - 2 * d["width"] * d["height"]) / (2 * (d["width"] + d["height"]))
    if shape == "triangle":
        return (area - d["base"] * d["height"]) / (d["base"] + d["height"] + d["hypotenuse"])
    return (area - 2 * d["radius"] ** 2) / (2 * d["radius"])


def cube_edge(p):
    return exact_root(Fraction(p["area"]) / 6)


def answer_for(p):
    form = p["form"]
    if form == "missing":
        return {"kind": "exact_measure", "value": rational_text(missing_length(p)),
                "pi": False, "unit": "cm"}
    if form == "cube":
        return {"kind": "exact_measure", "value": rational_text(cube_edge(p) ** 3),
                "pi": False, "unit": "cm^3"}
    d = {key: Fraction(value) for key, value in p["dims"].items()}
    return {"kind": "exact_measure", "value": rational_text(area_of(p["shape"], d)),
            "pi": p["shape"] in PI_SHAPES, "unit": "cm^2"}


def measure(value, uses_pi, tex=False):
    if uses_pi:
        return pi_expression(0, value, tex)
    return decimal_text(Fraction(value))


def display_for(answer):
    unit = answer["unit"]
    tex_unit = {"cm^2": r"\ \mathrm{cm}^{2}", "cm^3": r"\ \mathrm{cm}^{3}",
                "cm": r"\ \mathrm{cm}"}[unit]
    return Content(measure(answer["value"], answer["pi"]) + " " + unit,
                   measure(answer["value"], answer["pi"], True) + tex_unit)


def check_parameters(p, level):
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(form in FORMS[level], "Unexpected form for this level")
    keys = {"form", "shape", "dims", "style", "mirror"}
    if form in ("missing", "cube"):
        keys.add("area")
    require(set(p) == keys, "Unexpected parameters")
    require(type(p["mirror"]) is bool, "Invalid depth direction")
    shape = p["shape"]
    if form == "missing":
        require(shape in MISSING_SHAPES, "Invalid shape for a missing length")
        expected = set(DIMENSIONS[shape]) - {"length"}
    else:
        require(shape == form, "Shape does not match the form")
        expected = set(DIMENSIONS[shape])
    d = p["dims"]
    require(isinstance(d, dict) and set(d) == expected, "Wrong given dimensions")
    require(all(type(v) is int and 2 <= v <= 17 for v in d.values()), "Dimensions outside bounds")
    if "area" in p:
        area = Fraction(p["area"])
        require(area > 0 and rational_text(area) == p["area"], "Invalid surface area")
    if shape in ("triangle", "triangle_pythagoras"):
        legs = tuple(sorted((d["base"], d["height"])))
        require(any(legs == triple[:2] for triple in TRIPLES), "Unsupported triangle")
        if shape == "triangle":
            require(d["hypotenuse"] ** 2 == d["base"] ** 2 + d["height"] ** 2, "Invalid hypotenuse")
        require(p["style"].get("corner") in ("left", "right") and set(p["style"]) == {"corner"},
                "Invalid triangle style")
    else:
        require(p["style"] == {}, "Unexpected style")
    if form == "missing":
        length = missing_length(p)
        require(length.denominator == 1 and 3 <= length <= 15, "Recovered length outside bounds")
    if form == "cube":
        edge = cube_edge(p)
        require(edge.denominator == 1 and 2 <= edge <= 12, "Cube edge outside bounds")


# ------------------------------------------------------------ presentation

def label_texts(p):
    texts = {key: "{} cm".format(value) for key, value in p["dims"].items()}
    if p["form"] == "missing":
        texts["length"] = "x"
    return texts


def diagram_for(p):
    shape, form = p["shape"], p["form"]
    texts = label_texts(p)
    d = {key: Fraction(value) for key, value in p["dims"].items()}
    if form == "missing":
        d["length"] = missing_length(p)
    if shape in PI_SHAPES:
        return solid_figures.cylinder_scene(float(d["radius"]), float(d["length"]),
                                            texts["radius"], texts["length"])
    if form == "cube":
        edge = float(cube_edge(p))
        return solid_figures.prism_scene([(0, 0), (edge, 0), (edge, edge), (0, edge)],
                                         edge, {}, None, p["mirror"])
    if shape in ("cuboid", "open_box"):
        w, h = float(d["width"]), float(d["height"])
        height_edge = 1 if p["mirror"] else 3
        edges = {0: texts["width"], height_edge: texts["height"]}
        return solid_figures.prism_scene([(0, 0), (w, 0), (w, h), (0, h)], float(d["length"]),
                                         edges, texts["length"], p["mirror"])
    b, h = float(d["base"]), float(d["height"])
    left = p["style"]["corner"] == "left"
    section = [(0, 0), (b, 0), (0, h)] if left else [(0, 0), (b, 0), (b, h)]
    edges = {0: texts["base"], (2 if left else 1): texts["height"]}
    if "hypotenuse" in texts:
        edges[1 if left else 2] = texts["hypotenuse"]
    return solid_figures.prism_scene(section, float(d["length"]), edges, texts["length"],
                                     p["mirror"], (0,) if left else (1,))


def presentation(p):
    form, shape = p["form"], p["shape"]
    details = "; ".join("{} = {} cm".format(WORDS[k], v) for k, v in p["dims"].items())
    if form == "cube":
        lead = ("A cube has a total surface area of {} square centimetres. "
                "Find its volume.").format(p["area"])
        return Content(lead)
    if form == "missing":
        name = {"cuboid": "closed cuboid", "triangle": "closed right triangular prism",
                "cylinder": "closed cylinder"}[shape]
        area = measure(p["area"], shape == "cylinder")
        lead = "The total surface area of the {} is {} square centimetres. Find the length, x.".format(
            name, area)
        return Content(lead + " " + details + ".", display_text=lead)
    lead = {
        "cuboid": "Find the total surface area of the closed cuboid.",
        "open_box": "The box is a cuboid with no lid. Find its total outside surface area.",
        "triangle": "Find the total surface area of the closed right triangular prism.",
        "triangle_pythagoras": ("The cross-section of this closed prism is a right-angled "
                                "triangle. Find its total surface area."),
        "cylinder": "Find the total surface area of the closed cylinder.",
        "open_cylinder": ("The cylinder is open at the top and closed at the bottom. "
                          "Find its total outside surface area."),
    }[shape]
    if shape in PI_SHAPES:
        lead += " Give your answer in terms of pi."
    return Content(lead + " " + details + ".", display_text=lead)


def draw(rng, level):
    form = rng.choice(FORMS[level])
    shape = rng.choice(MISSING_SHAPES) if form == "missing" else form
    p = {"form": form, "shape": shape, "style": {}, "mirror": rng.random() < 0.5}
    if shape in ("cuboid", "open_box"):
        d = {"width": rng.randint(3, 12), "height": rng.randint(3, 12),
             "length": rng.randint(3, 15)}
    elif shape in ("triangle", "triangle_pythagoras"):
        base, height, hypotenuse = rng.choice(TRIPLES)
        if rng.random() < 0.5:
            base, height = height, base
        d = {"base": base, "height": height, "length": rng.randint(3, 15)}
        if shape == "triangle":
            d["hypotenuse"] = hypotenuse
        p["style"] = {"corner": rng.choice(("left", "right"))}
    elif shape in PI_SHAPES:
        d = {"radius": rng.randint(2, 12), "length": rng.randint(3, 15)}
    else:
        d = {}
        p["area"] = str(6 * rng.randint(2, 12) ** 2)
    if form == "missing":
        full = {key: Fraction(value) for key, value in d.items()}
        p["area"] = rational_text(area_of(shape, full))
        del d["length"]
    p["dims"] = d
    return p


# ------------------------------------------------------------ generator

class PrismSurfaceArea:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        for attempt in range(300):
            p = draw(rng, difficulty)
            try:
                check_parameters(p, difficulty)
                require(solid_figures.labels_ok(diagram_for(p)), "Labels not clear")
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a surface-area question")
        answer = answer_for(p)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=presentation(p), answer=answer,
            answer_display=display_for(answer), worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=5),
            parameters=p, question_visuals=(diagram_for(p),),
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        require(type(q.difficulty) is int and q.difficulty in (1, 2, 3, 4), "Invalid level")
        require(q.settings == {}, "Unsupported settings")
        check_parameters(q.parameters, q.difficulty)
        require(q.answer == answer_for(q.parameters), "Incorrect answer")
        require(q.answer_display == display_for(q.answer), "Display mismatch")
        require(q.prompt == presentation(q.parameters), "Prompt mismatch")
        require(q.visual_assets("questions") == (diagram_for(q.parameters),), "Diagram mismatch")
        require(not q.visual_assets("answers"), "Unexpected answer visuals")
        return True

    def validate_independently(self, q):
        """Add the faces of the net one by one; substitute reverse answers back."""
        p, answer = q.parameters, q.answer
        form, shape = p["form"], p["shape"]
        if form == "cube":
            volume = Fraction(answer["value"])
            edge = round(float(volume) ** (1 / 3))
            require(edge ** 3 == volume and 6 * edge * edge == Fraction(p["area"]),
                    "Cube volume and area disagree")
            return True
        d = {key: Fraction(value) for key, value in p["dims"].items()}
        if form == "missing":
            d["length"] = Fraction(answer["value"])
            require(d["length"] > 0, "Missing length must be positive")
        if shape in ("cuboid", "open_box"):
            w, h, l = d["width"], d["height"], d["length"]
            faces = [w * h, w * h, h * l, h * l, w * l] + ([] if shape == "open_box" else [w * l])
        elif shape in ("triangle", "triangle_pythagoras"):
            square = d["base"] ** 2 + d["height"] ** 2
            hypotenuse = math.isqrt(int(square))
            require(hypotenuse * hypotenuse == square, "Hypotenuse is not whole")
            triangle = d["base"] * d["height"] / 2
            faces = [triangle, triangle] + [side * d["length"] for side in
                                            (d["base"], d["height"], hypotenuse)]
        else:
            diameter = 2 * d["radius"]
            disk = diameter * diameter / 4
            ends = [disk] if shape == "open_cylinder" else [disk, disk]
            faces = ends + [diameter * d["length"]]
        target = Fraction(p["area"]) if form == "missing" else Fraction(answer["value"])
        require(sum(faces) == target, "Face-by-face surface area disagrees")
        require(answer["pi"] == (shape in PI_SHAPES and form != "missing"), "Wrong pi factor")
        return True