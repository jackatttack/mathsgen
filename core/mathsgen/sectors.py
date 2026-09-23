"""Arc length, sector area and reverse problems, drawn and oriented.

Every question is built from a hidden true radius r (whole cm) and angle t
(from ANGLES); the parameters store only what the student is given.
Forms (two per level):
  1  arc / area                  direct measures
  2  perimeter / major_area      two radii plus the arc; or 360 - t first
  3  angle / perimeter_angle     recover t from an arc or area, or from a
                                 perimeter after removing the two radii
  4  radius / arc_from_area      recover r; or recover r, then the arc
Known angles are drawn to scale. When the angle is the unknown, the drawing
uses a seeded decoy 20-40 degrees away in the same minor/reflex class, so a
protractor cannot answer it. Orientation is seeded; validation rebuilds the
exact scene.
"""
import math
from fractions import Fraction

from . import circle_figures, figures
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .circle_measures import pi_expression, exact_root, display_for


INFO = GeneratorInfo(
    id="geometry.circles.sectors", version=3,
    topic="geometry", subtopic="circles",
    title="Arc length, sector area and reverse problems",
    difficulty_descriptions={
        1: "Find the arc length or area of a sector.",
        2: "Find a sector's perimeter, or the area of the major sector.",
        3: "Recover the angle from an arc, an area or a perimeter.",
        4: "Recover the radius, or use it to find the arc from the area.",
    },
    tags=("geometry", "circles", "sectors", "arcs", "reverse"),
)


# ------------------------------------------------------------ editable knobs

ANGLES = (40, 45, 60, 72, 90, 120, 135, 150, 210, 240, 270, 300)
FORMS = {
    1: ("arc", "area"),
    2: ("perimeter", "major_area"),
    3: ("angle", "perimeter_angle"),
    4: ("radius", "arc_from_area"),
}
FORM_KEYS = {
    "arc": {"radius", "angle"}, "area": {"radius", "angle"},
    "perimeter": {"radius", "angle"}, "major_area": {"radius", "angle"},
    "angle": {"radius", "measure", "coefficient", "drawn"},
    "perimeter_angle": {"radius", "coefficient", "drawn"},
    "radius": {"angle", "measure", "coefficient"},
    "arc_from_area": {"angle", "coefficient"},
}
UNKNOWN_ANGLE = {"angle", "perimeter_angle"}
MARKS = {1: 2, 2: 3, 3: 3, 4: 4}
ANGLE_LABEL_DISTANCE = 42


# ------------------------------------------------------------ mathematics

def arc_coefficient(r, t):
    return Fraction(t, 360) * 2 * r


def area_coefficient(r, t):
    return Fraction(t, 360) * r * r


def truth(p):
    """The hidden (radius, angle) implied by the givens."""
    form = p["form"]
    if "radius" in p and "angle" in p:
        return Fraction(p["radius"]), Fraction(p["angle"])
    c = Fraction(p["coefficient"])
    if form == "angle":
        r = Fraction(p["radius"])
        return r, (c * 360 / (2 * r) if p["measure"] == "arc" else c * 360 / (r * r))
    if form == "perimeter_angle":
        r = Fraction(p["radius"])
        return r, c * 180 / r
    t = Fraction(p["angle"])
    if form == "radius" and p["measure"] == "arc":
        return c * 360 / (2 * t), t
    return exact_root(c * 360 / t), t


def exact(constant, coefficient, unit):
    return {"kind": "exact_pi_measure", "constant": rational_text(constant),
            "pi_coefficient": rational_text(coefficient), "unit": unit}


def answer_for(p):
    form = p["form"]
    r, t = truth(p)
    if form == "arc":
        return exact(0, arc_coefficient(r, t), "cm")
    if form == "area":
        return exact(0, area_coefficient(r, t), "cm^2")
    if form == "perimeter":
        return exact(2 * r, arc_coefficient(r, t), "cm")
    if form == "major_area":
        return exact(0, area_coefficient(r, 360 - t), "cm^2")
    if form in UNKNOWN_ANGLE:
        return {"kind": "angle", "value": rational_text(t), "unit": "degrees"}
    if form == "radius":
        return exact(r, 0, "cm")
    return exact(0, arc_coefficient(r, t), "cm")


def answer_display(answer):
    if answer["kind"] == "angle":
        return Content(answer["value"] + " degrees", answer["value"] + r"^{\circ}")
    return display_for(answer)


def decoy_choices(t):
    t = int(t)
    return [d for d in range(t - 40, t + 41, 5)
            if 20 <= abs(d - t) and 40 <= d <= 320 and d != 180
            and (d < 180) == (t < 180)]


