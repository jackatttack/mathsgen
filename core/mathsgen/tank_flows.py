"""Rectangular tank problems connecting volume, flow rates and elapsed time."""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question,
    make_context, rational_text, rational_tex, require,
)


INFO = GeneratorInfo(
    id="problem_solving.liquid_flow.tanks",
    version=1,
    topic="problem_solving",
    subtopic="liquid_flow",
    title="Tanks: filling, draining and missing dimensions",
    difficulty_descriptions={
        1: "Find the time to raise the water to a specified depth.",
        2: "Combine simultaneous inflow and outflow.",
        3: "Find an internal tank width from a change in depth and elapsed time.",
        4: "Account for a drain opening partway through filling.",
    },
    tags=("problem solving", "volume", "rates", "time", "units", "algebra"),
)


def paragraph(value):
    return {"kind": "paragraph", "text": value}


def equation(tex, fallback):
    return {"kind": "equation", "tex": tex, "text": fallback}


def duration(minutes):
    """Generation constrains elapsed times to exact whole seconds."""
    seconds = Fraction(minutes) * 60
    require(seconds.denominator == 1 and seconds >= 0, "Time must be whole seconds")
    whole_minutes, remainder = divmod(seconds.numerator, 60)
    parts = []
    if whole_minutes:
        parts.append("{} {}".format(whole_minutes, "minute" if whole_minutes == 1 else "minutes"))
    if remainder or not parts:
        parts.append("{} {}".format(remainder, "second" if remainder == 1 else "seconds"))
    return " ".join(parts)


def known_volume(parameters):
    return Fraction(
        parameters["length"] * parameters["width"]
        * (parameters["target_depth"] - parameters["initial_depth"]),
        1000,
    )


def results_for(p, level):
    net = p["inlet"] - p["outlet"]
    if level == 3:
        elapsed = Fraction(p["elapsed"])
        litres = elapsed * net
        width = litres * 1000 / (
            p["length"] * (p["target_depth"] - p["initial_depth"])
        )
        return {
            "kind": "tank_dimension",
            "width": rational_text(width),
            "litres_added": rational_text(litres),
            "net_rate": net,
        }
    litres = known_volume(p)
    delay = p["delay"]
    first_litres = delay * p["inlet"]
    remaining = litres - first_litres
    after = remaining / net
    return {
        "kind": "tank_time",
        "litres_added": rational_text(litres),
        "net_rate": net,
        "first_litres": rational_text(first_litres),
        "remaining_litres": rational_text(remaining),
        "after_minutes": rational_text(after),
        "total_minutes": rational_text(delay + after),
    }


def presentation(p, level):
    if level == 3:
        opening = (
            "An open rectangular tank has internal length {} cm and height {} cm. "
            "Its internal width is x cm."
        ).format(p["length"], p["tank_height"])
        first_block = {
            "kind": "paragraph",
            "runs": [
                {"text": "An open rectangular tank has internal length {} cm and height {} cm. "
                         "Its internal width is ".format(p["length"], p["tank_height"])},
                {"tex": r"x\,\mathrm{cm}", "text": "x cm"},
                {"text": "."},
            ],
        }
    else:
        opening = (
            "An open rectangular tank has internal length {} cm, width {} cm "
            "and height {} cm."
        ).format(p["length"], p["width"], p["tank_height"])
        first_block = paragraph(opening)
    initial = "Initially the water is {} cm deep.".format(p["initial_depth"])
    flow = "A pipe supplies water at a constant rate of {} litres per minute.".format(p["inlet"])
    if level in (2, 3):
        flow += (
            " At the same time, a pump removes water at a constant rate of "
            "{} litres per minute."
        ).format(p["outlet"])
    elif level == 4:
        flow += (
            " After {} minutes, an outlet opens and removes water at a constant "
            "rate of {} litres per minute. The inlet remains on."
        ).format(p["delay"], p["outlet"])
    assumptions = (
        "The tank stays upright on a level base. Ignore the pipe's volume. "
        "There are no other water losses. Use 1000 cubic centimetres = 1 litre."
    )
    assumption_block = {
        "kind": "paragraph",
        "runs": [
            {"text": "The tank stays upright on a level base. Ignore the pipe's volume. "
                     "There are no other water losses. Use "},
            {"tex": r"1000\,\mathrm{cm}^{3}=1\,\mathrm{L}",
             "text": "1000 cubic centimetres = 1 litre"},
            {"text": "."},
        ],
    }
    if level == 3:
        task = (
            "After {}, the water is {} cm deep. Form an equation and find "
            "the internal width of the tank."
        ).format(duration(Fraction(p["elapsed"])), p["target_depth"])
    else:
        task = (
            "How long after the inlet is switched on will the water first reach "
            "a depth of {} cm? Give your answer in minutes and seconds."
        ).format(p["target_depth"])
    return Content(
        " ".join((opening, initial, flow, assumptions, task)),
        blocks=(first_block, paragraph(initial), paragraph(flow),
                assumption_block, paragraph(task)),
    )


