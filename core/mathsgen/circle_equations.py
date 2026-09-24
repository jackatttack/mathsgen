"""Circles centred at the origin: equations, points and tangents.

Points on circles come from integer lattice points (a, b), so r^2 = a^2 + b^2
and every tangent, intercept and area is an exact fraction. The tangent at
P(a, b) is a x + b y = r^2, perpendicular to the radius OP.
"""
import math
from fractions import Fraction

from . import rich_blocks as rb
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_tex, rational_text, require,
)


INFO = GeneratorInfo(
    id="algebra.graphs.circle_equations", version=1,
    topic="algebra", subtopic="circle_equations",
    title="Circles centred at the origin: equations, points and tangents",
    difficulty_descriptions={
        1: "Write the equation from the radius, or read the centre and radius.",
        2: "Find a missing coordinate, or decide if a point is inside, on or outside.",
        3: "Find the equation of the tangent at a point on the circle.",
        4: "Use the tangent: where it meets the x-axis, or the area cut off with the axes.",
    },
    tags=("algebra", "graphs", "circles", "tangents"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("equation", "radius"),
    2: ("missing", "position"),
    3: ("tangent_slope", "tangent_general"),
    4: ("tangent_intercept", "tangent_area"),
}
COORDINATES = tuple(v for v in range(-8, 9) if v != 0)
LARGEST_R_SQUARED = 100
EQUATION_R_SQUARED = tuple(range(4, 145))
RADII = tuple(range(2, 13))
POSITION_R_SQUARED = tuple(range(10, 101))
POSITION_COORDINATES = tuple(range(-9, 10))
MARKS = {1: 2, 2: 2, 3: 3, 4: 4}
WORKING_LINES = {1: 3, 2: 4, 3: 6, 4: 8}

KEYS = {
    "equation": {"r_squared"},
    "radius": {"radius"},
    "missing": {"a", "b", "unknown"},
    "position": {"r_squared", "s", "t"},
    "tangent_slope": {"a", "b"},
    "tangent_general": {"a", "b"},
    "tangent_intercept": {"a", "b"},
    "tangent_area": {"a", "b"},
}


# ------------------------------------------------------------ checks

def is_square(n):
    return n >= 0 and math.isqrt(n) ** 2 == n


def lattice_ok(par):
    a, b = par["a"], par["b"]
    require(a in COORDINATES and b in COORDINATES, "Coordinate outside bounds")
    require(a * a + b * b <= LARGEST_R_SQUARED, "Radius too large")


def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    form = par.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(par) == KEYS[form] | {"form"}, "Unexpected parameters")
    require(all(type(par[k]) is int for k in KEYS[form] - {"unknown"}), "Integer parameters required")
    if form == "equation":
        require(par["r_squared"] in EQUATION_R_SQUARED, "r squared outside bounds")
    elif form == "radius":
        require(par["radius"] in RADII, "Radius outside bounds")
    elif form == "position":
        require(par["r_squared"] in POSITION_R_SQUARED, "r squared outside bounds")
        require(par["s"] in POSITION_COORDINATES and par["t"] in POSITION_COORDINATES,
                "Coordinate outside bounds")
        require((par["s"], par["t"]) != (0, 0), "The origin is too easy")
    else:
        lattice_ok(par)
        if form == "missing":
            require(par["unknown"] in ("x", "y"), "Unknown coordinate must be x or y")


# ------------------------------------------------------------ notation

def circle_parts(r_squared):
    return ("x^{2} + y^{2} = %d" % r_squared, "x^2 + y^2 = %d" % r_squared)


def squared_base(value):
    """Bracket only negative bases: 3^2 but (-3)^2."""
    return "({})".format(value) if value < 0 else str(value)


def point_text(x, y):
    return "({}, {})".format(x, y)


def coefficient_parts(value, symbol, first):
    """(tex, text) for value*symbol, or a constant when symbol is ''."""
    value = Fraction(value)
    if value == 0:
        return "", ""
    size = abs(value)
    if first:
        sign_tex = sign_text = "-" if value < 0 else ""
    else:
        sign_tex = sign_text = " - " if value < 0 else " + "
    if symbol and size == 1:
        return sign_tex + symbol, sign_text + symbol
    if size.denominator == 1:
        return sign_tex + str(size.numerator) + symbol, sign_text + str(size.numerator) + symbol
    tex = r"\frac{%d}{%d}" % (size.numerator, size.denominator) + symbol
    text = ("(%d/%d)" % (size.numerator, size.denominator) + symbol) if symbol \
        else "%d/%d" % (size.numerator, size.denominator)
    return sign_tex + tex, sign_text + text


