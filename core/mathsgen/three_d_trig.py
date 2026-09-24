"""3D Pythagoras and trigonometry in cuboids and square-based pyramids.

Cuboid ABCDEFGH: base ABCD, top EFGH, with E above A, and so on. In 3D
coordinates A = (0, 0, 0), B = (w, 0, 0), C = (w, d, 0), D = (0, d, 0), and the
top face is z = h. Drawings use an oblique projection; edges meeting the hidden
corner D are dashed. The independent check rebuilds everything in 3D
coordinates and uses distances and dot products, never tan or Pythagoras.
"""
import math
from fractions import Fraction

from . import figures
from . import solid_figures as solids
from .bearings import rounded_sig_figs, sig_figs_text
from .core import Content, GeneratorInfo, LayoutHint, Question, make_context, rational_text, require
from .sine_rule import rounded_value
from .trigonometry import one_decimal_text
from .vector_geometry import renders_cleanly


INFO = GeneratorInfo(
    id="geometry.trigonometry.three_d", version=1,
    topic="geometry", subtopic="three_d_trig",
    title="3D Pythagoras and trigonometry",
    difficulty_descriptions={
        1: "Find a space diagonal exactly, or a face diagonal of a cuboid.",
        2: "Find a space diagonal to 3 s.f., or its angle with the base.",
        3: "Find a sloping edge of a square-based pyramid, or its angle with the base.",
        4: "Find the length from a corner to an edge midpoint, or its angle with the base.",
    },
    tags=("geometry", "trigonometry", "3D", "Pythagoras"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("space_exact", "face_diagonal"),
    2: ("space_rounded", "diagonal_angle"),
    3: ("pyramid_edge", "pyramid_angle"),
    4: ("midpoint_length", "midpoint_angle"),
}
QUADRUPLES = ((1, 2, 2, 3), (2, 3, 6, 7), (1, 4, 8, 9), (4, 4, 7, 9), (2, 6, 9, 11),
              (6, 6, 7, 11), (3, 4, 12, 13), (2, 5, 14, 15), (2, 10, 11, 15), (8, 9, 12, 17))
DEPTH_SCALE = 0.5
MARKS = {1: 3, 2: 3, 3: 4, 4: 5}
WORKING_LINES = {1: 5, 2: 5, 3: 6, 4: 8}
CUBOID_FORMS = ("space_exact", "face_diagonal", "space_rounded", "diagonal_angle",
                "midpoint_length", "midpoint_angle")
KEYS = {form: {"width", "depth", "height"} for form in CUBOID_FORMS}
KEYS.update({"pyramid_edge": {"side", "height"}, "pyramid_angle": {"side", "height"}})


# ------------------------------------------------------------ mathematics

def results(par):
    """(value, kind) for the asked quantity: kind is 'length' or 'angle'."""
    form = par["form"]
    if form in ("pyramid_edge", "pyramid_angle"):
        s, h = par["side"], par["height"]
        half_diagonal = s * math.sqrt(2) / 2
        if form == "pyramid_edge":
            return math.hypot(half_diagonal, h), "length"
        return math.degrees(math.atan(h / half_diagonal)), "angle"
    w, d, h = par["width"], par["depth"], par["height"]
    if form == "face_diagonal":
        return math.hypot(w, d), "length"
    if form in ("space_exact", "space_rounded"):
        return math.sqrt(w * w + d * d + h * h), "length"
    if form == "diagonal_angle":
        return math.degrees(math.atan(h / math.hypot(w, d))), "angle"
    across = math.hypot(w, d / 2)
    if form == "midpoint_length":
        return math.hypot(across, h), "length"
    return math.degrees(math.atan(h / across)), "angle"


def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    form = par.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(par) == KEYS[form] | {"form"}, "Unexpected parameters")
    require(all(type(par[k]) is int for k in KEYS[form]), "Integer parameters required")
    if form in CUBOID_FORMS:
        require(all(2 <= par[k] <= 24 for k in ("width", "depth", "height")),
                "Dimensions outside bounds")
        if form == "space_exact":
            total = par["width"] ** 2 + par["depth"] ** 2 + par["height"] ** 2
            require(math.isqrt(total) ** 2 == total, "Space diagonal must be a whole number")
        if form in ("midpoint_length", "midpoint_angle"):
            require(par["depth"] % 2 == 0, "Midpoint needs an even depth")
    else:
        require(4 <= par["side"] <= 20 and 4 <= par["height"] <= 24, "Dimensions outside bounds")
    value, kind = results(par)
    if kind == "angle":
        require(15 <= value <= 75, "Angle outside a sensible range")
        rounded_value(value)
    elif form != "space_exact":
        rounded_sig_figs(value)
    require(renders_cleanly(visual_for(par)), "Diagram does not render cleanly")