def display_for(p, level, answer):
    litres = answer["litres_added"]
    blocks = [equation(
        r"\Delta V=" + rational_tex(Fraction(litres)) + r"\,\mathrm{L}",
        "Volume increase = " + litres + " litres",
    )]
    if level == 3:
        elapsed = Fraction(p["elapsed"])
        lhs = "{}x({}-{})".format(
            p["length"], p["target_depth"], p["initial_depth"],
        )
        rhs = "1000({}-{})".format(p["inlet"], p["outlet"])
        tex = lhs + "=" + rhs + r"\times " + rational_tex(elapsed)
        blocks += [
            paragraph("One valid equation, using cubic centimetres, is"),
            equation(tex, lhs + " = " + rhs + " * " + rational_text(elapsed)),
            equation(
                "x=" + rational_tex(Fraction(answer["width"])) + r"\,\mathrm{cm}",
                "Width = " + answer["width"] + " cm",
            ),
        ]
        fallback = (
            "Net inflow: {} litres/minute. Volume increase: {} litres. "
            "Equation: {} = {} * {}. Width = {} cm."
        ).format(answer["net_rate"], litres, lhs, rhs,
                 rational_text(elapsed), answer["width"])
    else:
        if level == 4:
            blocks.append(paragraph(
                "Before the outlet opens: {} litres added. "
                "{} litres still needed.".format(
                    answer["first_litres"], answer["remaining_litres"],
                )
            ))
        blocks.append(paragraph(
            "Net inflow{}: {} litres per minute.".format(
                " after the outlet opens" if level == 4 else "",
                answer["net_rate"],
            )
        ))
        blocks.append(equation(
            "t=" + (str(p["delay"]) + "+" if level == 4 else "")
            + r"\frac{" + rational_tex(Fraction(answer["remaining_litres"]))
            + "}{" + str(answer["net_rate"]) + "}"
            + "=" + rational_tex(Fraction(answer["total_minutes"])) + r"\,\mathrm{min}",
            "Total time = {} + {}/{} = {} minutes".format(
                p["delay"], answer["remaining_litres"],
                answer["net_rate"], answer["total_minutes"],
            ),
        ))
        conclusion = "Total elapsed time: " + duration(Fraction(answer["total_minutes"])) + "."
        blocks.append(paragraph(conclusion))
        fallback = (
            "Volume increase: {} litres. Before the outlet opens: {} litres. "
            "Remaining: {} litres. Net inflow: {} litres/minute. {}"
        ).format(litres, answer["first_litres"], answer["remaining_litres"],
                 answer["net_rate"], conclusion)
    return Content(fallback, blocks=tuple(blocks))


def check_parameters(p, level):
    keys = {
        "length", "tank_height", "initial_depth", "target_depth",
        "inlet", "outlet", "delay",
    } | ({"elapsed"} if level == 3 else {"width"})
    require(set(p) == keys, "Unexpected parameters")
    for key in keys - {"elapsed"}:
        require(type(p[key]) is int, "Expected integer " + key)
    require(p["length"] in range(40, 121, 10), "Invalid length")
    require(p["tank_height"] in range(60, 121, 10), "Invalid tank height")
    require(
        p["initial_depth"] in (10, 20, 30)
        and p["target_depth"] % 10 == 0
        and p["initial_depth"] < p["target_depth"] <= p["tank_height"] - 10,
        "Invalid water depths or insufficient freeboard",
    )
    require(2 <= p["inlet"] <= 18, "Invalid inlet rate")
    require(p["outlet"] == 0 if level == 1 else 2 <= p["outlet"] <= 6,
            "Invalid outlet rate")
    require(p["inlet"] - p["outlet"] in (2, 3, 4, 5, 6, 10, 12),
            "Unsupported net inflow")
    require(p["delay"] >= 1 if level == 4 else p["delay"] == 0,
            "Wrong stage timing")
    if level == 3:
        require(isinstance(p["elapsed"], str) and Fraction(p["elapsed"]) > 0,
                "Invalid elapsed time")
        require((Fraction(p["elapsed"]) * 60).denominator == 1,
                "Elapsed time must be whole seconds")
        width = Fraction(results_for(p, level)["width"])
        require(width.denominator == 1 and width.numerator in range(30, 101, 10),
                "Invalid recovered width")
    else:
        require(p["width"] in range(30, 101, 10), "Invalid width")
        require(p["delay"] * p["inlet"] < known_volume(p),
                "Target must be reached after the change of flow")
        require((Fraction(results_for(p, level)["total_minutes"]) * 60).denominator == 1,
                "Answer must be whole seconds")


