"""Similar shapes drawn to scale: lengths, nested triangles, areas and volumes.

Forms (two per level):
  1  enlarge / reduce          similar triangles in independent orientations;
                               correspondence comes from "ABC is similar to PQR"
  2  nested / nested_part      DE parallel to BC; find BC, or recover DB
  3  area / area_reverse       area of the image, or a length from two areas
  4  volume / area_to_volume   length from volumes, or volume from surface areas

Every figure is drawn from its true measurements at a common scale, so a pair
of similar shapes really looks similar. Seeded choices (shape, which sides
are labelled, letters, orientations, base angle) are stored in the
parameters and validation rebuilds the exact scene. Independent checks use
cross-multiplied invariants of the displayed numbers only.
"""
import math
from fractions import Fraction

from . import circle_figures, figures
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)


INFO = GeneratorInfo(
    id="geometry.similarity.scale_factors", version=2,
    topic="geometry", subtopic="similarity",
    title="Similar shapes: lengths, areas and volumes",
    difficulty_descriptions={
        1: "Find a corresponding length in similar triangles, enlarging or reducing.",
        2: "Use nested similar triangles to find a side or a recovered part.",
        3: "Use a length scale factor for areas, or recover a length from two areas.",
        4: "Use volume or surface-area scale factors for similar cuboids.",
    },
    tags=("geometry", "similarity", "scale_factors", "area", "volume"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("enlarge", "reduce"),
    2: ("nested", "nested_part"),
    3: ("area", "area_reverse"),
    4: ("volume", "area_to_volume"),
}
FAMILY = {
    "enlarge": "pair", "reduce": "pair", "nested": "nested", "nested_part": "nested",
    "area": "area", "area_reverse": "area", "volume": "solid", "area_to_volume": "solid",
}
KEYS = {
    "pair": {"sides", "scale", "known", "target", "orientations"},
    "nested": {"ad", "db", "de", "bc", "beta", "orientation"},
    "area": {"base", "height", "offset", "scale", "orientations"},
    "solid": {"dims", "scale", "edge"},
}
PAIR_SCALES = ((2, 1), (3, 1), (3, 2), (5, 2), (4, 3), (5, 3))
SCALES = ((2, 1), (3, 1), (3, 2), (5, 2))
NAME_SETS = {
    "pair": ("ABCPQR", "DEFKLM", "ABCXYZ", "PQRSTU", "EFGLMN"),
    "area": ("ABCPQR", "DEFKLM", "ABCXYZ", "PQRSTU", "EFGLMN"),
    "nested": ("ABCDE", "PQRST", "JKLMN", "UVWXY", "EFGHK"),
    "solid": ("AB", "PQ", "ST", "XY", "LM"),
}
MARKS = {1: 2, 2: 3, 3: 3, 4: 4}
SMALLEST_ANGLE = 28
PAIR_GAP = 40
PAIR_HEIGHT = 170
LETTER_GAP = 14
# side index -> the two vertex indices it joins (side i is opposite vertex i)
SIDE_ENDS = {0: (1, 2), 1: (2, 0), 2: (0, 1)}


# ------------------------------------------------------------ mathematics

def ratio(p):
    n, d = p["scale"]
    return Fraction(n, d)


def triangle_angles(sides):
    a, b, c = (float(v) for v in sides)
    def at(opposite, first, second):
        cosine = (first * first + second * second - opposite * opposite) / (2 * first * second)
        return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
    return at(a, b, c), at(b, c, a), at(c, a, b)


def good_triangle(sides, smallest=SMALLEST_ANGLE):
    a, b, c = sides
    if 2 * max(sides) >= a + b + c or len(set(sides)) < 3:
        return False
    return min(triangle_angles(sides)) >= smallest


def area_sides(p):
    c, h, o = p["base"], p["height"], p["offset"]
    return (math.hypot(c - o, h), math.hypot(o, h), float(c))


def answer_for(p):
    """(value, unit) by the textbook route."""
    form = p["form"]
    if form == "enlarge":
        return p["sides"][p["target"]] * ratio(p), "cm"
    if form == "reduce":
        return Fraction(p["sides"][p["target"]]), "cm"
    if form == "nested":
        return Fraction(p["bc"]), "cm"
    if form == "nested_part":
        return Fraction(p["db"]), "cm"
    if form == "area":
        return Fraction(p["base"] * p["height"], 2) * ratio(p) ** 2, "cm^2"
    if form == "area_reverse":
        return p["base"] * ratio(p), "cm"
    if form == "volume":
        return p["dims"][p["edge"]] * ratio(p), "cm"
    l, w, h = p["dims"]
    return l * w * h * ratio(p) ** 3, "cm^3"


def solid_facts(p):
    l, w, h = p["dims"]
    k = ratio(p)
    volume, surface = l * w * h, 2 * (l * w + w * h + h * l)
    return volume, volume * k ** 3, surface, surface * k ** 2


def check_parameters(p, level):
    """Check structure and ranges; return (value, unit)."""
    require(isinstance(p, dict), "Parameters must be a dictionary")
    form = p.get("form")
    require(form in FORMS[level], "Unexpected form for this level")
    family = FAMILY[form]
    require(set(p) == {"form", "names"} | KEYS[family], "Unexpected parameters")
    require(p["names"] in NAME_SETS[family], "Invalid letters")
    if family in ("pair", "area"):
        pair = p["orientations"]
        require(isinstance(pair, list) and len(pair) == 2
                and all(figures.valid_orientation(o) for o in pair), "Invalid orientations")
    if family == "nested":
        require(figures.valid_orientation(p["orientation"]), "Invalid orientation")
    if "scale" in p:
        scales = PAIR_SCALES if family == "pair" else SCALES
        require(isinstance(p["scale"], list) and tuple(p["scale"]) in scales,
                "Invalid scale factor")
        d = p["scale"][1]

    if family == "pair":
        sides = p["sides"]
        require(isinstance(sides, list) and len(sides) == 3
                and all(type(v) is int and v % d == 0 and 2 <= v <= 16 for v in sides),
                "Invalid sides")
        require(good_triangle(sides), "Triangle too narrow or not scalene")
        require(max(sides) * ratio(p) <= 30, "Image too large")
        require(p["known"] in (0, 1, 2) and p["target"] in (0, 1, 2)
                and p["known"] != p["target"], "Invalid side choice")
    elif family == "nested":
        values = [p[key] for key in ("ad", "db", "de", "bc", "beta")]
        require(all(type(v) is int for v in values), "Whole numbers required")
        require(3 <= p["ad"] <= 10 and 2 <= p["db"] <= 10 and 3 <= p["de"] <= 15
                and p["bc"] <= 30, "Lengths outside bounds")
        require(p["de"] * (p["ad"] + p["db"]) == p["bc"] * p["ad"],
                "DE and BC are not in the ratio AD : AB")
        require(45 <= p["beta"] <= 80, "Base angle outside bounds")
        ab = p["ad"] + p["db"]
        ac = math.sqrt(ab * ab + p["bc"] ** 2
                       - 2 * ab * p["bc"] * math.cos(math.radians(p["beta"])))
        require(min(triangle_angles((p["bc"], ac, ab))) >= 30, "Triangle too narrow")
    elif family == "area":
        c, h, o = p["base"], p["height"], p["offset"]
        require(all(type(v) is int for v in (c, h, o)), "Whole numbers required")
        require(4 <= c <= 12 and c % d == 0 and 3 <= h <= 10 and -3 <= o <= c + 3,
                "Triangle outside bounds")
        require((c * h) % 2 == 0, "Area must be whole")
        require(min(triangle_angles(area_sides(p))) >= 25, "Triangle too narrow")
        require((Fraction(c * h, 2) * ratio(p) ** 2).denominator == 1,
                "Image area must be whole")
    else:
        dims = p["dims"]
        require(isinstance(dims, list) and len(dims) == 3
                and all(type(v) is int and v % d == 0 and 2 <= v <= 9 for v in dims),
                "Invalid cuboid")
        require(p["edge"] in (0, 1, 2), "Invalid edge")
        if form == "area_to_volume":
            require(p["edge"] == 0, "No edge is labelled in this form")
    value, unit = answer_for(p)
    require(value.denominator == 1 and value > 0, "Answer must be a positive whole number")
    return int(value), unit


# ------------------------------------------------------------ drawing helpers

def line(first, second, dashed=False):
    node = {"type": "line", "points": [figures.rounded(first), figures.rounded(second)]}
    if dashed:
        node["dashed"] = True
    return node


def label(point, text):
    return {"type": "label", "point": figures.rounded(point), "text": text}


def outward(point, centre, gap=LETTER_GAP):
    direction = figures.unit(figures.minus(point, centre))
    return (point[0] + direction[0] * gap, point[1] + direction[1] * gap)


def centroid(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def place_pair(first, second, orient_first, orient_second, max_height=PAIR_HEIGHT):
    """Orient two figures separately and place them side by side at ONE scale."""
    moved = [{k: figures.transform(v, o) for k, v in pts.items()}
             for pts, o in ((first, orient_first), (second, orient_second))]
    boxes = []
    for pts in moved:
        xs = [v[0] for v in pts.values()]
        ys = [v[1] for v in pts.values()]
        boxes.append((min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)))
    total = boxes[0][2] + boxes[1][2]
    tallest = max(boxes[0][3], boxes[1][3])
    scale = min((figures.MAX_FIGURE_WIDTH - PAIR_GAP) / total, max_height / tallest)
    left = (figures.CANVAS_WIDTH - (total * scale + PAIR_GAP)) / 2
    placed = []
    for pts, (mx, my, w, h) in zip(moved, boxes):
        top = figures.MARGIN + (tallest - h) * scale / 2
        placed.append({k: (left + (v[0] - mx) * scale, top + (v[1] - my) * scale)
                       for k, v in pts.items()})
        left += w * scale + PAIR_GAP
    return placed, round(tallest * scale + 2 * figures.MARGIN, figures.DIGITS)


def scene(nodes, height):
    return {"kind": "scene", "version": 1, "width": 360, "height": height,
            "caption": "Not drawn accurately", "nodes": nodes}


def triangle_nodes(pts, names, side_texts):
    nodes = [line(pts[i], pts[(i + 1) % 3]) for i in range(3)]
    middle = centroid([pts[i] for i in range(3)])
    for i in range(3):
        nodes.append(label(outward(pts[i], middle), names[i]))
    for side, text in side_texts.items():
        first, second = SIDE_ENDS[side]
        nodes.append({"type": "label", "text": text, "point": figures.side_label(
            pts[first], pts[second], pts[side], len(text))})
    return nodes


def cm(value):
    return "{} cm".format(value)


# ------------------------------------------------------------ figures per family

def pair_texts(p):
    sides, k = p["sides"], ratio(p)
    image = [int(v * k) for v in sides]
    known, target = p["known"], p["target"]
    if p["form"] == "enlarge":
        return ({known: cm(sides[known]), target: cm(sides[target])},
                {known: cm(image[known]), target: "x"})
    return ({known: cm(sides[known]), target: "x"},
            {known: cm(image[known]), target: cm(image[target])})


def triangle_from_sides(sides):
    a, b, c = (float(v) for v in sides)
    x = (b * b + c * c - a * a) / (2 * c)
    return {0: (0.0, 0.0), 1: (c, 0.0), 2: (x, -math.sqrt(max(0.0, b * b - x * x)))}


def pair_scene(p, orientations):
    k = float(ratio(p))
    names = p["names"]
    if FAMILY[p["form"]] == "pair":
        shape = triangle_from_sides(p["sides"])
        s_texts, t_texts = pair_texts(p)
    else:
        c, h, o = p["base"], p["height"], p["offset"]
        shape = {0: (0.0, 0.0), 1: (float(c), 0.0), 2: (float(o), -float(h))}
        image = int(c * ratio(p))
        s_texts = {2: cm(c)}
        t_texts = {2: "x" if p["form"] == "area_reverse" else cm(image)}
    image_shape = {i: (v[0] * k, v[1] * k) for i, v in shape.items()}
    (first, second), height = place_pair(shape, image_shape, *orientations)
    nodes = triangle_nodes(first, names[:3], s_texts) + triangle_nodes(second, names[3:], t_texts)
    return scene(nodes, height)


def nested_points(p):
    ab = p["ad"] + p["db"]
    turn = math.radians(p["beta"])
    a = (ab * math.cos(turn), -ab * math.sin(turn))
    b, c = (0.0, 0.0), (float(p["bc"]), 0.0)
    d = (a[0] * p["db"] / ab, a[1] * p["db"] / ab)
    e = (a[0] + (c[0] - a[0]) * p["ad"] / ab, a[1] + (c[1] - a[1]) * p["ad"] / ab)
    return {"A": a, "B": b, "C": c, "D": d, "E": e}


def nested_scene(p, orientation):
    placed, height = figures.place(nested_points(p), orientation)
    names = dict(zip("ABCDE", p["names"]))
    a, b, c, d, e = (placed[k] for k in "ABCDE")
    nodes = [line(a, b), line(b, c), line(c, a), line(d, e),
             {"type": "parallel", "points": [figures.rounded(d), figures.rounded(e)],
              "position": 0.6},
             {"type": "parallel", "points": [figures.rounded(b), figures.rounded(c)],
              "position": 0.6}]
    middle = centroid([a, b, c])
    for key in "ABC":
        nodes.append(label(outward(placed[key], middle), names[key]))
    for key in "DE":
        nodes.append(label(outward(placed[key], middle, gap=16), names[key]))
    unknown = "bc" if p["form"] == "nested" else "db"
    texts = {key: ("x" if key == unknown else cm(p[key])) for key in ("ad", "db", "de", "bc")}
    base_middle = ((b[0] + c[0]) / 2, (b[1] + c[1]) / 2)
    for key, (first, second, inside) in {
        "ad": (a, d, c), "db": (d, b, c), "bc": (b, c, a), "de": (d, e, base_middle),
    }.items():
        nodes.append({"type": "label", "text": texts[key], "point": figures.side_label(
            first, second, inside, len(texts[key]))})
    return scene(nodes, height)


def cuboid_points(dims, scale_by=1.0):
    l, w, h = (v * scale_by for v in dims)
    ox, oy = 0.5 * w * math.cos(math.radians(30)), 0.5 * w * math.sin(math.radians(30))
    front = {"F0": (0.0, 0.0), "F1": (l, 0.0), "F2": (l, h), "F3": (0.0, h)}
    back = {"B" + key[1]: (x + ox, y - oy) for key, (x, y) in front.items()}
    return dict(front, **back)


VISIBLE_EDGES = (("F0", "F1"), ("F1", "F2"), ("F2", "F3"), ("F3", "F0"),
                 ("F0", "B0"), ("F1", "B1"), ("F2", "B2"), ("B0", "B1"), ("B1", "B2"))
HIDDEN_EDGES = (("B2", "B3"), ("B3", "B0"), ("F3", "B3"))
EDGE_ENDS = {0: ("F3", "F2"), 1: ("F2", "B2"), 2: ("F0", "F3")}


def solid_scene(p):
    k = float(ratio(p))
    (first, second), height = place_pair(cuboid_points(p["dims"]),
                                         cuboid_points(p["dims"], k), [0, False], [0, False])
    nodes = []
    image_edge = "x"
    for pts, name, edge_text in ((first, p["names"][0], cm(p["dims"][p["edge"]])),
                                 (second, p["names"][1], image_edge)):
        nodes += [line(pts[a], pts[b]) for a, b in VISIBLE_EDGES]
        nodes += [line(pts[a], pts[b], dashed=True) for a, b in HIDDEN_EDGES]
        top = ((pts["B0"][0] + pts["B1"][0]) / 2, pts["B0"][1] - 16)
        nodes.append(label(top, name))
        if p["form"] == "volume":
            face = centroid([pts[key] for key in ("F0", "F1", "F2", "F3")])
            a, b = EDGE_ENDS[p["edge"]]
            nodes.append({"type": "label", "text": edge_text, "point": figures.side_label(
                pts[a], pts[b], face, len(edge_text))})
    return scene(nodes, height + 20)


def diagram_for(p):
    family = FAMILY[p["form"]]
    if family in ("pair", "area"):
        return pair_scene(p, p["orientations"])
    if family == "nested":
        return nested_scene(p, p["orientation"])
    return solid_scene(p)


# ------------------------------------------------------------ presentation

def side_name(names, side):
    first, second = SIDE_ENDS[side]
    return names[first] + names[second]


def presentation(p):
    form, names = p["form"], p["names"]
    family = FAMILY[form]
    if family == "pair":
        lead = "Triangle {} is similar to triangle {}. Find x.".format(names[:3], names[3:])
        s_texts, t_texts = pair_texts(p)
        facts = ["{} = {}".format(side_name(names[:3], s), t) for s, t in sorted(s_texts.items())]
        facts += ["{} = {}".format(side_name(names[3:], s), t) for s, t in sorted(t_texts.items())]
        fallback = " Marked: " + "; ".join(facts) + "."
    elif family == "area":
        area = p["base"] * p["height"] // 2
        if form == "area":
            lead = ("Triangles {0} and {1} are similar. The area of triangle {0} is {2} "
                    "square centimetres. Calculate the area of triangle {1}.").format(
                names[:3], names[3:], area)
            fallback = " Marked: {} = {} cm; {} = {} cm.".format(
                side_name(names[:3], 2), p["base"], side_name(names[3:], 2),
                int(p["base"] * ratio(p)))
        else:
            image_area = int(Fraction(p["base"] * p["height"], 2) * ratio(p) ** 2)
            lead = ("Triangles {} and {} are similar. Their areas are {} and {} square "
                    "centimetres. Find x.").format(names[:3], names[3:], area, image_area)
            fallback = " Marked: {} = {} cm; {} = x.".format(
                side_name(names[:3], 2), p["base"], side_name(names[3:], 2))
    elif family == "nested":
        n = dict(zip("ABCDE", names))
        lead = ("{D} lies on {A}{B} and {E} lies on {A}{C}. {D}{E} is parallel to "
                "{B}{C}. Find x.").format(**n)
        unknown = "bc" if form == "nested" else "db"
        pairs = {"ad": n["A"] + n["D"], "db": n["D"] + n["B"],
                 "de": n["D"] + n["E"], "bc": n["B"] + n["C"]}
        fallback = " Marked: " + "; ".join(
            "{} = {}".format(pairs[key], "x" if key == unknown else cm(p[key]))
            for key in ("ad", "db", "de", "bc")) + "."
    else:
        volume, image_volume, surface, image_surface = solid_facts(p)
        first, second = p["names"]
        if form == "volume":
            lead = ("Cuboids {} and {} are mathematically similar. Their volumes are {} "
                    "and {} cubic centimetres. Find x.").format(
                first, second, volume, int(image_volume))
            fallback = " The marked edge of {} is {} cm; the corresponding edge of {} is x.".format(
                first, p["dims"][p["edge"]], second)
        else:
            lead = ("Cuboids {0} and {1} are mathematically similar. Their surface areas "
                    "are {2} and {3} square centimetres. The volume of {0} is {4} cubic "
                    "centimetres. Calculate the volume of {1}.").format(
                first, second, surface, int(image_surface), volume)
            fallback = ""
    return Content(lead + fallback, display_text=lead)


def answer_display(value, unit):
    if unit == "cm^2":
        return Content("{} square centimetres".format(value), str(value) + r"\ \mathrm{cm}^{2}")
    if unit == "cm^3":
        return Content("{} cubic centimetres".format(value), str(value) + r"\ \mathrm{cm}^{3}")
    return Content("x = {} cm".format(value))


# ------------------------------------------------------------ drawing the parameters

def draw(rng, level):
    form = rng.choice(FORMS[level])
    family = FAMILY[form]
    p = {"form": form, "names": rng.choice(NAME_SETS[family])}
    if family == "pair":
        n, d = rng.choice(PAIR_SCALES)
        p["scale"] = [n, d]
        p["sides"] = [d * rng.randint(2, 16 // d) for _ in range(3)]
        p["known"], p["target"] = rng.sample(range(3), 2)
        p["orientations"] = [[0, False], [0, False]]
    elif family == "nested":
        ad, db = rng.randint(3, 10), rng.randint(2, 10)
        g = math.gcd(ad, ad + db)
        unit_de, unit_bc = ad // g, (ad + db) // g
        choices = [m for m in range(1, 16) if 3 <= m * unit_de <= 15 and m * unit_bc <= 30]
        m = rng.choice(choices) if choices else 1
        p.update(ad=ad, db=db, de=m * unit_de, bc=m * unit_bc,
                 beta=rng.randint(45, 80), orientation=[0, False])
    elif family == "area":
        n, d = rng.choice(SCALES)
        c = d * rng.randint(max(2, 4 // d), 12 // d)
        p.update(scale=[n, d], base=c, height=rng.randint(3, 10),
                 offset=rng.randint(-3, c + 3), orientations=[[0, False], [0, False]])
    else:
        n, d = rng.choice(SCALES)
        p.update(scale=[n, d], dims=[d * rng.randint(max(1, 2 // d + (2 % d > 0)), 9 // d)
                                      for _ in range(3)],
                 edge=rng.randrange(3) if form == "volume" else 0)
    return p


def choose_pair(rng, make_spec):
    """Seeded independent orientations for two figures, kept only if labels are clear."""
    firsts, seconds = list(figures.ORIENTATIONS), list(figures.ORIENTATIONS)
    rng.shuffle(firsts)
    rng.shuffle(seconds)
    for first, second in zip(firsts, seconds):
        pair = [list(first), list(second)]
        spec = make_spec(pair)
        if circle_figures.labels_clear(spec) and circle_figures.renders_everywhere(spec):
            return pair
    raise ValueError("No orientation pair keeps every label clear")


def solid_is_clear(p):
    spec = solid_scene(p)
    return circle_figures.labels_clear(spec) and circle_figures.renders_everywhere(spec)


# ------------------------------------------------------------ generator

class SimilarShapes:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        for attempt in range(400):
            p = draw(rng, difficulty)
            try:
                value, unit = check_parameters(p, difficulty)
                family = FAMILY[p["form"]]
                if family in ("pair", "area"):
                    p["orientations"] = choose_pair(
                        rng, lambda pair: pair_scene(p, pair))
                elif family == "nested":
                    p["orientation"] = circle_figures.choose_orientation(
                        rng, lambda o: nested_scene(p, o))
                else:
                    require(solid_is_clear(p), "Cuboid labels are not clear")
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a similarity question")
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=presentation(p),
            answer={"kind": "integer", "value": value, "unit": unit},
            answer_display=answer_display(value, unit), worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=4 if difficulty <= 2 else 5),
            parameters=p, question_visuals=(diagram_for(p),),
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid level")
        require(q.settings == {}, "Unsupported settings")
        p = q.parameters
        value, unit = check_parameters(p, level)
        require(q.answer == {"kind": "integer", "value": value, "unit": unit},
                "Incorrect answer")
        require(q.prompt == presentation(p), "Prompt mismatch")
        require(q.answer_display == answer_display(value, unit), "Display mismatch")
        require(q.visual_assets("questions") == (diagram_for(p),), "Diagram mismatch")
        require(not q.visual_assets("answers"), "Unexpected answer visuals")
        return True

    def validate_independently(self, q):
        """Cross-multiplied invariants of the displayed numbers; no scale factor."""
        p, x = q.parameters, q.answer.get("value")
        require(type(x) is int and x > 0, "Invalid answer")
        form = p["form"]
        if form in ("enlarge", "reduce"):
            s_texts, t_texts = pair_texts(p)
            number = lambda text: int(text.split()[0])
            known, target = p["known"], p["target"]
            if form == "enlarge":
                valid = x * number(s_texts[known]) == number(t_texts[known]) * number(s_texts[target])
            else:
                valid = x * number(t_texts[known]) == number(s_texts[known]) * number(t_texts[target])
        elif form == "nested":
            valid = p["ad"] * (x - p["de"]) == p["db"] * p["de"]
        elif form == "nested_part":
            valid = p["ad"] * (p["bc"] - p["de"]) == x * p["de"]
        elif form == "area":
            image_base = p["base"] * ratio(p)
            valid = x * p["base"] ** 2 == Fraction(p["base"] * p["height"], 2) * image_base ** 2
        elif form == "area_reverse":
            area = Fraction(p["base"] * p["height"], 2)
            image_area = area * ratio(p) ** 2
            valid = x * x * area == p["base"] ** 2 * image_area
        elif form == "volume":
            volume, image_volume, _, _ = solid_facts(p)
            valid = x ** 3 * volume == p["dims"][p["edge"]] ** 3 * image_volume
        else:
            volume, _, surface, image_surface = solid_facts(p)
            valid = x * x * surface ** 3 == volume ** 2 * image_surface ** 3
        require(valid, "Independent similarity check disagrees")
        return True