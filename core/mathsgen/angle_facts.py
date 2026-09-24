"""Angle facts: straight lines, points, vertically opposite angles and quadrilaterals.

Every diagram is true geometry: rays are drawn at their real directions, and a
quadrilateral is built by intersecting a ray from B with a ray from D, so its
fourth angle comes out as 360 minus the other three. Algebraic forms pick x
first and build linear expressions c x + k that hit the required total.
"""
import math

from . import figures
from .core import Content, GeneratorInfo, LayoutHint, Question, make_context, require
from .vector_geometry import renders_cleanly


INFO = GeneratorInfo(
    id="geometry.angles.basic_facts", version=1,
    topic="geometry", subtopic="angle_facts",
    title="Angle facts: lines, points, opposite angles and quadrilaterals",
    difficulty_descriptions={
        1: "Find a missing angle on a straight line or around a point.",
        2: "Use vertically opposite angles, or find the fourth angle of a quadrilateral.",
        3: "Form and solve an equation from algebraic angles on a line or around a point.",
        4: "Solve for x in a quadrilateral with algebraic angles, then find the largest angle.",
    },
    tags=("geometry", "angles", "angle facts"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("straight_line", "around_point"),
    2: ("vertically_opposite", "quadrilateral"),
    3: ("algebraic_line", "algebraic_point"),
    4: ("algebraic_quad", "algebraic_quad_largest"),
}
TOTALS = {"straight_line": 180, "around_point": 360, "quadrilateral": 360,
          "algebraic_line": 180, "algebraic_point": 360,
          "algebraic_quad": 360, "algebraic_quad_largest": 360}
MIN_ANGLE, MAX_ANGLE = 35, 165
MARKS = {1: 1, 2: 2, 3: 3, 4: 4}
WORKING_LINES = {1: 2, 2: 3, 3: 5, 4: 6}
QUAD_SIDE = 0.9       # drawing only: AD relative to AB

KEYS = {
    "straight_line": {"angles", "unknown"},
    "around_point": {"angles", "unknown"},
    "vertically_opposite": {"angle", "turn"},
    "quadrilateral": {"angles", "unknown"},
    "algebraic_line": {"x", "terms"},
    "algebraic_point": {"x", "terms"},
    "algebraic_quad": {"x", "terms"},
    "algebraic_quad_largest": {"x", "terms"},
}
ALGEBRAIC = ("algebraic_line", "algebraic_point", "algebraic_quad", "algebraic_quad_largest")


# ------------------------------------------------------------ expressions

def expression_text(term):
    c, k = term
    head = "x" if c == 1 else "{}x".format(c)
    if k == 0:
        return head
    return "{} {} {}".format(head, "+" if k > 0 else "-", abs(k))


def angle_label_text(term):
    text = expression_text(term)
    return text + "°" if term[1] == 0 else "(" + text + ")°"


def values(par):
    if par["form"] in ALGEBRAIC:
        return [c * par["x"] + k for c, k in par["terms"]]
    if par["form"] == "vertically_opposite":
        a = par["angle"]
        return [a, 180 - a, a, 180 - a]
    return list(par["angles"])


# ------------------------------------------------------------ drawings

def label(point, text):
    return {"type": "label", "point": figures.rounded(point), "text": text}


def line(first, second):
    return {"type": "line", "points": [figures.rounded(first), figures.rounded(second)]}


def ray_scene(directions, texts):
    """Rays from O at the given directions (degrees); texts[i] labels the gap from
    ray i to ray i + 1 (None for no label)."""
    raw = {"O": (0.0, 0.0)}
    for i, d in enumerate(directions):
        raw["R%d" % i] = (math.cos(math.radians(d)), math.sin(math.radians(d)))
    placed, height = figures.place(raw, [0, False])
    centre = placed["O"]
    nodes = [line(centre, placed["R%d" % i]) for i in range(len(directions))]
    for i, text in enumerate(texts):
        if text:
            first, second = placed["R%d" % i], placed["R%d" % ((i + 1) % len(directions))]
            nodes.append({"type": "label", "text": text,
                          "point": figures.angle_label(centre, first, second, len(text))})
    return {"kind": "scene", "version": 1, "width": 360, "height": height,
            "caption": "", "nodes": nodes}


def quad_points(angles):
    a, b, c, d = angles
    A, B = (0.0, 0.0), (1.0, 0.0)
    D = (QUAD_SIDE * math.cos(math.radians(a)), QUAD_SIDE * math.sin(math.radians(a)))
    u = (math.cos(math.radians(180 - b)), math.sin(math.radians(180 - b)))
    v = (math.cos(math.radians(a - 180 + d)), math.sin(math.radians(a - 180 + d)))
    det = u[0] * (-v[1]) - u[1] * (-v[0])
    require(abs(det) > 1e-9, "Sides are parallel")
    rhs = (D[0] - B[0], D[1] - B[1])
    t = (rhs[0] * (-v[1]) - rhs[1] * (-v[0])) / det
    s = (u[0] * rhs[1] - u[1] * rhs[0]) / det
    require(t > 0.2 and s > 0.2, "Quadrilateral does not close sensibly")
    C = (B[0] + t * u[0], B[1] + t * u[1])
    return {"A": A, "B": B, "C": C, "D": D}


def quad_scene(angles, texts):
    placed, height = figures.place(quad_points(angles), [0, False])
    order = ["A", "B", "C", "D"]
    nodes = [{"type": "polygon", "points": [placed[v] for v in order]}]
    for i, v in enumerate(order):
        if texts[i]:
            prev, nxt = placed[order[i - 1]], placed[order[(i + 1) % 4]]
            nodes.append({"type": "label", "text": texts[i],
                          "point": figures.angle_label(placed[v], prev, nxt, len(texts[i]))})
    return {"kind": "scene", "version": 1, "width": 360, "height": height,
            "caption": "", "nodes": nodes}


def visual_for(par):
    form = par["form"]
    vals = values(par)
    if form == "vertically_opposite":
        base = par["turn"]
        directions = [base, base + vals[0], base + 180, base + 180 + vals[0]]
        return ray_scene(directions, ["{}°".format(vals[0]), "y", "x", None])
    if form in ("quadrilateral",):
        texts = ["{}°".format(v) if i != par["unknown"] else "x" for i, v in enumerate(vals)]
        return quad_scene(vals, texts)
    if form in ("algebraic_quad", "algebraic_quad_largest"):
        return quad_scene(vals, [angle_label_text(t) for t in par["terms"]])
    if form in ("algebraic_line", "algebraic_point"):
        texts = [angle_label_text(t) for t in par["terms"]]
    else:
        texts = ["{}°".format(v) if i != par["unknown"] else "x" for i, v in enumerate(vals)]
    directions, total = [], 0
    for v in vals:
        directions.append(total)
        total += v
    if form in ("straight_line", "algebraic_line"):
        directions.append(180)
        texts = texts + [None]
    return ray_scene(directions, texts)


# ------------------------------------------------------------ checks

def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    form = par.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(par) == KEYS[form] | {"form"}, "Unexpected parameters")
    if form == "vertically_opposite":
        require(type(par["angle"]) is int and 40 <= par["angle"] <= 140 and par["angle"] != 90,
                "Angle outside bounds")
        require(par["turn"] in range(0, 180, 15), "Unexpected orientation")
    elif form in ALGEBRAIC:
        require(type(par["x"]) is int and 5 <= par["x"] <= 40, "x outside bounds")
        terms = par["terms"]
        size = 2 if form == "algebraic_line" else (3 if form == "algebraic_point" else 4)
        require(isinstance(terms, list) and len(terms) == size
                and all(isinstance(t, list) and len(t) == 2 and all(type(v) is int for v in t)
                        and t[0] in (1, 2, 3, 4) and -40 <= t[1] <= 60 for t in terms),
                "Unexpected expressions")
        require(len({tuple(t) for t in terms}) == size, "Expressions must differ")
    else:
        angles = par["angles"]
        size = {"straight_line": 2, "around_point": 3, "quadrilateral": 4}[form]
        require(isinstance(angles, list) and len(angles) == size
                and all(type(a) is int for a in angles), "Unexpected angles")
        require(par["unknown"] in range(size), "Unknown angle out of range")
    vals = values(par)
    require(sum(vals) == TOTALS.get(form, 360), "Angles must total correctly")
    require(all(MIN_ANGLE <= v <= MAX_ANGLE for v in vals), "Angle outside drawable bounds")
    if form == "algebraic_quad_largest":
        require(sorted(vals)[-1] > sorted(vals)[-2], "Largest angle must be unique")
    require(renders_cleanly(visual_for(par)), "Diagram does not render cleanly")


