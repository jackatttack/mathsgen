"""Vector geometry: side vectors, ratio division, polygon paths and proof.

Every vector is exact: a pair (p, q) of Fractions meaning p·a + q·b, with O
as the origin, so each point is stored by its position vector. Questions
follow the GCSE pattern: vectors are given along sides from O, and students
build paths to new points.

Levels:
1  A triangle: a side vector, or a vector to a midpoint.
2  A point dividing a side in a given ratio.
3  Paths in a parallelogram or trapezium with points on two sides.
4  Show three points are collinear, or find the scalar that makes them so.
   C is constructed exactly where line MN meets OB extended, so the
   statement is true by construction and the scalar is known exactly.

Diagrams are schematic ("not drawn accurately"): shapes come from a small
seeded set, oriented like other geometry diagrams, and must render cleanly at
every PDF width.
"""
import math
from fractions import Fraction

from . import figures
from . import rich_blocks as rb
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_tex, rational_text, require,
)


INFO = GeneratorInfo(
    id="geometry.vectors.vector_geometry", version=1,
    topic="geometry", subtopic="vectors",
    title="Vector geometry: paths, ratios and collinearity",
    difficulty_descriptions={
        1: "Find a side vector or a vector to a midpoint in a triangle.",
        2: "Find the vector to a point that divides a side in a given ratio.",
        3: "Find vectors between points on the sides of a parallelogram or trapezium.",
        4: "Show three points are collinear, or find the scalar that makes them so.",
    },
    tags=("geometry", "vectors"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("side", "midpoint"),
    2: ("ratio_on_ab", "ratio_on_ob"),
    3: ("parallelogram", "trapezium"),
    4: ("collinear", "find_scalar"),
}
# Unequal ratios m : n in lowest terms with m + n <= 7.
RATIOS = tuple((m, n) for m in range(1, 7) for n in range(1, 7)
               if m != n and m + n <= 7 and math.gcd(m, n) == 1)
POINT_RATIOS = RATIOS + ((1, 1),)          # 1 : 1 is worded as a midpoint
MULTIPLES = {1: (1, 2, 3), 2: (1, 2)}      # OA = alpha a, OB = beta b
TRAPEZIUM_SCALES = (Fraction(1, 2), Fraction(3, 2), Fraction(2), Fraction(3))
SIDE_ASKS = ("AB", "BA")
MIDPOINT_ASKS = ("OM", "AM", "MB")
TRAPEZIUM_ASKS = ("OM", "CM")
LARGEST_SCALAR = 4                          # OC = k b with k at most this
MARKS = {1: 2, 2: 3, 3: 3, 4: 4}
WORKING_LINES = {1: 3, 2: 6, 3: 7, 4: 9}

# Diagram settings: figure directions for a and b, one pair per shape.
SHAPES = (
    ((6, 0), (2, 4)),
    ((6, 0), (4, 4)),
    ((6, 0), (1, 3)),
    ((5, 0), (3, 5)),
    ((6, 0), (-1, 3)),
)
SCENE_WIDTHS = (360, 250, 238)
VERTEX_GAP = 14
POINT_GAP = 13


# ------------------------------------------------------------ form structure

TRIANGLE_FORMS = ("side", "midpoint", "ratio_on_ab", "ratio_on_ob")
PROOF_FORMS = ("collinear", "find_scalar")
KEYS = {
    "side": {"alpha", "beta", "ask"},
    "midpoint": {"alpha", "beta", "ask"},
    "ratio_on_ab": {"alpha", "beta", "m", "n"},
    "ratio_on_ob": {"alpha", "beta", "m", "n"},
    "parallelogram": {"m", "n", "r", "s"},
    "trapezium": {"k_num", "k_den", "m", "n", "ask"},
    "collinear": {"e", "f", "m", "n"},
    "find_scalar": {"e", "f", "m", "n"},
}
FIXED_KEYS = {"form", "shape", "orientation"}
WORD_KEYS = {"ask"}


# ------------------------------------------------------------ vector algebra

def vector(p, q):
    return (Fraction(p), Fraction(q))


ZERO = vector(0, 0)
A_VECTOR = vector(1, 0)
B_VECTOR = vector(0, 1)


def add(u, v):
    return (u[0] + v[0], u[1] + v[1])


def sub(u, v):
    return (u[0] - v[0], u[1] - v[1])


def scale(c, u):
    return (c * u[0], c * u[1])


def divide(start, end, m, n):
    """The point splitting start-end in the ratio m : n, measured from start."""
    return add(start, scale(Fraction(m, m + n), sub(end, start)))


def scalar_through(p):
    """Where line MN meets line OB, for the level 4 construction.

    M = u a on OA and N = (1 - lam) a + lam b on AB. Points on MN are
    M + t(N - M); the a-coefficient vanishes at t = u / (u + lam - 1),
    giving C = t lam b. Returns (t, c) with MC = t MN and OC = c b.
    """
    u = Fraction(p["e"], p["e"] + p["f"])
    lam = Fraction(p["m"], p["m"] + p["n"])
    gap = u + lam - 1
    require(gap > 0, "Line MN does not meet OB beyond O")
    t = u / gap
    return t, t * lam


# ------------------------------------------------------------ geometry of each form

def segment_points(p):
    """Points on sides: name -> (start, end, m, n), dividing start-end as m : n."""
    form = p["form"]
    if form == "midpoint":
        return {"M": ("A", "B", 1, 1)}
    if form == "ratio_on_ab":
        return {"P": ("A", "B", p["m"], p["n"])}
    if form == "ratio_on_ob":
        return {"P": ("O", "B", p["m"], p["n"])}
    if form == "parallelogram":
        return {"M": ("A", "B", p["m"], p["n"]), "N": ("C", "B", p["r"], p["s"])}
    if form == "trapezium":
        return {"M": ("A", "B", p["m"], p["n"])}
    if form in PROOF_FORMS:
        return {"M": ("O", "A", p["e"], p["f"]), "N": ("A", "B", p["m"], p["n"])}
    return {}


def trapezium_scale(p):
    return Fraction(p["k_num"], p["k_den"])


def position_vectors(p):
    form = p["form"]
    if form in TRIANGLE_FORMS:
        points = {"O": ZERO, "A": vector(p["alpha"], 0), "B": vector(0, p["beta"])}
    elif form == "parallelogram":
        points = {"O": ZERO, "A": A_VECTOR, "C": B_VECTOR, "B": vector(1, 1)}
    elif form == "trapezium":
        points = {"O": ZERO, "A": A_VECTOR, "C": B_VECTOR,
                  "B": vector(trapezium_scale(p), 1)}
    else:
        _, c = scalar_through(p)
        points = {"O": ZERO, "A": A_VECTOR, "B": B_VECTOR, "C": vector(0, c)}
    for name, (start, end, m, n) in segment_points(p).items():
        points[name] = divide(points[start], points[end], m, n)
    return points


def given_sides(p):
    """(start, end, vector, labelled on the diagram) for each given vector."""
    form = p["form"]
    if form in TRIANGLE_FORMS:
        return [("O", "A", vector(p["alpha"], 0), True),
                ("O", "B", vector(0, p["beta"]), True)]
    if form in PROOF_FORMS:
        return [("O", "A", A_VECTOR, True), ("O", "B", B_VECTOR, True)]
    sides = [("O", "A", A_VECTOR, True), ("O", "C", B_VECTOR, True)]
    if form == "trapezium":
        sides.append(("C", "B", vector(trapezium_scale(p), 0), False))
    return sides


def asked(p):
    """(start, end) of the vector the question asks for."""
    form = p["form"]
    if form in ("side", "midpoint", "trapezium"):
        return p["ask"][0], p["ask"][1]
    return {"ratio_on_ab": ("O", "P"), "ratio_on_ob": ("A", "P"),
            "parallelogram": ("M", "N")}[form]


# ------------------------------------------------------------ checks

def check_parameters(p, level):
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(p) == KEYS[form] | FIXED_KEYS, "Unexpected parameters")
    require(all(type(p[name]) is int for name in (KEYS[form] - WORD_KEYS) | {"shape"}),
            "Integer parameters required")
    require(0 <= p["shape"] < len(SHAPES), "Unknown shape")
    require(figures.valid_orientation(p["orientation"]), "Invalid orientation")

    if form in TRIANGLE_FORMS:
        require(p["alpha"] in MULTIPLES[level] and p["beta"] in MULTIPLES[level],
                "Multiple outside bounds")
    if form == "side":
        require(p["ask"] in SIDE_ASKS, "Unexpected vector requested")
    elif form == "midpoint":
        require(p["ask"] in MIDPOINT_ASKS, "Unexpected vector requested")
    elif form == "trapezium":
        require(p["ask"] in TRAPEZIUM_ASKS, "Unexpected vector requested")
        require((p["m"], p["n"]) in POINT_RATIOS, "Ratio outside bounds")
        require(p["k_den"] > 0 and math.gcd(p["k_num"], p["k_den"]) == 1
                and trapezium_scale(p) in TRAPEZIUM_SCALES, "Trapezium scale outside bounds")
    else:
        require((p["m"], p["n"]) in RATIOS, "Ratio outside bounds")
    if form == "parallelogram":
        require((p["r"], p["s"]) in POINT_RATIOS, "Ratio outside bounds")

    if form in PROOF_FORMS:
        require((p["e"], p["f"]) in POINT_RATIOS, "Ratio outside bounds")
        t, c = scalar_through(p)
        require(t > 1 and c > 1, "C must lie beyond B on OB extended")
        require(c.denominator <= 2 and c <= LARGEST_SCALAR, "Awkward scalar")
    else:
        points = position_vectors(p)
        start, end = asked(p)
        require(sub(points[end], points[start]) != ZERO, "Zero vector requested")