# ------------------------------------------------------------ drawing

def project(point):
    x, y, z = point
    turn = math.radians(30)
    return (x + y * DEPTH_SCALE * math.cos(turn), z + y * DEPTH_SCALE * math.sin(turn))


def cuboid_scene(par):
    w, d, h = par["width"], par["depth"], par["height"]
    corners = {"A": (0, 0, 0), "B": (w, 0, 0), "C": (w, d, 0), "D": (0, d, 0),
               "E": (0, 0, h), "F": (w, 0, h), "G": (w, d, h), "H": (0, d, h)}
    raw = {name: project(p) for name, p in corners.items()}
    if par["form"] in ("midpoint_length", "midpoint_angle"):
        raw["M"] = project((w, d / 2, h))
        raw["N"] = project((w, d / 2, 0))
    placed, height = figures.place(raw, [0, False])
    edges = ("AB", "BC", "CD", "DA", "EF", "FG", "GH", "HE", "AE", "BF", "CG", "DH")
    nodes = []
    for edge in edges:
        nodes.append({"type": "line", "points": [placed[edge[0]], placed[edge[1]]],
                      **({"dashed": True} if "D" in edge else {})})
    form = par["form"]
    if form == "face_diagonal":
        nodes.append({"type": "line", "points": [placed["A"], placed["C"]]})
    elif form in ("space_exact", "space_rounded", "diagonal_angle"):
        nodes.append({"type": "line", "points": [placed["A"], placed["G"]]})
        if form == "diagonal_angle":
            nodes.append({"type": "line", "points": [placed["A"], placed["C"]], "dashed": True})
    else:
        nodes.append({"type": "line", "points": [placed["A"], placed["M"]]})
        nodes.append({"type": "line", "points": [placed["A"], placed["N"]], "dashed": True})
    xs = [p[0] for p in placed.values()]
    ys = [p[1] for p in placed.values()]
    centre = (sum(xs) / len(xs), sum(ys) / len(ys))
    for name in "ABCDEFGH" + ("M" if "M" in placed else ""):
        point = placed[name]
        outward = figures.unit(figures.minus(point, centre)) if point != list(centre) else (0, 1)
        nodes.append({"type": "label", "text": name,
                      "point": figures.rounded((point[0] + outward[0] * 12,
                                                point[1] + outward[1] * 12))})
    nodes.append(solids.side_text(placed["A"], placed["B"], placed["E"], "{} cm".format(w)))
    nodes.append(solids.side_text(placed["B"], placed["C"], placed["A"], "{} cm".format(d)))
    nodes.append(solids.side_text(placed["B"], placed["F"], placed["A"], "{} cm".format(h)))
    return {"kind": "scene", "version": 1, "width": 360, "height": height,
            "caption": "", "nodes": nodes}


def visual_for(par):
    if par["form"] in ("pyramid_edge", "pyramid_angle"):
        return solids.pyramid_scene(par["side"], par["height"], "{} cm".format(par["side"]),
                                    "{} cm".format(par["height"]))
    return cuboid_scene(par)


# ------------------------------------------------------------ wording

def prompt_for(par):
    form = par["form"]
    if form in ("pyramid_edge", "pyramid_angle"):
        opening = ("The diagram shows a square-based pyramid. The base has sides of {} cm and "
                   "the vertex is {} cm vertically above the centre of the base."
                   .format(par["side"], par["height"]))
        task = ("Work out the length of a sloping edge. Give your answer correct to 3 "
                "significant figures." if form == "pyramid_edge" else
                "Work out the angle between a sloping edge and the base. Give your answer "
                "correct to 1 decimal place.")
        return Content(opening + " " + task)
    opening = ("ABCDEFGH is a cuboid with AB = {} cm, BC = {} cm and BF = {} cm."
               .format(par["width"], par["depth"], par["height"]))
    if form in ("midpoint_length", "midpoint_angle"):
        opening += " M is the midpoint of FG."
    task = {
        "space_exact": "Work out the length of AG.",
        "face_diagonal": "Work out the length of AC. Give your answer correct to 3 significant figures.",
        "space_rounded": "Work out the length of AG. Give your answer correct to 3 significant figures.",
        "diagonal_angle": "Work out the angle between AG and the base ABCD. Give your answer "
                          "correct to 1 decimal place.",
        "midpoint_length": "Work out the length of AM. Give your answer correct to 3 significant "
                           "figures.",
        "midpoint_angle": "Work out the angle between AM and the base ABCD. Give your answer "
                          "correct to 1 decimal place.",
    }[form]
    return Content(opening + " " + task)


