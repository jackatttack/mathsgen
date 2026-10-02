"""Applied forms for geometry.volume.curved_solids: solids on a hemisphere.

L1 cone_hemisphere_volume  a cone on a hemisphere: the total volume in terms of pi
L3 cone_hemisphere_height  the total volume is given (a multiple of pi): find
                           the total height, to 3 significant figures
L4 frustum_density         a frustum (a cone with its tip removed) on a
                           hemisphere, two densities: the average density

Lengths are stored in tenths of a centimetre and volumes as coefficients of
pi (Fractions), so check() is exact until the final rounding. Every diagram
is drawn at true proportions by solid_figures.topped_hemisphere_scene and
must pass the shared label checks while the question is being built.

validate_independently() integrates cross-sections with Simpson's rule (exact
for these profiles) and finds the reverse height by bisection, never by
rearranging the volume formula.
"""
import math
from decimal import ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction

from . import rich_blocks as rb
from . import solid_figures as solids
from . import worded
from .core import Content, rational_text, require
from .worded import Context


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {1: 0.3, 2: 0.3, 3: 0.35, 4: 0.4}
MARKS = {1: 3, 2: 4, 3: 5, 4: 5}
WORKING_LINES = {1: 6, 2: 7, 3: 9, 4: 10}

FRUSTUM_SCALES = (Fraction(1, 2), Fraction(1, 3), Fraction(2, 3), Fraction(1, 4))
BUILD_ATTEMPTS = 200


def context_share(level):
    return CONTEXT_SHARE.get(level, 0.0)


# ------------------------------------------------------------------ helpers