# ------------------------------------------------------------ notation

def arrow_tex(name):
    return r"\overrightarrow{" + name + "}"


def bold(letter):
    return rb.maths(r"\mathbf{" + letter + "}", letter)


def combination(v):
    """(tex, text) for p a + q b, leading with a positive term when possible."""
    terms = [(v[0], "a"), (v[1], "b")]
    if v[0] < 0 < v[1]:
        terms.reverse()
    tex, text = [], []
    for coefficient, letter in terms:
        if coefficient == 0:
            continue
        size = abs(coefficient)
        if size == 1:
            size_tex = size_text = ""
        elif size.denominator == 1:
            size_tex = size_text = str(size.numerator)
        else:
            size_tex = r"\frac{%d}{%d}" % (size.numerator, size.denominator)
            size_text = "(%d/%d)" % (size.numerator, size.denominator)
        if tex:
            sign = " - " if coefficient < 0 else " + "
        else:
            sign = "-" if coefficient < 0 else ""
        tex.append(sign + size_tex + r"\mathbf{" + letter + "}")
        text.append(sign + size_text + letter)
    require(tex, "Zero vector")
    return "".join(tex), "".join(text)


def point_sentence(name, start, end, m, n):
    if m == n:
        return "{} is the midpoint of {}{}.".format(name, start, end)
    return "{0} is the point on {1}{2} such that {1}{0} : {0}{2} = {3} : {4}.".format(
        name, start, end, m, n)


