"""Exact Pythagoras lengths, progressing to dependent two-triangle problems."""
from fractions import Fraction
from itertools import combinations

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .rounding import decimal_text
from . import figures


TRIPLES = ((3, 4, 5), (5, 12, 13), (8, 15, 17),
           (7, 24, 25), (20, 21, 29))
# Build pairs of right triangles sharing a perpendicular height.
TRIANGLES = sorted({
    (height * scale, base * scale, hyp * scale)
    for a, b, hyp in TRIPLES
    for height, base in ((a, b), (b, a))
    for scale in range(1, 5)
})
LINKED = tuple(
    (first[0], first[1], second[1], first[2], second[2])
    for first, second in combinations(TRIANGLES, 2)
    if first[0] == second[0] and first[1] != second[1]
)

INFO = GeneratorInfo(
    id="geometry.pythagoras.lengths", version=3,
    topic="geometry", subtopic="pythagoras",
    title="Pythagoras: find missing lengths",
    difficulty_descriptions={
        1: "Find the hypotenuse from two perpendicular sides.",
        2: "Find either shorter side from the hypotenuse and the other side.",
        3: "Find the hypotenuse using decimal lengths.",
        4: "Find a shared side, then use a second triangle to find a length or perimeter.",
    },
    tags=("geometry", "pythagoras", "lengths"),
)


LINKED_TASKS = ("second_hypotenuse", "second_base", "total_base", "perimeter")


def answer_name(parameters, level):
    if level < 4:
        return "x"
    return {
        "second_hypotenuse": "CD",
        "second_base": "BD",
        "total_base": "AD",
        "perimeter": "Perimeter",
    }[parameters["task"]]


def linked_result(parameters):
    height, left, right, hyp_left, hyp_right = parameters["linked"]
    return {
        "second_hypotenuse": hyp_right,
        "second_base": right,
        "total_base": left + right,
        "perimeter": left + right + hyp_left + hyp_right,
    }[parameters["task"]]


def presentation(parameters, level):
    nodes = []
    if level < 4:
        a, b, c = map(Fraction, parameters["sides"])
        missing = parameters["missing"]
        names = ["x" if i == missing else decimal_text(v) + " cm"
                 for i, v in enumerate((a, b, c))]
        nodes = [
            {"type": "polygon", "points": [[70, 40], [285, 40], [70, 180]]},
            {"type": "right_angle", "vertex": [70, 40],
             "first": [285, 40], "second": [70, 180]},
            {"type": "label", "point": [175, 20], "text": names[0]},
            {"type": "label", "point": [35, 110], "text": names[1]},
            {"type": "label", "point": [198, 127], "text": names[2]},
        ]
        instruction = "Calculate the length x in the right-angled triangle."
        if missing == 2:
            fallback = " Perpendicular sides: {} cm and {} cm; x is the hypotenuse."
            fallback = fallback.format(decimal_text(a), decimal_text(b))
        else:
            fallback = " Hypotenuse: {} cm; other perpendicular side: {} cm."
            known_side = b if missing == 0 else a
            fallback = fallback.format(decimal_text(c), decimal_text(known_side))
    else:
        height, left, right, hyp_left, hyp_right = parameters["linked"]
        task = parameters["task"]
        target = {
            "second_hypotenuse": "Calculate the length CD.",
            "second_base": "Calculate the length BD.",
            "total_base": "Calculate the total length AD.",
            "perimeter": "Calculate the perimeter of triangle ACD.",
        }[task]
        instruction = (
            "A, B and D lie on a straight line, with B between A and D. "
            "CB is perpendicular to AD. " + target
        )
        third_name, third_value = (
            ("BD", right) if task == "second_hypotenuse" else ("CD", hyp_right)
        )
        fallback = " AB = {} cm, AC = {} cm and {} = {} cm.".format(
            left, hyp_left, third_name, third_value
        )
        nodes = [
            {"type": "polygon", "points": [[40, 40], [180, 185], [320, 40]]},
            {"type": "line", "points": [[180, 40], [180, 185]], "dashed": True},
            {"type": "right_angle", "vertex": [180, 40],
             "first": [320, 40], "second": [180, 185]},
            {"type": "label", "point": [35, 22], "text": "A"},
            {"type": "label", "point": [180, 22], "text": "B"},
            {"type": "label", "point": [180, 204], "text": "C"},
            {"type": "label", "point": [325, 22], "text": "D"},
            {"type": "label", "point": [88, 124], "text": str(hyp_left) + " cm"},
            {"type": "label", "point": [105, 20], "text": str(left) + " cm"},
            {"type": "label", "point": [272, 124],
             "text": "?" if task == "second_hypotenuse" else str(hyp_right) + " cm"},
            {"type": "label", "point": [250, 20],
             "text": str(right) + " cm" if task == "second_hypotenuse" else "?"},
        ]
    spec = {
        "kind": "scene", "version": 1, "width": 360, "height": 225,
        "caption": "Not drawn accurately", "nodes": nodes,
    }
    return (Content(instruction + fallback, display_text=instruction),
            figures.orient_scene(spec, parameters["orientation"]))


