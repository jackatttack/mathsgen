"""Tangent theorems drawn from the true kite, with linked forms.

A tangent meets a radius at 90 degrees and the two tangents from P are equal,
so the whole figure is fixed by one half-angle t = angle AOP:
    APO = 90 - t    AOB = 2t    APB = 180 - 2t    PAB = t    OAB = 90 - t
(PAB is a base angle of isosceles triangle APB; OAB of isosceles OAB.)
Labels are [k, b] pairs meaning kx + b degrees. The first label fixes t and
every other label must agree with it, so the drawing is always true. Letters
for A, B and P and the orientation are seeded.
"""
import math
from fractions import Fraction

from . import circle_figures, figures
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)


INFO = GeneratorInfo(
    id="geometry.circle_theorems.tangents", version=2,
    topic="geometry", subtopic="circle_theorems",
    title="Circle theorem: tangents and radii",
    difficulty_descriptions={
        1: "Use the radius-tangent right angle in a triangle, either way round.",
        2: "Relate the angle at the centre and the angle between two tangents.",
        3: "Use equal tangents or equal radii to find a base angle.",
        4: "Form and solve an equation across the kite or the isosceles triangle.",
    },
    tags=("geometry", "circle_theorems", "tangents", "angles", "equations"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("triangle_at_p", "triangle_at_o"),
    2: ("kite", "kite_reverse"),
    3: ("isosceles", "radius_chord"),
    4: ("algebra", "algebra_isosceles"),
}
# The first role fixes the half-angle; for numeric forms the second is x.
FORM_ROLES = {
    "triangle_at_p": ("AOP", "APO"),
    "triangle_at_o": ("APO", "AOP"),
    "kite": ("APB", "AOB"),
    "kite_reverse": ("AOB", "APB"),
    "isosceles": ("APB", "PAB"),
    "radius_chord": ("APB", "OAB"),
    "algebra": ("APB", "AOB"),
    "algebra_isosceles": ("APB", "PAB"),
}
SINGLE_TANGENT = {"triangle_at_p", "triangle_at_o"}
WITH_CHORD = {"isosceles", "radius_chord", "algebra_isosceles"}
ALGEBRA_FORMS = {"algebra", "algebra_isosceles"}
NAME_SETS = ("ABP", "CDP", "STQ", "EFT", "LMN")
MARKS = {
    "triangle_at_p": 2, "triangle_at_o": 2, "kite": 2, "kite_reverse": 2,
    "isosceles": 3, "radius_chord": 3, "algebra": 3, "algebra_isosceles": 3,
}
# role -> (vertex, first arm, second arm) in figure roles O, A, B, P.
CORNERS = {
    "AOP": ("O", "A", "P"), "APO": ("P", "A", "O"), "AOB": ("O", "A", "B"),
    "APB": ("P", "A", "B"), "PAB": ("A", "P", "B"), "OAB": ("A", "O", "B"),
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


def angle_sizes(t):
    return {"AOP": t, "APO": 90 - t, "AOB": 2 * t, "APB": 180 - 2 * t,
            "PAB": t, "OAB": 90 - t}


def half_angle_from(role, value):
    value = Fraction(value)
    return {"AOP": value, "APO": 90 - value, "AOB": value / 2,
            "APB": (180 - value) / 2, "PAB": value, "OAB": 90 - value}[role]


def solve(p):
    """x by the textbook route for each form."""
    form = p["form"]
    first = FORM_ROLES[form][0]
    if form in ("triangle_at_p", "triangle_at_o"):
        return Fraction(90 - p[first][1])
    if form in ("kite", "kite_reverse"):
        return Fraction(180 - p[first][1])
    if form == "isosceles":
        return Fraction(180 - p["APB"][1], 2)
    if form == "radius_chord":
        return Fraction(p["APB"][1], 2)
    if form == "algebra":
        (k1, b1), (k2, b2) = p["APB"], p["AOB"]
        return Fraction(180 - b1 - b2, k1 + k2)
    (k, b), (one, c) = p["APB"], p["PAB"]
    return Fraction(180 - b - 2 * c, k + 2 * one)


def half_angle(p, x):
    first = FORM_ROLES[p["form"]][0]
    return half_angle_from(first, value_of(p[first], x))


def check_parameters(p, level):
    """Check structure and agreement with the kite; return the whole-number x."""
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(form in FORMS[level], "Unexpected form for this level")
    roles = FORM_ROLES[form]
    require(set(p) == {"form", "names", "orientation"} | set(roles),
            "Unexpected parameters")
    require(p["names"] in NAME_SETS, "Invalid letters")
    require(figures.valid_orientation(p["orientation"]), "Invalid orientation")
    for role in roles:
        term = p[role]
        require(isinstance(term, list) and len(term) == 2
                and all(type(v) is int for v in term), "Invalid angle expression")
    x = solve(p)
    require(x.denominator == 1, "x must be a whole number")
    x = int(x)
    t = half_angle(p, x)
    require(t.denominator == 1, "The half-angle must be whole")
    sizes = angle_sizes(t)
    for role in roles:
        require(value_of(p[role], x) == sizes[role], "A label disagrees with the kite")

    if form in SINGLE_TANGENT:
        require(30 <= t <= 60, "Half-angle outside drawable bounds")
    else:
        require(35 <= t <= 60, "Half-angle outside drawable bounds")
    if form in ALGEBRA_FORMS:
        second = roles[1]
        require(2 <= p["APB"][0] <= 4 and 1 <= p[second][0] <= 3
                and p[second] != [1, 0] and 10 <= x <= 30,
                "Wrong algebraic structure")
    else:
        require(p[roles[0]][0] == 0 and p[roles[1]] == [1, 0], "Wrong numeric structure")
        # Equal marked angles would let a student copy the given angle.
        require(abs(sizes[roles[0]] - sizes[roles[1]]) >= 6,
                "Marked angles too close to tell the theorem was used")
    return x


# ------------------------------------------------------------ presentation

def letters(p):
    return dict(zip("ABP", p["names"]))


def angle_name(p, role):
    names = dict(letters(p), O="O")
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


def kite_points(t, centre=circle_figures.CENTRE, radius=circle_figures.RADIUS):
    """O, A, B and P with PA and PB tangent at A and B; OP along the x-axis."""
    turn = math.radians(float(t))
    ox, oy = centre
    return {
        "O": (ox, oy),
        "A": (ox + radius * math.cos(turn), oy + radius * math.sin(turn)),
        "B": (ox + radius * math.cos(turn), oy - radius * math.sin(turn)),
        "P": (ox + radius / math.cos(turn), oy),
    }


def diagram_for(p, x):
    form = p["form"]
    points = kite_points(half_angle(p, x))
    names = letters(p)
    nodes = circle_figures.circle_nodes()
    if form in SINGLE_TANGENT:
        segments = (("O", "A"), ("O", "P"), ("A", "P"))
        right_angles = ("A",)
    else:
        segments = (("O", "A"), ("O", "B"), ("A", "P"), ("B", "P"))
        right_angles = ("A", "B")
    for first, second in segments:
        nodes.append(circle_figures.line(points[first], points[second]))
    if form in WITH_CHORD:
        nodes.append(circle_figures.line(points["A"], points["B"]))
    for vertex in right_angles:
        nodes.append({"type": "right_angle", "vertex": figures.rounded(points[vertex]),
                      "first": figures.rounded(points["O"]),
                      "second": figures.rounded(points["P"])})
    nodes.append(circle_figures.vertex_label(points["O"], "O", away_from=points["P"],
                                             gap=circle_figures.CENTRE_GAP))
    for key in ("A", "P") if form in SINGLE_TANGENT else ("A", "B", "P"):
        nodes.append(circle_figures.vertex_label(points[key], names[key]))
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
    a, b, external = p["names"]
    form = p["form"]
    if form in SINGLE_TANGENT:
        lead = ("O is the centre of the circle. {0}{1} is a tangent, touching the "
                "circle at {1}.").format(external, a)
    else:
        lead = ("O is the centre of the circle. {0}{1} and {0}{2} are tangents, "
                "touching the circle at {1} and {2}.").format(external, a, b)
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


def draw(rng, level):
    form = rng.choice(FORMS[level])
    p = {"form": form, "names": rng.choice(NAME_SETS), "orientation": [0, False]}
    t = rng.randint(30, 60) if form in SINGLE_TANGENT else rng.randint(35, 60)
    sizes = angle_sizes(Fraction(t))
    if form == "algebra":
        x, k1, k2 = rng.randint(10, 30), rng.randint(2, 4), rng.randint(1, 3)
        p["APB"] = [k1, int(sizes["APB"]) - k1 * x]
        p["AOB"] = [k2, int(sizes["AOB"]) - k2 * x]
    elif form == "algebra_isosceles":
        x, k = rng.randint(10, 30), rng.randint(2, 3)
        p["APB"] = [k, int(sizes["APB"]) - k * x]
        p["PAB"] = [1, int(sizes["PAB"]) - x]
    else:
        given, unknown = FORM_ROLES[form]
        p[given] = [0, int(sizes[given])]
        p[unknown] = [1, 0]
    return p


# ------------------------------------------------------------ generator

class TangentTheorems:
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
            raise ValueError("Could not construct a tangent question")
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
                "Tangent diagram mismatch")
        require(not q.visual_assets("answers"), "Unexpected answer visuals")
        return True

    def validate_independently(self, q):
        """Build the kite from the first label, confirm tangency, measure with atan2."""
        p, x = q.parameters, q.answer.get("value")
        require(type(x) is int, "Expected a whole-number answer")
        t = half_angle(p, x)
        require(0 < t < 90, "Independent half-angle impossible")
        points = kite_points(t, centre=(0.0, 0.0), radius=1.0)

        def dot(first, vertex, second):
            return ((first[0] - vertex[0]) * (second[0] - vertex[0])
                    + (first[1] - vertex[1]) * (second[1] - vertex[1]))

        for touch in ("A", "B"):
            require(abs(dot(points["O"], points[touch], points["P"])) < 1e-9,
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