def given_equation(p):
    tex_parts, text_parts = [], []
    for start, end, value, _ in given_sides(p):
        value_tex, value_text = combination(value)
        tex_parts.append(arrow_tex(start + end) + " = " + value_tex)
        text_parts.append("vector {}{} = {}".format(start, end, value_text))
    return rb.equation(r",\quad ".join(tex_parts), ", ".join(text_parts))


def prompt_for(p):
    form = p["form"]
    if form == "parallelogram":
        opening = "OABC is a parallelogram."
    elif form == "trapezium":
        opening = "OABC is a trapezium with CB parallel to OA."
    else:
        opening = "OAB is a triangle."
    blocks = [rb.prose(opening), given_equation(p)]
    for name, (start, end, m, n) in sorted(segment_points(p).items()):
        blocks.append(rb.prose(point_sentence(name, start, end, m, n)))

    if form == "collinear":
        _, c = scalar_through(p)
        c_tex, c_text = combination(vector(0, c))
        blocks.append(rb.paragraph(
            rb.text("C is the point such that "),
            rb.maths(arrow_tex("OC") + " = " + c_tex, "vector OC = " + c_text),
            rb.text("."),
        ))
        blocks.append(rb.prose("Show that M, N and C lie on a straight line."))
    elif form == "find_scalar":
        blocks.append(rb.paragraph(
            rb.text("C is the point on OB extended such that "),
            rb.maths(arrow_tex("OC") + r" = k\mathbf{b}", "vector OC = kb"),
            rb.text(", where k is a constant."),
        ))
        blocks.append(rb.prose("M, N and C lie on a straight line. Find the value of k."))
    else:
        start, end = asked(p)
        runs = [rb.text("Find "), rb.maths(arrow_tex(start + end), "vector " + start + end),
                rb.text(" in terms of "), bold("a"), rb.text(" and "), bold("b"),
                rb.text(".")]
        if form not in ("side", "midpoint"):
            runs.append(rb.text(" Give your answer in its simplest form."))
        blocks.append(rb.paragraph(*runs))

    plain = []
    for block in blocks:
        if block["kind"] == "equation":
            plain.append(block["text"] + ".")
        elif "runs" in block:
            plain.append("".join(run["text"] for run in block["runs"]))
        else:
            plain.append(block["text"])
    return Content(" ".join(plain), blocks=tuple(blocks))


