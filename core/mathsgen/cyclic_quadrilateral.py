"""Cyclic quadrilateral theorems, drawn from true arcs, with linked forms.

The quadrilateral P0 P1 P2 P3 is stored as four arcs between consecutive
vertices: a = P0P1, b = P1P2, c = P2P3 and d = P3P0, all even so every angle
is a whole number. Each inscribed angle is half the arc it stands on:
    interior at P0 = (b + c) / 2    interior at P2 = (d + a) / 2
    interior at P1 = (c + d) / 2    interior at P3 = (a + b) / 2
    exterior at P2 (side P3P2 extended) = 180 - interior at P2
    angle P1P0P2 = b / 2, angle P2P0P3 = c / 2, angle P0P2P1 = a / 2
Labels are [k, b] pairs meaning kx + b degrees and must agree with the arcs,
so the drawing is always true. A seeded start index decides which letter P0
carries; letter set and orientation are seeded too.
"""
import math
from fractions import Fraction

from . import circle_figures, figures
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)


INFO = GeneratorInfo(
    id="geometry.circle_theorems.cyclic_quadrilateral", version=3,
    topic="geometry", subtopic="circle_theorems",
    title="Circle theorem: opposite angles of a cyclic quadrilateral",
    difficulty_descriptions={
        1: "Find the angle opposite a given angle.",
        2: "Link an exterior angle to the opposite interior angle, either way round.",
        3: "Use a diagonal: a triangle's angle sum or a split angle, then opposite angles.",
        4: "Form and solve an equation from opposite or exterior algebraic angles.",
    },
    tags=("geometry", "circle_theorems", "angles", "equations"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("opposite",),
    2: ("exterior", "exterior_reverse"),
    3: ("triangle_diagonal", "diagonal_split"),
    4: ("algebra", "algebra_exterior"),
}
# Labelled angles for each form; for numeric forms the last role is x.
FORM_ROLES = {
    "opposite": ("int0", "int2"),
    "exterior": ("ext2", "int0"),
    "exterior_reverse": ("int0", "ext2"),
    "triangle_diagonal": ("d01", "d21", "int3"),
    "diagonal_split": ("d01", "d03", "int2"),
    "algebra": ("int0", "int2"),
    "algebra_exterior": ("ext2", "int0"),
}
ALGEBRA_FORMS = {"algebra", "algebra_exterior"}
NAME_SETS = ("ABCD", "PQRS", "EFGH", "KLMN", "WXYZ")
MARKS = {
    "opposite": 2, "exterior": 2, "exterior_reverse": 2, "triangle_diagonal": 3,
    "diagonal_split": 3, "algebra": 3, "algebra_exterior": 3,
}
LEAST_ARC = 44
EXTENSION = 60      # canvas length of the extended side beyond P2
FIRST_POSITION = 200

# role -> (vertex, first arm, second arm) in figure roles P0-P3 and X.
CORNERS = {
    "int0": ("P0", "P3", "P1"), "int1": ("P1", "P0", "P2"),
    "int2": ("P2", "P1", "P3"), "int3": ("P3", "P2", "P0"),
    "ext2": ("P2", "P1", "X"),
    "d01": ("P0", "P1", "P2"), "d03": ("P0", "P2", "P3"), "d21": ("P2", "P0", "P1"),
}


# ------------------------------------------------------------ mathematics

def expression(term):
    """Write [coefficient, constant] as an angle expression."""
    k, b = term
    if not k:
        return str(b)
    text = "x" if k == 1 else str(k) + "x"
    if b:
        text += (" + " if b > 0 else " - ") + str(abs(b))
    return text


def value_of(term, x):
    return term[0] * x + term[1]


def angle_sizes(arcs):
    a, b, c, d = arcs
    interior_2 = Fraction(d + a, 2)
    return {
        "int0": Fraction(b + c, 2), "int1": Fraction(c + d, 2),
        "int2": interior_2, "int3": Fraction(a + b, 2),
        "ext2": 180 - interior_2,
        "d01": Fraction(b, 2), "d03": Fraction(c, 2), "d21": Fraction(a, 2),
    }


def solve(p):
    """x by the textbook route for each form."""
    form = p["form"]
    if form == "opposite":
        return Fraction(180 - p["int0"][1])
    if form == "exterior":
        return Fraction(p["ext2"][1])
    if form == "exterior_reverse":
        return Fraction(p["int0"][1])
    if form == "triangle_diagonal":
        return Fraction(p["d01"][1] + p["d21"][1])
    if form == "diagonal_split":
        return Fraction(180 - p["d01"][1] - p["d03"][1])
    if form == "algebra":
        (k1, b1), (k2, b2) = p["int0"], p["int2"]
        return Fraction(180 - b1 - b2, k1 + k2)
    (k, b), (one, c) = p["ext2"], p["int0"]
    require(k != one, "Angles do not determine x")
    return Fraction(c - b, k - one)


def check_parameters(p, level):
    """Check structure, arcs and label agreement; return the whole-number x."""
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(form in FORMS[level], "Unexpected form for this level")
    roles = FORM_ROLES[form]
    require(set(p) == {"form", "names", "start", "arcs", "orientation"} | set(roles),
            "Unexpected parameters")
    require(p["names"] in NAME_SETS, "Invalid letters")
    require(type(p["start"]) is int and 0 <= p["start"] <= 3, "Invalid starting letter")
    require(figures.valid_orientation(p["orientation"]), "Invalid orientation")
    arcs = p["arcs"]
    require(isinstance(arcs, list) and len(arcs) == 4
            and all(type(v) is int and v % 2 == 0 and v >= LEAST_ARC for v in arcs)
            and sum(arcs) == 360, "Invalid arcs")
    for role in roles:
        term = p[role]
        require(isinstance(term, list) and len(term) == 2
                and all(type(v) is int for v in term), "Invalid angle expression")
    x = solve(p)
    require(x.denominator == 1, "x must be a whole number")
    x = int(x)
    sizes = angle_sizes(arcs)
    for role in roles:
        require(value_of(p[role], x) == sizes[role], "A label disagrees with the drawing")
    for index in range(4):
        require(40 <= sizes["int%d" % index] <= 140, "Interior angle outside range")

    numeric = lambda role: p[role][0] == 0
    if form in ("opposite", "exterior", "exterior_reverse"):
        given, unknown = roles
        require(numeric(given) and p[unknown] == [1, 0], "Wrong numeric structure")
        require(50 <= sizes["int0"] <= 130 and abs(sizes["int0"] - 90) >= 5,
                "A right angle would not show the theorem")
    elif form in ("triangle_diagonal", "diagonal_split"):
        first, second, unknown = roles
        require(numeric(first) and numeric(second) and p[unknown] == [1, 0]
                and sizes[first] >= 22 and sizes[second] >= 22,
                "Wrong diagonal structure")
    elif form == "algebra":
        require(2 <= p["int0"][0] <= 4 and 1 <= p["int2"][0] <= 3 and 10 <= x <= 30
                and abs(sizes["int0"] - 90) >= 5, "Wrong algebraic structure")
    else:
        require(2 <= p["ext2"][0] <= 4 and p["int0"][0] == 1 and p["int0"][1] != 0
                and 10 <= x <= 30 and abs(sizes["int0"] - 90) >= 5,
                "Wrong algebraic exterior structure")
    return x


# ------------------------------------------------------------ presentation

def letter(p, index):
    return p["names"][(p["start"] + index) % 4]


def angle_name(p, role):
    if role == "ext2":
        return "the exterior angle at " + letter(p, 2)
    vertex, first, second = CORNERS[role]
    return "angle " + "".join(letter(p, int(key[1])) for key in (first, vertex, second))


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


def figure_points(arcs, on=circle_figures.on_circle):
    a, b, c, d = arcs
    positions = (FIRST_POSITION, FIRST_POSITION + a,
                 FIRST_POSITION + a + b, FIRST_POSITION + a + b + c)
    return {"P%d" % i: on(t) for i, t in enumerate(positions)}


def diagram_for(p, x):
    roles = FORM_ROLES[p["form"]]
    points = figure_points(p["arcs"])
    nodes = [{"type": "circle", "center": figures.rounded(circle_figures.CENTRE),
              "radius": circle_figures.RADIUS}]
    # Sides are lines, not a polygon, so label clearance checks them.
    for first, second in (("P0", "P1"), ("P1", "P2"), ("P2", "P3"), ("P3", "P0")):
        nodes.append(circle_figures.line(points[first], points[second]))
    if any(role.startswith("d") for role in roles):
        nodes.append(circle_figures.line(points["P0"], points["P2"]))
    if "ext2" in roles:
        outward = figures.unit(figures.minus(points["P2"], points["P3"]))
        points["X"] = (points["P2"][0] + outward[0] * EXTENSION,
                       points["P2"][1] + outward[1] * EXTENSION)
        nodes.append(circle_figures.line(points["P2"], points["X"]))
    for index in range(4):
        nodes.append(circle_figures.vertex_label(points["P%d" % index], letter(p, index)))
    for role, text in label_texts(p).items():
        vertex, first, second = CORNERS[role]
        nodes += circle_figures.angle_mark(points[vertex], points[first], points[second],
                                           text + r"^{\circ}", len(text))
    scene = {
        "kind": "scene", "version": 1, "width": 360, "height": 300,
        "caption": "Not drawn accurately", "nodes": nodes,
    }
    return figures.orient_scene(scene, p["orientation"])


def presentation(p, level):
    form = p["form"]
    lead = "{}, {}, {} and {} lie on the circle.".format(*p["names"])
    if "ext2" in FORM_ROLES[form]:
        lead += " Side {}{} is extended beyond {}.".format(
            letter(p, 3), letter(p, 2), letter(p, 2))
    if form in ("triangle_diagonal", "diagonal_split"):
        lead += " The diagonal {}{} is drawn.".format(letter(p, 0), letter(p, 2))
    texts = label_texts(p)
    definitions = ["{} = {}".format(texts[role], expression(p[role]))
                   for role in FORM_ROLES[form] if texts[role] in ("u", "v")]
    if definitions:
        lead += " In the diagram, " + " and ".join(definitions) + ", in degrees."
    lead += " Find x."
    fallback = " Marked: " + "; ".join(
        "{} is {} degrees".format(angle_name(p, role), expression(p[role]))
        for role in FORM_ROLES[form]) + "."
    return Content(lead + fallback, display_text=lead)


def display(value, form):
    if form in ALGEBRA_FORMS:
        return Content("x = " + str(value))
    return Content("x = {} degrees".format(value), str(value) + r"^{\circ}")


def draw_arcs(rng):
    units = (360 - 4 * LEAST_ARC) // 2
    cuts = sorted(rng.randint(0, units) for _ in range(3))
    parts = (cuts[0], cuts[1] - cuts[0], cuts[2] - cuts[1], units - cuts[2])
    return [LEAST_ARC + 2 * part for part in parts]


def draw(rng, level):
    form = rng.choice(FORMS[level])
    arcs = draw_arcs(rng)
    sizes = angle_sizes(arcs)
    p = {"form": form, "names": rng.choice(NAME_SETS), "start": rng.randrange(4),
         "arcs": arcs, "orientation": [0, False]}
    if form == "algebra":
        x, k1, k2 = rng.randint(10, 30), rng.randint(2, 4), rng.randint(1, 3)
        p["int0"] = [k1, int(sizes["int0"]) - k1 * x]
        p["int2"] = [k2, int(sizes["int2"]) - k2 * x]
    elif form == "algebra_exterior":
        x, k = rng.randint(10, 30), rng.randint(2, 4)
        p["ext2"] = [k, int(sizes["ext2"]) - k * x]
        p["int0"] = [1, int(sizes["int0"]) - x]
    else:
        *given, unknown = FORM_ROLES[form]
        for role in given:
            p[role] = [0, int(sizes[role])]
        p[unknown] = [1, 0]
    return p


# ------------------------------------------------------------ generator

class CyclicQuadrilateral:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        for attempt in range(400):
            p = draw(rng, difficulty)
            try:
                x = check_parameters(p, difficulty)
                p["orientation"] = circle_figures.choose_orientation(
                    rng, lambda orientation: diagram_for(dict(p, orientation=orientation), x))
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a cyclic-quadrilateral question")
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=presentation(p, difficulty),
            answer={"kind": "integer", "value": x},
            answer_display=display(x, p["form"]), worked_solution=(),
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
        require(q.answer_display == display(x, p["form"]), "Answer display mismatch")
        require(q.visual_assets("questions") == (diagram_for(p, x),),
                "Circle diagram mismatch")
        require(not q.visual_assets("answers"), "Unexpected answer visuals")
        return True

    def validate_independently(self, q):
        """Place the vertices from the arcs alone and measure each label with atan2."""
        p, x = q.parameters, q.answer.get("value")
        require(type(x) is int, "Expected a whole-number answer")

        def unit_circle(degrees):
            angle = math.radians(degrees)
            return (math.cos(angle), math.sin(angle))

        points = figure_points(p["arcs"], on=unit_circle)
        outward = figures.unit(figures.minus(points["P2"], points["P3"]))
        points["X"] = (points["P2"][0] + outward[0], points["P2"][1] + outward[1])

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