"""Cones, spheres, hemispheres, pyramids and frustums.

Volume, surface area, density and reverse problems. Exact answers are held as
the coefficient of pi (a Fraction), so "in terms of pi" questions need no
calculator; rounded answers use 3 significant figures with boundary checks.
Where Edexcel supplies a formula (cone and sphere volume, sphere area, cone
curved surface), the prompt shows it as a display equation.

The independent check recomputes every volume and area by Simpson-rule
integration of cross-sections or surfaces of revolution, never the textbook
formula. Simpson's rule is exact for these polynomial profiles, so exact
answers are checked tightly.
"""
import math
from fractions import Fraction

from . import rich_blocks as rb
from . import solid_figures as solids
from .bearings import rounded_sig_figs, sig_figs_text
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


INFO = GeneratorInfo(
    id="geometry.volume.curved_solids", version=1,
    topic="geometry", subtopic="curved_solids",
    title="Cones, spheres, pyramids and frustums",
    difficulty_descriptions={
        1: "Find an exact volume in terms of pi, or a square-based pyramid's volume.",
        2: "Find a total surface area in terms of pi: a cone or a hemisphere.",
        3: "Find a radius from a volume, or a mass from a density.",
        4: "Find a frustum's volume, or a cone's height after melting a sphere.",
    },
    tags=("geometry", "volume", "surface area", "density", "solids"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("exact_volume", "pyramid_volume"),
    2: ("cone_surface", "hemisphere_surface"),
    3: ("reverse_radius", "density"),
    4: ("frustum", "recast"),
}
TRIPLES = ((3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17), (7, 24, 25))
FRUSTUM_SCALES = (Fraction(1, 2), Fraction(1, 3), Fraction(2, 3), Fraction(1, 4), Fraction(3, 4))
DENSITY_SOLIDS = ("sphere", "cone", "pyramid")
MARKS = {1: 2, 2: 4, 3: 3, 4: 5}
WORKING_LINES = {1: 4, 2: 7, 3: 6, 4: 9}

FORMULAE = {
    "cone_volume": (r"V = \frac{1}{3}\pi r^{2}h", "V = (1/3)πr^2 h"),
    "sphere_volume": (r"V = \frac{4}{3}\pi r^{3}", "V = (4/3)πr^3"),
    "sphere_area": (r"A = 4\pi r^{2}", "A = 4πr^2"),
    "cone_curved": (r"S = \pi rl", "S = πrl"),
}
KEYS = {
    "exact_volume": {"solid", "radius", "height"},
    "pyramid_volume": {"side", "height"},
    "cone_surface": {"triple", "scale", "swap"},
    "hemisphere_surface": {"radius"},
    "reverse_radius": {"solid", "volume", "height"},
    "density": {"solid", "size", "height", "density_tenths"},
    "frustum": {"radius", "height", "scale_num", "scale_den"},
    "recast": {"sphere_radius", "cone_radius"},
}


# ------------------------------------------------------------ mathematics

def cone_triple(par):
    """(radius, height, slant); swap exchanges the radius and height roles."""
    a, b, c = TRIPLES[par["triple"]]
    if par["swap"]:
        a, b = b, a
    return a * par["scale"], b * par["scale"], c * par["scale"]


def solid_volume(solid, size, height):
    if solid == "sphere":
        return 4 / 3 * math.pi * size ** 3
    if solid == "cone":
        return math.pi * size * size * height / 3
    return size * size * height / 3


def frustum_scale(par):
    return Fraction(par["scale_num"], par["scale_den"])


def results(par):
    form = par["form"]
    if form == "exact_volume":
        r, h = par["radius"], par["height"]
        coefficient = Fraction(r * r * h, 3) if par["solid"] == "cone" else Fraction(4 * r ** 3, 3)
        return {"coefficient": coefficient}
    if form == "pyramid_volume":
        return {"value": Fraction(par["side"] ** 2 * par["height"], 3)}
    if form == "cone_surface":
        r, h, l = cone_triple(par)
        return {"coefficient": Fraction(r * (l + r))}
    if form == "hemisphere_surface":
        return {"coefficient": Fraction(3 * par["radius"] ** 2)}
    if form == "reverse_radius":
        if par["solid"] == "sphere":
            radius = (3 * par["volume"] / (4 * math.pi)) ** (1 / 3)
        else:
            radius = math.sqrt(3 * par["volume"] / (math.pi * par["height"]))
        return {"value": radius}
    if form == "density":
        volume = solid_volume(par["solid"], par["size"], par["height"])
        return {"value": volume * par["density_tenths"] / 10, "volume": volume}
    if form == "frustum":
        k = frustum_scale(par)
        return {"coefficient": Fraction(par["radius"] ** 2 * par["height"], 3) * (1 - k ** 3),
                "small_height": par["height"] * k}
    return {"value": 4 * par["sphere_radius"] ** 3 / par["cone_radius"] ** 2}


def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    form = par.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(par) == KEYS[form] | {"form"}, "Unexpected parameters")
    require(all(type(par[k]) is int for k in KEYS[form] - {"solid"}), "Integer parameters required")

    if form == "exact_volume":
        require(par["solid"] in ("cone", "sphere"), "Unknown solid")
        require(2 <= par["radius"] <= 12, "Radius outside bounds")
        if par["solid"] == "cone":
            require(3 <= par["height"] <= 20, "Height outside bounds")
        else:
            require(par["height"] == 0, "A sphere has no height parameter")
    elif form == "pyramid_volume":
        require(3 <= par["side"] <= 12 and 3 <= par["height"] <= 20, "Dimension outside bounds")
        require(results(par)["value"].denominator == 1, "Volume must be a whole number")
    elif form == "cone_surface":
        require(par["triple"] in range(len(TRIPLES)) and par["scale"] in (1, 2, 3)
                and par["swap"] in (0, 1), "Unexpected cone")
        r, h, l = cone_triple(par)
        require(r <= 16 and h <= 30, "Cone too large")
    elif form == "hemisphere_surface":
        require(2 <= par["radius"] <= 12, "Radius outside bounds")
    elif form == "reverse_radius":
        require(par["solid"] in ("sphere", "cone"), "Unknown solid")
        require(100 <= par["volume"] <= 5000, "Volume outside bounds")
        if par["solid"] == "cone":
            require(5 <= par["height"] <= 20, "Height outside bounds")
        else:
            require(par["height"] == 0, "A sphere has no height parameter")
        radius = results(par)["value"]
        require(1 <= radius <= 30, "Radius outside bounds")
        rounded_sig_figs(radius)
    elif form == "density":
        require(par["solid"] in DENSITY_SOLIDS, "Unknown solid")
        require(2 <= par["size"] <= 12, "Size outside bounds")
        if par["solid"] == "sphere":
            require(par["height"] == 0, "A sphere has no height parameter")
        else:
            require(3 <= par["height"] <= 20, "Height outside bounds")
        require(10 <= par["density_tenths"] <= 114, "Density outside bounds")
        mass = results(par)["value"]
        require(mass >= 10, "Mass too small")
        rounded_sig_figs(mass)
    elif form == "frustum":
        require(3 <= par["radius"] <= 12 and 6 <= par["height"] <= 24, "Dimension outside bounds")
        require(par["scale_den"] > 0 and math.gcd(par["scale_num"], par["scale_den"]) == 1
                and frustum_scale(par) in FRUSTUM_SCALES, "Unexpected scale")
        require(results(par)["small_height"].denominator == 1, "Small cone height must be whole")
    else:
        require(2 <= par["sphere_radius"] <= 9 and 3 <= par["cone_radius"] <= 12,
                "Radius outside bounds")
        height = results(par)["value"]
        require(2 <= height <= 60, "Cone height outside bounds")
        rounded_sig_figs(height)


