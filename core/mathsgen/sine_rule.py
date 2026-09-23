"""Sine-rule questions with explicit ambiguity constraints and linked triangles.

Integer givens are authoritative. Intermediate lengths remain unrounded;
only the final answer is rounded to one decimal place.
"""
import math
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .trigonometry import one_decimal_text
from . import figures


INFO = GeneratorInfo(
    id="geometry.trigonometry.sine_rule", version=3,
    topic="geometry", subtopic="trigonometry",
    title="Sine rule: sides, angles and linked triangles",
    difficulty_descriptions={
        1: "Find a side from a known opposite pair and another angle.",
        2: "Find an acute angle from two sides and an opposite angle.",
        3: "Find an acute angle, then the third angle and remaining side.",
        4: "Find a shared side, then use the sine rule in another triangle.",
    },
    tags=("geometry", "trigonometry", "sine_rule"),
)


def sine(degrees):
    return math.sin(math.radians(degrees))


def rounded_value(value):
    """Reject either nearby rounding boundary, then store exact tenths."""
    require(math.isfinite(value) and value > 0, "Invalid result")
    scaled = value * 10
    fraction = scaled - math.floor(scaled)
    require(abs(fraction - 0.5) > 1e-6, "Near rounding boundary")
    return Fraction(math.floor(scaled + 0.5), 10)


def result(p, level):
    if level == 1:
        return p["a"] * sine(p["B"]) / sine(p["A"])
    if level in (2, 3):
        angle_b = math.degrees(math.asin(p["b"] * sine(p["A"]) / p["a"]))
        if level == 2:
            return angle_b
        return p["a"] * sine(180 - p["A"] - angle_b) / sine(p["A"])
    shared = p["AB"] * sine(p["A"]) / sine(p["C"])
    # ABC and CBD share BC. Their angles at B are supplementary.
    return shared * sine(p["A"] + p["C"]) / sine(p["D"])


def check_parameters(p, level):
    keys = {
        1: {"a", "A", "B"},
        2: {"a", "b", "A"},
        3: {"a", "b", "A"},
        4: {"AB", "A", "C", "D"},
    }[level] | {"orientation"}
    require(set(p) == keys, "Unexpected parameters")
    require(figures.valid_orientation(p["orientation"]),
            "Unknown orientation")
    require(all(type(value) is int for key, value in p.items()
                if key != "orientation"), "Integer givens required")
    if level == 1:
        require(5 <= p["a"] <= 20, "Side outside bounds")
        require(25 <= p["A"] <= 75 and 25 <= p["B"] <= 100,
                "Angle outside bounds")
        require(p["A"] != p["B"] and p["A"] + p["B"] <= 150,
                "Degenerate or trivial triangle")
    elif level in (2, 3):
        require(5 <= p["a"] <= 20 and 5 <= p["b"] <= 20,
                "Side outside bounds")
        require(p["a"] != p["b"] and 25 <= p["A"] <= 65,
                "Trivial or invalid givens")
        ratio = p["b"] * sine(p["A"]) / p["a"]
        require(0 < ratio < 1, "No acute solution")
        angle_b = math.degrees(math.asin(ratio))
        angle_c = 180 - p["A"] - angle_b
        require(20 <= angle_b <= 75 and 25 <= angle_c <= 125,
                "Triangle too narrow")
    else:
        require(5 <= p["AB"] <= 20, "Side outside bounds")
        require(25 <= p["A"] <= 55 and 30 <= p["C"] <= 60,
                "First triangle outside bounds")
        require(20 <= p["D"] <= 45, "Second triangle outside bounds")
        require(p["A"] != p["C"], "Shared side already equals given side")
        require(25 <= 180 - p["A"] - p["C"] - p["D"] <= 100,
                "Second triangle too narrow")
        require(p["A"] + p["C"] != p["D"], "Second step is trivial")
    value = result(p, level)
    require(1 <= value <= 100, "Result outside teaching bounds")
    rounded_value(value)


