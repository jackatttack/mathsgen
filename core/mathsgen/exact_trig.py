"""Exact trigonometric values: recall, combine, use in triangles and invert.

Exact values are sums of rational multiples of sqrt(1), sqrt(2), sqrt(3) and
sqrt(6), stored as {root: Fraction}. Multiplying two surds reduces the
square factor exactly (sqrt(3) x sqrt(3) = 3, sqrt(2) x sqrt(3) = sqrt(6)).
The independent check uses floating-point trigonometry from math.
"""
import math
from fractions import Fraction

from . import rich_blocks as rb
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_tex, rational_text, require,
)


INFO = GeneratorInfo(
    id="geometry.trigonometry.exact_values", version=1,
    topic="geometry", subtopic="exact_trig",
    title="Exact trigonometric values",
    difficulty_descriptions={
        1: "Write down an exact value of sin, cos or tan.",
        2: "Work out the exact value of a sum or product of trigonometric values.",
        3: "Find an exact side length in a right-angled triangle with a special angle.",
        4: "Find an acute angle from an exact value or a simple equation.",
    },
    tags=("geometry", "trigonometry", "exact values", "surds"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("sin_cos", "tan"),
    2: ("sum", "product"),
    3: ("from_hypotenuse", "from_adjacent"),
    4: ("find_angle", "solve_equation"),
}
HALF = Fraction(1, 2)
EXACT = {
    "sin": {0: {}, 30: {1: HALF}, 45: {2: HALF}, 60: {3: HALF}, 90: {1: Fraction(1)}},
    "cos": {0: {1: Fraction(1)}, 30: {3: HALF}, 45: {2: HALF}, 60: {1: HALF}, 90: {}},
    "tan": {0: {}, 30: {3: Fraction(1, 3)}, 45: {1: Fraction(1)}, 60: {3: Fraction(1)}},
}
SPECIAL = (30, 45, 60)
MARKS = {1: 1, 2: 2, 3: 2, 4: 2}
WORKING_LINES = {1: 2, 2: 4, 3: 4, 4: 4}

KEYS = {
    "sin_cos": {"function", "angle"},
    "tan": {"angle"},
    "sum": {"terms"},
    "product": {"factors"},
    "from_hypotenuse": {"function", "angle", "hypotenuse"},
    "from_adjacent": {"angle", "adjacent"},
    "find_angle": {"function", "angle"},
    "solve_equation": {"function", "angle", "multiplier"},
}


# ------------------------------------------------------------ exact surd arithmetic

def square_free(n):
    """(outside, inside) with n = outside^2 * inside and inside square-free."""
    outside, inside = 1, n
    for f in range(2, int(math.isqrt(n)) + 1):
        while inside % (f * f) == 0:
            inside //= f * f
            outside *= f
    return outside, inside


def tidy(u):
    return {k: c for k, c in sorted(u.items()) if c != 0}


def plus(u, v):
    out = dict(u)
    for k, c in v.items():
        out[k] = out.get(k, 0) + c
    return tidy(out)


def times(u, v):
    out = {}
    for a, ca in u.items():
        for b, cb in v.items():
            outside, inside = square_free(a * b)
            out[inside] = out.get(inside, 0) + ca * cb * outside
    return tidy(out)


def scaled(k, u):
    return tidy({root: k * c for root, c in u.items()})


def as_float(u):
    return sum(float(c) * math.sqrt(k) for k, c in u.items())


def surd_parts(u):
    """(tex, text) for an exact value, e.g. \\frac{\\sqrt{3}}{2} and √3/2."""
    if not u:
        return "0", "0"
    tex, text = "", ""
    for k, c in sorted(u.items()):
        size = abs(c)
        if k == 1:
            piece_tex, piece_text = rational_tex(size), rational_text(size)
        else:
            top = "" if size.numerator == 1 else str(size.numerator)
            if size.denominator == 1:
                piece_tex = top + r"\sqrt{%d}" % k
                piece_text = top + "√%d" % k
            else:
                piece_tex = r"\frac{%s\sqrt{%d}}{%d}" % (top, k, size.denominator)
                piece_text = "%s√%d/%d" % (top, k, size.denominator)
        if not tex:
            sign = "-" if c < 0 else ""
        else:
            sign = " - " if c < 0 else " + "
        tex += sign + piece_tex
        text += sign + piece_text
    return tex, text


def encode(u):
    return {str(k): rational_text(c) for k, c in u.items()}


def decode(data):
    return {int(k): Fraction(c) for k, c in data.items()}


# ------------------------------------------------------------ mathematics

def value(par):
    """The exact answer for a value form, or the exact given value for an angle form."""
    form = par["form"]
    if form == "sin_cos":
        return EXACT[par["function"]][par["angle"]]
    if form == "tan":
        return EXACT["tan"][par["angle"]]
    if form == "sum":
        total = {}
        for coefficient, function, angle in par["terms"]:
            total = plus(total, scaled(coefficient, EXACT[function][angle]))
        return total
    if form == "product":
        (f1, a1), (f2, a2) = par["factors"]
        return times(EXACT[f1][a1], EXACT[f2][a2])
    if form == "from_hypotenuse":
        return scaled(par["hypotenuse"], EXACT[par["function"]][par["angle"]])
    if form == "from_adjacent":
        return scaled(par["adjacent"], EXACT["tan"][par["angle"]])
    if form == "find_angle":
        return EXACT[par["function"]][par["angle"]]
    return scaled(par["multiplier"], EXACT[par["function"]][par["angle"]])


def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    form = par.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(par) == KEYS[form] | {"form"}, "Unexpected parameters")
    if form == "sin_cos":
        require(par["function"] in ("sin", "cos") and par["angle"] in EXACT["sin"],
                "Unexpected value")
    elif form == "tan":
        require(par["angle"] in EXACT["tan"], "Unexpected angle")
    elif form == "sum":
        terms = par["terms"]
        require(isinstance(terms, list) and len(terms) == 2, "Two terms required")
        for term in terms:
            require(isinstance(term, list) and len(term) == 3 and term[0] in (-2, -1, 1, 2, 3)
                    and term[1] in EXACT and term[2] in SPECIAL, "Unexpected term")
        require(terms[0][1:] != terms[1][1:], "Terms must differ")
        require(value(par) != {}, "Sum must not be zero")
    elif form == "product":
        factors = par["factors"]
        require(isinstance(factors, list) and len(factors) == 2
                and all(isinstance(f, list) and len(f) == 2 and f[0] in EXACT and f[1] in SPECIAL
                        for f in factors), "Unexpected factors")
        require(factors[0] != factors[1], "Factors must differ")
    elif form == "from_hypotenuse":
        require(par["function"] in ("sin", "cos") and par["angle"] in SPECIAL,
                "Unexpected angle")
        require(type(par["hypotenuse"]) is int and 2 <= par["hypotenuse"] <= 20
                and par["hypotenuse"] % 2 == 0, "Hypotenuse outside bounds")
    elif form == "from_adjacent":
        require(par["angle"] in SPECIAL and type(par["adjacent"]) is int
                and 2 <= par["adjacent"] <= 15, "Values outside bounds")
    elif form == "find_angle":
        require(par["function"] in EXACT and par["angle"] in SPECIAL, "Unexpected value")
    else:
        require(par["function"] in EXACT and par["angle"] in SPECIAL
                and par["multiplier"] in (2, 3), "Unexpected equation")
        require(len(value(par)) == 1, "Right-hand side must be a single term")


