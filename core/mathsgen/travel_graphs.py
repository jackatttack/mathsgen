"""Travel graphs: distance-time journeys and velocity-time motion.

Distance-time journeys are legs [minutes, change in km] with vertices on grid
lines, whole-number speeds in km/h, one stop, and a return home. Velocity-time
profiles accelerate, hold a speed, then decelerate, with terminating
accelerations. The level 4 curve is v = c t (T - t), whose exact area c T^3 / 6
lets the four-strip trapezium estimate be checked as a genuine underestimate.
"""
import math
from fractions import Fraction

from .bearings import rounded_sig_figs, sig_figs_text
from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


INFO = GeneratorInfo(
    id="ratio.graphs.travel", version=1,
    topic="ratio", subtopic="travel_graphs",
    title="Travel graphs: distance-time and velocity-time",
    difficulty_descriptions={
        1: "Read a distance-time graph: a distance at a time, or the length of a stop.",
        2: "Find a speed from a distance-time graph, or the fastest part of the journey.",
        3: "Find an acceleration, or a distance travelled, from a velocity-time graph.",
        4: "Find an average speed, or estimate the area under a curve with trapezia.",
    },
    tags=("ratio", "graphs", "speed", "distance-time", "velocity-time"),
)


# ------------------------------------------------------------ editable knobs

FORMS = {
    1: ("distance_at", "stop_length"),
    2: ("leg_speed", "fastest"),
    3: ("acceleration", "distance"),
    4: ("average_speed", "curve_estimate"),
}
JOURNEY_FORMS = ("distance_at", "stop_length", "leg_speed", "fastest")
TERMINATING = (1, 2, 4, 5, 10, 20, 25, 50, 100)
CURVE_SPANS = (8, 12, 16, 20)
STRIPS = 4
MARKS = {1: 1, 2: 2, 3: 2, 4: 3}
WORKING_LINES = {1: 2, 2: 3, 3: 4, 4: 7}

KEYS = {
    "distance_at": {"legs", "ask"},
    "stop_length": {"legs"},
    "leg_speed": {"legs", "ask"},
    "fastest": {"legs"},
    "acceleration": {"profile", "top"},
    "distance": {"profile", "top"},
    "average_speed": {"profile", "top"},
    "curve_estimate": {"span", "peak"},
}


# ------------------------------------------------------------ journeys

def vertices(legs):
    out, time, distance = [(0, 0)], 0, 0
    for minutes, change in legs:
        time += minutes
        distance += change
        out.append((time, distance))
    return out


def speed(leg):
    minutes, change = leg
    return Fraction(abs(change) * 60, minutes)


def check_journey(par):
    legs = par["legs"]
    require(isinstance(legs, list) and 3 <= len(legs) <= 4
            and all(isinstance(l, list) and len(l) == 2 and all(type(v) is int for v in l)
                    for l in legs), "Unexpected legs")
    require(all(10 <= m <= 60 and m % 10 == 0 for m, _ in legs), "Durations outside bounds")
    require(all(c % 2 == 0 and abs(c) <= 30 for _, c in legs), "Distance changes outside bounds")
    points = vertices(legs)
    require(all(0 <= d <= 30 for _, d in points) and points[-1][1] == 0, "Must return home")
    require(points[-1][0] <= 180, "Journey too long")
    require(sum(1 for _, c in legs if c == 0) == 1, "Exactly one stop")
    require(legs[0][1] > 0, "The journey starts by leaving home")
    for leg in legs:
        if leg[1]:
            require(speed(leg).denominator == 1, "Speeds must be whole numbers")
            # A cyclist: nothing slower than walking pace or faster than 30 km/h.
            require(6 <= speed(leg) <= 30, "Unrealistic cycling speed")


# ------------------------------------------------------------ velocity-time

def motion_vertices(par):
    t1, t2, t3 = par["profile"]
    v = par["top"]
    return [(0, 0), (t1, v), (t1 + t2, v), (t1 + t2 + t3, 0)]


def motion_distance(par):
    t1, t2, t3 = par["profile"]
    return Fraction(par["top"]) * (Fraction(t1, 2) + t2 + Fraction(t3, 2))


