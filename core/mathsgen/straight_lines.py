"""Straight-line graphs, point membership, equations from points and intersections."""
from fractions import Fraction
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)


INFO = GeneratorInfo(
    id="algebra.graphs.straight_lines", version=2,
    topic="algebra", subtopic="straight_line_graphs",
    title="Straight-line graphs and equations",
    difficulty_descriptions={
        1: "Draw a line given its equation in y = mx + c form.",
        2: "Find the equation of a displayed line, including fractional gradients.",
        3: "Check point membership or find a line from two plotted points.",
        4: "Rearrange a line equation or find where two lines intersect.",
    },
    tags=("graphs", "linear", "gradient", "intercept", "coordinates"),
)


def linear_text(m, c, tex=False):
    formatter = rational_tex if tex else rational_text
    if m == 1:
        result = "x"
    elif m == -1:
        result = "-x"
    else:
        coefficient = formatter(m)
        if not tex and m.denominator != 1:
            coefficient = "(" + coefficient + ")"
        result = coefficient + "x"
    if c:
        result += (" - " if c < 0 else " + ") + formatter(abs(c))
    return "y = " + result


def implicit_text(a, b, total):
    first = ("-" if a == -1 else "" if a == 1 else str(a)) + "x"
    return first + " + " + str(b) + "y = " + str(total)


def plot(m=None, c=None):
    visual = {
        "kind": "plot", "version": 1,
        "x_range": [-6, 6], "y_range": [-8, 8],
        "x_step": 2, "y_step": 2,
        "minor_divisions": 2, "equal_units": False,
        "x_label": "x", "y_label": "y",
    }
    if m is not None:
        visual["curves"] = [{"segments": [[
            [-6, float(-6 * m + c)], [6, float(6 * m + c)],
        ]]}]
    return visual


def plot_two(m1, c1, m2, c2):
    visual = plot(m1, c1)
    visual["curves"].append(plot(m2, c2)["curves"][0])
    return visual


def presentation(parameters, level):
    if parameters.get("form") == "two_points":
        first, second = parameters["points"]
        instruction = (
            "The points ({}, {}) and ({}, {}) are marked on the grid. "
            "Draw the straight line through them and find its equation."
        ).format(first[0], first[1], second[0], second[1])
        answer = answer_for(parameters, level)[0]
        m, c = Fraction(answer["m"]), Fraction(answer["c"])
        student, teacher = plot(), plot(m, c)
        student["points"] = [list(first), list(second)]
        teacher["points"] = [list(first), list(second)]
        return Content(instruction), (student,), (teacher,)

    if parameters.get("form") == "intersection":
        (m1, c1), (m2, c2) = parameters["lines"]
        m1, c1, m2, c2 = map(Fraction, (m1, c1, m2, c2))
        first, second = linear_text(m1, c1), linear_text(m2, c2)
        instruction = (
            "The two lines on the grid have equations {} and {}. "
            "Find the coordinates of their intersection."
        ).format(first, second)
        student = plot_two(m1, c1, m2, c2)
        teacher = plot_two(m1, c1, m2, c2)
        intersection = answer_for(parameters, level)[0]
        teacher["points"] = [[intersection["x"], intersection["y"]]]
        return Content(instruction), (student,), (teacher,)

    if level == 4:
        a, b, total = parameters["implicit"]
        equation = implicit_text(a, b, total)
        instruction = "Find the gradient and the y-intercept of this line."
        return Content(
            instruction + " " + equation, equation, display_text=instruction,
        ), (), ()

    m, c = map(Fraction, (parameters["m"], parameters["c"]))
    if level == 1:
        instruction = "Draw the following straight line on the grid."
        return Content(
            instruction + " " + linear_text(m, c),
            linear_text(m, c, True), display_text=instruction,
        ), (plot(),), (plot(m, c),)
    if level == 2:
        # CLI gets exact points because it cannot display the graph.
        first, second = (0, c), (2, 2 * m + c)
        fallback = "The displayed line passes through (0, {}) and (2, {}).".format(
            rational_text(first[1]), rational_text(second[1])
        )
        return Content(
            "Find the equation of the line. " + fallback,
            display_text="Find the equation of the line shown.",
        ), (plot(m, c),), ()
    x, y = parameters["point"]
    instruction = (
        "Does the point ({}, {}) lie on this line? "
        "Show your substitution to justify your answer."
    ).format(x, y)
    return Content(
        instruction + " " + linear_text(m, c),
        linear_text(m, c, True), display_text=instruction,
    ), (), ()