def check_parameters(p, level):
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(form in FORMS[level], "Unexpected form for this level")
    require(set(p) == {"form", "orientation"} | FORM_KEYS[form], "Unexpected parameters")
    require(figures.valid_orientation(p["orientation"]), "Invalid orientation")
    if "measure" in p:
        require(p["measure"] in ("arc", "area"), "Unknown measure")
    if "coefficient" in p:
        c = Fraction(p["coefficient"])
        require(c > 0 and rational_text(c) == p["coefficient"], "Invalid exact coefficient")
    for key in ("radius", "angle", "drawn"):
        if key in p:
            require(type(p[key]) is int, "Whole numbers required")
    r, t = truth(p)
    require(r.denominator == 1 and 3 <= r <= 18, "Radius outside bounds")
    require(t.denominator == 1 and int(t) in ANGLES, "Angle outside bounds")
    if form == "major_area":
        require(t < 180, "The given angle must be the minor sector")
    if form in UNKNOWN_ANGLE:
        require(p["drawn"] in decoy_choices(t), "Invalid drawn angle")
    return r, t


# ------------------------------------------------------------ presentation

def diagram_for(p):
    r, t = truth(p)
    form = p["form"]
    shown = float(p.get("drawn", t))
    centre = circle_figures.CENTRE
    radius = circle_figures.RADIUS
    on = circle_figures.on_circle
    # Orientation is applied directly (start angle and sweep direction) so
    # every label below is placed in the final frame. Rotating a finished
    # scene would leave side labels sized for the wrong edge direction.
    rotation, mirror = p["orientation"]
    sweep = -shown if mirror else shown
    a, b = on(rotation), on(rotation + sweep)
    middle = on(rotation + sweep / 2)
    if form == "major_area":
        nodes = circle_figures.circle_nodes()
    else:
        nodes = [{"type": "arc", "center": figures.rounded(centre), "radius": radius,
                  "start": float(rotation), "sweep": round(sweep, figures.DIGITS)},
                 {"type": "circle", "center": figures.rounded(centre), "radius": 1.6,
                  "shade": True}]
    nodes += [circle_figures.line(centre, a), circle_figures.line(centre, b)]
    nodes.append(circle_figures.vertex_label(centre, "O", away_from=middle,
                                             gap=circle_figures.CENTRE_GAP))
    angle_text = "x" if form in UNKNOWN_ANGLE else "{}°".format(int(t))
    turn = math.radians(rotation + sweep / 2)
    nodes.append({"type": "arc", "center": figures.rounded(centre), "radius": 20,
                  "start": float(rotation), "sweep": round(sweep, figures.DIGITS)})
    nodes.append({"type": "label", "text": angle_text, "point": figures.rounded((
        centre[0] + ANGLE_LABEL_DISTANCE * math.cos(turn),
        centre[1] + ANGLE_LABEL_DISTANCE * math.sin(turn)))})
    if form in ("radius", "arc_from_area"):
        radius_text = "x" if form == "radius" else None
    else:
        radius_text = "{} cm".format(int(r))
    if radius_text:
        nodes.append({"type": "label", "text": radius_text,
                      "point": figures.side_label(centre, a, middle, len(radius_text))})
    return {"kind": "scene", "version": 1, "width": 360, "height": 300,
            "caption": "Not drawn accurately", "nodes": nodes}


def presentation(p):
    form = p["form"]
    r, t = truth(p)
    if form in ("arc", "area", "perimeter"):
        text = "A sector has radius {} cm and angle {} degrees. ".format(int(r), int(t))
        text += {"arc": "Find its arc length.", "area": "Find its area.",
                 "perimeter": "Find its complete perimeter, including both radii."}[form]
        return Content(text + " Give your answer in terms of pi.")
    if form == "major_area":
        text = ("A circle with centre O and radius {} cm is split into two sectors. The "
                "minor sector has angle {} degrees. Find the area of the major sector. "
                "Give your answer in terms of pi.").format(int(r), int(t))
        return Content(text)
    c = Fraction(p["coefficient"])
    if form == "perimeter_angle":
        lead = ("A sector has radius {} cm. Its complete perimeter, including both radii, "
                "is given below. Find the angle x.").format(int(r))
        given = pi_expression(2 * r, c)
        tex = "P = " + pi_expression(2 * r, c, True) + r"\ \mathrm{cm}"
        return Content(lead + " The perimeter is " + given + " cm.", tex, display_text=lead)
    measure = p.get("measure", "area")
    name = "arc length" if measure == "arc" else "area"
    symbol = "L" if measure == "arc" else "A"
    unit_text = "cm" if measure == "arc" else "cm^2"
    unit_tex = r"\ \mathrm{cm}" if measure == "arc" else r"\ \mathrm{cm}^{2}"
    if form == "angle":
        lead = "A sector has radius {} cm. Its {} is given below. Find the angle x.".format(
            int(r), name)
    elif form == "radius":
        lead = ("A sector has angle {} degrees. Its {} is given below. Find the radius x. "
                "Give an exact answer.").format(int(t), name)
    else:
        lead = ("A sector has angle {} degrees. Its area is given below. Find its arc "
                "length. Give your answer in terms of pi.").format(int(t))
    tex = symbol + " = " + pi_expression(0, c, True) + unit_tex
    return Content(lead + " The {} is {} {}.".format(name, pi_expression(0, c), unit_text),
                   tex, display_text=lead)


