"""Areas of triangles, parallelograms and trapezia, including reverse tasks.

Diagrams are fixed schematics ("Not drawn accurately"); answers never come
from pixels. Level 3 labels a sloping side as a distractor. Its length comes
from a Pythagorean triple (height, horizontal offset, slope), so every
labelled length is geometrically consistent. The independent check places
the shape on coordinates and uses the shoelace formula, which gives the same
area whatever the offsets.
"""
from fractions import Fraction

from .core import Content, GeneratorInfo, require
from .family import GeneratorFamily
from . import figures


# ------------------------------------------------------------ editable pools

SHAPES = ("triangle", "parallelogram", "trapezium")
TRIPLES = (  # (height, offset, slope)
    (3, 4, 5), (4, 3, 5), (6, 8, 10), (8, 6, 10), (5, 12, 13),
    (12, 5, 13), (8, 15, 17), (9, 12, 15), (12, 9, 15),
)
MAX_AREA = 400

# Fixed schematic layouts: polygon, the dashed height from foot to top, the
# direction along the base for the right-angle marker, and label anchors.
LAYOUTS = {
    "triangle": {
        "points": [[60, 40], [290, 40], [200, 190]],
        "foot": [200, 40], "top": [200, 190], "along": [290, 40],
        "base_label": [175, 20], "height_label": [224, 105], "slant_label": [100, 125],
    },
    "parallelogram": {
        "points": [[60, 40], [250, 40], [310, 180], [120, 180]],
        "foot": [120, 40], "top": [120, 180], "along": [250, 40],
        "base_label": [155, 20], "height_label": [146, 110], "slant_label": [318, 105],
    },
    "trapezium": {
        "points": [[50, 40], [310, 40], [240, 180], [120, 180]],
        "foot": [120, 40], "top": [120, 180], "along": [310, 40],
        "base_label": [180, 20], "height_label": [146, 110], "slant_label": [314, 115],
        "top_label": [180, 198],
    },
}
REVERSE_UNKNOWNS = {"triangle": ("height", "base"), "parallelogram": ("height", "base"),
                    "trapezium": ("height", "top", "base")}


def area_of(p):
    b, h = p["base"], p["height"]
    if p["shape"] == "triangle":
        return Fraction(b * h, 2)
    if p["shape"] == "parallelogram":
        return Fraction(b * h)
    return Fraction((p["top"] + b) * h, 2)


def scene(p):
    layout = LAYOUTS[p["shape"]]
    hidden = p["unknown"]
    nodes = [
        {"type": "polygon", "points": layout["points"], "shade": True},
        {"type": "line", "points": [layout["foot"], layout["top"]], "dashed": True},
        {"type": "right_angle", "vertex": layout["foot"],
         "first": layout["along"], "second": layout["top"]},
    ]

    def label(anchor, name):
        text = "x" if hidden == name else "{} cm".format(p[name])
        nodes.append({"type": "label", "point": layout[anchor], "text": text})

    label("base_label", "base")
    label("height_label", "height")
    if p["shape"] == "trapezium":
        label("top_label", "top")
    if p["slant"]:
        nodes.append({"type": "label", "point": layout["slant_label"],
                      "text": "{} cm".format(p["slant"])})
    spec = {"kind": "scene", "version": 1, "width": 360, "height": 220,
            "caption": "Not drawn accurately", "nodes": nodes}
    return figures.orient_scene(spec, p["orientation"])


def described(p):
    """Plain description of the labelled lengths for the CLI fallback."""
    def value(name):
        return "x" if p["unknown"] == name else "{} cm".format(p[name])
    if p["shape"] == "trapezium":
        parts = ["parallel sides {} and {}".format(value("top"), value("base"))]
    else:
        parts = ["base {}".format(value("base"))]
    parts.append("perpendicular height {}".format(value("height")))
    if p["slant"]:
        parts.append("sloping side {} cm".format(p["slant"]))
    return "Lengths: " + ", ".join(parts) + "."


