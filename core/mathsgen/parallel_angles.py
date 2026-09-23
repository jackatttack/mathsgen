"""Parallel-line angles with explicit sectors and exact angle relationships."""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)
from . import figures

INFO = GeneratorInfo(
    id="geometry.angles.parallel_lines", version=2,
    topic="geometry", subtopic="angles",
    title="Angles in parallel lines",
    difficulty_descriptions={
        1: "Use corresponding or alternate angles.",
        2: "Use co-interior angles summing to 180 degrees.",
        3: "Use parallel lines, then the angle sum of a triangle.",
        4: "Form and solve an equation from algebraic angle labels.",
    },
    tags=("geometry", "angles", "parallel_lines", "equations"),
)


def expression(term):
    k, b = term
    if not k:
        return str(b)
    text = "x" if k == 1 else str(k) + "x"
    if b:
        text += (" + " if b > 0 else " - ") + str(abs(b))
    return text


def display_answer(value, level):
    if level == 4:
        return Content("x = " + str(value))
    return Content("x = {} degrees".format(value), str(value) + r"^{\circ}")


def expected(parameters):
    terms = parameters["terms"]
    relation = parameters["relation"]
    if relation in ("corresponding", "alternate"):
        a, b = terms
        return Fraction(b[1] - a[1], a[0] - b[0])
    return Fraction(
        180 - sum(t[1] for t in terms), sum(t[0] for t in terms)
    )


def presentation(parameters, level):
    relation = parameters["relation"]
    terms = parameters["terms"]
    upper, lower = [210, 180], [130, 60]
    nodes = [
        {"type": "line", "points": [[25, 180], [335, 180]]},
        {"type": "line", "points": [[25, 60], [335, 60]]},
        {"type": "parallel", "points": [[25, 180], [335, 180]],
         "position": 0.18},
        {"type": "parallel", "points": [[25, 60], [335, 60]],
         "position": 0.18},
        {"type": "line", "points": [[110, 30], [236, 219]]},
    ]

    def marked(center, start, sweep, position, term):
        nodes.append({
            "type": "arc", "center": center, "radius": 19,
            "start": start, "sweep": sweep,
        })
        text = expression(term)
        if term[0] and term[1]:
            text = "(" + text + ")"
        nodes.append({
            "type": "label", "point": position,
            "tex": text + r"^{\circ}",
        })

    if relation == "triangle":
        nodes.append({"type": "line", "points": [upper, [280, 60]]})
        marked(upper, 0, 56.31, [257, 202], terms[0])
        marked([280, 60], 120.26, 59.74, [248, 85], terms[1])
        marked(upper, 236.31, 63.95, [211, 141], terms[2])
        fallback = (
            " A corresponding angle of {} degrees gives one interior angle "
            "of the triangle. Another interior angle is {} degrees, and "
            "the remaining interior angle is x degrees."
        ).format(expression(terms[0]), expression(terms[1]))
    else:
        if relation == "corresponding":
            marked(upper, 0, 56.31, [257, 202], terms[0])
        else:
            marked(upper, 180, 56.31, [160, 152], terms[0])
        if relation == "cointerior":
            marked(lower, 56.31, 123.69, [82, 99], terms[1])
        else:
            marked(lower, 0, 56.31, [182, 84], terms[1])
        relationship = {
            "corresponding": "corresponding",
            "alternate": "alternate",
            "cointerior": "co-interior",
        }[relation]
        fallback = (
            " A transversal crosses the parallel lines. The marked "
            "angles are {} angles: one is {} degrees and the other "
            "is {} degrees."
        ).format(relationship, expression(terms[0]), expression(terms[1]))

    instruction = "The marked lines are parallel. Find x."
    if level == 4:
        instruction += " Angle expressions are in degrees."
    scene = {
        "kind": "scene", "version": 1, "width": 360, "height": 240,
        "caption": "Not drawn accurately", "nodes": nodes,
    }
    return (Content(instruction + fallback, display_text=instruction),
            figures.orient_scene(scene, parameters["orientation"]))


