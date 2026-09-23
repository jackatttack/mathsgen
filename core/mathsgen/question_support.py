"""Authored teaching support. No generated answers are read by these builders."""
from dataclasses import dataclass
from fractions import Fraction

from .core import Content, require

LINEAR = "algebra.linear.two_sided"
QUADRATIC = "algebra.quadratic.factorisable_monic"
TRIG = "geometry.trigonometry.right_angled"

# Explicit versions prevent stale support silently attaching to changed models.
SUPPORTED_VERSIONS = {LINEAR: 3, QUADRATIC: 1, TRIG: 4}


@dataclass(frozen=True)
class SupportCard:
    title: str
    content: Content
    visuals: tuple = ()


def paragraph(text):
    return {"kind": "paragraph", "text": text}


def equation(text, tex):
    return {"kind": "equation", "text": text, "tex": tex}


def make_card(title, blocks, visuals=()):
    fallback = "\n".join(block["text"] for block in blocks)
    return SupportCard(title, Content(fallback, blocks=tuple(blocks)), tuple(visuals))


def supports(question):
    return (
        SUPPORTED_VERSIONS.get(question.generator_id) == question.generator_version
        and question.difficulty in (1, 2, 3, 4)
    )


def linear_facts(question):
    blocks = [
        paragraph("An equation is a balance: do the same operation to both sides."),
        paragraph("Collect the variable terms on one side and the constants on the other. "
                  "Then divide by the coefficient of the variable."),
        paragraph("Check by substituting your result into the original equation."),
    ]
    if question.difficulty >= 3:
        blocks += [
            paragraph("Expand a bracket by multiplying every term inside it."),
            equation("a(bx + c) = abx + ac", r"a(bx+c)=abx+ac"),
        ]
    if question.difficulty == 4:
        blocks += [
            paragraph("Clear numerical denominators by multiplying every term on both "
                      "sides by their lowest common multiple. Then expand and collect."),
            paragraph("Keep fractions exact until the equation is solved."),
        ]
    return make_card("Linear equations: useful facts", blocks)


def linear_hint(question):
    if question.difficulty <= 2:
        from .linear_two_sided import linear_expression
        b = Fraction(question.parameters["b"])
        term = linear_expression(abs(b), 0)
        operation = "Add" if b < 0 else "Subtract"
        direction = "to" if b < 0 else "from"
        blocks = [
            paragraph("{} {} {} both sides. This removes the x term on the right."
                      .format(operation, term, direction)),
            paragraph("Collect the remaining x terms before moving the constants."),
        ]
    elif question.difficulty == 3:
        blocks = [
            paragraph("Start by expanding both brackets. Multiply the outside number "
                      "by every term inside, including the constant."),
            paragraph("Write the expanded equation before collecting the x terms."),
        ]
    else:
        blocks = [
            paragraph("Start with the denominators: find their lowest common multiple."),
            paragraph("Multiply the entire equation by it, including every term on both "
                      "sides. Then expand any remaining brackets."),
        ]
    return make_card("Linear equations: first step", blocks)


def quadratic_facts(question):
    blocks = [
        paragraph("First arrange the equation so that one side is zero."),
        equation("x squared + bx + c = (x + m)(x + n)",
                 r"x^2+bx+c=(x+m)(x+n)"),
        equation("m + n = b and mn = c", r"m+n=b,\qquad mn=c"),
        paragraph("Find two numbers with the required sum and product."),
        paragraph("If a product is zero, at least one factor is zero. "
                  "Set each bracket equal to zero and solve both equations."),
        equation("x + m = 0 gives x = -m", r"x+m=0\quad\Rightarrow\quad x=-m"),
    ]
    if question.difficulty >= 3:
        blocks.insert(1, paragraph(
            "Move the right-hand terms to the left and collect like terms before "
            "choosing a factor pair."
        ))
    return make_card("Monic quadratics: useful facts", blocks)


def quadratic_hint(question):
    left = question.parameters["left"]
    right = question.parameters["right"]
    b = left[1] - right[1]
    c = left[2] - right[2]
    if question.difficulty <= 2:
        blocks = [
            paragraph("Look for two integers that multiply to {} and add to {}."
                      .format(c, b)),
            paragraph("These are the numbers inside the brackets, not yet the solutions."),
        ]
    else:
        from .quadratic_monic import polynomial
        coefficients = [a - b for a, b in zip(left, right)]
        blocks = [
            paragraph("Move the right-hand terms to the left and collect like terms."),
            equation(polynomial(coefficients) + " = 0",
                     polynomial(coefficients, True) + "=0"),
            paragraph("Now look for a factor pair with product {} and sum {}."
                      .format(c, b)),
        ]
    return make_card("Monic quadratics: first step", blocks)


