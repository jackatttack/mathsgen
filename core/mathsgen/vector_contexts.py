"""Applied forms for geometry.vectors.column: points on a straight line.

L2 midpoint_end    M is the midpoint of AB; from A and M, find B
L3 divide_segment  P lies on AB with AP : PB = m : n; find P
L4 extend_line     A, B and C lie on a line in that order with
                   AB : BC = m : n; from A and B, find C

Every point is built backwards from whole-number coordinates. check() uses
the section formula with exact Fractions. validate_independently() checks
the stated point a different way: collinearity (cross product), order (dot
product) and the length ratio through squared distances.
"""
from fractions import Fraction

from .core import Content, require
from . import worded
from .worded import Context


# ------------------------------------------------------------ editable knobs

CONTEXT_SHARE = {2: 0.3, 3: 0.35, 4: 0.4}
MARKS = {2: 2, 3: 3, 4: 3}
WORKING_LINES = {2: 3, 3: 4, 4: 5}

# (first, middle, last) letters, in order along the line.
LETTERS = (("A", "M", "B"), ("P", "Q", "R"), ("L", "M", "N"), ("D", "E", "F"))
RATIOS = ((1, 2), (2, 1), (1, 3), (3, 1), (2, 3), (3, 2), (3, 4), (4, 3), (2, 5), (5, 2))
LIMIT = 24        # largest coordinate size anywhere in a question


def context_share(level):
    return CONTEXT_SHARE.get(level, 0.0)


# ------------------------------------------------------------------ helpers

def point(value):
    require(isinstance(value, list) and len(value) == 2
            and all(type(v) is int and abs(v) <= LIMIT for v in value),
            "Point out of bounds")
    return value


def letters(p):
    require(isinstance(p["letters"], list) and tuple(p["letters"]) in LETTERS,
            "Unknown letters")
    return p["letters"]


def ratio(p):
    require(isinstance(p["ratio"], list) and tuple(p["ratio"]) in RATIOS, "Unknown ratio")
    return p["ratio"]


def coordinates(xy):
    return "({}, {})".format(xy[0], xy[1])


def along(start, step, scale):
    """start + scale × step, which must land on whole numbers."""
    result = [Fraction(s) + Fraction(scale) * d for s, d in zip(start, step)]
    require(all(v.denominator == 1 for v in result), "Point is not on whole numbers")
    return point([int(v) for v in result])


def point_parts(prompt, answer):
    return {
        "prompt": Content(prompt),
        "answer": {"kind": "point", "x": str(answer[0]), "y": str(answer[1])},
        "answer_display": Content(coordinates(answer)),
    }


def small_step(rng):
    while True:
        step = [rng.randint(-4, 4), rng.randint(-4, 4)]
        if step != [0, 0]:
            return step


def start_point(rng):
    return [rng.randint(-9, 9), rng.randint(-9, 9)]


# ---------------------------------------------------- L2: midpoint, find B

def build_midpoint(rng):
    middle = start_point(rng)
    step = small_step(rng)
    return {"context": "midpoint_end", "letters": list(rng.choice(LETTERS)),
            "first": [middle[0] - step[0], middle[1] - step[1]], "middle": middle}


def check_midpoint(p):
    letters(p)
    first, middle = point(p["first"]), point(p["middle"])
    require(first != middle, "Distinct points needed")
    return along(first, [m - f for f, m in zip(first, middle)], 2)


def parts_midpoint(p):
    end = check_midpoint(p)
    a, m, b = letters(p)
    text = ("{m} is the midpoint of the line segment {a}{b}. {a} is {first} and {m} is "
            "{middle}. Find the coordinates of {b}.").format(
        a=a, m=m, b=b, first=coordinates(p["first"]), middle=coordinates(p["middle"]))
    return point_parts(text, end)


# ------------------------------------------------- L3: divide in a ratio

def build_divide(rng):
    m, n = rng.choice(RATIOS)
    first, step = start_point(rng), small_step(rng)
    return {"context": "divide_segment", "letters": list(rng.choice(LETTERS)),
            "first": first, "last": [first[0] + (m + n) * step[0], first[1] + (m + n) * step[1]],
            "ratio": [m, n]}


