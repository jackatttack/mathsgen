"""Right-angled trigonometry: finding sides, angles, perimeter and area.

The triangle is the same schematic shape the Pythagoras family draws, with
the right angle at the top left. Relative to the marked angle at the top
right, the horizontal side is adjacent, the vertical side is opposite, and
the slanted side is the hypotenuse.

Unlike Pythagoras, trigonometry has no exact integer answers in general, so
answers are rounded to one decimal place. The rounding is protected the
same way the quadratic-formula family protects it: any value close enough
to a rounding boundary to be ambiguous is rejected during construction,
rather than rounded on a guess.

The stated inputs are always exact integers, so every question is
reproducible and independently checkable even though its answer is not
exact.

Difficulty follows the reasoning: find a side, then find an angle, then
find a side and use it for the perimeter, then find a side and use it for
the area.
"""
import math
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .rounding import decimal_text
from . import figures


INFO = GeneratorInfo(
    id="geometry.trigonometry.right_angled", version=4,
    topic="geometry", subtopic="trigonometry",
    title="Trigonometry in right-angled triangles",
    difficulty_descriptions={
        1: "Find a missing side using sine, cosine or tangent.",
        2: "Find a missing angle using an inverse function.",
        3: "Find a missing side, then the perimeter.",
        4: "Find a missing side, then the area.",
    },
    tags=("geometry", "trigonometry", "sohcahtoa", "sides", "angles"),
)

# Angles that keep the triangle a sensible shape to draw and to reason about.
ANGLES = tuple(range(20, 71, 5))
# How close a value may sit to a rounding boundary before it is rejected.
BOUNDARY_MARGIN = 1e-6

TASKS = {
    "opposite": "the side opposite the marked angle",
    "adjacent": "the side adjacent to the marked angle",
    "hypotenuse": "the hypotenuse",
}


def sides_from(angle_degrees, known, known_length):
    """All three sides, as floats, from one side and the marked angle.

    The marked angle sits at the top right, so the vertical side is
    opposite it and the horizontal side is adjacent to it.
    """
    angle = math.radians(angle_degrees)
    if known == "hypotenuse":
        hypotenuse = float(known_length)
        opposite = hypotenuse * math.sin(angle)
        adjacent = hypotenuse * math.cos(angle)
    elif known == "adjacent":
        adjacent = float(known_length)
        opposite = adjacent * math.tan(angle)
        hypotenuse = adjacent / math.cos(angle)
    else:
        opposite = float(known_length)
        adjacent = opposite / math.tan(angle)
        hypotenuse = opposite / math.sin(angle)
    return {"opposite": opposite, "adjacent": adjacent, "hypotenuse": hypotenuse}


def rounded(value):
    """One decimal place, with the distance from the boundary reported."""
    scaled = value * 10
    nearest = math.floor(scaled + 0.5)
    distance = abs(scaled - (nearest - 0.5))
    return Fraction(nearest, 10), distance


def answer_value(p):
    """The exact float the answer rounds from."""
    angle = p["angle"]
    form = p["form"]

    if form == "find_angle":
        opposite = float(p["opposite"])
        adjacent = float(p["adjacent"])
        return math.degrees(math.atan2(opposite, adjacent))

    sides = sides_from(angle, p["known"], p["known_length"])

    if form == "find_side":
        return sides[p["wanted"]]
    if form == "perimeter":
        return sides["opposite"] + sides["adjacent"] + sides["hypotenuse"]
    return sides["opposite"] * sides["adjacent"] / 2


