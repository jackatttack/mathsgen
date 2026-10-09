"""IB AI SL three-dimensional solids, drawn with the GCSE solid figures.

Level 1 formula-booklet volumes and surface areas; level 2 a right
square pyramid; level 3 diagonals of a cuboid and the angle to the base;
level 4 a sector rolled into a cone.
"""
import math
from fractions import Fraction

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from .. import solid_figures
from ..three_d_trig import cuboid_scene
from . import common as ib
from . import diagrams
from . import trig
from .sectors import sector_scene


def pyramid_scene(side, edge, height):
    """Square-based pyramid as in solid_figures.pyramid_scene, labelled with the
    base side and the sloping edge (IB gives the edge and asks for the height)."""
    turn = math.radians(solid_figures.DEPTH_ANGLE)
    dx = side * solid_figures.DEPTH_SCALE * math.cos(turn)
    dy = side * solid_figures.DEPTH_SCALE * math.sin(turn)
    raw = {"A": (0, 0), "B": (side, 0), "C": (side + dx, dy), "D": (dx, dy)}
    raw["P"] = ((side + dx) / 2, dy / 2 + height)
    place, scene_height = solid_figures.fit(list(raw.values()))
    p = {name: place(point) for name, point in raw.items()}
    line = solid_figures.line
    nodes = [
        line(p["A"], p["B"]), line(p["B"], p["C"]),
        line(p["C"], p["D"], dashed=True), line(p["D"], p["A"], dashed=True),
        line(p["P"], p["A"]), line(p["P"], p["B"]), line(p["P"], p["C"]),
        line(p["P"], p["D"], dashed=True),
        solid_figures.side_text(p["A"], p["B"], p["P"], "{} cm".format(side)),
        solid_figures.side_text(p["P"], p["B"], p["A"], "{} cm".format(edge)),
    ]
    return solid_figures.scene(nodes, scene_height)


# --- Editable pools ---------------------------------------------------------
SHAPES = {
    "cylinder": "A tin is a closed cylinder with radius {r} cm and height {h} cm.",
    "cone": "A solid cone has base radius {r} cm and height {h} cm.",
    "sphere": "A ball is a sphere with radius {r} cm.",
}
RADII = tuple(range(2, 16))
HEIGHTS = tuple(range(4, 31))
BASES = tuple(range(6, 21, 2))
EDGES = tuple(range(6, 31))
CUBOID = tuple(range(3, 21))
ROLL_RADII = tuple(range(10, 41))
ROLL_ANGLES = tuple(range(90, 301, 10))


# ------------------------------------------------------------ generator

