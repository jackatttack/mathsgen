"""Authored mathematical presentation for related solids; no string parsing."""
from fractions import Fraction
from .core import rational_tex


def prose(text):
    return {"kind": "paragraph", "text": text}


def text(value):
    return {"text": value}


def maths(tex, fallback):
    return {"tex": tex, "text": fallback}


def question_blocks(parameters, relationship):
    known = parameters["known"]
    d = known["dimensions"]
    if known["shape"] == "cuboid":
        first = prose(
            "Solid A is a cuboid with dimensions {} cm, {} cm and {} cm.".format(*d)
        )
    elif known["shape"] == "cylinder":
        first = prose(
            "Solid A is a cylinder with radius {} cm and perpendicular height {} cm.".format(*d)
        )
    else:
        first = prose("Solid A is a sphere with radius {} cm.".format(d[0]))

    model = parameters["target"]["model"]
    d = parameters["target"]["dimensions"]
    if model == "linear":
        runs = [
            text("Solid B is a cuboid with dimensions {} cm, {} cm and ".format(d[0], d[1])),
            maths(r"(x+{})\,\mathrm{{cm}}".format(d[2]), "(x + {}) cm".format(d[2])),
            text("."),
        ]
    elif model == "quadratic":
        runs = [
            text("Solid B is a cuboid with dimensions "),
            maths(r"x\,\mathrm{cm}", "x cm"),
            text(", "),
            maths(r"(x+{})\,\mathrm{{cm}}".format(d[0]), "(x + {}) cm".format(d[0])),
            text(" and {} cm.".format(d[1])),
        ]
    elif model == "cylinder":
        runs = [
            text("Solid B is a cylinder with radius "),
            maths(r"x\,\mathrm{cm}", "x cm"),
            text(" and perpendicular height {} cm.".format(d[0])),
        ]
    else:
        runs = [text("Solid B is a sphere with radius "),
                maths(r"x\,\mathrm{cm}", "x cm"), text(".")]
    blocks = [
        first,
        {"kind": "paragraph", "runs": runs},
        prose(relationship),
    ]
    if known["shape"] == "sphere" or model == "sphere":
        blocks.append({
            "kind": "paragraph",
            "runs": [
                text("The volume of a sphere is "),
                maths(r"V=\frac{4}{3}\pi r^{3}", "V = (4/3)pi*r^3"),
                text("."),
            ],
        })
    blocks.append({
        "kind": "paragraph",
        "runs": [
            text("Form an equation in "),
            maths("x", "x"),
            text(" and solve it. Given that "),
            maths("x>0", "x > 0"),
            text(", give "),
            maths("x", "x"),
            text(" to 1 decimal place."),
        ],
    })
    return tuple(blocks)


def equation_tex(parameters):
    # Import at call time so generator and presentation modules do not form
    # an import-time cycle.
    from .related_solids import known_coefficient, relation_factor, uses_pi
    model = parameters["target"]["model"]
    d = parameters["target"]["dimensions"]
    if model == "linear":
        left = "{}(x+{})".format(d[0] * d[1], d[2])
    elif model == "quadratic":
        left = "{}x(x+{})".format(d[1], d[0])
    elif model == "cylinder":
        left = str(d[0]) + r"\pi x^{2}"
    else:
        left = r"\frac{4}{3}\pi x^{3}"
    coefficient = relation_factor(parameters["relation"]) * known_coefficient(parameters["known"])
    right = rational_tex(Fraction(coefficient))
    if uses_pi(parameters["known"]["shape"]):
        right += r"\pi"
    return left + "=" + right


def answer_blocks(parameters, answer):
    return (
        prose("One valid equation is"),
        {"kind": "equation", "tex": equation_tex(parameters), "text": answer["equation"]},
        {
            "kind": "paragraph",
            "runs": [
                text("The positive solution is "),
                maths(
                    r"x\approx " + answer["x_1dp"] + r"\,\mathrm{cm}",
                    "x is approximately " + answer["x_1dp"] + " cm",
                ),
                text(" (to 1 decimal place)."),
            ],
        },
        prose("Equivalent equations are accepted."),
    )