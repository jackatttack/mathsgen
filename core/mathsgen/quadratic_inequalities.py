"""Factorisable quadratic inequalities with exact interval answers."""
from fractions import Fraction
from math import isqrt

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)
from .quadratic_monic import polynomial

OPS = ("<", "<=", ">", ">=")
TEX_OPS = {"<": "<", "<=": r"\leq", ">": ">", ">=": r"\geq"}

INFO = GeneratorInfo(
    id="algebra.inequalities.quadratic",
    version=1,
    topic="algebra",
    subtopic="inequalities",
    title="Solve quadratic inequalities",
    difficulty_descriptions={
        1: "Solve a strict inequality given in factorised form.",
        2: "Factorise a monic quadratic and solve a strict or inclusive inequality.",
        3: "Factorise a non-monic quadratic and solve a strict or inclusive inequality.",
        4: "Rearrange terms from both sides, then solve a quadratic inequality.",
    },
    tags=("quadratics", "inequalities", "factorising", "intervals"),
)


def relation(left, operator, right, tex=False):
    symbol = TEX_OPS[operator] if tex else operator
    return "{} {} {}".format(left, symbol, right)


def factor(root, tex=False):
    if root == 0:
        return "x"
    return "(x {} {})".format("-" if root > 0 else "+", abs(root))


def factorised(parameters, tex=False):
    a = parameters["coefficient"]
    roots = parameters["roots"]
    prefix = "" if a == 1 else "-" if a == -1 else str(a)
    return prefix + factor(roots[0], tex) + factor(roots[1], tex)


def prompt_for(parameters):
    op = parameters["operator"]
    if parameters["form"] == "factorised":
        left = factorised(parameters)
        right = "0"
        left_tex = left
        right_tex = right
    else:
        left = polynomial(parameters["left"])
        right = polynomial(parameters["right"])
        left_tex = polynomial(parameters["left"], True)
        right_tex = polynomial(parameters["right"], True)
    instruction = "Solve the inequality."
    return Content(
        instruction + " " + relation(left, op, right),
        relation(left_tex, op, right_tex, True),
        display_text=instruction,
    )


def solution_parts(parameters):
    """Return ordered intervals as (lower, upper, lower_closed, upper_closed).

    None represents an unbounded endpoint. The two-root construction
    guarantees there are no repeated roots or empty solution sets.
    """
    low, high = parameters["roots"]
    a = parameters["coefficient"]
    op = parameters["operator"]
    inside = (a > 0) == (op in ("<", "<="))
    closed = op in ("<=", ">=")
    if inside:
        return [(low, high, closed, closed)]
    return [
        (None, low, False, closed),
        (high, None, closed, False),
    ]


def answer_for(parameters):
    intervals = solution_parts(parameters)
    answer = {
        "kind": "interval_union",
        "variable": "x",
        "intervals": [
            {
                "lower": None if lo is None else str(lo),
                "upper": None if hi is None else str(hi),
                "lower_closed": lc,
                "upper_closed": uc,
            }
            for lo, hi, lc, uc in intervals
        ],
    }
    if len(intervals) == 1:
        lo, hi, lc, uc = intervals[0]
        left = "<=" if lc else "<"
        right = "<=" if uc else "<"
        plain = "{} {} x {} {}".format(lo, left, right, hi)
        maths = "{} {} x {} {}".format(
            lo, TEX_OPS[left], TEX_OPS[right], hi
        )
    else:
        lo = intervals[0][1]
        hi = intervals[1][0]
        left = "<=" if intervals[0][3] else "<"
        right = ">=" if intervals[1][2] else ">"
        plain = "x {} {} or x {} {}".format(left, lo, right, hi)
        maths = r"x {} {}\quad\mathrm{{or}}\quad x {} {}".format(
            TEX_OPS[left], lo, TEX_OPS[right], hi
        )
    return answer, Content(plain, maths)


