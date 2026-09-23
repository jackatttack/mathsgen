"""Angles in triangles, drawn from the actual angles in varied orientations.

Forms by level:
1 missing         two angles given; the unknown can sit at any vertex
2 isosceles_base  apex given; find a base angle (both marked x)
  isosceles_apex  one base angle given; find the apex
3 exterior        a side is extended at any vertex; exterior = sum of the
                  two opposite interior angles
  isosceles_exterior  apex given; a side is extended at a base vertex
4 algebra         three algebraic angles
  algebra_isosceles   equal base expressions and an apex expression

The triangle is built from its real angles (so a 25 degree angle looks
sharp), then oriented by figures.choose_orientation. The caption still says
the diagram is not drawn accurately; answers never come from pixels.
"""
import math

from .core import Content, GeneratorInfo, LayoutHint, Question, make_context, require
from . import figures


INFO = GeneratorInfo(
    id="geometry.angles.triangle", version=2, topic="geometry", subtopic="angles",
    title="Angles in triangles",
    difficulty_descriptions={
        1: "Find a missing interior angle; the unknown can be at any vertex.",
        2: "Isosceles triangles: find a base angle or the apex angle.",
        3: "Exterior angles, including an isosceles triangle with a side extended.",
        4: "Form and solve an equation from algebraic angles, including isosceles triangles.",
    },
    tags=("geometry", "angles", "triangles"),
)

FORMS = {
    1: ("missing",),
    2: ("isosceles_base", "isosceles_apex"),
    3: ("exterior", "isosceles_exterior"),
    4: ("algebra", "algebra_isosceles"),
}
KEYS = {
    "missing": {"form", "angles", "unknown", "orientation"},
    "isosceles_base": {"form", "angles", "orientation"},
    "isosceles_apex": {"form", "angles", "orientation"},
    "exterior": {"form", "angles", "vertex", "extend_from", "orientation"},
    "isosceles_exterior": {"form", "angles", "vertex", "extend_from", "orientation"},
    "algebra": {"form", "terms", "orientation"},
    "algebra_isosceles": {"form", "terms", "orientation"},
}
KNOWN_ANGLES = tuple(range(30, 81, 5))
ISOSCELES = ("isosceles_base", "isosceles_apex", "isosceles_exterior", "algebra_isosceles")
EXTENSION = 0.45


# ------------------------------------------------------------ text helpers

def expression(coefficient, constant):
    if coefficient == 0:
        return str(constant)
    text = "x" if coefficient == 1 else str(coefficient) + "x"
    if constant:
        text += " + " + str(constant)
    return text


def angle_text(coefficient, constant):
    """(plain, tex) for an angle label."""
    text = expression(coefficient, constant)
    bracketed = "(" + text + ")" if coefficient and constant else text
    return bracketed + "°", bracketed + r"^{\circ}"


def value_text(value):
    return angle_text(0, value)


X_TEXT = angle_text(1, 0)


# ------------------------------------------------------------ mathematics

def interior(p, x):
    """The three interior angles at vertices 0, 1, 2."""
    if p["form"] in ("algebra", "algebra_isosceles"):
        return [k * x + b for k, b in p["terms"]]
    return list(p["angles"])


def solution(p):
    form = p["form"]
    if form == "missing":
        return p["angles"][p["unknown"]]
    if form == "isosceles_base":
        return p["angles"][0]
    if form == "isosceles_apex":
        return p["angles"][2]
    if form in ("exterior", "isosceles_exterior"):
        return 180 - p["angles"][p["vertex"]]
    total_k = sum(t[0] for t in p["terms"])
    total_b = sum(t[1] for t in p["terms"])
    require(total_k != 0 and (180 - total_b) % total_k == 0, "x must be a whole number")
    return (180 - total_b) // total_k


