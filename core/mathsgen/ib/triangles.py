"""IB AI SL non-right-angled triangle trigonometry.

Level 1 cosine rule and area; level 2 cosine rule then an acute angle by
the sine rule; level 3 angles of elevation from the top and base of a
building; level 4 side, angle, area and the shortest distance to a side.
Diagrams use true coordinates. The independent check rebuilds each figure
from coordinates and uses atan2 and Heron's formula, never the rules.
"""
import math
from fractions import Fraction

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from . import common as ib
from . import diagrams
from . import trig


# --- Editable pools ---------------------------------------------------------
NAMINGS = (("A", "B", "C"), ("P", "Q", "R"), ("X", "Y", "Z"), ("D", "E", "F"))
UNITS = ("cm", "m")
SIDES = tuple(range(5, 26))
ANGLES = tuple(range(30, 141, 5))
HEIGHTS = tuple(range(50, 201, 2))
ELEVATIONS = tuple(range(20, 71))


# ------------------------------------------------------------ mathematics

def far_angle(p):
    """Angle at the end of side c (opposite side b), in degrees."""
    a = trig.cosine_rule_side(p["b"], p["c"], p["angle"])
    return trig.asin_deg(Fraction(p["b"]) * trig.sin_deg(p["angle"]) / a)


def far_angle_is_acute(p):
    b, c = p["b"], p["c"]
    a_squared = b * b + c * c - 2 * b * c * trig.cos_deg(p["angle"])
    return b * b < a_squared + c * c


def triangle_scene(p, show_angle=True):
    v, first, second = p["names"]
    turn = math.radians(p["angle"])
    points = {"V": (0, 0), "P": (p["c"], 0),
              "Q": (p["b"] * math.cos(turn), p["b"] * math.sin(turn))}
    unit = p["unit"]
    return diagrams.figure(
        points, polygons=[("V", "P", "Q")], names={"V": v, "P": first, "Q": second},
        sides=[("V", "P", "{} {}".format(p["c"], unit)), ("V", "Q", "{} {}".format(p["b"], unit))],
        angles=[("V", "P", "Q", "{}°".format(p["angle"]))] if show_angle else [])


def balloon(p):
    """(angle AHB, BH, height of H) for the elevation question."""
    alpha, beta, h = p["alpha"], p["beta"], p["height"]
    bh = h * trig.cos_deg(alpha) / trig.sin_deg(beta - alpha)
    return beta - alpha, bh, bh * trig.sin_deg(beta)


def balloon_scene(p):
    _, bh, top = balloon(p)
    across = float(bh * trig.cos_deg(p["beta"]))
    h = p["height"]
    points = {"B": (0, 0), "A": (0, h), "X": (across, 0), "H": (across, float(top)),
              "K": (across * 0.55, h)}
    return diagrams.figure(
        points, lines=[("A", "B"), ("B", "X"), ("X", "H"), ("A", "H"), ("B", "H")],
        dashed=[("A", "K")], names={"A": "A", "B": "B", "X": "X", "H": "H"},
        sides=[("A", "B", "{} m".format(h))],
        angles=[("A", "K", "H", "{}°".format(p["alpha"])), ("B", "X", "H", "{}°".format(p["beta"]))],
        right_angles=[("X", "B", "H")])


# ------------------------------------------------------------ generator

