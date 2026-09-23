"""Linear inequalities, including the reversal caused by dividing by a
negative, and the integer solutions of a double inequality.

Difficulty changes the reasoning required, not the size of the numbers:
level 1 is a two-step solve, level 2 collects unknowns from both sides,
level 3 forces the direction to reverse, and level 4 asks for the integer
solutions of a double inequality instead of an algebraic solution.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, rational_tex, require,
)


# --- Presentation of the four relations -----------------------------------
# Plain text is the CLI fallback; the TeX form is used for PDF rendering.
OPERATOR_TEX = {"<": "<", "<=": r"\leq", ">": ">", ">=": r"\geq"}
REVERSED = {"<": ">", "<=": ">=", ">": "<", ">=": "<="}

FORMS = {1: "simple", 2: "both_sides", 3: "negative", 4: "double"}

EXPECTED_KEYS = {
    "simple": {"form", "variable", "coefficient", "constant", "target", "operator"},
    "negative": {"form", "variable", "coefficient", "constant", "target", "operator"},
    "both_sides": {
        "form", "variable", "left_coefficient", "left_constant",
        "right_coefficient", "right_constant", "operator",
    },
    "double": {
        "form", "variable", "coefficient", "constant",
        "lower", "upper", "lower_operator", "upper_operator",
    },
}


INFO = GeneratorInfo(
    id="algebra.inequalities.linear", version=2,
    topic="algebra", subtopic="inequalities",
    title="Solve linear inequalities",
    difficulty_descriptions={
        1: "Solve a two-step inequality; or the greatest whole number within a budget.",
        2: "Collect unknowns from both sides; or the least whole number exceeding a target.",
        3: "Divide by a negative so the direction reverses; or a falling quantity crossing a threshold.",
        4: "List the integer solutions of a double inequality, bare or from a context.",
    },
    tags=("inequalities", "linear", "solving", "integers"),
)


def term(coefficient, variable):
    """Write a single algebraic term without a redundant coefficient of one."""
    if coefficient == 1:
        return variable
    if coefficient == -1:
        return "-" + variable
    return str(coefficient) + variable


def linear_side(coefficient, constant, variable):
    text = term(coefficient, variable)
    if constant:
        text += (" - " if constant < 0 else " + ") + str(abs(constant))
    return text


def subtracted_side(constant, coefficient, variable):
    """Write the form that makes the unknown's coefficient negative."""
    return str(constant) + " - " + term(coefficient, variable)


def relation_text(left, operator, right, tex=False):
    symbol = OPERATOR_TEX[operator] if tex else operator
    return "{} {} {}".format(left, symbol, right)


def satisfies(left, operator, right):
    return left < right if operator == "<" else left <= right


def sides(parameters):
    """Return the displayed left and right sides of a single inequality."""
    variable = parameters["variable"]
    form = parameters["form"]
    if form == "simple":
        left = linear_side(parameters["coefficient"], parameters["constant"], variable)
        return left, str(parameters["target"])
    if form == "negative":
        left = subtracted_side(
            parameters["constant"], parameters["coefficient"], variable
        )
        return left, str(parameters["target"])
    left = linear_side(
        parameters["left_coefficient"], parameters["left_constant"], variable
    )
    right = linear_side(
        parameters["right_coefficient"], parameters["right_constant"], variable
    )
    return left, right


def presentation(parameters):
    variable = parameters["variable"]
    if parameters["form"] == "double":
        middle = linear_side(
            parameters["coefficient"], parameters["constant"], variable
        )
        instruction = (
            "{} is an integer. List all the values of {} "
            "that satisfy this inequality."
        ).format(variable, variable)
        plain = "{} {} {} {} {}".format(
            parameters["lower"], parameters["lower_operator"], middle,
            parameters["upper_operator"], parameters["upper"],
        )
        maths = "{} {} {} {} {}".format(
            parameters["lower"], OPERATOR_TEX[parameters["lower_operator"]], middle,
            OPERATOR_TEX[parameters["upper_operator"]], parameters["upper"],
        )
        return Content(instruction + " " + plain, maths, display_text=instruction)

    left, right = sides(parameters)
    instruction = "Solve this inequality."
    return Content(
        instruction + " " + relation_text(left, parameters["operator"], right),
        relation_text(left, parameters["operator"], right, True),
        display_text=instruction,
    )


def integer_solutions(parameters):
    """Test candidate integers directly against the displayed inequality."""
    coefficient, constant = parameters["coefficient"], parameters["constant"]
    lower, upper = parameters["lower"], parameters["upper"]
    first = (lower - constant) // coefficient - 2
    last = (upper - constant) // coefficient + 2
    found = []
    for value in range(first, last + 1):
        middle = coefficient * value + constant
        if (satisfies(lower, parameters["lower_operator"], middle)
                and satisfies(middle, parameters["upper_operator"], upper)):
            found.append(value)
    return found