class ParallelAngles:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        if difficulty == 1:
            relation = rng.choice(("corresponding", "alternate"))
            value = rng.randint(35, 75)
            terms = [[0, value], [1, 0]]
        elif difficulty == 2:
            relation = "cointerior"
            known = rng.randint(35, 75)
            value = 180 - known
            terms = [[0, known], [1, 0]]
        elif difficulty == 3:
            relation = "triangle"
            first = rng.randint(35, 70)
            second = rng.randint(35, 65)
            value = 180 - first - second
            terms = [[0, first], [0, second], [1, 0]]
        else:
            relation = rng.choice(("alternate", "cointerior"))
            value = rng.randint(10, 20)
            k = rng.choice((2, 3))
            b = rng.randint(2, 12)
            first_angle = k * value + b
            other_angle = (
                first_angle if relation == "alternate" else 180 - first_angle
            )
            other_k = 1
            terms = [[k, b], [other_k, other_angle - other_k * value]]
        parameters = {"relation": relation, "terms": terms}
        parameters["orientation"] = figures.choose_orientation(
            rng, lambda orientation: presentation(
                dict(parameters, orientation=orientation), difficulty)[1])
        prompt, diagram = presentation(parameters, difficulty)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt,
            answer={"kind": "integer", "value": value},
            answer_display=display_answer(value, difficulty),
            worked_solution=(), marks=3 if difficulty >= 3 else 1,
            tags=self.info.tags, layout_hint=LayoutHint(working_lines=3),
            parameters=parameters, question_visuals=(diagram,),
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid level")
        require(q.settings == {}, "Unsupported settings")
        p = q.parameters
        require(set(p) == {"relation", "terms", "orientation"},
                "Unexpected parameters")
        require(figures.valid_orientation(p["orientation"]),
                "Unknown orientation")
        relation, terms = p["relation"], p["terms"]
        allowed = {
            1: ("corresponding", "alternate"),
            2: ("cointerior",),
            3: ("triangle",),
            4: ("alternate", "cointerior"),
        }
        require(relation in allowed[level], "Wrong angle relationship")
        require(
            isinstance(terms, list)
            and len(terms) == (3 if level == 3 else 2)
            and all(isinstance(t, list) and len(t) == 2
                    and all(type(v) is int for v in t) for t in terms),
            "Invalid angle expressions",
        )
        value = q.answer.get("value")
        require(type(value) is int and 0 < value < 180, "Invalid x")
        require(q.answer == {"kind": "integer", "value": value}, "Invalid answer")
        angles = [k * value + b for k, b in terms]
        require(all(0 < a < 180 for a in angles), "Invalid angle")
        if level in (1, 2):
            require(terms[0][0] == 0 and 35 <= terms[0][1] <= 75
                    and terms[1] == [1, 0], "Wrong direct structure")
        elif level == 3:
            require(terms[0][0] == terms[1][0] == 0
                    and 35 <= terms[0][1] <= 70
                    and 35 <= terms[1][1] <= 65
                    and terms[2] == [1, 0], "Wrong triangle structure")
        else:
            require(10 <= value <= 20 and terms[0][0] in (2, 3)
                    and 2 <= terms[0][1] <= 12 and terms[1][0] == 1
                    and terms[1][1] > 0, "Wrong algebraic structure")
        require(expected(p) == value, "Incorrect angle answer")
        prompt, diagram = presentation(p, level)
        require(q.prompt == prompt, "Prompt mismatch")
        require(q.visual_assets("questions") == (diagram,), "Diagram mismatch")
        require(not q.visual_assets("answers"), "Unexpected answer visuals")
        require(q.answer_display == display_answer(value, level),
                "Answer display mismatch")
        return True

    def validate_independently(self, q):
        """Solve the emitted angle constraints symbolically."""
        import sympy
        x = sympy.Symbol("x")
        angles = [k * x + b for k, b in q.parameters["terms"]]
        relation = q.parameters["relation"]
        if relation in ("corresponding", "alternate"):
            equation = angles[0] - angles[1]
        elif relation in ("cointerior", "triangle"):
            equation = sum(angles) - 180
        else:
            raise ValueError("Unknown angle relationship")
        solutions = sympy.solve(equation, x)
        require(solutions == [sympy.Integer(q.answer["value"])],
                "Independent angle solution disagrees")
        return True