def curve_values(par):
    span, peak = par["span"], par["peak"]
    c = Fraction(4 * peak, span * span)
    width = Fraction(span, STRIPS)
    return c, width, [c * (i * width) * (span - i * width) for i in range(STRIPS + 1)]


def curve_estimate(par):
    _, width, values = curve_values(par)
    return sum(width * (values[i] + values[i + 1]) / 2 for i in range(STRIPS))


def check_parameters(par, level):
    require(isinstance(par, dict), "Parameters must be a dictionary")
    form = par.get("form")
    require(level in FORMS and form in FORMS[level], "Unexpected form for this level")
    require(set(par) == KEYS[form] | {"form"}, "Unexpected parameters")
    if form in JOURNEY_FORMS:
        check_journey(par)
        legs = par["legs"]
        if form == "distance_at":
            require(type(par["ask"]) is int and 1 <= par["ask"] <= len(legs) - 1,
                    "Unexpected time")
        elif form == "leg_speed":
            require(type(par["ask"]) is int and 0 <= par["ask"] < len(legs)
                    and legs[par["ask"]][1] != 0, "Ask about a moving stage")
        elif form == "fastest":
            speeds = sorted((speed(l) for l in legs if l[1]), reverse=True)
            require(speeds[0] > speeds[1], "Fastest stage must be unique")
    elif form == "curve_estimate":
        require(par["span"] in CURVE_SPANS and type(par["peak"]) is int
                and 6 <= par["peak"] <= 24, "Curve outside bounds")
    else:
        profile = par["profile"]
        require(isinstance(profile, list) and len(profile) == 3
                and all(type(t) is int for t in profile), "Unexpected profile")
        t1, t2, t3 = profile
        require(2 <= t1 <= 10 and 2 <= t2 <= 20 and 2 <= t3 <= 10 and t1 + t2 + t3 <= 40,
                "Times outside bounds")
        require(type(par["top"]) is int and 4 <= par["top"] <= 20, "Speed outside bounds")
        require(Fraction(par["top"], t1).denominator in TERMINATING,
                "Acceleration must terminate")
        if form == "average_speed":
            rounded_sig_figs(float(motion_distance(par) / (t1 + t2 + t3)))


# ------------------------------------------------------------ presentation

def axis(top, choices):
    for step in choices:
        if top / step <= 12:
            return step, step * math.ceil(top / step)
    return choices[-1], choices[-1] * math.ceil(top / choices[-1])


def plot(par):
    form = par["form"]
    if form in JOURNEY_FORMS:
        points = vertices(par["legs"])
        x_step, x_top = axis(points[-1][0], (10, 20, 30))
        y_step, y_top = axis(max(d for _, d in points), (2, 4, 5))
        labels = ("Time (minutes)", "Distance from home (km)")
    elif form == "curve_estimate":
        c, _, _ = curve_values(par)
        span = par["span"]
        points = [(span * i / 40, float(c * Fraction(span * i, 40) * (span - Fraction(span * i, 40))))
                  for i in range(41)]
        x_step, x_top = axis(span, (2, 4, 5))
        y_step, y_top = axis(par["peak"] + 1, (2, 4, 5))
        labels = ("Time (seconds)", "Velocity (m/s)")
    else:
        points = motion_vertices(par)
        x_step, x_top = axis(points[-1][0], (2, 4, 5))
        y_step, y_top = axis(par["top"] + 1, (2, 4, 5))
        labels = ("Time (seconds)", "Velocity (m/s)")
    return {
        "kind": "plot", "version": 1, "x_range": [0, x_top], "y_range": [0, y_top],
        "x_step": x_step, "y_step": y_step, "minor_divisions": 2, "equal_units": False,
        "x_label": labels[0], "y_label": labels[1],
        "curves": [{"segments": [[[float(x), float(y)] for x, y in points]]}],
    }