def presentation(p, level):
    """Keep angle givens in prose, with an uncluttered labelled diagram."""
    if level < 4:
        if level == 1:
            givens = (
                "In triangle ABC, BC = {a} cm, angle BAC = {A} degrees "
                "and angle ABC = {B} degrees. Find AC."
            ).format(**p)
            side_labels = [("BC", str(p["a"]) + " cm"), ("AC", "x")]
        else:
            givens = (
                "In triangle ABC, BC = {a} cm, AC = {b} cm "
                "and angle BAC = {A} degrees. Angle ABC is acute. "
            ).format(**p)
            givens += (
                "Find angle ABC." if level == 2 else "Find AB."
            )
            side_labels = [("BC", str(p["a"]) + " cm"),
                           ("AC", str(p["b"]) + " cm")]
            if level == 3:
                side_labels.append(("AB", "x"))
        nodes = [
            {"type": "polygon", "points": [[50, 40], [310, 40], [180, 185]]},
            {"type": "label", "point": [40, 22], "text": "A"},
            {"type": "label", "point": [320, 22], "text": "B"},
            {"type": "label", "point": [180, 207], "text": "C"},
        ]
        positions = {"AB": [180, 20], "AC": [83, 120], "BC": [277, 120]}
        for name, text in side_labels:
            nodes.append({"type": "label", "point": positions[name], "text": text})
        # Given angles sit inside their vertex; the unknown angle is x.
        angle_labels = [([94, 56], "{}°".format(p["A"]))]
        if level == 1:
            angle_labels.append(([266, 56], "{}°".format(p["B"])))
        elif level == 2:
            angle_labels.append(([266, 56], "x"))
        for point, text in angle_labels:
            nodes.append({"type": "label", "point": point, "text": text})
    else:
        givens = (
            "A, B and D lie on a straight line, with B between A and D. "
            "AB = {AB} cm, angle BAC = {A} degrees, angle ACB = {C} degrees "
            "and angle BDC = {D} degrees. Find CD."
        ).format(**p)
        # Adapt the existing Pythagoras linked scene without its right angle.
        nodes = [
            {"type": "polygon", "points": [[40, 40], [180, 185], [320, 40]]},
            {"type": "line", "points": [[150, 40], [180, 185]], "dashed": True},
            {"type": "label", "point": [30, 22], "text": "A"},
            {"type": "label", "point": [150, 22], "text": "B"},
            {"type": "label", "point": [180, 207], "text": "C"},
            {"type": "label", "point": [330, 22], "text": "D"},
            {"type": "label", "point": [92, 20], "text": str(p["AB"]) + " cm"},
            {"type": "label", "point": [280, 125], "text": "x"},
            # Angle ACB is narrow; this point clears both of its edges.
            {"type": "label", "point": [80, 54], "text": "{}°".format(p["A"])},
            {"type": "label", "point": [154, 140], "text": "{}°".format(p["C"])},
            {"type": "label", "point": [282, 54], "text": "{}°".format(p["D"])},
        ]
    prompt = Content(givens + " Give your answer to 1 decimal place.")
    scene = {
        "kind": "scene", "version": 1, "width": 360, "height": 230,
        "caption": "Not drawn accurately", "nodes": nodes,
    }
    return prompt, (figures.orient_scene(scene, p["orientation"]),)


def answer_for(p, level):
    value = rounded_value(result(p, level))
    unit = "degrees" if level == 2 else "cm"
    return (
        {"kind": "rounded_measure", "value": rational_text(value), "unit": unit},
        Content(one_decimal_text(value) + " " + unit),
    )


class SineRule:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        for attempt in range(500):
            if difficulty == 1:
                p = {"a": rng.randint(5, 20),
                     "A": rng.randrange(25, 76, 5),
                     "B": rng.randrange(25, 101, 5)}
            elif difficulty in (2, 3):
                p = {"a": rng.randint(5, 20), "b": rng.randint(5, 20),
                     "A": rng.randrange(25, 66, 5)}
            else:
                p = {"AB": rng.randint(5, 20),
                     "A": rng.randrange(25, 56, 5),
                     "C": rng.randrange(30, 61, 5),
                     "D": rng.randrange(20, 46, 5)}
            p["orientation"] = [0, False]
            try:
                check_parameters(p, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a suitable sine-rule question")
        p["orientation"] = figures.choose_orientation(
            rng, lambda orientation: presentation(
                dict(p, orientation=orientation), difficulty)[1][0])
        prompt, visuals = presentation(p, difficulty)
        answer, display = answer_for(p, difficulty)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=3 if difficulty <= 2 else 5, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=5),
            parameters=p, question_visuals=visuals,
        )
        self.validate(question)
        return question

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        require(type(q.difficulty) is int and q.difficulty in (1, 2, 3, 4),
                "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        check_parameters(q.parameters, q.difficulty)
        answer, display = answer_for(q.parameters, q.difficulty)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Answer display mismatch")
        prompt, visuals = presentation(q.parameters, q.difficulty)
        require(q.prompt == prompt, "Prompt mismatch")
        require(q.visual_assets("questions") == visuals, "Diagram mismatch")
        require(q.visual_assets("answers") == (), "Unexpected answer visuals")
        return True

    def validate_independently(self, q):
        """Reconstruct using ray intersection or projection and Pythagoras.

        No production result or sine-rule calculation is used here.
        """
        p, level = q.parameters, q.difficulty

        def intersection_side(base, left_angle, right_angle):
            # Place the base on the x-axis. Intersect rays from its ends.
            left = math.radians(left_angle)
            right = math.radians(right_angle)
            numerator = base * math.sin(right)
            determinant = (
                math.cos(left) * math.sin(right)
                + math.sin(left) * math.cos(right)
            )
            distance = numerator / determinant
            return distance * math.cos(left), distance * math.sin(left)

        if level == 1:
            # Base BC, left angle B, right angle C; distance CA is requested.
            x, y = intersection_side(p["a"], p["B"], 180 - p["A"] - p["B"])
            expected = math.hypot(p["a"] - x, y)
        elif level in (2, 3):
            # A=(0,0), C=(b*cos A,b*sin A), B=(c,0).
            x = p["b"] * math.cos(math.radians(p["A"]))
            y = p["b"] * math.sin(math.radians(p["A"]))
            horizontal = math.sqrt(p["a"] ** 2 - y ** 2)
            # The positive projection selects the explicitly acute angle B.
            expected = (
                math.degrees(math.atan2(y, horizontal))
                if level == 2 else x + horizontal
            )
        else:
            # Recover C from base AB, then intersect CD with the baseline.
            x, y = intersection_side(
                p["AB"], p["A"], 180 - p["A"] - p["C"]
            )
            horizontal = y / math.tan(math.radians(p["D"]))
            d_x = x + horizontal
            require(d_x > p["AB"], "D is not beyond B")
            expected = math.hypot(horizontal, y)
        stated = Fraction(q.answer["value"])
        require((stated * 10).denominator == 1, "Answer is not exact tenths")
        require(abs(expected - float(stated)) < 0.05,
                "Independent coordinate reconstruction disagrees")
        return True