# ------------------------------------------------------------ wording and answers

def prompt_for(par):
    form = par["form"]
    vals = values(par)
    if form == "straight_line":
        known = [v for i, v in enumerate(vals) if i != par["unknown"]]
        text = ("The diagram shows angles on a straight line. One angle is {}°. Work out the "
                "size of the angle marked x.".format(known[0]))
    elif form == "around_point":
        known = [str(v) + "°" for i, v in enumerate(vals) if i != par["unknown"]]
        text = ("The diagram shows angles around a point: {}. Work out the size of the angle "
                "marked x.".format(" and ".join(known)))
    elif form == "vertically_opposite":
        text = ("Two straight lines cross. One of the angles is {}°. Work out the sizes of the "
                "angles marked x and y. Give a reason for each answer.".format(vals[0]))
    elif form == "quadrilateral":
        known = [str(v) + "°" for i, v in enumerate(vals) if i != par["unknown"]]
        text = ("Three angles of a quadrilateral are {}. Work out the size of the angle marked "
                "x.".format(", ".join(known)))
    else:
        exprs = ", ".join(angle_label_text(t) for t in par["terms"])
        place = {"algebraic_line": "on a straight line", "algebraic_point": "around a point"}.get(
            form, "in a quadrilateral")
        text = "The angles {} are {}. Work out the value of x.".format(exprs, place)
        if form == "algebraic_quad_largest":
            text = text[:-1] + ", then the size of the largest angle."
    return Content(text)


