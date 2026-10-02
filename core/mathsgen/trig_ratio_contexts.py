"""Applied forms for geometry.trigonometry.right_angled: equal trig ratios.

L2 one_ratio        one right-angled triangle with an algebraic side and a
                    given value such as tan a = 3/4: find x
L3 equal_linear     two triangles and a relation such as sin a = tan b; the
                    algebraic sides give a linear equation
L4 equal_quadratic  the same, with the algebraic sides placed so that
                    cross-multiplying gives a quadratic; only one root makes
                    real triangles

Each triangle stores its trig function and the two sides that ratio uses,
"top" over "bottom", as linear expressions [a, b] meaning a x + b (a = 0 is a
plain number). Diagrams are schematic ("Not drawn accurately"), like the
bare questions, and must pass the shared label checks while building.

check() solves the cross-multiplied polynomial with exact Fractions and
keeps the roots that make real triangles: every side positive and each leg
shorter than its hypotenuse. Exactly one root may remain.
validate_independently() solves the original ratio equation with SymPy and
applies the same triangle test.
"""
from fractions import Fraction
from math import isqrt

from . import rich_blocks as rb
from . import solid_figures as solids
from . import worded
from .core import Content, rational_text, require
from .worded import Context


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {2: 0.3, 3: 0.35, 4: 0.35}
MARKS = {2: 3, 3: 4, 4: 5}
WORKING_LINES = {2: 5, 3: 6, 4: 8}

FUNCTIONS = ("sin", "cos", "tan")
# The sides each ratio uses, relative to the marked angle: (top, bottom).
SIDES = {"sin": ("opposite", "hypotenuse"), "cos": ("adjacent", "hypotenuse"),
         "tan": ("opposite", "adjacent")}
RATIOS = (Fraction(1, 2), Fraction(1, 3), Fraction(2, 3), Fraction(3, 4), Fraction(3, 5),
          Fraction(4, 5), Fraction(2, 5), Fraction(5, 8), Fraction(3, 8), Fraction(5, 6))
SLOPES = (-2, -1, 1, 2, 3)
ANSWER_DENOMINATORS = (1, 2, 4, 5)
LETTERS = ("a", "b")
BUILD_ATTEMPTS = 300


def context_share(level):
    return CONTEXT_SHARE.get(level, 0.0)


# ------------------------------------------------------- linear expressions

def term(raw):
    require(isinstance(raw, list) and len(raw) == 2, "Expression must be [a, b]")
    a, b = raw
    require(a in (0,) + SLOPES and type(b) is int and -40 <= b <= 40, "Expression bounds")
    require(a != 0 or b > 0, "A plain length must be positive")
    return a, b


def at(raw, x):
    a, b = term(raw)
    return a * x + b


def expression(raw):
    a, b = term(raw)
    if a == 0:
        return str(b)
    x = "x" if a == 1 else "-x" if a == -1 else "{}x".format(a)
    if b == 0:
        return x
    if a < 0 and b > 0:
        return "{} - {}".format(b, x[1:])
    return "{} {} {}".format(x, "+" if b > 0 else "-", abs(b))


def times(first, second):
    """Coefficients (x², x, 1) of the product of two linear expressions."""
    a, b = term(first)
    c, d = term(second)
    return (a * c, a * d + b * c, b * d)


def rational_sqrt(value):
    value = Fraction(value)
    top, bottom = isqrt(value.numerator), isqrt(value.denominator)
    require(top * top == value.numerator and bottom * bottom == value.denominator,
            "The equation must have rational roots")
    return Fraction(top, bottom)


def roots(c2, c1, c0):
    c2, c1, c0 = Fraction(c2), Fraction(c1), Fraction(c0)
    if c2 == 0:
        require(c1 != 0, "The equation must involve x")
        return [-c0 / c1]
    discriminant = c1 * c1 - 4 * c2 * c0
    require(discriminant > 0, "Two distinct roots needed")
    root = rational_sqrt(discriminant)
    return sorted({(-c1 + root) / (2 * c2), (-c1 - root) / (2 * c2)})


# ---------------------------------------------------------------- triangles

def triangle(raw):
    require(isinstance(raw, dict) and set(raw) == {"function", "top", "bottom"},
            "Triangle must give a function and two sides")
    require(raw["function"] in FUNCTIONS, "Unknown trig function")
    term(raw["top"])
    term(raw["bottom"])
    return raw


def is_real(raw, x):
    """Both stated sides positive; a leg must be shorter than its hypotenuse."""
    top, bottom = at(raw["top"], x), at(raw["bottom"], x)
    if top <= 0 or bottom <= 0:
        return False
    return raw["function"] == "tan" or top < bottom


