"""IB AI SL Voronoi diagrams.

Level 1 the perpendicular bisector of two sites and the nearer site to a
point; level 2 a Voronoi vertex from two bisectors; level 3 nearest-
neighbour interpolation; level 4 the toxic-waste-dump problem (the vertex
of an acute triangle of towns) and adding a town.

Sites have integer coordinates in a 0 to 14 km map. Each cell is the map
rectangle clipped by bisector half-planes in exact Fractions, so the
diagram shows the true Voronoi diagram. The independent check uses
brute-force distances and numpy.linalg.solve.
"""
from fractions import Fraction

from ..core import GeneratorInfo, require
from ..family import GeneratorFamily
from .. import figures
from . import common as ib
from . import diagrams
from . import trig


# --- Editable pools ---------------------------------------------------------
BOX = 14
COORDINATES = tuple(range(1, BOX))
LETTERS = ("A", "B", "C", "D", "E")
MIN_SEPARATION_SQUARED = 9
CONTEXTS = {
    "restaurants": {"intro": "The diagram shows the locations of {} restaurants in a city, with "
                             "coordinates in km.", "site": "restaurant", "quantity": "waiting time",
                    "unit": "minutes", "values": tuple(range(5, 41))},
    "weather": {"intro": "The diagram shows {} weather stations in a region, with coordinates "
                         "in km.", "site": "weather station", "quantity": "rainfall",
                "unit": "mm", "values": tuple(range(20, 121))},
    "noise": {"intro": "The diagram shows {} noise sensors in a town, with coordinates in km.",
              "site": "sensor", "quantity": "noise level", "unit": "dB",
              "values": tuple(range(45, 91))},
}


# ------------------------------------------------------------ mathematics

def as_point(value):
    return Fraction(value[0]), Fraction(value[1])


def squared(p, q):
    return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2


def bisector(p, q):
    """(a, b, c) with a x + b y = c, the perpendicular bisector of pq."""
    a, b = q[0] - p[0], q[1] - p[1]
    return a, b, (q[0] ** 2 + q[1] ** 2 - p[0] ** 2 - p[1] ** 2) / 2


def meet(first, second):
    (a1, b1, c1), (a2, b2, c2) = first, second
    determinant = a1 * b2 - a2 * b1
    require(determinant != 0, "Bisectors are parallel")
    return (c1 * b2 - c2 * b1) / determinant, (a1 * c2 - a2 * c1) / determinant


def line_text(line):
    """y = mx + c, x = k or y = k, exactly."""
    a, b, c = line
    if b == 0:
        return "x = " + ib.exact_or_fraction(c / a)
    if a == 0:
        return "y = " + ib.exact_or_fraction(c / b)
    gradient, intercept = -a / b, c / b
    slope = {1: "", -1: "-"}.get(gradient, ib.exact_or_fraction(gradient))
    text = "y = {}x".format(slope)
    if intercept:
        text += " {} {}".format("-" if intercept < 0 else "+", ib.exact_or_fraction(abs(intercept)))
    return text


def point_text(point):
    return "({}, {})".format(ib.nice(point[0]), ib.nice(point[1]))


def nearest(sites, point):
    """(index of the nearest site, sorted squared distances)."""
    distances = sorted((squared(site, point), i) for i, site in enumerate(sites))
    return distances[0][1], [d for d, _ in distances]


def clip(polygon, normal, bound):
    """Keep the part of a convex polygon with normal . p <= bound."""
    def inside(p):
        return normal[0] * p[0] + normal[1] * p[1] <= bound

    def crossing(p, q):
        t = (bound - normal[0] * p[0] - normal[1] * p[1]) / (
            normal[0] * (q[0] - p[0]) + normal[1] * (q[1] - p[1]))
        return p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])

    result = []
    for index, current in enumerate(polygon):
        previous = polygon[index - 1]
        if inside(current):
            if not inside(previous):
                result.append(crossing(previous, current))
            result.append(current)
        elif inside(previous):
            result.append(crossing(previous, current))
    cleaned = []
    for point in result:
        if not cleaned or point != cleaned[-1]:
            cleaned.append(point)
    if len(cleaned) > 1 and cleaned[0] == cleaned[-1]:
        cleaned.pop()
    return cleaned