def line_parts(m, c):
    m_tex, m_text = coefficient_parts(m, "x", True)
    c_tex, c_text = coefficient_parts(c, "", not m_tex)
    return "y = " + m_tex + c_tex, "y = " + m_text + c_text


def general_line(a, b):
    """Integer form A x + B y = C with no common factor and A > 0."""
    r_squared = a * a + b * b
    common = math.gcd(math.gcd(abs(a), abs(b)), r_squared)
    A, B, C = a // common, b // common, r_squared // common
    if A < 0:
        A, B, C = -A, -B, -C
    return A, B, C


def general_parts(A, B, C):
    x_tex, x_text = coefficient_parts(A, "x", True)
    y_tex, y_text = coefficient_parts(B, "y", False)
    return x_tex + y_tex + " = " + str(C), x_text + y_text + " = " + str(C)


def content(blocks):
    plain = []
    for block in blocks:
        if "runs" in block:
            plain.append("".join(run["text"] for run in block["runs"]))
        else:
            plain.append(block["text"])
    return Content(" ".join(plain), blocks=tuple(blocks))


# ------------------------------------------------------------ prompts and answers

def prompt_for(par):
    form = par["form"]
    if form == "equation":
        r_squared = par["r_squared"]
        radius = (rb.maths(str(math.isqrt(r_squared)), str(math.isqrt(r_squared)))
                  if is_square(r_squared)
                  else rb.maths(r"\sqrt{%d}" % r_squared, "sqrt(%d)" % r_squared))
        return content([rb.paragraph(
            rb.text("A circle has centre (0, 0) and radius "), radius,
            rb.text(". Write down the equation of the circle."))])
    if form == "radius":
        return content([rb.paragraph(
            rb.text("A circle has equation "), rb.maths(*circle_parts(par["radius"] ** 2)),
            rb.text(". Write down (a) the coordinates of its centre, (b) its radius."))])
    if form == "position":
        return content([rb.paragraph(
            rb.text("Is the point {} inside, on or outside the circle ".format(
                point_text(par["s"], par["t"]))),
            rb.maths(*circle_parts(par["r_squared"])),
            rb.text("? Show how you decide."))])

    a, b = par["a"], par["b"]
    circle = rb.maths(*circle_parts(a * a + b * b))
    if form == "missing":
        if par["unknown"] == "y":
            point, sign = "(%d, k)" % a, "positive" if b > 0 else "negative"
        else:
            point, sign = "(k, %d)" % b, "positive" if a > 0 else "negative"
        return content([rb.paragraph(
            rb.text("The point P{} lies on the circle ".format(point)), circle,
            rb.text(", where k is {}. Find the value of k.".format(sign)))])

    opening = [rb.text("The point P{} lies on the circle ".format(point_text(a, b))),
               circle, rb.text(". ")]
    if form == "tangent_slope":
        task = ("Find an equation of the tangent to the circle at P. Give your answer "
                "in the form y = mx + c.")
    elif form == "tangent_general":
        task = ("Find an equation of the tangent to the circle at P. Give your answer "
                "in the form ax + by = c, where a, b and c are integers.")
    elif form == "tangent_intercept":
        task = ("The tangent to the circle at P meets the x-axis at Q. "
                "Find the coordinates of Q.")
    else:
        task = ("The tangent to the circle at P meets the x-axis at A and the y-axis at B. "
                "Find the area of triangle OAB, where O is the origin.")
    return content([rb.paragraph(*opening, rb.text(task))])