def triangles_of(p):
    if p["context"] == "one_ratio":
        return [triangle(p["triangle"])]
    require(isinstance(p["triangles"], list) and len(p["triangles"]) == 2, "Two triangles")
    first, second = (triangle(raw) for raw in p["triangles"])
    require(first["function"] != second["function"], "Two different trig functions")
    return [first, second]


def equation(p):
    """Coefficients (x², x, 1) of the cross-multiplied equation, set to zero."""
    tris = triangles_of(p)
    if p["context"] == "one_ratio":
        top, bottom = Fraction(*ratio(p)).numerator, Fraction(*ratio(p)).denominator
        a, b = term(tris[0]["top"])
        c, d = term(tris[0]["bottom"])
        return (0, bottom * a - top * c, bottom * b - top * d)
    left = times(tris[0]["top"], tris[1]["bottom"])
    right = times(tris[1]["top"], tris[0]["bottom"])
    return tuple(l - r for l, r in zip(left, right))


def ratio(p):
    require(isinstance(p["ratio"], list) and Fraction(*p["ratio"]) in RATIOS, "Unknown ratio")
    return p["ratio"]


def solve(p):
    c2, c1, c0 = equation(p)
    if p["context"] == "equal_quadratic":
        require(c2 != 0, "The equation must be quadratic")
    else:
        require(c2 == 0, "The equation must be linear")
    tris = triangles_of(p)
    real = [x for x in roots(c2, c1, c0) if x > 0 and all(is_real(t, x) for t in tris)]
    require(len(real) == 1, "Exactly one root must make real triangles")
    x = real[0]
    require(x.denominator in ANSWER_DENOMINATORS and x <= 20, "Answer out of bounds")
    for t in tris:
        require(all(at(t[key], x) <= 40 for key in ("top", "bottom")), "Sides too long")
    return x


# ------------------------------------------------------------------ diagram

SIDE_NAMES = {"opposite": "the side opposite {}", "adjacent": "the side adjacent to {}",
              "hypotenuse": "the hypotenuse"}
TRIANGLE_WIDTH, TRIANGLE_HEIGHT = 120, 110


def side_labels(raw):
    top, bottom = SIDES[raw["function"]]
    return {top: expression(raw["top"]), bottom: expression(raw["bottom"])}


def diagram(tris):
    origins = [(40, 50), (220, 50)] if len(tris) == 2 else [(110, 50)]
    nodes = []
    for raw, (x0, y0), letter in zip(tris, origins, LETTERS):
        corner, along, up = [x0, y0], [x0 + TRIANGLE_WIDTH, y0], [x0, y0 + TRIANGLE_HEIGHT]
        nodes.append({"type": "polygon", "points": [corner, along, up]})
        nodes.append({"type": "right_angle", "vertex": corner, "first": along, "second": up})
        for name, text in side_labels(raw).items():
            reach = 3.5 * len(text)
            point = {
                "adjacent": (x0 + TRIANGLE_WIDTH / 2, y0 - 14),
                "opposite": (x0 - 6 - reach, y0 + TRIANGLE_HEIGHT / 2),
                "hypotenuse": (x0 + TRIANGLE_WIDTH / 2 + 10 + reach,
                               y0 + TRIANGLE_HEIGHT / 2 + 8),
            }[name]
            nodes.append({"type": "label", "point": [round(point[0], 1), round(point[1], 1)],
                          "text": text})
        nodes.append({"type": "label", "point": [x0 + TRIANGLE_WIDTH - 26, y0 + 11],
                      "text": letter})
    return {"kind": "scene", "version": 1, "width": 360 if len(tris) == 2 else 300,
            "height": 200, "caption": "Not drawn accurately", "nodes": nodes}


def describe(raw, letter):
    parts = ["{} is {}".format(SIDE_NAMES[name].format(letter), text)
             for name, text in side_labels(raw).items()]
    return "In the triangle with angle {}, {}.".format(letter, " and ".join(parts))


# ------------------------------------------------------------------ building

def algebraic(rng, length, x):
    slope = rng.choice(SLOPES)
    return [slope, length - slope * x]


def numeric_triangle(rng, function, value):
    scale = rng.randint(1, 4)
    return {"function": function, "top": [0, value.numerator * scale],
            "bottom": [0, value.denominator * scale]}


def drawable(p):
    try:
        solve(p)
        return solids.labels_ok(diagram(triangles_of(p)))
    except ValueError:
        return False


