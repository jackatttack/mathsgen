"""Bar charts and pie charts, drawn as scene nodes.

Bar charts use even frequencies, ticks every 2 and axis numbers every 4. Pie
totals divide 360, so every sector angle is a whole number, and every sector
is at least MIN_SECTOR degrees so its label fits. Sectors are drawn clockwise
from the top, like bearings. The independent check reads answers back from the
drawing: bar heights from polygon tops against the axis scale, sector angles
from the directions of the radii.
"""
import math
from fractions import Fraction

from . import figures
from .core import Content, GeneratorInfo, LayoutHint, Question, make_context, require
from .vector_geometry import renders_cleanly


INFO = GeneratorInfo(
    id="data.charts.bar_pie", version=1,
    topic="data", subtopic="bar_pie_charts",
    title="Bar charts and pie charts",
    difficulty_descriptions={
        1: "Read a bar chart: a difference between bars, or the mode.",
        2: "Read a pie chart with its total, or work out one sector angle.",
        3: "Work out all the angles for a pie chart, or a missing sector.",
        4: "Use one sector to find another frequency, or compare two pie charts.",
    },
    tags=("statistics", "bar charts", "pie charts"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("bar_difference", "bar_mode"),
    2: ("sector_frequency", "angle_from_frequency"),
    3: ("pie_angles", "missing_angle"),
    4: ("total_from_sector", "compare_pies"),
}
THEMES = {
    "pets": ("favourite pet", ("Cat", "Dog", "Fish", "Rabbit", "Bird")),
    "sports": ("favourite sport", ("Football", "Tennis", "Swim", "Netball", "Rugby")),
    "fruit": ("favourite fruit", ("Apple", "Banana", "Grape", "Pear", "Orange")),
}
TOTALS = (20, 24, 30, 36, 40, 45, 60, 72, 90, 120)
MIN_SECTOR = 45
GROUPS = ("Year 10", "Year 11")
MARKS = {1: 1, 2: 2, 3: 3, 4: 3}
WORKING_LINES = {1: 2, 2: 3, 3: 5, 4: 5}

# Bar chart layout, in scene units with y upwards.
LEFT, BASE, PLOT_WIDTH, PLOT_HEIGHT = 56, 40, 280, 150

BAR_FORMS = ("bar_difference", "bar_mode")
KEYS = {
    "bar_difference": {"theme", "counts", "pair"},
    "bar_mode": {"theme", "counts"},
    "sector_frequency": {"theme", "counts", "ask"},
    "angle_from_frequency": {"theme", "counts", "ask"},
    "pie_angles": {"theme", "counts"},
    "missing_angle": {"theme", "counts", "ask"},
    "total_from_sector": {"theme", "counts", "pair"},
    "compare_pies": {"theme", "counts", "counts_b", "ask"},
}


# ------------------------------------------------------------ helpers

def names(par):
    return THEMES[par["theme"]][1][:len(par["counts"])]


def angles(counts):
    total = sum(counts)
    return [Fraction(360 * c, total) for c in counts]


def bar_top(counts):
    return 4 * math.ceil(max(counts) / 4)


def label(point, text):
    return {"type": "label", "point": figures.rounded(point), "text": text}


def line(first, second):
    return {"type": "line", "points": [figures.rounded(first), figures.rounded(second)]}


def scene(nodes, height):
    return {"kind": "scene", "version": 1, "width": 360, "height": height,
            "caption": "", "nodes": nodes}


# ------------------------------------------------------------ drawings

def bar_scene(par):
    counts, top = par["counts"], bar_top(par["counts"])
    scale = PLOT_HEIGHT / top
    nodes = [line((LEFT, BASE), (LEFT, BASE + PLOT_HEIGHT)),
             line((LEFT, BASE), (LEFT + PLOT_WIDTH, BASE))]
    for value in range(0, top + 1, 2):
        y = BASE + value * scale
        nodes.append(line((LEFT - 4, y), (LEFT, y)))
        if value % 4 == 0:
            nodes.append(label((LEFT - 18, y), str(value)))
    slot = PLOT_WIDTH / len(counts)
    for i, (name, count) in enumerate(zip(names(par), counts)):
        x0, x1 = LEFT + i * slot + slot * 0.2, LEFT + (i + 1) * slot - slot * 0.2
        y1 = BASE + count * scale
        nodes.append({"type": "polygon", "shade": True,
                      "points": [figures.rounded(p) for p in ((x0, BASE), (x1, BASE),
                                                              (x1, y1), (x0, y1))]})
        nodes.append(label(((x0 + x1) / 2, BASE - 16), name))
    nodes.append(label((LEFT + 40, BASE + PLOT_HEIGHT + 16), "Frequency"))
    return scene(nodes, BASE + PLOT_HEIGHT + 32)


def pie_nodes(counts, centre, radius, labels_for):
    nodes = [{"type": "circle", "center": figures.rounded(centre), "radius": radius}]
    start = 0
    for i, angle in enumerate(angles(counts)):
        turn = math.radians(start)
        nodes.append(line(centre, (centre[0] + radius * math.sin(turn),
                                   centre[1] + radius * math.cos(turn))))
        middle = math.radians(start + float(angle) / 2)
        nodes.append(label((centre[0] + 0.6 * radius * math.sin(middle),
                            centre[1] + 0.6 * radius * math.cos(middle)), labels_for[i]))
        start += float(angle)
    return nodes


def pie_labels(par, hide=None, with_angles=True):
    out = []
    for i, (name, angle) in enumerate(zip(names(par), angles(par["counts"]))):
        if with_angles and i != hide:
            out.append("{} {}°".format(name, int(angle)))
        else:
            out.append(name)
    return out


def visuals_for(par):
    form = par["form"]
    if form in BAR_FORMS:
        return (bar_scene(par),)
    if form in ("angle_from_frequency", "pie_angles"):
        return ()
    if form == "compare_pies":
        nodes = []
        for counts, centre, group in ((par["counts"], (95, 110), GROUPS[0]),
                                      (par["counts_b"], (265, 110), GROUPS[1])):
            fake = dict(par, counts=counts)
            nodes += pie_nodes(counts, centre, 72, pie_labels(fake))
            nodes.append(label((centre[0], 20), group))
        return (scene(nodes, 196),)
    hide = par["ask"] if form == "missing_angle" else None
    return (scene(pie_nodes(par["counts"], (180, 110), 88, pie_labels(par, hide)), 210),)


# ------------------------------------------------------------ checks

def check_counts(counts, pie):
    require(isinstance(counts, list) and 4 <= len(counts) <= 5
            and all(type(c) is int and c > 0 for c in counts), "Unexpected counts")
    if pie:
        require(sum(counts) in TOTALS, "Total must divide 360")
        require(all(a.denominator == 1 and a >= MIN_SECTOR for a in angles(counts)),
                "Sectors must be whole-degree and large enough to label")
    else:
        require(all(c % 2 == 0 and 2 <= c <= 20 for c in counts), "Bars must be even, up to 20")


def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    form = par.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(par) == KEYS[form] | {"form"}, "Unexpected parameters")
    require(par["theme"] in THEMES, "Unknown theme")
    check_counts(par["counts"], form not in BAR_FORMS)
    n = len(par["counts"])
    if "pair" in par:
        pair = par["pair"]
        require(isinstance(pair, list) and len(pair) == 2 and pair[0] != pair[1]
                and all(i in range(n) for i in pair), "Unexpected pair")
        if form == "bar_difference":
            require(par["counts"][pair[0]] > par["counts"][pair[1]], "First bar must be taller")
    if "ask" in par:
        require(par["ask"] in range(n), "Unexpected category")
    if form == "bar_mode":
        counts = par["counts"]
        require(counts.count(max(counts)) == 1, "Mode must be unique")
    if form == "compare_pies":
        check_counts(par["counts_b"], True)
        require(len(par["counts_b"]) == n, "Both pies need the same categories")
        a, b = par["counts"][par["ask"]], par["counts_b"][par["ask"]]
        require(a != b, "Counts must differ")
        require(sum(par["counts"]) != sum(par["counts_b"]), "Totals must differ")
    for visual in visuals_for(par):
        require(renders_cleanly(visual), "Chart does not render cleanly")


