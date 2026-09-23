"""Multi-step circle problems: theorems chained on true figures.

A single-theorem question is a Foundation exercise; Higher papers chain.
Each chain here is built from one given angle s (or, for the algebra chain,
from the expression u), drawn at its true size, and records every
intermediate angle and the reason for it, so a mark scheme can follow the
intended route. The answer is always the last step.

Chains by level (two per level):
  1  centre_then_cyclic          AOC -> ADC = s/2 -> ABC = 180 - s/2
     semicircle_then_triangle    AB diameter: ACB = 90 -> CBA = 90 - s
  2  tangent_then_isosceles      TAC -> OAC = 90 - s -> AOC = 2s
     kite_then_circumference     APB -> AOB = 180 - s -> ACB = 90 - s/2
  3  semicircle_then_same_segment ACB = 90 -> ABC = 90 - s -> ADC = ABC
     alternate_then_centre       BAT -> ACB = s -> AOB = 2s -> OAB = 90 - s
  4  kite_then_reflex            APB -> AOB -> reflex AOB -> ADB = 90 + s/2
     algebra_centre_cyclic       AOC = u, ABC = v; 180 - u/2 = v
Points the given angle leaves free (B and D on their arcs, C on the major
arc, D on the minor arc) are seeded, stored in "free" and bounded in
validation. Letters and orientation are seeded too.
"""
import math
from fractions import Fraction

from . import circle_figures, figures
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)