class TankFlows:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        for attempt in range(100):
            net = rng.choice((2, 3, 4, 5, 6, 10, 12))
            outlet = 0 if difficulty == 1 else rng.randint(2, 6)
            initial = rng.choice((10, 20, 30))
            height = rng.randrange(60, 121, 10)
            p = {
                "length": rng.randrange(40, 121, 10),
                "width": rng.randrange(30, 101, 10),
                "tank_height": height,
                "initial_depth": initial,
                "target_depth": rng.randrange(initial + 10, height, 10),
                "inlet": net + outlet, "outlet": outlet, "delay": 0,
            }
            litres = known_volume(p)
            if difficulty == 4:
                possible = [t for t in range(1, 11) if t * p["inlet"] < litres]
                if not possible:
                    continue
                p["delay"] = rng.choice(possible)
            if difficulty == 3:
                p["elapsed"] = rational_text(litres / net)
                del p["width"]
            break
        else:
            raise ValueError("Could not construct a staged tank question")
        answer = results_for(p, difficulty)
        q = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=presentation(p, difficulty),
            answer=answer, answer_display=display_for(p, difficulty, answer),
            worked_solution=(), marks=5 if difficulty >= 3 else 4,
            tags=self.info.tags, layout_hint=LayoutHint(working_lines=7),
            parameters=p,
        )
        self.validate(q)
        return q

    def validate(self, q):
        require(q.generator_id == self.info.id and q.generator_version == self.info.version,
                "Generator/version mismatch")
        require(type(q.difficulty) is int and q.difficulty in (1, 2, 3, 4), "Invalid level")
        require(q.settings == {}, "Unsupported settings")
        check_parameters(q.parameters, q.difficulty)
        expected = results_for(q.parameters, q.difficulty)
        require(q.answer == expected, "Incorrect answer")
        require(q.prompt == presentation(q.parameters, q.difficulty), "Prompt mismatch")
        require(q.answer_display == display_for(q.parameters, q.difficulty, expected),
                "Answer display mismatch")
        return True

    def validate_independently(self, q):
        """Verify conservation using initial/final volumes and elapsed seconds."""
        p, answer = q.parameters, q.answer
        width = Fraction(answer["width"]) if q.difficulty == 3 else Fraction(p["width"])
        seconds = Fraction(p["elapsed"] if q.difficulty == 3 else answer["total_minutes"]) * 60
        require(seconds > 0 and seconds.denominator == 1 and width > 0, "Invalid time/width")
        before = Fraction(p["length"]) * width * p["initial_depth"]
        after = Fraction(p["length"]) * width * p["target_depth"]
        outlet_seconds = seconds - 60 * p["delay"]
        require(outlet_seconds > 0, "Target occurs before stage change")
        supplied = Fraction(p["inlet"] * 1000, 60) * seconds
        removed = Fraction(p["outlet"] * 1000, 60) * outlet_seconds
        require(before + supplied - removed == after, "Water conservation failed")
        require(Fraction(answer["litres_added"]) * 1000 == after - before, "Wrong volume change")
        require(answer["net_rate"] == p["inlet"] - p["outlet"], "Wrong net rate")
        if q.difficulty != 3:
            first = Fraction(p["inlet"]) * p["delay"]
            require(Fraction(answer["first_litres"]) == first, "Wrong first-stage volume")
            require(Fraction(answer["remaining_litres"]) == (after - before) / 1000 - first,
                    "Wrong remaining volume")
            require(Fraction(answer["after_minutes"]) * 60 == outlet_seconds,
                    "Wrong second-stage duration")
        return True