def answer_for(p):
    form = p["form"]
    if form == "find_scalar":
        _, c = scalar_through(p)
        return ({"kind": "rational", "value": rational_text(c)},
                Content("k = " + rational_text(c), "k = " + rational_tex(c)))
    points = position_vectors(p)
    if form == "collinear":
        t, _ = scalar_through(p)
        mn = sub(points["N"], points["M"])
        mc = sub(points["C"], points["M"])
        answer = {
            "kind": "collinear",
            "mn_a": rational_text(mn[0]), "mn_b": rational_text(mn[1]),
            "mc_a": rational_text(mc[0]), "mc_b": rational_text(mc[1]),
            "multiple": rational_text(t),
        }
        display = (
            "vector MN = {}; vector MC = {} = {} times vector MN. MC is a multiple "
            "of MN and both pass through M, so M, N and C are collinear."
        ).format(combination(mn)[1], combination(mc)[1], rational_text(t))
        return answer, Content(display)
    start, end = asked(p)
    value = sub(points[end], points[start])
    value_tex, value_text = combination(value)
    answer = {"kind": "vector", "a": rational_text(value[0]), "b": rational_text(value[1])}
    display = Content("vector {}{} = {}".format(start, end, value_text),
                      arrow_tex(start + end) + " = " + value_tex)
    return answer, display


# ------------------------------------------------------------ diagrams

def to_figure(value, shape):
    (ax, ay), (bx, by) = SHAPES[shape]
    return (float(value[0] * ax + value[1] * bx), float(value[0] * ay + value[1] * by))


def dashed_segment(p):
    form = p["form"]
    if form == "side":
        return None
    if form == "midpoint":
        return ("O", "M") if p["ask"] == "OM" else None
    if form in PROOF_FORMS:
        return ("M", "C")
    return asked(p)


def chevron_position(busy):
    """Direction arrow position along a side, clear of any division tick."""
    for candidate in (0.5, 0.3, 0.7):
        if all(abs(candidate - float(b)) > 0.15 for b in busy):
            return candidate
    return 0.85


def outward_label(point, centre, gap, text):
    outward = figures.unit(figures.minus(point, centre))
    return {"type": "label", "text": text,
            "point": figures.rounded((point[0] + outward[0] * gap,
                                      point[1] + outward[1] * gap))}