def prompt_for(par):
    form = par["form"]
    if form in JOURNEY_FORMS:
        legs, points = par["legs"], vertices(par["legs"])
        listing = "The graph passes through " + ", ".join(
            "({}, {})".format(t, d) for t, d in points) + " (minutes, km)."
        opening = ("Sam cycles from home to a lake, stops for a rest, and later returns home. "
                   "The distance-time graph shows the journey.")
        if form == "distance_at":
            task = "How far from home was Sam after {} minutes?".format(points[par["ask"]][0])
        elif form == "stop_length":
            task = "For how many minutes did Sam stop?"
        elif form == "leg_speed":
            start, end = points[par["ask"]][0], points[par["ask"] + 1][0]
            task = ("Work out Sam's speed, in km/h, between {} and {} minutes."
                    .format(start, end))
        else:
            task = "During which part of the journey was Sam travelling fastest? Give a reason."
        instruction = opening + " " + task
        return Content(instruction + " " + listing, display_text=instruction)
    if form == "curve_estimate":
        span = par["span"]
        c, _, _ = curve_values(par)
        instruction = ("The velocity-time graph shows the first {} seconds of a car's journey. "
                       "(a) Use 4 strips of equal width to estimate the distance travelled in "
                       "the {} seconds. (b) Is your answer an underestimate or an overestimate? "
                       "Give a reason.").format(span, span)
        listing = "The curve is v = ({})t({} - t).".format(rational_text(c), span)
        return Content(instruction + " " + listing, display_text=instruction)
    points = motion_vertices(par)
    listing = "The graph passes through " + ", ".join(
        "({}, {})".format(t, v) for t, v in points) + " (seconds, m/s)."
    opening = "The velocity-time graph shows a cyclist's journey between two sets of lights."
    if form == "acceleration":
        task = "Work out the acceleration during the first {} seconds.".format(points[1][0])
    elif form == "distance":
        task = "Work out the total distance travelled."
    else:
        task = ("Work out the average speed for the whole journey. Give your answer correct "
                "to 3 significant figures.")
    instruction = opening + " " + task
    return Content(instruction + " " + listing, display_text=instruction)


def decimal(value):
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return ("{:.2f}".format(float(value))).rstrip("0").rstrip(".")


def answer_for(par):
    form = par["form"]
    if form in JOURNEY_FORMS:
        legs, points = par["legs"], vertices(par["legs"])
        if form == "distance_at":
            d = points[par["ask"]][1]
            return {"kind": "quantity", "value": str(d), "unit": "km"}, Content("{} km".format(d))
        if form == "stop_length":
            minutes = [m for m, c in legs if c == 0][0]
            return ({"kind": "quantity", "value": str(minutes), "unit": "minutes"},
                    Content("{} minutes".format(minutes)))
        if form == "leg_speed":
            value = speed(legs[par["ask"]])
            return ({"kind": "quantity", "value": rational_text(value), "unit": "km/h"},
                    Content("{} km/h".format(rational_text(value))))
        index = max((i for i, l in enumerate(legs) if l[1]), key=lambda i: speed(legs[i]))
        start, end = points[index][0], points[index + 1][0]
        return ({"kind": "interval", "start": str(start), "end": str(end)},
                Content("Between {} and {} minutes: the line is steepest there ({} km/h)."
                        .format(start, end, rational_text(speed(legs[index])))))
    if form == "acceleration":
        value = Fraction(par["top"], par["profile"][0])
        return ({"kind": "quantity", "value": rational_text(value), "unit": "m/s^2"},
                Content("{} m/s²".format(decimal(value))))
    if form == "distance":
        value = motion_distance(par)
        return ({"kind": "quantity", "value": rational_text(value), "unit": "m"},
                Content("{} m".format(decimal(value))))
    if form == "average_speed":
        rounded = rounded_sig_figs(float(motion_distance(par) / sum(par["profile"])))
        return ({"kind": "rounded_measure", "value": rational_text(rounded), "unit": "m/s"},
                Content("{} m/s".format(sig_figs_text(rounded))))
    value = curve_estimate(par)
    return ({"kind": "estimate", "value": rational_text(value), "judgement": "underestimate"},
            Content("(a) {} m (b) An underestimate: the curve bends above the tops of the "
                    "trapezia, so they miss some of the area.".format(decimal(value))))