# ------------------------------------------------------------ wording and answers

def table_text(par):
    return ", ".join("{} {}".format(n, c) for n, c in zip(names(par), par["counts"]))


def prompt_for(par):
    form = par["form"]
    topic = THEMES[par["theme"]][0]
    counts, labels = par["counts"], names(par)
    total = sum(counts)
    if form in BAR_FORMS:
        opening = "The bar chart shows the {} of some students.".format(topic)
        if form == "bar_difference":
            a, b = (labels[i] for i in par["pair"])
            task = "How many more students chose {} than {}?".format(a, b)
        else:
            task = "Write down the mode."
        data = "Frequencies: {}.".format(table_text(par))
    elif form == "sector_frequency":
        opening = "The pie chart shows the {} of {} students.".format(topic, total)
        task = "How many students chose {}?".format(labels[par["ask"]])
        data = "Angles: " + ", ".join(pie_labels(par)) + "."
    elif form in ("angle_from_frequency", "pie_angles"):
        opening = "The table shows the {} of {} students: {}.".format(topic, total, table_text(par))
        task = ("Work out the angle for {} in a pie chart.".format(labels[par["ask"]])
                if form == "angle_from_frequency"
                else "Work out the angle for each sector of a pie chart.")
        return Content(opening + " " + task)
    elif form == "missing_angle":
        opening = "The pie chart shows the {} of {} students.".format(topic, total)
        task = ("(a) Work out the angle of the {} sector. (b) How many students chose {}?"
                .format(labels[par["ask"]], labels[par["ask"]]))
        data = "Angles: " + ", ".join(pie_labels(par, par["ask"])) + "."
    elif form == "total_from_sector":
        a, b = par["pair"]
        opening = "The pie chart shows the {} of some students.".format(topic)
        task = ("The {} sector represents {} students. How many students chose {}?"
                .format(labels[a], counts[a], labels[b]))
        data = "Angles: " + ", ".join(pie_labels(par)) + "."
    else:
        total_b = sum(par["counts_b"])
        opening = ("The pie charts show the {} of {} students in {} and {} students in {}."
                   .format(topic, total, GROUPS[0], total_b, GROUPS[1]))
        task = ("Which year group had more students who chose {}? You must show your working."
                .format(labels[par["ask"]]))
        other = dict(par, counts=par["counts_b"])
        data = "{} angles: {}. {} angles: {}.".format(
            GROUPS[0], ", ".join(pie_labels(par)), GROUPS[1], ", ".join(pie_labels(other)))
    instruction = opening + " " + task
    return Content(instruction + " " + data, display_text=instruction)