def presentation(p):
    form = p["form"]
    angle = p["angle"]

    if form == "find_angle":
        opposite = p["opposite"]
        adjacent = p["adjacent"]
        names = [str(adjacent) + " cm", str(opposite) + " cm", ""]
        angle_label = "x"
        instruction = (
            "Find the size of angle x. Give your answer to 1 decimal place."
        )
        fallback = (
            " The side opposite x is {} cm and the side adjacent to x is "
            "{} cm."
        ).format(opposite, adjacent)
    else:
        known = p["known"]
        known_length = p["known_length"]
        labels = {"opposite": "", "adjacent": "", "hypotenuse": ""}
        labels[known] = str(known_length) + " cm"
        if form == "find_side":
            labels[p["wanted"]] = "x"
            instruction = (
                "Find the length x. Give your answer to 1 decimal place."
            )
            fallback = (
                " The marked angle is {} degrees and {} is {} cm. "
                "x is {}."
            ).format(angle, TASKS[known], known_length, TASKS[p["wanted"]])
        elif form == "perimeter":
            instruction = (
                "Find the perimeter of the triangle. Give your answer to "
                "1 decimal place."
            )
            fallback = (
                " The marked angle is {} degrees and {} is {} cm."
            ).format(angle, TASKS[known], known_length)
        else:
            instruction = (
                "Find the area of the triangle. Give your answer to "
                "1 decimal place."
            )
            fallback = (
                " The marked angle is {} degrees and {} is {} cm."
            ).format(angle, TASKS[known], known_length)
        names = [labels["adjacent"], labels["opposite"], labels["hypotenuse"]]
        angle_label = str(angle) + "°"

    nodes = [
        {"type": "polygon", "points": [[70, 40], [285, 40], [70, 180]]},
        {"type": "right_angle", "vertex": [70, 40],
         "first": [285, 40], "second": [70, 180]},
    ]
    # Side labels sit where the Pythagoras family places them, so both
    # families draw an identical triangle.
    for point, text in (
        ([175, 20], names[0]), ([35, 110], names[1]), ([198, 127], names[2]),
    ):
        if text:
            nodes.append({"type": "label", "point": point, "text": text})
    # The marked angle sits inside the triangle at the top right, clear of
    # the hypotenuse: the layout smoke measured the first placement at nine
    # points from that line, which is the threshold it reports.
    nodes.append({"type": "label", "point": [236, 52], "text": angle_label})

    scene = {
        "kind": "scene", "version": 1, "width": 340, "height": 210,
        "caption": "Not drawn accurately", "nodes": nodes,
    }
    return (
        Content(instruction + fallback, display_text=instruction),
        (figures.orient_scene(scene, p["orientation"]),),
    )