def trig_reference_scene():
    return {
        "kind": "scene", "version": 1, "width": 390, "height": 235,
        "caption": "Side names are relative to the marked angle x.",
        "nodes": [
            {"type": "polygon", "points": [[85, 50], [320, 50], [85, 195]]},
            {"type": "right_angle", "vertex": [85, 50],
             "first": [320, 50], "second": [85, 195]},
            {"type": "label", "point": [195, 28], "text": "A"},
            {"type": "label", "point": [56, 125], "text": "O"},
            {"type": "label", "point": [240, 137], "text": "H"},
            {"type": "label", "point": [272, 65], "text": "x"},
        ],
    }


def trig_facts(question):
    blocks = [
        paragraph("Use these ratios for a right-angled triangle. Set your calculator "
                  "to degrees for these questions."),
        paragraph("H is the hypotenuse, opposite the right angle. O is opposite the "
                  "marked angle. A touches the marked angle and is not the hypotenuse."),
        equation("sin x = O/H", r"\sin x=\frac{O}{H}"),
        equation("cos x = A/H", r"\cos x=\frac{A}{H}"),
        equation("tan x = O/A", r"\tan x=\frac{O}{A}"),
    ]
    if question.difficulty == 2:
        blocks += [
            paragraph("For an unknown angle, use the inverse of the chosen trig function."),
            equation("x = inverse tan(O/A)", r"x=\tan^{-1}\left(\frac{O}{A}\right)"),
            paragraph("Inverse tan finds an angle; it does not mean 1 divided by tan."),
        ]
    elif question.difficulty == 3:
        blocks += [
            equation("Perimeter = O + A + H", r"P=O+A+H"),
            paragraph("You need all three side lengths. Keep unrounded values until the end."),
        ]
    elif question.difficulty == 4:
        blocks += [
            equation("Area = one half times O times A", r"\mathrm{Area}=\frac{1}{2}OA"),
            paragraph("The base and height must be perpendicular. The hypotenuse "
                      "is not the perpendicular height."),
        ]
    blocks.append(paragraph("Round only your final answer to the requested accuracy."))
    return make_card("Right-angled trigonometry: useful facts",
                     blocks, [trig_reference_scene()])


def trig_hint(question):
    p = question.parameters
    if p["form"] == "find_angle":
        blocks = [
            paragraph("The supplied sides are opposite and adjacent to x, so choose tangent."),
            equation(
                "tan x = {}/{}".format(p["opposite"], p["adjacent"]),
                r"\tan x=\frac{" + str(p["opposite"]) + "}{" + str(p["adjacent"]) + "}",
            ),
            paragraph("Use inverse tan in degree mode to find x."),
        ]
    else:
        known = p["known"]
        wanted = p.get("wanted")
        if wanted is None:
            wanted = "adjacent" if known == "opposite" else "opposite"
        pair = frozenset((known, wanted))
        ratios = {
            frozenset(("opposite", "hypotenuse")): ("sin", "opposite", "hypotenuse"),
            frozenset(("adjacent", "hypotenuse")): ("cos", "adjacent", "hypotenuse"),
            frozenset(("opposite", "adjacent")): ("tan", "opposite", "adjacent"),
        }
        function, top, bottom = ratios[pair]
        values = {known: str(p["known_length"]), wanted: "u"}
        tex = (
            "\\" + function + "(" + str(p["angle"]) + r"^\circ)=\frac{"
            + values[top] + "}{" + values[bottom] + "}"
        )
        plain = "{}({} degrees) = {}/{}".format(
            function, p["angle"], values[top], values[bottom]
        )
        blocks = [
            paragraph("The known side is the {}. Call the {} u and use {}."
                      .format(known, wanted, function)),
            equation(plain, tex),
            paragraph("Rearrange this equation to find u."),
        ]
        if p["form"] == "find_side":
            blocks.append(paragraph("Here u is the side labelled x in your question."))
        elif p["form"] == "perimeter":
            blocks.append(paragraph("Then find the remaining side and add all three lengths."))
        else:
            blocks.append(paragraph("You need both perpendicular sides for the area. "
                                    "Find the other one if necessary, then use half their product."))
    return make_card("Right-angled trigonometry: first step", blocks)


BUILDERS = {
    LINEAR: {"facts": linear_facts, "hint": linear_hint},
    QUADRATIC: {"facts": quadratic_facts, "hint": quadratic_hint},
    TRIG: {"facts": trig_facts, "hint": trig_hint},
}


def card_for(question, action):
    require(supports(question), "Teaching support is not yet available for this generator version")
    require(action in ("facts", "hint"), "Unknown teaching-support action")
    card = BUILDERS[question.generator_id][action](question)
    card.content.validate_blocks()
    return card