def answer_for(par):
    form = par["form"]
    counts, labels = par["counts"], names(par)
    if form == "bar_difference":
        a, b = par["pair"]
        return ({"kind": "integer", "value": str(counts[a] - counts[b])},
                Content(str(counts[a] - counts[b])))
    if form == "bar_mode":
        mode = labels[counts.index(max(counts))]
        return {"kind": "choice", "value": mode}, Content(mode)
    if form == "sector_frequency":
        return ({"kind": "integer", "value": str(counts[par["ask"]])},
                Content(str(counts[par["ask"]])))
    if form == "angle_from_frequency":
        angle = int(angles(counts)[par["ask"]])
        return {"kind": "angle", "value": str(angle)}, Content("{}°".format(angle))
    if form == "pie_angles":
        values = [int(a) for a in angles(counts)]
        return ({"kind": "angles", "values": [str(v) for v in values]},
                Content(", ".join("{} {}°".format(n, v) for n, v in zip(labels, values))))
    if form == "missing_angle":
        angle = int(angles(counts)[par["ask"]])
        return ({"kind": "angle_and_count", "angle": str(angle), "count": str(counts[par["ask"]])},
                Content("(a) {}° (b) {}".format(angle, counts[par["ask"]])))
    if form == "total_from_sector":
        b = par["pair"][1]
        return {"kind": "integer", "value": str(counts[b])}, Content(str(counts[b]))
    a, b = counts[par["ask"]], par["counts_b"][par["ask"]]
    winner = GROUPS[0] if a > b else GROUPS[1]
    return ({"kind": "choice", "value": winner, "counts": [str(a), str(b)]},
            Content("{}: {} students; {}: {} students. {} had more.".format(
                GROUPS[0], a, GROUPS[1], b, winner)))


def draw_counts(rng, pie):
    size = rng.choice((4, 5))
    if not pie:
        return [2 * rng.randint(1, 10) for _ in range(size)]
    total = rng.choice(TOTALS)
    unit = Fraction(total, 360)
    least = math.ceil(MIN_SECTOR * unit)
    spare = total - least * size
    if spare < 0:
        return [1] * size
    cuts = sorted(rng.randint(0, spare) for _ in range(size - 1))
    parts = [b - a for a, b in zip([0] + cuts, cuts + [spare])]
    return [least + p for p in parts]


