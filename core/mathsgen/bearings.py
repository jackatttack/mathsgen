"""Bearings: back bearings, angle facts with north lines, and two-leg journeys.

Bearings are measured clockwise from north, so these diagrams are never
rotated or mirrored: north stays up and clockwise stays clockwise. Variety
comes from the directions, lengths and point names instead.

Figure coordinates are (east, north). The PDF scene renderer draws y upwards
and figures.place() keeps that direction at the fixed orientation used here.

Levels:
1  Back bearings, no diagram.
2  Angle facts with north lines: the angle between two legs, or an isosceles
   triangle that gives a new bearing.
3  Two legs along compass directions: distance (3 s.f.) and a bearing (1 d.p.).
4  Two legs on any bearings: cosine-rule distance and a bearing (1 d.p.).
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
    id="geometry.bearings.bearings", version=1,
    topic="geometry", subtopic="bearings",
    title="Bearings: back bearings, north-line angles and journeys",
    difficulty_descriptions={
        1: "Find a back bearing from a given three-figure bearing.",
        2: "Use angle facts with north lines to find an angle or a bearing.",
        3: "Two legs along compass directions: find a distance and a bearing.",
        4: "Two legs on any bearings: use the cosine rule, then find a bearing.",
    },
    tags=("geometry", "bearings", "trigonometry"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("back",),
    2: ("angle_between", "isosceles"),
    3: ("from_start", "to_start"),
    4: ("from_start", "to_start"),
}
PAIRS = ("AB", "PQ", "ST", "XY")
TRIPLES = ("ABC", "PQR", "LMN", "XYZ")
PLACES = ("town", "port", "village", "lighthouse")
COMPASS = {"north": 0, "east": 90, "south": 180, "west": 270}
MARKS = {1: 2, 2: 3, 3: 5, 4: 6}
WORKING_LINES = {1: 3, 2: 5, 3: 7, 4: 8}

# Diagram settings. The orientation is fixed: see the module docstring.
FIXED_ORIENTATION = [0, False]
NORTH_LENGTH = 0.4   # north arrows, as a share of the figure's larger span
ARC_RADIUS = 15
ARC_VERTEX_GAP = ARC_RADIUS + 13   # vertex letters clear of a bearing arc
ARC_LABEL_LIMIT = 60               # furthest a bearing label sits from its vertex
VERTEX_GAP = 16
# Every width a scene is drawn at, including the 238 pt working-row layout.
SCENE_WIDTHS = (360, 250, 238)

KEYS = {
    "back": {"form", "names", "place", "bearing"},
    "angle_between": {"form", "names", "b1", "b2", "l1", "l2"},
    "isosceles": {"form", "names", "b1", "b2"},
}
COMPASS_JOURNEY_KEYS = {"form", "names", "first", "second", "d1", "d2"}
BEARING_JOURNEY_KEYS = {"form", "names", "b1", "b2", "d1", "d2"}
WORD_KEYS = {"form", "names", "place", "first", "second"}


# ------------------------------------------------------------ bearing arithmetic

def back_bearing(bearing):
    return (bearing + 180) % 360


def clockwise_turn(start, finish):
    """How far clockwise you turn from facing bearing start to facing finish."""
    return (finish - start) % 360


def angle_between_bearings(first, second):
    """The non-reflex angle between two directions given as bearings."""
    difference = (first - second) % 360
    return min(difference, 360 - difference)


def heading(bearing):
    """Unit vector (east, north) for a bearing."""
    turn = math.radians(bearing)
    return (math.sin(turn), math.cos(turn))


def bearing_text(value, tenths=False):
    """Three-figure bearing: 54 -> 054°, and 38.7 -> 038.7° when tenths."""
    if not tenths:
        return "{:03d}°".format(int(value))
    whole, tenth = one_decimal_text(value).split(".")
    return "{:0>3}.{}°".format(whole, tenth)


def rounded_sig_figs(value, significant=3):
    """Reject a nearby rounding boundary, then store the exact rounded value."""
    require(math.isfinite(value) and value > 0, "Invalid result")
    decimals = significant - 1 - math.floor(math.log10(value))
    scaled = value * 10 ** decimals
    fraction = scaled - math.floor(scaled)
    require(abs(fraction - 0.5) > 1e-6, "Near rounding boundary")
    return Fraction(math.floor(scaled + 0.5)) / Fraction(10) ** decimals


def sig_figs_text(value, significant=3):
    """Show a rounded value with its significant trailing zeros kept."""
    value = Fraction(value)
    decimals = max(0, significant - 1 - math.floor(math.log10(float(value))))
    scaled = value * 10 ** decimals
    require(scaled.denominator == 1, "Value is not rounded to this precision")
    if decimals == 0:
        return str(int(scaled))
    digits = str(int(scaled)).rjust(decimals + 1, "0")
    return digits[:-decimals] + "." + digits[-decimals:]


# ------------------------------------------------------------ mathematics

def isosceles_result(p):
    """Bearing of C from B when AB = AC, from the base angles of the triangle."""
    apex = angle_between_bearings(p["b1"], p["b2"])
    base = (180 - apex) // 2
    towards_a = back_bearing(p["b1"])
    if clockwise_turn(p["b1"], p["b2"]) < 180:
        return (towards_a - base) % 360
    return (towards_a + base) % 360


def journey_legs(p, level):
    """(first bearing, first length, second bearing, second length)."""
    if level == 3:
        return COMPASS[p["first"]], p["d1"], COMPASS[p["second"]], p["d2"]
    return p["b1"], p["d1"], p["b2"], p["d2"]


def journey_results(p, level):
    """Distance AC, the requested bearing, and the angles at A and B.

    The angle at B comes from the two bearings, AC from the cosine rule and
    the angle at A from the cosine rule again. A turn to the right at B puts
    C clockwise of AB as seen from A.
    """
    b1, d1, b2, d2 = journey_legs(p, level)
    angle_b = angle_between_bearings(back_bearing(b1), b2)
    distance = math.sqrt(
        d1 * d1 + d2 * d2 - 2 * d1 * d2 * math.cos(math.radians(angle_b)))
    cosine_a = (d1 * d1 + distance * distance - d2 * d2) / (2 * d1 * distance)
    angle_a = math.degrees(math.acos(max(-1.0, min(1.0, cosine_a))))
    if clockwise_turn(b1, b2) < 180:
        bearing = (b1 + angle_a) % 360
    else:
        bearing = (b1 - angle_a) % 360
    if p["form"] == "to_start":
        bearing = (bearing + 180) % 360
    return distance, bearing, angle_a, angle_b


def results(p, level):
    """Unrounded answers, in the order the question asks for them."""
    form = p["form"]
    if form == "back":
        return (back_bearing(p["bearing"]),)
    if form == "angle_between":
        return (angle_between_bearings(back_bearing(p["b1"]), p["b2"]),)
    if form == "isosceles":
        return (isosceles_result(p),)
    distance, bearing, _, _ = journey_results(p, level)
    return distance, bearing


def check_parameters(p, level):
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    if level < 3:
        expected = KEYS[form]
    elif level == 3:
        expected = COMPASS_JOURNEY_KEYS
    else:
        expected = BEARING_JOURNEY_KEYS
    require(set(p) == expected, "Unexpected parameters")
    require(all(type(p[name]) is int for name in expected - WORD_KEYS),
            "Integer parameters required")

    if level == 1:
        require(p["names"] in PAIRS, "Invalid point names")
        require(p["place"] in PLACES, "Invalid place")
        require(1 <= p["bearing"] <= 359 and p["bearing"] != 180,
                "Bearing outside bounds")
        return

    require(p["names"] in TRIPLES, "Invalid point names")
    if level == 2:
        for name in ("b1", "b2"):
            require(1 <= p[name] <= 359, "Bearing outside bounds")
        if form == "angle_between":
            require(3 <= p["l1"] <= 6 and 3 <= p["l2"] <= 6,
                    "Drawing lengths outside bounds")
            require(25 <= results(p, level)[0] <= 155,
                    "Angle too sharp or too open")
        else:
            apex = angle_between_bearings(p["b1"], p["b2"])
            require(30 <= apex <= 120 and apex % 2 == 0, "Apex angle outside bounds")
            require(1 <= isosceles_result(p) <= 359,
                    "Answer must be a bearing from 001 to 359")
        return

    if level == 3:
        require(p["first"] in COMPASS and p["second"] in COMPASS,
                "Unknown compass direction")
        require(angle_between_bearings(COMPASS[p["first"]], COMPASS[p["second"]]) == 90,
                "Legs must be perpendicular")
        for name in ("d1", "d2"):
            require(50 <= p[name] <= 400 and p[name] % 10 == 0, "Leg outside bounds")
        smallest, largest = 100, 999.5
    else:
        for name in ("b1", "b2"):
            require(5 <= p[name] <= 355 and p[name] % 5 == 0, "Bearing outside bounds")
        for name in ("d1", "d2"):
            require(4 <= p[name] <= 20, "Leg outside bounds")
        smallest, largest = 10, 99.5
    require(p["d1"] != p["d2"], "Expected unequal legs")
    distance, bearing, angle_a, angle_b = journey_results(p, level)
    if level == 4:
        require(35 <= angle_b <= 145 and abs(angle_b - 90) >= 10,
                "Turn gives a degenerate or right-angled triangle")
        require(min(angle_a, 180 - angle_a - angle_b) >= 15, "Triangle too narrow")
    require(smallest <= distance < largest, "Distance outside bounds")
    require(0.5 < bearing < 359.5, "Bearing too close to north")
    rounded_sig_figs(distance)
    rounded_value(bearing)


# ------------------------------------------------------------ diagrams

def letters(p):
    return dict(zip("ABC", p["names"]))


def figure_points(p, level):
    """True (east, north) coordinates for roles A, B and C."""
    if p["form"] == "isosceles":
        return {"A": (0.0, 0.0), "B": heading(p["b1"]), "C": heading(p["b2"])}
    if p["form"] == "angle_between":
        b1, first, b2, second = p["b1"], p["l1"], p["b2"], p["l2"]
    else:
        b1, first, b2, second = journey_legs(p, level)
    step, turn = heading(b1), heading(b2)
    B = (first * step[0], first * step[1])
    C = (B[0] + second * turn[0], B[1] + second * turn[1])
    return {"A": (0.0, 0.0), "B": B, "C": C}


def label(point, text):
    return {"type": "label", "point": figures.rounded(point), "text": text}


def line(first, second, **extra):
    node = {"type": "line", "points": [first, second]}
    node.update(extra)
    return node


def vertex_label_point(point, centre, gap):
    """Outward from the triangle, but never straight up onto a north arrow."""
    outward = figures.unit(figures.minus(point, centre))
    if outward[1] > 0.5:
        side = 1.0 if outward[0] >= 0 else -1.0
        outward = figures.unit((side, 0.35))
    return (point[0] + outward[0] * gap, point[1] + outward[1] * gap)


def bearing_arc(vertex, bearing):
    """Arc clockwise from north through the bearing, labelled mid-arc."""
    text = "{}°".format(bearing)
    middle = heading(bearing / 2)
    # Narrow arcs push the label out so it clears both the north line and the leg.
    opening = math.radians(min(bearing, 180) / 2)
    distance = ARC_RADIUS + (8 + 2.6 * len(text)) / max(math.sin(opening), 0.35)
    distance = min(distance, ARC_LABEL_LIMIT)
    return [
        {"type": "arc", "center": vertex, "radius": ARC_RADIUS,
         "start": 90 - bearing, "sweep": bearing},
        label((vertex[0] + middle[0] * distance, vertex[1] + middle[1] * distance), text),
    ]


def scene_for(p, level):
    points = figure_points(p, level)
    xs = [x for x, _ in points.values()]
    ys = [y for _, y in points.values()]
    span = max(max(xs) - min(xs), max(ys) - min(ys))
    raw = dict(points)
    for role in ("A", "B"):
        x, y = points[role]
        raw["N" + role] = (x, y + NORTH_LENGTH * span)
    placed, height = figures.place(raw, FIXED_ORIENTATION)
    A, B, C = placed["A"], placed["B"], placed["C"]
    form = p["form"]

    nodes = []
    if form == "isosceles":
        nodes.append({"type": "polygon", "points": [A, B, C]})
        nodes.append({"type": "ticks", "points": [A, B]})
        nodes.append({"type": "ticks", "points": [A, C]})
    else:
        nodes += [line(A, B), line(B, C)]
        if level >= 3:
            nodes.append(line(A, C, dashed=True))
    for role in ("A", "B"):
        tip = placed["N" + role]
        nodes.append(line(placed[role], tip, arrow=True))
        nodes.append(label((tip[0], tip[1] + 10), "N"))

    centre = ((A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3)
    names = letters(p)
    arcs_at = ("A", "B") if form == "angle_between" or level == 4 else ()
    for role in "ABC":
        gap = ARC_VERTEX_GAP if role in arcs_at else VERTEX_GAP
        nodes.append(label(vertex_label_point(placed[role], centre, gap), names[role]))

    if form == "angle_between":
        nodes += bearing_arc(A, p["b1"]) + bearing_arc(B, p["b2"])
        nodes.append({"type": "label", "point": figures.angle_label(B, A, C, 1),
                      "text": "x"})
    elif level >= 3:
        unit = "m" if level == 3 else "km"
        for first, second, inside, length in ((A, B, C, p["d1"]), (B, C, A, p["d2"])):
            text = "{} {}".format(length, unit)
            nodes.append({"type": "label", "text": text,
                          "point": figures.side_label(first, second, inside, len(text))})
        if level == 3:
            nodes.append({"type": "right_angle", "vertex": B, "first": A, "second": C})
        else:
            nodes += bearing_arc(A, p["b1"]) + bearing_arc(B, p["b2"])

    return {
        "kind": "scene", "version": 1, "width": figures.CANVAS_WIDTH,
        "height": height, "caption": "Not drawn accurately", "nodes": nodes,
    }


def renders_cleanly(scene):
    """Like figures.renderable, but also at the 238 pt working-row width."""
    from .visuals import drawing_for
    try:
        for width in SCENE_WIDTHS:
            drawing_for(scene, width)
    except ValueError:
        return False
    return True


# ------------------------------------------------------------ presentation

def presentation(p, level):
    form = p["form"]
    if level == 1:
        first, second = p["names"][0], p["names"][1]
        text = (
            "The bearing of {place} {second} from {place} {first} is {bearing}. "
            "Work out the bearing of {place} {first} from {place} {second}."
        ).format(place=p["place"], first=first, second=second,
                 bearing=bearing_text(p["bearing"]))
        return Content(text), ()

    fields = dict(letters(p))
    for name in ("b1", "b2"):
        if name in p:
            fields[name] = bearing_text(p[name])
    for name in ("d1", "d2", "first", "second"):
        if name in p:
            fields[name] = p[name]

    if form == "angle_between":
        text = ("The bearing of {B} from {A} is {b1}. The bearing of {C} from {B} "
                "is {b2}. Work out the size of angle {A}{B}{C}, marked x.")
    elif form == "isosceles":
        text = ("{A}, {B} and {C} are points such that {A}{B} = {A}{C}. "
                "The bearing of {B} from {A} is {b1}. The bearing of {C} from {A} "
                "is {b2}. Work out the bearing of {C} from {B}.")
    else:
        if level == 3:
            text = ("From point {A}, a walker walks {d1} m due {first} to point {B}. "
                    "From {B}, they walk {d2} m due {second} to point {C}. ")
        else:
            text = ("A ship sails {d1} km from point {A} to point {B} on a bearing "
                    "of {b1}. It then sails {d2} km from {B} to point {C} on a "
                    "bearing of {b2}. ")
        target = "{C} from {A}" if form == "from_start" else "{A} from {C}"
        text += ("(a) Work out the distance {A}{C}. Give your answer to 3 "
                 "significant figures. (b) Work out the bearing of " + target
                 + ". Give your answer to 1 decimal place.")
    return Content(text.format(**fields)), (scene_for(p, level),)


def answer_for(p, level):
    form = p["form"]
    values = results(p, level)
    if form in ("back", "isosceles"):
        return ({"kind": "bearing", "value": str(values[0])},
                Content(bearing_text(values[0])))
    if form == "angle_between":
        return ({"kind": "angle", "value": str(values[0]), "unit": "degrees"},
                Content("{}°".format(values[0])))
    unit = "m" if level == 3 else "km"
    distance = rounded_sig_figs(values[0])
    bearing = rounded_value(values[1])
    answer = {
        "kind": "distance_and_bearing", "distance": rational_text(distance),
        "unit": unit, "bearing": rational_text(bearing),
    }
    display = "(a) {} {}; (b) {}".format(
        sig_figs_text(distance), unit, bearing_text(bearing, tenths=True))
    return answer, Content(display)


def draw_parameters(rng, level, form):
    """Candidate parameters for a form chosen once per question.

    Retrying only the numbers keeps forms evenly mixed, even when one form
    rejects more candidates than another.
    """
    p = {"form": form}
    if level == 1:
        p.update(names=rng.choice(PAIRS), place=rng.choice(PLACES),
                 bearing=rng.randint(1, 359))
        return p
    p["names"] = rng.choice(TRIPLES)
    if form == "angle_between":
        p.update(b1=rng.randint(1, 359), b2=rng.randint(1, 359),
                 l1=rng.randint(3, 6), l2=rng.randint(3, 6))
    elif form == "isosceles":
        b1 = rng.randint(1, 359)
        apex = rng.randrange(30, 121, 2)
        p.update(b1=b1, b2=(b1 + rng.choice((-1, 1)) * apex) % 360)
    elif level == 3:
        first = rng.choice(sorted(COMPASS))
        options = [name for name in sorted(COMPASS)
                   if angle_between_bearings(COMPASS[first], COMPASS[name]) == 90]
        p.update(first=first, second=rng.choice(options),
                 d1=rng.randrange(50, 401, 10), d2=rng.randrange(50, 401, 10))
    else:
        p.update(b1=rng.randrange(5, 356, 5), b2=rng.randrange(5, 356, 5),
                 d1=rng.randint(4, 20), d2=rng.randint(4, 20))
    return p


# ------------------------------------------------------------ generator

class Bearings:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        form = rng.choice(FORMS[difficulty])
        for attempt in range(1000):
            p = draw_parameters(rng, difficulty, form)
            try:
                check_parameters(p, difficulty)
                if difficulty > 1:
                    require(renders_cleanly(scene_for(p, difficulty)),
                            "Diagram does not render cleanly")
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a bearings question")
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
        """Walk the legs as east/north components and read answers with atan2.

        Never uses the cosine rule, back-bearing arithmetic or base angles.
        """
        p = q.parameters
        form = p.get("form")
        require(form in FORMS.get(q.difficulty, ()), "Unexpected form")

        def move(start, bearing, length):
            turn = math.radians(bearing)
            return (start[0] + length * math.sin(turn),
                    start[1] + length * math.cos(turn))

        def bearing_of(target, origin):
            return math.degrees(math.atan2(target[0] - origin[0],
                                           target[1] - origin[1])) % 360

        def angle_at(vertex, first, second):
            u = (first[0] - vertex[0], first[1] - vertex[1])
            v = (second[0] - vertex[0], second[1] - vertex[1])
            return math.degrees(math.atan2(abs(u[0] * v[1] - u[1] * v[0]),
                                           u[0] * v[0] + u[1] * v[1]))

        def agrees(stated, value, tolerance):
            difference = (stated - value) % 360
            require(min(difference, 360 - difference) <= tolerance,
                    "Independent reconstruction disagrees")

        origin = (0.0, 0.0)
        if form == "back":
            B = move(origin, p["bearing"], 1)
            agrees(int(q.answer["value"]), bearing_of(origin, B), 1e-6)
            return True
        if form == "angle_between":
            B = move(origin, p["b1"], 1)
            C = move(B, p["b2"], 1)
            require(abs(angle_at(B, origin, C) - int(q.answer["value"])) < 1e-6,
                    "Independent angle disagrees")
            return True
        if form == "isosceles":
            B, C = move(origin, p["b1"], 5), move(origin, p["b2"], 5)
            agrees(int(q.answer["value"]), bearing_of(C, B), 1e-6)
            return True

        if q.difficulty == 3:
            first, second = COMPASS[p["first"]], COMPASS[p["second"]]
        else:
            first, second = p["b1"], p["b2"]
        C = move(move(origin, first, p["d1"]), second, p["d2"])
        distance = math.hypot(C[0], C[1])
        bearing = bearing_of(C, origin) if form == "from_start" else bearing_of(origin, C)
        stated_distance = Fraction(q.answer["distance"])
        stated_bearing = Fraction(q.answer["bearing"])
        require((stated_bearing * 10).denominator == 1, "Expected exact tenths")
        step = 10 ** (math.floor(math.log10(float(stated_distance))) - 2)
        require(abs(distance - float(stated_distance)) <= step / 2 + 1e-9,
                "Independent distance disagrees")
        agrees(float(stated_bearing), bearing, 0.05 + 1e-9)
        return True