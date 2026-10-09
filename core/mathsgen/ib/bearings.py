"""IB AI SL bearings and distances.

Level 1 a two-leg journey; level 2 coordinates on a map; level 3 three
points (angle, distance and bearing); level 4 legs from speed and time.
Positions are built from (east, north) steps; diagrams draw north lines.
"""
import math
from fractions import Fraction

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from . import common as ib
from . import diagrams
from . import trig


# --- Editable pools ---------------------------------------------------------
DISTANCES = tuple(range(3, 16))
BEARINGS = tuple(range(5, 360, 5))
MAP_COORDINATES = tuple(range(0, 21))
SPEEDS = tuple(range(8, 31, 2))
TIMES = ("0.5", "1", "1.5", "2", "2.5", "3")


# ------------------------------------------------------------ mathematics

def journey(legs):
    """Positions after each (distance, bearing) leg, starting at the origin."""
    east, north = Fraction(0), Fraction(0)
    positions = [(east, north)]
    for distance, bearing in legs:
        de, dn = trig.step(distance, bearing)
        east, north = east + de, north + dn
        positions.append((east, north))
    return positions


def distance(first, second):
    return trig.sqrt((second[0] - first[0]) ** 2 + (second[1] - first[1]) ** 2)


def turn_angle(previous, corner, following):
    """Interior angle at corner, in degrees."""
    u = (previous[0] - corner[0], previous[1] - corner[1])
    v = (following[0] - corner[0], following[1] - corner[1])
    cosine = (u[0] * v[0] + u[1] * v[1]) / (distance(corner, previous) * distance(corner, following))
    return trig.acos_deg(max(Fraction(-1), min(Fraction(1), cosine)))


def journey_scene(positions, names, leg_labels, unit):
    reach = max(abs(float(v)) for point in positions for v in point) or 1
    arrow = 0.3 * reach
    points, lines, dashed, labels, sides = {}, [], [], [], []
    for index, ((east, north), name) in enumerate(zip(positions, names)):
        points[name] = (float(east), float(north))
        if index < len(positions) - 1:
            tip = "N" + str(index)
            points[tip] = (float(east), float(north) + arrow)
            points[tip + "t"] = (float(east), float(north) + arrow * 1.18)
            lines.append((name, tip))
            labels.append((tip + "t", "N"))
    for index in range(len(positions) - 1):
        lines.append((names[index], names[index + 1]))
        sides.append((names[index], names[index + 1], "{} {}".format(leg_labels[index], unit)))
    dashed.append((names[-1], names[0]))
    return diagrams.figure(points, lines=lines, dashed=dashed, names={n: n for n in names},
                           sides=sides, labels=labels)


# ------------------------------------------------------------ generator