INFO = GeneratorInfo(
    id="geometry.circle_theorems.multi_step", version=2,
    topic="geometry", subtopic="circle_theorems",
    title="Circle theorems: multi-step problems",
    difficulty_descriptions={
        1: "Chain two theorems: centre then cyclic, or semicircle then triangle.",
        2: "Chain a tangent fact into an isosceles triangle or the centre theorem.",
        3: "Chain three steps through a semicircle or the alternate segment.",
        4: "Chain three steps from two tangents, or solve an algebraic chain.",
    },
    tags=("geometry", "circle_theorems", "angles", "multi_step", "reasoning"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("centre_then_cyclic", "semicircle_then_triangle"),
    2: ("tangent_then_isosceles", "kite_then_circumference"),
    3: ("semicircle_then_same_segment", "alternate_then_centre"),
    4: ("kite_then_reflex", "algebra_centre_cyclic"),
}
REASONING = {
    "centre_then_cyclic": (
        "the angle at the centre is twice the angle at the circumference",
        "opposite angles of a cyclic quadrilateral sum to 180",
    ),
    "semicircle_then_triangle": (
        "the angle in a semicircle is 90",
        "angles in a triangle sum to 180",
    ),
    "tangent_then_isosceles": (
        "a tangent meets a radius at 90",
        "two radii make an isosceles triangle, whose angles sum to 180",
    ),
    "kite_then_circumference": (
        "tangents meet radii at 90, so the other two angles of the kite sum to 180",
        "the angle at the centre is twice the angle at the circumference",
    ),
    "semicircle_then_same_segment": (
        "the angle in a semicircle is 90",
        "angles in a triangle sum to 180",
        "angles in the same segment are equal",
    ),
    "alternate_then_centre": (
        "the tangent-chord angle equals the angle in the alternate segment",
        "the angle at the centre is twice the angle at the circumference",
        "two radii make an isosceles triangle, whose angles sum to 180",
    ),
    "kite_then_reflex": (
        "tangents meet radii at 90, so the other two angles of the kite sum to 180",
        "angles around a point sum to 360",
        "the angle at the centre is twice the angle at the circumference",
    ),
    "algebra_centre_cyclic": (
        "the angle at the centre is twice the angle at the circumference",
        "opposite angles of a cyclic quadrilateral sum to 180",
    ),
}
# Letters in role order A, B, C, D, P, T, S; O is always the centre.
NAME_SETS = ("ABCDPTS", "EFGHQUV", "KLMNRWZ", "JKLMNPQ", "PQRSXTU")
MARKS = {1: 3, 2: 3, 3: 4, 4: 4}
TANGENT_REACH = 110
LEAST_SEPARATION = 6   # numeric answers stay this far from the given angle


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


def chain_steps(chain, s):
    """Every intermediate angle, in the order a student writes them."""
    s = Fraction(s)
    if chain in ("centre_then_cyclic", "algebra_centre_cyclic"):
        return [s / 2, 180 - s / 2]
    if chain == "semicircle_then_triangle":
        return [Fraction(90), 90 - s]
    if chain == "tangent_then_isosceles":
        return [90 - s, 2 * s]
    if chain == "kite_then_circumference":
        return [180 - s, 90 - s / 2]
    if chain == "semicircle_then_same_segment":
        return [Fraction(90), 90 - s, 90 - s]
    if chain == "alternate_then_centre":
        return [s, 2 * s, 90 - s]
    return [180 - s, 180 + s, 90 + s / 2]


def solve(p):
    if p["chain"] == "algebra_centre_cyclic":
        (k, b), (one, c) = p["u"], p["v"]
        return Fraction(360 - b - 2 * c, k + 2 * one)
    return chain_steps(p["chain"], p["start"])[-1]


def given_size(p, x):
    if p["chain"] == "algebra_centre_cyclic":
        return value_of(p["u"], x)
    return p["start"]


def floor5(value):
    return max(0, int(value) // 5 * 5)


def free_limits(chain, s):
    """How far each free point may move from its default, in degrees."""
    s = float(s)
    if chain in ("centre_then_cyclic", "algebra_centre_cyclic"):
        return [floor5(s / 2 - 25), floor5(180 - s / 2 - 30)]
    if chain == "semicircle_then_same_segment":
        return [55]
    if chain in ("kite_then_circumference", "kite_then_reflex"):
        t = (180 - s) / 2
        if chain == "kite_then_circumference":
            return [floor5(180 - t - 35)]
        return [floor5(t - 18)]
    return []


START_RANGES = {
    "centre_then_cyclic": (100, 160, 2),
    "semicircle_then_triangle": (25, 65, 1),
    "tangent_then_isosceles": (35, 65, 1),
    "kite_then_circumference": (60, 110, 2),
    "semicircle_then_same_segment": (25, 65, 1),
    "alternate_then_centre": (30, 60, 1),
    "kite_then_reflex": (50, 100, 2),
}


def check_parameters(p, level):
    """Check structure, ranges and free points; return (x, steps)."""
    require(isinstance(p, dict), "Parameters must be a dictionary")
    chain = p.get("chain")
    require(chain in FORMS[level], "Chain does not match difficulty")
    algebra = chain == "algebra_centre_cyclic"
    require(set(p) == {"chain", "names", "orientation", "free"}
            | ({"u", "v"} if algebra else {"start"}), "Unexpected parameters")
    require(p["names"] in NAME_SETS, "Invalid letters")
    require(figures.valid_orientation(p["orientation"]), "Invalid orientation")
    if algebra:
        for key in ("u", "v"):
            term = p[key]
            require(isinstance(term, list) and len(term) == 2
                    and all(type(v) is int for v in term), "Invalid angle expression")
        x = solve(p)
        require(x.denominator == 1, "x must be a whole number")
        x = int(x)
        s = value_of(p["u"], x)
        require(2 <= p["u"][0] <= 4 and p["v"][0] == 1 and p["v"][1] != 0
                and 10 <= x <= 30, "Wrong algebraic structure")
        require(100 <= s <= 160 and s % 2 == 0, "Centre angle outside bounds")
        steps = chain_steps(chain, s)
        require(steps[-1] == value_of(p["v"], x), "The labels disagree with the chain")
    else:
        s = p["start"]
        low, high, step = START_RANGES[chain]
        require(type(s) is int and low <= s <= high and (s - low) % step == 0,
                "Given angle outside bounds")
        steps = chain_steps(chain, s)
        x = steps[-1]
        require(x.denominator == 1, "Chain should give a whole angle")
        x = int(x)
        require(abs(x - s) >= LEAST_SEPARATION,
                "The answer must not be close to the angle already given")
    for value in steps:
        require(0 < value < 360, "A step produces an impossible angle")
    require(0 < x < 180, "Answer must be an ordinary angle")
    limits = free_limits(chain, s)
    free = p["free"]
    require(isinstance(free, list) and len(free) == len(limits)
            and all(type(v) is int and v % 5 == 0 and abs(v) <= limit
                    for v, limit in zip(free, limits)), "Invalid free positions")
    return x, steps


# ------------------------------------------------------------ figures

def midpoint(first, second):
    return ((first[0] + second[0]) / 2, (first[1] + second[1]) / 2)


def figure(p, x, on=circle_figures.on_circle, centre=circle_figures.CENTRE,
           radius=circle_figures.RADIUS, reach=TANGENT_REACH):
    """True points and drawing instructions for the chain."""
    chain, free = p["chain"], p["free"]
    s = float(given_size(p, x))
    pts = {"O": tuple(centre)}
    fig = {"segments": [], "letters": [], "ends": [], "right": []}
    if chain in ("centre_then_cyclic", "algebra_centre_cyclic"):
        pts.update(A=on(270 - s / 2), C=on(270 + s / 2),
                   B=on(270 + free[0]), D=on(90 + free[1]))
        fig["segments"] = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
                           ("O", "A"), ("O", "C")]
        fig["letters"] = ["A", "B", "C", "D"]
        fig.update(given=("O", "A", "C"), answer=("B", "A", "C"),
                   away=midpoint(pts["A"], pts["C"]))
    elif chain in ("semicircle_then_triangle", "semicircle_then_same_segment"):
        pts.update(A=on(180), B=on(0), C=on(360 - 2 * s))
        fig["segments"] = [("A", "B"), ("A", "C"), ("B", "C")]
        fig["letters"] = ["A", "B", "C"]
        fig.update(given=("A", "C", "B"), away=pts["C"])
        if chain == "semicircle_then_triangle":
            fig["answer"] = ("B", "C", "A")
        else:
            pts["D"] = on(90 + free[0])
            fig["segments"] += [("D", "A"), ("D", "C")]
            fig["letters"].append("D")
            fig["answer"] = ("D", "A", "C")
    elif chain in ("tangent_then_isosceles", "alternate_then_centre"):
        a = on(90)
        pts.update(A=a, T=(a[0] - reach, a[1]), S=(a[0] + reach, a[1]))
        fig["ends"] = ["T", "S"]
        if chain == "tangent_then_isosceles":
            pts["C"] = on(90 + 2 * s)
            fig["segments"] = [("T", "S"), ("A", "C"), ("O", "A"), ("O", "C")]
            fig["letters"] = ["A", "C"]
            fig.update(given=("A", "T", "C"), answer=("O", "A", "C"),
                       away=midpoint(pts["A"], pts["C"]))
        else:
            pts.update(B=on(90 + 2 * s), C=on(270 + s))
            fig["segments"] = [("T", "S"), ("A", "B"), ("A", "C"), ("B", "C"),
                               ("O", "A"), ("O", "B")]
            fig["letters"] = ["A", "B", "C"]
            fig.update(given=("A", "T", "B"), answer=("A", "O", "B"),
                       away=midpoint(pts["A"], pts["B"]))
    else:
        t = (180 - s) / 2
        pts.update(A=on(t), B=on(-t),
                   P=(centre[0] + radius / math.cos(math.radians(t)), centre[1]))
        fig["segments"] = [("P", "A"), ("P", "B"), ("O", "A"), ("O", "B")]
        fig["letters"] = ["A", "B", "P"]
        fig["right"] = ["A", "B"]
        fig.update(given=("P", "A", "B"), away=pts["P"])
        if chain == "kite_then_circumference":
            pts["C"] = on(180 + free[0])
            fig["segments"] += [("C", "A"), ("C", "B")]
            fig["letters"].append("C")
            fig["answer"] = ("C", "A", "B")
        else:
            pts["D"] = on(free[0])
            fig["segments"] += [("D", "A"), ("D", "B")]
            fig["letters"].append("D")
            fig["answer"] = ("D", "A", "B")
    return fig, pts


# ------------------------------------------------------------ presentation

def letters(p):
    return dict(zip("ABCDPTS", p["names"]), O="O")


def angle_name(names, corner):
    vertex, first, second = corner
    return "angle " + names[first] + names[vertex] + names[second]


def mark_texts(p):
    if p["chain"] == "algebra_centre_cyclic":
        return "u", "v"
    return str(p["start"]), "x"


def diagram_for(p, x):
    fig, pts = figure(p, x)
    names = letters(p)
    nodes = circle_figures.circle_nodes()
    for first, second in fig["segments"]:
        nodes.append(circle_figures.line(pts[first], pts[second]))
    for vertex in fig["right"]:
        nodes.append({"type": "right_angle", "vertex": figures.rounded(pts[vertex]),
                      "first": figures.rounded(pts["O"]),
                      "second": figures.rounded(pts["P"])})
    for key in fig["letters"]:
        nodes.append(circle_figures.vertex_label(pts[key], names[key]))
    for key in fig["ends"]:
        nodes.append(circle_figures.vertex_label(pts[key], names[key],
                                                 away_from=pts["A"], gap=18))
    nodes.append(circle_figures.vertex_label(pts["O"], "O", away_from=fig["away"],
                                             gap=circle_figures.CENTRE_GAP))
    given_text, answer_text = mark_texts(p)
    for corner, text in ((fig["given"], given_text), (fig["answer"], answer_text)):
        vertex, first, second = corner
        nodes += circle_figures.angle_mark(pts[vertex], pts[first], pts[second],
                                           text + r"^{\circ}", len(text))
    scene = {
        "kind": "scene", "version": 1, "width": 360, "height": 300,
        "caption": "Not drawn accurately", "nodes": nodes,
    }
    return figures.orient_scene(scene, p["orientation"])


def presentation(p):
    chain = p["chain"]
    names = letters(p)
    if chain in ("centre_then_cyclic", "algebra_centre_cyclic"):
        lead = "{A}, {B}, {C} and {D} lie on the circle with centre O."
    elif chain == "semicircle_then_triangle":
        lead = "{A}{B} is a diameter of the circle with centre O. {C} lies on the circle."
    elif chain == "semicircle_then_same_segment":
        lead = ("{A}{B} is a diameter of the circle with centre O. {C} and {D} lie "
                "on the circle.")
    elif chain == "tangent_then_isosceles":
        lead = ("{T}{S} is a tangent to the circle at {A}. O is the centre and {C} "
                "lies on the circle.")
    elif chain == "alternate_then_centre":
        lead = ("{T}{S} is a tangent to the circle at {A}. O is the centre, and {B} "
                "and {C} lie on the circle.")
    elif chain == "kite_then_circumference":
        lead = ("{P}{A} and {P}{B} are tangents to the circle with centre O. {C} "
                "lies on the major arc {A}{B}.")
    else:
        lead = ("{P}{A} and {P}{B} are tangents to the circle with centre O. {D} "
                "lies on the minor arc {A}{B}.")
    lead = lead.format(**names)
    if chain == "algebra_centre_cyclic":
        lead += " In the diagram, u = {} and v = {}, in degrees.".format(
            expression(p["u"]), expression(p["v"]))
    lead += " Find x, showing each step of your reasoning."
    fig, _ = figure(p, int(solve(p)))
    given_text, answer_text = mark_texts(p)
    if chain == "algebra_centre_cyclic":
        given_text, answer_text = expression(p["u"]), expression(p["v"])
    fallback = " Marked: {} is {} degrees; {} is {} degrees.".format(
        angle_name(names, fig["given"]), given_text,
        angle_name(names, fig["answer"]), answer_text)
    return Content(lead + fallback, display_text=lead)


def display(value, chain):
    if chain == "algebra_centre_cyclic":
        return Content("x = " + str(value))
    return Content("x = {} degrees".format(value), str(value) + r"^{\circ}")


def answer_for(p, x, steps):
    return {
        "kind": "integer", "value": x,
        "steps": [str(v) for v in steps],
        "reasoning": list(REASONING[p["chain"]]),
    }


def draw(rng, level):
    chain = rng.choice(FORMS[level])
    p = {"chain": chain, "names": rng.choice(NAME_SETS), "orientation": [0, False]}
    if chain == "algebra_centre_cyclic":
        s = rng.randrange(100, 161, 2)
        x, k = rng.randint(10, 30), rng.randint(2, 4)
        p["u"] = [k, s - k * x]
        p["v"] = [1, int(180 - Fraction(s, 2)) - x]
    else:
        low, high, step = START_RANGES[chain]
        s = rng.randrange(low, high + 1, step)
        p["start"] = s
    p["free"] = [rng.randrange(-limit, limit + 1, 5) if limit else 0
                 for limit in free_limits(chain, s)]
    return p


# ------------------------------------------------------------ generator

class MultiStepCircles:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        for attempt in range(400):
            p = draw(rng, difficulty)
            try:
                x, steps = check_parameters(p, difficulty)
                p["orientation"] = circle_figures.choose_orientation(
                    rng, lambda orientation: diagram_for(dict(p, orientation=orientation), x))
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a multi-step circle question")
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=presentation(p),
            answer=answer_for(p, x, steps),
            answer_display=display(x, p["chain"]), worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=5),
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
        p = q.parameters
        x, steps = check_parameters(p, level)
        require(q.answer == answer_for(p, x, steps), "Answer, steps or reasoning mismatch")
        require(q.prompt == presentation(p), "Prompt mismatch")
        require(q.answer_display == display(x, p["chain"]), "Answer display mismatch")
        require(q.visual_assets("questions") == (diagram_for(p, x),), "Diagram mismatch")
        require(not q.visual_assets("answers"), "Unexpected answer visuals")
        return True

    def validate_independently(self, q):
        """Build the figure from the given angle alone and measure the answer with atan2."""
        p, x = q.parameters, q.answer.get("value")
        require(type(x) is int, "Expected a whole-number answer")

        def unit_circle(degrees):
            angle = math.radians(degrees)
            return (math.cos(angle), math.sin(angle))

        fig, pts = figure(p, x, on=unit_circle, centre=(0.0, 0.0), radius=1.0, reach=1.0)

        def measured(corner):
            vertex, first, second = (pts[key] for key in corner)
            u = (first[0] - vertex[0], first[1] - vertex[1])
            v = (second[0] - vertex[0], second[1] - vertex[1])
            return math.degrees(math.atan2(abs(u[0] * v[1] - u[1] * v[0]),
                                           u[0] * v[0] + u[1] * v[1]))

        require(abs(measured(fig["given"]) - float(given_size(p, x))) < 1e-6,
                "The figure does not show the given angle")
        expected = value_of(p["v"], x) if p["chain"] == "algebra_centre_cyclic" else x
        require(abs(measured(fig["answer"]) - expected) < 1e-6,
                "Measured answer angle disagrees")
        return True