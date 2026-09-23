"""Painting scenarios: connected area, coverage, purchasing and budget decisions."""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question,
    make_context, rational_text, require,
)


INFO = GeneratorInfo(
    id="problem_solving.painting.budget",
    version=2,
    topic="problem_solving",
    subtopic="painting_and_decorating",
    title="Painting: quantities, budgets and paint choices",
    difficulty_descriptions={
        1: "Find the paint cost for a rectangular wall and assess a budget.",
        2: "Exclude a door and window before calculating whole tins and cost.",
        3: "Calculate paint for a stepped wall made from two rectangles.",
        4: "Compare two paints with different coverage, coats and tin sizes.",
    },
    tags=("problem solving", "area", "money", "rounding", "coverage", "budget"),
)


def metres(decimetres):
    whole, tenth = divmod(decimetres, 10)
    return str(whole) if not tenth else "{}.{}".format(whole, tenth)


def money(pence):
    return "£{}.{:02d}".format(pence // 100, pence % 100)


def decimal_or_fraction(value):
    value = Fraction(value)
    for places in range(7):
        scaled = value * 10 ** places
        if scaled.denominator == 1:
            if places == 0:
                return str(scaled.numerator)
            return (
                "{}.{:0{}d}".format(
                    scaled.numerator // 10 ** places,
                    scaled.numerator % 10 ** places,
                    places,
                ).rstrip("0").rstrip(".")
            )
    return rational_text(value)


def dimensions(rectangle):
    return "{} m wide and {} m high".format(
        metres(rectangle[0]), metres(rectangle[1]),
    )


def paintable_area(parameters):
    """Dimensions are stored as exact integer decimetres."""
    return (
        sum(Fraction(w * h, 100) for w, h in parameters["sections"])
        - sum(Fraction(w * h, 100) for w, h in parameters["openings"])
    )


def results_for(parameters):
    area = paintable_area(parameters)
    purchases = []
    for paint in parameters["paints"]:
        litres = area * paint["coats"] / paint["coverage"]
        tin_litres = Fraction(paint["tin_tenths"], 10)
        quotient = litres / tin_litres
        tins = -(-quotient.numerator // quotient.denominator)
        purchases.append({
            "litres": rational_text(litres),
            "tins": tins,
            "cost_pence": tins * paint["price_pence"],
        })
    cheapest = min(item["cost_pence"] for item in purchases)
    winner = min(range(len(purchases)), key=lambda i: purchases[i]["cost_pence"])
    return {
        "kind": "painting_budget",
        "area": rational_text(area),
        "purchases": purchases,
        "winner": winner,
        "affordable": cheapest <= parameters["budget_pence"],
        "budget_difference_pence": parameters["budget_pence"] - cheapest,
    }


def presentation(parameters, level):
    if level == 3:
        lead = (
            "A stepped wall consists of two non-overlapping rectangular sections. "
            "The first is {}; the second is {}. "
        ).format(*(dimensions(section) for section in parameters["sections"]))
    else:
        lead = "A rectangular wall is {}. ".format(dimensions(parameters["sections"][0]))
    if parameters["openings"]:
        door, window = parameters["openings"]
        lead += (
            "It contains a door {} and a window {}. Neither is to be painted. "
        ).format(dimensions(door), dimensions(window))
    lead += "Only one face of the wall is to be painted. "
    for index, paint in enumerate(parameters["paints"]):
        name = "Paint " + chr(65 + index) if level == 4 else "The paint"
        lead += (
            "{} requires {} coats. One litre covers {} square metres for "
            "one coat. It is sold only in {}-litre tins costing {} each. "
        ).format(
            name, paint["coats"], paint["coverage"],
            metres(paint["tin_tenths"]), money(paint["price_pence"]),
        )
    lead += (
        "The budget for paint is {}. Assume the stated coverage is exact, "
        "there is no wastage, and no paint is already available. "
    ).format(money(parameters["budget_pence"]))
    if level == 4:
        lead += (
            "Use one paint throughout. Which paint gives the lower total "
            "purchase cost, and is the budget sufficient? Show the number "
            "of whole tins and total cost for each paint."
        )
    else:
        lead += (
            "Is the budget sufficient? Show the paintable area, the number "
            "of whole tins needed and the total purchase cost."
        )
    from .painting_typography import question_blocks
    return Content(lead, blocks=question_blocks(parameters, level))


def answer_display(answer, level):
    text = "Paintable area: {} square metres. ".format(
        decimal_or_fraction(answer["area"]),
    )
    for index, purchase in enumerate(answer["purchases"]):
        name = "Paint {}: ".format(chr(65 + index)) if level == 4 else ""
        text += "{}{} litres needed; {} tins; purchase cost {}. ".format(
            name, decimal_or_fraction(purchase["litres"]),
            purchase["tins"], money(purchase["cost_pence"]),
        )
    if level == 4:
        text += "Choose Paint {}. ".format(chr(65 + answer["winner"]))
    difference = answer["budget_difference_pence"]
    if difference >= 0:
        text += "The budget is sufficient, with {} remaining.".format(money(difference))
    else:
        text += "The budget is insufficient by {}.".format(money(-difference))
    from .painting_typography import answer_blocks
    return Content(text, blocks=answer_blocks(answer, level))


def check_parameters(parameters, level):
    require(
        set(parameters) == {"sections", "openings", "paints", "budget_pence"},
        "Unexpected parameters",
    )
    require(
        isinstance(parameters["sections"], list)
        and len(parameters["sections"]) == (2 if level == 3 else 1),
        "Wrong wall structure",
    )
    require(
        isinstance(parameters["openings"], list)
        and len(parameters["openings"]) == (2 if level in (2, 4) else 0),
        "Wrong opening structure",
    )
    for rectangle in parameters["sections"] + parameters["openings"]:
        require(
            isinstance(rectangle, list) and len(rectangle) == 2
            and all(type(value) is int and value > 0 for value in rectangle),
            "Invalid rectangle",
        )
    width, height = parameters["sections"][0]
    require(60 <= width <= 140 and 24 <= height <= 36, "Invalid main wall")
    if level == 3:
        width2, height2 = parameters["sections"][1]
        require(20 <= width2 <= 50 and 12 <= height2 <= 20, "Invalid wall extension")
    if parameters["openings"]:
        door, window = parameters["openings"]
        require(
            8 <= door[0] <= 10 and 20 <= door[1] <= 22
            and 10 <= window[0] <= 18 and 10 <= window[1] <= 16,
            "Invalid door/window dimensions",
        )
        require(
            door[0] + window[0] + 10 < width
            and max(door[1], window[1]) < height,
            "Openings must fit separately inside the wall",
        )
    paints = parameters["paints"]
    require(isinstance(paints, list) and len(paints) == (2 if level == 4 else 1),
            "Wrong number of paints")
    for paint in paints:
        require(
            isinstance(paint, dict)
            and set(paint) == {"coats", "coverage", "tin_tenths", "price_pence"}
            and all(type(value) is int for value in paint.values()),
            "Invalid paint specification",
        )
        require(
            paint["coats"] in (1, 2, 3)
            and paint["coverage"] in (8, 10, 12)
            and paint["tin_tenths"] in (25, 50)
            and 1800 <= paint["price_pence"] <= 4500,
            "Unsupported paint specification",
        )
    if level == 4:
        require(
            all(paints[0][key] != paints[1][key]
                for key in ("coverage", "coats", "tin_tenths")),
            "Comparison must vary coverage, coats and tin size",
        )
    require(type(parameters["budget_pence"]) is int and parameters["budget_pence"] > 0,
            "Invalid budget")
    require(paintable_area(parameters) > 0, "No paintable area")


class PaintingBudget:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        sections = [[rng.randrange(60, 141, 5), rng.choice((24, 25, 28, 30, 32, 36))]]
        if difficulty == 3:
            sections.append([rng.randrange(20, 51, 5), rng.choice((12, 15, 18, 20))])
        openings = []
        if difficulty in (2, 4):
            openings = [
                [rng.choice((8, 9, 10)), rng.choice((20, 21, 22))],
                [rng.choice((10, 12, 15, 18)), rng.choice((10, 12, 15, 16))],
            ]
        for attempt in range(100):
            paint = {
                "coats": rng.choice((1, 2)) if difficulty == 4 else 2,
                "coverage": rng.choice((8, 10, 12)),
                "tin_tenths": rng.choice((25, 50)),
                "price_pence": rng.randrange(1800, 4501, 100),
            }
            paints = [paint]
            if difficulty == 4:
                paints.append({
                    "coats": 3 - paint["coats"],
                    "coverage": rng.choice([n for n in (8, 10, 12) if n != paint["coverage"]]),
                    "tin_tenths": 75 - paint["tin_tenths"],
                    "price_pence": rng.randrange(1800, 4501, 100),
                })
            parameters = {
                "sections": sections, "openings": openings,
                "paints": paints, "budget_pence": 1,
            }
            preliminary = results_for(parameters)
            costs = [purchase["cost_pence"] for purchase in preliminary["purchases"]]
            if len(costs) == 1 or costs[0] != costs[1]:
                break
        else:
            raise ValueError("Could not construct a non-tied comparison")
        parameters["budget_pence"] = min(costs) + rng.choice((-500, -200, 0, 300, 700))
        answer = results_for(parameters)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=presentation(parameters, difficulty),
            answer=answer, answer_display=answer_display(answer, difficulty),
            worked_solution=(), marks=5 if difficulty == 4 else 4,
            tags=self.info.tags, layout_hint=LayoutHint(working_lines=8),
            parameters=parameters,
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")
        check_parameters(question.parameters, level)
        answer = results_for(question.parameters)
        if level == 4:
            require(
                answer["purchases"][0]["cost_pence"] != answer["purchases"][1]["cost_pence"],
                "Comparison must have a unique cheaper paint",
            )
        require(question.answer == answer, "Incorrect answer")
        require(question.prompt == presentation(question.parameters, level), "Prompt mismatch")
        require(question.answer_display == answer_display(answer, level), "Answer display mismatch")
        return True

    def validate_independently(self, question):
        """Enumerate whole-tin purchases using integer square-decimetre coverage."""
        p, answer = question.parameters, question.answer
        area_units = sum(w * h for w, h in p["sections"])
        area_units -= sum(w * h for w, h in p["openings"])
        require(Fraction(answer["area"]) * 100 == area_units, "Wrong net area")
        require(len(answer["purchases"]) == len(p["paints"]), "Missing paint result")
        costs = []
        for paint, purchase in zip(p["paints"], answer["purchases"]):
            demand = area_units * paint["coats"]
            capacity = paint["tin_tenths"] * 10 * paint["coverage"]
            feasible = [n for n in range(1, 101) if n * capacity >= demand]
            require(bool(feasible), "Purchase enumeration bound exceeded")
            tins = min(feasible)
            require(purchase["tins"] == tins, "Purchase is insufficient or not minimal")
            require(
                Fraction(purchase["litres"]) * paint["coverage"] * 100 == demand,
                "Incorrect litres required",
            )
            cost = sum(paint["price_pence"] for tin in range(tins))
            require(purchase["cost_pence"] == cost, "Incorrect purchase cost")
            costs.append(cost)
        winner = costs.index(min(costs))
        difference = p["budget_pence"] - costs[winner]
        require(answer["winner"] == winner, "Wrong paint choice")
        require(answer["affordable"] is (difference >= 0), "Wrong budget conclusion")
        require(answer["budget_difference_pence"] == difference, "Wrong budget difference")
        return True