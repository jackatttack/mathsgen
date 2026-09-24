"""Graph transformations of y = f(x): translations, reflections and combinations.

f is the quadratic (x - p)^2 + q with an integer turning point (p, q). Every
image is stored as g(x) = s * f(r * x + a) + b with s, r in {1, -1}: a is the
inside shift, b the outside shift, r = -1 reflects in the y-axis and s = -1
reflects in the x-axis. Plots use a fixed grid from -8 to 8.
"""
from . import rich_blocks as rb
from .core import Content, GeneratorInfo, LayoutHint, Question, make_context, require
from .iteration import join_terms


INFO = GeneratorInfo(
    id="algebra.graphs.transformations", version=1,
    topic="algebra", subtopic="graph_transformations",
    title="Graph transformations: translations and reflections of y = f(x)",
    difficulty_descriptions={
        1: "Find the turning point after a translation or a reflection.",
        2: "Describe a translation by a column vector, or name a reflection.",
        3: "Write the equation of a transformed graph shown on a grid.",
        4: "Combine two transformations, or expand f(x + a) for a given quadratic.",
    },
    tags=("algebra", "graphs", "transformations", "functions"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("point_translate", "point_reflect"),
    2: ("describe_translation", "describe_reflection"),
    3: ("graph_translation", "graph_reflection"),
    4: ("combined_point", "expand_translation"),
}
TURNING = tuple(range(-3, 4))
SHIFTS = tuple(v for v in range(-4, 5) if v)
MARKS = {1: 1, 2: 2, 3: 2, 4: 3}
WORKING_LINES = {1: 2, 2: 3, 3: 3, 4: 5}
KEYS = {"p", "q", "shift_x", "shift_y", "reflect_in", "reflect_out"}


# ------------------------------------------------------------ mathematics

def f(par, x):
    return (x - par["p"]) ** 2 + par["q"]


def g(par, x):
    s = -1 if par["reflect_out"] else 1
    r = -1 if par["reflect_in"] else 1
    return s * f(par, r * x + par["shift_x"]) + par["shift_y"]


def image_vertex(par):
    r = -1 if par["reflect_in"] else 1
    s = -1 if par["reflect_out"] else 1
    return (par["p"] - par["shift_x"]) * r, s * par["q"] + par["shift_y"]


def operations(par):
    return [name for name in ("shift_x", "shift_y", "reflect_in", "reflect_out") if par[name]]


def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    form = par.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(par) == KEYS | {"form"}, "Unexpected parameters")
    require(all(type(par[k]) is int for k in KEYS), "Integer parameters required")
    require(par["p"] in TURNING and par["q"] in TURNING, "Turning point outside bounds")
    require(par["shift_x"] in SHIFTS + (0,) and par["shift_y"] in SHIFTS + (0,),
            "Shifts outside bounds")
    require(par["reflect_in"] in (0, 1) and par["reflect_out"] in (0, 1), "Flags must be 0 or 1")
    ops = operations(par)
    if form in ("point_translate", "describe_translation"):
        require(len(ops) == 1 and ops[0] in ("shift_x", "shift_y"), "One translation")
    elif form in ("point_reflect", "describe_reflection", "graph_reflection"):
        require(len(ops) == 1 and ops[0] in ("reflect_in", "reflect_out"), "One reflection")
        require(par["p"] != 0 and par["q"] != 0, "The reflection must move the turning point")
    elif form == "graph_translation":
        require(1 <= len(ops) <= 2 and set(ops) <= {"shift_x", "shift_y"}, "A translation")
    elif form == "combined_point":
        require(len(ops) == 2 and "reflect_in" not in ops, "Two transformations")
    else:
        require(ops == ["shift_x"] or set(ops) == {"shift_x", "shift_y"}, "A horizontal shift")
    x, y = image_vertex(par)
    require(-6 <= x <= 6 and -6 <= y <= 6, "Image outside the grid")


# ------------------------------------------------------------ notation

def inside_parts(par):
    r = -1 if par["reflect_in"] else 1
    return join_terms([(r, "x", "x"), (par["shift_x"], "", "")])


