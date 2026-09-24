"""Column vectors: arithmetic, vectors between points, translations and unknowns.

Vectors are [x, y] integer pairs, written with MathText's \\binom as a column.
Level 4 unknown scalars come from a real combination p a + q b of two
non-parallel vectors, so p and q are unique whole numbers.
"""
from . import rich_blocks as rb
from .core import Content, GeneratorInfo, LayoutHint, Question, make_context, require


INFO = GeneratorInfo(
    id="geometry.vectors.column", version=1,
    topic="geometry", subtopic="column_vectors",
    title="Column vectors: add, subtract, multiply and solve",
    difficulty_descriptions={
        1: "Add or subtract two column vectors.",
        2: "Work out a combination such as 2a + 3b, or a + b - c.",
        3: "Find the vector between two points, or use a translation vector.",
        4: "Find an unknown vector, or the scalars p and q with pa + qb = c.",
    },
    tags=("geometry", "vectors", "column vectors"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("add", "subtract"),
    2: ("combination", "three_vectors"),
    3: ("between_points", "translate"),
    4: ("unknown_vector", "scalars"),
}
COMPONENTS = tuple(v for v in range(-9, 10) if v)
MARKS = {1: 1, 2: 2, 3: 2, 4: 3}
WORKING_LINES = {1: 3, 2: 4, 3: 4, 4: 6}

KEYS = {
    "add": {"a", "b"},
    "subtract": {"a", "b"},
    "combination": {"a", "b", "p", "q"},
    "three_vectors": {"a", "b", "c"},
    "between_points": {"start", "end"},
    "translate": {"point", "vector", "direction"},
    "unknown_vector": {"a", "b", "p"},
    "scalars": {"a", "b", "p", "q"},
}


# ------------------------------------------------------------ helpers

def is_pair(value, low=-9, high=9, nonzero=True):
    return (isinstance(value, list) and len(value) == 2
            and all(type(v) is int and low <= v <= high and (v != 0 or not nonzero)
                    for v in value))


def plus(u, v):
    return [u[0] + v[0], u[1] + v[1]]


def times(k, u):
    return [k * u[0], k * u[1]]


def column(v):
    return r"\binom{%d}{%d}" % (v[0], v[1]), "(%d, %d)" % (v[0], v[1])


def definitions(pairs):
    tex = r",\quad ".join(r"\mathbf{%s} = %s" % (name, column(v)[0]) for name, v in pairs)
    text = ", ".join("%s = %s" % (name, column(v)[1]) for name, v in pairs)
    return rb.equation(tex, text)


def combination_parts(terms):
    """(tex, text) for terms [(coefficient, name)], e.g. 2a - 3b."""
    tex, text = "", ""
    for coefficient, name in terms:
        size = abs(coefficient)
        shown = "" if size == 1 else str(size)
        if not tex:
            sign = "-" if coefficient < 0 else ""
        else:
            sign = " - " if coefficient < 0 else " + "
        tex += sign + shown + r"\mathbf{%s}" % name
        text += sign + shown + name
    return tex, text


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


# ------------------------------------------------------------ mathematics

def terms_for(par):
    form = par["form"]
    if form == "add":
        return [(1, "a"), (1, "b")]
    if form == "subtract":
        return [(1, "a"), (-1, "b")]
    if form == "combination":
        return [(par["p"], "a"), (par["q"], "b")]
    return [(1, "a"), (1, "b"), (-1, "c")]


def result(par):
    form = par["form"]
    if form in ("add", "subtract", "combination", "three_vectors"):
        total = [0, 0]
        for coefficient, name in terms_for(par):
            total = plus(total, times(coefficient, par[name]))
        return total
    if form == "between_points":
        return plus(par["end"], times(-1, par["start"]))
    if form == "translate":
        sign = 1 if par["direction"] == "image" else -1
        return plus(par["point"], times(sign, par["vector"]))
    if form == "unknown_vector":
        return plus(par["b"], times(-par["p"], par["a"]))
    return plus(times(par["p"], par["a"]), times(par["q"], par["b"]))


def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    form = par.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(par) == KEYS[form] | {"form"}, "Unexpected parameters")
    if form in ("add", "subtract", "combination", "three_vectors", "unknown_vector", "scalars"):
        require(all(is_pair(par[name]) for name in ("a", "b", "c") if name in par),
                "Vector components outside bounds")
    if form == "combination":
        require(type(par["p"]) is int and type(par["q"]) is int
                and 2 <= par["p"] <= 4 and par["q"] in (-3, -2, 2, 3, 4), "Scalars outside bounds")
    elif form == "between_points":
        require(is_pair(par["start"], nonzero=False) and is_pair(par["end"], nonzero=False)
                and par["start"] != par["end"], "Points outside bounds")
    elif form == "translate":
        require(is_pair(par["point"], nonzero=False) and is_pair(par["vector"]),
                "Point or vector outside bounds")
        require(par["direction"] in ("image", "object"), "Unknown direction")
    elif form == "unknown_vector":
        require(type(par["p"]) is int and 2 <= par["p"] <= 4, "Scalar outside bounds")
    elif form == "scalars":
        require(all(type(par[k]) is int and par[k] in (-4, -3, -2, -1, 1, 2, 3, 4)
                    for k in ("p", "q")) and (par["p"], par["q"]) != (1, 1),
                "Scalars outside bounds")
        a, b = par["a"], par["b"]
        require(a[0] * b[1] - a[1] * b[0] != 0, "a and b must not be parallel")
        require(all(abs(v) <= 30 for v in result(par)), "c too large")
    require(result(par) != [0, 0], "Zero result")


# ------------------------------------------------------------ wording and answers

