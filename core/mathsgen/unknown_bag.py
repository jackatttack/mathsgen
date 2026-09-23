"""Recover an unknown bag composition from a two-draw probability.

A bag holds red and other counters. Two are taken without replacement, and
the probability that both are red is stated. Writing that probability as
a product of two fractions and clearing the denominators gives a quadratic
in the unknown, which factorises.

Every question is built backwards from a real bag, so a valid answer
always exists. The quadratic's other root is then checked to be impossible
- negative, fractional, or more reds than counters - so the composition the
student finds is the only one that fits.

Difficulty follows what is unknown: the number of reds, then the total, then
a total expressed in terms of the reds, then a three-colour bag where the
stated probability involves two different colours.
"""
from fractions import Fraction
from math import isqrt

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)


INFO = GeneratorInfo(
    id="probability.unknown_bag.two_draws", version=1,
    topic="probability", subtopic="unknown_totals",
    title="Find an unknown bag composition from a probability",
    difficulty_descriptions={
        1: "Find how many red counters are in a bag of known size.",
        2: "Find the total number of counters from the number of reds.",
        3: "Find the number of reds when the total is stated in terms of them.",
        4: "Find a composition from the probability of two different colours.",
    },
    tags=("probability", "quadratics", "problem solving", "without replacement"),
)

COUNTERS = (
    ("red", "blue"),
    ("green", "yellow"),
    ("black", "white"),
)


def two_same_probability(chosen, total):
    """P(both counters the same stated colour), without replacement."""
    require(total >= 2, "A bag needs at least two counters")
    require(0 <= chosen <= total, "Impossible number of counters")
    return Fraction(chosen * (chosen - 1), total * (total - 1))


def two_different_probability(first, second, total):
    """P(one of each stated colour, in either order), without replacement."""
    require(total >= 2, "A bag needs at least two counters")
    return Fraction(2 * first * second, total * (total - 1))


