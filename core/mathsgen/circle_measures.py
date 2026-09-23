"""Circle measures with exact multiples of pi, drawn true and oriented.

Forms (two per level):
  1  area / circumference            from a radius or a diameter
  2  radius_from / diameter_from     from an area or a circumference
  3  semicircle / quarter            area or complete perimeter
  4  ring / square_circle            ring area or boundary; square minus its
                                     inscribed circle
Only stated givens are stored; reverse questions recover the radius from
the supplied measure. Shapes are drawn at true proportions with the seeded
orientation applied directly, so every label is placed in the final frame.
pi_expression, exact_root and display_for are shared with sectors.py.
"""
import math
from fractions import Fraction
from math import isqrt

from . import circle_figures, figures
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)


INFO = GeneratorInfo(
    id="geometry.circles.measures", version=4,
    topic="geometry", subtopic="circles",
    title="Circle area, circumference and circular regions",
    difficulty_descriptions={
        1: "Find area or circumference from a radius or diameter.",
        2: "Recover a radius or diameter from an area or circumference.",
        3: "Find the area or perimeter of a semicircle or quarter circle.",
        4: "Find ring measures, or the area of a square outside its inscribed circle.",
    },
    tags=("geometry", "circles", "area", "perimeter", "reverse"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("area", "circumference"),
    2: ("radius_from", "diameter_from"),
    3: ("semicircle", "quarter"),
    4: ("ring", "square_circle"),
}
FORM_KEYS = {
    "area": {"given", "value"}, "circumference": {"given", "value"},
    "radius_from": {"given", "value"}, "diameter_from": {"given", "value"},
    "semicircle": {"task", "given", "value"}, "quarter": {"task", "value"},
    "ring": {"task", "outer", "inner"}, "square_circle": {"side"},
}
MARKS = {1: 2, 2: 2, 3: 3, 4: 3}
DRAW_RADIUS = 90


# ------------------------------------------------------------ shared exact helpers

def exact_root(value):
    value = Fraction(value)
    top, bottom = isqrt(value.numerator), isqrt(value.denominator)
    require(top * top == value.numerator and bottom * bottom == value.denominator,
            "Expected a rational radius")
    return Fraction(top, bottom)


def pi_expression(constant, coefficient, tex=False):
    """Format constant + coefficient*pi without decimal approximation."""
    write = rational_tex if tex else rational_text
    constant, coefficient = Fraction(constant), Fraction(coefficient)
    pieces = []
    if constant:
        pieces.append(write(constant))
    if coefficient:
        magnitude = abs(coefficient)
        pi = r"\pi" if tex else "pi"
        if magnitude.denominator == 1:
            body = (str(magnitude.numerator) if magnitude != 1 else "") + pi
        elif tex:
            top = (str(magnitude.numerator) if magnitude.numerator != 1 else "") + pi
            body = r"\frac{" + top + "}{" + str(magnitude.denominator) + "}"
        else:
            top = (str(magnitude.numerator) if magnitude.numerator != 1 else "") + pi
            body = top + "/" + str(magnitude.denominator)
        pieces.append(
            ((" - " if coefficient < 0 else " + ") if pieces else
             ("-" if coefficient < 0 else "")) + body
        )
    return "".join(pieces) or "0"


def display_for(answer):
    constant, coefficient = answer["constant"], answer["pi_coefficient"]
    unit = answer["unit"]
    return Content(
        pi_expression(constant, coefficient) + " " + unit,
        pi_expression(constant, coefficient, True)
        + (r"\ \mathrm{cm}^{2}" if unit == "cm^2" else r"\ \mathrm{cm}"),
    )


# ------------------------------------------------------------ mathematics

def radius_of(p):
    """The radius implied by the givens (not used for rings or squares)."""
    given, value = p["given"] if "given" in p else "radius", p["value"]
    if given == "radius":
        return Fraction(value)
    if given == "diameter":
        return Fraction(value, 2)
    if given == "area":
        return exact_root(value)
    return Fraction(value, 2)          # circumference = 2 r pi


def exact(constant, coefficient, unit):
    return {"kind": "exact_pi_measure", "constant": rational_text(constant),
            "pi_coefficient": rational_text(coefficient), "unit": unit}


def answer_for(p):
    form = p["form"]
    if form == "ring":
        outer, inner = p["outer"], p["inner"]
        if p["task"] == "area":
            return exact(0, outer * outer - inner * inner, "cm^2")
        return exact(0, 2 * (outer + inner), "cm")
    if form == "square_circle":
        s = Fraction(p["side"])
        return exact(s * s, -(s * s) / 4, "cm^2")
    r = radius_of(p)
    if form == "area":
        return exact(0, r * r, "cm^2")
    if form == "circumference":
        return exact(0, 2 * r, "cm")
    if form == "radius_from":
        return exact(r, 0, "cm")
    if form == "diameter_from":
        return exact(2 * r, 0, "cm")
    share = Fraction(1, 2) if form == "semicircle" else Fraction(1, 4)
    if p["task"] == "area":
        return exact(0, share * r * r, "cm^2")
    return exact(2 * r, share * 2 * r, "cm")


def check_parameters(p, level):
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(form in FORMS[level], "Unexpected form for this level")
    require(set(p) == {"form", "orientation"} | FORM_KEYS[form], "Unexpected parameters")
    require(figures.valid_orientation(p["orientation"]), "Invalid orientation")
    for key in ("value", "outer", "inner", "side"):
        if key in p:
            require(type(p[key]) is int and p[key] > 0, "Whole positive givens required")
    if form in ("area", "circumference", "semicircle"):
        require(p["given"] in ("radius", "diameter") and 3 <= p["value"] <= 20,
                "Invalid length given")
    if form in ("semicircle", "quarter", "ring"):
        require(p["task"] in ("area", "perimeter"), "Unknown task")
    if form == "quarter":
        require(3 <= p["value"] <= 20, "Radius outside bounds")
    if form in ("radius_from", "diameter_from"):
        require(p["given"] in ("area", "circumference"), "Invalid reverse given")
        r = radius_of(p)
        require(r.denominator == 1 and 2 <= r <= 15, "Reverse radius outside bounds")
    if form == "ring":
        require(2 <= p["inner"] <= 10 and 2 <= p["outer"] - p["inner"] <= 8,
                "Invalid ring radii")
    if form == "square_circle":
        require(p["side"] % 2 == 0 and 4 <= p["side"] <= 20, "Side must be even, 4 to 20")


# ------------------------------------------------------------ drawing

def point(degrees, length, centre=circle_figures.CENTRE):
    turn = math.radians(degrees)
    return (centre[0] + length * math.cos(turn), centre[1] + length * math.sin(turn))


def labelled_line(start, end, text, away_from):
    return [circle_figures.line(start, end),
            {"type": "label", "text": text,
             "point": figures.side_label(start, end, away_from, len(text))}]


def diagram_for(p):
    form = p["form"]
    rotation, mirror = p["orientation"]
    turn = -1 if mirror else 1
    centre = circle_figures.CENTRE
    R = DRAW_RADIUS
    dot = {"type": "circle", "center": figures.rounded(centre), "radius": 1.6, "shade": True}
    nodes = []
    if form in ("area", "circumference", "radius_from", "diameter_from"):
        nodes += [{"type": "circle", "center": figures.rounded(centre), "radius": R}, dot]
        if form in ("radius_from", "diameter_from"):
            through = form == "diameter_from"
            text = "x"
        else:
            through = p["given"] == "diameter"
            text = "{} cm".format(p["value"])
        start = point(rotation + 180, R) if through else centre
        nodes += labelled_line(start, point(rotation, R), text, point(rotation + 90, 40))
    elif form == "semicircle":
        sweep = 180 * turn
        nodes.append({"type": "arc", "center": figures.rounded(centre), "radius": R,
                      "start": float(rotation), "sweep": float(sweep)})
        ends = point(rotation, R), point(rotation + 180, R)
        inside = point(rotation + 90 * turn, 40)
        if p["given"] == "diameter":
            nodes += labelled_line(ends[1], ends[0], "{} cm".format(p["value"]), inside)
        else:
            nodes.append(circle_figures.line(*ends))
            nodes.append(dot)
            middle = point(rotation + 90 * turn, R)
            nodes += labelled_line(centre, middle, "{} cm".format(p["value"]),
                                   point(rotation + 45 * turn, 40))
    elif form == "quarter":
        sweep = 90 * turn
        first, second = point(rotation, R), point(rotation + sweep, R)
        nodes.append({"type": "arc", "center": figures.rounded(centre), "radius": R,
                      "start": float(rotation), "sweep": float(sweep)})
        nodes.append({"type": "right_angle", "vertex": figures.rounded(centre),
                      "first": figures.rounded(first), "second": figures.rounded(second)})
        nodes += labelled_line(centre, first, "{} cm".format(p["value"]),
                               point(rotation + 45 * turn, 40))
        nodes.append(circle_figures.line(centre, second))
    elif form == "ring":
        inner = R * p["inner"] / p["outer"]
        nodes += [{"type": "circle", "center": figures.rounded(centre), "radius": R},
                  {"type": "circle", "center": figures.rounded(centre),
                   "radius": round(inner, figures.DIGITS)}, dot]
        nodes += labelled_line(centre, point(rotation, R), "{} cm".format(p["outer"]),
                               point(rotation + 90 * turn, 30))
        other = rotation + 150 * turn
        nodes += labelled_line(centre, point(other, inner), "{} cm".format(p["inner"]),
                               point(other + 90 * turn, 20))
    else:
        half = 80
        corners = [point(rotation + 45 + 90 * i, half * math.sqrt(2)) for i in range(4)]
        for i in range(4):
            nodes.append(circle_figures.line(corners[i], corners[(i + 1) % 4]))
        nodes.append({"type": "circle", "center": figures.rounded(centre), "radius": half})
        text = "{} cm".format(p["side"])
        nodes.append({"type": "label", "text": text,
                      "point": figures.side_label(corners[0], corners[1], centre, len(text))})
    return {"kind": "scene", "version": 1, "width": 360, "height": 300,
            "caption": "Not drawn accurately", "nodes": nodes}


# ------------------------------------------------------------ presentation

def presentation(p):
    form = p["form"]
    tail = " Give your answer in terms of pi."
    if form in ("area", "circumference"):
        text = "A circle has {} {} cm. Find its {}.".format(p["given"], p["value"], form)
        return Content(text + tail)
    if form in ("radius_from", "diameter_from"):
        task = "radius" if form == "radius_from" else "diameter"
        name = "A" if p["given"] == "area" else "C"
        unit = "square centimetres" if p["given"] == "area" else "centimetres"
        lead = "The {}, {}, of a circle is given below. Find its {}, x. Give an exact answer.".format(
            p["given"], name, task)
        full = "A circle has {} {} {}. Find its {}, x. Give an exact answer.".format(
            p["given"], pi_expression(0, p["value"]), unit, task)
        tex = name + " = " + pi_expression(0, p["value"], True)
        tex += r"\ \mathrm{cm}^{2}" if p["given"] == "area" else r"\ \mathrm{cm}"
        return Content(full, tex, display_text=lead)
    if form in ("semicircle", "quarter"):
        shape = "semicircle" if form == "semicircle" else "quarter circle"
        given = p.get("given", "radius")
        text = "A {} has {} {} cm. ".format(shape, given, p["value"])
        text += ("Find its area." if p["task"] == "area" else
                 "Find its complete perimeter, including the straight edge{}.".format(
                     "" if form == "semicircle" else "s"))
        return Content(text + tail)
    if form == "ring":
        text = "A ring is formed by two circles with the same centre, of radii {} cm and {} cm. ".format(
            p["outer"], p["inner"])
        text += ("Find the area of the ring." if p["task"] == "area" else
                 "Find the total length of its boundary, including both circles.")
        return Content(text + tail)
    return Content(("A circle fits exactly inside a square of side {} cm. Find the area of "
                    "the region inside the square but outside the circle. Give your answer "
                    "in terms of pi.").format(p["side"]))


def draw(rng, level):
    form = rng.choice(FORMS[level])
    p = {"form": form, "orientation": [0, False]}
    if form in ("area", "circumference"):
        p.update(given=rng.choice(("radius", "diameter")), value=rng.randint(3, 20))
    elif form in ("radius_from", "diameter_from"):
        r = rng.randint(2, 15)
        given = rng.choice(("area", "circumference"))
        p.update(given=given, value=r * r if given == "area" else 2 * r)
    elif form == "semicircle":
        p.update(task=rng.choice(("area", "perimeter")),
                 given=rng.choice(("radius", "diameter")), value=rng.randint(3, 20))
    elif form == "quarter":
        p.update(task=rng.choice(("area", "perimeter")), value=rng.randint(3, 20))
    elif form == "ring":
        inner = rng.randint(2, 10)
        p.update(task=rng.choice(("area", "perimeter")), inner=inner,
                 outer=inner + rng.randint(2, 8))
    else:
        p["side"] = 2 * rng.randint(2, 10)
    return p


# ------------------------------------------------------------ generator

class CircleMeasures:
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
            raise ValueError("Could not construct a circle-measures question")
        answer = answer_for(p)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=presentation(p), answer=answer,
            answer_display=display_for(answer), worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=4),
            parameters=p, question_visuals=(diagram_for(p),),
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        require(type(q.difficulty) is int and q.difficulty in (1, 2, 3, 4),
                "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        check_parameters(q.parameters, q.difficulty)
        require(q.answer == answer_for(q.parameters), "Incorrect answer")
        require(q.answer_display == display_for(q.answer), "Display mismatch")
        require(q.prompt == presentation(q.parameters), "Prompt mismatch")
        require(q.visual_assets("questions") == (diagram_for(q.parameters),),
                "Diagram mismatch")
        require(not q.visual_assets("answers"), "Unexpected answer visuals")
        return True

    def validate_independently(self, q):
        """Diameter identities, inverse substitution and ring factorisation."""
        p, form = q.parameters, q.parameters["form"]
        constant = Fraction(q.answer["constant"])
        coefficient = Fraction(q.answer["pi_coefficient"])
        unit = q.answer["unit"]
        if form in ("radius_from", "diameter_from"):
            require(coefficient == 0 and constant > 0 and unit == "cm",
                    "Expected a positive length")
            diameter = constant * 2 if form == "radius_from" else constant
            rebuilt = diameter * diameter / 4 if p["given"] == "area" else diameter
            require(rebuilt == p["value"], "Recovered length fails the given")
        elif form == "ring":
            if p["task"] == "area":
                ok = coefficient == (p["outer"] - p["inner"]) * (p["outer"] + p["inner"])
            else:
                ok = coefficient == 2 * p["outer"] + 2 * p["inner"]
            require(constant == 0 and ok, "Ring result disagrees")
        elif form == "square_circle":
            s = p["side"]
            require(constant == s * s and -4 * coefficient == s * s and unit == "cm^2",
                    "Square-minus-circle disagrees")
        else:
            given = p.get("given", "radius")
            diameter = Fraction(p["value"]) * (2 if given == "radius" else 1)
            parts = {"area": 1, "circumference": 1, "semicircle": 2, "quarter": 4}[form]
            task = p.get("task", "area" if form == "area" else "perimeter")
            if task == "area":
                require(constant == 0 and 4 * parts * coefficient == diameter ** 2
                        and unit == "cm^2", "Area/diameter identity disagrees")
            else:
                straight = 0 if parts == 1 else (diameter if parts == 2 else diameter)
                require(coefficient == diameter / parts and constant == straight
                        and unit == "cm", "Boundary lengths disagree")
        return True