class Solids(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.geometry.solids_3d",
        version=1,
        topic=ib.TOPIC,
        subtopic="geometry_and_trigonometry",
        title="Three-dimensional solids",
        difficulty_descriptions={
            1: "Volume and surface area of a cylinder, cone or sphere.",
            2: "Right square pyramid: height, volume and the angle of an edge to the base.",
            3: "Cuboid: base and space diagonals, and the angle to the base.",
            4: "A sector rolled into a cone: arc, radius, height and volume.",
        },
        tags=ib.BASE_TAGS + ("volume", "surface_area", "pythagoras_3d", "angles_3d"),
    )
    keys = {
        1: {"shape", "r", "h"},
        2: {"base", "edge"},
        3: {"length", "width", "height"},
        4: {"radius", "angle"},
    }

    def build(self, level, rng):
        def check(p):
            self.check_rules(p, level)
            diagrams.require_drawable(self.parts(p, level))
        return ib.pick_valid(rng, lambda r: self.candidate(level, r), check)

    def parts(self, p, level):
        built = self.text_parts(p, level)
        built["question_visuals"] = (self.visual(p, level),)
        return built

    def visual(self, p, level):
        cm = "{} cm".format
        if level == 1:
            r, h = p["r"], p["h"]
            if p["shape"] == "cylinder":
                return solid_figures.cylinder_scene(r, h, cm(r), cm(h))
            if p["shape"] == "cone":
                return solid_figures.cone_scene(r, h, cm(r), cm(h))
            return solid_figures.sphere_scene(r, cm(r))
        if level == 2:
            height = float(trig.sqrt(p["edge"] ** 2 - Fraction(p["base"] ** 2, 2)))
            return pyramid_scene(p["base"], p["edge"], height)
        if level == 3:
            return cuboid_scene({"width": p["length"], "depth": p["width"],
                                 "height": p["height"], "form": "diagonal_angle"})
        return sector_scene(p["radius"], p["angle"])

    def candidate(self, level, rng):
        if level == 1:
            shape = rng.choice(tuple(SHAPES))
            return {"shape": shape, "r": rng.choice(RADII), "h": 0 if shape == "sphere" else rng.choice(HEIGHTS)}
        if level == 2:
            return {"base": rng.choice(BASES), "edge": rng.choice(EDGES)}
        if level == 3:
            return {"length": rng.choice(CUBOID), "width": rng.choice(CUBOID), "height": rng.choice(CUBOID)}
        return {"radius": rng.choice(ROLL_RADII), "angle": rng.choice(ROLL_ANGLES)}

    def check_rules(self, p, level):
        if level == 1:
            require(p["shape"] in SHAPES and p["r"] in RADII, "Solid outside pools")
            if p["shape"] == "sphere":
                require(p["h"] == 0, "A sphere has no height")
            else:
                require(p["h"] in HEIGHTS, "Height outside pool")
        elif level == 2:
            require(p["base"] in BASES and p["edge"] in EDGES, "Pyramid outside pools")
            require(2 * p["edge"] ** 2 > p["base"] ** 2 * Fraction(3, 2), "Pyramid too flat")
        elif level == 3:
            require(all(p[k] in CUBOID for k in ("length", "width", "height")), "Cuboid outside pool")
            require(p["length"] != p["width"], "Use a non-square base")
        else:
            require(p["radius"] in ROLL_RADII and p["angle"] in ROLL_ANGLES, "Sector outside pools")

    def text_parts(self, p, level):
        pi = trig.pi()
        if level == 1:
            r, h = p["r"], p["h"]
            context = [SHAPES[p["shape"]].format(r=r, h=h)]
            if p["shape"] == "cylinder":
                volume, surface = pi * r * r * h, 2 * pi * r * r + 2 * pi * r * h
                surface_task = "Find the total surface area of the tin."
            elif p["shape"] == "cone":
                slant = trig.sqrt(r * r + h * h)
                volume, surface = pi * r * r * h / 3, pi * r * r + pi * r * slant
                surface_task = "Find the total surface area of the cone, including its base."
            else:
                volume, surface = 4 * pi * r ** 3 / 3, 4 * pi * r * r
                surface_task = "Find the surface area of the ball."
            return ib.assemble(context, [
                ib.part("a", "Find the volume.", 2, "{} cm^3".format(ib.sf3(volume)), volume),
                ib.part("b", surface_task, 2, "{} cm^2".format(ib.sf3(surface)), surface),
            ])
        if level == 2:
            s, e = p["base"], p["edge"]
            diagonal = trig.sqrt(2 * s * s)
            height = trig.sqrt(e * e - Fraction(s * s, 2))
            volume = s * s * height / 3
            angle = trig.atan_deg(height / (diagonal / 2))
            context = ["A right pyramid has a square base of side {} cm. Each edge from the apex to a "
                       "corner of the base is {} cm long.".format(s, e)]
            return ib.assemble(context, [
                ib.part("a", "Find the length of a diagonal of the base.", 1,
                        "{} cm".format(ib.sf3(diagonal)), diagonal),
                ib.part("b", "Find the height of the pyramid.", 2, "{} cm".format(ib.sf3(height)), height),
                ib.part("c", "Find the volume of the pyramid.", 2, "{} cm^3".format(ib.sf3(volume)), volume),
                ib.part("d", "Find the angle between an edge from the apex and the base.", 2,
                        "{}°".format(ib.sf3(angle)), angle),
            ])
        if level == 3:
            l, w, h = p["length"], p["width"], p["height"]
            base = trig.sqrt(l * l + w * w)
            space = trig.sqrt(l * l + w * w + h * h)
            angle = trig.atan_deg(h / base)
            context = ["A box is a cuboid {} cm long, {} cm wide and {} cm high.".format(l, w, h)]
            return ib.assemble(context, [
                ib.part("a", "Find the length of a diagonal of the base.", 2, "{} cm".format(ib.sf3(base)), base),
                ib.part("b", "Find the length of the longest rod that fits inside the box.", 2,
                        "{} cm".format(ib.sf3(space)), space),
                ib.part("c", "Find the angle between this rod and the base of the box.", 2,
                        "{}°".format(ib.sf3(angle)), angle),
            ])
        big, angle = p["radius"], p["angle"]
        arc = Fraction(angle, 360) * 2 * pi * big
        small = Fraction(big * angle, 360)
        height = trig.sqrt(big * big - small * small)
        volume = pi * small * small * height / 3
        context = ["A sector of a circle has radius {} cm and angle {}°. Its two straight edges are "
                   "joined to make a cone, with no overlap.".format(big, angle)]
        return ib.assemble(context, [
            ib.part("a", "Find the arc length of the sector.", 2, "{} cm".format(ib.sf3(arc)), arc),
            ib.part("b", "Find the radius of the base of the cone.", 2, "{} cm".format(ib.nice(small)), small),
            ib.part("c", "Find the height of the cone.", 2, "{} cm".format(ib.sf3(height)), height),
            ib.part("d", "Find the volume of the cone.", 2, "{} cm^3".format(ib.sf3(volume)), volume),
        ])

    def validate_independently(self, question):
        """Float formulas from first principles."""
        p, level = question.parameters, question.difficulty
        values = ib.answer_values(question)
        if level == 1:
            r, h = p["r"], p["h"]
            if p["shape"] == "cylinder":
                expected = (math.pi * r * r * h, 2 * math.pi * r * (r + h))
            elif p["shape"] == "cone":
                expected = (math.pi * r * r * h / 3, math.pi * r * (r + math.hypot(r, h)))
            else:
                expected = (4 / 3 * math.pi * r ** 3, 4 * math.pi * r * r)
            require(ib.close(values["a"], expected[0]) and ib.close(values["b"], expected[1]),
                    "Independent solid failed")
        elif level == 2:
            s, e = p["base"], p["edge"]
            half = s / math.sqrt(2)
            height = math.sqrt(e * e - half * half)
            require(ib.close(values["b"], height) and ib.close(values["c"], s * s * height / 3)
                    and ib.close(values["d"], math.degrees(math.acos(half / e)), 1e-8),
                    "Independent pyramid failed")
        elif level == 3:
            l, w, h = p["length"], p["width"], p["height"]
            space = math.sqrt(l * l + w * w + h * h)
            require(ib.close(values["b"], space)
                    and ib.close(values["c"], math.degrees(math.asin(h / space)), 1e-8),
                    "Independent cuboid failed")
        else:
            big, angle = p["radius"], p["angle"]
            arc = math.radians(angle) * big
            small = arc / (2 * math.pi)
            height = math.sqrt(big * big - small * small)
            require(ib.close(values["a"], arc) and ib.close(values["b"], small)
                    and ib.close(values["d"], math.pi * small * small * height / 3), "Independent cone failed")
        return True