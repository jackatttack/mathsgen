"""Two-stage frequency trees with calibrated missing-count problems.

The four terminal groups are disjoint and exhaustive. Every parent count
equals the sum of its two children. Student diagrams omit only counts needed
for the question; teacher diagrams show all counts.
"""
from fractions import Fraction

from .core import Content, GeneratorInfo, rational_text, rational_tex, require
from .family import GeneratorFamily
from .visuals import scene


CONTEXTS = (
    {
        "intro": "Students at a school were asked how they travel to school.",
        "first": ("Bus", "Walk"),
        "second": ("Year 10", "Year 11"),
        "noun": "students",
    },
    {
        "intro": "Members of a leisure centre were asked about their visits.",
        "first": ("Weekday", "Weekend"),
        "second": ("Adult", "Child"),
        "noun": "members",
    },
    {
        "intro": "Visitors to a museum were asked about their tickets.",
        "first": ("Online", "At the door"),
        "second": ("Adult", "Child"),
        "noun": "visitors",
    },
)

# Circles are centred at each count. Branches meet their circumferences,
# rather than running underneath the numbers.
ROOT = (24, 160)
FIRST_A = (124, 240)
FIRST_B = (124, 80)
ENDS = ((286, 285), (286, 195), (286, 125), (286, 35))
RADIUS = 15
CIRCLE_SIDES = 32

COUNT_POSITIONS = {
    "total": ROOT,
    "a": FIRST_A,
    "b": FIRST_B,
    "a1": ENDS[0],
    "a2": ENDS[1],
    "b1": ENDS[2],
    "b2": ENDS[3],
}
FIRST_LABEL_POSITIONS = ((65, 224), (65, 96))
SECOND_LABEL_POSITIONS = (
    (203, 283), (203, 177), (203, 143), (203, 37)
)
ALL_COUNTS = ("total", "a", "b", "a1", "a2", "b1", "b2")


def counts(p):
    a1, a2, b1, b2 = (p[key] for key in ("a1", "a2", "b1", "b2"))
    a, b = a1 + a2, b1 + b2
    return {
        "a": a, "b": b,
        "a1": a1, "a2": a2, "b1": b1, "b2": b2,
        "total": a + b,
    }


def hidden_for(level, p):
    if level == 1:
        return (p["missing"],)
    if level == 2:
        return ("a", "a1")
    if level == 3:
        return (p["missing"],)
    return ("a", "a2")


def circle_points(centre):
    """A closed, 32-sided outline rendered as a near-perfect circle."""
    import math

    x, y = centre
    return [
        [
            round(x + RADIUS * math.cos(2 * math.pi * i / CIRCLE_SIDES), 4),
            round(y + RADIUS * math.sin(2 * math.pi * i / CIRCLE_SIDES), 4),
        ]
        for i in range(CIRCLE_SIDES)
    ]


def trimmed_branch(start, end):
    """Connect the boundaries of two count circles."""
    import math

    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    return [
        [start[0] + RADIUS * ux, start[1] + RADIUS * uy],
        [end[0] - RADIUS * ux, end[1] - RADIUS * uy],
    ]


def diagram(p, level, student):
    ctx = CONTEXTS[p["context"]]
    values = counts(p)
    hidden = set(hidden_for(level, p)) if student else set()
    nodes = []

    for start, end in (
        (ROOT, FIRST_A), (ROOT, FIRST_B),
        (FIRST_A, ENDS[0]), (FIRST_A, ENDS[1]),
        (FIRST_B, ENDS[2]), (FIRST_B, ENDS[3]),
    ):
        nodes.append({
            "type": "line",
            "points": trimmed_branch(start, end),
        })

    for name, centre in COUNT_POSITIONS.items():
        nodes.append({
            "type": "polygon",
            "points": circle_points(centre),
            "shade": False,
        })
        nodes.append({
            "type": "label",
            "point": list(centre),
            "text": "" if name in hidden else str(values[name]),
        })

    for label, position in zip(ctx["first"], FIRST_LABEL_POSITIONS):
        nodes.append({
            "type": "label",
            "point": list(position),
            "text": label,
        })

    for label, position in zip(
        (ctx["second"][0], ctx["second"][1],
         ctx["second"][0], ctx["second"][1]),
        SECOND_LABEL_POSITIONS,
    ):
        nodes.append({
            "type": "label",
            "point": list(position),
            "text": label,
        })

    return scene(nodes, height=320, caption="")