class TriangleTrigonometry(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.geometry.triangle_trigonometry",
        version=1,
        topic=ib.TOPIC,
        subtopic="geometry_and_trigonometry",
        title="Sine rule, cosine rule and triangle area",
        difficulty_descriptions={
            1: "Cosine rule for a side, then the area 1/2 ab sin C.",
            2: "Cosine rule, then an acute angle by the sine rule.",
            3: "Angles of elevation from the top and base of a building.",
            4: "Side, angle and area, then the shortest distance to a side.",
        },
        tags=ib.BASE_TAGS + ("sine_rule", "cosine_rule", "triangle_area", "elevation"),
    )
    keys = {
        1: {"names", "unit", "b", "c", "angle"},
        2: {"names", "unit", "b", "c", "angle"},
        3: {"height", "alpha", "beta"},
        4: {"names", "unit", "b", "c", "angle"},
    }

    def build(self, level, rng):
        def check(p):
            self.check_rules(p, level)
            diagrams.require_drawable(self.parts(p, level))
        return ib.pick_valid(rng, lambda r: self.candidate(level, r), check)

    def candidate(self, level, rng):
        if level == 3:
            alpha = rng.choice(ELEVATIONS[:26])
            return {"height": rng.choice(HEIGHTS), "alpha": alpha,
                    "beta": alpha + rng.randint(8, 30)}
        return {"names": list(rng.choice(NAMINGS)), "unit": rng.choice(UNITS),
                "b": rng.choice(SIDES), "c": rng.choice(SIDES), "angle": rng.choice(ANGLES)}

    def check_rules(self, p, level):
        if level == 3:
            require(p["height"] in HEIGHTS, "Height outside pool")
            require(p["alpha"] in ELEVATIONS and p["beta"] in ELEVATIONS
                    and p["beta"] - p["alpha"] >= 8, "Elevations outside rules")
            return
        require(isinstance(p["names"], list) and tuple(p["names"]) in NAMINGS, "Names outside pool")
        require(p["unit"] in UNITS, "Unknown unit")
        require(p["b"] in SIDES and p["c"] in SIDES and p["angle"] in ANGLES, "Triangle outside pools")
        require(p["b"] != p["c"], "Use two different sides")
        if level in (2, 4):
            require(far_angle_is_acute(p), "The angle asked for must be acute")
            require(far_angle(p) >= 15, "Angle too small to draw")

    def parts(self, p, level):
        if level == 3:
            angle, bh, top = balloon(p)
            context = ["A point H on a hot-air balloon is observed at the same moment from A, the "
                       "top of a vertical building, and from B, its base. The building is {} m tall. "
                       "The angle of elevation of H is {}° from A and {}° from B. X is the point on "
                       "the ground directly below H.".format(p["height"], p["alpha"], p["beta"])]
            parts = ib.assemble(context, [
                ib.part("a", "Find angle AHB.", 2, "{}°".format(angle), angle),
                ib.part("b", "Find BH.", 3, "{} m".format(ib.sf3(bh)), bh),
                ib.part("c", "Find the height of H above the ground.", 2, "{} m".format(ib.sf3(top)), top),
            ])
            parts["question_visuals"] = (balloon_scene(p),)
            return parts
        v, first, second = p["names"]
        unit = p["unit"]
        side = trig.cosine_rule_side(p["b"], p["c"], p["angle"])
        area = trig.triangle_area(p["b"], p["c"], p["angle"])
        context = ["In triangle {0}{1}{2}, {0}{1} = {3} {5}, {0}{2} = {4} {5} and angle {1}{0}{2} = "
                   "{6}°.".format(v, first, second, p["c"], p["b"], unit, p["angle"])]
        find_side = ib.part("a", "Find {}{}.".format(first, second), 3,
                            "{} {}".format(ib.sf3(side), unit), side)
        if level == 1:
            parts = ib.assemble(context, [
                find_side,
                ib.part("b", "Find the area of triangle {}{}{}.".format(v, first, second), 2,
                        "{} {}^2".format(ib.sf3(area), unit), area),
            ])
        else:
            angle = far_angle(p)
            angle_part = ib.part("b", "Given that angle {}{}{} is acute, find angle {}{}{}.".format(
                v, first, second, v, first, second), 3, "{}°".format(ib.sf3(angle)), angle)
            if level == 2:
                parts = ib.assemble(context, [find_side, angle_part])
            else:
                distance = 2 * area / side
                parts = ib.assemble(context, [
                    find_side, angle_part,
                    ib.part("c", "Find the area of triangle {}{}{}.".format(v, first, second), 2,
                            "{} {}^2".format(ib.sf3(area), unit), area),
                    ib.part("d", "Find the shortest distance from {} to the line {}{}.".format(
                        v, first, second), 2, "{} {}".format(ib.sf3(distance), unit), distance),
                ])
        parts["question_visuals"] = (triangle_scene(p),)
        return parts

    def validate_independently(self, question):
        """Coordinates, atan2 and Heron's formula."""
        p, level = question.parameters, question.difficulty
        values = ib.answer_values(question)
        if level == 3:
            alpha, beta = math.radians(p["alpha"]), math.radians(p["beta"])
            # B + s(cos beta, sin beta) = A + t(cos alpha, sin alpha), A = (0, h)
            determinant = math.cos(beta) * math.sin(alpha) - math.sin(beta) * math.cos(alpha)
            s = -p["height"] * math.cos(alpha) / determinant
            hx, hy = s * math.cos(beta), s * math.sin(beta)
            to_a = (0 - hx, p["height"] - hy)
            to_b = (-hx, -hy)
            angle = math.degrees(math.atan2(to_a[0] * to_b[1] - to_a[1] * to_b[0],
                                            to_a[0] * to_b[0] + to_a[1] * to_b[1]))
            require(ib.close(values["a"], abs(angle), 1e-8), "Independent angle failed")
            require(ib.close(values["b"], s) and ib.close(values["c"], hy), "Independent balloon failed")
            return True
        turn = math.radians(p["angle"])
        q = (p["b"] * math.cos(turn), p["b"] * math.sin(turn))
        side = math.dist((p["c"], 0), q)
        require(ib.close(values["a"], side), "Independent side failed")
        a, b, c = side, p["b"], p["c"]
        s = (a + b + c) / 2
        heron = math.sqrt(s * (s - a) * (s - b) * (s - c))
        if level == 1:
            require(ib.close(values["b"], heron, 1e-8), "Independent area failed")
            return True
        at_p = math.degrees(math.atan2(abs(q[1]), p["c"] - q[0]))
        require(ib.close(values["b"], at_p, 1e-8), "Independent angle failed")
        if level == 4:
            require(ib.close(values["c"], heron, 1e-8) and ib.close(values["d"], 2 * heron / side, 1e-8),
                    "Independent area or distance failed")
        return True