def build_one(rng):
    for _ in range(BUILD_ATTEMPTS):
        x, value = rng.randint(2, 8), rng.choice(RATIOS)
        tri = numeric_triangle(rng, rng.choice(FUNCTIONS), value)
        place = rng.choice(("top", "bottom"))
        tri[place] = algebraic(rng, tri[place][1], x)
        p = {"context": "one_ratio", "triangle": tri,
             "ratio": [value.numerator, value.denominator]}
        if drawable(p):
            return p
    raise ValueError("Could not build a one-triangle ratio question")


def build_pair(rng, context):
    for _ in range(BUILD_ATTEMPTS):
        x, value = rng.randint(1, 6), rng.choice(RATIOS)
        tris = [numeric_triangle(rng, f, value) for f in rng.sample(FUNCTIONS, 2)]
        if context == "equal_linear":
            places = rng.choice((("top", "top"), ("bottom", "bottom")))
        else:
            places = rng.choice((("top", "bottom"), ("bottom", "top")))
        for tri, place in zip(tris, places):
            tri[place] = algebraic(rng, tri[place][1], x)
        p = {"context": context, "triangles": tris}
        if drawable(p):
            return p
    raise ValueError("Could not build a two-triangle ratio question")


# --------------------------------------------------------------------- parts

def answer_parts(x):
    shown = str(x.numerator) if x.denominator == 1 else "{:g}".format(float(x))
    return {"answer": {"kind": "value", "value": rational_text(x)},
            "answer_display": Content("x = " + shown)}


def parts_one(p):
    x = solve(p)
    tri = triangles_of(p)[0]
    top, bottom = ratio(p)
    function = tri["function"]
    tex = r"\%s a=\frac{%d}{%d}" % (function, top, bottom)
    plain = "{} a = {}/{}".format(function, top, bottom)
    intro = ("The diagram shows a right-angled triangle. All lengths are measured in "
             "centimetres.")
    text = "{} {} Given that {}, work out the value of x.".format(intro, describe(tri, "a"),
                                                                  plain)
    blocks = (rb.prose(intro),
              rb.paragraph(rb.text("Given that "), rb.maths(tex, plain),
                           rb.text(", work out the value of x.")))
    return dict(prompt=Content(text, blocks=blocks), question_visuals=(diagram([tri]),),
                **answer_parts(x))


def parts_pair(p):
    x = solve(p)
    tris = triangles_of(p)
    first, second = tris[0]["function"], tris[1]["function"]
    tex = r"\%s a=\%s b" % (first, second)
    plain = "{} a = {} b".format(first, second)
    intro = ("The diagram shows two right-angled triangles. All lengths are measured in "
             "centimetres.")
    text = "{} {} {} Given that {}, work out the value of x.".format(
        intro, describe(tris[0], "a"), describe(tris[1], "b"), plain)
    blocks = (rb.prose(intro),
              rb.paragraph(rb.text("Given that "), rb.maths(tex, plain),
                           rb.text(", work out the value of x.")))
    return dict(prompt=Content(text, blocks=blocks), question_visuals=(diagram(tris),),
                **answer_parts(x))


# ----------------------------------------------------------------- registry

PAIR_KEYS = frozenset({"context", "triangles"})

CONTEXTS = {
    "one_ratio": Context(2, frozenset({"context", "triangle", "ratio"}),
                         build_one, solve, parts_one, None),
    "equal_linear": Context(3, PAIR_KEYS, lambda rng: build_pair(rng, "equal_linear"),
                            solve, parts_pair, None),
    "equal_quadratic": Context(4, PAIR_KEYS, lambda rng: build_pair(rng, "equal_quadratic"),
                               solve, parts_pair, None),
}


# ------------------------------------------------ generate and validate

def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def validate_independently(q):
    """Solve the original ratio equation with SymPy, then test for real triangles."""
    import sympy
    p = q.parameters
    x = sympy.Symbol("x")
    tris = triangles_of(p)

    def side(raw):
        return raw[0] * x + raw[1]

    ratios = [side(t["top"]) / side(t["bottom"]) for t in tris]
    if p["context"] == "one_ratio":
        equation_ = sympy.Eq(ratios[0], sympy.Rational(*p["ratio"]))
    else:
        equation_ = sympy.Eq(ratios[0], ratios[1])
    real = []
    for candidate in sympy.solve(equation_, x):
        if not candidate.is_real or candidate <= 0:
            continue
        lengths = [(side(t["top"]).subs(x, candidate), side(t["bottom"]).subs(x, candidate),
                    t["function"]) for t in tris]
        if all(top > 0 and bottom > 0 and (f == "tan" or top < bottom)
               for top, bottom, f in lengths):
            real.append(candidate)
    require(real == [sympy.Rational(q.answer["value"])], "Independent solution disagrees")
    return True