def integer_roots(a, b, c):
    """Both roots of a quadratic that factorises over the integers."""
    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return None
    root = isqrt(discriminant)
    if root * root != discriminant:
        return None
    if (-b + root) % (2 * a) or (-b - root) % (2 * a):
        return None
    return sorted(((-b - root) // (2 * a), (-b + root) // (2 * a)))


def quadratic_for(p):
    """The quadratic the stated probability produces, as [a, b, c]."""
    probability = Fraction(p["probability"])
    numerator, denominator = probability.numerator, probability.denominator
    form = p["form"]

    if form == "find_reds":
        # n(n-1)/[T(T-1)] = p, with T known: n^2 - n - p*T*(T-1) = 0.
        total = p["total"]
        constant = probability * total * (total - 1)
        require(constant.denominator == 1, "Probability does not clear")
        return [1, -1, -int(constant)]

    if form == "find_total":
        # n known: p*T^2 - p*T - n(n-1) = 0, cleared of fractions.
        reds = p["reds"]
        return [
            numerator, -numerator, -denominator * reds * (reds - 1),
        ]

    if form == "total_in_terms":
        # The total is reds + extra, so the unknown is the number of reds.
        extra = p["extra"]
        # n(n-1)/[(n+e)(n+e-1)] = p  ->
        # (d - k)n^2 - (d - k(2e+1))n - k*e*(e-1) ... expanded below.
        d, k = denominator, numerator
        a = d - k
        b = -(d + k * (2 * extra - 1))
        c = -k * extra * (extra - 1)
        return [a, b, c]

    # Two colours: first * second * 2 / [T(T-1)] = p, with the second
    # colour count expressed as the total minus the first and the rest.
    reds = p["reds"]
    others = p["others"]
    return [
        numerator, -numerator,
        -denominator * 2 * reds * others,
    ]


def answer_value(p):
    form = p["form"]
    if form == "find_reds":
        return p["reds"]
    if form in ("find_total", "two_colours"):
        return p["total"]
    return p["reds"]


def probability_text(value):
    value = Fraction(value)
    return "{}/{}".format(value.numerator, value.denominator)


def presentation(p):
    first, second = COUNTERS[p["context"]]
    probability = probability_text(p["probability"])
    form = p["form"]

    if form == "find_reds":
        return Content(
            "A bag contains {} counters. Some are {} and the rest are {}. "
            "Two counters are taken at random without replacement. The "
            "probability that both are {} is {}. Find how many {} counters "
            "are in the bag.".format(
                p["total"], first, second, first, probability, first
            )
        )

    if form == "find_total":
        return Content(
            "A bag contains {} {} counters and some {} counters. Two counters "
            "are taken at random without replacement. The probability that "
            "both are {} is {}. Find the total number of counters.".format(
                p["reds"], first, second, first, probability
            )
        )

    if form == "total_in_terms":
        return Content(
            "A bag contains n {} counters and {} {} counters. Two counters "
            "are taken at random without replacement. The probability that "
            "both are {} is {}. Find the value of n.".format(
                first, p["extra"], second, first, probability
            )
        )

    return Content(
        "A bag contains {} {} counters, {} {} counters and some other "
        "counters. Two counters are taken at random without replacement. "
        "The probability that one is {} and one is {} is {}. Find the total "
        "number of counters.".format(
            p["reds"], first, p["others"], second, first, second, probability
        )
    )


def answer_for(p):
    value = answer_value(p)
    answer = {"kind": "integer", "value": value}
    form = p["form"]
    if form == "find_reds":
        return answer, Content("{} counters".format(value))
    if form == "total_in_terms":
        return answer, Content("n = {}".format(value))
    return answer, Content("{} counters".format(value))


class UnknownBag:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng

        for attempt in range(600):
            p = self.make_bag(rng, difficulty)
            if p is not None and self.acceptable(p):
                break
        else:
            raise ValueError("Could not construct a suitable bag")

        prompt = presentation(p)
        answer, display = answer_for(p)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=4 if difficulty >= 3 else 3, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=7),
            parameters=p,
        )
        self.validate(question)
        return question

    def make_bag(self, rng, difficulty):
        """Build a real bag first, then state its probability."""
        context_index = rng.randrange(len(COUNTERS))

        if difficulty == 1:
            total = rng.randint(6, 14)
            reds = rng.randint(3, total - 1)
            return {
                "form": "find_reds", "context": context_index,
                "total": total, "reds": reds,
                "probability": rational_text(two_same_probability(reds, total)),
            }

        if difficulty == 2:
            total = rng.randint(7, 16)
            reds = rng.randint(3, total - 2)
            return {
                "form": "find_total", "context": context_index,
                "total": total, "reds": reds,
                "probability": rational_text(two_same_probability(reds, total)),
            }

        if difficulty == 3:
            reds = rng.randint(3, 10)
            extra = rng.randint(2, 8)
            total = reds + extra
            return {
                "form": "total_in_terms", "context": context_index,
                "reds": reds, "extra": extra, "total": total,
                "probability": rational_text(two_same_probability(reds, total)),
            }

        total = rng.randint(8, 16)
        reds = rng.randint(2, 6)
        others = rng.randint(2, 6)
        if reds + others > total:
            return None
        return {
            "form": "two_colours", "context": context_index,
            "total": total, "reds": reds, "others": others,
            "probability": rational_text(
                two_different_probability(reds, others, total)
            ),
        }

    def acceptable(self, p):
        """Whether the quadratic has a single valid solution."""
        coefficients = quadratic_for(p)
        if coefficients[0] == 0:
            return False
        roots = integer_roots(*coefficients)
        if roots is None:
            return False

        wanted = answer_value(p)
        if wanted not in roots:
            return False

        # The other root must be impossible, so the composition is unique.
        others = [value for value in roots if value != wanted]
        if not others:
            # A repeated root is fine: there is only one solution anyway.
            return True
        for value in others:
            if self.plausible(p, value):
                return False
        return True

    def plausible(self, p, candidate):
        """Whether a root could be mistaken for a valid answer."""
        if candidate < 0:
            return False
        form = p["form"]
        if form == "find_reds":
            return 2 <= candidate <= p["total"]
        if form == "find_total":
            return candidate >= max(2, p["reds"])
        if form == "total_in_terms":
            return candidate >= 2
        return candidate >= max(2, p["reds"] + p["others"])

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid level")
        require(q.settings == {}, "Unsupported settings")

        p = q.parameters
        expected = {
            1: "find_reds", 2: "find_total",
            3: "total_in_terms", 4: "two_colours",
        }[level]
        require(p["form"] == expected, "Form does not match difficulty")
        require(p["context"] in range(len(COUNTERS)), "Unknown context")

        probability = Fraction(p["probability"])
        require(p["probability"] == rational_text(probability),
                "Non-canonical probability")
        require(0 < probability < 1, "Probability must be strictly between 0 and 1")

        total = p["total"]
        require(type(total) is int and total >= 4, "Bag is too small")

        if p["form"] == "two_colours":
            reds, others = p["reds"], p["others"]
            require(reds >= 2 and others >= 2, "Both colours need counters")
            require(reds + others <= total, "The bag cannot hold these counters")
            require(probability == two_different_probability(reds, others, total),
                    "Stated probability does not match the bag")
        else:
            reds = p["reds"]
            require(type(reds) is int and 2 <= reds <= total,
                    "Impossible number of reds")
            require(probability == two_same_probability(reds, total),
                    "Stated probability does not match the bag")
            if p["form"] == "total_in_terms":
                require(p["extra"] >= 2, "There must be other counters")
                require(total == reds + p["extra"],
                        "The total must be the reds plus the others")

        require(self.acceptable(p), "The composition is not uniquely recoverable")

        answer, display = answer_for(p)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Display mismatch")
        require(q.prompt == presentation(p), "Prompt mismatch")
        require(q.visual_assets("questions") == ()
                and q.visual_assets("answers") == (),
                "This family uses no visual assets")
        return True

    def validate_independently(self, q):
        """Search every possible bag and confirm only one fits.

        Enumerating the compositions is a different route from solving the
        quadratic, and it proves uniqueness directly rather than by
        reasoning about the second root.
        """
        p = q.parameters
        probability = Fraction(p["probability"])
        form = p["form"]
        matches = []

        if form == "find_reds":
            total = p["total"]
            for reds in range(2, total + 1):
                if two_same_probability(reds, total) == probability:
                    matches.append(reds)
        elif form == "find_total":
            reds = p["reds"]
            for total in range(max(2, reds), 60):
                if two_same_probability(reds, total) == probability:
                    matches.append(total)
        elif form == "total_in_terms":
            extra = p["extra"]
            for reds in range(2, 40):
                total = reds + extra
                if two_same_probability(reds, total) == probability:
                    matches.append(reds)
        else:
            reds, others = p["reds"], p["others"]
            for total in range(reds + others, 60):
                if two_different_probability(reds, others, total) == probability:
                    matches.append(total)

        require(matches, "No composition produces the stated probability")
        require(len(matches) == 1,
                "More than one composition produces the stated probability")
        require(matches[0] == q.answer["value"],
                "Independent search disagrees with the stated answer")
        return True