def image_equation(par):
    """(tex, text) for y = s f(r x + a) + b."""
    inner_tex, inner_text = inside_parts(par)
    sign = "-" if par["reflect_out"] else ""
    tex, text = "y = %sf(%s)" % (sign, inner_tex), "y = %sf(%s)" % (sign, inner_text)
    b = par["shift_y"]
    if b:
        tex += (" - %d" % -b) if b < 0 else (" + %d" % b)
        text += (" - %d" % -b) if b < 0 else (" + %d" % b)
    return tex, text


def quadratic_parts(b, c):
    return join_terms([(1, "x^{2}", "x^2"), (b, "x", "x"), (c, "", "")])


def content(runs, display=None):
    text = "".join(run["text"] for run in runs)
    return Content(text, blocks=(rb.paragraph(*runs),))


def plot(par):
    xs = [i / 4 for i in range(-32, 33)]
    return {
        "kind": "plot", "version": 1, "x_range": [-8, 8], "y_range": [-8, 8],
        "x_step": 2, "y_step": 2, "minor_divisions": 2, "equal_units": True,
        "x_label": "x", "y_label": "y",
        "curves": [{"segments": [[[x, float(f(par, x))] for x in xs]]},
                   {"segments": [[[x, float(g(par, x))] for x in xs]], "dashed": True}],
    }


def visuals_for(par):
    return (plot(par),) if par["form"] in ("graph_translation", "graph_reflection") else ()


def prompt_for(par):
    form = par["form"]
    p, q = par["p"], par["q"]
    turning = "The graph of y = f(x) has a turning point at ({}, {}). ".format(p, q)
    eq_tex, eq_text = image_equation(par)
    if form in ("point_translate", "point_reflect", "combined_point"):
        return content([rb.text(turning + "Write down the coordinates of the turning point of "
                                "the graph of "), rb.maths(eq_tex, eq_text), rb.text(".")])
    if form in ("describe_translation", "describe_reflection"):
        return content([rb.text(turning + "Describe fully the single transformation that maps the graph "
                                "of y = f(x) onto the graph of "), rb.maths(eq_tex, eq_text),
                        rb.text(".")])
    if form in ("graph_translation", "graph_reflection"):
        return content([rb.text("The graph of y = f(x) is shown as a solid curve, with a turning "
                                "point at ({}, {}). The dashed curve is the image of y = f(x) "
                                "after a transformation. Write down the equation of the dashed "
                                "curve in terms of f.".format(p, q))])
    b, c = -2 * p, p * p + q
    fx = quadratic_parts(b, c)
    return content([rb.text("Given that "), rb.maths("f(x) = " + fx[0], "f(x) = " + fx[1]),
                    rb.text(", write "), rb.maths(eq_tex[4:], eq_text[4:]),
                    rb.text(" in the form "), rb.maths("x^{2} + px + q", "x^2 + px + q"),
                    rb.text(".")])


def answer_for(par):
    form = par["form"]
    if form in ("point_translate", "point_reflect", "combined_point"):
        x, y = image_vertex(par)
        return {"kind": "point", "x": str(x), "y": str(y)}, Content("({}, {})".format(x, y))
    if form == "describe_translation":
        vector = (-par["shift_x"], par["shift_y"])
        return ({"kind": "translation", "x": str(vector[0]), "y": str(vector[1])},
                Content("Translation by the vector ({}, {})".format(*vector),
                        r"\mathrm{Translation}\ \binom{%d}{%d}" % vector))
    if form == "describe_reflection":
        axis = "x-axis" if par["reflect_out"] else "y-axis"
        return {"kind": "choice", "value": axis}, Content("Reflection in the " + axis)
    if form in ("graph_translation", "graph_reflection"):
        tex, text = image_equation(par)
        structure = {k: str(par[k]) for k in ("shift_x", "shift_y", "reflect_in", "reflect_out")}
        return dict({"kind": "function_equation", "text": text}, **structure), Content(text, tex)
    a0, a1, a2 = g(par, 0), g(par, 1), g(par, -1)
    c2 = (a1 + a2 - 2 * a0) // 2
    c1 = (a1 - a2) // 2
    tex, text = quadratic_parts(c1, a0)
    return ({"kind": "polynomial", "coefficients": [str(a0), str(c1), str(c2)]},
            Content("y = " + text, "y = " + tex))


