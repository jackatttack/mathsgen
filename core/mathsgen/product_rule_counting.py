"""The product rule for counting: multiply the choices at each stage.

If one stage has m outcomes and the next has n, the pair has m times n.
The misconception is adding instead of multiplying, which is why no
question here is built where the sum and the product coincide.

Difficulty follows the structure: independent stages, then stages where a
choice is used up, then a restriction that removes some options, then a
count that must be assembled from two separate cases.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context, require,
)


INFO = GeneratorInfo(
    id="number.counting.product_rule", version=2,
    topic="number", subtopic="counting",
    title="The product rule for counting",
    difficulty_descriptions={
        1: "Count the combinations from two or three independent choices.",
        2: "Count arrangements where each item can be used only once.",
        3: "Count arrangements subject to a restriction.",
        4: "Count by adding two separate cases together.",
    },
    tags=("counting", "product rule", "combinations", "arrangements"),
)

# Each entry carries its own opening clause, since "a menu offers" only
# suits the food context: a wardrobe does not offer a menu of shirts.
# The last entry describes the choice when only the first two stages are
# listed, so a two-stage menu never asks for "a three-course meal".
MENU_CONTEXTS = (
    ("starters", "main courses", "desserts", "a three-course meal",
     "A menu offers", "a starter and a main course"),
    ("shirts", "pairs of trousers", "pairs of shoes", "an outfit",
     "A wardrobe contains", "a shirt and a pair of trousers"),
    ("colours", "sizes", "patterns", "a design",
     "A product is available in", "a colour and a size"),
)

LETTER_CONTEXTS = (
    ("letters", "a code"),
    ("digits", "a passcode"),
)


def factorial_from(count, taken):
    """Arrangements of `taken` items chosen from `count`, without repeats."""
    total = 1
    for step in range(taken):
        total *= count - step
    return total


def answer_value(p):
    form = p["form"]
    if form == "independent":
        total = 1
        for value in p["choices"]:
            total *= value
        return total
    if form == "no_repeats":
        return factorial_from(p["count"], p["taken"])
    if form == "restricted":
        # The first position is restricted, the rest are filled from what
        # remains.
        return p["first_options"] * factorial_from(p["count"] - 1, p["taken"] - 1)
    # Two cases added: each arranges ALL of its own items, so the second
    # case takes other_count items, not the first case's count. Reusing
    # taken here counted 5 items three at a time, and multiplied through
    # zero whenever the other count was the smaller one.
    first = factorial_from(p["count"], p["count"])
    second = factorial_from(p["other_count"], p["other_count"])
    return first + second


def presentation(p):
    form = p["form"]

    if form == "independent":
        names = MENU_CONTEXTS[p["context"]]
        counts = p["choices"]
        if len(counts) == 2:
            body = "{} {} and {} {}".format(
                counts[0], names[0], counts[1], names[1]
            )
        else:
            body = "{} {}, {} {} and {} {}".format(
                counts[0], names[0], counts[1], names[1], counts[2], names[2]
            )
        choice = names[3] if len(counts) == 3 else names[5]
        return Content(
            "{} {}. How many different ways are there to choose "
            "{}?".format(names[4], body, choice)
        )

    unit, thing = LETTER_CONTEXTS[p["context"]]

    if form == "no_repeats":
        return Content(
            "{} is made from {} different {}, arranged in a row. No {} may "
            "be repeated. How many different codes are possible?".format(
                thing.capitalize(), p["count"], unit, unit[:-1]
            )
        )

    if form == "restricted":
        return Content(
            "{} is made from {} different {}, arranged in a row, with no "
            "repeats. The first place must be one of {} particular {}. "
            "How many different codes are possible?".format(
                thing.capitalize(), p["count"], unit,
                p["first_options"], unit
            )
        )

    return Content(
        "A code uses {} different {} arranged in a row, with no repeats. "
        "A second code uses {} different {} in the same way. "
        "How many codes are possible altogether?".format(
            p["count"], unit, p["other_count"], unit
        )
    )


def answer_for(p):
    value = answer_value(p)
    answer = {"kind": "integer", "value": value}
    return answer, Content(str(value))


class ProductRuleCounting:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng

        if difficulty == 1:
            stages = rng.choice((2, 3))
            for attempt in range(200):
                choices = [rng.randint(2, 6) for _ in range(stages)]
                product = 1
                for value in choices:
                    product *= value
                # Adding instead of multiplying is the misconception, so the
                # two must differ or the question cannot reveal it.
                if product != sum(choices):
                    break
            else:
                raise ValueError("Could not construct distinct totals")
            p = {
                "form": "independent",
                "context": rng.randrange(len(MENU_CONTEXTS)),
                "choices": choices,
            }
        elif difficulty == 2:
            count = rng.randint(4, 7)
            p = {
                "form": "no_repeats",
                "context": rng.randrange(len(LETTER_CONTEXTS)),
                "count": count, "taken": count,
            }
        elif difficulty == 3:
            count = rng.randint(4, 6)
            p = {
                "form": "restricted",
                "context": rng.randrange(len(LETTER_CONTEXTS)),
                "count": count, "taken": count,
                "first_options": rng.randint(2, count - 1),
            }
        else:
            count = rng.randint(3, 5)
            p = {
                "form": "two_cases",
                "context": rng.randrange(len(LETTER_CONTEXTS)),
                "count": count, "taken": count,
                "other_count": rng.choice(
                    [v for v in range(3, 6) if v != count]
                ),
            }

        prompt = presentation(p)
        answer, display = answer_for(p)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=2 if difficulty <= 2 else 3, tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=3),
            parameters=p,
        )
        self.validate(question)
        return question

    def validate(self, q):
        require(q.generator_id == self.info.id, "Generator mismatch")
        require(q.generator_version == self.info.version, "Version mismatch")
        level = q.difficulty
        require(type(level) is int and level in (1, 2, 3, 4), "Invalid level")
        require(q.settings == {}, "Unsupported settings")

        p = q.parameters
        expected = {
            1: "independent", 2: "no_repeats",
            3: "restricted", 4: "two_cases",
        }[level]
        require(p["form"] == expected, "Form does not match difficulty")

        value = q.answer.get("value")
        require(type(value) is int and value > 0, "Count must be positive")
        require(value <= 100000, "Count is too large to be reasonable")

        if p["form"] == "independent":
            require(p["context"] in range(len(MENU_CONTEXTS)), "Unknown context")
            choices = p["choices"]
            require(isinstance(choices, list) and len(choices) in (2, 3),
                    "Expected two or three stages")
            require(all(type(v) is int and 2 <= v <= 6 for v in choices),
                    "Stage sizes outside bounds")
            product = 1
            for entry in choices:
                product *= entry
            require(product != sum(choices),
                    "Product and sum must differ, or the misconception hides")
        else:
            require(p["context"] in range(len(LETTER_CONTEXTS)),
                    "Unknown context")
            require(type(p["count"]) is int, "Invalid count")
            require(p["taken"] == p["count"],
                    "These levels arrange every item")
            if p["form"] == "no_repeats":
                require(4 <= p["count"] <= 7, "Count outside bounds")
            elif p["form"] == "restricted":
                require(4 <= p["count"] <= 6, "Count outside bounds")
                require(2 <= p["first_options"] < p["count"],
                        "Restriction must remove some but not all options")
            else:
                require(3 <= p["count"] <= 5, "Count outside bounds")
                require(3 <= p["other_count"] <= 5, "Other count outside bounds")
                require(p["count"] != p["other_count"],
                        "Two identical cases are one case")

        answer, display = answer_for(p)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Display mismatch")
        require(q.prompt == presentation(p), "Prompt mismatch")
        require(q.visual_assets("questions") == ()
                and q.visual_assets("answers") == (),
                "This family uses no visual assets")
        return True

    def validate_independently(self, q):
        """Count by enumeration instead of by multiplying.

        Building the arrangements and counting them is a genuinely different
        route from applying the product rule, and it fails loudly if the
        rule was applied to the wrong structure.
        """
        from itertools import permutations, product as cartesian

        p = q.parameters
        form = p["form"]
        submitted = q.answer["value"]

        if form == "independent":
            ranges = [range(value) for value in p["choices"]]
            counted = sum(1 for _ in cartesian(*ranges))
        elif form == "no_repeats":
            counted = sum(1 for _ in permutations(range(p["count"])))
        elif form == "restricted":
            # Enumerate every arrangement, then keep those whose first entry
            # is one of the allowed options.
            allowed = set(range(p["first_options"]))
            counted = sum(
                1 for arrangement in permutations(range(p["count"]))
                if arrangement[0] in allowed
            )
        else:
            counted = (
                sum(1 for _ in permutations(range(p["count"])))
                + sum(1 for _ in permutations(range(p["other_count"])))
            )

        require(counted == submitted, "Independent enumeration disagrees")
        return True