def one_decimal_text(value):
    """Always show the decimal place, even when it is zero.

    decimal_text drops it, because 160/10 reduces to 16, but an answer
    given to one decimal place should read 16.0.
    """
    value = Fraction(value)
    tenths = int(value * 10)
    sign = "-" if tenths < 0 else ""
    tenths = abs(tenths)
    return "{}{}.{}".format(sign, tenths // 10, tenths % 10)


def answer_for(p):
    value, _ = rounded(answer_value(p))
    unit = {
        "find_angle": " degrees", "find_side": " cm",
        "perimeter": " cm", "area": " cm²",
    }[p["form"]]
    answer = {"kind": "rounded_measure", "value": rational_text(value)}
    return answer, Content(one_decimal_text(value) + unit)


class RightAngledTrigonometry:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng

        for attempt in range(400):
            if difficulty == 2:
                p = {
                    "form": "find_angle",
                    "opposite": rng.randint(3, 18),
                    "adjacent": rng.randint(3, 18),
                    "angle": 0,
                }
            else:
                known = rng.choice(("opposite", "adjacent", "hypotenuse"))
                p = {
                    "form": {
                        1: "find_side", 3: "perimeter", 4: "area",
                    }[difficulty],
                    "angle": rng.choice(ANGLES),
                    "known": known,
                    "known_length": rng.randint(4, 20),
                }
                if difficulty == 1:
                    p["wanted"] = rng.choice([
                        name for name in TASKS if name != known
                    ])

            if self.acceptable(p):
                break
        else:
            raise ValueError("Could not construct a suitable triangle")

        p["orientation"] = figures.choose_orientation(
            rng, lambda orientation: presentation(
                dict(p, orientation=orientation))[1][0])
        prompt, visuals = presentation(p)
        answer, display = answer_for(p)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=3 if difficulty <= 2 else 4, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=5),
            parameters=p, question_visuals=visuals,
        )
        self.validate(question)
        return question

    def acceptable(self, p):
        """Whether the answer rounds unambiguously and is a sensible size."""
        if p["form"] == "find_angle":
            if p["opposite"] == p["adjacent"]:
                # A 45 degree answer is fine, but it makes the triangle
                # isosceles and the diagram misleading at this shape.
                return False
        value = answer_value(p)
        if value <= 0 or value > 400:
            return False
        _, distance = rounded(value)
        if distance < BOUNDARY_MARGIN:
            return False
        return True

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid level")
        require(q.settings == {}, "Unsupported settings")

        p = q.parameters
        require(figures.valid_orientation(p.get("orientation")),
                "Unknown orientation")
        expected = {
            1: "find_side", 2: "find_angle", 3: "perimeter", 4: "area",
        }[level]
        require(p["form"] == expected, "Form does not match difficulty")

        if p["form"] == "find_angle":
            require(set(p) == {"form", "opposite", "adjacent", "angle",
                               "orientation"}, "Unexpected parameters")
            require(all(type(p[key]) is int for key in ("opposite", "adjacent")),
                    "Sides must be integers")
            require(3 <= p["opposite"] <= 18 and 3 <= p["adjacent"] <= 18,
                    "Sides outside bounds")
            require(p["opposite"] != p["adjacent"],
                    "Equal sides make the diagram misleading")
        else:
            keys = {"form", "angle", "known", "known_length", "orientation"}
            if p["form"] == "find_side":
                keys.add("wanted")
            require(set(p) == keys, "Unexpected parameters")
            require(p["angle"] in ANGLES, "Angle outside bounds")
            require(p["known"] in TASKS, "Unknown given side")
            require(type(p["known_length"]) is int
                    and 4 <= p["known_length"] <= 20,
                    "Given length outside bounds")
            if p["form"] == "find_side":
                require(p["wanted"] in TASKS, "Unknown requested side")
                require(p["wanted"] != p["known"],
                        "The requested side is the one already given")

        require(self.acceptable(p), "Answer does not round unambiguously")

        answer, display = answer_for(p)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Display mismatch")
        prompt, visuals = presentation(p)
        require(q.prompt == prompt, "Prompt mismatch")
        require(q.visual_assets("questions") == visuals, "Diagram mismatch")
        require(q.visual_assets("answers") == (), "Unexpected answer visuals")
        return True

    def validate_independently(self, q):
        """Rebuild the triangle from a different relationship.

        Where the generator reaches a side through one ratio, this check
        reaches it through another and through Pythagoras, so a wrong
        choice of sine against cosine does not survive. Angles are checked
        by taking a different inverse function of the same triangle.
        """
        p = q.parameters
        stated = Fraction(q.answer["value"])

        if p["form"] == "find_angle":
            opposite = float(p["opposite"])
            adjacent = float(p["adjacent"])
            hypotenuse = math.sqrt(opposite * opposite + adjacent * adjacent)
            # asin of opposite over hypotenuse, rather than atan.
            by_sine = math.degrees(math.asin(opposite / hypotenuse))
            by_cosine = math.degrees(math.acos(adjacent / hypotenuse))
            for candidate in (by_sine, by_cosine):
                require(abs(candidate - float(stated)) <= 0.05 + 1e-9,
                        "Independent inverse function disagrees")
            return True

        angle = math.radians(p["angle"])
        known = p["known"]
        length = float(p["known_length"])

        # Rebuild every side using Pythagoras from two of them, rather than
        # from the ratio the generator used.
        if known == "hypotenuse":
            opposite = length * math.sin(angle)
            adjacent = math.sqrt(length * length - opposite * opposite)
            hypotenuse = length
        elif known == "adjacent":
            hypotenuse = length / math.cos(angle)
            opposite = math.sqrt(hypotenuse * hypotenuse - length * length)
            adjacent = length
        else:
            hypotenuse = length / math.sin(angle)
            adjacent = math.sqrt(hypotenuse * hypotenuse - length * length)
            opposite = length

        if p["form"] == "find_side":
            expected = {
                "opposite": opposite, "adjacent": adjacent,
                "hypotenuse": hypotenuse,
            }[p["wanted"]]
        elif p["form"] == "perimeter":
            expected = opposite + adjacent + hypotenuse
        else:
            expected = opposite * adjacent / 2

        require(abs(expected - float(stated)) <= 0.05 + 1e-6,
                "Independent reconstruction disagrees")
        return True