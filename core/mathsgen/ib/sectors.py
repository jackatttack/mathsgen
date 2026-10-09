"""IB AI SL arcs, sectors and segments (degrees).

Level 1 arc, area and perimeter; level 2 a segment; level 3 a triangular
field beside a major sector; level 4 a curved track whose radius comes
from a chord, then the area and volume of the annular sector.
"""
import math
from fractions import Fraction

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from . import common as ib
from . import diagrams
from . import trig


# --- Editable pools ---------------------------------------------------------
RADII = tuple(range(4, 21))
SECTOR_ANGLES = tuple(range(20, 301, 5))
SEGMENT_ANGLES = tuple(range(40, 171, 5))
FIELD_SIDES = tuple(range(10, 31))
FIELD_ANGLES = tuple(range(50, 121, 2))
GOAT_RADII = tuple(range(4, 13))
CHORDS = tuple(range(30, 81, 2))
OFFSETS = tuple(range(10, 41))
WIDTHS = ("1", "1.5", "2", "2.5", "3")
DEPTHS = (10, 12, 15, 20)


# ------------------------------------------------------------ mathematics

def arc_length(radius, angle):
    return Fraction(angle, 360) * 2 * trig.pi() * radius


def sector_area(radius, angle):
    return Fraction(angle, 360) * trig.pi() * radius * radius


def track(p):
    """(half chord, radius, angle BFM in degrees) for the track."""
    half = Fraction(p["chord"], 2)
    radius = trig.sqrt(half * half + p["offset"] ** 2)
    return half, radius, trig.atan_deg(half / p["offset"])


def sector_scene(radius, angle):
    turn = math.radians(angle)
    middle = math.radians(angle / 2)
    points = {"O": (0, 0), "A": (radius, 0), "B": (radius * math.cos(turn), radius * math.sin(turn)),
              "T": (0.32 * radius * math.cos(middle), 0.32 * radius * math.sin(middle))}
    return diagrams.figure(points, lines=[("O", "A"), ("O", "B")],
                           names={"O": "O", "A": "A", "B": "B"},
                           sides=[("O", "A", "{} cm".format(radius))],
                           arcs=[("O", radius, 0, angle), ("O", radius * 0.18, 0, angle)],
                           labels=[("T", "{}°".format(angle))])


def field_scene(p):
    half = p["angle"] / 2
    to_b, to_c = math.radians(270 + half), math.radians(270 - half)
    points = {"A": (0, 0), "B": (p["c"] * math.cos(to_b), p["c"] * math.sin(to_b)),
              "C": (p["b"] * math.cos(to_c), p["b"] * math.sin(to_c)),
              "G": (0, p["goat"] * 0.55)}
    return diagrams.figure(points, polygons=[("A", "B", "C")], names={"A": "A", "B": "B", "C": "C"},
                           sides=[("A", "B", "{} m".format(p["c"])), ("A", "C", "{} m".format(p["b"]))],
                           angles=[("A", "B", "C", "{}°".format(p["angle"]))],
                           arcs=[("A", p["goat"], 270 + half, 360 - p["angle"])],
                           labels=[("G", "goat")])


def track_scene(p):
    half, radius, _ = track(p)
    r, w = float(radius), float(Fraction(p["width"]))
    start = math.degrees(math.atan2(p["offset"], float(half)))
    sweep = 180 - 2 * start
    scale_out = (r + w) / r
    points = {"F": (0, 0), "M": (0, p["offset"]), "A": (float(half), p["offset"]),
              "B": (-float(half), p["offset"])}
    points["C"] = (points["A"][0] * scale_out, points["A"][1] * scale_out)
    points["D"] = (points["B"][0] * scale_out, points["B"][1] * scale_out)
    return diagrams.figure(points, lines=[("A", "C"), ("B", "D")],
                           dashed=[("F", "A"), ("F", "B"), ("F", "M"), ("A", "B")],
                           names={role: role for role in ("A", "B", "C", "D", "F", "M")},
                           arcs=[("F", r, start, sweep), ("F", r + w, start, sweep)],
                           right_angles=[("M", "F", "A")])


# ------------------------------------------------------------ generator