def answer_for(par):
    form = par["form"]
    if form == "equation":
        tex, text = circle_parts(par["r_squared"])
        return {"kind": "circle_equation", "r_squared": str(par["r_squared"])}, Content(text, tex)
    if form == "radius":
        return ({"kind": "centre_radius", "centre_x": "0", "centre_y": "0",
                 "radius": str(par["radius"])},
                Content("(a) (0, 0) (b) {}".format(par["radius"])))
    if form == "position":
        s, t, r_squared = par["s"], par["t"], par["r_squared"]
        distance = s * s + t * t
        if distance < r_squared:
            word, compare = "inside", "less than"
        elif distance == r_squared:
            word, compare = "on", "equal to"
        else:
            word, compare = "outside", "more than"
        return ({"kind": "position", "value": word, "distance_squared": str(distance)},
                Content("{}^2 + {}^2 = {}, which is {} {}, so the point is {} the circle."
                        .format(squared_base(s), squared_base(t), distance, compare,
                                r_squared, word)))

    a, b = par["a"], par["b"]
    r_squared = a * a + b * b
    if form == "missing":
        value = b if par["unknown"] == "y" else a
        return {"kind": "rational", "value": str(value)}, Content("k = %d" % value, "k = %d" % value)
    if form == "tangent_slope":
        m, c = Fraction(-a, b), Fraction(r_squared, b)
        tex, text = line_parts(m, c)
        return {"kind": "line", "m": rational_text(m), "c": rational_text(c)}, Content(text, tex)
    if form == "tangent_general":
        A, B, C = general_line(a, b)
        tex, text = general_parts(A, B, C)
        return {"kind": "line_general", "a": str(A), "b": str(B), "c": str(C)}, Content(text, tex)
    if form == "tangent_intercept":
        x = Fraction(r_squared, a)
        return ({"kind": "point", "x": rational_text(x), "y": "0"},
                Content("Q = ({}, 0)".format(rational_text(x))))
    area = Fraction(r_squared * r_squared, 2 * abs(a * b))
    return ({"kind": "rational", "value": rational_text(area)},
            Content("Area = " + rational_text(area), r"\mathrm{Area} = " + rational_tex(area)))


def draw_parameters(rng, level, form):
    par = {"form": form}
    if form == "equation":
        par["r_squared"] = rng.choice(EQUATION_R_SQUARED)
    elif form == "radius":
        par["radius"] = rng.choice(RADII)
    elif form == "position":
        par.update(r_squared=rng.choice(POSITION_R_SQUARED),
                   s=rng.choice(POSITION_COORDINATES), t=rng.choice(POSITION_COORDINATES))
    else:
        par.update(a=rng.choice(COORDINATES), b=rng.choice(COORDINATES))
        if form == "missing":
            par["unknown"] = rng.choice(("x", "y"))
    return par


# ------------------------------------------------------------ generator

class CircleEquations:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        form = rng.choice(FORMS[difficulty])
        for attempt in range(1000):
            par = draw_parameters(rng, difficulty, form)
            try:
                check_parameters(par, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a circle equation question")
        answer, display = answer_for(par)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(par),
            answer=answer, answer_display=display, worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=WORKING_LINES[difficulty]),
            parameters=par,
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
        return True

    def validate_independently(self, q):
        """Tangency by distance from O, perpendicularity by dot products, area by 1/2 r |AB|."""
        par, answer = q.parameters, q.answer
        form = par.get("form")
        if form == "equation":
            require(int(answer["r_squared"]) == par["r_squared"], "Independent equation disagrees")
            return True
        if form == "radius":
            require(int(answer["radius"]) ** 2 == par["radius"] ** 2 and int(answer["radius"]) > 0,
                    "Independent radius disagrees")
            return True
        if form == "position":
            gap = par["s"] ** 2 + par["t"] ** 2 - par["r_squared"]
            expected = "inside" if gap < 0 else "on" if gap == 0 else "outside"
            require(answer["value"] == expected, "Independent position disagrees")
            return True
        a, b = par["a"], par["b"]
        r_squared = a * a + b * b
        if form == "missing":
            k = int(answer["value"])
            known = a if par["unknown"] == "y" else b
            require(known * known + k * k == r_squared, "Point is not on the circle")
            require((k > 0) == ((b if par["unknown"] == "y" else a) > 0), "Wrong sign of k")
            return True
        if form == "tangent_slope":
            m, c = Fraction(answer["m"]), Fraction(answer["c"])
            require(m * a + c == b, "P is not on the stated line")
            require(c * c == r_squared * (1 + m * m), "Line is not at distance r from O")
            return True
        if form == "tangent_general":
            A, B, C = int(answer["a"]), int(answer["b"]), int(answer["c"])
            require(A * a + B * b == C, "P is not on the stated line")
            require(C * C == r_squared * (A * A + B * B), "Line is not at distance r from O")
            return True
        if form == "tangent_intercept":
            x = Fraction(answer["x"])
            require((x - a) * a + (0 - b) * b == 0, "PQ is not perpendicular to OP")
            return True
        x0, y0 = Fraction(r_squared, a), Fraction(r_squared, b)
        area = Fraction(answer["value"])
        require((2 * area) ** 2 == r_squared * (x0 * x0 + y0 * y0),
                "Area disagrees with 1/2 r |AB|")
        return True