def cells(sites):
    """The Voronoi cell of every site, clipped to the map."""
    box = [(Fraction(0), Fraction(0)), (Fraction(BOX), Fraction(0)),
           (Fraction(BOX), Fraction(BOX)), (Fraction(0), Fraction(BOX))]
    result = []
    for i, site in enumerate(sites):
        polygon = list(box)
        for j, other in enumerate(sites):
            if i != j:
                a, b, c = bisector(site, other)
                polygon = clip(polygon, (a, b), c)
        result.append(polygon)
    return result


def adjacent(sites, i, j):
    """Whether cells i and j share an edge of positive length."""
    polygon = cells(sites)[i]
    for index, p in enumerate(polygon):
        q = polygon[index - 1]
        if p != q and all(squared(v, sites[i]) == squared(v, sites[j]) for v in (p, q)):
            return True
    return False


def scene(sites, letters, point=None, show_cells=True):
    roles, polygons = {}, []
    if show_cells:
        for i, polygon in enumerate(cells(sites)):
            names = []
            for k, vertex in enumerate(polygon):
                name = "v{}_{}".format(i, k)
                roles[name] = (float(vertex[0]), float(vertex[1]))
                names.append(name)
            polygons.append(names)
    else:
        corners = ((0, 0), (BOX, 0), (BOX, BOX), (0, BOX))
        names = []
        for k, corner in enumerate(corners):
            roles["frame{}".format(k)] = corner
            names.append("frame{}".format(k))
        polygons.append(names)
    for i, site in enumerate(sites):
        roles["S{}".format(i)] = (float(site[0]), float(site[1]))
    if point is not None:
        roles["X"] = (float(point[0]), float(point[1]))
    placed, height = figures.place(roles, [0, False])
    nodes = [{"type": "polygon", "points": [placed[name] for name in polygon]} for polygon in polygons]
    for i, letter in enumerate(letters):
        x, y = placed["S{}".format(i)]
        nodes.append({"type": "circle", "center": [x, y], "radius": 2.2, "shade": True})
        nodes.append({"type": "label", "text": letter, "point": figures.rounded((x + 9, y + 9))})
    if point is not None:
        x, y = placed["X"]
        nodes.append({"type": "circle", "center": [x, y], "radius": 2.4})
        nodes.append({"type": "label", "text": "P", "point": figures.rounded((x - 9, y + 9))})
    return diagrams.scene(nodes, height)


# ------------------------------------------------------------ generator

