"""Construct independent linear equations around exact chosen solutions."""
from fractions import Fraction
from math import gcd

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)


def term(coefficient, letter):
    """One term, without a redundant coefficient of one."""
    if coefficient == 1:
        return letter
    if coefficient == -1:
        return "-" + letter
    return str(coefficient) + letter


def equation(a, b, total):
    return "{} + {} = {}".format(term(a, "x"), term(b, "y"), rational_text(total))


def rearranged_equation(a, b, total, layout):
    """Write the same equation with terms on both sides.

    The mathematics is unchanged: only which terms sit on which side of the
    equals sign differs, so the student must collect them before
    eliminating. "y_left" moves the y term across; "constant_left" moves
    the constant across instead.
    """
    if layout == "y_left":
        # ax = total - by, with the sign written once rather than as a
        # plus followed by a negative term.
        return "{} = {} {} {}".format(
            term(a, "x"), rational_text(total),
            "-" if b > 0 else "+", term(abs(b), "y"),
        )
    if layout == "x_right":
        # by = total - ax, written with the x term on the right.
        return "{} = {} {} {}".format(
            term(b, "y"), rational_text(total),
            "-" if a > 0 else "+", term(abs(a), "x"),
        )
    # constant_left: total - by = ax
    return "{} {} {} = {}".format(
        rational_text(total), "-" if b > 0 else "+",
        term(abs(b), "y"), term(a, "x"),
    )


def prompt(rows, layouts=None):
    if layouts:
        equations = [
            rearranged_equation(*row, layout=layout)
            for row, layout in zip(rows, layouts)
        ]
        instruction = (
            "Rearrange each equation, then solve them simultaneously "
            "for x and y."
        )
    else:
        equations = [equation(*row) for row in rows]
        instruction = "Solve these simultaneous equations for x and y."
    return Content(
        instruction + " " + "; ".join(equations),
        r"\qquad ".join(equations),
        display_text=instruction,
    )


def answer_display(x, y):
    return Content(
        "x = {}; y = {}".format(rational_text(x), rational_text(y)),
        "x = " + rational_tex(x) + r",\quad y = " + rational_tex(y),
    )


def coefficient_choices(level):
    """Small primitive rows keep elimination deliberate and manageable."""
    if level == 1:
        return [(a, 1, c, 1) for a in range(1, 7)
                for c in range(1, 7) if a != c]
    if level == 2:
        return [(a, 1, c, d) for a in range(1, 6)
                for c in range(2, 8) for d in range(2, 5)
                if gcd(c, d) == 1 and a * d != c]
    values = (2, 3, 4, 5, 7) if level == 3 else (3, 5, 7)
    rows = [(a, b) for a in values for b in values if gcd(a, b) == 1]
    return [
        (a, b, c, d) for a, b in rows for c, d in rows
        if a * d != b * c
        and a % c != 0 and c % a != 0
        and b % d != 0 and d % b != 0
    ]


COEFFICIENTS = {level: tuple(coefficient_choices(level)) for level in (1, 2, 3, 4)}