def scene_for(p):
    form = p["form"]
    points = position_vectors(p)
    figure = {name: to_figure(value, p["shape"]) for name, value in points.items()}
    placed, height = figures.place(figure, p["orientation"])

    outline = ["O", "A", "B", "C"] if form in ("parallelogram", "trapezium") else ["O", "A", "B"]
    centre = (sum(placed[v][0] for v in outline) / len(outline),
              sum(placed[v][1] for v in outline) / len(outline))
    divisions = segment_points(p)

    nodes = [{"type": "polygon", "points": [placed[v] for v in outline]}]
    if form in PROOF_FORMS:
        nodes.append({"type": "line", "points": [placed["B"], placed["C"]]})
    dashed = dashed_segment(p)
    if dashed:
        nodes.append({"type": "line", "points": [placed[dashed[0]], placed[dashed[1]]],
                      "dashed": True})
    for name, (start, end, m, n) in sorted(divisions.items()):
        nodes.append({"type": "ticks", "points": [placed[start], placed[end]],
                      "position": float(Fraction(m, m + n))})
    for start, end, value, labelled in given_sides(p):
        busy = [Fraction(m, m + n) for s, e, m, n in divisions.values() if (s, e) == (start, end)]
        nodes.append({"type": "parallel", "points": [placed[start], placed[end]],
                      "position": chevron_position(busy)})
        if labelled:
            text = combination(value)[1]
            nodes.append({"type": "label", "text": text,
                          "point": figures.side_label(placed[start], placed[end],
                                                      centre, len(text))})
    vertices = outline + (["C"] if form in PROOF_FORMS else [])
    for name in vertices:
        nodes.append(outward_label(placed[name], centre, VERTEX_GAP, name))
    for name in sorted(divisions):
        nodes.append(outward_label(placed[name], centre, POINT_GAP, name))
    return {
        "kind": "scene", "version": 1, "width": figures.CANVAS_WIDTH,
        "height": height, "caption": "Not drawn accurately", "nodes": nodes,
    }


def renders_cleanly(scene):
    """Renders at every PDF width, including the 238 pt working-row layout."""
    from .visuals import drawing_for
    try:
        for width in SCENE_WIDTHS:
            drawing_for(scene, width)
    except ValueError:
        return False
    return True


def choose_orientation(rng, build):
    candidates = list(figures.ORIENTATIONS)
    rng.shuffle(candidates)
    for orientation in candidates:
        if renders_cleanly(build(list(orientation))):
            return list(orientation)
    raise ValueError("No orientation renders this figure cleanly")


# ------------------------------------------------------------ generation

def draw_parameters(rng, level, form):
    """Candidate parameters for a form chosen once per question."""
    p = {"form": form, "shape": rng.randrange(len(SHAPES)), "orientation": [0, False]}
    if form in TRIANGLE_FORMS:
        p["alpha"] = rng.choice(MULTIPLES[level])
        p["beta"] = rng.choice(MULTIPLES[level])
    if form == "side":
        p["ask"] = rng.choice(SIDE_ASKS)
    elif form == "midpoint":
        p["ask"] = rng.choice(MIDPOINT_ASKS)
    elif form in ("ratio_on_ab", "ratio_on_ob"):
        p["m"], p["n"] = rng.choice(RATIOS)
    elif form == "parallelogram":
        p["m"], p["n"] = rng.choice(RATIOS)
        p["r"], p["s"] = rng.choice(POINT_RATIOS)
    elif form == "trapezium":
        k = rng.choice(TRAPEZIUM_SCALES)
        p.update(k_num=k.numerator, k_den=k.denominator, ask=rng.choice(TRAPEZIUM_ASKS))
        p["m"], p["n"] = rng.choice(POINT_RATIOS)
    else:
        p["e"], p["f"] = rng.choice(POINT_RATIOS)
        p["m"], p["n"] = rng.choice(RATIOS)
    return p