def check_structure(p, level):
    require(isinstance(p, dict) and p.get("form") in FORMS[level], "Form outside this level")
    form = p["form"]
    require(set(p) == KEYS[form], "Unexpected parameters")
    require(figures.valid_orientation(p["orientation"]), "Unknown orientation")
    if "angles" in p:
        require(isinstance(p["angles"], list) and len(p["angles"]) == 3
                and all(type(a) is int for a in p["angles"]), "Three integer angles")
    else:
        terms = p["terms"]
        require(isinstance(terms, list) and len(terms) == 3
                and all(isinstance(t, list) and len(t) == 2 and all(type(v) is int for v in t)
                        for t in terms), "Three integer coefficient pairs")
    x = solution(p)
    angles = interior(p, x)
    require(sum(angles) == 180 and all(20 <= a <= 130 for a in angles),
            "Interior angles do not form the intended triangle")
    if form in ISOSCELES:
        require(angles[0] == angles[1] != angles[2], "Isosceles, not equilateral")
    if form == "missing":
        require(p["unknown"] in (0, 1, 2), "Unknown vertex")
        known = [a for i, a in enumerate(angles) if i != p["unknown"]]
        require(all(a in KNOWN_ANGLES for a in known), "Known angle structure")
    elif form in ("isosceles_base", "isosceles_apex", "isosceles_exterior"):
        require(25 <= angles[0] <= 75, "Base angle bounds")
    if form in ("exterior", "isosceles_exterior"):
        k, j = p["vertex"], p["extend_from"]
        allowed = (0, 1) if form == "isosceles_exterior" else (0, 1, 2)
        require(k in allowed and j in (0, 1, 2) and j != k, "Extension structure")
        if form == "exterior":
            require(all(angles[i] in KNOWN_ANGLES for i in range(3) if i != k),
                    "Known angle structure")
    if form == "algebra":
        terms = p["terms"]
        require(12 <= x <= 28 and all(1 <= t[0] <= 3 for t in terms)
                and all(0 <= t[1] <= 20 for t in terms[:2]) and 0 <= terms[2][1] <= 40,
                "Algebraic structure outside bounds")
        require(len({t[0] for t in terms}) > 1 and any(t[1] for t in terms),
                "Expected varied coefficients and a constant")
    if form == "algebra_isosceles":
        base, apex = p["terms"][0], p["terms"][2]
        require(p["terms"][1] == base and base != apex, "Equal base expressions")
        require(8 <= x <= 30 and 1 <= base[0] <= 4 and 0 <= base[1] <= 30
                and 1 <= apex[0] <= 4 and 0 <= apex[1] <= 40, "Algebraic bounds")
    return x, angles


# ------------------------------------------------------------ construction

def build(level, rng):
    form = rng.choice(FORMS[level])
    if form == "missing":
        first, second = rng.choice(KNOWN_ANGLES), rng.choice(KNOWN_ANGLES)
        unknown = rng.randrange(3)
        known = iter((first, second))
        angles = [180 - first - second if i == unknown else next(known) for i in range(3)]
        return {"form": form, "angles": angles, "unknown": unknown}
    if form in ("isosceles_base", "isosceles_apex", "isosceles_exterior"):
        base = rng.choice([b for b in range(25, 76) if b != 60])
        p = {"form": form, "angles": [base, base, 180 - 2 * base]}
        if form == "isosceles_exterior":
            p["vertex"] = rng.choice((0, 1))
            p["extend_from"] = rng.choice([j for j in range(3) if j != p["vertex"]])
        return p
    if form == "exterior":
        first, second = rng.choice(KNOWN_ANGLES), rng.choice(KNOWN_ANGLES)
        vertex = rng.randrange(3)
        known = iter((first, second))
        angles = [180 - first - second if i == vertex else next(known) for i in range(3)]
        return {"form": form, "angles": angles, "vertex": vertex,
                "extend_from": rng.choice([j for j in range(3) if j != vertex])}
    if form == "algebra":
        x = rng.randint(12, 28)
        coefficients = [rng.randint(1, 3) for _ in range(3)]
        constants = [rng.randint(0, 20), rng.randint(0, 20)]
        constants.append(180 - sum(coefficients) * x - sum(constants))
        return {"form": form, "terms": [list(t) for t in zip(coefficients, constants)]}
    x, a, b, c = rng.randint(8, 30), rng.randint(1, 4), rng.randint(0, 30), rng.randint(1, 4)
    d = 180 - 2 * (a * x + b) - c * x
    return {"form": form, "terms": [[a, b], [a, b], [c, d]]}


# ------------------------------------------------------------ presentation

def figure_points(p, angles):
    a, b = math.radians(angles[0]), math.radians(angles[1])
    apex = math.sin(b) / math.sin(a + b)
    points = {0: (0.0, 0.0), 1: (1.0, 0.0), 2: (apex * math.cos(a), apex * math.sin(a))}
    if "vertex" in p:
        k, j = p["vertex"], p["extend_from"]
        direction = figures.unit(figures.minus(points[k], points[j]))
        points["E"] = (points[k][0] + EXTENSION * direction[0],
                       points[k][1] + EXTENSION * direction[1])
    return points


def vertex_labels(p, x):
    """{vertex: (plain, tex)} for interior labels; the exterior label is separate."""
    form = p["form"]
    angles = interior(p, x)
    if form == "missing":
        return {i: X_TEXT if i == p["unknown"] else value_text(angles[i]) for i in range(3)}
    if form == "isosceles_base":
        return {0: X_TEXT, 1: X_TEXT, 2: value_text(angles[2])}
    if form == "isosceles_apex":
        return {0: value_text(angles[0]), 2: X_TEXT}
    if form == "exterior":
        return {i: value_text(angles[i]) for i in range(3) if i != p["vertex"]}
    if form == "isosceles_exterior":
        return {2: value_text(angles[2])}
    return {i: angle_text(*p["terms"][i]) for i in range(3)}