def draw_parameters(rng, form):
    par = {"form": form, "p": rng.choice(TURNING), "q": rng.choice(TURNING),
           "shift_x": 0, "shift_y": 0, "reflect_in": 0, "reflect_out": 0}
    if form in ("point_translate", "describe_translation"):
        par[rng.choice(("shift_x", "shift_y"))] = rng.choice(SHIFTS)
    elif form in ("point_reflect", "describe_reflection", "graph_reflection"):
        par[rng.choice(("reflect_in", "reflect_out"))] = 1
    elif form == "graph_translation":
        par["shift_x"] = rng.choice(SHIFTS + (0,))
        par["shift_y"] = rng.choice(SHIFTS + (0,))
    elif form == "combined_point":
        first, second = rng.sample(("shift_x", "shift_y", "reflect_out"), 2)
        for name in (first, second):
            par[name] = 1 if name == "reflect_out" else rng.choice(SHIFTS)
    else:
        par["shift_x"] = rng.choice(SHIFTS)
        if rng.random() < 0.5:
            par["shift_y"] = rng.choice(SHIFTS)
    return par


# ------------------------------------------------------------ generator

class GraphTransformations:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        form = rng.choice(FORMS[difficulty])
        for attempt in range(2000):
            par = draw_parameters(rng, form)
            try:
                check_parameters(par, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a graph transformation question")
        answer, display = answer_for(par)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(par),
            answer=answer, answer_display=display, worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=WORKING_LINES[difficulty]),
            parameters=par, question_visuals=visuals_for(par),
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
        require(q.visual_assets("questions") == visuals_for(q.parameters), "Graph mismatch")
        return True

    def validate_independently(self, q):
        """Evaluate the image directly; confirm turning points by symmetry, reflections
        pointwise, graph answers against the dashed samples, expansions at seven x."""
        par, answer = q.parameters, q.answer
        form = par["form"]

        def base(x):
            return (x - par["p"]) ** 2 + par["q"]

        def image(x):
            inside = (-x if par["reflect_in"] else x) + par["shift_x"]
            value = base(inside)
            return (-value if par["reflect_out"] else value) + par["shift_y"]

        if form in ("point_translate", "point_reflect", "combined_point"):
            x, y = int(answer["x"]), int(answer["y"])
            require(image(x) == y and image(x - 1) == image(x + 1) != y,
                    "Stated point is not the turning point of the image")
        elif form == "describe_translation":
            dx, dy = int(answer["x"]), int(answer["y"])
            require(all(image(x + dx) == base(x) + dy for x in range(-5, 6)),
                    "Stated vector does not map f onto the image")
        elif form == "describe_reflection":
            if answer["value"] == "x-axis":
                require(all(image(x) == -base(x) for x in range(-5, 6)), "Not a reflection in x")
            else:
                require(all(image(x) == base(-x) for x in range(-5, 6)), "Not a reflection in y")
        elif form in ("graph_translation", "graph_reflection"):
            dashed = q.visual_assets("questions")[0]["curves"][1]["segments"][0]
            s = -1 if answer["reflect_out"] == "1" else 1
            r = -1 if answer["reflect_in"] == "1" else 1
            a, b = int(answer["shift_x"]), int(answer["shift_y"])
            for x, y in dashed:
                require(abs(s * base(r * x + a) + b - y) < 1e-9, "Stated equation misses the curve")
        else:
            c0, c1, c2 = (int(c) for c in answer["coefficients"])
            require(c2 == 1 and all(c0 + c1 * x + c2 * x * x == image(x) for x in range(-3, 4)),
                    "Expansion disagrees")
        return True