class VectorGeometry:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        form = rng.choice(FORMS[difficulty])
        for attempt in range(300):
            p = draw_parameters(rng, difficulty, form)
            try:
                check_parameters(p, difficulty)
                p["orientation"] = choose_orientation(
                    rng, lambda orientation: scene_for(dict(p, orientation=orientation)))
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a vector geometry question")
        answer, display = answer_for(p)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(p), answer=answer,
            answer_display=display, worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=WORKING_LINES[difficulty]),
            parameters=p, question_visuals=(scene_for(p),),
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        require(type(q.difficulty) is int and q.difficulty in (1, 2, 3, 4),
                "Invalid difficulty")
        require(q.settings == {}, "Unsupported settings")
        check_parameters(q.parameters, q.difficulty)
        answer, display = answer_for(q.parameters)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Answer display mismatch")
        require(q.prompt == prompt_for(q.parameters), "Prompt mismatch")
        require(q.visual_assets("questions") == (scene_for(q.parameters),),
                "Diagram mismatch")
        require(q.visual_assets("answers") == (), "Unexpected answer visuals")
        return True

    def validate_independently(self, q):
        """Rebuild every point in coordinates from a fixed generic basis.

        Uses the section formula and a 2x2 line intersection, never the
        generator's position-vector algebra or scalar_through().
        """
        p = q.parameters
        form = p.get("form")
        require(form in FORMS.get(q.difficulty, ()), "Unexpected form")
        a = (Fraction(3), Fraction(1))
        b = (Fraction(1), Fraction(4))

        def comb(x, y):
            return (x * a[0] + y * b[0], x * a[1] + y * b[1])

        def section(start, end, m, n):
            return tuple((n * start[i] + m * end[i]) / (m + n) for i in (0, 1))

        def minus(first, second):
            return (first[0] - second[0], first[1] - second[1])

        O = (Fraction(0), Fraction(0))
        if form in TRIANGLE_FORMS:
            A, B = comb(p["alpha"], 0), comb(0, p["beta"])
            points = {"O": O, "A": A, "B": B}
            if form == "midpoint":
                points["M"] = section(A, B, 1, 1)
            elif form == "ratio_on_ab":
                points["P"] = section(A, B, p["m"], p["n"])
            elif form == "ratio_on_ob":
                points["P"] = section(O, B, p["m"], p["n"])
        elif form == "parallelogram":
            A, C = a, b
            B = (A[0] + C[0], A[1] + C[1])
            points = {"O": O, "A": A, "B": B, "C": C,
                      "M": section(A, B, p["m"], p["n"]),
                      "N": section(C, B, p["r"], p["s"])}
        elif form == "trapezium":
            k = Fraction(p["k_num"], p["k_den"])
            A, C = a, b
            B = (C[0] + k * A[0], C[1] + k * A[1])
            points = {"O": O, "A": A, "B": B, "C": C,
                      "M": section(A, B, p["m"], p["n"])}
        else:
            M = section(O, a, p["e"], p["f"])
            N = section(a, b, p["m"], p["n"])
            d = minus(N, M)
            det = b[0] * d[1] - d[0] * b[1]
            require(det != 0, "MN is parallel to OB")
            s = (d[1] * M[0] - d[0] * M[1]) / det   # M + t d = s b
            if form == "find_scalar":
                require(Fraction(q.answer["value"]) == s, "Independent scalar disagrees")
                return True
            C = (s * b[0], s * b[1])
            mn, mc = minus(N, M), minus(C, M)
            require(comb(Fraction(q.answer["mn_a"]), Fraction(q.answer["mn_b"])) == mn,
                    "Independent MN disagrees")
            require(comb(Fraction(q.answer["mc_a"]), Fraction(q.answer["mc_b"])) == mc,
                    "Independent MC disagrees")
            t = Fraction(q.answer["multiple"])
            require((t * mn[0], t * mn[1]) == mc, "MC is not the stated multiple of MN")
            return True
        start, end = asked(p)
        stated = comb(Fraction(q.answer["a"]), Fraction(q.answer["b"]))
        require(stated == minus(points[end], points[start]),
                "Independent reconstruction disagrees")
        return True