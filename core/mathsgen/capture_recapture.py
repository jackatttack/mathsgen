"""Capture–recapture population estimates and reverse questions."""
from fractions import Fraction

from .core import Content, GeneratorInfo, require
from .family import GeneratorFamily


CONTEXTS = (
    ("fish", "a lake", "fish"),
    ("butterflies", "a nature reserve", "butterflies"),
    ("frogs", "a pond", "frogs"),
    ("beetles", "a woodland", "beetles"),
)


def estimate(p):
    return Fraction(p["first"] * p["second"], p["recaptured"])


class CaptureRecapture(GeneratorFamily):
    info = GeneratorInfo(
        id="probability.capture_recapture",
        version=1,
        topic="probability",
        subtopic="capture_recapture",
        title="Capture–recapture",
        difficulty_descriptions={
            1: "Estimate a population from two samples and the recaptured count.",
            2: "Find the number recaptured from a population estimate.",
            3: "Compare estimates from two different second samples.",
            4: "Identify the recaptured count from a mixed second sample, then estimate.",
        },
        tags=("probability", "capture_recapture", "population_estimate"),
    )
    keys = {
        1: {"context", "first", "second", "recaptured", "population"},
        2: {"context", "first", "second", "recaptured", "population"},
        3: {"context", "first", "second", "recaptured", "population",
            "second_b", "recaptured_b"},
        4: {"context", "first", "second", "recaptured", "population"},
    }

    def build(self, level, rng):
        for _ in range(1000):
            context = rng.randrange(len(CONTEXTS))
            population = rng.randrange(8, 81) * 10
            first = rng.randrange(3, 13) * 10
            recaptured = rng.randint(4, min(25, first - 1))
            numerator = population * recaptured
            if numerator % first:
                continue
            second = numerator // first
            if not (recaptured < second <= population and second <= 180):
                continue
            p = {
                "context": context,
                "first": first,
                "second": second,
                "recaptured": recaptured,
                "population": population,
            }
            if level == 3:
                candidates = [
                    r for r in range(4, min(26, first))
                    if r != recaptured
                    and (population * r) % first == 0
                    and r < (population * r) // first <= 180
                ]
                if not candidates:
                    continue
                other = rng.choice(candidates)
                p["recaptured_b"] = other
                p["second_b"] = population * other // first
            self.check_rules(p, level)
            return p
        raise ValueError("Could not construct capture–recapture question")

    def check_rules(self, p, level):
        require(type(p["context"]) is int
                and 0 <= p["context"] < len(CONTEXTS), "Invalid context")
        for key in ("first", "second", "recaptured", "population"):
            require(type(p[key]) is int and p[key] > 0, "Invalid count")
        require(30 <= p["first"] <= 120 and p["first"] % 10 == 0,
                "First sample outside bounds")
        require(4 <= p["recaptured"] <= 25
                and p["recaptured"] < min(p["first"], p["second"]),
                "Invalid recaptured count")
        require(p["second"] <= min(180, p["population"]),
                "Invalid second sample")
        require(80 <= p["population"] <= 800
                and p["population"] % 10 == 0, "Population outside bounds")
        require(estimate(p) == p["population"], "Population estimate disagrees")
        if level == 3:
            require(type(p["second_b"]) is int
                    and type(p["recaptured_b"]) is int, "Invalid second trial")
            require(4 <= p["recaptured_b"] <= 25
                    and p["recaptured_b"] != p["recaptured"]
                    and p["recaptured_b"] < min(p["first"], p["second_b"])
                    and p["second_b"] <= min(180, p["population"]),
                    "Invalid comparison sample")
            require(Fraction(p["first"] * p["second_b"],
                             p["recaptured_b"]) == p["population"],
                    "Comparison estimate disagrees")

    def parts(self, p, level):
        animal, location, plural = CONTEXTS[p["context"]]
        intro = (
            "A researcher is estimating the number of {} in {}. "
            "{} are caught, marked and released. "
        ).format(plural, location, p["first"])
        if level == 1:
            text = (
                intro + "Later, {} are caught. Of these, {} have a mark. "
                "Estimate the total number of {} in {}."
            ).format(p["second"], p["recaptured"], plural, location)
            value = p["population"]
        elif level == 2:
            text = (
                intro + "Later, {} are caught. The researcher estimates "
                "that there are {} {} in {}. "
                "How many of the second sample had a mark?"
            ).format(p["second"], p["population"], plural, location)
            value = p["recaptured"]
        elif level == 3:
            text = (
                intro + "In a second sample, {} are caught and {} have a mark. "
                "In a separate third sample, {} are caught and {} have a mark. "
                "Calculate the population estimate using each sample."
            ).format(p["second"], p["recaptured"],
                     p["second_b"], p["recaptured_b"])
            value = p["population"]
        else:
            unmarked = p["second"] - p["recaptured"]
            text = (
                intro + "In a later sample, {} {} are caught. "
                "{} have a mark and {} do not. "
                "Estimate the total number of {} in {}."
            ).format(p["second"], plural, p["recaptured"],
                     unmarked, plural, location)
            value = p["population"]

        answer_text = (
            "Both estimates = {}".format(value)
            if level == 3 else str(value)
        )
        return {
            "prompt": Content(text),
            "answer": {"kind": "integer", "value": value},
            "answer_display": Content(answer_text),
            "marks": {1: 2, 2: 3, 3: 3, 4: 3}[level],
            "working_lines": {1: 3, 2: 4, 3: 5, 4: 4}[level],
        }

    def validate_independently(self, question):
        import sympy
        p = question.parameters
        n = sympy.Symbol("N")
        r = sympy.Symbol("r")
        if question.difficulty == 2:
            solutions = sympy.solve(
                sympy.Eq(p["first"] * p["second"], p["population"] * r), r
            )
            require(solutions == [question.answer["value"]],
                    "Independent reverse solution disagrees")
        else:
            solutions = sympy.solve(
                sympy.Eq(p["first"] * p["second"], n * p["recaptured"]), n
            )
            require(solutions == [question.answer["value"]],
                    "Independent population solution disagrees")
            if question.difficulty == 3:
                other = sympy.solve(
                    sympy.Eq(p["first"] * p["second_b"],
                             n * p["recaptured_b"]), n
                )
                require(other == solutions,
                        "Independent comparison solution disagrees")
        return True