def answer_for(par):
    form = par["form"]
    vals = values(par)
    if form == "vertically_opposite":
        return ({"kind": "angles", "x": str(vals[0]), "y": str(vals[1])},
                Content("x = {}° (vertically opposite angles are equal); y = {}° (angles on a "
                        "straight line add up to 180°)".format(vals[0], vals[1])))
    if form in ALGEBRAIC:
        answer = {"kind": "solve", "x": str(par["x"])}
        text = "x = {}".format(par["x"])
        if form == "algebraic_quad_largest":
            answer["largest"] = str(max(vals))
            text += "; largest angle = {}°".format(max(vals))
        return answer, Content(text)
    value = vals[par["unknown"]]
    return {"kind": "angle", "value": str(value)}, Content("x = {}°".format(value))


def draw_parameters(rng, form):
    par = {"form": form}
    if form == "vertically_opposite":
        par.update(angle=rng.randint(40, 140), turn=rng.randrange(0, 180, 15))
        return par
    total = TOTALS[form]
    size = {"straight_line": 2, "around_point": 3, "quadrilateral": 4,
            "algebraic_line": 2, "algebraic_point": 3}.get(form, 4)
    if form in ALGEBRAIC:
        x = rng.randint(5, 40)
        terms = [[rng.randint(1, 4), rng.randrange(-40, 61, 5)] for _ in range(size - 1)]
        used = sum(c * x + k for c, k in terms)
        c = rng.randint(1, 4)
        terms.append([c, total - used - c * x])
        par.update(x=x, terms=terms)
        return par
    angles = [rng.randint(MIN_ANGLE, MAX_ANGLE) for _ in range(size - 1)]
    angles.append(total - sum(angles))
    par.update(angles=angles, unknown=rng.randrange(size))
    return par


# ------------------------------------------------------------ generator

class AngleFacts:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        form = rng.choice(FORMS[difficulty])
        for attempt in range(5000):
            par = draw_parameters(rng, form)
            try:
                check_parameters(par, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct an angle facts question")
        answer, display = answer_for(par)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(par),
            answer=answer, answer_display=display, worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=WORKING_LINES[difficulty]),
            parameters=par, question_visuals=(visual_for(par),),
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        require(type(q.difficulty) is int and q.difficulty in (1, 2, 3, 4), "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        check_parameters(q.parameters, q.difficulty)
        answer, display = answer_for(q.parameters)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Answer display mismatch")
        require(q.prompt == prompt_for(q.parameters), "Prompt mismatch")
        require(q.visual_assets("questions") == (visual_for(q.parameters),), "Diagram mismatch")
        return True

    def validate_independently(self, q):
        """Measure angles from the drawing with atan2; solve algebraic totals directly."""
        par, answer = q.parameters, q.answer
        form = par["form"]
        if form in ALGEBRAIC:
            total = TOTALS[form]
            coefficient = sum(c for c, _ in par["terms"])
            constant = sum(k for _, k in par["terms"])
            require((total - constant) % coefficient == 0
                    and int(answer["x"]) == (total - constant) // coefficient,
                    "Independent solution for x disagrees")
            if form == "algebraic_quad_largest":
                x = int(answer["x"])
                require(int(answer["largest"]) == max(c * x + k for c, k in par["terms"]),
                        "Largest angle disagrees")
            return True
        nodes = q.visual_assets("questions")[0]["nodes"]

        def turn(vertex, first, second):
            a = math.atan2(first[1] - vertex[1], first[0] - vertex[0])
            b = math.atan2(second[1] - vertex[1], second[0] - vertex[0])
            return math.degrees(abs(a - b)) % 360

        if form == "quadrilateral":
            corners = next(n for n in nodes if n["type"] == "polygon")["points"]
            i = par["unknown"]
            measured = turn(corners[i], corners[i - 1], corners[(i + 1) % 4])
            measured = min(measured, 360 - measured)
            require(abs(measured - int(answer["value"])) < 0.5, "Measured angle disagrees")
            return True
        rays = [n["points"] for n in nodes if n["type"] == "line"]
        centre = rays[0][0]
        ends = [r[1] for r in rays]
        if form == "vertically_opposite":
            gap_x = turn(centre, ends[2], ends[3]) % 360
            gap_y = turn(centre, ends[1], ends[2]) % 360
            gap_x, gap_y = min(gap_x, 360 - gap_x), min(gap_y, 360 - gap_y)
            require(abs(gap_x - int(answer["x"])) < 0.5 and abs(gap_y - int(answer["y"])) < 0.5,
                    "Measured angles disagree")
            return True
        i = par["unknown"]
        measured = turn(centre, ends[i], ends[(i + 1) % len(ends)])
        measured = min(measured, 360 - measured)
        require(abs(measured - int(answer["value"])) < 0.5, "Measured angle disagrees")
        return True