"""Centre -> cyclic angle -> exterior angle -> outside triangle.

The diagram uses true points and line intersections. Level 3 finds an
angle; level 4 solves a linear expression for that angle. Existing circle
chains remain the simpler lead-in.
"""
import math
from fractions import Fraction

from .core import Content, LayoutHint, Question, rational_text, require
from . import circle_figures, figures

CONTEXT = "centre_cyclic_external"
SHARE = {3: 0.35, 4: 0.35}
NAME_SETS = ("ABCDP", "EFGHQ", "JKLMN", "PQRSX")
CENTRE = (155.0, 235.0)
RADIUS = 100.0
# orient_scene fits into the shared 360-point canvas.
WIDTH, HEIGHT = 360, 380
REASONS = (
    "the angle at the centre is twice the angle at the circumference",
    "opposite angles of a cyclic quadrilateral sum to 180 degrees",
    "angles on a straight line at B sum to 180 degrees",
    "angles on a straight line at C sum to 180 degrees",
    "angles in a triangle sum to 180 degrees",
)


def is_applied(q):
    return isinstance(q.parameters, dict) and q.parameters.get("context") == CONTEXT


def intersect(first, second, third, fourth):
    """Intersection and the two line parameters; reject parallel lines."""
    u = (second[0] - first[0], second[1] - first[1])
    v = (fourth[0] - third[0], fourth[1] - third[1])
    w = (third[0] - first[0], third[1] - first[1])
    cross = u[0] * v[1] - u[1] * v[0]
    require(abs(cross) > 1e-9, "Extended sides are parallel")
    t = (w[0] * v[1] - w[1] * v[0]) / cross
    z = (w[0] * u[1] - w[1] * u[0]) / cross
    return (first[0] + t * u[0], first[1] + t * u[1]), t, z


def points(p, centre=CENTRE, radius=RADIUS):
    """Build from the two given angles, without using the answer."""
    def on(degrees):
        a = math.radians(degrees)
        return (centre[0] + radius * math.cos(a),
                centre[1] + radius * math.sin(a))

    s, t, offset = p["centre_angle"], p["other_angle"], p["offset"]
    positions = (270 - s / 2, 90 + offset + 2 * t,
                 270 + s / 2, 90 + offset)
    a, b, c, d = (on(value) for value in positions)
    outside, along_ab, along_dc = intersect(a, b, d, c)
    require(along_ab > 1 and along_dc > 1,
            "P must lie beyond B on AB and beyond C on DC")
    require(math.hypot(outside[0] - centre[0], outside[1] - centre[1])
            < 2.7 * radius, "Outside triangle is too elongated")
    return dict(A=a, B=b, C=c, D=d, P=outside, O=centre)


def check(p, level):
    require(type(level) is int and level in (3, 4), "Wrong applied difficulty")
    require(isinstance(p, dict), "Expected parameters")
    require(set(p) == {"context", "centre_angle", "other_angle", "offset",
                       "names", "orientation", "coefficient", "constant"},
            "Unexpected parameters")
    require(p["context"] == CONTEXT and p["names"] in NAME_SETS,
            "Unknown context or letters")
    for key in ("centre_angle", "other_angle", "offset", "coefficient", "constant"):
        require(type(p[key]) is int, "Expected an integer parameter")
    s, t = p["centre_angle"], p["other_angle"]
    require(100 <= s <= 140 and s % 2 == 0, "Centre angle outside bounds")
    require(65 <= t <= 95 and -10 <= p["offset"] <= 10
            and p["offset"] % 5 == 0, "Other angle or free point outside bounds")
    require(figures.valid_orientation(p["orientation"]), "Invalid orientation")
    angle = Fraction(t) - Fraction(s, 2)
    require(25 <= angle <= 60, "Outside angle outside useful bounds")
    if level == 3:
        require(p["coefficient"] == 1 and p["constant"] == 0,
                "Numeric form must label the angle x")
    else:
        require(2 <= p["coefficient"] <= 5 and p["constant"] != 0
                and abs(p["constant"]) <= 60, "Wrong algebraic structure")
    value = (angle - p["constant"]) / p["coefficient"]
    require(value.denominator == 1 and 1 <= value <= 60,
            "x must be a positive whole number")
    points(p)
    return int(value), angle


def expression(p):
    k, b = p["coefficient"], p["constant"]
    text = "x" if k == 1 else str(k) + "x"
    if b:
        text += (" + " if b > 0 else " - ") + str(abs(b))
    return text


def diagram(p, level):
    pts = points(p)
    names = dict(zip("ABCDP", p["names"]), O="O")
    nodes = [
        {"type": "circle", "center": list(CENTRE), "radius": RADIUS},
        {"type": "circle", "center": list(CENTRE), "radius": 1.6, "shade": True},
    ]
    for first, second in (("A", "P"), ("D", "P"), ("B", "C"),
                          ("D", "A"), ("O", "A"), ("O", "C")):
        nodes.append(circle_figures.line(pts[first], pts[second]))
    for key in "ABCDP":
        nodes.append(circle_figures.vertex_label(
            pts[key], names[key], away_from=CENTRE, gap=28))
    nodes.append(circle_figures.vertex_label(
        pts["O"], "O", away_from=((pts["A"][0] + pts["C"][0]) / 2,
                                  (pts["A"][1] + pts["C"][1]) / 2), gap=18))
    # u keeps algebraic labels compact; its exact expression is in the prompt.
    labels = (("O", "A", "C", str(p["centre_angle"])),
              ("C", "B", "D", str(p["other_angle"])),
              ("P", "B", "C", "x" if level == 3 else "u"))
    for vertex, first, second, text in labels:
        marks = circle_figures.angle_mark(
            pts[vertex], pts[first], pts[second], text + r"^{\circ}", len(text))
        # The second given sits beside a radius inside its angle. Moving its
        # label farther along the established bisector clears that radius.
        if vertex == "C":
            label = marks[1]["point"]
            origin = pts[vertex]
            marks[1]["point"] = figures.rounded((
                origin[0] + 1.6 * (label[0] - origin[0]),
                origin[1] + 1.6 * (label[1] - origin[1])))
        nodes.extend(marks)
    scene = {"kind": "scene", "version": 1, "width": WIDTH, "height": HEIGHT,
             "caption": "Not drawn accurately", "nodes": nodes}
    return figures.orient_scene(scene, p["orientation"], max_height=320)