# ------------------------------------------------------------ wording

def trig_parts(function, angle, variable=None):
    shown = variable if variable else r"%d^{\circ}" % angle
    shown_text = variable if variable else "%d°" % angle
    return r"\%s %s" % (function, shown), "%s %s" % (function, shown_text)


def content(runs):
    return Content("".join(run["text"] for run in runs), blocks=(rb.paragraph(*runs),))


def prompt_for(par):
    form = par["form"]
    if form in ("sin_cos", "tan"):
        function = par.get("function", "tan")
        return content([rb.text("Write down the exact value of "),
                        rb.maths(*trig_parts(function, par["angle"])), rb.text(".")])
    if form == "sum":
        tex, text = "", ""
        for coefficient, function, angle in par["terms"]:
            piece_tex, piece_text = trig_parts(function, angle)
            size = abs(coefficient)
            shown = "" if size == 1 else str(size)
            if not tex:
                sign = "-" if coefficient < 0 else ""
            else:
                sign = " - " if coefficient < 0 else " + "
            tex += sign + shown + piece_tex
            text += sign + shown + piece_text
        return content([rb.text("Work out the exact value of "), rb.maths(tex, text),
                        rb.text(". Give your answer in its simplest form.")])
    if form == "product":
        (f1, a1), (f2, a2) = par["factors"]
        t1, t2 = trig_parts(f1, a1), trig_parts(f2, a2)
        return content([rb.text("Work out the exact value of "),
                        rb.maths(t1[0] + r" \times " + t2[0], t1[1] + " x " + t2[1]),
                        rb.text(". Give your answer in its simplest form.")])
    if form == "from_hypotenuse":
        side = "BC" if par["function"] == "sin" else "AB"
        return content([rb.text(
            "Triangle ABC has a right angle at B. Angle BAC = {}° and AC = {} cm. Find the "
            "exact length of {}.".format(par["angle"], par["hypotenuse"], side))])
    if form == "from_adjacent":
        return content([rb.text(
            "Triangle ABC has a right angle at B. Angle BAC = {}° and AB = {} cm. Find the "
            "exact length of BC.".format(par["angle"], par["adjacent"]))])
    given_tex, given_text = surd_parts(value(par))
    if form == "find_angle":
        left = trig_parts(par["function"], None, "x")
        equation = (left[0] + " = " + given_tex, left[1] + " = " + given_text)
    else:
        left = trig_parts(par["function"], None, "x")
        equation = ("%d%s = %s" % (par["multiplier"], left[0], given_tex),
                    "%d%s = %s" % (par["multiplier"], left[1], given_text))
    return content([rb.text("Given that "), rb.maths(*equation),
                    rb.text(" and 0° < x < 90°, find the value of x.")])