def draw_parameters(rng, form):
    par = {"form": form, "theme": rng.choice(sorted(THEMES))}
    par["counts"] = draw_counts(rng, form not in BAR_FORMS)
    n = len(par["counts"])
    if form in ("bar_difference", "total_from_sector"):
        par["pair"] = rng.sample(range(n), 2)
    if form in ("sector_frequency", "angle_from_frequency", "missing_angle", "compare_pies"):
        par["ask"] = rng.randrange(n)
    if form == "compare_pies":
        other = draw_counts(rng, True)
        while len(other) != n:
            other = draw_counts(rng, True)
        par["counts_b"] = other
    return par


# ------------------------------------------------------------ generator

class BarPieCharts:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        form = rng.choice(FORMS[difficulty])
        for attempt in range(3000):
            par = draw_parameters(rng, form)
            try:
                check_parameters(par, difficulty)
            except ValueError:
                continue
            break
        else:
            raise ValueError("Could not construct a chart question")
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
        require(q.visual_assets("questions") == visuals_for(q.parameters), "Chart mismatch")
        return True

    def validate_independently(self, q):
        """Read bar heights and sector angles back from the drawing itself."""
        par, answer = q.parameters, q.answer
        form = par["form"]
        visuals = q.visual_assets("questions")

        def bars_from(spec):
            axis = [n for n in spec["nodes"] if n["type"] == "line"][0]
            length = axis["points"][1][1] - axis["points"][0][1]
            numbers = [int(n["text"]) for n in spec["nodes"]
                       if n["type"] == "label" and n["text"].isdigit()]
            top = max(numbers)
            return [round((n["points"][2][1] - n["points"][0][1]) / length * top)
                    for n in spec["nodes"] if n["type"] == "polygon"]

        def sectors_from(nodes, centre):
            radii = [n["points"][1] for n in nodes if n["type"] == "line"
                     and n["points"][0] == list(figures.rounded(centre))]
            bearings = [math.degrees(math.atan2(p[0] - centre[0], p[1] - centre[1])) % 360
                        for p in radii]
            bearings.append(360.0)
            return [round(bearings[i + 1] - bearings[i]) for i in range(len(radii))]

        counts = par["counts"]
        if form in BAR_FORMS:
            read = bars_from(visuals[0])
            require(read == counts, "Bar heights do not match the data")
            if form == "bar_difference":
                a, b = par["pair"]
                require(int(answer["value"]) == read[a] - read[b], "Difference disagrees")
            else:
                require(answer["value"] == names(par)[read.index(max(read))], "Mode disagrees")
            return True
        total = sum(counts)
        if form in ("angle_from_frequency", "pie_angles"):
            expected = [c * 360 // total for c in counts]
            require(all(c * 360 == e * total for c, e in zip(counts, expected)), "Angles not whole")
            if form == "pie_angles":
                require([int(v) for v in answer["values"]] == expected and sum(expected) == 360,
                        "Angles disagree")
            else:
                require(int(answer["value"]) == expected[par["ask"]], "Angle disagrees")
            return True
        if form == "compare_pies":
            nodes = visuals[0]["nodes"]
            first = sectors_from(nodes, (95, 110))
            second = sectors_from(nodes, (265, 110))
            a = first[par["ask"]] * total / 360
            b = second[par["ask"]] * sum(par["counts_b"]) / 360
            require([int(v) for v in answer["counts"]] == [a, b], "Counts disagree")
            return True
        read = sectors_from(visuals[0]["nodes"], (180, 110))
        require(sum(read) == 360, "Sectors do not make a full turn")
        if form == "sector_frequency":
            require(int(answer["value"]) * 360 == read[par["ask"]] * total, "Frequency disagrees")
        elif form == "missing_angle":
            require(int(answer["angle"]) == read[par["ask"]], "Missing angle disagrees")
            require(int(answer["count"]) * 360 == read[par["ask"]] * total, "Count disagrees")
        else:
            a, b = par["pair"]
            per_degree = Fraction(counts[a], read[a])
            require(int(answer["value"]) == per_degree * read[b], "Frequency disagrees")
        return True