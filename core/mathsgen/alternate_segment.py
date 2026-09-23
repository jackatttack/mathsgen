"""Alternate segment theorem drawn from true arcs, with linked forms.

The tangent TS touches the circle at A, and B and C lie on the circle. The
figure is stored as three even arcs: ab (A to B, the minor arc), bc and ca,
summing to 360. With t = ab / 2:
    BAT = ACB = t              (alternate segment, chord AB, T on B's side)
    CAS = ABC = ca / 2         (alternate segment, chord AC, S on C's side)
    BAC = bc / 2               AOB = ab = 2t   (O the centre)
Labels are [k, b] pairs meaning kx + b degrees and must agree with the arcs,
so the drawing is always true. Letters and orientation are seeded.
"""
import math
from fractions import Fraction

from . import circle_figures, figures
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)


INFO = GeneratorInfo(
    id="geometry.circle_theorems.alternate_segment", version=4,
    topic="geometry", subtopic="circle_theorems",
    title="Circle theorem: alternate segment",
    difficulty_descriptions={
        1: "Apply the theorem forwards or backwards on one chord.",
        2: "Apply the theorem to the other chord, either way round.",
        3: "Apply the theorem, then the triangle sum or the angle at the centre.",
        4: "Form and solve an equation, directly or with the triangle sum.",
    },
    tags=("geometry", "circle_theorems", "tangents", "angles", "equations"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("forward", "backward"),
    2: ("other_chord", "other_chord_reverse"),
    3: ("triangle", "centre"),
    4: ("algebra", "algebra_triangle"),
}
# Labelled angles; for numeric forms the last role is x.
FORM_ROLES = {
    "forward": ("BAT", "ACB"),
    "backward": ("ACB", "BAT"),
    "other_chord": ("CAS", "ABC"),
    "other_chord_reverse": ("ABC", "CAS"),
    "triangle": ("BAT", "ABC", "BAC"),
    "centre": ("BAT", "AOB"),
    "algebra": ("BAT", "ACB"),
    "algebra_triangle": ("BAT", "ABC", "BAC"),
}
ALGEBRA_FORMS = {"algebra", "algebra_triangle"}
CENTRE_FORMS = {"centre"}
# Letters in role order A, B, C, T, S.
NAME_SETS = ("ABCTS", "PQRXY", "EFGUV", "KLMWZ", "JKLPQ")
MARKS = {
    "forward": 1, "backward": 1, "other_chord": 2, "other_chord_reverse": 2,
    "triangle": 3, "centre": 3, "algebra": 3, "algebra_triangle": 3,
}
LEAST_ARC = 50
TANGENT_HALF_LENGTH = 110
# role -> (vertex, first arm, second arm)
CORNERS = {
    "BAT": ("A", "T", "B"), "ACB": ("C", "A", "B"), "BAC": ("A", "B", "C"),
    "ABC": ("B", "A", "C"), "CAS": ("A", "C", "S"), "AOB": ("O", "A", "B"),
}


# ------------------------------------------------------------ mathematics

def expression(term):
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
    ab, bc, ca = arcs
    t = Fraction(ab, 2)
    return {"BAT": t, "ACB": t, "CAS": Fraction(ca, 2), "ABC": Fraction(ca, 2),
            "BAC": Fraction(bc, 2), "AOB": Fraction(ab)}


def canonical_split(ab):
    """Arc BC used when C is not drawn: half the rest, rounded to an even number."""
    return 2 * ((360 - ab) // 4)


def solve(p):
    """x by the textbook route for each form."""
    form = p["form"]
    if form in ("forward", "backward", "other_chord", "other_chord_reverse"):
        return Fraction(p[FORM_ROLES[form][0]][1])
    if form == "triangle":
        return Fraction(180 - p["BAT"][1] - p["ABC"][1])
    if form == "centre":
        return Fraction(2 * p["BAT"][1])
    if form == "algebra":
        (k, b), (one, c) = p["BAT"], p["ACB"]
        require(k != one, "Angles do not determine x")
        return Fraction(c - b, k - one)
    (k, b), (_, a), (one, c) = p["BAT"], p["ABC"], p["BAC"]
    return Fraction(180 - b - a - c, k + one)


def check_parameters(p, level):
    """Check structure, arcs and label agreement; return the whole-number x."""
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(form in FORMS[level], "Unexpected form for this level")
    roles = FORM_ROLES[form]
    require(set(p) == {"form", "names", "arcs", "orientation"} | set(roles),
            "Unexpected parameters")
    require(p["names"] in NAME_SETS, "Invalid letters")
    require(figures.valid_orientation(p["orientation"]), "Invalid orientation")
    arcs = p["arcs"]
    require(isinstance(arcs, list) and len(arcs) == 3
            and all(type(v) is int and v % 2 == 0 for v in arcs)
            and sum(arcs) == 360, "Invalid arcs")
    require(60 <= arcs[0] <= 140, "Tangent-chord angle outside drawable bounds")
    require(arcs[1] >= LEAST_ARC and arcs[2] >= LEAST_ARC, "Arc too small to draw")
    if form in CENTRE_FORMS:
        # C is not drawn, so its split of the major arc is fixed, not free.
        require(arcs[1] == canonical_split(arcs[0]), "Non-canonical arcs")
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
    if form == "algebra":
        require(2 <= p["BAT"][0] <= 4 and p["ACB"][0] == 1 and p["ACB"][1] != 0
                and 10 <= x <= 30, "Wrong algebraic structure")
    elif form == "algebra_triangle":
        require(2 <= p["BAT"][0] <= 3 and p["ABC"][0] == 0 and p["BAC"][0] == 1
                and p["BAC"][1] != 0 and 10 <= x <= 30,
                "Wrong algebraic triangle structure")
    else:
        *given, unknown = roles
        require(all(p[role][0] == 0 for role in given) and p[unknown] == [1, 0],
                "Wrong numeric structure")
        if form == "triangle":
            # Copying a given angle must never happen to be right.
            require(all(abs(x - p[role][1]) >= 6 for role in given),
                    "Answer too close to a given angle")
    return x


# ------------------------------------------------------------ presentation

def letters(p):
    return dict(zip("ABCTS", p["names"]), O="O")


def angle_name(p, role):
    names = letters(p)
    return "angle " + "".join(names[ch] for ch in role)


def label_texts(p):
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


def figure_points(arcs, on=circle_figures.on_circle, centre=circle_figures.CENTRE,
                  half_length=TANGENT_HALF_LENGTH):
    """A at the bottom, B and C anticlockwise on screen, tangent through A."""
    ab, bc, ca = arcs
    a = on(90)
    return {
        "O": tuple(centre), "A": a, "B": on(90 + ab), "C": on(90 + ab + bc),
        "T": (a[0] - half_length, a[1]), "S": (a[0] + half_length, a[1]),
    }


def diagram_for(p, x):
    form = p["form"]
    roles = FORM_ROLES[form]
    points = figure_points(p["arcs"])
    names = letters(p)
    if form in CENTRE_FORMS:
        nodes = circle_figures.circle_nodes()
        segments = [("T", "S"), ("A", "B"), ("O", "A"), ("O", "B")]
        labelled = ["A", "B"]
        middle = ((points["A"][0] + points["B"][0]) / 2,
                  (points["A"][1] + points["B"][1]) / 2)
        nodes.append(circle_figures.vertex_label(points["O"], "O", away_from=middle,
                                                 gap=circle_figures.CENTRE_GAP))
    else:
        nodes = [{"type": "circle", "center": figures.rounded(circle_figures.CENTRE),
                  "radius": circle_figures.RADIUS}]
        segments = [("T", "S"), ("A", "B"), ("A", "C"), ("B", "C")]
        labelled = ["A", "B", "C"]
    for first, second in segments:
        nodes.append(circle_figures.line(points[first], points[second]))
    for key in labelled:
        nodes.append(circle_figures.vertex_label(points[key], names[key]))
    for key in ("T", "S"):
        nodes.append(circle_figures.vertex_label(points[key], names[key],
                                                 away_from=points["A"], gap=18))
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
    names = letters(p)
    form = p["form"]
    if form in CENTRE_FORMS:
        lead = ("O is the centre of the circle. {T}{S} is a tangent to the circle "
                "at {A}. {B} lies on the circle.").format(**names)
    else:
        lead = ("{T}{S} is a tangent to the circle at {A}. {B} and {C} lie on "
                "the circle.").format(**names)
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
        return Content("x = {}".format(value), "x = {}".format(value))
    return Content("x = {} degrees".format(value), str(value) + r"^{\circ}")


def draw(rng, level):
    form = rng.choice(FORMS[level])
    ab = 2 * rng.randint(30, 70)
    rest = 360 - ab
    if form in CENTRE_FORMS:
        bc = canonical_split(ab)
    else:
        bc = 2 * rng.randint(LEAST_ARC // 2, rest // 2 - LEAST_ARC // 2)
    arcs = [ab, bc, rest - bc]
    sizes = angle_sizes(arcs)
    p = {"form": form, "names": rng.choice(NAME_SETS), "arcs": arcs,
         "orientation": [0, False]}
    if form == "algebra":
        x, k = rng.randint(10, 30), rng.randint(2, 4)
        p["BAT"] = [k, int(sizes["BAT"]) - k * x]
        p["ACB"] = [1, int(sizes["ACB"]) - x]
    elif form == "algebra_triangle":
        x, k = rng.randint(10, 30), rng.randint(2, 3)
        p["BAT"] = [k, int(sizes["BAT"]) - k * x]
        p["ABC"] = [0, int(sizes["ABC"])]
        p["BAC"] = [1, int(sizes["BAC"]) - x]
    else:
        *given, unknown = FORM_ROLES[form]
        for role in given:
            p[role] = [0, int(sizes[role])]
        p[unknown] = [1, 0]
    return p


# ------------------------------------------------------------ generator

class AlternateSegment:
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
            raise ValueError("Could not construct an alternate-segment question")
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
                "Alternate segment diagram mismatch")
        require(not q.visual_assets("answers"), "Unexpected answer visuals")
        return True

    def validate_independently(self, q):
        """Place points from the arcs, confirm OA is perpendicular to TS, measure with atan2."""
        p, x = q.parameters, q.answer.get("value")
        require(type(x) is int, "Expected a whole-number answer")

        def unit_circle(degrees):
            angle = math.radians(degrees)
            return (math.cos(angle), math.sin(angle))

        points = figure_points(p["arcs"], on=unit_circle, centre=(0.0, 0.0),
                               half_length=1.0)
        tangent = (points["S"][0] - points["T"][0], points["S"][1] - points["T"][1])
        radius = points["A"]
        require(abs(tangent[0] * radius[0] + tangent[1] * radius[1]) < 1e-9,
                "Tangent is not perpendicular to the radius")

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