def answer_for(parameters):
    variable = parameters["variable"]
    form = parameters["form"]
    if form == "double":
        values = integer_solutions(parameters)
        answer = {
            "kind": "integer_solutions", "variable": variable, "values": values,
        }
        display = Content(
            "{} = {}".format(variable, ", ".join(str(value) for value in values))
        )
        return answer, display

    if form == "simple":
        boundary = Fraction(
            parameters["target"] - parameters["constant"], parameters["coefficient"]
        )
        operator = parameters["operator"]
    elif form == "negative":
        # Dividing by the negative coefficient reverses the relation.
        boundary = Fraction(
            parameters["constant"] - parameters["target"], parameters["coefficient"]
        )
        operator = REVERSED[parameters["operator"]]
    else:
        boundary = Fraction(
            parameters["right_constant"] - parameters["left_constant"],
            parameters["left_coefficient"] - parameters["right_coefficient"],
        )
        operator = parameters["operator"]

    answer = {
        "kind": "inequality_solution", "variable": variable,
        "operator": operator, "boundary": rational_text(boundary),
    }
    display = Content(
        relation_text(variable, operator, rational_text(boundary)),
        relation_text(variable, operator, rational_tex(boundary), True),
    )
    return answer, display


class LinearInequality:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        from . import inequalities_contexts as worded_forms
        if rng.random() < worded_forms.CONTEXT_SHARE.get(difficulty, 0.0):
            return worded_forms.generate(self, context)

        if difficulty == 4:
            parameters = self.make_double(rng)
        else:
            parameters = self.make_single(rng, difficulty)

        prompt = presentation(parameters)
        answer, display = answer_for(parameters)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=2 if difficulty <= 2 else 3, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=3 if difficulty <= 2 else 4),
            parameters=parameters,
        )
        self.validate(question)
        return question

    def make_single(self, rng, difficulty):
        """Build backwards from a chosen integer boundary."""
        operator = rng.choice(("<", "<=", ">", ">="))
        boundary = rng.choice([value for value in range(-8, 9) if value])
        constant = rng.choice([value for value in range(-12, 13) if value])
        if difficulty == 1:
            coefficient = rng.randint(2, 9)
            return {
                "form": "simple", "variable": "x", "coefficient": coefficient,
                "constant": constant, "target": coefficient * boundary + constant,
                "operator": operator,
            }
        if difficulty == 3:
            coefficient = rng.randint(2, 9)
            return {
                "form": "negative", "variable": "x", "coefficient": coefficient,
                "constant": constant, "target": constant - coefficient * boundary,
                "operator": operator,
            }
        left_coefficient = rng.randint(3, 9)
        right_coefficient = rng.randint(1, left_coefficient - 1)
        difference = left_coefficient - right_coefficient
        return {
            "form": "both_sides", "variable": "x",
            "left_coefficient": left_coefficient, "left_constant": constant,
            "right_coefficient": right_coefficient,
            "right_constant": difference * boundary + constant,
            "operator": operator,
        }

    def make_double(self, rng):
        """Choose the wanted integer solutions, then bounds that produce them."""
        coefficient = rng.randint(2, 5)
        constant = rng.choice([value for value in range(-9, 10) if value])
        first = rng.randint(-6, 3)
        last = first + rng.randint(2, 5)
        lower_operator = rng.choice(("<", "<="))
        upper_operator = rng.choice(("<", "<="))
        # A strict bound may sit on the neighbouring value; an inclusive one
        # may sit on the solution itself. Both keep the endpoints exact.
        low_gap = (rng.randint(1, coefficient) if lower_operator == "<"
                   else rng.randint(0, coefficient - 1))
        high_gap = (rng.randint(1, coefficient) if upper_operator == "<"
                    else rng.randint(0, coefficient - 1))
        return {
            "form": "double", "variable": "n", "coefficient": coefficient,
            "constant": constant,
            "lower": coefficient * first + constant - low_gap,
            "upper": coefficient * last + constant + high_gap,
            "lower_operator": lower_operator, "upper_operator": upper_operator,
        }

    def validate(self, question):
        from .worded import is_worded
        if is_worded(question):
            from .inequalities_contexts import validate as validate_worded
            return validate_worded(self, question)
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.settings == {}, "Unsupported settings")

        parameters = question.parameters
        form = FORMS[level]
        require(parameters.get("form") == form, "Form does not match difficulty")
        require(set(parameters) == EXPECTED_KEYS[form], "Unexpected parameters")
        require(parameters["variable"] == ("n" if level == 4 else "x"),
                "Unexpected variable")

        answer, display = answer_for(parameters)
        if level == 4:
            self.check_double(parameters, answer)
        else:
            self.check_single(parameters, answer, level)

        require(question.answer == answer, "Incorrect answer")
        require(question.answer_display == display, "Display mismatch")
        require(question.prompt == presentation(parameters), "Prompt mismatch")
        require(question.visual_assets("questions") == ()
                and question.visual_assets("answers") == (),
                "This family uses no visual assets")
        return True

    def check_single(self, parameters, answer, level):
        require(parameters["operator"] in OPERATOR_TEX, "Invalid operator")
        integers = [value for key, value in parameters.items()
                    if key not in ("form", "variable", "operator")]
        require(all(type(value) is int for value in integers),
                "Expected integer coefficients")
        if parameters["form"] == "both_sides":
            left = parameters["left_coefficient"]
            right = parameters["right_coefficient"]
            require(3 <= left <= 9 and 1 <= right < left,
                    "Coefficients outside difficulty bounds")
            require(abs(parameters["left_constant"]) <= 12
                    and parameters["left_constant"] != 0, "Constant outside bounds")
        else:
            require(2 <= parameters["coefficient"] <= 9,
                    "Coefficient outside difficulty bounds")
            require(abs(parameters["constant"]) <= 12 and parameters["constant"] != 0,
                    "Constant outside bounds")
        boundary = Fraction(answer["boundary"])
        require(boundary.denominator == 1 and 1 <= abs(boundary) <= 8,
                "Solution outside difficulty bounds")
        reversed_direction = answer["operator"] != parameters["operator"]
        require(reversed_direction == (level == 3),
                "Incorrect direction change for this level")

    def check_double(self, parameters, answer):
        require(parameters["lower_operator"] in ("<", "<=")
                and parameters["upper_operator"] in ("<", "<="),
                "Invalid double inequality operators")
        require(type(parameters["coefficient"]) is int
                and 2 <= parameters["coefficient"] <= 5,
                "Coefficient outside difficulty bounds")
        require(type(parameters["constant"]) is int
                and parameters["constant"] != 0 and abs(parameters["constant"]) <= 9,
                "Constant outside bounds")
        require(type(parameters["lower"]) is int and type(parameters["upper"]) is int,
                "Bounds must be integers")
        require(parameters["lower"] < parameters["upper"], "Reversed bounds")
        values = answer["values"]
        require(3 <= len(values) <= 6, "Unexpected number of integer solutions")
        require(values == list(range(values[0], values[-1] + 1)),
                "Integer solutions must be consecutive")

    def validate_independently(self, question):
        """Solve the displayed relation symbolically rather than by rearranging."""
        from .worded import is_worded
        if is_worded(question):
            from .inequalities_contexts import validate_independently as independent_worded
            return independent_worded(question)
        import sympy

        parameters = question.parameters
        unknown = sympy.Symbol(parameters["variable"], real=True)
        relations = {"<": sympy.Lt, "<=": sympy.Le, ">": sympy.Gt, ">=": sympy.Ge}

        if parameters["form"] == "double":
            middle = parameters["coefficient"] * unknown + parameters["constant"]
            # Each bound is solved separately, because the univariate solver
            # accepts a single relation rather than a conjunction of two.
            solution = sympy.Intersection(*[
                sympy.solve_univariate_inequality(relation, unknown, relational=False)
                for relation in (
                    relations[parameters["lower_operator"]](parameters["lower"], middle),
                    relations[parameters["upper_operator"]](middle, parameters["upper"]),
                )
            ])
            values = question.answer["values"]
            for value in values:
                require(bool(solution.contains(value)),
                        "Independent solution excludes a listed integer")
            require(not bool(solution.contains(values[0] - 1)),
                    "Independent solution includes a smaller integer")
            require(not bool(solution.contains(values[-1] + 1)),
                    "Independent solution includes a larger integer")
            return True

        if parameters["form"] == "simple":
            left = parameters["coefficient"] * unknown + parameters["constant"]
            right = sympy.Integer(parameters["target"])
        elif parameters["form"] == "negative":
            left = parameters["constant"] - parameters["coefficient"] * unknown
            right = sympy.Integer(parameters["target"])
        else:
            left = (parameters["left_coefficient"] * unknown
                    + parameters["left_constant"])
            right = (parameters["right_coefficient"] * unknown
                     + parameters["right_constant"])

        solution = sympy.solve_univariate_inequality(
            relations[parameters["operator"]](left, right), unknown, relational=False,
        )
        boundary = sympy.Rational(question.answer["boundary"])
        operator = question.answer["operator"]
        if operator in (">", ">="):
            expected = sympy.Interval(
                boundary, sympy.oo, left_open=(operator == ">"), right_open=True,
            )
        else:
            expected = sympy.Interval(
                -sympy.oo, boundary, left_open=True, right_open=(operator == "<"),
            )
        require(solution == expected, "Independent solution set disagrees")
        return True