"""Prism and cylinder volumes drawn to true proportion, with linked forms.

Forms (two per level):
  1  cuboid / triangle                    direct volume
  2  trapezium / cylinder                 right-trapezium cross-section; pi r^2 h
  3  triangle_pythagoras / cylinder_diameter
                                          find a leg by Pythagoras first; halve a
                                          diameter first
  4  missing / litres                     recover a dimension; capacity in litres
Solids are drawn by solid_figures at their true proportions with a seeded
depth direction; presentation choices (triangle corner, trapezium side) are
stored in "style". The independent check computes the cross-section by the
shoelace formula on its own coordinates.
An L-shaped prism form was tried and dropped: its non-convex face needs
real hidden-line removal.
scene_for and LABEL_ANCHORS below are legacy, kept only for
related_solids.py until it is upgraded.
"""
import math
from fractions import Fraction

from . import solid_figures
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)
from .circle_measures import exact_root, pi_expression
from .rounding import decimal_text


INFO = GeneratorInfo(
    id="geometry.volume.prisms", version=3,
    topic="geometry", subtopic="volume",
    title="Prism and cylinder volumes",
    difficulty_descriptions={
        1: "Find the volume of a cuboid or a right triangular prism.",
        2: "Find the volume of a trapezium prism or a cylinder.",
        3: "Find a missing leg by Pythagoras, or start a cylinder from its diameter.",
        4: "Recover a missing dimension, or give a capacity in litres.",
    },
    tags=("geometry", "volume", "prisms", "cylinders", "reverse"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("cuboid", "triangle"),
    2: ("trapezium", "cylinder"),
    3: ("triangle_pythagoras", "cylinder_diameter"),
    4: ("missing", "litres"),
}
SHAPE_OF = {"cuboid": "cuboid", "triangle": "triangle", "trapezium": "trapezium",
            "cylinder": "cylinder", "triangle_pythagoras": "triangle_p",
            "cylinder_diameter": "cylinder_d", "litres": "cuboid"}
DIMENSIONS = {
    "cuboid": ("width", "height", "length"),
    "triangle": ("base", "height", "length"),
    "triangle_p": ("base", "hypotenuse", "length"),
    "trapezium": ("a", "b", "height", "length"),
    "cylinder": ("radius", "length"),
    "cylinder_d": ("diameter", "length"),
}
TRIPLES = ((3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17), (9, 12, 15))
MISSING_SHAPES = ("cuboid", "triangle", "trapezium", "cylinder")
NAMES = {"cuboid": "cuboid", "triangle": "right triangular prism",
         "triangle_p": "right triangular prism",
         "trapezium": "prism with a trapezium cross-section",
         "cylinder": "cylinder", "cylinder_d": "cylinder"}
WORDS = {"width": "width", "height": "height", "length": "length", "base": "base",
         "hypotenuse": "hypotenuse", "a": "shorter parallel side",
         "b": "longer parallel side", "radius": "radius", "diameter": "diameter"}
MARKS = {1: 2, 2: 3, 3: 3, 4: 4}


# ------------------------------------------------------------ mathematics

def other_leg(base, hypotenuse):
    return exact_root(Fraction(hypotenuse) ** 2 - Fraction(base) ** 2)


def full_dimensions(p):
    d = {key: Fraction(value) for key, value in p["dims"].items()}
    if p["form"] == "missing":
        d[p["wanted"]] = missing_dimension(p)
    return d


def volume_of(shape, d):
    if shape == "cuboid":
        return d["width"] * d["height"] * d["length"]
    if shape == "triangle":
        return d["base"] * d["height"] * d["length"] / 2
    if shape == "triangle_p":
        return d["base"] * other_leg(d["base"], d["hypotenuse"]) * d["length"] / 2
    if shape == "trapezium":
        return (d["a"] + d["b"]) * d["height"] * d["length"] / 2
    if shape == "cylinder":
        return d["radius"] ** 2 * d["length"]
    return (d["diameter"] / 2) ** 2 * d["length"]


def missing_dimension(p):
    shape, wanted = p["shape"], p["wanted"]
    d = {key: Fraction(value) for key, value in p["dims"].items()}
    volume = Fraction(p["volume"])
    if shape == "cylinder" and wanted == "radius":
        return exact_root(volume / d["length"])
    if shape == "trapezium" and wanted in ("a", "b"):
        other = "b" if wanted == "a" else "a"
        return 2 * volume / (d["height"] * d["length"]) - d[other]
    d[wanted] = Fraction(1)
    return volume / volume_of(shape, d)


def answer_for(p):
    form, shape = p["form"], p["shape"]
    if form == "missing":
        return {"kind": "exact_measure", "value": rational_text(missing_dimension(p)),
                "pi": False, "unit": "cm"}
    volume = volume_of(shape, full_dimensions(p))
    if form == "litres":
        return {"kind": "exact_measure", "value": rational_text(volume / 1000),
                "pi": False, "unit": "litres"}
    return {"kind": "exact_measure", "value": rational_text(volume),
            "pi": shape in ("cylinder", "cylinder_d"), "unit": "cm^3"}


def measure_text(value, uses_pi, tex=False):
    """Pi multiples stay exact; other measures here always terminate, so use decimals."""
    if uses_pi:
        return pi_expression(0, value, tex)
    return decimal_text(Fraction(value))


def display_for(answer):
    if answer["unit"] == "litres":
        text = decimal_text(Fraction(answer["value"])) + " litres"
        return Content(text, text)
    plain = measure_text(answer["value"], answer["pi"])
    tex = measure_text(answer["value"], answer["pi"], True)
    unit_tex = r"\ \mathrm{cm}^{3}" if answer["unit"] == "cm^3" else r"\ \mathrm{cm}"
    return Content(plain + " " + answer["unit"], tex + unit_tex)


def check_parameters(p, level):
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(form in FORMS[level], "Unexpected form for this level")
    keys = {"form", "shape", "dims", "style", "mirror"}
    if form == "missing":
        keys |= {"wanted", "volume"}
    require(set(p) == keys, "Unexpected parameters")
    require(type(p["mirror"]) is bool, "Invalid depth direction")
    shape = p["shape"]
    if form == "missing":
        require(shape in MISSING_SHAPES and p["wanted"] in DIMENSIONS[shape],
                "Invalid missing-dimension task")
        expected = set(DIMENSIONS[shape]) - {p["wanted"]}
        volume = Fraction(p["volume"])
        require(volume > 0 and rational_text(volume) == p["volume"], "Invalid volume")
    else:
        require(shape == SHAPE_OF[form], "Shape does not match the form")
        expected = set(DIMENSIONS[shape])
    d = p["dims"]
    require(isinstance(d, dict) and set(d) == expected, "Wrong given dimensions")
    require(all(type(v) is int and v > 0 for v in d.values()), "Whole dimensions required")
    full = full_dimensions(p)
    if form == "missing":
        value = full[p["wanted"]]
        require(value.denominator == 1 and 3 <= value <= 15, "Missing dimension outside bounds")
    if form == "litres":
        require(all(10 <= v <= 60 and v % 5 == 0 for v in d.values()), "Tank outside bounds")
    elif shape == "triangle_p":
        require(full["base"] < full["hypotenuse"] <= 17, "Hypotenuse must be the longest side")
        leg = other_leg(full["base"], full["hypotenuse"])
        require(leg.denominator == 1 and 3 <= leg <= 15 and 3 <= full["base"] <= 15
                and 3 <= full["length"] <= 15, "Triangle outside bounds")
    elif shape == "cylinder_d":
        require(full["diameter"] % 2 == 0 and 4 <= full["diameter"] <= 24
                and 3 <= full["length"] <= 15, "Cylinder outside bounds")
    else:
        require(all(3 <= v <= 15 for v in full.values()), "Dimension outside bounds")
    style = p["style"]
    if shape in ("triangle", "triangle_p"):
        require(set(style) == {"corner"} and style["corner"] in ("left", "right"),
                "Invalid triangle style")
    elif shape == "trapezium":
        require(full["a"] < full["b"], "Parallel sides must differ")
        inset = style.get("inset")
        require(set(style) == {"inset"} and type(inset) is int
                and inset in (0, full["b"] - full["a"]), "Invalid trapezium inset")
    else:
        require(style == {}, "Unexpected style")


# ------------------------------------------------------------ presentation

def label_texts(p):
    texts = {key: "{} cm".format(value) for key, value in p["dims"].items()}
    if p["form"] == "missing":
        texts[p["wanted"]] = "x"
    return texts


def section_for(shape, d, style):
    """Cross-section vertices (y up), edge-label map and right-angle vertices."""
    if shape == "cuboid":
        w, h = float(d["width"]), float(d["height"])
        return [(0, 0), (w, 0), (w, h), (0, h)], {"width": 0, "height": 3}, ()
    if shape in ("triangle", "triangle_p"):
        b = float(d["base"])
        h = float(d["height"] if shape == "triangle" else other_leg(d["base"], d["hypotenuse"]))
        left = style["corner"] == "left"
        points = [(0, 0), (b, 0), (0, h)] if left else [(0, 0), (b, 0), (b, h)]
        if shape == "triangle":
            return points, {"base": 0, "height": 2 if left else 1}, (0,) if left else (1,)
        return points, {"base": 0, "hypotenuse": 1 if left else 2}, (0,) if left else (1,)
    # Right trapeziums only: a slanted one puts hidden back edges across the
    # face, where an internal height label would sit.
    a, b, h = float(d["a"]), float(d["b"]), float(d["height"])
    if style["inset"] == 0:
        return ([(0, 0), (b, 0), (a, h), (0, h)],
                {"b": 0, "a": (2, True), "height": 3}, (0, 3))
    return ([(0, 0), (b, 0), (b, h), (b - a, h)],
            {"b": 0, "a": (2, True), "height": 1}, (1, 2))


def diagram_for(p):
    shape = p["shape"]
    texts = label_texts(p)
    d = full_dimensions(p)
    if shape in ("cylinder", "cylinder_d"):
        radius = d["radius"] if shape == "cylinder" else d["diameter"] / 2
        key = "radius" if shape == "cylinder" else "diameter"
        return solid_figures.cylinder_scene(float(radius), float(d["length"]),
                                            texts[key], texts["length"],
                                            diameter=shape == "cylinder_d")
    section, edges, right = section_for(shape, d, p["style"])
    if shape == "cuboid" and p["mirror"]:
        edges = {"width": 0, "height": 1}
    edge_labels = {}
    for key, where in edges.items():
        index, inward = where if isinstance(where, tuple) else (where, False)
        edge_labels[index] = (texts[key], inward)
    return solid_figures.prism_scene(section, float(d["length"]), edge_labels,
                                     texts["length"], p["mirror"], right)


def presentation(p):
    form, shape = p["form"], p["shape"]
    details = "; ".join("{} = {} cm".format(WORDS[key], value)
                        for key, value in p["dims"].items())
    if form == "litres":
        lead = ("A tank in the shape of a cuboid is shown. Find its capacity in litres. "
                "1 litre is 1000 cubic centimetres.")
        return Content(lead + " " + details + ".", display_text=lead)
    if form == "missing":
        lead = "The volume of the {} is given below. Find the {}, x.".format(
            NAMES[shape], WORDS[p["wanted"]])
        volume = measure_text(p["volume"], shape == "cylinder")
        tex = "V = " + measure_text(p["volume"], shape == "cylinder", True) + r"\ \mathrm{cm}^{3}"
        return Content(lead + " " + details + ". Its volume is " + volume + " cm^3.",
                       tex, display_text=lead)
    lead = "Find the volume of the {}.".format(NAMES[shape])
    if shape == "triangle_p":
        lead = ("The cross-section of this prism is a right-angled triangle. "
                "Find the volume of the prism.")
    if shape in ("cylinder", "cylinder_d"):
        lead += " Give your answer in terms of pi."
    return Content(lead + " " + details + ".", display_text=lead)


def draw(rng, level):
    form = rng.choice(FORMS[level])
    shape = rng.choice(MISSING_SHAPES) if form == "missing" else SHAPE_OF[form]
    p = {"form": form, "shape": shape, "style": {}, "mirror": rng.random() < 0.5}
    if form == "litres":
        d = {key: 5 * rng.randint(2, 12) for key in DIMENSIONS["cuboid"]}
    elif shape == "triangle_p":
        legs = list(rng.choice(TRIPLES))
        hypotenuse = legs.pop()
        d = {"base": rng.choice(legs), "hypotenuse": hypotenuse,
             "length": rng.randint(3, 15)}
    elif shape == "cylinder_d":
        d = {"diameter": 2 * rng.randint(2, 12), "length": rng.randint(3, 15)}
    else:
        d = {key: rng.randint(3, 15) for key in DIMENSIONS[shape]}
        if shape == "trapezium":
            d["a"], d["b"] = sorted(rng.sample(range(3, 16), 2))
    if shape in ("triangle", "triangle_p"):
        p["style"] = {"corner": rng.choice(("left", "right"))}
    if shape == "trapezium":
        p["style"] = {"inset": rng.choice((0, d["b"] - d["a"]))}
    if form == "missing":
        full = {key: Fraction(value) for key, value in d.items()}
        p["volume"] = rational_text(volume_of(shape, full))
        p["wanted"] = rng.choice(DIMENSIONS[shape])
        del d[p["wanted"]]
    p["dims"] = d
    return p


# ------------------------------------------------------------ generator

class PrismVolume:
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
            raise ValueError("Could not construct a prism-volume question")
        answer = answer_for(p)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=presentation(p), answer=answer,
            answer_display=display_for(answer), worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=4 if difficulty <= 2 else 5),
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
        """Shoelace cross-section area times length; diameter identity for cylinders."""
        p, answer = q.parameters, q.answer
        shape = p["shape"]
        d = {key: Fraction(value) for key, value in p["dims"].items()}
        if p["form"] == "missing":
            d[p["wanted"]] = Fraction(answer["value"])
            require(d[p["wanted"]] > 0, "Length must be positive")
        if shape in ("cylinder", "cylinder_d"):
            diameter = 2 * d["radius"] if shape == "cylinder" else d["diameter"]
            area = diameter * diameter / 4
        else:
            if shape == "cuboid":
                v = [(0, 0), (d["width"], 0), (d["width"], d["height"]), (0, d["height"])]
            elif shape == "triangle":
                v = [(0, 0), (d["base"], 0), (0, d["height"])]
            elif shape == "triangle_p":
                square = d["hypotenuse"] ** 2 - d["base"] ** 2
                leg = math.isqrt(int(square))
                require(leg * leg == square, "The other leg is not whole")
                v = [(0, 0), (d["base"], 0), (0, Fraction(leg))]
            else:
                v = [(0, 0), (d["b"], 0), (d["a"], d["height"]), (0, d["height"])]
            area = abs(sum(x1 * y2 - x2 * y1
                           for (x1, y1), (x2, y2) in zip(v, v[1:] + v[:1]))) / 2
        volume = area * d["length"]
        if p["form"] == "missing":
            require(volume == Fraction(p["volume"]), "Recovered dimension fails the volume")
        elif p["form"] == "litres":
            require(volume == 1000 * Fraction(answer["value"]) and answer["unit"] == "litres",
                    "Capacity disagrees")
        else:
            require(volume == Fraction(answer["value"]) and answer["unit"] == "cm^3",
                    "Volume disagrees")
        require(answer["pi"] == (shape in ("cylinder", "cylinder_d") and p["form"] != "missing"),
                "Incorrect pi factor")
        return True