def answer_for(par):
    form = par["form"]
    if form in ("find_angle", "solve_equation"):
        return ({"kind": "angle", "value": str(par["angle"]), "unit": "degrees"},
                Content("x = {}°".format(par["angle"])))
    exact = value(par)
    tex, text = surd_parts(exact)
    if form in ("from_hypotenuse", "from_adjacent"):
        return ({"kind": "exact_length", "value": encode(exact), "unit": "cm"},
                Content(text + " cm", tex + r"\ \mathrm{cm}"))
    return {"kind": "exact_value", "value": encode(exact)}, Content(text, tex)


def draw_parameters(rng, form):
    par = {"form": form}
    if form == "sin_cos":
        par.update(function=rng.choice(("sin", "cos")), angle=rng.choice(sorted(EXACT["sin"])))
    elif form == "tan":
        par["angle"] = rng.choice(sorted(EXACT["tan"]))
    elif form == "sum":
        par["terms"] = [[rng.choice((1, 2, 3)), rng.choice(sorted(EXACT)), rng.choice(SPECIAL)],
                        [rng.choice((-2, -1, 1, 2)), rng.choice(sorted(EXACT)), rng.choice(SPECIAL)]]
    elif form == "product":
        par["factors"] = [[rng.choice(sorted(EXACT)), rng.choice(SPECIAL)] for _ in range(2)]
    elif form == "from_hypotenuse":
        par.update(function=rng.choice(("sin", "cos")), angle=rng.choice(SPECIAL),
                   hypotenuse=rng.randrange(2, 21, 2))
    elif form == "from_adjacent":
        par.update(angle=rng.choice(SPECIAL), adjacent=rng.randint(2, 15))
    elif form == "find_angle":
        par.update(function=rng.choice(sorted(EXACT)), angle=rng.choice(SPECIAL))
    else:
        par.update(function=rng.choice(sorted(EXACT)), angle=rng.choice(SPECIAL),
                   multiplier=rng.choice((2, 3)))
    return par


# ------------------------------------------------------------ generator

class ExactTrig:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        form = rng.choice(FORMS[difficulty])
        for attempt in range(1000):
            par = draw_parameters(rng, form)
            try:
                check_parameters(par, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct an exact trigonometry question")
        answer, display = answer_for(par)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(par),
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
        answer, display = answer_for(q.parameters)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Answer display mismatch")
        require(q.prompt == prompt_for(q.parameters), "Prompt mismatch")
        return True

    def validate_independently(self, q):
        """Floating-point trigonometry from math, never the exact table."""
        par, answer = q.parameters, q.answer
        form = par.get("form")
        functions = {"sin": math.sin, "cos": math.cos, "tan": math.tan}

        def real(function, angle):
            return functions[function](math.radians(angle))

        if form in ("find_angle", "solve_equation"):
            x = int(answer["value"])
            target = as_float(value(par)) / (par["multiplier"] if form == "solve_equation" else 1)
            require(0 < x < 90 and abs(real(par["function"], x) - target) < 1e-9,
                    "Stated angle does not satisfy the equation")
            return True
        stated = as_float(decode(answer["value"]))
        if form == "sin_cos":
            expected = real(par["function"], par["angle"])
        elif form == "tan":
            expected = real("tan", par["angle"])
        elif form == "sum":
            expected = sum(c * real(f, a) for c, f, a in par["terms"])
        elif form == "product":
            expected = real(*par["factors"][0]) * real(*par["factors"][1])
        elif form == "from_hypotenuse":
            expected = par["hypotenuse"] * real(par["function"], par["angle"])
        else:
            expected = par["adjacent"] * real("tan", par["angle"])
        require(abs(stated - expected) < 1e-9 * max(1.0, abs(expected)),
                "Independent trigonometry disagrees")
        return True