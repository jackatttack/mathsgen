"""Centre/circumference theorem drawn from true positions, with linked forms.

Each question labels two of three angles: the minor angle AOB at the centre,
the angle ACB at the circumference, and the base angle OAB of the isosceles
triangle OAB. A label is [k, b], meaning kx + b degrees. The form decides
which pair is labelled and whether C lies on the major or the minor arc.

Every label converts to "the minor central angle AOB" as a linear expression
in x, so one solver covers every form. Diagrams place A, B and C at their true
positions, vary where C sits on its arc, vary the letters and use a seeded
orientation; validation rebuilds the exact scene from the parameters.
"""
from fractions import Fraction

from . import circle_figures, figures
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)


INFO = GeneratorInfo(
    id="geometry.circle_theorems.centre_angle", version=2,
    topic="geometry", subtopic="circle_theorems",
    title="Circle theorem: angle at the centre",
    difficulty_descriptions={
        1: "Find the central angle from an angle at the circumference.",
        2: "Find a circumference angle, or a base angle via the isosceles triangle.",
        3: "Recover a reflex central angle, directly or from a base angle.",
        4: "Form and solve an equation from two algebraic angle labels.",
    },
    tags=("geometry", "circle_theorems", "angles", "equations"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("central",),
    2: ("circumference", "base_angle"),
    3: ("reflex", "base_to_reflex"),
    4: ("algebra", "algebra_base"),
}
# The labelled pair for each form; the first label fixes the drawing.
FORM_ROLES = {
    "central": ("central", "circumference"),
    "circumference": ("central", "circumference"),
    "base_angle": ("circumference", "base"),
    "reflex": ("central", "circumference"),
    "base_to_reflex": ("base", "circumference"),
    "algebra": ("central", "circumference"),
    "algebra_base": ("circumference", "base"),
}
MINOR_ARC_FORMS = {"reflex", "base_to_reflex"}
ALGEBRA_FORMS = {"algebra", "algebra_base"}
NAME_SETS = ("ABC", "PQR", "DEF", "KLM", "STU")
MARKS = {
    "central": 1, "circumference": 1, "base_angle": 2, "reflex": 3,
    "base_to_reflex": 3, "algebra": 3, "algebra_base": 4,
}
FIXED_KEYS = {"form", "names", "orientation", "c_shift"}


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


def central_line(role, term, minor):
    """The minor central angle AOB implied by one label, as (coefficient, constant)."""
    k, b = term
    if role == "central":
        return Fraction(k), Fraction(b)
    if role == "circumference":
        if minor:
            return Fraction(-2 * k), Fraction(360 - 2 * b)
        return Fraction(2 * k), Fraction(2 * b)
    return Fraction(-2 * k), Fraction(180 - 2 * b)


def solve(p):
    minor = p["form"] in MINOR_ARC_FORMS
    first, second = (central_line(role, p[role], minor) for role in FORM_ROLES[p["form"]])
    require(first[0] != second[0], "Labels do not determine x")
    return (second[1] - first[1]) / (first[0] - second[0])


def central_value(p, x):
    role = FORM_ROLES[p["form"]][0]
    k, b = central_line(role, p[role], p["form"] in MINOR_ARC_FORMS)
    return k * x + b


def shift_limit(p, central):
    """How far C may move from the middle of its arc, in whole 5-degree steps."""
    if p["form"] in MINOR_ARC_FORMS:
        room = min(30, central / 2 - 25)
    else:
        room = min(45, 180 - central / 2 - 35)
    return max(0, int(room) // 5 * 5)


def check_parameters(p, level):
    """Check structure and ranges; return the whole-number answer x."""
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(form in FORMS[level], "Unexpected form for this level")
    roles = FORM_ROLES[form]
    require(set(p) == FIXED_KEYS | set(roles), "Unexpected parameters")
    require(p["names"] in NAME_SETS, "Invalid letters")
    require(figures.valid_orientation(p["orientation"]), "Invalid orientation")
    for role in roles:
        term = p[role]
        require(isinstance(term, list) and len(term) == 2
                and all(type(v) is int for v in term), "Invalid angle expression")
    x = solve(p)
    require(x.denominator == 1, "x must be a whole number")
    x = int(x)
    central = central_value(p, x)
    require(20 <= central <= 170, "Central angle outside range")
    for role in roles:
        require(0 < value_of(p[role], x) < 180, "Labelled angle outside range")

    c, g, base = p.get("central"), p.get("circumference"), p.get("base")
    if form == "central":
        require(c == [1, 0] and g[0] == 0 and 30 <= g[1] <= 75, "Wrong direct structure")
    elif form == "circumference":
        require(g == [1, 0] and c[0] == 0 and c[1] % 2 == 0 and 60 <= c[1] <= 150,
                "Wrong reverse structure")
    elif form == "base_angle":
        require(base == [1, 0] and g[0] == 0 and 30 <= g[1] <= 65,
                "Wrong base-angle structure")
    elif form == "reflex":
        require(g == [1, 0] and c[0] == 0 and 100 <= x <= 145, "Wrong reflex structure")
    elif form == "base_to_reflex":
        require(g == [1, 0] and base[0] == 0 and 25 <= base[1] <= 35,
                "Wrong base-to-reflex structure")
    elif form == "algebra":
        require(c[0] == 3 and g[0] == 1 and 15 <= g[1] <= 25 and 5 <= c[1] <= 40
                and 10 <= x <= 25, "Wrong algebraic structure")
    else:
        require(g[0] == 1 and base[0] == 1 and 5 <= g[1] <= 25 and base[1] >= 1
                and base[1] != g[1] and 10 <= x <= 25 and value_of(base, x) >= 20,
                "Wrong algebraic base structure")

    shift = p["c_shift"]
    require(type(shift) is int and shift % 5 == 0
            and abs(shift) <= shift_limit(p, central), "Invalid position for C")
    return x


# ------------------------------------------------------------ presentation

def label_tex(term):
    text = expression(term) if term != [1, 0] else "x"
    if term[0] and term[1]:
        text = "(" + text + ")"
    return text + r"^{\circ}", len(text)


def diagram_for(p, x):
    form = p["form"]
    roles = FORM_ROLES[form]
    central = float(central_value(p, x))
    minor = form in MINOR_ARC_FORMS
    centre = circle_figures.CENTRE
    a = circle_figures.on_circle(270 - central / 2)
    b = circle_figures.on_circle(270 + central / 2)
    c = circle_figures.on_circle((270 if minor else 90) + p["c_shift"])
    first, second, third = p["names"]
    middle = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)

    nodes = circle_figures.circle_nodes()
    for start, end in ((centre, a), (centre, b), (c, a), (c, b)):
        nodes.append(circle_figures.line(start, end))
    if "base" in roles:
        nodes.append(circle_figures.line(a, b))
    nodes += [
        circle_figures.vertex_label(a, first),
        circle_figures.vertex_label(b, second),
        circle_figures.vertex_label(c, third),
        circle_figures.vertex_label(centre, "O", away_from=middle,
                                    gap=circle_figures.CENTRE_GAP),
    ]
    corners = {"central": (centre, a, b), "circumference": (c, a, b), "base": (a, centre, b)}
    for index, role in enumerate(roles):
        if form in ALGEBRA_FORMS:
            # Long expressions cannot sit inside these angles at 250 pt, so the
            # diagram names them u and v and the prompt states the expressions.
            tex, length = ("u", "v")[index] + r"^{\circ}", 1
        else:
            tex, length = label_tex(p[role])
        nodes += circle_figures.angle_mark(*corners[role], tex, length)
    scene = {
        "kind": "scene", "version": 1, "width": 360, "height": 300,
        "caption": "Not drawn accurately", "nodes": nodes,
    }
    return figures.orient_scene(scene, p["orientation"])


def presentation(p, level):
    first, second, third = p["names"]
    form = p["form"]
    lead = (
        "O is the centre of the circle. {}, {} and {} lie on the circumference. Find x."
    ).format(first, second, third)
    if form in ALGEBRA_FORMS:
        lead += " In the diagram, u = {} and v = {}, in degrees.".format(
            *(expression(p[role]) for role in FORM_ROLES[form]))
    wording = {
        "central": "the minor angle {}O{}".format(first, second),
        "circumference": "angle {}{}{}".format(first, third, second),
        "base": "angle O{}{}".format(first, second),
    }
    parts = ["{} is {} degrees".format(wording[role], expression(p[role]))
             for role in FORM_ROLES[form]]
    fallback = " Marked: {}. {} lies on the {} arc {}{}.".format(
        "; ".join(parts), third, "minor" if form in MINOR_ARC_FORMS else "major",
        first, second)
    return Content(lead + fallback, display_text=lead)


def display(value, form):
    if form in ALGEBRA_FORMS:
        return Content("x = " + str(value))
    return Content("x = {} degrees".format(value), str(value) + r"^{\circ}")


def draw(rng, level):
    form = rng.choice(FORMS[level])
    p = {"form": form, "names": rng.choice(NAME_SETS),
         "orientation": [0, False], "c_shift": 0}
    if form == "central":
        p.update(central=[1, 0], circumference=[0, rng.randint(30, 75)])
    elif form == "circumference":
        p.update(central=[0, 2 * rng.randint(30, 75)], circumference=[1, 0])
    elif form == "base_angle":
        p.update(circumference=[0, rng.randint(30, 65)], base=[1, 0])
    elif form == "reflex":
        p.update(central=[0, 360 - 2 * rng.randint(100, 145)], circumference=[1, 0])
    elif form == "base_to_reflex":
        # 25-35 keeps triangle OAB tall enough for its label and leaves room
        # for the obtuse label at C above chord AB.
        p.update(base=[0, rng.randint(25, 35)], circumference=[1, 0])
    elif form == "algebra":
        value, offset = rng.randint(10, 25), rng.randint(15, 25)
        p.update(central=[3, 2 * offset - value], circumference=[1, offset])
    else:
        value, first = rng.randint(10, 25), rng.randint(5, 25)
        p.update(circumference=[1, first], base=[1, 90 - 2 * value - first])
    return p


# ------------------------------------------------------------ generator

class CircleCentreAngles:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        for attempt in range(300):
            p = draw(rng, difficulty)
            try:
                x = check_parameters(p, difficulty)
                limit = shift_limit(p, central_value(p, x))
                p["c_shift"] = rng.randrange(-limit, limit + 1, 5) if limit else 0
                check_parameters(p, difficulty)
                p["orientation"] = circle_figures.choose_orientation(
                    rng, lambda orientation: diagram_for(dict(p, orientation=orientation), x))
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a centre-angle question")
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
        """Measure a true drawing with atan2; the theorem itself is never used.

        A and B are placed from the central or base label alone, C goes on the
        stated arc, and every labelled angle must match its measured size.
        """
        import math
        p, x = q.parameters, q.answer.get("value")
        require(type(x) is int, "Expected a whole-number answer")
        form = p["form"]
        if "central" in p:
            central = value_of(p["central"], x)
        else:
            central = 180 - 2 * value_of(p["base"], x)
        require(0 < central < 180, "Independent central angle impossible")
        half = math.radians(central) / 2
        a = (math.cos(-half), math.sin(-half))
        b = (math.cos(half), math.sin(half))
        c_angle = half / 3 if form in MINOR_ARC_FORMS else math.pi + 0.4
        c = (math.cos(c_angle), math.sin(c_angle))
        o = (0.0, 0.0)

        def measured(vertex, first, second):
            u = (first[0] - vertex[0], first[1] - vertex[1])
            v = (second[0] - vertex[0], second[1] - vertex[1])
            return math.degrees(math.atan2(abs(u[0] * v[1] - u[1] * v[0]),
                                           u[0] * v[0] + u[1] * v[1]))

        sizes = {"central": measured(o, a, b), "circumference": measured(c, a, b),
                 "base": measured(a, o, b)}
        for role in FORM_ROLES[form]:
            require(abs(sizes[role] - value_of(p[role], x)) < 1e-6,
                    "Measured {} angle disagrees".format(role))
        return True