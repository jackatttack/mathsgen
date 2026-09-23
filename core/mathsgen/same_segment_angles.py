"""Angles in the same segment, drawn from true positions, with linked forms.

Points sit on the circle at scene-angle positions (y increases downward):
A at 270 - t, B at 270 + t, D at 90 + d and C at 90 + c, so the order round
the circle is A, B, D, C and chords AD and BC cross at E. Here t is the angle
ACB = ADB, and every other angle follows from the arcs:
    DAB = (180 + d - t) / 2      ABD = (180 - t - d) / 2
    CAD = CBD = (c - d) / 2      AEC = 180 - t - CAD
A form labels some of these angles with [k, b], meaning kx + b degrees.
Positions the labels leave free are seeded presentation choices stored in
the parameters; validation rebuilds the exact diagram from them.
"""
import math
from fractions import Fraction

from . import circle_figures, figures
from .core import Content, GeneratorInfo, LayoutHint, Question, make_context, require


INFO = GeneratorInfo(
    id="geometry.circle_theorems.same_segment", version=3,
    topic="geometry", subtopic="circle_theorems",
    title="Circle theorem: angles in the same segment",
    difficulty_descriptions={
        1: "Find an angle subtended by the same chord.",
        2: "Solve a single expression, or use the other chord of the quadrilateral.",
        3: "Transfer an angle, then use triangle ABD or the crossing chords.",
        4: "Form and solve an equation from algebraic angles, directly or with a triangle.",
    },
    tags=("geometry", "circle_theorems", "angles", "equations"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("direct",),
    2: ("expression", "other_chord"),
    3: ("triangle", "crossing"),
    4: ("algebra", "algebra_triangle"),
}
# Labelled angles for each form. Roles name the angle's vertex and chord.
FORM_ROLES = {
    "direct": ("C", "D"),
    "expression": ("C", "D"),
    "other_chord": ("A_cross", "B_cross"),
    "triangle": ("C", "A_tri", "B_tri"),
    "crossing": ("D", "A_cross", "E"),
    "algebra": ("C", "D"),
    "algebra_triangle": ("C", "A_tri", "B_tri"),
}
# Positions the labels do not fix, chosen with the seed.
FREE = {
    "direct": ("c", "d"),
    "expression": ("c", "d"),
    "other_chord": ("t", "d"),
    "triangle": ("c",),
    "crossing": ("d",),
    "algebra": ("c", "d"),
    "algebra_triangle": ("c",),
}
ALGEBRA_FORMS = {"expression", "algebra", "algebra_triangle"}
NAME_SETS = ("ABCDE", "PQRST", "FGHJK", "KLMNP", "UVWXY")
MARKS = {
    "direct": 1, "expression": 2, "other_chord": 2, "triangle": 3,
    "crossing": 3, "algebra": 4, "algebra_triangle": 4,
}
GAP = 25          # least arc, in degrees, between neighbouring points
LEAST_CHORD = 30  # least arc DC, so the two lower points stay apart

# role -> (vertex, first arm, second arm), in figure roles A-E.
CORNERS = {
    "C": ("C", "A", "B"), "D": ("D", "A", "B"),
    "A_tri": ("A", "D", "B"), "B_tri": ("B", "A", "D"),
    "A_cross": ("A", "C", "D"), "B_cross": ("B", "C", "D"),
    "E": ("E", "A", "C"),
}


# ------------------------------------------------------------ mathematics

def expression(term):
    k, b = term
    text = str(b) if not k else ("x" if k == 1 else str(k) + "x")
    if k and b:
        text += (" + " if b > 0 else " - ") + str(abs(b))
    return text


def value_of(term, x):
    return term[0] * x + term[1]


def solve(p):
    """x by the textbook route for each form."""
    form = p["form"]
    if form == "direct":
        return Fraction(p["C"][1])
    if form == "expression":
        k, b = p["D"]
        return Fraction(p["C"][1] - b, k)
    if form == "other_chord":
        return Fraction(p["A_cross"][1])
    if form == "triangle":
        return Fraction(180 - p["C"][1] - p["A_tri"][1])
    if form == "crossing":
        return Fraction(180 - p["D"][1] - p["A_cross"][1])
    if form == "algebra":
        (k, b), (one, c) = p["C"], p["D"]
        require(k != one, "Angles do not determine x")
        return Fraction(c - b, k - one)
    (k, b), (one, c) = p["C"], p["B_tri"]
    return Fraction(180 - p["A_tri"][1] - b - c, k + one)


def geometry(p, x):
    """The arc positions (t, d, c) implied by the labels and free choices."""
    values = {role: value_of(p[role], x) for role in FORM_ROLES[p["form"]]}
    t = values["C"] if "C" in values else values["D"] if "D" in values else p["t"]
    d = 2 * values["A_tri"] - 180 + t if "A_tri" in values else p["d"]
    c = d + 2 * values["A_cross"] if "A_cross" in values else p["c"]
    return Fraction(t), Fraction(d), Fraction(c)


def place_free(rng, p, x):
    """Choose the seeded positions that the labels leave free."""
    free = FREE[p["form"]]
    if "t" in free:
        p["t"] = rng.randrange(35, 71, 5)
    values = {role: value_of(p[role], x) for role in FORM_ROLES[p["form"]]}
    t = values["C"] if "C" in values else values["D"] if "D" in values else p["t"]
    lowest_d = math.ceil(t - 180 + GAP)
    highest_c = math.floor(180 - t - GAP)
    if "d" in free:
        span = 2 * values["A_cross"] if "A_cross" in values else LEAST_CHORD
        require(lowest_d <= highest_c - span, "No room for D")
        p["d"] = rng.randint(lowest_d, int(highest_c - span))
    if "c" in free:
        d = 2 * values["A_tri"] - 180 + t if "A_tri" in values else p["d"]
        require(math.ceil(d + LEAST_CHORD) <= highest_c, "No room for C")
        p["c"] = rng.randint(math.ceil(d + LEAST_CHORD), highest_c)


def check_parameters(p, level):
    """Check structure, ranges and positions; return the whole-number x."""
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(form in FORMS[level], "Unexpected form for this level")
    roles, free = FORM_ROLES[form], FREE[form]
    require(set(p) == {"form", "names", "orientation"} | set(roles) | set(free),
            "Unexpected parameters")
    require(p["names"] in NAME_SETS, "Invalid letters")
    require(figures.valid_orientation(p["orientation"]), "Invalid orientation")
    for role in roles:
        term = p[role]
        require(isinstance(term, list) and len(term) == 2
                and all(type(v) is int for v in term), "Invalid angle expression")
    require(all(type(p[key]) is int for key in free), "Positions must be whole degrees")
    x = solve(p)
    require(x.denominator == 1, "x must be a whole number")
    x = int(x)
    for role in roles:
        require(10 <= value_of(p[role], x) < 180, "Labelled angle outside range")

    C, D = p.get("C"), p.get("D")
    if form == "direct":
        require(C[0] == 0 and 35 <= C[1] <= 75 and D == [1, 0], "Wrong direct structure")
    elif form == "expression":
        require(C[0] == 0 and 2 <= D[0] <= 3 and 3 <= D[1] <= 12 and 10 <= x <= 25,
                "Wrong single-expression structure")
    elif form == "other_chord":
        require(p["A_cross"][0] == 0 and 20 <= p["A_cross"][1] <= 40
                and p["B_cross"] == [1, 0] and 35 <= p["t"] <= 70,
                "Wrong other-chord structure")
    elif form == "triangle":
        require(C[0] == 0 and 35 <= C[1] <= 65 and p["A_tri"][0] == 0
                and 20 <= p["A_tri"][1] <= 40 and p["B_tri"] == [1, 0],
                "Wrong triangle structure")
    elif form == "crossing":
        require(D[0] == 0 and 35 <= D[1] <= 65 and p["A_cross"][0] == 0
                and 25 <= p["A_cross"][1] <= 45 and p["E"] == [1, 0],
                "Wrong crossing-chords structure")
    elif form == "algebra":
        require(2 <= C[0] <= 3 and 3 <= C[1] <= 12 and D[0] == 1 and 10 <= x <= 25,
                "Wrong two-expression structure")
    else:
        require(2 <= C[0] <= 3 and 3 <= C[1] <= 12 and p["A_tri"][0] == 0
                and 20 <= p["A_tri"][1] <= 40 and p["B_tri"][0] == 1
                and p["B_tri"][1] >= 1 and 10 <= x <= 25,
                "Wrong algebraic triangle structure")

    t, d, c = geometry(p, x)
    require(30 <= t <= 80, "Subtended angle outside range")
    require(d >= t - 180 + GAP, "D too close to B")
    require(c - d >= LEAST_CHORD, "C and D too close")
    require(c <= 180 - t - GAP, "C too close to A")
    return x


# ------------------------------------------------------------ presentation

ANGLE_LETTERS = {
    "C": "ACB", "D": "ADB", "A_tri": "DAB", "B_tri": "ABD",
    "A_cross": "CAD", "B_cross": "CBD", "E": "AEC",
}


def angle_name(role, names):
    letters = dict(zip("ABCDE", names))
    return "angle " + "".join(letters[ch] for ch in ANGLE_LETTERS[role])


def label_texts(p):
    """Diagram text per role: numbers, x, or u/v for longer expressions."""
    spare = iter("uv")
    texts = {}
    for role in FORM_ROLES[p["form"]]:
        term = p[role]
        if term == [1, 0]:
            texts[role] = "x"
        elif term[0]:
            texts[role] = next(spare)
        else:
            texts[role] = str(term[1])
    return texts


def distance(first, second):
    return math.hypot(first[0] - second[0], first[1] - second[1])


def midpoint(first, second):
    return ((first[0] + second[0]) / 2, (first[1] + second[1]) / 2)


def distance_to_line(point, first, second):
    """Perpendicular distance from point to the line through first and second."""
    dx, dy = second[0] - first[0], second[1] - first[1]
    cross = dx * (point[1] - first[1]) - dy * (point[0] - first[0])
    return abs(cross) / math.hypot(dx, dy)


def crossing_point(a, d, b, c):
    """Intersection of lines AD and BC."""
    r = (d[0] - a[0], d[1] - a[1])
    s = (c[0] - b[0], c[1] - b[1])
    denominator = r[0] * s[1] - r[1] * s[0]
    require(abs(denominator) > 1e-9, "Chords do not cross")
    u = ((b[0] - a[0]) * s[1] - (b[1] - a[1]) * s[0]) / denominator
    return (a[0] + u * r[0], a[1] + u * r[1])


def diagram_for(p, x):
    t, d, c = (float(v) for v in geometry(p, x))
    on = circle_figures.on_circle
    points = {"A": on(270 - t), "B": on(270 + t), "C": on(90 + c), "D": on(90 + d)}
    roles = FORM_ROLES[p["form"]]
    names = dict(zip("ABCDE", p["names"]))
    edges = [("A", "C"), ("B", "C"), ("A", "D"), ("B", "D")]
    if "A_tri" in roles:
        edges.append(("A", "B"))
    nodes = [{"type": "circle", "center": figures.rounded(circle_figures.CENTRE),
              "radius": circle_figures.RADIUS}]
    nodes += [circle_figures.line(points[a], points[b]) for a, b in edges]
    for key in "ABCD":
        nodes.append(circle_figures.vertex_label(points[key], names[key]))
    corners = dict(CORNERS)
    if "E" in roles:
        e = points["E"] = crossing_point(points["A"], points["D"], points["B"], points["C"])
        # x is marked in whichever vertical angle (AEC or BED, which are equal)
        # has the larger triangle, and the letter goes in whichever remaining
        # angle (AEB or CED) opens towards more of the circle.
        if distance_to_line(e, points["A"], points["C"]) < distance_to_line(
                e, points["B"], points["D"]):
            corners["E"] = ("E", "B", "D")
        if distance(e, midpoint(points["A"], points["B"])) >= distance(
                e, midpoint(points["C"], points["D"])):
            letter_arms = ("A", "B")
        else:
            letter_arms = ("C", "D")
        nodes.append(circle_figures.label_in_angle(
            e, points[letter_arms[0]], points[letter_arms[1]], names["E"]))
    for role, text in label_texts(p).items():
        vertex, first, second = corners[role]
        nodes += circle_figures.angle_mark(points[vertex], points[first], points[second],
                                           text + r"^{\circ}", len(text))
    scene = {
        "kind": "scene", "version": 1, "width": 360, "height": 300,
        "caption": "Not drawn accurately", "nodes": nodes,
    }
    return figures.orient_scene(scene, p["orientation"])


def presentation(p, level):
    names, form = p["names"], p["form"]
    lead = "{}, {}, {} and {} lie on the circle.".format(*names[:4])
    if form == "crossing":
        lead += " Chords {}{} and {}{} meet at {}.".format(
            names[0], names[3], names[1], names[2], names[4])
    texts = label_texts(p)
    definitions = ["{} = {}".format(texts[role], expression(p[role]))
                   for role in FORM_ROLES[form] if texts[role] in ("u", "v")]
    if definitions:
        lead += " In the diagram, " + " and ".join(definitions) + ", in degrees."
    lead += " Find x."
    fallback = " Marked: " + "; ".join(
        "{} is {} degrees".format(angle_name(role, names), expression(p[role]))
        for role in FORM_ROLES[form]) + "."
    return Content(lead + fallback, display_text=lead)


def answer_display(value, form):
    if form in ALGEBRA_FORMS:
        return Content("x = " + str(value))
    return Content("x = {} degrees".format(value), "x = " + str(value) + r"^{\circ}")


def draw_labels(rng, level):
    form = rng.choice(FORMS[level])
    p = {"form": form, "names": rng.choice(NAME_SETS), "orientation": [0, False]}
    if form == "direct":
        p.update(C=[0, rng.randint(35, 75)], D=[1, 0])
    elif form == "expression":
        x, k, b = rng.randint(10, 25), rng.randint(2, 3), rng.randint(3, 12)
        p.update(C=[0, k * x + b], D=[k, b])
    elif form == "other_chord":
        p.update(A_cross=[0, rng.randint(20, 40)], B_cross=[1, 0])
    elif form == "triangle":
        p.update(C=[0, rng.randint(35, 65)], A_tri=[0, rng.randint(20, 40)], B_tri=[1, 0])
    elif form == "crossing":
        # CAD of 25-45 keeps its label near A and the crossing triangle roomy.
        p.update(D=[0, rng.randint(35, 65)], A_cross=[0, rng.randint(25, 45)], E=[1, 0])
    elif form == "algebra":
        x, k, b = rng.randint(10, 25), rng.randint(2, 3), rng.randint(3, 12)
        p.update(C=[k, b], D=[1, (k - 1) * x + b])
    else:
        x, k, b = rng.randint(10, 25), rng.randint(2, 3), rng.randint(3, 12)
        a = rng.randint(20, 40)
        p.update(C=[k, b], A_tri=[0, a], B_tri=[1, 180 - a - (k * x + b) - x])
    return p


# ------------------------------------------------------------ generator

class SameSegmentAngles:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        for attempt in range(300):
            p = draw_labels(rng, difficulty)
            try:
                x = solve(p)
                require(x.denominator == 1, "x must be a whole number")
                place_free(rng, p, int(x))
                x = check_parameters(p, difficulty)
                p["orientation"] = circle_figures.choose_orientation(
                    rng, lambda orientation: diagram_for(dict(p, orientation=orientation), x))
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a same-segment question")
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=presentation(p, difficulty),
            answer={"kind": "integer", "value": x},
            answer_display=answer_display(x, p["form"]), worked_solution=(),
            marks=MARKS[p["form"]], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=3 if difficulty <= 2 else 4),
            parameters=p, question_visuals=(diagram_for(p, x),),
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid level")
        require(q.settings == {}, "Unsupported settings")
        x = check_parameters(q.parameters, level)
        require(q.answer == {"kind": "integer", "value": x}, "Incorrect answer")
        p = q.parameters
        require(q.prompt == presentation(p, level), "Prompt mismatch")
        require(q.answer_display == answer_display(x, p["form"]), "Answer display mismatch")
        require(q.visual_assets("questions") == (diagram_for(p, x),), "Diagram mismatch")
        require(not q.visual_assets("answers"), "Unexpected answer visuals")
        return True

    def validate_independently(self, q):
        """Measure every labelled angle on the true drawing with atan2."""
        p, x = q.parameters, q.answer.get("value")
        require(type(x) is int, "Expected a whole-number answer")
        t, d, c = (float(v) for v in geometry(p, x))

        def at(degrees):
            angle = math.radians(degrees)
            return (math.cos(angle), math.sin(angle))

        points = {"A": at(270 - t), "B": at(270 + t), "C": at(90 + c), "D": at(90 + d)}
        points["E"] = crossing_point(points["A"], points["D"], points["B"], points["C"])

        def measured(vertex, first, second):
            u = (first[0] - vertex[0], first[1] - vertex[1])
            v = (second[0] - vertex[0], second[1] - vertex[1])
            return math.degrees(math.atan2(abs(u[0] * v[1] - u[1] * v[0]),
                                           u[0] * v[0] + u[1] * v[1]))

        for role in FORM_ROLES[p["form"]]:
            vertex, first, second = CORNERS[role]
            size = measured(points[vertex], points[first], points[second])
            require(abs(size - value_of(p[role], x)) < 1e-6,
                    "Measured {} angle disagrees".format(role))
        return True