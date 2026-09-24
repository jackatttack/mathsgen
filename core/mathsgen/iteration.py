"""Iteration: sign changes, iterative formulae and locating a root.

Every question uses a cubic x^3 + b x + c = 0 with integer coefficients and a
change of sign on [a, a + 1]. Two rearrangements are used:

    cube_root:  x = cube root(-c - b x)
    quotient:   x = -c / (x^2 + b)      (only when b > 0, so it never divides by 0)

A rearrangement is kept only when iterating it from x0 converges to the root
inside (a, a + 1) at a visible but reasonable rate (RATE_BOUNDS on |g'(root)|).
Iterates use unrounded previous values, as with a calculator's ANS key, and
are rounded to 4 d.p.; roots to 3 d.p. Nearby rounding boundaries are rejected.
"""
import math
from fractions import Fraction

from . import rich_blocks as rb
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


INFO = GeneratorInfo(
    id="algebra.iteration.numerical", version=1,
    topic="algebra", subtopic="iteration",
    title="Iteration: sign changes, iterative formulae and roots",
    difficulty_descriptions={
        1: "Show a cubic has a solution between two integers by a change of sign.",
        2: "Use an iterative formula to find x1, x2 and x3 to 4 decimal places.",
        3: "Show a rearrangement, then iterate three times for an estimate.",
        4: "Show a sign change, then iterate to the solution to 3 decimal places.",
    },
    tags=("algebra", "iteration", "numerical methods"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {1: "sign_change", 2: "iterate", 3: "rearrange_iterate", 4: "root"}
B_VALUES = tuple(v for v in range(-6, 7) if v != 0)
C_VALUES = tuple(v for v in range(-9, 10) if v != 0)
INTERVAL_STARTS = tuple(range(-3, 3))
ARRANGEMENTS = ("cube_root", "quotient")
RATE_BOUNDS = (0.1, 0.75)          # |g'(root)|: visibly moving, still converging
MARKS = {1: 2, 2: 3, 3: 5, 4: 5}
WORKING_LINES = {1: 4, 2: 6, 3: 8, 4: 9}

SIGN_KEYS = {"form", "b", "c", "a"}
ITERATION_KEYS = SIGN_KEYS | {"arrangement", "x0_tenths"}


# ------------------------------------------------------------ mathematics

def cubic(b, c, x):
    return x ** 3 + b * x + c


def step(b, c, arrangement, x):
    if arrangement == "cube_root":
        value = -b * x - c
        return math.copysign(abs(value) ** (1 / 3), value)
    denominator = x * x + b
    require(abs(denominator) > 1e-9, "Division by zero in the iteration")
    return -c / denominator


def limit(b, c, arrangement, x0):
    x = x0
    for _ in range(400):
        following = step(b, c, arrangement, x)
        require(math.isfinite(following) and abs(following) < 1e6, "Iteration diverges")
        if abs(following - x) < 1e-13:
            return following
        x = following
    raise ValueError("Iteration does not converge")


def rate(b, c, arrangement, root):
    h = 1e-6
    return abs(step(b, c, arrangement, root + h) - step(b, c, arrangement, root - h)) / (2 * h)


def rounded_places(value, places):
    """Exact value rounded to places, rejecting a nearby rounding boundary."""
    scaled = value * 10 ** places
    fraction = scaled - math.floor(scaled)
    require(abs(fraction - 0.5) > 1e-4, "Near a rounding boundary")
    return Fraction(math.floor(scaled + 0.5), 10 ** places)


def fixed_text(value, places):
    scaled = Fraction(value) * 10 ** places
    require(scaled.denominator == 1, "Value is not at this precision")
    number = int(scaled)
    sign = "-" if number < 0 else ""
    digits = str(abs(number)).rjust(places + 1, "0")
    return sign + digits[:-places] + "." + digits[-places:]


def start(par):
    return Fraction(par["x0_tenths"], 10)


def iterates(par):
    x = float(start(par))
    values = []
    for _ in range(3):
        x = step(par["b"], par["c"], par["arrangement"], x)
        values.append(x)
    return values


def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    require(level in FORMS and par.get("form") == FORMS[level], "Unexpected form for this level")
    keys = SIGN_KEYS if level == 1 else ITERATION_KEYS
    require(set(par) == keys, "Unexpected parameters")
    require(all(type(par[k]) is int for k in keys - {"form", "arrangement"}),
            "Integer parameters required")
    b, c, a = par["b"], par["c"], par["a"]
    require(b in B_VALUES and c in C_VALUES and a in INTERVAL_STARTS, "Coefficient outside bounds")
    require(cubic(b, c, a) * cubic(b, c, a + 1) < 0, "No change of sign on the interval")
    if level == 1:
        return
    arrangement = par["arrangement"]
    require(arrangement in ARRANGEMENTS, "Unknown rearrangement")
    if arrangement == "quotient":
        require(b > 0, "The quotient form needs x^2 + b to stay positive")
    require(par["x0_tenths"] in (10 * a, 10 * a + 5, 10 * a + 10), "Start value outside the interval")
    root = limit(b, c, arrangement, float(start(par)))
    require(a < root < a + 1 and abs(cubic(b, c, root)) < 1e-9, "Converges to the wrong root")
    require(RATE_BOUNDS[0] <= rate(b, c, arrangement, root) <= RATE_BOUNDS[1],
            "Convergence too fast or too slow")
    if level in (2, 3):
        rounded = [rounded_places(value, 4) for value in iterates(par)]
        require(len(set(rounded)) == 3, "Iterates too similar")
    else:
        rounded_places(root, 3)


# ------------------------------------------------------------ notation

def join_terms(terms):
    """(tex, text) for integer-coefficient terms; symbol "" marks a constant."""
    tex, text = "", ""
    for coefficient, symbol_tex, symbol_text in terms:
        if coefficient == 0:
            continue
        size = abs(coefficient)
        shown = "" if (size == 1 and symbol_tex) else str(size)
        if not tex:
            sign = "-" if coefficient < 0 else ""
        else:
            sign = " - " if coefficient < 0 else " + "
        tex += sign + shown + symbol_tex
        text += sign + shown + symbol_text
    return (tex or "0"), (text or "0")


def cubic_parts(b, c):
    return join_terms([(1, "x^{3}", "x^3"), (b, "x", "x"), (c, "", "")])


def radicand_terms(b, c, var_tex, var_text):
    """-c - b x, written with a positive term first: 3x - 8 rather than -8 + 3x."""
    terms = [(-c, "", ""), (-b, var_tex, var_text)]
    if -c < 0 < -b:
        terms.reverse()
    return terms


def formula_parts(b, c, arrangement, left_tex, left_text, var_tex, var_text):
    if arrangement == "cube_root":
        inner_tex, inner_text = join_terms(radicand_terms(b, c, var_tex, var_text))
        return (left_tex + r" = \sqrt[3]{" + inner_tex + "}",
                left_text + " = cube root(" + inner_text + ")")
    den_tex, den_text = join_terms([(1, var_tex + "^{2}", var_text + "^2"), (b, "", "")])
    return (left_tex + r" = \frac{" + str(-c) + "}{" + den_tex + "}",
            left_text + " = " + str(-c) + "/(" + den_text + ")")


def iteration_formula(par):
    return formula_parts(par["b"], par["c"], par["arrangement"],
                         "x_{n+1}", "x_(n+1)", "x_{n}", "x_n")


def rearranged_formula(par):
    return formula_parts(par["b"], par["c"], par["arrangement"], "x", "x", "x", "x")


def start_run(par):
    value = start(par)
    shown = str(int(value)) if value.denominator == 1 else fixed_text(value, 1)
    return rb.maths("x_{0} = " + shown, "x_0 = " + shown)


def content(blocks):
    plain = []
    for block in blocks:
        if block["kind"] == "equation":
            plain.append(block["text"] + ".")
        elif "runs" in block:
            plain.append("".join(run["text"] for run in block["runs"]))
        else:
            plain.append(block["text"])
    return Content(" ".join(plain), blocks=tuple(blocks))


def prompt_for(par, level):
    b, c, a = par["b"], par["c"], par["a"]
    cubic_tex, cubic_text = cubic_parts(b, c)
    equation = rb.maths(cubic_tex + " = 0", cubic_text + " = 0")
    between = " has a solution between {} and {}.".format(a, a + 1)
    if level == 1:
        return content([rb.paragraph(rb.text("Show that the equation "), equation,
                                     rb.text(between))])
    formula = rb.maths(*iteration_formula(par))
    if level == 2:
        return content([rb.paragraph(
            rb.text("Using "), formula, rb.text(" with "), start_run(par),
            rb.text(", find the values of "), rb.maths("x_{1}", "x_1"), rb.text(", "),
            rb.maths("x_{2}", "x_2"), rb.text(" and "), rb.maths("x_{3}", "x_3"),
            rb.text(". Give each value to 4 decimal places."),
        )])
    if level == 3:
        return content([
            rb.paragraph(rb.text("(a) Show that the equation "), equation,
                         rb.text(" can be rearranged to give "),
                         rb.maths(*rearranged_formula(par)), rb.text(".")),
            rb.paragraph(rb.text("(b) Starting with "), start_run(par),
                         rb.text(", use the iteration formula "), formula,
                         rb.text(" three times to find an estimate for a solution of the "
                                 "equation. Give your answer to 4 decimal places.")),
        ])
    return content([
        rb.paragraph(rb.text("(a) Show that the equation "), equation, rb.text(between)),
        rb.paragraph(rb.text("(b) Using "), formula, rb.text(" with "), start_run(par),
                     rb.text(", find this solution correct to 3 decimal places.")),
    ])


def sign_sentence(par):
    b, c, a = par["b"], par["c"], par["a"]
    return ("At x = {}: {}. At x = {}: {}. The sign changes, so there is a solution "
            "between {} and {}.").format(a, cubic(b, c, a), a + 1, cubic(b, c, a + 1), a, a + 1)


def rearrangement_sentence(par):
    b, c = par["b"], par["c"]
    if par["arrangement"] == "cube_root":
        inner = join_terms(radicand_terms(b, c, "x", "x"))[1]
        return "x^3 = {0}, so x = cube root({0}).".format(inner)
    factor = join_terms([(1, "x^{2}", "x^2"), (b, "", "")])[1]
    return "x({0}) = {1}, so x = {1}/({0}).".format(factor, -c)


def answer_for(par, level):
    b, c, a = par["b"], par["c"], par["a"]
    if level == 1:
        answer = {"kind": "sign_change", "lower": str(cubic(b, c, a)),
                  "upper": str(cubic(b, c, a + 1))}
        return answer, Content(sign_sentence(par))
    if level in (2, 3):
        values = [rounded_places(value, 4) for value in iterates(par)]
        shown = [fixed_text(value, 4) for value in values]
        listing = ", ".join("x_{} = {}".format(i + 1, s) for i, s in enumerate(shown))
        answer = {"kind": "iterates", "values": [rational_text(v) for v in values]}
        if level == 2:
            tex = r",\quad ".join("x_{%d} = %s" % (i + 1, s) for i, s in enumerate(shown))
            return answer, Content(listing, tex)
        return answer, Content("(a) {} (b) {}. Estimate: {}.".format(
            rearrangement_sentence(par), listing, shown[-1]))
    root = rounded_places(limit(b, c, par["arrangement"], float(start(par))), 3)
    answer = {"kind": "sign_change_root", "lower": str(cubic(b, c, a)),
              "upper": str(cubic(b, c, a + 1)), "root": rational_text(root)}
    return answer, Content("(a) {} (b) x = {}".format(sign_sentence(par), fixed_text(root, 3)))


def draw_parameters(rng, level):
    b, c = rng.choice(B_VALUES), rng.choice(C_VALUES)
    starts = [a for a in INTERVAL_STARTS if cubic(b, c, a) * cubic(b, c, a + 1) < 0]
    a = rng.choice(starts) if starts else INTERVAL_STARTS[0]
    par = {"form": FORMS[level], "b": b, "c": c, "a": a}
    if level > 1:
        par["arrangement"] = rng.choice(ARRANGEMENTS)
        par["x0_tenths"] = rng.choice((10 * a, 10 * a + 5, 10 * a + 10))
    return par


# ------------------------------------------------------------ generator

class Iteration:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        for attempt in range(2000):
            par = draw_parameters(context.rng, difficulty)
            try:
                check_parameters(par, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct an iteration question")
        answer, display = answer_for(par, difficulty)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(par, difficulty),
            answer=answer, answer_display=display, worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=WORKING_LINES[difficulty]),
            parameters=par,
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        require(type(q.difficulty) is int and q.difficulty in (1, 2, 3, 4), "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        check_parameters(q.parameters, q.difficulty)
        answer, display = answer_for(q.parameters, q.difficulty)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Answer display mismatch")
        require(q.prompt == prompt_for(q.parameters, q.difficulty), "Prompt mismatch")
        return True

    def validate_independently(self, q):
        """Horner evaluation, cube roots by bisection and the root by bisection on f."""
        par = q.parameters
        b, c, a = par["b"], par["c"], par["a"]

        def f(x):
            return (x * x + b) * x + c

        def cube_root(value):
            low, high = -30.0, 30.0
            for _ in range(200):
                middle = (low + high) / 2
                if middle * middle * middle < value:
                    low = middle
                else:
                    high = middle
            return (low + high) / 2

        def following(x):
            if par["arrangement"] == "cube_root":
                return cube_root(-b * x - c)
            return -c / (x * x + b)

        if q.difficulty in (1, 4):
            require(int(q.answer["lower"]) == f(a) and int(q.answer["upper"]) == f(a + 1),
                    "Independent values of the cubic disagree")
            require(f(a) * f(a + 1) < 0, "No independent sign change")
        if q.difficulty in (2, 3):
            x = par["x0_tenths"] / 10
            for stated in q.answer["values"]:
                x = following(x)
                require(abs(x - float(Fraction(stated))) <= 0.5e-4 + 1e-9,
                        "Independent iterate disagrees")
        if q.difficulty == 4:
            low, high = float(a), float(a + 1)
            for _ in range(200):
                middle = (low + high) / 2
                if f(low) * f(middle) <= 0:
                    high = middle
                else:
                    low = middle
            stated = Fraction(q.answer["root"])
            require((stated * 1000).denominator == 1, "Expected 3 decimal places")
            require(abs((low + high) / 2 - float(stated)) <= 0.5e-3 + 1e-9,
                    "Independent root disagrees")
        return True