def event_description(p, key):
    ctx = CONTEXTS[p["context"]]
    first = ctx["first"][0 if key.startswith("a") else 1]
    second = ctx["second"][0 if key.endswith("1") else 1]
    return "{} and {}".format(first.lower(), second.lower())


class FrequencyTrees(GeneratorFamily):
    info = GeneratorInfo(
        id="probability.frequency.trees",
        version=1,
        topic="probability",
        subtopic="frequency_trees",
        title="Frequency tree diagrams",
        difficulty_descriptions={
            1: "Complete one missing terminal count using subtraction.",
            2: "Find a missing branch total, then use it to find a terminal count.",
            3: "Complete a missing count and calculate a probability from the whole group.",
            4: "Use a conditional fraction to recover a branch total, then find a probability with a different denominator.",
        },
        tags=("probability", "frequency_trees", "conditional_probability"),
    )

    keys = {
        level: (
            {"context", "a1", "a2", "b1", "b2", "missing"}
            if level in (1, 3)
            else {"context", "a1", "a2", "b1", "b2"}
        )
        for level in (1, 2, 3, 4)
    }

    def build(self, level, rng):
        for _ in range(500):
            p = {
                "context": rng.randrange(len(CONTEXTS)),
                "a1": rng.randint(8, 45),
                "a2": rng.randint(8, 45),
                "b1": rng.randint(8, 45),
                "b2": rng.randint(8, 45),
            }
            if level in (1, 3):
                p["missing"] = rng.choice(("a1", "a2", "b1", "b2"))
            if level == 4:
                # Keep the given conditional fraction nontrivial.
                fraction = Fraction(p["a1"], p["a1"] + p["a2"])
                if fraction in (Fraction(1, 2), Fraction(1, 3),
                                Fraction(2, 3), Fraction(1, 4),
                                Fraction(3, 4)):
                    continue
            self.check_rules(p, level)
            return p
        raise ValueError("Could not build a frequency-tree question")

    def check_rules(self, p, level):
        require(type(p["context"]) is int
                and 0 <= p["context"] < len(CONTEXTS), "Invalid context")
        for key in ("a1", "a2", "b1", "b2"):
            require(type(p[key]) is int and 8 <= p[key] <= 45,
                    "Terminal count outside bounds")
        if level in (1, 3):
            require(p["missing"] in ("a1", "a2", "b1", "b2"),
                    "Invalid missing terminal")
        values = counts(p)
        require(values["total"] <= 180, "Total outside bounds")
        if level == 4:
            fraction = Fraction(p["a1"], values["a"])
            require(fraction not in (
                Fraction(1, 2), Fraction(1, 3), Fraction(2, 3),
                Fraction(1, 4), Fraction(3, 4),
            ), "Conditional fraction is too simple for level 4")

    def parts(self, p, level):
        ctx = CONTEXTS[p["context"]]
        values = counts(p)
        intro = ctx["intro"] + " The frequency tree shows the results. "
        if level == 1:
            instruction = (
                "There are {} {} altogether. "
                "Complete the missing count on the tree."
            ).format(values["total"], ctx["noun"])
            answer_value = values[p["missing"]]
            answer = {"kind": "integer", "value": answer_value}
            answer_display = Content(str(answer_value))
        elif level == 2:
            instruction = (
                "There are {} {} altogether. "
                "Complete both missing counts on the tree."
            ).format(values["total"], ctx["noun"])
            answer = {
                "kind": "table_completion",
                "values": [
                    ["a", values["a"]],
                    ["a1", values["a1"]],
                ],
            }
            answer_display = Content(
                "{}: {}; {} and {}: {}".format(
                    ctx["first"][0], values["a"],
                    ctx["first"][0], ctx["second"][0], values["a1"],
                )
            )
        elif level == 3:
            target = p["missing"]
            probability = Fraction(values[target], values["total"])
            instruction = (
                "There are {} {} altogether. Complete the missing count "
                "on the tree. One {} is chosen at random. "
                "Find the probability that the {} is in the "
                "'{}' group. Give your answer as a fraction "
                "in its simplest form."
            ).format(
                values["total"], ctx["noun"], ctx["noun"][:-1]
                if ctx["noun"].endswith("s") else ctx["noun"],
                ctx["noun"][:-1] if ctx["noun"].endswith("s") else ctx["noun"],
                event_description(p, target),
            )
            answer = {
                "kind": "rational",
                "value": rational_text(probability),
            }
            answer_display = Content(
                rational_text(probability), rational_tex(probability)
            )
        else:
            conditional = Fraction(values["a1"], values["a"])
            target_probability = Fraction(values["b1"], values["total"])
            instruction = (
                "Complete the two missing counts on the tree. "
                "Of the {} who are in the '{}' group, {} are in the "
                "'{}' group. Use this information to find the total "
                "number of {}. One {} is then chosen at random. "
                "Find the probability that the {} is in the "
                "'{}' group. Give your answer as a fraction "
                "in its simplest form."
            ).format(
                ctx["noun"], ctx["first"][0],
                rational_text(conditional), ctx["second"][0],
                ctx["noun"],
                ctx["noun"][:-1] if ctx["noun"].endswith("s") else ctx["noun"],
                ctx["noun"][:-1] if ctx["noun"].endswith("s") else ctx["noun"],
                event_description(p, "b1"),
            )
            answer = {
                "kind": "rational",
                "value": rational_text(target_probability),
            }
            answer_display = Content(
                rational_text(target_probability),
                rational_tex(target_probability),
            )

        return {
            "prompt": Content(intro + instruction),
            "question_visuals": [diagram(p, level, student=True)],
            "answer_visuals": [diagram(p, level, student=False)],
            "answer": answer,
            "answer_display": answer_display,
            "marks": {1: 1, 2: 2, 3: 3, 4: 5}[level],
            "working_lines": {1: 2, 2: 3, 3: 4, 4: 6}[level],
        }

    def validate_independently(self, question):
        """Solve the visible count equations without using counts()."""
        import sympy

        p, level = question.parameters, question.difficulty
        leaves = {key: sympy.Integer(p[key])
                  for key in ("a1", "a2", "b1", "b2")}
        a = leaves["a1"] + leaves["a2"]
        b = leaves["b1"] + leaves["b2"]
        total = a + b

        if level == 1:
            missing = p["missing"]
            parent = a if missing.startswith("a") else b
            sibling = missing[0] + ("2" if missing.endswith("1") else "1")
            expected = parent - leaves[sibling]
            require(expected == question.answer["value"],
                    "Independent single-count check failed")

        elif level == 2:
            recovered_a = total - b
            recovered_a1 = recovered_a - leaves["a2"]
            require(
                question.answer["values"] == [
                    ["a", int(recovered_a)],
                    ["a1", int(recovered_a1)],
                ],
                "Independent linked-count check failed",
            )

        elif level == 3:
            missing = p["missing"]
            parent = a if missing.startswith("a") else b
            sibling = missing[0] + ("2" if missing.endswith("1") else "1")
            recovered = parent - leaves[sibling]
            expected = sympy.Rational(recovered, total)
            require(
                expected == sympy.Rational(question.answer["value"]),
                "Independent probability check failed",
            )

        else:
            conditional = sympy.Rational(leaves["a1"], a)
            recovered_a = leaves["a1"] / conditional
            recovered_a2 = recovered_a - leaves["a1"]
            recovered_total = recovered_a + b
            require(recovered_a2 == leaves["a2"],
                    "Conditional fraction does not recover the hidden count")
            expected = sympy.Rational(leaves["b1"], recovered_total)
            require(
                expected == sympy.Rational(question.answer["value"]),
                "Independent reverse probability check failed",
            )

        return True