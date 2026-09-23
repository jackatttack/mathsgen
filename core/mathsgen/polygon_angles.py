"""Polygon angle sums, regular angles and reverse angle reasoning."""
from fractions import Fraction
import math

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)
from . import figures

# Each gives whole-degree interior and exterior angles.
SIDE_COUNTS = (3, 4, 5, 6, 8, 9, 10, 12)
# Distinct regular polygons whose interior angles make exactly one full turn.
VERTEX_TRIPLES = (
    (3, 8, 24), (3, 9, 18), (3, 10, 15),
    (4, 5, 20), (4, 6, 12),
)
NAMES = {
    3: "triangle", 4: "quadrilateral", 5: "pentagon",
    6: "hexagon", 8: "octagon", 9: "nonagon",
    10: "decagon", 12: "dodecagon",
}

INFO = GeneratorInfo(
    id="geometry.angles.polygons", version=4,
    topic="geometry", subtopic="angles",
    title="Angles in polygons",
    difficulty_descriptions={
        1: "Find the sum of the interior angles of a polygon.",
        2: "Find an interior or exterior angle of a regular polygon.",
        3: "Reverse a regular angle, or find an irregular quadrilateral's exterior angle.",
        4: "Reason with regular polygons sharing a side or meeting at a vertex.",
    },
    tags=("geometry", "angles", "polygons", "regular", "reverse"),
)


def interior(n):
    return 180 - Fraction(360, n)


def advanced_diagram(p):
    form = p["form"]
    if form == "quadrilateral_exterior":
        vertices = [[65, 45], [295, 55], [270, 205], [85, 210]]
        nodes = [{"type": "polygon", "points": vertices}]
        positions = ([110, 75], [250, 84], [231, 177])
        for position, value in zip(positions, p["angles"]):
            nodes.append({
                "type": "label", "point": position,
                "tex": str(value) + r"^{\circ}",
            })
        # Extend one side at the fourth vertex to mark its exterior angle.
        nodes.extend((
            {"type": "line", "points": [vertices[3], [93, 253]],
             "dashed": True},
            {"type": "arc", "center": vertices[3], "radius": 22,
             "start": -2, "sweep": 84},
            {"type": "label", "point": [132, 245], "tex": r"x^{\circ}"},
        ))
        caption = "Angles not drawn to scale"
        height = 285
    else:
        centre = [180, 135]
        counts = (p["first_sides"], p["second_sides"],
                  int(recover(p, 4)))
        direction = -90.0
        nodes = [{"type": "circle", "center": centre,
                  "radius": 2, "shade": True}]
        for count, name in zip(counts, ("K", "L", "P")):
            radians = math.radians(direction)
            end = [centre[0] + 92 * math.cos(radians),
                   centre[1] + 92 * math.sin(radians)]
            nodes.append({"type": "line", "points": [centre, end]})
            sweep = float(interior(count))
            middle = math.radians(direction + sweep / 2)
            nodes.append({
                "type": "label",
                "point": [centre[0] + 53 * math.cos(middle),
                          centre[1] + 53 * math.sin(middle)],
                "text": name,
            })
            nodes.append({
                "type": "arc", "center": centre, "radius": 20,
                "start": direction, "sweep": sweep,
            })
            direction += sweep
        caption = "Only the polygon corners are shown"
        height = 275
    scene = {
        "kind": "scene", "version": 1, "width": 360,
        "height": height, "caption": caption, "nodes": nodes,
    }
    return figures.orient_scene(scene, p["orientation"])