class SimultaneousLinear:
    info = GeneratorInfo(
        id="algebra.simultaneous.linear",
        version=2,
        topic="algebra",
        subtopic="simultaneous_equations",
        title="Solve simultaneous linear equations",
        difficulty_descriptions={
            1: "Matching y coefficients; or a sum-and-difference or shop problem.",
            2: "Scale one equation to eliminate y; or form the equations from a shop problem.",
            3: "Scale both equations; or form them from ticket prices or a coin jar.",
            4: "Collect terms before eliminating; or form, solve and use both values in context.",
        },
        tags=("algebra", "simultaneous", "elimination"),
    )

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        from . import simultaneous_contexts as worded_forms
        if rng.random() < worded_forms.CONTEXT_SHARE.get(difficulty, 0.0):
            return worded_forms.generate(self, context)
        a, b, c, d = rng.choice(COEFFICIENTS[difficulty])
        if difficulty == 1:
            values = [Fraction(n) for n in range(1, 10)]
            solutions = [(x, y) for x in values for y in values]
        else:
            # Every level now uses integer solutions. Half-integers were
            # tried at level 3, but its coefficient set only yields whole
            # constants for integer solutions: the old level 4 had its own
            # coefficients chosen for halves, and that level is now a
            # rearrangement task with integer answers by request.
            values = [Fraction(n) for n in range(1, 10)]
            solutions = [(x, -y) for x in values for y in values]
            solutions += [(-x, y) for x in values for y in values]
        solutions = [
            (x, y) for x, y in solutions
            if a * x + b * y != 0 and c * x + d * y != 0
        ]
        require(bool(solutions), "No suitable solutions for coefficient matrix")
        x, y = rng.choice(solutions)
        first_total = a * x + b * y
        second_total = c * x + d * y
        require(first_total.denominator == 1 and second_total.denominator == 1,
                "Constants must be whole numbers")
        rows = [
            [a, b, int(first_total)],
            [c, d, int(second_total)],
        ]
        # Level 4 states each equation with terms on both sides, so the
        # student must collect them into standard form first.
        layouts = (
            [rng.choice(("y_left", "x_right", "constant_left")) for _ in rows]
            if difficulty == 4 else None
        )
        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=prompt(rows, layouts),
            answer={
                "kind": "variable_values",
                "values": {"x": rational_text(x), "y": rational_text(y)},
            },
            answer_display=answer_display(x, y),
            worked_solution=(),
            marks=3 if difficulty < 3 else 4,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=8),
            parameters=(
                {"rows": rows, "layouts": layouts} if layouts
                else {"rows": rows}
            ),
        )
        self.validate(question)
        return question

    def validate(self, question):
        from .worded import is_worded
        if is_worded(question):
            from .simultaneous_contexts import validate as validate_worded
            return validate_worded(self, question)
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in COEFFICIENTS, "Invalid difficulty")
        require(not question.settings, "Unexpected settings")
        rows = question.parameters["rows"]
        require(len(rows) == 2 and all(len(row) == 3 for row in rows),
                "Expected two linear equations")
        require(all(type(value) is int for row in rows for value in row),
                "Expected integer coefficients and constants")
        a, b, total_one = rows[0]
        c, d, total_two = rows[1]
        require(a * d - b * c != 0, "Equations are not independent")
        require((a, b, c, d) in COEFFICIENTS[level],
                "Coefficients violate difficulty structure")
        require(all(0 < abs(total) <= 120 for total in (total_one, total_two)),
                "Constants outside intended bounds")
        require(
            isinstance(question.answer, dict)
            and question.answer.get("kind") == "variable_values"
            and isinstance(question.answer.get("values"), dict)
            and set(question.answer["values"]) == {"x", "y"},
            "Unexpected answer shape",
        )
        values = question.answer["values"]
        x, y = Fraction(values["x"]), Fraction(values["y"])
        expected = {
            "kind": "variable_values",
            "values": {"x": rational_text(x), "y": rational_text(y)},
        }
        require(question.answer == expected, "Noncanonical answer")
        require(a * x + b * y == total_one, "Answer fails first equation")
        require(c * x + d * y == total_two, "Answer fails second equation")
        if level == 1:
            require(x.denominator == y.denominator == 1 and
                    1 <= x <= 9 and 1 <= y <= 9, "Expected positive integers")
        elif level == 2:
            require(x.denominator == y.denominator == 1 and
                    x * y < 0 and max(abs(x), abs(y)) <= 9,
                    "Expected bounded opposite-sign integers")
        elif level == 3:
            require(x.denominator == y.denominator == 1 and
                    x * y < 0 and max(abs(x), abs(y)) <= 9,
                    "Expected bounded opposite-sign integers")
        else:
            require(x.denominator == y.denominator == 1 and
                    x * y < 0 and max(abs(x), abs(y)) <= 9,
                    "Expected bounded opposite-sign integers")
        layouts = question.parameters.get("layouts")
        require(bool(layouts) == (level == 4),
                "Only level 4 states rearranged equations")
        if layouts:
            require(len(layouts) == 2, "Each equation needs a layout")
            require(all(value in ("y_left", "x_right", "constant_left")
                        for value in layouts), "Unknown layout")
        require(question.prompt == prompt(rows, layouts), "Prompt mismatch")
        require(question.answer_display == answer_display(x, y), "Display mismatch")
        return True

    def validate_independently(self, question):
        """Recover the unique solution with determinants, not substitution."""
        from .worded import is_worded
        if is_worded(question):
            from .simultaneous_contexts import validate_independently as independent_worded
            return independent_worded(question)
        a, b, first = question.parameters["rows"][0]
        c, d, second = question.parameters["rows"][1]
        determinant = a * d - b * c
        require(determinant != 0, "Singular coefficient matrix")
        recovered = {
            "x": Fraction(first * d - b * second, determinant),
            "y": Fraction(a * second - first * c, determinant),
        }
        submitted = {
            key: Fraction(value) for key, value in question.answer["values"].items()
        }
        require(recovered == submitted, "Independent determinant solution disagrees")
        return True