class ArcsSectors(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.geometry.arcs_sectors",
        version=1,
        topic=ib.TOPIC,
        subtopic="geometry_and_trigonometry",
        title="Arcs, sectors and segments",
        difficulty_descriptions={
            1: "Arc length, sector area and perimeter.",
            2: "Segment: sector and triangle areas, chord and perimeter.",
            3: "Compare a triangular field with a major sector.",
            4: "Curved track: radius from a chord, arc, annular area and volume.",
        },
        tags=ib.BASE_TAGS + ("arcs", "sectors", "segments", "annulus"),
    )
    keys = {
        1: {"radius", "angle"},
        2: {"radius", "angle"},
        3: {"b", "c", "angle", "goat"},
        4: {"chord", "offset", "width", "depth"},
    }

    def build(self, level, rng):
        def check(p):
            self.check_rules(p, level)
            diagrams.require_drawable(self.parts(p, level))
        return ib.pick_valid(rng, lambda r: self.candidate(level, r), check)

    def candidate(self, level, rng):
        if level in (1, 2):
            return {"radius": rng.choice(RADII),
                    "angle": rng.choice(SECTOR_ANGLES if level == 1 else SEGMENT_ANGLES)}
        if level == 3:
            return {"b": rng.choice(FIELD_SIDES), "c": rng.choice(FIELD_SIDES),
                    "angle": rng.choice(FIELD_ANGLES), "goat": rng.choice(GOAT_RADII)}
        return {"chord": rng.choice(CHORDS), "offset": rng.choice(OFFSETS),
                "width": rng.choice(WIDTHS), "depth": rng.choice(DEPTHS)}

    def check_rules(self, p, level):
        if level in (1, 2):
            require(p["radius"] in RADII, "Radius outside pool")
            require(p["angle"] in (SECTOR_ANGLES if level == 1 else SEGMENT_ANGLES), "Angle outside pool")
        elif level == 3:
            require(p["b"] in FIELD_SIDES and p["c"] in FIELD_SIDES and p["angle"] in FIELD_ANGLES,
                    "Field outside pools")
            require(p["goat"] in GOAT_RADII and p["goat"] < min(p["b"], p["c"]) - 2,
                    "Goat radius must be shorter than both sides")
            triangle = trig.triangle_area(p["b"], p["c"], p["angle"])
            require(abs(triangle - sector_area(p["goat"], 360 - p["angle"])) >= 1, "Fields too close")
        else:
            require(p["chord"] in CHORDS and p["offset"] in OFFSETS, "Track outside pools")
            require(p["width"] in WIDTHS and p["depth"] in DEPTHS, "Track outside pools")
            require(Fraction(p["chord"], 2) >= p["offset"] * Fraction(3, 5), "Arc too flat to draw")

    def parts(self, p, level):
        if level in (1, 2):
            r, angle = p["radius"], p["angle"]
            arc, area = arc_length(r, angle), sector_area(r, angle)
            context = ["The diagram shows a sector OAB of a circle with centre O, radius {} cm and "
                       "angle AOB = {}°.".format(r, angle)]
            if level == 1:
                parts = ib.assemble(context, [
                    ib.part("a", "Find the length of the arc AB.", 2, "{} cm".format(ib.sf3(arc)), arc),
                    ib.part("b", "Find the area of the sector.", 2, "{} cm^2".format(ib.sf3(area)), area),
                    ib.part("c", "Find the perimeter of the sector.", 1,
                            "{} cm".format(ib.sf3(arc + 2 * r)), arc + 2 * r),
                ])
            else:
                triangle = trig.triangle_area(r, r, angle)
                chord = trig.cosine_rule_side(r, r, angle)
                parts = ib.assemble(context, [
                    ib.part("a", "Find the area of the sector.", 2, "{} cm^2".format(ib.sf3(area)), area),
                    ib.part("b", "Find the area of triangle OAB.", 2,
                            "{} cm^2".format(ib.sf3(triangle)), triangle),
                    ib.part("c", "Hence find the area of the segment between the chord AB and the arc.", 1,
                            "{} cm^2".format(ib.sf3(area - triangle)), area - triangle),
                    ib.part("d", "Find the length of the chord AB.", 2, "{} cm".format(ib.sf3(chord)), chord),
                    ib.part("e", "Find the perimeter of the segment.", 1,
                            "{} cm".format(ib.sf3(chord + arc)), chord + arc),
                ])
            parts["question_visuals"] = (sector_scene(r, angle),)
            return parts
        if level == 3:
            triangle = trig.triangle_area(p["b"], p["c"], p["angle"])
            goat = sector_area(p["goat"], 360 - p["angle"])
            winner = "The sheep's field" if triangle > goat else "The goat's field"
            context = ["A sheep grazes in triangular field ABC, where AC = {} m, AB = {} m and angle "
                       "CAB = {}°. A goat grazes in the major sector with centre A and radius {} m "
                       "outside the triangle, as shown.".format(p["b"], p["c"], p["angle"], p["goat"])]
            parts = ib.assemble(context, [
                ib.part("a", "Find the area of the sheep's field.", 2, "{} m^2".format(ib.sf3(triangle)), triangle),
                ib.part("b", "Find the area of the goat's field.", 3, "{} m^2".format(ib.sf3(goat)), goat),
                ib.part("c", "Determine which animal has the larger field, and by how many square metres.", 1,
                        "{} is larger, by {} m^2".format(winner, ib.sf3(abs(triangle - goat))),
                        abs(triangle - goat)),
            ])
            parts["question_visuals"] = (field_scene(p),)
            return parts
        half, radius, angle = track(p)
        width = Fraction(p["width"])
        arc = arc_length(radius, 2 * angle)
        area = sector_area(radius + width, 2 * angle) - sector_area(radius, 2 * angle)
        volume = area * Fraction(p["depth"], 100)
        context = ["The inner edge of a curved jogging track is an arc AB of a circle with centre F. "
                   "The chord AB = {} m and M is its midpoint. FM = {} m and is perpendicular to AB. "
                   "The outer edge CD is an arc with the same centre, and the track is {} m wide.".format(
                       p["chord"], p["offset"], p["width"])]
        parts = ib.assemble(context, [
            ib.part("a", "Write down BM.", 1, "{} m".format(ib.nice(half)), half),
            ib.part("b", "Find BF.", 2, "{} m".format(ib.sf3(radius)), radius),
            ib.part("c", "Find angle BFM.", 2, "{}°".format(ib.sf3(angle)), angle),
            ib.part("d", "Hence find the length of the arc AB.", 3, "{} m".format(ib.sf3(arc)), arc),
            ib.part("e", "Find the area of the curved part of the track, ABDC.", 3,
                    "{} m^2".format(ib.sf3(area)), area),
            ib.part("f", "The concrete base of the track is {} cm deep. Find the volume of concrete "
                    "needed for the curved part.".format(p["depth"]), 2, "{} m^3".format(ib.sf3(volume)), volume),
        ])
        parts["question_visuals"] = (track_scene(p),)
        return parts

    def validate_independently(self, question):
        """Radians throughout: arc = r theta, sector = r^2 theta / 2."""
        p, level = question.parameters, question.difficulty
        values = ib.answer_values(question)
        if level in (1, 2):
            r, theta = p["radius"], math.radians(p["angle"])
            if level == 1:
                require(ib.close(values["a"], r * theta) and ib.close(values["b"], r * r * theta / 2)
                        and ib.close(values["c"], r * theta + 2 * r), "Independent sector failed")
            else:
                chord = 2 * r * math.sin(theta / 2)
                triangle = r * r * math.sin(theta) / 2
                require(ib.close(values["b"], triangle) and ib.close(values["d"], chord)
                        and ib.close(values["c"], r * r * theta / 2 - triangle), "Independent segment failed")
            return True
        if level == 3:
            triangle = p["b"] * p["c"] * math.sin(math.radians(p["angle"])) / 2
            goat = p["goat"] ** 2 * math.radians(360 - p["angle"]) / 2
            require(ib.close(values["a"], triangle) and ib.close(values["b"], goat), "Independent fields failed")
            return True
        half = p["chord"] / 2
        radius = math.hypot(half, p["offset"])
        theta = 2 * math.atan2(half, p["offset"])
        width = float(Fraction(p["width"]))
        area = ((radius + width) ** 2 - radius ** 2) * theta / 2
        require(ib.close(values["b"], radius) and ib.close(values["d"], radius * theta), "Independent arc failed")
        require(ib.close(values["e"], area) and ib.close(values["f"], area * p["depth"] / 100),
                "Independent track failed")
        return True