# ------------------------------------------------------------ legacy (surface area v3)

LABEL_ANCHORS = {
    "cuboid": {"width": [145, 22], "height": [36, 92], "length": [285, 62]},
    "triangle": {"base": [145, 22], "height": [36, 92], "length": [285, 62],
                 "hypotenuse": [118, 76]},
    "trapezium": {"b": [145, 22], "a": [148, 128], "height": [126, 92], "length": [285, 62]},
    "cylinder": {"radius": [218, 174], "length": [290, 125]},
}


def scene_for(shape, labels=None):
    """Legacy schematic solids, used only by prism_surface_area v3."""
    nodes = []
    if shape == "cylinder":
        for y in (65, 185):
            points = [[180 + 75 * math.cos(2 * math.pi * i / 48),
                       y + 22 * math.sin(2 * math.pi * i / 48)] for i in range(48)]
            nodes.append({"type": "polygon", "points": points})
        for x in (105, 255):
            nodes.append({"type": "line", "points": [[x, 65], [x, 185]]})
        nodes.append({"type": "line", "points": [[180, 185], [255, 185]]})
        nodes.append({"type": "circle", "center": [180, 185], "radius": 1.6, "shade": True})
    else:
        front = {
            "cuboid": [[65, 40], [225, 40], [225, 145], [65, 145]],
            "triangle": [[65, 40], [225, 40], [65, 145]],
            "trapezium": [[65, 40], [225, 40], [190, 145], [100, 145]],
        }[shape]
        back = [[x + 65, y + 65] for x, y in front]
        nodes.extend([{"type": "polygon", "points": back},
                      {"type": "polygon", "points": front}])
        for first, second in zip(front, back):
            nodes.append({"type": "line", "points": [first, second]})
        if shape == "triangle":
            nodes.append({"type": "right_angle", "vertex": front[0],
                          "first": front[1], "second": front[2]})
    for key, text in sorted((labels or {}).items()):
        nodes.append({"type": "label", "point": LABEL_ANCHORS[shape][key], "text": text})
    return {"kind": "scene", "version": 1, "width": 360, "height": 250,
            "caption": "Not drawn accurately", "nodes": nodes}