# ------------------------------------------------------------ notation

def pi_parts(coefficient):
    """(tex, text) for coefficient x pi, e.g. 96π or 256π/3."""
    n, d = coefficient.numerator, coefficient.denominator
    if d == 1:
        return r"%d\pi" % n, "%dπ" % n
    return r"\frac{%d\pi}{%d}" % (n, d), "%dπ/%d" % (n, d)


def density_text(tenths):
    return "{}.{}".format(tenths // 10, tenths % 10)


def formula_blocks(*names):
    return [rb.equation(*FORMULAE[name]) for name in names]


def in_terms_of_pi(task):
    return rb.paragraph(rb.text(task + " Give your answer in terms of "),
                        rb.maths(r"\pi", "π"), rb.text("."))


def content(blocks):
    plain = []
    for block in blocks:
        if block["kind"] == "equation":
            plain.append("[" + block["text"] + "]")
        elif "runs" in block:
            plain.append("".join(run["text"] for run in block["runs"]))
        else:
            plain.append(block["text"])
    return Content(" ".join(plain), blocks=tuple(blocks))


SOLID_NAMES = {"sphere": "sphere", "cone": "cone", "pyramid": "square-based pyramid"}


def dimension_sentence(solid, size, height):
    if solid == "sphere":
        return "The sphere has radius {} cm.".format(size)
    if solid == "cone":
        return "The cone has base radius {} cm and perpendicular height {} cm.".format(size, height)
    return ("The square base has sides of length {} cm and the perpendicular height is "
            "{} cm.".format(size, height))


def prompt_for(par):
    form = par["form"]
    if form == "exact_volume":
        solid = par["solid"]
        blocks = [rb.prose("The diagram shows a solid {}. {}".format(
            solid, dimension_sentence(solid, par["radius"], par["height"]))),
            in_terms_of_pi("Work out the volume of the {}.".format(solid))]
        return content(blocks + formula_blocks(solid + "_volume"))
    if form == "pyramid_volume":
        return content([rb.prose(
            "The diagram shows a solid square-based pyramid. {} Work out the volume of the "
            "pyramid.".format(dimension_sentence("pyramid", par["side"], par["height"])))])
    if form == "cone_surface":
        r, h, l = cone_triple(par)
        blocks = [rb.prose("The diagram shows a solid cone. {}".format(
            dimension_sentence("cone", r, h))),
            in_terms_of_pi("Work out the total surface area of the cone.")]
        return content(blocks + formula_blocks("cone_curved"))
    if form == "hemisphere_surface":
        blocks = [rb.prose("The diagram shows a solid hemisphere of radius {} cm.".format(
            par["radius"])),
            in_terms_of_pi("Work out the total surface area of the hemisphere.")]
        return content(blocks + formula_blocks("sphere_area"))
    if form == "reverse_radius":
        if par["solid"] == "sphere":
            text = ("A sphere has a volume of {} cm³. Work out the radius of the sphere. "
                    "Give your answer correct to 3 significant figures.").format(par["volume"])
            return content([rb.prose(text)] + formula_blocks("sphere_volume"))
        text = ("A cone has a volume of {} cm³ and a perpendicular height of {} cm. Work out "
                "the radius of its base. Give your answer correct to 3 significant "
                "figures.").format(par["volume"], par["height"])
        return content([rb.prose(text)] + formula_blocks("cone_volume"))
    if form == "density":
        solid = par["solid"]
        text = ("The diagram shows a solid {} made from metal. {} The density of the metal is "
                "{} g/cm³. Work out the mass of the {}. Give your answer correct to 3 "
                "significant figures.").format(
            SOLID_NAMES[solid], dimension_sentence(solid, par["size"], par["height"]),
            density_text(par["density_tenths"]), SOLID_NAMES[solid])
        extra = formula_blocks(solid + "_volume") if solid != "pyramid" else []
        return content([rb.prose(text)] + extra)
    if form == "frustum":
        blocks = [rb.prose(
            "A frustum is made by removing a small cone from the top of a large cone. The "
            "large cone has base radius {} cm and perpendicular height {} cm. The small cone "
            "has perpendicular height {} cm.".format(
                par["radius"], par["height"], results(par)["small_height"])),
            in_terms_of_pi("Work out the volume of the frustum.")]
        return content(blocks + formula_blocks("cone_volume"))
    text = ("A solid metal sphere of radius {} cm is melted down and recast into a solid cone "
            "with base radius {} cm. No metal is lost. Work out the perpendicular height of "
            "the cone. Give your answer correct to 3 significant figures.").format(
        par["sphere_radius"], par["cone_radius"])
    return content([rb.prose(text)] + formula_blocks("sphere_volume", "cone_volume"))


def answer_for(par):
    form = par["form"]
    values = results(par)
    if "coefficient" in values:
        unit, power = ("cm²", 2) if form in ("cone_surface", "hemisphere_surface") else ("cm³", 3)
        tex, text = pi_parts(values["coefficient"])
        return ({"kind": "pi_multiple", "coefficient": rational_text(values["coefficient"]),
                 "unit": unit},
                Content(text + " " + unit, tex + r"\ " + rb.unit_tex("cm", power)))
    if form == "pyramid_volume":
        volume = values["value"]
        return ({"kind": "quantity", "value": rational_text(volume), "unit": "cm³"},
                Content("{} cm³".format(volume), r"%d\ %s" % (volume, rb.unit_tex("cm", 3))))
    unit = "g" if form == "density" else "cm"
    rounded = rounded_sig_figs(values["value"])
    return ({"kind": "rounded_measure", "value": rational_text(rounded), "unit": unit},
            Content("{} {}".format(sig_figs_text(rounded), unit)))


def visuals_for(par):
    form = par["form"]
    cm = "{} cm".format
    if form == "exact_volume":
        if par["solid"] == "cone":
            return (solids.cone_scene(par["radius"], par["height"], cm(par["radius"]),
                                      cm(par["height"])),)
        return (solids.sphere_scene(par["radius"], cm(par["radius"])),)
    if form == "pyramid_volume":
        return (solids.pyramid_scene(par["side"], par["height"], cm(par["side"]),
                                     cm(par["height"])),)
    if form == "cone_surface":
        r, h, l = cone_triple(par)
        return (solids.cone_scene(r, h, cm(r), cm(h)),)
    if form == "hemisphere_surface":
        return (solids.hemisphere_scene(par["radius"], cm(par["radius"])),)
    if form == "reverse_radius":
        radius = results(par)["value"]
        if par["solid"] == "sphere":
            return (solids.sphere_scene(radius, "r"),)
        return (solids.cone_scene(radius, par["height"], "r", cm(par["height"])),)
    if form == "density":
        solid, size, height = par["solid"], par["size"], par["height"]
        if solid == "sphere":
            return (solids.sphere_scene(size, cm(size)),)
        if solid == "cone":
            return (solids.cone_scene(size, height, cm(size), cm(height)),)
        return (solids.pyramid_scene(size, height, cm(size), cm(height)),)
    if form == "frustum":
        return (solids.frustum_scene(par["radius"], par["height"], float(frustum_scale(par)),
                                     cm(par["radius"])),)
    # One diagram only: two stacked solids plus working space overflow a page.
    return (solids.cone_scene(par["cone_radius"], results(par)["value"],
                              cm(par["cone_radius"]), "h"),)


def draw_parameters(rng, form):
    par = {"form": form}
    if form == "exact_volume":
        solid = rng.choice(("cone", "sphere"))
        par.update(solid=solid, radius=rng.randint(2, 12),
                   height=rng.randint(3, 20) if solid == "cone" else 0)
    elif form == "pyramid_volume":
        par.update(side=rng.randint(3, 12), height=rng.randint(3, 20))
    elif form == "cone_surface":
        par.update(triple=rng.randrange(len(TRIPLES)), scale=rng.choice((1, 2, 3)),
                   swap=rng.randint(0, 1))
    elif form == "hemisphere_surface":
        par["radius"] = rng.randint(2, 12)
    elif form == "reverse_radius":
        solid = rng.choice(("sphere", "cone"))
        par.update(solid=solid, volume=rng.randint(100, 5000),
                   height=rng.randint(5, 20) if solid == "cone" else 0)
    elif form == "density":
        solid = rng.choice(DENSITY_SOLIDS)
        par.update(solid=solid, size=rng.randint(2, 12),
                   height=0 if solid == "sphere" else rng.randint(3, 20),
                   density_tenths=rng.randint(10, 114))
    elif form == "frustum":
        k = rng.choice(FRUSTUM_SCALES)
        par.update(radius=rng.randint(3, 12), height=rng.randint(6, 24),
                   scale_num=k.numerator, scale_den=k.denominator)
    else:
        par.update(sphere_radius=rng.randint(2, 9), cone_radius=rng.randint(3, 12))
    return par


# ------------------------------------------------------------ generator

class CurvedSolids:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        form = rng.choice(FORMS[difficulty])
        for attempt in range(2000):
            par = draw_parameters(rng, form)
            try:
                check_parameters(par, difficulty)
                require(all(solids.labels_ok(scene) for scene in visuals_for(par)),
                        "Diagram labels do not fit")
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a curved solids question")
        answer, display = answer_for(par)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(par),
            answer=answer, answer_display=display, worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=WORKING_LINES[difficulty]),
            parameters=par, question_visuals=visuals_for(par),
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        require(type(q.difficulty) is int and q.difficulty in (1, 2, 3, 4), "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        check_parameters(q.parameters, q.difficulty)
        answer, display = answer_for(q.parameters)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Answer display mismatch")
        require(q.prompt == prompt_for(q.parameters), "Prompt mismatch")
        require(q.visual_assets("questions") == visuals_for(q.parameters), "Diagram mismatch")
        require(q.visual_assets("answers") == (), "Unexpected answer visuals")
        return True

    def validate_independently(self, q):
        """Simpson-rule volumes and surfaces of revolution, never the formulae."""
        par, answer = q.parameters, q.answer
        form = par.get("form")

        def simpson(f, low, high, steps=200):
            width = (high - low) / steps
            total = f(low) + f(high)
            for i in range(1, steps):
                total += (4 if i % 2 else 2) * f(low + i * width)
            return total * width / 3

        def volume(solid, size, height):
            if solid == "sphere":
                return simpson(lambda y: math.pi * (size * size - y * y), -size, size)
            if solid == "cone":
                return simpson(lambda y: math.pi * (size * (1 - y / height)) ** 2, 0, height)
            return simpson(lambda y: (size * (1 - y / height)) ** 2, 0, height)

        def half_step(value):
            return 10 ** (math.floor(math.log10(value)) - 2) / 2

        def close(expected, stated, tolerance):
            require(abs(expected - stated) <= tolerance, "Independent reconstruction disagrees")

        if answer.get("kind") == "pi_multiple":
            stated = float(Fraction(answer["coefficient"])) * math.pi
            if form == "exact_volume":
                expected = volume(par["solid"], par["radius"], par["height"])
            elif form == "cone_surface":
                r, h, l = cone_triple(par)
                curved = simpson(lambda y: 2 * math.pi * r * (1 - y / h)
                                 * math.sqrt(1 + (r / h) ** 2), 0, h)
                expected = curved + math.pi * r * r
            elif form == "hemisphere_surface":
                r = par["radius"]
                # Archimedes: a spherical zone of height t has area 2 pi r t.
                expected = 2 * math.pi * r * r + math.pi * r * r
            else:
                R, H = par["radius"], par["height"]
                cut = H * (1 - float(frustum_scale(par)))
                expected = simpson(lambda y: math.pi * (R * (1 - y / H)) ** 2, 0, cut)
            close(expected, stated, 1e-9 * max(1.0, expected))
            return True
        if form == "pyramid_volume":
            close(volume("pyramid", par["side"], par["height"]),
                  float(Fraction(answer["value"])), 1e-9 * par["side"] ** 2 * par["height"])
            return True
        stated = float(Fraction(answer["value"]))
        if form == "reverse_radius":
            power = 3 if par["solid"] == "sphere" else 2
            achieved = volume(par["solid"], stated, par["height"])
            close(achieved, par["volume"],
                  par["volume"] * power * half_step(stated) / stated * 1.01 + 1e-9)
        elif form == "density":
            mass = volume(par["solid"], par["size"], par["height"]) * par["density_tenths"] / 10
            close(mass, stated, half_step(stated) + 1e-9)
        else:
            sphere = volume("sphere", par["sphere_radius"], 0)
            cone = volume("cone", par["cone_radius"], stated)
            close(cone, sphere, sphere * half_step(stated) / stated * 1.01 + 1e-9)
        return True