class BasicShapeArea(GeneratorFamily):
    info = GeneratorInfo(
        id="geometry.area.basic_shapes",
        version=2,
        topic="geometry",
        subtopic="area",
        title="Area of triangles, parallelograms and trapezia",
        difficulty_descriptions={
            1: "Triangle or parallelogram from base and perpendicular height.",
            2: "Trapezium from its parallel sides and height.",
            3: "Any of the three, with a sloping side given as a distractor.",
            4: "Find a missing length from the area.",
        },
        tags=("geometry", "area", "triangles", "trapezium", "reverse"),
    )
    keys = {level: {"shape", "base", "top", "height", "offset", "slant", "unknown",
                    "orientation"}
            for level in (1, 2, 3, 4)}

    def build(self, level, rng):
        for _ in range(500):
            p = self.candidate(level, rng)
            try:
                self.check_rules(p, level)
            except ValueError:
                continue
            p["orientation"] = figures.choose_orientation(
                rng, lambda orientation: scene(dict(p, orientation=orientation)))
            return p
        raise ValueError("Could not build a shape-area question")

    def candidate(self, level, rng):
        p = {"top": 0, "offset": 0, "slant": 0, "unknown": "area", "orientation": [0, False]}
        if level == 1:
            p.update(shape=rng.choice(("triangle", "parallelogram")),
                     base=rng.randint(4, 20), height=rng.randint(3, 15))
        elif level == 2:
            top = rng.randint(3, 12)
            p.update(shape="trapezium", top=top, base=top + rng.randint(2, 12),
                     height=rng.randint(2, 12))
        elif level == 3:
            shape = rng.choice(SHAPES)
            height, offset, slope = rng.choice(TRIPLES)
            p.update(shape=shape, height=height, offset=offset, slant=slope)
            if shape == "triangle":
                p["base"] = offset + rng.randint(1, 12)
            elif shape == "parallelogram":
                p["base"] = rng.randint(4, 20)
            else:
                p["top"] = rng.randint(3, 10)
                p["base"] = p["top"] + offset + rng.randint(0, 6)
        else:
            shape = rng.choice(SHAPES)
            p["shape"] = shape
            p["height"] = rng.randint(3, 12)
            if shape == "trapezium":
                p["top"] = rng.randint(3, 12)
                p["base"] = p["top"] + rng.randint(2, 10)
            else:
                p["base"] = rng.randint(4, 20)
            p["unknown"] = rng.choice(REVERSE_UNKNOWNS[shape])
        return p

    def check_rules(self, p, level):
        require(p["shape"] in SHAPES, "Unknown shape")
        require(figures.valid_orientation(p["orientation"]), "Unknown orientation")
        for name in ("base", "top", "height", "offset", "slant"):
            require(type(p[name]) is int and p[name] >= 0, "Lengths must be whole numbers")
        require(3 <= p["base"] <= 30 and 2 <= p["height"] <= 15, "Length outside bounds")
        trapezium = p["shape"] == "trapezium"
        require((3 <= p["top"] < p["base"]) if trapezium else p["top"] == 0, "Invalid parallel side")
        if level == 1:
            require(p["shape"] in ("triangle", "parallelogram"), "Level 1 uses triangles or parallelograms")
        if level == 2:
            require(trapezium, "Level 2 uses trapezia")
        if level == 3:
            require([p["height"], p["offset"], p["slant"]] in [list(t) for t in TRIPLES],
                    "Sloping side must come from a listed triple")
            if p["shape"] == "triangle":
                require(p["offset"] < p["base"], "Apex must lie above the base")
            if trapezium:
                require(p["base"] >= p["top"] + p["offset"], "Trapezium offsets do not fit")
        else:
            require(p["offset"] == 0 and p["slant"] == 0, "No sloping side at this level")
        if level == 4:
            require(p["unknown"] in REVERSE_UNKNOWNS[p["shape"]], "Unknown length outside this shape")
        else:
            require(p["unknown"] == "area", "Levels 1 to 3 ask for the area")
        area = area_of(p)
        require(area.denominator == 1 and area <= MAX_AREA, "Area must be a whole number within bounds")

    def parts(self, p, level):
        area = area_of(p)
        if level == 4:
            instruction = "The area of the {} is {} cm². Find the length x.".format(
                p["shape"], area.numerator)
            value = p[p["unknown"]]
            answer = {"kind": "measure", "value": value, "unit": "cm"}
            shown = Content("x = {} cm".format(value), r"x = " + str(value) + r"\ \mathrm{cm}")
        else:
            instruction = "Calculate the area of the {}.".format(p["shape"])
            value = area.numerator
            answer = {"kind": "measure", "value": value, "unit": "cm^2"}
            shown = Content("{} cm²".format(value), str(value) + r"\ \mathrm{cm}^{2}")
        return {
            "prompt": Content(instruction + " " + described(p), display_text=instruction),
            "question_visuals": [scene(p)],
            "answer": answer, "answer_display": shown,
            "marks": {1: 2, 2: 2, 3: 2, 4: 3}[level],
            "working_lines": {1: 3, 2: 3, 3: 3, 4: 4}[level],
        }

    def validate_independently(self, question):
        """Shoelace area on coordinates; level 4 solves for the unknown."""
        import sympy
        p, level = question.parameters, question.difficulty
        values = {name: sympy.Integer(p[name]) for name in ("base", "top", "height")}
        unknown = p["unknown"]
        if level == 4:
            values[unknown] = sympy.Symbol("x", positive=True)
        b, a, h = values["base"], values["top"], values["height"]
        o = sympy.Integer(p["offset"])
        if p["shape"] == "triangle":
            corners = [(0, 0), (b, 0), (o, h)]
        elif p["shape"] == "parallelogram":
            corners = [(0, 0), (b, 0), (b + o, h), (o, h)]
        else:
            left = (b - a - o) if p["offset"] else (b - a) / 2
            corners = [(0, 0), (b, 0), (left + a, h), (left, h)]
        shoelace = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2)
                       in zip(corners, corners[1:] + corners[:1])) / 2
        if p["slant"]:
            require(p["slant"] ** 2 == p["offset"] ** 2 + p["height"] ** 2,
                    "Sloping side inconsistent with the height")
        if level == 4:
            given_area = int(question.prompt.display_text.split(" is ")[1].split(" ")[0])
            solutions = sympy.solve(sympy.Eq(shoelace, given_area), values[unknown])
            require(solutions == [question.answer["value"]], "Independent reverse length disagrees")
        else:
            require(sympy.simplify(shoelace - question.answer["value"]) == 0,
                    "Independent shoelace area disagrees")
        return True