def make_parameters(rng, difficulty):
    if difficulty == 1:
        roots = sorted(rng.sample(range(-8, 9), 2))
        coefficient = 1
        operator = rng.choice(("<", ">"))
        form = "factorised"
    elif difficulty == 2:
        roots = sorted(rng.sample(range(-8, 9), 2))
        coefficient = 1
        operator = rng.choice(OPS)
        form = "expanded"
    elif difficulty == 3:
        roots = sorted(rng.sample(range(-7, 8), 2))
        coefficient = rng.choice((2, 3))
        operator = rng.choice(OPS)
        form = "expanded"
    else:
        roots = sorted(rng.sample(range(-6, 7), 2))
        coefficient = rng.choice((-3, -2, -1, 1, 2, 3))
        operator = rng.choice(OPS)
        form = "rearrange"

    reduced = [
        coefficient,
        -coefficient * sum(roots),
        coefficient * roots[0] * roots[1],
    ]
    right = [0, 0, 0]
    if difficulty == 4:
        # Both sides visibly contain an x-term and a constant.
        for _ in range(100):
            right = [
                0,
                rng.choice(tuple(range(-6, 0)) + tuple(range(1, 7))),
                rng.choice(tuple(range(-9, 0)) + tuple(range(1, 10))),
            ]
            left = [reduced[i] + right[i] for i in range(3)]
            if left[1] and left[2]:
                break
        else:
            raise ValueError("Could not construct rearrangement")
    else:
        left = reduced[:]

    return {
        "form": form,
        "roots": roots,
        "coefficient": coefficient,
        "operator": operator,
        "left": left,
        "right": right,
    }


class QuadraticInequalities:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        p = make_parameters(context.rng, difficulty)
        answer, display = answer_for(p)
        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=prompt_for(p),
            answer=answer,
            answer_display=display,
            worked_solution=(),
            marks={1: 2, 2: 3, 3: 4, 4: 5}[difficulty],
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines={1: 4, 2: 6, 3: 7, 4: 9}[difficulty]),
            parameters=p,
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid difficulty")
        require(question.settings == {}, "Unexpected settings")
        p = question.parameters
        require(set(p) == {
            "form", "roots", "coefficient", "operator", "left", "right"
        }, "Unexpected parameters")
        require(p["operator"] in OPS, "Invalid operator")
        require(
            p["form"] == {
                1: "factorised", 2: "expanded",
                3: "expanded", 4: "rearrange",
            }[level],
            "Form does not match difficulty",
        )
        roots = p["roots"]
        require(
            isinstance(roots, list) and len(roots) == 2
            and all(type(r) is int for r in roots)
            and roots[0] < roots[1],
            "Expected two ordered distinct integer roots",
        )
        require(
            all(-8 <= r <= 8 for r in roots),
            "Roots outside teaching bounds",
        )
        a = p["coefficient"]
        require(type(a) is int and a != 0 and abs(a) <= 3, "Invalid coefficient")
        if level <= 2:
            require(a == 1, "Expected monic quadratic")
        if level == 3:
            require(a in (2, 3), "Expected positive non-monic quadratic")
        if level == 1:
            require(p["operator"] in ("<", ">"), "Expected strict inequality")
        left, right = p["left"], p["right"]
        require(
            isinstance(left, list) and isinstance(right, list)
            and len(left) == len(right) == 3
            and all(type(v) is int for v in left + right),
            "Invalid polynomial coefficients",
        )
        reduced = [l - r for l, r in zip(left, right)]
        require(
            reduced == [a, -a * sum(roots), a * roots[0] * roots[1]],
            "Displayed quadratic does not match roots",
        )
        if level < 4:
            require(right == [0, 0, 0], "Unexpected right-hand terms")
        else:
            require(
                right[0] == 0 and right[1] and right[2]
                and left[1] and left[2],
                "Expected terms on both sides",
            )
        answer, display = answer_for(p)
        require(question.answer == answer, "Incorrect interval answer")
        require(question.answer_display == display, "Answer display mismatch")
        require(question.prompt == prompt_for(p), "Prompt mismatch")
        require(
            question.visual_assets("questions") == ()
            and question.visual_assets("answers") == (),
            "Unexpected visuals",
        )
        return True

    def validate_independently(self, question):
        """Compare against SymPy's solution set for the displayed inequality."""
        import sympy

        p = question.parameters
        x = sympy.Symbol("x", real=True)
        left = sum(v * x ** (2 - i) for i, v in enumerate(p["left"]))
        right = sum(v * x ** (2 - i) for i, v in enumerate(p["right"]))
        relations = {
            "<": sympy.Lt, "<=": sympy.Le,
            ">": sympy.Gt, ">=": sympy.Ge,
        }
        actual = sympy.solve_univariate_inequality(
            relations[p["operator"]](left, right), x, relational=False
        )

        pieces = []
        for item in question.answer["intervals"]:
            lower = (
                -sympy.oo if item["lower"] is None
                else sympy.Rational(item["lower"])
            )
            upper = (
                sympy.oo if item["upper"] is None
                else sympy.Rational(item["upper"])
            )
            pieces.append(sympy.Interval(
                lower, upper,
                left_open=not item["lower_closed"],
                right_open=not item["upper_closed"],
            ))
        expected = sympy.Union(*pieces)
        require(actual == expected, "Independent solution set disagrees")
        return True