def answer_for(par):
    value, kind = results(par)
    if par["form"] == "space_exact":
        exact = int(round(value))
        return {"kind": "quantity", "value": str(exact), "unit": "cm"}, Content("{} cm".format(exact))
    if kind == "angle":
        rounded = rounded_value(value)
        return ({"kind": "rounded_measure", "value": rational_text(rounded), "unit": "degrees"},
                Content("{}°".format(one_decimal_text(rounded))))
    rounded = rounded_sig_figs(value)
    return ({"kind": "rounded_measure", "value": rational_text(rounded), "unit": "cm"},
            Content("{} cm".format(sig_figs_text(rounded))))


def draw_parameters(rng, form):
    par = {"form": form}
    if form == "space_exact":
        a, b, c, _ = rng.choice(QUADRUPLES)
        dims = [a, b, c]
        rng.shuffle(dims)
        scale = rng.choice((1, 2))
        par.update(width=dims[0] * scale, depth=dims[1] * scale, height=dims[2] * scale)
    elif form in ("pyramid_edge", "pyramid_angle"):
        par.update(side=rng.randint(4, 20), height=rng.randint(4, 24))
    else:
        par.update(width=rng.randint(3, 20), depth=rng.randrange(2, 21, 2),
                   height=rng.randint(3, 20))
    return par


# ------------------------------------------------------------ generator

class ThreeDTrig:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        form = rng.choice(FORMS[difficulty])
        for attempt in range(3000):
            par = draw_parameters(rng, form)
            try:
                check_parameters(par, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a 3D trigonometry question")
        answer, display = answer_for(par)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(par),
            answer=answer, answer_display=display, worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=WORKING_LINES[difficulty]),
            parameters=par, question_visuals=(visual_for(par),),
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
        require(q.visual_assets("questions") == (visual_for(q.parameters),), "Diagram mismatch")
        return True

    def validate_independently(self, q):
        """3D coordinates, distances and the dot product with the projection onto the base."""
        par, answer = q.parameters, q.answer
        form = par["form"]

        def distance(p, r):
            return math.sqrt(sum((a - b) ** 2 for a, b in zip(p, r)))

        def base_angle(start, end):
            v = [b - a for a, b in zip(start, end)]
            flat = [v[0], v[1], 0.0]
            dot = sum(a * b for a, b in zip(v, flat))
            return math.degrees(math.acos(dot / (distance((0, 0, 0), v) * distance((0, 0, 0), flat))))

        if form in ("pyramid_edge", "pyramid_angle"):
            s, h = par["side"], par["height"]
            corner, apex = (0.0, 0.0, 0.0), (s / 2, s / 2, float(h))
            segment = (corner, apex)
        else:
            w, d, h = par["width"], par["depth"], par["height"]
            A = (0.0, 0.0, 0.0)
            ends = {"face_diagonal": (w, d, 0), "space_exact": (w, d, h), "space_rounded": (w, d, h),
                    "diagonal_angle": (w, d, h), "midpoint_length": (w, d / 2, h),
                    "midpoint_angle": (w, d / 2, h)}
            segment = (A, tuple(float(v) for v in ends[form]))
        if answer["unit"] == "degrees":
            measured = base_angle(*segment)
            require(abs(measured - float(Fraction(answer["value"]))) <= 0.05 + 1e-9,
                    "Angle disagrees")
        else:
            measured = distance(*segment)
            stated = float(Fraction(answer["value"]))
            step = 10 ** (math.floor(math.log10(stated)) - 2)
            tolerance = 1e-9 if form == "space_exact" else step / 2 + 1e-9
            require(abs(measured - stated) <= tolerance, "Length disagrees")
        return True