def check_divide(p):
    letters(p)
    m, n = ratio(p)
    first, last = point(p["first"]), point(p["last"])
    require(first != last, "Distinct points needed")
    return along(first, [l - f for f, l in zip(first, last)], Fraction(m, m + n))


def parts_divide(p):
    inside = check_divide(p)
    a, q, b = letters(p)
    m, n = p["ratio"]
    text = ("{q} lies on the line segment {a}{b} with {a}{q} : {q}{b} = {m} : {n}. "
            "{a} is {first} and {b} is {last}. Find the coordinates of {q}.").format(
        a=a, q=q, b=b, m=m, n=n, first=coordinates(p["first"]), last=coordinates(p["last"]))
    return point_parts(text, inside)


# ------------------------------------------ L4: extend a line in a ratio

def build_extend(rng):
    m, n = rng.choice(RATIOS)
    first, step = start_point(rng), small_step(rng)
    return {"context": "extend_line", "letters": list(rng.choice(LETTERS)),
            "first": first, "middle": [first[0] + m * step[0], first[1] + m * step[1]],
            "ratio": [m, n]}


def check_extend(p):
    letters(p)
    m, n = ratio(p)
    first, middle = point(p["first"]), point(p["middle"])
    require(first != middle, "Distinct points needed")
    return along(middle, [b - a for a, b in zip(first, middle)], Fraction(n, m))


def parts_extend(p):
    end = check_extend(p)
    a, b, c = letters(p)
    m, n = p["ratio"]
    text = ("The points {a}, {b} and {c} lie on a straight line, in that order. "
            "{a} is {first} and {b} is {middle}. Given that {a}{b} : {b}{c} = {m} : {n}, "
            "find the coordinates of {c}.").format(
        a=a, b=b, c=c, m=m, n=n, first=coordinates(p["first"]),
        middle=coordinates(p["middle"]))
    return point_parts(text, end)


# ----------------------------------------------------------------- registry

CONTEXTS = {
    "midpoint_end": Context(
        2, frozenset({"context", "letters", "first", "middle"}),
        build_midpoint, check_midpoint, parts_midpoint, None),
    "divide_segment": Context(
        3, frozenset({"context", "letters", "first", "last", "ratio"}),
        build_divide, check_divide, parts_divide, None),
    "extend_line": Context(
        4, frozenset({"context", "letters", "first", "middle", "ratio"}),
        build_extend, check_extend, parts_extend, None),
}


# ------------------------------------------------ generate and validate

def generate(generator, context):
    return worded.generate(generator, context, CONTEXTS, MARKS, WORKING_LINES)


def validate(generator, q):
    return worded.validate(generator, q, CONTEXTS, MARKS, WORKING_LINES)


def difference(start, end):
    return (end[0] - start[0], end[1] - start[1])


def cross(u, v):
    return u[0] * v[1] - u[1] * v[0]


def dot(u, v):
    return u[0] * v[0] + u[1] * v[1]


def validate_independently(q):
    """Check the stated point by geometry, not by the section formula."""
    p = q.parameters
    stated = (int(q.answer["x"]), int(q.answer["y"]))
    if p["context"] == "midpoint_end":
        first, middle = p["first"], p["middle"]
        require(dot(difference(first, middle), difference(first, middle))
                == dot(difference(middle, stated), difference(middle, stated))
                and cross(difference(first, middle), difference(middle, stated)) == 0
                and dot(difference(first, middle), difference(middle, stated)) > 0,
                "The midpoint is not halfway")
        return True
    m, n = p["ratio"]
    if p["context"] == "divide_segment":
        start, near, far = p["first"], stated, p["last"]
    else:
        start, near, far = p["first"], p["middle"], stated
    first_part, second_part = difference(start, near), difference(near, far)
    require(cross(first_part, second_part) == 0, "The points are not on one line")
    require(dot(first_part, second_part) > 0, "The points are not in order")
    require(dot(first_part, first_part) * n * n == dot(second_part, second_part) * m * m,
            "The lengths are not in the stated ratio")
    return True