class PythagorasLengths:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        if difficulty < 4:
            a, b, c = rng.choice(TRIPLES)
            if rng.choice((False, True)):
                a, b = b, a
            scale = rng.choice((Fraction(1, 2), Fraction(3, 2))) if difficulty == 3 else rng.randint(1, 4)
            sides = [Fraction(v) * scale for v in (a, b, c)]
            missing = rng.choice((0, 1)) if difficulty == 2 else 2
            result = sides[missing]
            parameters = {"sides": [rational_text(v) for v in sides], "missing": missing}
        else:
            linked = rng.choice(LINKED)
            parameters = {"linked": list(linked), "task": rng.choice(LINKED_TASKS)}
            result = Fraction(linked_result(parameters))
        parameters["orientation"] = figures.choose_orientation(
            rng, lambda orientation: presentation(
                dict(parameters, orientation=orientation), difficulty)[1])
        prompt, diagram = presentation(parameters, difficulty)
        name = answer_name(parameters, difficulty)
        display = "{} = {} cm".format(name, decimal_text(result))
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt,
            answer={"kind": "length", "value": rational_text(result), "unit": "cm"},
            answer_display=Content(display), worked_solution=(),
            marks=(5 if parameters.get("task") in ("total_base", "perimeter")
                   else 4) if difficulty == 4 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=4 if difficulty == 4 else 3),
            parameters=parameters, question_visuals=(diagram,),
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        require(isinstance(q.answer, dict) and q.answer.get("kind") == "length",
                "Unexpected answer shape")
        require(figures.valid_orientation(q.parameters.get("orientation")),
                "Unknown orientation")
        result = Fraction(q.answer["value"])
        require(result > 0 and q.answer == {
            "kind": "length", "value": rational_text(result), "unit": "cm"
        }, "Invalid length answer")
        if level < 4:
            raw = q.parameters["sides"]
            require(isinstance(raw, list) and len(raw) == 3, "Expected three sides")
            a, b, c = map(Fraction, raw)
            require(raw == [rational_text(v) for v in (a, b, c)], "Non-canonical sides")
            require(all(0 < v <= 116 for v in (a, b, c)), "Side outside bounds")
            require(a * a + b * b == c * c, "Not a right triangle")
            missing = q.parameters["missing"]
            require(type(missing) is int
                    and missing in ((0, 1) if level == 2 else (2,)),
                    "Wrong missing-side structure")
            require(result == (a, b, c)[missing], "Incorrect length")
            if level == 3:
                require(all((v * 2).denominator == 1 for v in (a, b, c))
                        and c.denominator == 2, "Expected decimal lengths and answer")
            else:
                require(all(v.denominator == 1 for v in (a, b, c)), "Expected integer lengths")
        else:
            linked = q.parameters["linked"]
            require(isinstance(linked, list) and tuple(linked) in LINKED,
                    "Unsupported linked-triangle configuration")
            height, left, right, hyp_left, hyp_right = linked
            require(left * left + height * height == hyp_left * hyp_left
                    and right * right + height * height == hyp_right * hyp_right,
                    "Linked triangles disagree")
            require(q.parameters.get("task") in LINKED_TASKS, "Unknown linked task")
            require(result == linked_result(q.parameters), "Incorrect linked-triangle answer")
        prompt, diagram = presentation(q.parameters, level)
        require(q.prompt == prompt, "Prompt mismatch")
        require(q.visual_assets("questions") == (diagram,), "Diagram mismatch")
        require(not q.visual_assets("answers"), "Unexpected answer assets")
        name = answer_name(q.parameters, level)
        require(q.answer_display == Content("{} = {} cm".format(name, decimal_text(result))),
                "Answer display mismatch")
        return True

    def validate_independently(self, q):
        """Calculate solely from the lengths given to the student."""
        import sympy

        if q.difficulty == 4:
            # Use only AB, AC and the third stated side. Neither the stored
            # shared height nor the stored unknown side enters this check.
            values = q.parameters["linked"]
            left = sympy.Rational(values[1])
            hyp_left = sympy.Rational(values[3])
            height_squared = hyp_left ** 2 - left ** 2
            require(height_squared > 0, "Invalid first triangle")
            task = q.parameters["task"]
            if task == "second_hypotenuse":
                right = sympy.Rational(values[2])
                expected = sympy.sqrt(height_squared + right ** 2)
            else:
                hyp_right = sympy.Rational(values[4])
                right_squared = hyp_right ** 2 - height_squared
                require(right_squared > 0, "Invalid second triangle")
                right = sympy.sqrt(right_squared)
                if task == "second_base":
                    expected = right
                elif task == "total_base":
                    expected = left + right
                elif task == "perimeter":
                    expected = left + right + hyp_left + hyp_right
                else:
                    raise ValueError("Unknown linked task")
        else:
            a, b, c = map(sympy.Rational, q.parameters["sides"])
            if q.difficulty == 2:
                known = b if q.parameters["missing"] == 0 else a
                expected = sympy.sqrt(c * c - known * known)
            else:
                expected = sympy.sqrt(a * a + b * b)
        require(expected == sympy.Rational(q.answer["value"]),
                "Independent Pythagoras answer disagrees")
        return True