def prompt_for(par):
    form = par["form"]
    if form in ("add", "subtract", "combination", "three_vectors"):
        names = [name for name in ("a", "b", "c") if name in par]
        expression = rb.maths(*combination_parts(terms_for(par)))
        return content([definitions([(name, par[name]) for name in names]),
                        rb.paragraph(rb.text("Work out "), expression,
                                     rb.text(" as a column vector."))])
    if form == "between_points":
        return content([rb.paragraph(
            rb.text("A is the point ({}, {}) and B is the point ({}, {}). Write "
                    .format(*par["start"], *par["end"])),
            rb.maths(r"\overrightarrow{AB}", "vector AB"),
            rb.text(" as a column vector."))])
    if form == "translate":
        vector = rb.maths(*column(par["vector"]))
        if par["direction"] == "image":
            return content([rb.paragraph(
                rb.text("The point P ({}, {}) is translated by the vector ".format(*par["point"])),
                vector, rb.text(". Write down the coordinates of the image of P."))])
        return content([rb.paragraph(
            rb.text("A point Q is translated by the vector "), vector,
            rb.text(". Its image is at ({}, {}). Work out the coordinates of Q."
                    .format(*par["point"])))])
    if form == "unknown_vector":
        return content([
            definitions([("a", par["a"]), ("b", par["b"])]),
            rb.paragraph(rb.text("Find the column vector "), rb.maths(r"\mathbf{x}", "x"),
                         rb.text(" such that "),
                         rb.maths(r"%d\mathbf{a} + \mathbf{x} = \mathbf{b}" % par["p"],
                                  "%da + x = b" % par["p"]),
                         rb.text("."))])
    return content([
        definitions([("a", par["a"]), ("b", par["b"]), ("c", result(par))]),
        rb.paragraph(rb.text("Find the values of p and q such that "),
                     rb.maths(r"p\mathbf{a} + q\mathbf{b} = \mathbf{c}", "pa + qb = c"),
                     rb.text("."))])


def answer_for(par):
    form = par["form"]
    if form == "scalars":
        return ({"kind": "scalars", "p": str(par["p"]), "q": str(par["q"])},
                Content("p = {}, q = {}".format(par["p"], par["q"])))
    value = result(par)
    if form == "translate":
        return ({"kind": "point", "x": str(value[0]), "y": str(value[1])},
                Content("({}, {})".format(*value)))
    tex, text = column(value)
    return ({"kind": "column_vector", "x": str(value[0]), "y": str(value[1])},
            Content(text, tex))


def draw_parameters(rng, form):
    def pair(nonzero=True):
        values = COMPONENTS if nonzero else tuple(range(-9, 10))
        return [rng.choice(values), rng.choice(values)]

    par = {"form": form}
    if form in ("add", "subtract"):
        par.update(a=pair(), b=pair())
    elif form == "combination":
        par.update(a=pair(), b=pair(), p=rng.randint(2, 4), q=rng.choice((-3, -2, 2, 3, 4)))
    elif form == "three_vectors":
        par.update(a=pair(), b=pair(), c=pair())
    elif form == "between_points":
        par.update(start=pair(False), end=pair(False))
    elif form == "translate":
        par.update(point=pair(False), vector=pair(), direction=rng.choice(("image", "object")))
    elif form == "unknown_vector":
        par.update(a=pair(), b=pair(), p=rng.randint(2, 4))
    else:
        par.update(a=[rng.choice(range(-5, 6)) or 1, rng.choice(range(-5, 6)) or 2],
                   b=[rng.choice(range(-5, 6)) or 3, rng.choice(range(-5, 6)) or -1],
                   p=rng.choice((-4, -3, -2, -1, 1, 2, 3, 4)),
                   q=rng.choice((-4, -3, -2, -1, 1, 2, 3, 4)))
    return par


# ------------------------------------------------------------ generator

class ColumnVectors:
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
            raise ValueError("Could not construct a column vector question")
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
        """Repeated addition, translating back, and Cramer's rule for p and q."""
        par, answer = q.parameters, q.answer
        form = par.get("form")
        if form == "scalars":
            a, b = par["a"], par["b"]
            c = [par["p"] * a[0] + par["q"] * b[0], par["p"] * a[1] + par["q"] * b[1]]
            det = a[0] * b[1] - a[1] * b[0]
            p = (c[0] * b[1] - c[1] * b[0]) / det
            q_value = (a[0] * c[1] - a[1] * c[0]) / det
            require(int(answer["p"]) == p and int(answer["q"]) == q_value,
                    "Independent scalars disagree")
            return True
        stated = [int(answer["x"]), int(answer["y"])]
        if form in ("add", "subtract", "combination", "three_vectors"):
            total = [0, 0]
            for coefficient, name in terms_for(par):
                for _ in range(abs(coefficient)):
                    step = par[name] if coefficient > 0 else [-v for v in par[name]]
                    total = [total[0] + step[0], total[1] + step[1]]
            require(stated == total, "Independent combination disagrees")
        elif form == "between_points":
            require([par["start"][0] + stated[0], par["start"][1] + stated[1]] == par["end"],
                    "Start plus vector is not the end point")
        elif form == "translate":
            if par["direction"] == "image":
                require([stated[0] - par["vector"][0], stated[1] - par["vector"][1]] == par["point"],
                        "Translating back does not return to P")
            else:
                require([stated[0] + par["vector"][0], stated[1] + par["vector"][1]] == par["point"],
                        "Translating Q does not reach the image")
        else:
            p = par["p"]
            require([p * par["a"][0] + stated[0], p * par["a"][1] + stated[1]] == par["b"],
                    "pa + x is not b")
        return True