def draw(rng, level):
    form = rng.choice(FORMS[level])
    r = rng.randint(3, 18)
    minor = [a for a in ANGLES if a < 180]
    t = rng.choice(minor if form == "major_area" else ANGLES)
    p = {"form": form, "orientation": [0, False]}
    if form in ("arc", "area", "perimeter", "major_area"):
        p.update(radius=r, angle=t)
    elif form == "angle":
        measure = rng.choice(("arc", "area"))
        c = arc_coefficient(r, t) if measure == "arc" else area_coefficient(r, t)
        p.update(radius=r, measure=measure, coefficient=rational_text(c),
                 drawn=rng.choice(decoy_choices(t)))
    elif form == "perimeter_angle":
        p.update(radius=r, coefficient=rational_text(arc_coefficient(r, t)),
                 drawn=rng.choice(decoy_choices(t)))
    elif form == "radius":
        measure = rng.choice(("arc", "area"))
        c = arc_coefficient(r, t) if measure == "arc" else area_coefficient(r, t)
        p.update(angle=t, measure=measure, coefficient=rational_text(c))
    else:
        p.update(angle=t, coefficient=rational_text(area_coefficient(r, t)))
    return p


# ------------------------------------------------------------ generator

class Sectors:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        for attempt in range(300):
            p = draw(rng, difficulty)
            try:
                check_parameters(p, difficulty)
                p["orientation"] = circle_figures.choose_orientation(
                    rng, lambda orientation: diagram_for(dict(p, orientation=orientation)))
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a sector question")
        answer = answer_for(p)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=presentation(p), answer=answer,
            answer_display=answer_display(answer), worked_solution=(),
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
        require(q.answer_display == answer_display(q.answer), "Display mismatch")
        require(q.prompt == presentation(q.parameters), "Prompt mismatch")
        require(q.visual_assets("questions") == (diagram_for(q.parameters),),
                "Diagram mismatch")
        require(not q.visual_assets("answers"), "Unexpected answer visuals")
        return True

    def validate_independently(self, q):
        """Exact angular proportion: an arc of coefficient L (in pi) satisfies 180 L = r t."""
        p, answer, form = q.parameters, q.answer, q.parameters["form"]

        def arc_ok(arc, r, t):
            return arc * 180 == r * t

        if form in UNKNOWN_ANGLE:
            t = Fraction(answer["value"])
            r = Fraction(p["radius"])
            c = Fraction(p["coefficient"])
            arc = c if form == "perimeter_angle" or p["measure"] == "arc" else 2 * c / r
            require(0 < t < 360 and arc_ok(arc, r, t), "Recovered angle fails the given")
        elif form == "radius":
            r, t, c = Fraction(answer["constant"]), Fraction(p["angle"]), Fraction(p["coefficient"])
            arc = c if p["measure"] == "arc" else 2 * c / r
            require(r > 0 and Fraction(answer["pi_coefficient"]) == 0 and arc_ok(arc, r, t),
                    "Recovered radius fails the given")
        elif form == "arc_from_area":
            arc, t, area = (Fraction(answer["pi_coefficient"]), Fraction(p["angle"]),
                            Fraction(p["coefficient"]))
            r = 180 * arc / t
            require(area == r * arc / 2, "Arc and area disagree")
        else:
            r, t = Fraction(p["radius"]), Fraction(p["angle"])
            c, constant = Fraction(answer["pi_coefficient"]), Fraction(answer["constant"])
            require(constant == (2 * r if form == "perimeter" else 0),
                    "Straight boundary contribution is wrong")
            if form == "major_area":
                t = 360 - t
            arc = c if form in ("arc", "perimeter") else 2 * c / r
            require(arc_ok(arc, r, t), "Angular proportion disagrees")
        return True