def draw_parameters(rng, form):
    par = {"form": form}
    if form in JOURNEY_FORMS:
        out = rng.randrange(4, 17, 2)
        more = rng.choice((0, 2, 4, 6, 8))
        speeds = (6, 8, 10, 12, 15, 20, 24, 30)

        def leg(change):
            options = [m for m in range(10, 61, 10) if abs(change) * 60 % m == 0
                       and abs(change) * 60 // m in speeds]
            return [rng.choice(options) if options else 10, change]

        legs = [leg(out), [rng.randrange(10, 41, 10), 0]]
        if more:
            legs.append(leg(more))
        legs.append(leg(-(out + more)))
        par["legs"] = legs
        if form == "distance_at":
            par["ask"] = rng.randint(1, len(legs) - 1)
        elif form == "leg_speed":
            par["ask"] = rng.choice([i for i, l in enumerate(legs) if l[1]])
    elif form == "curve_estimate":
        par.update(span=rng.choice(CURVE_SPANS), peak=rng.randint(6, 24))
    else:
        par.update(profile=[rng.randint(2, 10), rng.randint(2, 20), rng.randint(2, 10)],
                   top=rng.randint(4, 20))
    return par


# ------------------------------------------------------------ generator

class TravelGraphs:
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
            raise ValueError("Could not construct a travel graph question")
        answer, display = answer_for(par)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt_for(par),
            answer=answer, answer_display=display, worked_solution=(),
            marks=MARKS[difficulty], tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=WORKING_LINES[difficulty]),
            parameters=par, question_visuals=(plot(par),),
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
        require(q.visual_assets("questions") == (plot(q.parameters),), "Graph mismatch")
        return True

    def validate_independently(self, q):
        """Shoelace areas, rise over run from vertices, cross-multiplied speeds and the
        exact integral of the curve."""
        par, answer = q.parameters, q.answer
        form = par.get("form")

        def shoelace(points):
            closed = points + [points[0]]
            return abs(sum(Fraction(x1) * y2 - Fraction(x2) * y1
                           for (x1, y1), (x2, y2) in zip(closed, closed[1:]))) / 2

        if form in JOURNEY_FORMS:
            legs = par["legs"]
            times, distances = [0], [0]
            for minutes, change in legs:
                times.append(times[-1] + minutes)
                distances.append(distances[-1] + change)
            if form == "distance_at":
                require(int(answer["value"]) == distances[par["ask"]], "Distance disagrees")
            elif form == "stop_length":
                stops = [times[i + 1] - times[i] for i in range(len(legs))
                         if distances[i + 1] == distances[i]]
                require([int(answer["value"])] == stops, "Stop disagrees")
            elif form == "leg_speed":
                i = par["ask"]
                rise, run = abs(distances[i + 1] - distances[i]), times[i + 1] - times[i]
                require(Fraction(answer["value"]) * run == rise * 60, "Speed disagrees")
            else:
                start, end = int(answer["start"]), int(answer["end"])
                i = times.index(start)
                require(times[i + 1] == end, "Stated interval is not a stage")
                rise, run = abs(distances[i + 1] - distances[i]), end - start
                for j in range(len(legs)):
                    if j != i:
                        other_rise = abs(distances[j + 1] - distances[j])
                        other_run = times[j + 1] - times[j]
                        require(rise * other_run > other_rise * run, "Not the fastest stage")
            return True
        if form == "curve_estimate":
            c, width, values = curve_values(par)
            composite = width / 2 * (values[0] + 2 * sum(values[1:-1]) + values[-1])
            exact = c * Fraction(par["span"]) ** 3 / 6
            require(Fraction(answer["value"]) == composite, "Trapezium estimate disagrees")
            require(composite < exact and answer["judgement"] == "underestimate",
                    "Estimate should be an underestimate")
            return True
        points = motion_vertices(par)
        if form == "acceleration":
            (t0, v0), (t1, v1) = points[0], points[1]
            require(Fraction(answer["value"]) == Fraction(v1 - v0, t1 - t0),
                    "Acceleration disagrees")
        else:
            area = shoelace(points)
            if form == "distance":
                require(Fraction(answer["value"]) == area, "Distance disagrees")
            else:
                average = area / points[-1][0]
                stated = Fraction(answer["value"])
                step = 10 ** (math.floor(math.log10(float(stated))) - 2)
                require(abs(float(average) - float(stated)) <= step / 2 + 1e-9,
                        "Average speed disagrees")
        return True