def diagram(p, x):
    angles = interior(p, x)
    placed, height = figures.place(figure_points(p, angles), p["orientation"])
    corners = [placed[0], placed[1], placed[2]]
    nodes = [{"type": "polygon", "points": corners}]
    if p["form"] in ISOSCELES:
        nodes += [{"type": "ticks", "points": [corners[0], corners[2]], "count": 1},
                  {"type": "ticks", "points": [corners[1], corners[2]], "count": 1}]
    if "vertex" in p:
        nodes.append({"type": "line", "points": [corners[p["vertex"]], placed["E"]]})
    for i, (plain, tex) in sorted(vertex_labels(p, x).items()):
        others = [corners[j] for j in range(3) if j != i]
        nodes.append({"type": "label", "tex": tex,
                      "point": figures.angle_label(corners[i], others[0], others[1], len(plain))})
    if "vertex" in p:
        k, j = p["vertex"], p["extend_from"]
        other = [i for i in range(3) if i not in (j, k)][0]
        nodes.append({"type": "label", "tex": X_TEXT[1],
                      "point": figures.angle_label(corners[k], placed["E"], corners[other], 2)})
    return {"kind": "scene", "version": 1, "width": figures.CANVAS_WIDTH, "height": height,
            "caption": "Not drawn accurately", "nodes": nodes}


INSTRUCTIONS = {
    "missing": "Find the size of angle x.",
    "isosceles_base": "The triangle is isosceles; the marked sides are equal. Find the size of angle x.",
    "isosceles_apex": "The triangle is isosceles; the marked sides are equal. Find the size of angle x.",
    "exterior": "One side of the triangle has been extended in a straight line. Find the size of angle x.",
    "isosceles_exterior": ("The triangle is isosceles; the marked sides are equal. One side has been "
                           "extended in a straight line. Find the size of angle x."),
    "algebra": "The three angles of the triangle are given in degrees. Find the value of x.",
    "algebra_isosceles": ("The triangle is isosceles; the marked sides are equal. The angles are "
                          "given in degrees. Find the value of x."),
}


def prompt(p, x):
    instruction = INSTRUCTIONS[p["form"]]
    shown = [plain for _, (plain, _) in sorted(vertex_labels(p, x).items())]
    fallback = " Labelled interior angles: " + ", ".join(shown) + "."
    if "vertex" in p:
        fallback += " The exterior angle is x."
    return Content(instruction + fallback, display_text=instruction)


def answer_display(x):
    return Content("x = {}".format(x), "x = {}".format(x))


# ------------------------------------------------------------ generator

class TriangleAngles:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        for _ in range(500):
            p = build(difficulty, rng)
            p["orientation"] = [0, False]
            try:
                x, _ = check_structure(p, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a suitable triangle")
        p["orientation"] = figures.choose_orientation(
            rng, lambda orientation: diagram(dict(p, orientation=orientation), x))
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt(p, x),
            answer={"kind": "integer", "value": x}, answer_display=answer_display(x),
            worked_solution=(), marks=2 if difficulty <= 2 else 3,
            tags=self.info.tags, layout_hint=LayoutHint(working_lines=3 if difficulty <= 2 else 4),
            parameters=p, question_visuals=(diagram(p, x),),
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in FORMS, "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")
        require(isinstance(question.answer, dict)
                and question.answer.get("kind") == "integer", "Unexpected answer shape")
        x, _ = check_structure(question.parameters, level)
        require(question.answer == {"kind": "integer", "value": x}, "Incorrect answer")
        p = question.parameters
        require(question.prompt == prompt(p, x), "Prompt mismatch")
        require(question.visual_assets("questions") == (diagram(p, x),), "Diagram mismatch")
        require(not question.visual_assets("answers"), "Unexpected answer visuals")
        require(question.answer_display == answer_display(x), "Answer display mismatch")
        return True

    def validate_independently(self, question):
        """Solve the angle facts for this form with SymPy, not the generator's shortcut."""
        import sympy
        p = question.parameters
        x = sympy.Symbol("x")
        form = p["form"]
        if form == "missing":
            known = [a for i, a in enumerate(p["angles"]) if i != p["unknown"]]
            equation = sympy.Eq(sum(known) + x, 180)
        elif form == "isosceles_base":
            equation = sympy.Eq(2 * x + p["angles"][2], 180)
        elif form == "isosceles_apex":
            equation = sympy.Eq(2 * p["angles"][0] + x, 180)
        elif form == "exterior":
            known = [a for i, a in enumerate(p["angles"]) if i != p["vertex"]]
            equation = sympy.Eq(sum(known) + (180 - x), 180)
        elif form == "isosceles_exterior":
            equation = sympy.Eq(p["angles"][2] + 2 * (180 - x), 180)
        else:
            equation = sympy.Eq(sum(k * x + b for k, b in p["terms"]), 180)
        solutions = sympy.solve(equation, x)
        require(solutions == [question.answer["value"]], "Independent angle facts disagree")
        return True