def answer_for(parameters, level):
    if parameters.get("form") == "two_points":
        (x1, y1), (x2, y2) = parameters["points"]
        m = Fraction(y2 - y1, x2 - x1)
        c = Fraction(y1) - m * x1
        answer = {"kind": "linear_equation",
                  "m": rational_text(m), "c": rational_text(c)}
        return answer, Content(linear_text(m, c), linear_text(m, c, True))

    if parameters.get("form") == "intersection":
        (m1, c1), (m2, c2) = parameters["lines"]
        m1, c1, m2, c2 = map(Fraction, (m1, c1, m2, c2))
        x = (c2 - c1) / (m1 - m2)
        y = m1 * x + c1
        require(x.denominator == y.denominator == 1,
                "Expected an integer intersection")
        answer = {"kind": "point", "x": int(x), "y": int(y)}
        return answer, Content("The lines meet at ({}, {}).".format(x, y))

    if level == 4:
        a, b, total = parameters["implicit"]
        m, c = Fraction(-a, b), Fraction(total, b)
    else:
        m, c = Fraction(parameters["m"]), Fraction(parameters["c"])
    if level == 3:
        x, y = parameters["point"]
        evaluated = m * x + c
        on_line = evaluated == y
        answer = {
            "kind": "point_membership", "on_line": on_line,
            "evaluated_y": rational_text(evaluated),
        }
        display = Content(
            "{}. When x = {}, the line gives y = {}, which {} {}.".format(
                "Yes" if on_line else "No", x, rational_text(evaluated),
                "equals" if on_line else "does not equal", y,
            )
        )
        return answer, display
    answer = {"kind": "linear_equation", "m": rational_text(m), "c": rational_text(c)}
    if level == 4:
        display = Content(
            "Gradient = {}; y-intercept = {}. {}".format(
                rational_text(m), rational_text(c), linear_text(m, c)
            ),
        )
    else:
        display = Content(linear_text(m, c), linear_text(m, c, True))
    return answer, display