def prompt(p, level):
    a, b, c, d, outside = p["names"]
    lead = (
        "{a}, {b}, {c} and {d} lie on a circle with centre O. "
        "{a}{b} is extended beyond {b} and {d}{c} is extended beyond {c}; "
        "the extended sides meet at {outside}. "
    ).format(a=a, b=b, c=c, d=d, outside=outside)
    if level == 4:
        lead += "The marked angle u = {} degrees. ".format(expression(p))
    lead += "Find x, giving a reason for each step."
    fallback = (
        " Angle {a}O{c} = {s} degrees; angle {b}{c}{d} = {t} degrees; "
        "angle {b}{outside}{c} = {target} degrees."
    ).format(a=a, b=b, c=c, d=d, outside=outside,
             s=p["centre_angle"], t=p["other_angle"], target=expression(p))
    return Content(lead + fallback, display_text=lead)


def answer(p, level):
    value, angle = check(p, level)
    s = Fraction(p["centre_angle"])
    steps = [s / 2, 180 - s / 2, s / 2, 180 - p["other_angle"], angle]
    return {"kind": "integer", "value": value,
            "angle": rational_text(angle),
            "steps": [rational_text(v) for v in steps],
            "reasoning": list(REASONS)}


def display(p, level):
    value, _ = check(p, level)
    return Content("x = {}{}".format(value, " degrees" if level == 3 else ""))


def generate(generator, context):
    rng, level = context.rng, context.difficulty
    for _ in range(400):
        s, t = rng.randrange(100, 141, 2), rng.randint(65, 95)
        angle = t - s // 2
        coefficient = 1 if level == 3 else rng.randint(2, 5)
        constant = 0 if level == 3 else angle - coefficient * rng.randint(3, 20)
        p = dict(context=CONTEXT, centre_angle=s, other_angle=t,
                 offset=rng.choice((-10, -5, 0, 5, 10)),
                 coefficient=coefficient, constant=constant,
                 names=rng.choice(NAME_SETS), orientation=[0, False])
        try:
            check(p, level)
            p["orientation"] = circle_figures.choose_orientation(
                rng, lambda orientation: diagram(dict(p, orientation=orientation), level))
        except ValueError:
            continue
        break
    else:
        raise ValueError("Could not construct a clear external circle chain")
    info = generator.info
    q = Question(
        id=context.identity, generator_id=info.id, generator_version=info.version,
        topic=info.topic, subtopic=info.subtopic, difficulty=level,
        seed=context.seed, settings=context.settings, prompt=prompt(p, level),
        answer=answer(p, level), answer_display=display(p, level),
        worked_solution=(), marks=5 if level == 3 else 6, tags=info.tags,
        layout_hint=LayoutHint(working_lines=7), parameters=p,
        question_visuals=(diagram(p, level),))
    generator.validate(q)
    return q


def validate(generator, q):
    require(q.generator_id == generator.info.id
            and q.generator_version == generator.info.version, "Generator mismatch")
    require(q.settings == {}, "Unsupported settings")
    p, level = q.parameters, q.difficulty
    check(p, level)
    require(q.answer == answer(p, level), "Answer or reasoning mismatch")
    require(q.prompt == prompt(p, level), "Prompt mismatch")
    require(q.answer_display == display(p, level), "Display mismatch")
    require(q.visual_assets("questions") == (diagram(p, level),), "Diagram mismatch")
    require(not q.visual_assets("answers"), "Unexpected teacher diagram")
    require(q.marks == (5 if level == 3 else 6)
            and q.layout_hint.working_lines == 7, "Layout or marks mismatch")
    return True


def validate_independently(q):
    """Measure both givens and the outside angle on a unit-circle figure."""
    p = q.parameters
    pts = points(p, centre=(0.0, 0.0), radius=1.0)

    def measured(vertex, first, second):
        a, b, c = pts[vertex], pts[first], pts[second]
        u, v = (b[0] - a[0], b[1] - a[1]), (c[0] - a[0], c[1] - a[1])
        return math.degrees(math.atan2(abs(u[0] * v[1] - u[1] * v[0]),
                                       u[0] * v[0] + u[1] * v[1]))

    require(abs(measured("O", "A", "C") - p["centre_angle"]) < 1e-6,
            "Centre angle does not match the drawing")
    require(abs(measured("C", "B", "D") - p["other_angle"]) < 1e-6,
            "Second given does not match the drawing")
    value = q.answer.get("value")
    require(type(value) is int, "Expected integer x")
    require(abs(measured("P", "B", "C") -
                (p["coefficient"] * value + p["constant"])) < 1e-6,
            "Measured external angle disagrees with x")
    return True