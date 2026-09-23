"""Rich painting questions and answer keys, authored from exact problem data.

Example for future conversions:
- Keep the generator's full plain-text fallback.
- Group related givens into short paragraphs.
- Build mathematical runs from exact values, never parse prose.
- Separate intermediate quantities from the final decision.
"""
from fractions import Fraction
from .core import rational_tex


def prose(value):
    return {"kind": "paragraph", "text": value}


def text(value):
    return {"text": value}


def quantity(value, unit_tex, unit_text):
    from .painting import decimal_or_fraction
    plain = decimal_or_fraction(value)
    tex = rational_tex(Fraction(value)) if "/" in plain else plain
    return {
        "tex": tex + r"\," + unit_tex,
        "text": plain + " " + unit_text,
    }


def paragraph(*runs):
    return {"kind": "paragraph", "runs": list(runs)}


def question_blocks(parameters, level):
    from .painting import dimensions, money, metres
    if level == 3:
        blocks = [
            prose("A stepped wall consists of two non-overlapping rectangular sections."),
            prose("The first section is {}. The second is {}.".format(
                *(dimensions(section) for section in parameters["sections"])
            )),
        ]
    else:
        blocks = [prose(
            "A rectangular wall is {}.".format(dimensions(parameters["sections"][0]))
        )]
    if parameters["openings"]:
        door, window = parameters["openings"]
        blocks.append(prose(
            "The wall contains a door {} and a window {}. Neither is to be painted.".format(
                dimensions(door), dimensions(window),
            )
        ))
    blocks.append(prose("Only one face of the wall is to be painted."))

    for index, paint in enumerate(parameters["paints"]):
        name = "Paint " + chr(65 + index) if level == 4 else "The paint"
        coats = "{} {}".format(paint["coats"], "coat" if paint["coats"] == 1 else "coats")
        blocks.append(paragraph(
            text("{} requires {}. One litre covers ".format(name, coats)),
            quantity(paint["coverage"], r"\mathrm{m}^{2}", "square metres"),
            text(
                " for one coat. It is sold only in {}-litre tins at {} each.".format(
                    metres(paint["tin_tenths"]), money(paint["price_pence"]),
                )
            ),
        ))
    blocks.append(prose(
        "The paint budget is {}. Assume exact coverage, no wastage and no paint "
        "already available.".format(money(parameters["budget_pence"]))
    ))
    if level == 4:
        blocks.append(prose(
            "Use one paint throughout. Which paint gives the lower total purchase "
            "cost, and is the budget sufficient? Show the whole tins needed and "
            "total cost for each paint."
        ))
    else:
        blocks.append(prose(
            "Is the budget sufficient? Show the paintable area, the whole tins "
            "needed and the total purchase cost."
        ))
    return tuple(blocks)


def answer_blocks(answer, level):
    from .painting import money
    blocks = [paragraph(
        text("Paintable area: "),
        quantity(answer["area"], r"\mathrm{m}^{2}", "square metres"),
        text("."),
    )]
    for index, purchase in enumerate(answer["purchases"]):
        name = "Paint {}: ".format(chr(65 + index)) if level == 4 else ""
        count = purchase["tins"]
        blocks.append(paragraph(
            text(name),
            quantity(purchase["litres"], r"\mathrm{L}", "litres"),
            text(" needed. Buy {} {}; total cost {}.".format(
                count, "tin" if count == 1 else "tins", money(purchase["cost_pence"]),
            )),
        ))
    if level == 4:
        blocks.append(prose("Choose Paint {}.".format(chr(65 + answer["winner"]))))
    difference = answer["budget_difference_pence"]
    if difference > 0:
        conclusion = "The budget is sufficient, with {} remaining.".format(money(difference))
    elif difference == 0:
        conclusion = "The budget is exactly sufficient."
    else:
        conclusion = "The budget is insufficient by {}.".format(money(-difference))
    blocks.append(prose(conclusion))
    return tuple(blocks)