class VoronoiDiagrams(GeneratorFamily):
    info = GeneratorInfo(
        id="ib_ai_sl.geometry.voronoi",
        version=1,
        topic=ib.TOPIC,
        subtopic="geometry_and_trigonometry",
        title="Voronoi diagrams",
        difficulty_descriptions={
            1: "Perpendicular bisector of two sites, and the nearer site to a point.",
            2: "Find a bisector, then a Voronoi vertex from two bisectors.",
            3: "Nearest-neighbour interpolation, a cell edge and a distance.",
            4: "Toxic-waste-dump problem: the vertex of three towns, then a new town.",
        },
        tags=ib.BASE_TAGS + ("voronoi", "perpendicular_bisector", "nearest_neighbour"),
    )
    keys = {
        1: {"sites", "point"},
        2: {"sites"},
        3: {"context", "sites", "values", "point", "pair"},
        4: {"sites", "extra"},
    }

    def build(self, level, rng):
        def check(p):
            self.check_rules(p, level)
            diagrams.require_drawable(self.parts(p, level))
        return ib.pick_valid(rng, lambda r: self.candidate(level, r), check)

    def candidate(self, level, rng):
        count = {1: 2, 2: 3, 3: rng.choice((4, 5)), 4: 3}[level]
        sites = [[rng.choice(COORDINATES), rng.choice(COORDINATES)] for _ in range(count)]
        p = {"sites": sites}
        if level in (1, 3):
            p["point"] = [rng.choice(COORDINATES), rng.choice(COORDINATES)]
        if level == 3:
            context = rng.choice(tuple(CONTEXTS))
            p.update(context=context,
                     values=[rng.choice(CONTEXTS[context]["values"]) for _ in range(count)],
                     pair=sorted(rng.sample(range(count), 2)))
        if level == 4:
            p["extra"] = [rng.choice(COORDINATES), rng.choice(COORDINATES)]
        return p

    def check_rules(self, p, level):
        raw = p["sites"]
        count = {1: (2,), 2: (3,), 3: (4, 5), 4: (3,)}[level]
        require(isinstance(raw, list) and len(raw) in count and all(
            isinstance(s, list) and len(s) == 2 and s[0] in COORDINATES and s[1] in COORDINATES
            for s in raw), "Sites outside rules")
        sites = [as_point(s) for s in raw]
        for i in range(len(sites)):
            for j in range(i + 1, len(sites)):
                require(squared(sites[i], sites[j]) >= MIN_SEPARATION_SQUARED, "Sites too close")
        if level in (1, 2, 4):
            a, b = sites[0], sites[1]
            require(a[0] != b[0] and a[1] != b[1], "The bisector asked for must have a gradient")
        if level in (2, 4):
            c = sites[2]
            require((b[0] - a[0]) * (c[1] - a[1]) != (b[1] - a[1]) * (c[0] - a[0]), "Sites are collinear")
            require(b[0] != c[0] and b[1] != c[1], "The given bisector must have a gradient")
            # A printed equation should look like an exam's: no awkward fractions.
            require("/" not in line_text(bisector(b, c)), "Given bisector needs short decimals")
            vertex = meet(bisector(a, b), bisector(b, c))
            require(0 < vertex[0] < BOX and 0 < vertex[1] < BOX, "Vertex outside the map")
        if level in (1, 3):
            point = p["point"]
            require(isinstance(point, list) and len(point) == 2 and point[0] in COORDINATES
                    and point[1] in COORDINATES, "Point outside rules")
            point = as_point(point)
            _, distances = nearest(sites, point)
            require(distances[0] > 0 and distances[1] - distances[0] >= 2, "Point too near a cell edge")
        if level == 3:
            require(p["context"] in CONTEXTS, "Unknown context")
            values = p["values"]
            require(isinstance(values, list) and len(values) == len(sites)
                    and all(v in CONTEXTS[p["context"]]["values"] for v in values), "Values outside pool")
            pair = p["pair"]
            require(isinstance(pair, list) and len(pair) == 2 and all(type(i) is int for i in pair)
                    and 0 <= pair[0] < pair[1] < len(sites), "Pair outside rules")
            require(adjacent(sites, pair[0], pair[1]), "The pair must share a cell edge")
        if level == 4:
            a, b, c = sites
            for first, second, third in ((a, b, c), (b, c, a), (c, a, b)):
                require(squared(first, second) < squared(first, third) + squared(second, third),
                        "Towns must form an acute triangle")
            extra = p["extra"]
            require(isinstance(extra, list) and len(extra) == 2 and extra[0] in COORDINATES
                    and extra[1] in COORDINATES, "New town outside rules")
            _, distances = nearest(sites, as_point(extra))
            require(distances[0] > 0 and distances[1] - distances[0] >= 2, "New town too near a cell edge")

    def parts(self, p, level):
        sites = [as_point(s) for s in p["sites"]]
        letters = LETTERS[:len(sites)]
        listing = ", ".join("{}{}".format(letter, point_text(site)) for letter, site in zip(letters, sites))
        if level == 1:
            a, b = sites
            point = as_point(p["point"])
            middle = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            gradient = (b[1] - a[1]) / (b[0] - a[0])
            line = bisector(a, b)
            index, _ = nearest(sites, point)
            far = 1 - index
            reason = "{}, since P{} = {} km and P{} = {} km".format(
                letters[index], letters[index], ib.sf3(trig.sqrt(squared(point, sites[index]))),
                letters[far], ib.sf3(trig.sqrt(squared(point, sites[far]))))
            context = ["Two mobile phone masts are at {}, with coordinates in km. A phone at "
                       "P{} connects to the nearer mast.".format(listing, point_text(point))]
            built = ib.assemble(context, [
                ib.part("a", "Find the midpoint of AB.", 1, point_text(middle), middle[0]),
                ib.part("b", "Find the gradient of AB.", 1, ib.exact_or_fraction(gradient), gradient),
                ib.part("c", "Find the equation of the perpendicular bisector of AB, in the form "
                        "y = mx + c.", 2, line_text(line)),
                ib.part("d", "Determine which mast the phone at P connects to. Justify your answer.", 2, reason),
            ])
            built["question_visuals"] = (scene(sites, letters, point, show_cells=False),)
            return built
        if level == 2:
            a, b, c = sites
            middle = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            gradient = (b[1] - a[1]) / (b[0] - a[0])
            vertex = meet(bisector(a, b), bisector(b, c))
            context = ["Three schools are at {}, with coordinates in km. The diagram shows the "
                       "Voronoi diagram for the schools.".format(listing),
                       "The perpendicular bisector of BC has equation {}.".format(line_text(bisector(b, c)))]
            built = ib.assemble(context, [
                ib.part("a", "Find the midpoint of AB.", 1, point_text(middle), middle[0]),
                ib.part("b", "Find the gradient of AB.", 1, ib.exact_or_fraction(gradient), gradient),
                ib.part("c", "Find the equation of the perpendicular bisector of AB.", 2,
                        line_text(bisector(a, b))),
                ib.part("d", "Find the coordinates of the vertex where the cells of A, B and C meet.", 2,
                        point_text(vertex), vertex[0]),
            ])
            built["question_visuals"] = (scene(sites, letters),)
            return built
        if level == 3:
            c = CONTEXTS[p["context"]]
            point = as_point(p["point"])
            index, distances = nearest(sites, point)
            first, second = p["pair"]
            distance = trig.sqrt(distances[0])
            values = ", ".join("{} {} {}".format(letter, value, c["unit"])
                               for letter, value in zip(letters, p["values"]))
            context = [c["intro"].format(len(sites)) + " The sites are " + listing + ".",
                       "The {} recorded at each {} is: {}.".format(c["quantity"], c["site"], values),
                       "The point P{} is also shown.".format(point_text(point))]
            built = ib.assemble(context, [
                ib.part("a", "Use nearest-neighbour interpolation to estimate the {} at P.".format(
                    c["quantity"]), 2, "{} {} (P is in the cell of {})".format(
                        p["values"][index], c["unit"], letters[index]), p["values"][index]),
                ib.part("b", "Find the equation of the edge of the Voronoi diagram between the cells of "
                        "{} and {}.".format(letters[first], letters[second]), 3,
                        line_text(bisector(sites[first], sites[second]))),
                ib.part("c", "Find the distance from P to the nearest {}.".format(c["site"]), 2,
                        "{} km".format(ib.sf3(distance)), distance),
            ])
            built["question_visuals"] = (scene(sites, letters, point),)
            return built
        a, b, c = sites
        vertex = meet(bisector(a, b), bisector(b, c))
        distance = trig.sqrt(squared(vertex, a))
        extra = as_point(p["extra"])
        index, _ = nearest(sites, extra)
        context = ["Three towns are at {}, with coordinates in km. The diagram shows their Voronoi "
                   "diagram.".format(listing),
                   "The perpendicular bisector of BC has equation {}.".format(line_text(bisector(b, c))),
                   "A recycling plant is to be built inside triangle ABC, as far as possible from the "
                   "nearest town."]
        built = ib.assemble(context, [
            ib.part("a", "Find the equation of the perpendicular bisector of AB.", 3, line_text(bisector(a, b))),
            ib.part("b", "Find the coordinates of the point that is equidistant from all three towns.", 3,
                    point_text(vertex), vertex[0]),
            ib.part("c", "Find the distance from this point to each town.", 2,
                    "{} km".format(ib.sf3(distance)), distance),
            ib.part("d", "Explain why the recycling plant should be built at this point.", 1,
                    "It is the vertex of the Voronoi diagram inside the triangle, so it is the point "
                    "farthest from its nearest town."),
            ib.part("e", "A new town D is built at {}. State which town's cell D was in before "
                    "the diagram changed.".format(point_text(extra)), 1, letters[index]),
        ])
        built["question_visuals"] = (scene(sites, letters),)
        return built

    def validate_independently(self, question):
        """Brute-force nearest sites; numpy solves for the vertex."""
        import math
        import numpy
        p, level = question.parameters, question.difficulty
        values, shown = ib.answer_values(question), ib.answer_shown(question)
        sites = [tuple(float(v) for v in s) for s in p["sites"]]

        def on_bisector(text, first, second):
            # Two points on the stated line must be equidistant from both sites.
            if text.startswith("x = "):
                x = float(Fraction(text[4:]))
                probes = [(x, 0.0), (x, 10.0)]
            else:
                right = text[4:].replace(" ", "")
                if "x" not in right:
                    probes = [(0.0, float(Fraction(right))), (10.0, float(Fraction(right)))]
                else:
                    slope_text, _, rest = right.partition("x")
                    slope = {"": 1.0, "-": -1.0}.get(slope_text)
                    slope = float(Fraction(slope_text)) if slope is None else slope
                    intercept = float(Fraction(rest)) if rest else 0.0
                    probes = [(x, slope * x + intercept) for x in (0.0, 10.0)]
            return all(abs(math.dist(q, first) - math.dist(q, second)) < 1e-9 for q in probes)

        def vertex_of(a, b, c):
            matrix = numpy.array([[b[0] - a[0], b[1] - a[1]], [c[0] - b[0], c[1] - b[1]]])
            rhs = numpy.array([(b[0] ** 2 + b[1] ** 2 - a[0] ** 2 - a[1] ** 2) / 2,
                               (c[0] ** 2 + c[1] ** 2 - b[0] ** 2 - b[1] ** 2) / 2])
            return numpy.linalg.solve(matrix, rhs)

        if level == 1:
            point = tuple(float(v) for v in p["point"])
            closer = min(range(2), key=lambda i: math.dist(point, sites[i]))
            require(shown["d"].startswith(LETTERS[closer]), "Independent nearest site failed")
            require(on_bisector(shown["c"], sites[0], sites[1]), "Independent bisector failed")
        elif level == 2:
            require(on_bisector(shown["c"], sites[0], sites[1]), "Independent bisector failed")
            require(ib.close(values["d"], float(vertex_of(*sites)[0])), "Independent vertex failed")
        elif level == 3:
            point = tuple(float(v) for v in p["point"])
            closest = min(range(len(sites)), key=lambda i: math.dist(point, sites[i]))
            require(Fraction(values["a"]) == p["values"][closest], "Independent interpolation failed")
            first, second = p["pair"]
            require(on_bisector(shown["b"], sites[first], sites[second]), "Independent edge failed")
            require(ib.close(values["c"], math.dist(point, sites[closest])), "Independent distance failed")
        else:
            vertex = vertex_of(*sites)
            require(on_bisector(shown["a"], sites[0], sites[1]), "Independent bisector failed")
            require(ib.close(values["b"], float(vertex[0])), "Independent vertex failed")
            require(ib.close(values["c"], math.dist(tuple(vertex), sites[0])), "Independent distance failed")
            extra = tuple(float(v) for v in p["extra"])
            closest = min(range(3), key=lambda i: math.dist(extra, sites[i]))
            require(shown["e"] == LETTERS[closest], "Independent cell failed")
        return True