def tenths_text(tenths):
    return str(tenths // 10) if tenths % 10 == 0 else "{}.{}".format(tenths // 10, tenths % 10)


def cm(tenths):
    return tenths_text(tenths) + " cm"


def three_sf(value):
    """value rounded half up to 3 significant figures, as text."""
    value = Fraction(value)
    require(Fraction(1, 10) <= value < 1000, "Value outside the rounding range")
    with localcontext() as context:
        context.prec = 40
        exact = Decimal(value.numerator) / Decimal(value.denominator)
        step = Decimal(1).scaleb(exact.adjusted() - 2)
        return str(exact.quantize(step, rounding=ROUND_HALF_UP))


def whole_in(value, low, high, message):
    require(type(value) is int and low <= value <= high, message)
    return value


def formulae():
    from .curved_solids import formula_blocks
    return formula_blocks("cone_volume", "sphere_volume")


def assembled(blocks):
    from .curved_solids import content
    return content(blocks)


def pi_piece(coefficient):
    from .curved_solids import pi_parts
    return pi_parts(Fraction(coefficient))


def hemisphere_coefficient(radius):
    return Fraction(2, 3) * radius ** 3


def cone_coefficient(radius, height):
    return Fraction(1, 3) * radius ** 2 * height


def build_until_drawable(make):
    """Draw parameters until their diagram passes the shared label checks."""
    for _ in range(BUILD_ATTEMPTS):
        p = make()
        try:
            scene = diagram(p)
        except ValueError:
            continue
        if solids.labels_ok(scene):
            return p
    raise ValueError("Could not draw a clear composite solid")


def diagram(p):
    if p["context"] == "cone_hemisphere_volume":
        radius = Fraction(p["diameter"], 2)
        return solids.topped_hemisphere_scene(
            float(radius), p["height"], width_label="{} cm".format(p["diameter"]),
            top_label="{} cm".format(p["height"]))
    if p["context"] == "cone_hemisphere_surface":
        radius, height, _ = surface_dimensions(p)
        return solids.topped_hemisphere_scene(
            radius, height, width_label="{} cm".format(2 * radius),
            top_label="{} cm".format(height))
    if p["context"] == "cone_hemisphere_height":
        radius = Fraction(p["diameter"], 2)
        return solids.topped_hemisphere_scene(
            float(radius), float(cone_height_from_volume(p)),
            width_label="{} cm".format(p["diameter"]), total_label="y cm")
    radius = Fraction(p["diameter_tenths"], 20)
    cone = Fraction(p["cone_tenths"], 10)
    scale = Fraction(p["removed_tenths"], p["cone_tenths"])
    return solids.topped_hemisphere_scene(
        float(radius), float(cone), scale=float(scale), width_label=cm(p["diameter_tenths"]),
        top_label=cm(p["cone_tenths"] - p["removed_tenths"]))


# ------------------------------------------- L1: total volume in terms of pi

def build_volume(rng):
    return build_until_drawable(lambda: {
        "context": "cone_hemisphere_volume", "diameter": rng.randint(4, 16),
        "height": rng.randint(3, 15)})


def check_volume(p):
    diameter = whole_in(p["diameter"], 4, 16, "Diameter out of bounds")
    height = whole_in(p["height"], 3, 15, "Height out of bounds")
    radius = Fraction(diameter, 2)
    return hemisphere_coefficient(radius) + cone_coefficient(radius, height)


def parts_volume(p):
    coefficient = check_volume(p)
    from .curved_solids import in_terms_of_pi
    blocks = [rb.prose(
        "A solid is made from a cone on top of a hemisphere. The base of the cone and the "
        "hemisphere both have diameter {} cm. The perpendicular height of the cone is {} "
        "cm.".format(p["diameter"], p["height"]))]
    blocks += formulae()
    blocks.append(in_terms_of_pi("Work out the total volume of the solid."))
    tex, text = pi_piece(coefficient)
    return {"prompt": assembled(blocks),
            "answer": {"kind": "pi_multiple", "coefficient": rational_text(coefficient)},
            "answer_display": Content(text + " cm³", tex + r"\ \mathrm{cm}^{3}"),
            "question_visuals": (diagram(p),)}


# --------------------------------------------- L3: total height from the volume

def cone_height_from_volume(p):
    radius = Fraction(p["diameter"], 2)
    return (Fraction(p["volume"]) - hemisphere_coefficient(radius)) / (radius ** 2 / 3)


def build_height(rng):
    def make():
        diameter = rng.randint(4, 14)
        radius = Fraction(diameter, 2)
        target = rng.randint(4, 16)
        volume = int(round(hemisphere_coefficient(radius) + cone_coefficient(radius, target)))
        return {"context": "cone_hemisphere_height", "diameter": diameter, "volume": volume}
    return build_until_drawable(make)


def check_height(p):
    whole_in(p["diameter"], 4, 14, "Diameter out of bounds")
    whole_in(p["volume"], 10, 3000, "Volume out of bounds")
    cone_height = cone_height_from_volume(p)
    require(3 <= cone_height <= 18, "Cone height out of bounds")
    total = cone_height + Fraction(p["diameter"], 2)
    return three_sf(total)


def parts_height(p):
    answer = check_height(p)
    blocks = [
        rb.prose("A solid cone is joined to a solid hemisphere to make the solid shown."),
        rb.prose("The diameter of the base of the cone is {d} cm. The diameter of the "
                 "hemisphere is {d} cm.".format(d=p["diameter"])),
        rb.paragraph(rb.text("The total volume of the solid is "),
                     rb.maths(r"%d\pi" % p["volume"], "%dπ" % p["volume"]),
                     rb.text(" cm³. The total height of the solid is y cm.")),
    ]
    blocks += formulae()
    blocks.append(rb.prose("Calculate the value of y. Give your answer correct to 3 "
                           "significant figures."))
    return {"prompt": assembled(blocks),
            "answer": {"kind": "rounded", "value": answer, "sf": 3, "unit": "cm"},
            "answer_display": Content("y = " + answer),
            "question_visuals": (diagram(p),)}


# ---------------------------------------- L2: total surface area in terms of pi

def surface_dimensions(p):
    """(radius, height, slant) from a Pythagorean triple; the slant is not shown."""
    from .curved_solids import TRIPLES
    whole_in(p["triple"], 0, len(TRIPLES) - 1, "Unknown triple")
    whole_in(p["scale"], 1, 3, "Scale out of bounds")
    require(p["swap"] in (0, 1), "Unknown swap")
    a, b, c = TRIPLES[p["triple"]]
    if p["swap"]:
        a, b = b, a
    radius, height, slant = a * p["scale"], b * p["scale"], c * p["scale"]
    require(2 <= radius <= 12 and 3 <= height <= 30, "Solid out of bounds")
    return radius, height, slant


def build_surface(rng):
    return build_until_drawable(lambda: {
        "context": "cone_hemisphere_surface", "triple": rng.randrange(5),
        "scale": rng.randint(1, 3), "swap": rng.randint(0, 1)})


def check_surface(p):
    radius, _, slant = surface_dimensions(p)
    # Curved cone surface plus the hemisphere's curved surface; no flat faces.
    return Fraction(radius * slant + 2 * radius * radius)


def parts_surface(p):
    coefficient = check_surface(p)
    radius, height, _ = surface_dimensions(p)
    from .curved_solids import formula_blocks, in_terms_of_pi
    blocks = [rb.prose(
        "A solid is made from a cone on top of a hemisphere. The base of the cone and the "
        "hemisphere both have diameter {} cm. The perpendicular height of the cone is {} "
        "cm.".format(2 * radius, height))]
    blocks += formula_blocks("cone_curved", "sphere_area")
    blocks.append(in_terms_of_pi("Work out the total surface area of the solid."))
    tex, text = pi_piece(coefficient)
    return {"prompt": assembled(blocks),
            "answer": {"kind": "pi_multiple", "coefficient": rational_text(coefficient)},
            "answer_display": Content(text + " cm²", tex + r"\ \mathrm{cm}^{2}"),
            "question_visuals": (diagram(p),)}


# ------------------------------------------------- L4: frustum density

def build_density(rng):
    def make():
        scale = rng.choice(FRUSTUM_SCALES)
        cone_tenths = scale.denominator * rng.randint(40 // scale.denominator + 1,
                                                      120 // scale.denominator)
        densities = rng.sample(range(10, 120), 2)
        return {"context": "frustum_density", "diameter_tenths": 2 * rng.randint(20, 60),
                "cone_tenths": cone_tenths,
                "removed_tenths": int(cone_tenths * scale),
                "frustum_density_tenths": densities[0],
                "hemisphere_density_tenths": densities[1]}
    return build_until_drawable(make)


def density_parts(p):
    diameter = whole_in(p["diameter_tenths"], 40, 120, "Diameter out of bounds")
    cone = whole_in(p["cone_tenths"], 40, 120, "Cone height out of bounds")
    removed = whole_in(p["removed_tenths"], 10, cone - 10, "Removed height out of bounds")
    require(Fraction(removed, cone) in FRUSTUM_SCALES, "Unsupported frustum scale")
    first = whole_in(p["frustum_density_tenths"], 10, 119, "Density out of bounds")
    second = whole_in(p["hemisphere_density_tenths"], 10, 119, "Density out of bounds")
    require(first != second, "The two densities differ")
    radius = Fraction(diameter, 20)
    height = Fraction(cone, 10)
    scale = Fraction(removed, cone)
    frustum = cone_coefficient(radius, height) * (1 - scale ** 3)
    hemisphere = hemisphere_coefficient(radius)
    return frustum, hemisphere, Fraction(first, 10), Fraction(second, 10)


def check_density(p):
    frustum, hemisphere, first, second = density_parts(p)
    return three_sf((first * frustum + second * hemisphere) / (frustum + hemisphere))


def parts_density(p):
    answer = check_density(p)
    d, cone, removed = p["diameter_tenths"], p["cone_tenths"], p["removed_tenths"]
    blocks = [
        rb.prose("The frustum shown is made by removing a cone of height {} from a solid "
                 "cone of height {} and base diameter {}.".format(cm(removed), cm(cone), cm(d))),
        rb.prose("The frustum is joined to a solid hemisphere of diameter {} to form the "
                 "solid S.".format(cm(d))),
        rb.prose("The density of the frustum is {} g/cm³. The density of the hemisphere is "
                 "{} g/cm³.".format(tenths_text(p["frustum_density_tenths"]),
                                    tenths_text(p["hemisphere_density_tenths"]))),
    ]
    blocks += formulae()
    blocks.append(rb.prose("Calculate the average density of solid S. Give your answer "
                           "correct to 3 significant figures."))
    return {"prompt": assembled(blocks),
            "answer": {"kind": "rounded", "value": answer, "sf": 3, "unit": "g/cm³"},
            "answer_display": Content(answer + " g/cm³"),
            "question_visuals": (diagram(p),)}


# ----------------------------------------------------------------- registry

CONTEXTS = {
    "cone_hemisphere_volume": Context(
        1, frozenset({"context", "diameter", "height"}),
        build_volume, check_volume, parts_volume, None),
    "cone_hemisphere_surface": Context(
        2, frozenset({"context", "triple", "scale", "swap"}),
        build_surface, check_surface, parts_surface, None),
    "cone_hemisphere_height": Context(
        3, frozenset({"context", "diameter", "volume"}),
        build_height, check_height, parts_height, None),
    "frustum_density": Context(
        4, frozenset({"context", "diameter_tenths", "cone_tenths", "removed_tenths",
                      "frustum_density_tenths", "hemisphere_density_tenths"}),
        build_density, check_density, parts_density, None),
}


# ------------------------------------------------ generate and validate

def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def simpson(f, low, high, steps=200):
    width = (high - low) / steps
    total = f(low) + f(high)
    for i in range(1, steps):
        total += (4 if i % 2 else 2) * f(low + i * width)
    return total * width / 3


def hemisphere_volume(radius):
    return simpson(lambda y: math.pi * (radius * radius - y * y), -radius, 0)


def cone_slice_volume(radius, height, top):
    """Volume of a cone of the given radius and height, from its base up to top."""
    return simpson(lambda y: math.pi * (radius * (1 - y / height)) ** 2, 0, top)


def half_step(value):
    return 10 ** (math.floor(math.log10(value)) - 2) / 2


def validate_independently(q):
    p, answer = q.parameters, q.answer
    if p["context"] == "cone_hemisphere_volume":
        radius = p["diameter"] / 2
        expected = hemisphere_volume(radius) + cone_slice_volume(radius, p["height"], p["height"])
        stated = float(Fraction(answer["coefficient"])) * math.pi
        require(abs(expected - stated) <= 1e-9 * expected, "Independent volume disagrees")
        return True
    if p["context"] == "cone_hemisphere_surface":
        from .curved_solids import TRIPLES
        a, b, _ = TRIPLES[p["triple"]]
        if p["swap"]:
            a, b = b, a
        r, h = a * p["scale"], b * p["scale"]
        # Surface of revolution for the cone; Archimedes for the hemisphere.
        cone = simpson(lambda y: 2 * math.pi * r * (1 - y / h) * math.sqrt(1 + (r / h) ** 2),
                       0, h)
        expected = cone + 2 * math.pi * r * r
        stated = float(Fraction(answer["coefficient"])) * math.pi
        require(abs(expected - stated) <= 1e-9 * expected, "Independent surface disagrees")
        return True
    stated = float(answer["value"])
    if p["context"] == "cone_hemisphere_height":
        radius = p["diameter"] / 2
        target = p["volume"] * math.pi
        low, high = 0.001, 200.0
        for _ in range(200):
            middle = (low + high) / 2
            if hemisphere_volume(radius) + cone_slice_volume(radius, middle, middle) < target:
                low = middle
            else:
                high = middle
        expected = low + radius
    else:
        radius = p["diameter_tenths"] / 20
        cone = p["cone_tenths"] / 10
        top = (p["cone_tenths"] - p["removed_tenths"]) / 10
        frustum = cone_slice_volume(radius, cone, top)
        hemisphere = hemisphere_volume(radius)
        expected = ((p["frustum_density_tenths"] / 10) * frustum
                    + (p["hemisphere_density_tenths"] / 10) * hemisphere) / (frustum + hemisphere)
    require(abs(expected - stated) <= half_step(stated) * 1.001 + 1e-9,
            "Independent value disagrees")
    return True