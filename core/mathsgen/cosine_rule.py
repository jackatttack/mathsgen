"""Cosine-rule families drawn from their true triangles with varied layouts.

Levels 1-3 letter the triangle with a seeded permutation of A, B and C, so
the known or unknown angle can sit at any vertex. Roles X, Y and Z carry the
mathematics: X is the key angle, a = YZ is opposite it, b = XZ and c = XY.
Level 4 keeps the conventional quadrilateral ABCD split by the shared side AC.

Diagrams are built from real coordinates with figures.place(), then oriented
by a seeded rotation/reflection stored in the parameters. Validation rebuilds
the exact scene from the parameters and never renders.
"""
import math
from fractions import Fraction

from . import figures
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .sine_rule import rounded_value
from .trigonometry import one_decimal_text


INFO = GeneratorInfo(
    id="geometry.trigonometry.cosine_rule", version=4,
    topic="geometry", subtopic="trigonometry",
    title="Cosine rule: sides, angles, area and linked triangles",
    difficulty_descriptions={
        1: "Find a side from two sides and their included angle, at any vertex.",
        2: "Find any angle from three sides.",
        3: "Find an angle then the area, or a side then another angle.",
        4: "Use the cosine rule twice across a shared side to find a side or an angle.",
    },
    tags=("geometry", "trigonometry", "cosine_rule"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("side",),
    2: ("angle",),
    3: ("angle_area", "side_angle"),
    4: ("linked_side", "linked_angle"),
}
GIVENS = {
    "side": ("b", "c", "X"),
    "angle": ("a", "b", "c"),
    "angle_area": ("a", "b", "c"),
    "side_angle": ("b", "c", "X"),
    "linked_side": ("AB", "BC", "B", "AD", "CAD"),
    "linked_angle": ("AB", "BC", "B", "AD", "CD"),
}
ANGLE_GIVENS = {"X", "B", "CAD"}
NAMINGS = ("ABC", "ACB", "BAC", "BCA", "CAB", "CBA")
SMALLEST_ANGLE = 20
VERTEX_GAP = 16
MARKS = {1: 3, 2: 3, 3: 5, 4: 5}
WORKING_LINES = {1: 5, 2: 5, 3: 7, 4: 7}


# ------------------------------------------------------------ mathematics

def third_side(first, second, angle):
    return math.sqrt(
        first * first + second * second
        - 2 * first * second * math.cos(math.radians(angle))
    )


def included_angle(first, second, opposite):
    cosine = (first * first + second * second - opposite * opposite) / (
        2 * first * second
    )
    require(-1 < cosine < 1, "Invalid triangle")
    return math.degrees(math.acos(cosine))


def triangle_angles(a, b, c):
    """Angles at X, Y and Z of the triangle with YZ = a, XZ = b and XY = c."""
    return (
        included_angle(b, c, a),
        included_angle(a, c, b),
        included_angle(a, b, c),
    )


def shared_side(p):
    return third_side(p["AB"], p["BC"], p["B"])


def results(p):
    """Unrounded answers, in the order the question asks for them."""
    form = p["form"]
    if form == "side":
        return (third_side(p["b"], p["c"], p["X"]),)
    if form in ("angle", "angle_area"):
        angle = included_angle(p["b"], p["c"], p["a"])
        if form == "angle":
            return (angle,)
        return angle, p["b"] * p["c"] * math.sin(math.radians(angle)) / 2
    if form == "side_angle":
        side = third_side(p["b"], p["c"], p["X"])
        return side, included_angle(side, p["c"], p["b"])
    shared = shared_side(p)
    if form == "linked_side":
        return (third_side(shared, p["AD"], p["CAD"]),)
    return (included_angle(shared, p["AD"], p["CD"]),)


def check_parameters(p, level):
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(form in FORMS[level], "Unexpected form for this level")
    givens = set(GIVENS[form])
    fixed = {"form", "orientation"} | ({"names"} if level < 4 else set())
    require(set(p) == givens | fixed, "Unexpected parameters")
    require(figures.valid_orientation(p["orientation"]), "Invalid orientation")
    if level < 4:
        require(p["names"] in NAMINGS, "Invalid vertex names")
    require(all(type(p[name]) is int for name in givens),
            "Integer givens required")
    for name in givens - ANGLE_GIVENS:
        require(5 <= p[name] <= 20, "Side outside bounds")

    if form in ("side", "side_angle"):
        require(35 <= p["X"] <= 125 and p["X"] != 90,
                "Expected a non-right included angle")
        a = third_side(p["b"], p["c"], p["X"])
        require(min(triangle_angles(a, p["b"], p["c"])) >= SMALLEST_ANGLE,
                "Triangle too narrow")
        if form == "side_angle":
            require(p["b"] != p["c"], "Expected unequal known sides")
    elif form in ("angle", "angle_area"):
        sides = (p["a"], p["b"], p["c"])
        require(2 * max(sides) < sum(sides), "Triangle inequality failed")
        require(len(set(sides)) == 3, "Expected a scalene triangle")
        for angle in triangle_angles(*sides):
            require(25 <= angle <= 125 and abs(angle - 90) > 2,
                    "Triangle too narrow or effectively right-angled")
    else:
        require(40 <= p["B"] <= 120 and p["B"] != 90,
                "Invalid first included angle")
        shared = shared_side(p)
        for angle in (
            included_angle(p["AB"], shared, p["BC"]),
            included_angle(p["BC"], shared, p["AB"]),
        ):
            require(angle >= SMALLEST_ANGLE, "First triangle too narrow")
        require(abs(shared - p["AD"]) > 1, "Avoid an isosceles second triangle")
        if form == "linked_side":
            require(35 <= p["CAD"] <= 100 and p["CAD"] != 90,
                    "Invalid second included angle")
            last = third_side(shared, p["AD"], p["CAD"])
        else:
            last = p["CD"]
            angle = included_angle(shared, p["AD"], last)
            require(35 <= angle <= 110 and abs(angle - 90) > 2,
                    "Second included angle outside range")
        for angle in (
            included_angle(shared, last, p["AD"]),
            included_angle(p["AD"], last, shared),
        ):
            require(angle >= SMALLEST_ANGLE, "Second triangle too narrow")
    for value in results(p):
        require(1 <= value <= 400, "Result outside bounds")
        rounded_value(value)


# ------------------------------------------------------------ wording

def letters(p):
    return dict(zip("XYZ", p["names"]))


def side_name(first, second):
    return "".join(sorted(first + second))


def angle_name(vertex, first, second):
    ends = sorted(first + second)
    return "angle " + ends[0] + vertex + ends[1]


def cm(value):
    return "{} cm".format(value)


def degrees(value):
    return "{}°".format(value)


# ------------------------------------------------------------ diagrams

def triangle_points(p):
    """True figure coordinates for roles X, Y and Z."""
    b, c = p["b"], p["c"]
    if p["form"] in ("side", "side_angle"):
        angle = p["X"]
    else:
        angle = included_angle(b, c, p["a"])
    turn = math.radians(angle)
    return {
        "X": (0.0, 0.0),
        "Y": (float(c), 0.0),
        "Z": (b * math.cos(turn), b * math.sin(turn)),
    }


def quadrilateral_points(p):
    """True coordinates for ABCD, with B and D on opposite sides of AC."""
    shared = shared_side(p)
    along = (p["AB"] ** 2 - p["BC"] ** 2 + shared ** 2) / (2 * shared)
    below = -math.sqrt(max(0.0, p["AB"] ** 2 - along ** 2))
    if p["form"] == "linked_side":
        angle = p["CAD"]
    else:
        angle = included_angle(shared, p["AD"], p["CD"])
    turn = math.radians(angle)
    return {
        "A": (0.0, 0.0),
        "B": (along, below),
        "C": (shared, 0.0),
        "D": (p["AD"] * math.cos(turn), p["AD"] * math.sin(turn)),
    }


def build_scene(points, outline, names, sides, angles, orientation, dashed=()):
    """Place the figure, then label vertices, sides and angles in canvas points.

    sides: (first, second, inside, text) with the label kept away from inside.
    angles: (vertex, first, second, text) with the label on the bisector.
    """
    placed, height = figures.place(points, orientation)
    centre_x = sum(placed[role][0] for role in outline) / len(outline)
    centre_y = sum(placed[role][1] for role in outline) / len(outline)
    nodes = [{"type": "polygon", "points": [placed[role] for role in outline]}]
    for first, second in dashed:
        nodes.append({"type": "line", "points": [placed[first], placed[second]],
                      "dashed": True})
    for role in outline:
        x, y = placed[role]
        outward = figures.unit((x - centre_x, y - centre_y))
        nodes.append({
            "type": "label",
            "point": figures.rounded((x + outward[0] * VERTEX_GAP,
                                      y + outward[1] * VERTEX_GAP)),
            "text": names[role],
        })
    for first, second, inside, text in sides:
        nodes.append({
            "type": "label",
            "point": figures.side_label(placed[first], placed[second],
                                        placed[inside], len(text)),
            "text": text,
        })
    for vertex, first, second, text in angles:
        nodes.append({
            "type": "label",
            "point": figures.angle_label(placed[vertex], placed[first],
                                         placed[second], len(text)),
            "text": text,
        })
    return {
        "kind": "scene", "version": 1, "width": 360, "height": height,
        "caption": "Not drawn accurately", "nodes": nodes,
    }


# ------------------------------------------------------------ presentation

def presentation(p, level):
    if level == 4:
        return linked_presentation(p)
    form = p["form"]
    names = letters(p)
    X, Y, Z = names["X"], names["Y"], names["Z"]
    XY, XZ, YZ = side_name(X, Y), side_name(X, Z), side_name(Y, Z)
    at_X, at_Y = angle_name(X, Y, Z), angle_name(Y, X, Z)
    if form in ("side", "side_angle"):
        text = "In triangle ABC, {} = {} cm, {} = {} cm and {} = {} degrees. ".format(
            XY, p["c"], XZ, p["b"], at_X, p["X"])
        if form == "side":
            text += "Find {}.".format(YZ)
        else:
            text += (
                "(a) Find {0}. (b) Hence find {1}. "
                "Use your unrounded value of {0} in part (b)."
            ).format(YZ, at_Y)
        sides = [("X", "Y", "Z", cm(p["c"])), ("X", "Z", "Y", cm(p["b"])),
                 ("Y", "Z", "X", "x")]
        angles = [("X", "Y", "Z", degrees(p["X"]))]
        if form == "side_angle":
            angles.append(("Y", "X", "Z", "y"))
    else:
        # List the sides alphabetically so the order never hints at the angle.
        lengths = sorted(((XY, p["c"]), (XZ, p["b"]), (YZ, p["a"])))
        text = "In triangle ABC, {} = {} cm, {} = {} cm and {} = {} cm. ".format(
            *[item for pair in lengths for item in pair])
        if form == "angle":
            text += "Find {}.".format(at_X)
        else:
            text += (
                "(a) Find {}. (b) Hence find the area of triangle ABC. "
                "Use your unrounded angle in part (b)."
            ).format(at_X)
        sides = [("X", "Y", "Z", cm(p["c"])), ("X", "Z", "Y", cm(p["b"])),
                 ("Y", "Z", "X", cm(p["a"]))]
        angles = [("X", "Y", "Z", "x")]
    scene = build_scene(triangle_points(p), ("X", "Y", "Z"), names,
                        sides, angles, p["orientation"])
    return Content(text + " Give answers to 1 decimal place."), (scene,)


def linked_presentation(p):
    text = (
        "Triangles ABC and ACD share AC and lie on opposite sides of AC. "
        "AB = {AB} cm, BC = {BC} cm, angle ABC = {B} degrees, AD = {AD} cm and "
    ).format(**p)
    sides = [("A", "B", "C", cm(p["AB"])), ("B", "C", "A", cm(p["BC"])),
             ("A", "D", "C", cm(p["AD"]))]
    angles = [("B", "A", "C", degrees(p["B"]))]
    if p["form"] == "linked_side":
        text += "angle CAD = {} degrees. Find CD.".format(p["CAD"])
        sides.append(("C", "D", "A", "x"))
        angles.append(("A", "C", "D", degrees(p["CAD"])))
    else:
        text += "CD = {} cm. Find angle CAD.".format(p["CD"])
        sides.append(("C", "D", "A", cm(p["CD"])))
        angles.append(("A", "C", "D", "x"))
    text += " Do not round the shared length AC during your calculation."
    scene = build_scene(
        quadrilateral_points(p), ("A", "B", "C", "D"),
        {role: role for role in "ABCD"}, sides, angles, p["orientation"],
        dashed=(("A", "C"),),
    )
    return Content(text + " Give answers to 1 decimal place."), (scene,)


def answer_for(p, level):
    form = p["form"]
    values = [rounded_value(value) for value in results(p)]
    if form == "angle_area":
        answer = {
            "kind": "angle_and_area",
            "angle": rational_text(values[0]),
            "area": rational_text(values[1]),
        }
        display = "(a) {} degrees; (b) {} cm²".format(
            one_decimal_text(values[0]), one_decimal_text(values[1]))
    elif form == "side_angle":
        answer = {
            "kind": "side_and_angle",
            "side": rational_text(values[0]),
            "angle": rational_text(values[1]),
        }
        display = "(a) {} cm; (b) {} degrees".format(
            one_decimal_text(values[0]), one_decimal_text(values[1]))
    else:
        unit = "degrees" if form in ("angle", "linked_angle") else "cm"
        answer = {"kind": "rounded_measure",
                  "value": rational_text(values[0]), "unit": unit}
        display = one_decimal_text(values[0]) + " " + unit
    return answer, Content(display)


def draw_parameters(rng, level):
    form = rng.choice(FORMS[level])
    p = {"form": form, "orientation": [0, False]}
    if level < 4:
        p["names"] = rng.choice(NAMINGS)
    if form in ("side", "side_angle"):
        p.update(b=rng.randint(5, 20), c=rng.randint(5, 20),
                 X=rng.randrange(35, 126, 5))
    elif form in ("angle", "angle_area"):
        p.update(a=rng.randint(5, 20), b=rng.randint(5, 20), c=rng.randint(5, 20))
    else:
        p.update(AB=rng.randint(5, 20), BC=rng.randint(5, 20),
                 AD=rng.randint(5, 20), B=rng.randrange(40, 121, 5))
        if form == "linked_side":
            p["CAD"] = rng.randrange(35, 101, 5)
        else:
            p["CD"] = rng.randint(5, 20)
    return p


# ------------------------------------------------------------ generator

class CosineRule:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        for attempt in range(1000):
            p = draw_parameters(rng, difficulty)
            try:
                check_parameters(p, difficulty)
                p["orientation"] = figures.choose_orientation(
                    rng, lambda orientation: presentation(
                        dict(p, orientation=orientation), difficulty)[1][0])
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a cosine-rule question")
        prompt, visuals = presentation(p, difficulty)
        answer, display = answer_for(p, difficulty)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=WORKING_LINES[difficulty]),
            parameters=p, question_visuals=visuals,
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
        answer, display = answer_for(q.parameters, q.difficulty)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Answer display mismatch")
        prompt, visuals = presentation(q.parameters, q.difficulty)
        require(q.prompt == prompt, "Prompt mismatch")
        require(q.visual_assets("questions") == visuals, "Diagram mismatch")
        require(q.visual_assets("answers") == (), "Unexpected answer visuals")
        return True

    def validate_independently(self, q):
        """Rebuild from coordinates, Heron's area and atan2; never the cosine rule."""
        p = q.parameters
        form = p.get("form")
        require(form in FORMS.get(q.difficulty, ()), "Unexpected form")

        def point_at(length, angle):
            turn = math.radians(angle)
            return (length * math.cos(turn), length * math.sin(turn))

        def gap(first, second):
            return math.hypot(first[0] - second[0], first[1] - second[1])

        def turn_at(vertex, first, second):
            u = (first[0] - vertex[0], first[1] - vertex[1])
            v = (second[0] - vertex[0], second[1] - vertex[1])
            return math.degrees(math.atan2(abs(u[0] * v[1] - u[1] * v[0]),
                                           u[0] * v[0] + u[1] * v[1]))

        def heron(opposite, first, second):
            half = (opposite + first + second) / 2
            area = math.sqrt(max(0.0, half * (half - opposite)
                                 * (half - first) * (half - second)))
            angle = math.degrees(math.atan2(
                4 * area, first * first + second * second - opposite * opposite))
            return angle, area

        if form in ("side", "side_angle"):
            X, Y, Z = (0.0, 0.0), (float(p["c"]), 0.0), point_at(p["b"], p["X"])
            side = gap(Y, Z)
            expected = ({"value": side} if form == "side"
                        else {"side": side, "angle": turn_at(Y, X, Z)})
        elif form in ("angle", "angle_area"):
            angle, area = heron(p["a"], p["b"], p["c"])
            expected = ({"value": angle} if form == "angle"
                        else {"angle": angle, "area": area})
        else:
            # B at the origin with BA along the axis, so AC is a plain distance.
            shared = gap((float(p["AB"]), 0.0), point_at(p["BC"], p["B"]))
            if form == "linked_side":
                expected = {"value": gap((shared, 0.0), point_at(p["AD"], p["CAD"]))}
            else:
                expected = {"value": heron(p["CD"], shared, p["AD"])[0]}
        require(set(q.answer) - {"kind", "unit"} == set(expected),
                "Answer parts mismatch")
        for key, value in expected.items():
            stated = Fraction(q.answer[key])
            require((stated * 10).denominator == 1, "Expected exact tenths")
            require(abs(value - float(stated)) < 0.05,
                    "Independent reconstruction disagrees")
        return True