def diagram_for(p, level):
    if p.get("form") in ("quadrilateral_exterior", "vertex_fit"):
        return advanced_diagram(p)
    nodes = []
    caption = "Not drawn accurately"

    def line(a, b, dashed=False):
        nodes.append({"type": "line", "points": [a, b], "dashed": dashed})

    def label(point, text):
        nodes.append({"type": "label", "point": point, "text": text})

    def angle(center, start, sweep, point, text):
        nodes.append({
            "type": "arc", "center": center, "radius": 22,
            "start": start, "sweep": sweep,
        })
        nodes.append({"type": "label", "point": point, "tex": text})

    if level <= 2:
        n = p["sides"]
        points = [
            [180 + 100 * math.cos(2 * math.pi * i / n),
             125 + 100 * math.sin(2 * math.pi * i / n)]
            for i in range(n)
        ]
        nodes.append({"type": "polygon", "points": points})
        label([180, 125], "{} sides".format(n))
        if level == 2:
            # At the rightmost vertex, the two incident rays are symmetric.
            half_exterior = 180 / n
            start = 90 + half_exterior
            if p["angle_kind"] == "interior":
                angle(points[0], start, 180 - 2 * half_exterior,
                      [240, 125], r"x^{\circ}")
            else:
                incoming = math.radians(90 - half_exterior)
                end = [points[0][0] + 46 * math.cos(incoming),
                       points[0][1] + 46 * math.sin(incoming)]
                line(points[0], end, dashed=True)
                angle(points[0], 90 - half_exterior, 2 * half_exterior,
                      [280, 187], r"x^{\circ}")
    elif level == 3:
        # Only two adjacent sides are shown: counting cannot reveal n.
        vertex = [140, 65]
        line([35, 65], vertex)
        line(vertex, [210, 195])
        line(vertex, [300, 65], dashed=True)
        if p["angle_kind"] == "interior":
            angle(vertex, 61.7, 118.3, [110, 104],
                  str(p["angle"]) + r"^{\circ}")
        else:
            angle(vertex, 0, 61.7, [197, 91],
                  str(p["angle"]) + r"^{\circ}")
        caption = "Part of the polygon shown; not drawn accurately"
    else:
        # Local boundary at A. Both polygons continue beyond this extract.
        a, b = [180, 135], [180, 225]
        line(a, b)
        line(a, [40, 55])
        line(a, [320, 55])
        label([180, 151], "A")
        label([180, 240], "B")
        label([85, 158], "K")
        label([275, 158], "P")
        angle(a, 209.745, 120.51, [180, 83],
              str(p["gap"]) + r"^{\circ}")
        caption = "Parts of K and P shown; not drawn accurately"

    scene = {
        "kind": "scene", "version": 1, "width": 360, "height": 260,
        "caption": caption, "nodes": nodes,
    }
    return figures.orient_scene(scene, p["orientation"])


def presentation(p, level):
    if p.get("form") == "quadrilateral_exterior":
        a, b, c = p["angles"]
        return Content(
            "Three interior angles of a quadrilateral are {}, {} and {} "
            "degrees. Find the exterior angle x at the fourth vertex."
            .format(a, b, c)
        )
    if p.get("form") == "vertex_fit":
        return Content(
            "Three regular polygons K, L and P meet at a vertex without "
            "gaps or overlaps. K has {} sides and L has {} sides. "
            "How many sides does P have?"
            .format(p["first_sides"], p["second_sides"])
        )
    if level == 1:
        prompt = (
            "Calculate the sum of the interior angles of a polygon with "
            "{} sides.".format(p["sides"])
        )
    elif level == 2:
        prompt = (
            "A regular polygon has {} sides. Calculate the size of one "
            "{} angle.".format(p["sides"], p["angle_kind"])
        )
    elif level == 3:
        prompt = (
            "Each {} angle of a regular polygon is {} degrees. "
            "How many sides does the polygon have?"
        ).format(p["angle_kind"], p["angle"])
    else:
        prompt = (
            "A regular {} K and a regular polygon P share a side AB and lie "
            "on opposite sides of AB. At A, the two interior angles and "
            "the remaining angle outside both polygons make a full turn. "
            "The remaining angle is {} degrees. "
            "How many sides does polygon P have?"
        ).format(NAMES[p["known_sides"]], p["gap"])
    return Content(prompt)


def answer_display(value, level, form=None):
    if level <= 2 or form == "quadrilateral_exterior":
        return Content("{} degrees".format(value), str(value) + r"^{\circ}")
    return Content("{} sides".format(value))