class StraightLines:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        if difficulty == 3 and rng.random() < 0.5:
            for _ in range(200):
                x1, x2 = rng.choice((-3, -2, -1)), rng.choice((1, 2, 3))
                m = rng.choice((-2, -1, 1, 2))
                c = rng.choice((-3, -2, -1, 1, 2, 3))
                y1, y2 = m * x1 + c, m * x2 + c
                if -8 <= y1 <= 8 and -8 <= y2 <= 8:
                    parameters = {"form": "two_points",
                                  "points": [[x1, y1], [x2, y2]]}
                    break
            else:
                raise ValueError("Could not place two points on the grid")
        elif difficulty == 4 and rng.random() < 0.5:
            for _ in range(200):
                m1, m2 = rng.choice((1, 2)), rng.choice((-1, -2))
                x = rng.choice((-2, -1, 1, 2))
                y = rng.randint(-3, 3)
                c1, c2 = y - m1 * x, y - m2 * x
                if -4 <= c1 <= 4 and -4 <= c2 <= 4:
                    parameters = {
                        "form": "intersection",
                        "lines": [[str(m1), str(c1)], [str(m2), str(c2)]],
                    }
                    break
            else:
                raise ValueError("Could not place an intersection on the grid")
        elif difficulty == 4:
            b = rng.randint(2, 6)
            a = rng.choice([v for v in range(-9, 10) if v and gcd(abs(v), b) == 1])
            total = rng.choice([v for v in range(-12, 13) if v])
            parameters = {"implicit": [a, b, total]}
        else:
            pool = (-3, -2, -1, 1, 2, 3) if difficulty == 1 else (
                Fraction(-3, 2), -1, Fraction(-1, 2),
                Fraction(1, 2), 1, Fraction(3, 2),
            )
            m, c = Fraction(rng.choice(pool)), Fraction(rng.randint(-3, 3))
            parameters = {"m": rational_text(m), "c": rational_text(c)}
            if difficulty == 3:
                x = rng.choice((-6, -4, -2, 2, 4, 6))
                actual = m * x + c
                offset = 0 if rng.choice((False, True)) else rng.choice((-3, -2, -1, 1, 2, 3))
                parameters["point"] = [x, int(actual) + offset]

        prompt, student, teacher = presentation(parameters, difficulty)
        answer, display = answer_for(parameters, difficulty)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=4 if parameters.get("form") == "intersection" else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(
                working_lines=0 if difficulty == 1 else
                5 if parameters.get("form") in ("two_points", "intersection") else 3
            ),
            parameters=parameters, question_visuals=student, answer_visuals=teacher,
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        p = q.parameters
        if p.get("form") == "two_points":
            require(level == 3 and set(p) == {"form", "points"},
                    "Unexpected two-point parameters")
            points = p["points"]
            require(isinstance(points, list) and len(points) == 2
                    and all(isinstance(point, list) and len(point) == 2
                            and all(type(value) is int for value in point)
                            for point in points), "Invalid plotted points")
            (x1, y1), (x2, y2) = points
            require(x1 in (-3, -2, -1) and x2 in (1, 2, 3)
                    and -8 <= y1 <= 8 and -8 <= y2 <= 8,
                    "Points outside the grid")
            m = Fraction(y2 - y1, x2 - x1)
            c = Fraction(y1) - m * x1
            require(m in (-2, -1, 1, 2) and c in (-3, -2, -1, 1, 2, 3),
                    "Line outside two-point bounds")
        elif p.get("form") == "intersection":
            require(level == 4 and set(p) == {"form", "lines"},
                    "Unexpected intersection parameters")
            lines = p["lines"]
            require(isinstance(lines, list) and len(lines) == 2
                    and all(isinstance(line, list) and len(line) == 2
                            and all(type(value) is str for value in line)
                            for line in lines), "Invalid line equations")
            (m1, c1), (m2, c2) = lines
            require(m1 in ("1", "2") and m2 in ("-1", "-2"),
                    "Gradients outside bounds")
            require(c1 in tuple(map(str, range(-4, 5)))
                    and c2 in tuple(map(str, range(-4, 5))),
                    "Intercepts outside bounds")
            x = Fraction(int(c2) - int(c1), int(m1) - int(m2))
            y = int(m1) * x + int(c1)
            require(x in (-2, -1, 1, 2)
                    and y.denominator == 1 and -3 <= y <= 3,
                    "Intersection outside grid bounds")
        elif level == 4:
            require(set(p) == {"implicit"}, "Unexpected parameters")
            values = p["implicit"]
            require(isinstance(values, list) and len(values) == 3
                    and all(type(v) is int for v in values), "Expected integer equation")
            a, b, total = values
            require(1 <= abs(a) <= 9 and 2 <= b <= 6
                    and gcd(abs(a), b) == 1 and 1 <= abs(total) <= 12,
                    "Equation outside difficulty bounds")
        else:
            require(set(p) == ({"m", "c", "point"} if level == 3 else {"m", "c"}),
                    "Unexpected parameters")
            m, c = Fraction(p["m"]), Fraction(p["c"])
            require(p["m"] == rational_text(m) and p["c"] == rational_text(c),
                    "Non-canonical coefficients")
            allowed = tuple(map(Fraction, (-3, -2, -1, 1, 2, 3))) if level == 1 else (
                Fraction(-3, 2), -1, Fraction(-1, 2),
                Fraction(1, 2), 1, Fraction(3, 2),
            )
            require(m in allowed and c.denominator == 1 and -3 <= c <= 3,
                    "Coefficients outside difficulty bounds")
            if level == 3:
                point = p["point"]
                require(isinstance(point, list) and len(point) == 2
                        and all(type(v) is int for v in point), "Invalid point")
                x, y = point
                require(x in (-6, -4, -2, 2, 4, 6)
                        and y - (m * x + c) in range(-3, 4), "Point outside bounds")
        answer, display = answer_for(p, level)
        require(q.answer == answer, "Incorrect answer")
        if level == 3 and "point" in p:
            require(type(q.answer["on_line"]) is bool, "Membership must be boolean")
        require(q.answer_display == display, "Display mismatch")
        prompt, student, teacher = presentation(p, level)
        require(q.prompt == prompt, "Prompt mismatch")
        require(q.visual_assets("questions") == student, "Student graph mismatch")
        require(q.visual_assets("answers") == teacher, "Answer graph mismatch")
        return True

    def validate_independently(self, q):
        import sympy

        if q.parameters.get("form") == "two_points":
            (x1, y1), (x2, y2) = q.parameters["points"]
            m = sympy.Rational(q.answer["m"])
            c = sympy.Rational(q.answer["c"])
            require(m * x1 + c == y1 and m * x2 + c == y2,
                    "Independent two-point equation disagrees")
            return True
        if q.parameters.get("form") == "intersection":
            (m1, c1), (m2, c2) = q.parameters["lines"]
            x, y = map(sympy.Integer, (q.answer["x"], q.answer["y"]))
            require(y == sympy.Rational(m1) * x + sympy.Rational(c1)
                    and y == sympy.Rational(m2) * x + sympy.Rational(c2),
                    "Independent intersection disagrees")
            return True
        if q.difficulty == 4:
            a, b, total = map(sympy.Integer, q.parameters["implicit"])
            m = sympy.Rational(q.answer["m"])
            c = sympy.Rational(q.answer["c"])
            # The submitted line must satisfy the given equation identically.
            x = sympy.Symbol("x")
            require(sympy.expand(a * x + b * (m * x + c) - total) == 0,
                    "Independent rearrangement disagrees")
            return True
        m, c = map(sympy.Rational, (q.parameters["m"], q.parameters["c"]))
        if q.difficulty == 3:
            x, y = q.parameters["point"]
            residual = y - m * x - c
            require(q.answer["on_line"] == bool(residual == 0),
                    "Independent point membership disagrees")
            require(sympy.Rational(q.answer["evaluated_y"]) == y - residual,
                    "Independent substituted value disagrees")
        else:
            submitted_m = sympy.Rational(q.answer["m"])
            submitted_c = sympy.Rational(q.answer["c"])
            # Two distinct points uniquely determine this nonvertical line.
            for x in (-2, 2):
                require(submitted_m * x + submitted_c == m * x + c,
                        "Independent line substitution disagrees")
        return True