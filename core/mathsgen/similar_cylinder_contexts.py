"""Similar cylinders: square and cube scaling, then linked ratios.

All solids have the same density. Parameters store the displayed givens;
length ratios are recovered using exact integer roots, never float roots.
The existing cylinder renderer supplies the outlines.
"""
import math
from fractions import Fraction

from .core import Content, require
from . import figures, solid_figures, worded

CONTEXT_SHARE = {1: 0.0, 2: 0.35, 3: 0.35, 4: 0.45}
PAIRS = ((2, 3), (3, 4), (2, 5), (3, 5), (4, 5))
NAMES = ("ABC", "PQR", "XYZ", "KLM")
MARKS = {2: 2, 3: 3, 4: 5}
WORKING_LINES = {2: 4, 3: 5, 4: 7}


def simplified(values):
    divisor = 0
    for value in values:
        divisor = math.gcd(divisor, value)
    return [value // divisor for value in values]


def exact_root(value, power):
    """Small positive integer root of a reduced ratio component."""
    for candidate in range(1, 21):
        if candidate ** power == value:
            return candidate
        if candidate ** power > value:
            break
    raise ValueError("Ratio is not a perfect power")


def linear_ratio(values, power):
    reduced = simplified(values)
    return [exact_root(value, power) for value in reduced]


def given_pair(values, maximum):
    require(isinstance(values, list) and len(values) == 2
            and all(type(v) is int and 1 <= v <= maximum for v in values),
            "Expected two positive whole-number givens")


def check_lengths(p):
    given_pair(p["heights"], 6)
    require(tuple(p["heights"]) in PAIRS, "Height ratio outside bounds")
    return simplified([v ** 3 for v in p["heights"]])


def check_masses(p):
    given_pair(p["masses"], 10000)
    lengths = linear_ratio(p["masses"], 3)
    require(tuple(lengths) in PAIRS, "Mass ratio outside useful bounds")
    require(p["masses"][0] != p["masses"][1], "Equal masses make a trivial problem")
    return lengths


def check_three(p):
    given_pair(p["masses"], 10000)
    given_pair(p["areas"], 10000)
    ab = linear_ratio(p["masses"], 3)
    bc = linear_ratio(p["areas"], 2)
    require(tuple(ab) in PAIRS and tuple(bc) in PAIRS,
            "Linked ratios outside bounds")
    result = simplified([ab[0] * bc[0], ab[1] * bc[0], ab[1] * bc[1]])
    require(Fraction(max(result), min(result)) <= 3,
            "Cylinder sizes too disparate for the diagram")
    return result


def check(p):
    require(p["names"] in NAMES, "Unknown cylinder names")
    function = {
        "cylinder_height_to_mass": check_lengths,
        "cylinder_mass_to_height": check_masses,
        "three_cylinder_ratios": check_three,
    }[p["context"]]
    return function(p)


def build_lengths(rng):
    return dict(context="cylinder_height_to_mass", names=rng.choice(NAMES),
                heights=list(rng.choice(PAIRS)))


def build_masses(rng):
    a, b = rng.choice(PAIRS)
    factor = rng.randint(2, 9)
    return dict(context="cylinder_mass_to_height", names=rng.choice(NAMES),
                masses=[factor * a ** 3, factor * b ** 3])


def build_three(rng):
    a, b = rng.choice(PAIRS)
    d, e = rng.choice(PAIRS)
    mass_factor, area_factor = rng.randint(2, 9), rng.randint(3, 12)
    return dict(context="three_cylinder_ratios", names=rng.choice(NAMES),
                masses=[mass_factor * a ** 3, mass_factor * b ** 3],
                areas=[area_factor * d ** 2, area_factor * e ** 2])


def lengths_for_diagram(p):
    if p["context"] == "cylinder_height_to_mass":
        return p["heights"]
    return check(p)


def diagram(p):
    """Compose existing cylinder outlines at one common scale.

    No lengths are labelled: all givens live in the prompt. Identity labels
    sit below the solids and keep their normal text size at narrow widths.
    """
    ratios = lengths_for_diagram(p)
    template = solid_figures.cylinder_scene(3, 7)
    count = len(ratios)
    nodes = []
    common = 130 / (template["height"] * max(ratios))
    for index, length in enumerate(ratios):
        scale = common * length
        centre_x = (index + 0.5) * 360 / count

        def position(point):
            return figures.rounded((
                centre_x + (point[0] - 180) * scale,
                175 + (point[1] - template["height"]) * scale))

        for original in template["nodes"]:
            node = dict(original)
            if "points" in node:
                node["points"] = [position(pt) for pt in node["points"]]
            for key in ("center", "point", "vertex", "first", "second"):
                if key in node:
                    node[key] = position(node[key])
            if "radius" in node:
                node["radius"] *= scale
            nodes.append(node)
        nodes.append({"type": "label", "point": [centre_x, 200],
                      "text": p["names"][index]})
    return {"kind": "scene", "version": 1, "width": 360, "height": 225,
            "caption": "Not drawn accurately", "nodes": nodes}


def parts(p):
    result = check(p)
    a, b, c = p["names"]
    form = p["context"]
    count = 3 if form == "three_cylinder_ratios" else 2
    lead = ("Solid cylinders {} are mathematically similar and made from "
            "the same material, with the same density. ").format(
                "{} and {}".format(a, b) if count == 2 else "{}, {} and {}".format(a, b, c))
    if form == "cylinder_height_to_mass":
        h1, h2 = p["heights"]
        lead += ("Their heights are in the ratio {a}:{b} = {h1}:{h2}. "
                 "Find the ratio of their masses, {a}:{b}, in its simplest form.").format(
                     a=a, b=b, h1=h1, h2=h2)
    elif form == "cylinder_mass_to_height":
        m1, m2 = p["masses"]
        lead += ("Cylinder {a} has mass {m1} g and cylinder {b} has mass {m2} g. "
                 "Find the ratio of their heights, {a}:{b}, in its simplest form.").format(
                     a=a, b=b, m1=m1, m2=m2)
    else:
        m1, m2 = p["masses"]
        area1, area2 = p["areas"]
        lead += (
            "Cylinder {a} has mass {m1} g and cylinder {b} has mass {m2} g. "
            "The total surface areas of {b} and {c} are in the ratio "
            "{area1}:{area2}. Find the ratio of the heights of {a}, {b} and {c}, "
            "in its simplest form."
        ).format(a=a, b=b, c=c, m1=m1, m2=m2, area1=area1, area2=area2)
    return dict(prompt=Content(lead),
                answer={"kind": "ratio", "values": result},
                answer_display=Content(":".join(str(v) for v in result)),
                question_visuals=(diagram(p),))


def independent(q):
    """Check the answer by cross multiplication of powers of the givens."""
    p = q.parameters
    values = q.answer.get("values")
    count = 3 if p["context"] == "three_cylinder_ratios" else 2
    require(isinstance(values, list) and len(values) == count
            and all(type(v) is int and v > 0 for v in values),
            "Expected a positive integer ratio")
    require(values == simplified(values), "Ratio must be in simplest form")
    a, b = values[:2]
    if p["context"] == "cylinder_height_to_mass":
        h1, h2 = p["heights"]
        require(a * h2 ** 3 == b * h1 ** 3, "Mass scaling disagrees")
    else:
        m1, m2 = p["masses"]
        require(a ** 3 * m2 == b ** 3 * m1, "Height/mass invariant disagrees")
        if count == 3:
            area1, area2 = p["areas"]
            c = values[2]
            require(b ** 2 * area2 == c ** 2 * area1,
                    "Height/surface-area invariant disagrees")
    return True


CONTEXTS = {
    "cylinder_height_to_mass": worded.Context(
        2, {"context", "names", "heights"}, build_lengths, check, parts, independent),
    "cylinder_mass_to_height": worded.Context(
        3, {"context", "names", "masses"}, build_masses, check, parts, independent),
    "three_cylinder_ratios": worded.Context(
        4, {"context", "names", "masses", "areas"}, build_three, check, parts, independent),
}


def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    return independent(q)