def recover(p, level):
    if p.get("form") == "quadrilateral_exterior":
        missing_interior = 360 - sum(p["angles"])
        return Fraction(180 - missing_interior)
    if p.get("form") == "vertex_fit":
        missing_interior = (
            360 - interior(p["first_sides"]) - interior(p["second_sides"])
        )
        return Fraction(360, 180 - missing_interior)
    if level == 1:
        return Fraction((p["sides"] - 2) * 180)
    if level == 2:
        return (interior(p["sides"]) if p["angle_kind"] == "interior"
                else Fraction(360, p["sides"]))
    if level == 3:
        exterior = 180 - p["angle"] if p["angle_kind"] == "interior" else p["angle"]
        return Fraction(360, exterior)
    unknown_interior = 360 - interior(p["known_sides"]) - p["gap"]
    return Fraction(360, 180 - unknown_interior)


class PolygonAngles:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        if difficulty == 1:
            p = {"sides": rng.randint(5, 15)}
        elif difficulty == 2:
            p = {
                "sides": rng.choice(SIDE_COUNTS[2:]),
                "angle_kind": rng.choice(("interior", "exterior")),
            }
        elif difficulty == 3 and rng.random() < 0.5:
            while True:
                angles = [rng.randrange(65, 136, 5) for _ in range(3)]
                exterior = sum(angles) - 180
                if 45 <= exterior <= 135:
                    break
            p = {"form": "quadrilateral_exterior", "angles": angles}
        elif difficulty == 3:
            n = rng.choice(SIDE_COUNTS)
            kind = rng.choice(("interior", "exterior"))
            angle = interior(n) if kind == "interior" else Fraction(360, n)
            p = {"angle_kind": kind, "angle": int(angle)}
        elif rng.random() < 0.5:
            triple = list(rng.choice(VERTEX_TRIPLES))
            rng.shuffle(triple)
            p = {
                "form": "vertex_fit",
                "first_sides": triple[0],
                "second_sides": triple[1],
            }
        else:
            known = rng.choice(SIDE_COUNTS)
            unknown = rng.choice(tuple(n for n in SIDE_COUNTS if n != known))
            gap = 360 - interior(known) - interior(unknown)
            p = {"known_sides": known, "gap": int(gap)}
        p["orientation"] = figures.choose_orientation(
            rng, lambda orientation: diagram_for(
                dict(p, orientation=orientation), difficulty))
        value = recover(p, difficulty)
        require(value.denominator == 1, "Expected an integer result")
        value = value.numerator
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty,
            seed=seed, settings=context.settings,
            prompt=presentation(p, difficulty),
            answer={"kind": "integer", "value": value},
            answer_display=answer_display(value, difficulty, p.get("form")),
            worked_solution=(), marks=(2, 2, 3, 4)[difficulty - 1],
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=(3, 3, 4, 5)[difficulty - 1]),
            parameters=p, question_visuals=(diagram_for(p, difficulty),),
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid level")
        require(q.settings == {}, "Unsupported settings")
        p = q.parameters
        keys = {
            1: {"sides"},
            2: {"sides", "angle_kind"},
            3: {"angle_kind", "angle"},
            4: {"known_sides", "gap"},
        }
        form = p.get("form")
        if level == 3 and form == "quadrilateral_exterior":
            expected = {"form", "angles", "orientation"}
        elif level == 4 and form == "vertex_fit":
            expected = {"form", "first_sides", "second_sides", "orientation"}
        else:
            expected = keys[level] | {"orientation"}
        require(set(p) == expected, "Unexpected parameters")
        require(figures.valid_orientation(p.get("orientation")),
                "Unknown orientation")
        if form == "quadrilateral_exterior":
            angles = p["angles"]
            require(isinstance(angles, list) and len(angles) == 3
                    and all(type(a) is int and 65 <= a <= 135 and a % 5 == 0
                            for a in angles), "Invalid quadrilateral angles")
            require(45 <= sum(angles) - 180 <= 135,
                    "Exterior angle outside bounds")
        elif form == "vertex_fit":
            a, b = p["first_sides"], p["second_sides"]
            require(type(a) is int and type(b) is int,
                    "Side counts must be integers")
            require(a >= 3 and b >= 3, "Invalid known side counts")
            require(a != b, "Expected distinct known polygons")
            missing = 360 - interior(a) - interior(b)
            require(0 < missing < 180, "Invalid polygon corner")
            result = recover(p, level)
            require(result.denominator == 1
                    and tuple(sorted((a, b, int(result)))) in VERTEX_TRIPLES,
                    "The three polygons cannot meet as specified")
        else:
            for key in set(p) - {"angle_kind", "orientation"}:
                require(type(p[key]) is int, "Expected integer parameter")
            if level == 1:
                require(5 <= p["sides"] <= 15, "Side count outside bounds")
            elif level in (2, 3):
                require(p["angle_kind"] in ("interior", "exterior"),
                        "Unknown angle kind")
                if level == 2:
                    require(p["sides"] in SIDE_COUNTS[2:],
                            "Unsupported polygon")
                else:
                    require(0 < p["angle"] < 180, "Invalid angle")
            else:
                require(p["known_sides"] in SIDE_COUNTS,
                        "Unsupported known polygon")
                require(0 < p["gap"] < 360,
                        "Invalid remaining angle")

        value = q.answer.get("value")
        require(type(value) is int, "Expected integer answer")
        require(q.answer == {"kind": "integer", "value": value}, "Invalid answer")
        require(recover(p, level) == value, "Incorrect polygon answer")
        if level >= 3 and form not in ("quadrilateral_exterior", "vertex_fit"):
            require(value in SIDE_COUNTS, "Unsupported recovered side count")
        if level == 4 and form != "vertex_fit":
            require(value != p["known_sides"], "Expected different polygons")
        require(q.prompt == presentation(p, level), "Prompt mismatch")
        require(q.answer_display == answer_display(value, level, form),
                "Display mismatch")
        require(q.visual_assets("questions") == (diagram_for(p, level),),
                "Polygon diagram mismatch")
        require(not q.visual_assets("answers"), "Unexpected answer visuals")
        return True

    def validate_independently(self, q):
        """Enumerate side counts using the interior-angle sum identity."""
        p, level = q.parameters, q.difficulty
        value = q.answer["value"]
        if p.get("form") == "quadrilateral_exterior":
            # The unknown interior angle and its exterior make 180 degrees.
            require(sum(p["angles"]) + (180 - value) == 360,
                    "Independent quadrilateral angle sum disagrees")
            return True
        if p.get("form") == "vertex_fit":
            a, b = p["first_sides"], p["second_sides"]
            require(type(a) is int and type(b) is int and a >= 3 and b >= 3,
                    "Invalid known side counts")
            candidates = [
                n for n in range(3, 101)
                if interior(a) + interior(b) + interior(n) == 360
            ]
            require(candidates == [value],
                    "Independent vertex side count disagrees")
            return True
        if level == 1:
            # Triangulate from an interior point, then remove the full turn.
            require(value == p["sides"] * 180 - 360, "Angle sum disagrees")
        elif level == 2:
            n = p["sides"]
            internal = value if p["angle_kind"] == "interior" else 180 - value
            require(n * internal == (n - 2) * 180, "Regular angle disagrees")
        else:
            candidates = []
            for n in range(3, 101):
                if level == 3:
                    internal = (p["angle"] if p["angle_kind"] == "interior"
                                else 180 - p["angle"])
                    valid = n * internal == (n - 2) * 180
                else:
                    k = p["known_sides"]
                    # Clear both denominators from the full-turn equation.
                    valid = (
                        180 * (k - 2) * n + 180 * (n - 2) * k
                        + p["gap"] * k * n == 360 * k * n
                    )
                if valid:
                    candidates.append(n)
            require(candidates == [value], "Independent side count disagrees")
        return True