class Bearings(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.geometry.bearings",
        version=1,
        topic=ib.TOPIC,
        subtopic="geometry_and_trigonometry",
        title="Bearings and distances",
        difficulty_descriptions={
            1: "Two-leg journey: distance from the start and the bearing back.",
            2: "Coordinates on a map: a distance and a bearing.",
            3: "Three points: the angle at the turn, a distance and a bearing.",
            4: "Legs from speed and time: distance, bearing and time to return.",
        },
        tags=ib.BASE_TAGS + ("bearings", "cosine_rule", "trigonometry"),
    )
    keys = {
        1: {"d1", "b1", "d2", "b2"},
        2: {"ax", "ay", "bx", "by"},
        3: {"d1", "b1", "d2", "b2"},
        4: {"v1", "t1", "b1", "v2", "t2", "b2", "v3"},
    }

    def build(self, level, rng):
        def check(p):
            self.check_rules(p, level)
            diagrams.require_drawable(self.parts(p, level))
        return ib.pick_valid(rng, lambda r: self.candidate(level, r), check)

    def candidate(self, level, rng):
        if level == 2:
            return {"ax": rng.choice(MAP_COORDINATES), "ay": rng.choice(MAP_COORDINATES),
                    "bx": rng.choice(MAP_COORDINATES), "by": rng.choice(MAP_COORDINATES)}
        if level == 4:
            return {"v1": rng.choice(SPEEDS), "t1": rng.choice(TIMES), "b1": rng.choice(BEARINGS),
                    "v2": rng.choice(SPEEDS), "t2": rng.choice(TIMES), "b2": rng.choice(BEARINGS),
                    "v3": rng.choice(SPEEDS)}
        return {"d1": rng.choice(DISTANCES), "b1": rng.choice(BEARINGS),
                "d2": rng.choice(DISTANCES), "b2": rng.choice(BEARINGS)}

    def legs(self, p, level):
        if level == 4:
            return [(p["v1"] * Fraction(p["t1"]), p["b1"]), (p["v2"] * Fraction(p["t2"]), p["b2"])]
        return [(p["d1"], p["b1"]), (p["d2"], p["b2"])]

    def check_rules(self, p, level):
        if level == 2:
            require(all(p[k] in MAP_COORDINATES for k in ("ax", "ay", "bx", "by")), "Coordinates outside pool")
            require(p["ax"] != p["bx"] and p["ay"] != p["by"], "Points must not share a grid line")
            return
        if level == 4:
            require(p["v1"] in SPEEDS and p["v2"] in SPEEDS and p["v3"] in SPEEDS, "Speeds outside pool")
            require(p["t1"] in TIMES and p["t2"] in TIMES, "Times outside pool")
        else:
            require(p["d1"] in DISTANCES and p["d2"] in DISTANCES, "Distances outside pool")
        require(p["b1"] in BEARINGS and p["b2"] in BEARINGS, "Bearings outside pool")
        turn = abs(p["b1"] - p["b2"]) % 360
        turn = min(turn, 360 - turn)
        require(40 <= turn <= 150, "The turn must be clear and not double back")

    def parts(self, p, level):
        if level == 2:
            a, b = (p["ax"], p["ay"]), (p["bx"], p["by"])
            length = distance(a, b)
            bearing = trig.bearing_of(a[0] - b[0], a[1] - b[1])
            context = ["On a map, distances are in metres east and north of an origin. Attraction A is "
                       "at ({}, {}) and attraction B is at ({}, {}).".format(*a, *b)]
            return ib.assemble(context, [
                ib.part("a", "Find the distance AB.", 2, "{} m".format(ib.sf3(length)), length),
                ib.part("b", "Find the bearing of A from B.", 3, trig.bearing_text(bearing), bearing),
            ])
        legs = self.legs(p, level)
        positions = journey(legs)
        start, corner, end = positions
        home = distance(end, start)
        back = trig.bearing_of(start[0] - end[0], start[1] - end[1])
        if level in (1, 4):
            names = ["S", "T", "E"]
            if level == 1:
                context = ["A boat leaves harbour S and sails {} km on a bearing of {}, to T. It then "
                           "sails {} km on a bearing of {}, to E.".format(
                               p["d1"], trig.bearing_text(p["b1"]), p["d2"], trig.bearing_text(p["b2"]))]
                parts = ib.assemble(context, [
                    ib.part("a", "Find the distance from E back to S.", 3, "{} km".format(ib.sf3(home)), home),
                    ib.part("b", "Find the bearing on which the boat must sail to return directly to S.", 3,
                            trig.bearing_text(back), back),
                ])
                labels = [p["d1"], p["d2"]]
            else:
                first, second = legs[0][0], legs[1][0]
                context = ["A ship leaves port S and sails at {} km/h for {} hours on a bearing of {}, to T. "
                           "It then sails at {} km/h for {} hours on a bearing of {}, to E.".format(
                               p["v1"], p["t1"], trig.bearing_text(p["b1"]),
                               p["v2"], p["t2"], trig.bearing_text(p["b2"]))]
                hours = home / p["v3"]
                parts = ib.assemble(context, [
                    ib.part("a", "Find the distances ST and TE.", 1,
                            "ST = {} km, TE = {} km".format(ib.nice(first), ib.nice(second)), first),
                    ib.part("b", "Find the distance from E back to S.", 3, "{} km".format(ib.sf3(home)), home),
                    ib.part("c", "Find the bearing on which the ship must sail to return directly to S.", 3,
                            trig.bearing_text(back), back),
                    ib.part("d", "The ship returns directly to S at {} km/h. Find the time taken.".format(p["v3"]),
                            1, "{} hours".format(ib.sf3(hours)), hours),
                ])
                labels = [ib.nice(first), ib.nice(second)]
            parts["question_visuals"] = (journey_scene(positions, names, labels, "km"),)
            return parts
        angle = turn_angle(start, corner, end)
        outward = trig.bearing_of(end[0], end[1])
        context = ["A hiker walks {} km from P on a bearing of {} to Q, then {} km on a bearing of {} "
                   "to R.".format(p["d1"], trig.bearing_text(p["b1"]), p["d2"], trig.bearing_text(p["b2"]))]
        parts = ib.assemble(context, [
            ib.part("a", "Find angle PQR.", 2, "{}°".format(ib.sf3(angle)), angle),
            ib.part("b", "Find the distance PR.", 3, "{} km".format(ib.sf3(home)), home),
            ib.part("c", "Find the bearing of R from P.", 3, trig.bearing_text(outward), outward),
        ])
        parts["question_visuals"] = (journey_scene(positions, ["P", "Q", "R"], [p["d1"], p["d2"]], "km"),)
        return parts

    def validate_independently(self, question):
        """Float coordinates and math.atan2 for every bearing."""
        p, level = question.parameters, question.difficulty
        values = ib.answer_values(question)

        def bearing(east, north):
            return math.degrees(math.atan2(east, north)) % 360

        if level == 2:
            de, dn = p["ax"] - p["bx"], p["ay"] - p["by"]
            require(ib.close(values["a"], math.hypot(de, dn)) and ib.close(values["b"], bearing(de, dn), 1e-8),
                    "Independent map failed")
            return True
        legs = [(float(d), b) for d, b in self.legs(p, level)]
        east = sum(d * math.sin(math.radians(b)) for d, b in legs)
        north = sum(d * math.cos(math.radians(b)) for d, b in legs)
        home = math.hypot(east, north)
        if level == 3:
            angle = 180 - abs((legs[1][1] - legs[0][1] + 180) % 360 - 180)
            require(ib.close(values["a"], angle, 1e-8), "Independent angle failed")
            require(ib.close(values["b"], home) and ib.close(values["c"], bearing(east, north), 1e-8),
                    "Independent distance or bearing failed")
            return True
        labels = ("a", "b") if level == 1 else ("b", "c")
        require(ib.close(values[labels[0]], home) and ib.close(values[labels[1]], bearing(-east, -north), 1e-8),
                "Independent return failed")
        if level == 4:
            require(ib.close(values["d"], home / p["v3"]), "Independent time failed")
        return True