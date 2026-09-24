"""Expand and simplify three brackets.

Every factor is a linear bracket (p x + a) with integer coefficients, stored as
[p, a]; [1, 0] is a bare x. Repeated factors are shown compactly, as in
(x + 3)^2(x - 2) or (2x - 1)^3. The independent check evaluates the product
directly at nine points, which pins down a cubic completely.
"""
from . import rich_blocks as rb
from .algebraic_proof import linear, mul, parts
from .core import Content, GeneratorInfo, LayoutHint, Question, make_context, require


INFO = GeneratorInfo(
    id="algebra.expanding.triple_brackets", version=1,
    topic="algebra", subtopic="triple_brackets",
    title="Expand and simplify three brackets",
    difficulty_descriptions={
        1: "Three brackets with positive constants, or x times two brackets.",
        2: "Mixed signs, or a squared bracket times another bracket.",
        3: "One coefficient of x above one, or a cubed bracket.",
        4: "Two coefficients of x above one, or a cubed bracket with a coefficient.",
    },
    tags=("algebra", "expanding", "brackets"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("positive", "x_factor"),
    2: ("mixed_signs", "squared"),
    3: ("one_coefficient", "cube"),
    4: ("two_coefficients", "linear_cube"),
}
MARKS = {1: 3, 2: 3, 3: 3, 4: 4}
WORKING_LINES = {1: 5, 2: 5, 3: 6, 4: 7}


def nonzero(low, high):
    return [v for v in range(low, high + 1) if v]


# ------------------------------------------------------------ checks

def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    form = par.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(par) == {"form", "factors"}, "Unexpected parameters")
    factors = par["factors"]
    require(isinstance(factors, list) and len(factors) == 3
            and all(isinstance(f, list) and len(f) == 2 and all(type(v) is int for v in f)
                    for f in factors), "Three [p, a] factors required")
    coefficients = [f[0] for f in factors]
    constants = [f[1] for f in factors]

    if form == "positive":
        require(coefficients == [1, 1, 1] and all(1 <= a <= 6 for a in constants),
                "Positive constants from 1 to 6 required")
    elif form == "x_factor":
        require(factors[0] == [1, 0] and coefficients == [1, 1, 1]
                and all(1 <= a <= 6 for a in constants[1:]), "x times two positive brackets")
    elif form == "mixed_signs":
        require(coefficients == [1, 1, 1] and all(a in nonzero(-6, 6) for a in constants),
                "Nonzero constants required")
        require(min(constants) < 0 and len(set(constants)) > 1, "At least one negative sign")
    elif form == "squared":
        require(coefficients == [1, 1, 1] and factors[0] == factors[1] != factors[2]
                and all(a in nonzero(-6, 6) for a in constants), "A squared bracket")
    elif form == "one_coefficient":
        require(2 <= coefficients[0] <= 5 and coefficients[1:] == [1, 1]
                and all(a in nonzero(-5, 5) for a in constants), "One coefficient above one")
    elif form == "cube":
        require(factors[0] == factors[1] == factors[2] and coefficients[0] == 1
                and constants[0] in nonzero(-5, 5), "A cubed bracket")
    elif form == "two_coefficients":
        require(2 <= coefficients[0] <= 4 and 2 <= coefficients[1] <= 4 and coefficients[2] == 1
                and all(a in nonzero(-5, 5) for a in constants), "Two coefficients above one")
    else:
        require(factors[0] == factors[1] == factors[2] and 2 <= coefficients[0] <= 3
                and constants[0] in nonzero(-4, 4), "A cubed bracket with a coefficient")


# ------------------------------------------------------------ notation

def expanded(par):
    product = [1]
    for p, a in par["factors"]:
        product = mul(product, linear(p, a))
    return product


def expression_parts(par):
    groups = []
    for factor in par["factors"]:
        if groups and groups[-1][0] == factor:
            groups[-1][1] += 1
        else:
            groups.append([factor, 1])
    tex, text = "", ""
    for factor, count in groups:
        inner_tex, inner_text = parts(linear(*factor), "x")
        piece_tex = inner_tex if factor == [1, 0] else "(" + inner_tex + ")"
        piece_text = inner_text if factor == [1, 0] else "(" + inner_text + ")"
        if count > 1:
            piece_tex += "^{%d}" % count
            piece_text += "^%d" % count
        tex += piece_tex
        text += piece_text
    return tex, text


def prompt_for(par):
    tex, text = expression_parts(par)
    runs = [rb.text("Expand and simplify "), rb.maths(tex, text), rb.text(".")]
    return Content("".join(run["text"] for run in runs), blocks=(rb.paragraph(*runs),))


def answer_for(par):
    polynomial = expanded(par)
    tex, text = parts(polynomial, "x")
    return {"kind": "polynomial", "coefficients": [str(c) for c in polynomial]}, Content(text, tex)


def draw_parameters(rng, form):
    if form == "positive":
        factors = [[1, rng.randint(1, 6)] for _ in range(3)]
    elif form == "x_factor":
        factors = [[1, 0], [1, rng.randint(1, 6)], [1, rng.randint(1, 6)]]
    elif form == "mixed_signs":
        factors = [[1, rng.choice(nonzero(-6, 6))] for _ in range(3)]
    elif form == "squared":
        a, b = rng.choice(nonzero(-6, 6)), rng.choice(nonzero(-6, 6))
        factors = [[1, a], [1, a], [1, b]]
    elif form == "one_coefficient":
        factors = [[rng.randint(2, 5), rng.choice(nonzero(-5, 5))],
                   [1, rng.choice(nonzero(-5, 5))], [1, rng.choice(nonzero(-5, 5))]]
    elif form == "cube":
        a = rng.choice(nonzero(-5, 5))
        factors = [[1, a], [1, a], [1, a]]
    elif form == "two_coefficients":
        factors = [[rng.randint(2, 4), rng.choice(nonzero(-5, 5))],
                   [rng.randint(2, 4), rng.choice(nonzero(-5, 5))],
                   [1, rng.choice(nonzero(-5, 5))]]
    else:
        p, a = rng.randint(2, 3), rng.choice(nonzero(-4, 4))
        factors = [[p, a], [p, a], [p, a]]
    return {"form": form, "factors": factors}


# ------------------------------------------------------------ generator

class TripleBrackets:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        form = rng.choice(FORMS[difficulty])
        for attempt in range(500):
            par = draw_parameters(rng, form)
            try:
                check_parameters(par, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a triple brackets question")
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
        """Evaluate the original product at x = -4..4 and compare with the stated cubic."""
        coefficients = [int(c) for c in q.answer["coefficients"]]
        require(len(coefficients) == 4 and coefficients[3] != 0, "Expected a cubic")
        for x in range(-4, 5):
            product = 1
            for p, a in q.parameters["factors"]:
                product *= p * x + a
            stated = sum(c * x ** i for i, c in enumerate(coefficients))
            require(stated == product, "Independent evaluation disagrees at x = {}".format(x))
        return True