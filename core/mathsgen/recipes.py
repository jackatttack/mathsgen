"""Recipe scaling, ending in a limiting-ingredient problem.

Levels 1 to 3 scale a recipe up, down, and to a non-integer multiple. Level
4 is a genuine problem: given what is actually in the cupboard, how many
batches can be made? Every ingredient permits some number of batches and
the smallest of those decides the answer, so a student who scales by the
first ingredient they read gets it wrong.

All quantities are exact rationals and every stated amount terminates as a
decimal, so no question needs rounding.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .rounding import decimal_text, terminates


INFO = GeneratorInfo(
    id="ratio.proportion.recipes", version=1,
    topic="ratio", subtopic="recipes",
    title="Scaling recipes",
    difficulty_descriptions={
        1: "Scale a recipe up to serve more people.",
        2: "Scale a recipe to a number of servings that is not a multiple.",
        3: "Work backwards from one ingredient to the number of servings.",
        4: "Find how many batches the available ingredients allow.",
    },
    tags=("ratio", "proportion", "recipes", "problem solving"),
)

# --- Editable recipe table ------------------------------------------------
# Each recipe states its serving count and its ingredients as
# (name, amount, unit). Amounts are for the stated number of servings.
# "potatoes" is measured in grams but is grammatically plural, so the unit
# alone cannot decide between "how much ... is" and "how many ... are".
# Each ingredient states its own verb form instead.
PLURAL_INGREDIENTS = {"potatoes", "eggs", "onions"}

RECIPES = (
    ("pancakes", 4, (
        ("flour", 200, "g"), ("milk", 300, "ml"), ("eggs", 2, ""),
    )),
    ("soup", 6, (
        ("potatoes", 900, "g"), ("stock", 1200, "ml"), ("onions", 3, ""),
    )),
    ("biscuits", 12, (
        ("butter", 150, "g"), ("sugar", 100, "g"), ("flour", 225, "g"),
    )),
)


def quantity(amount, unit):
    written = decimal_text(Fraction(amount))
    return "{} {}".format(written, unit) if unit else written


def ingredient_list(recipe):
    return ", ".join(
        quantity(amount, unit) + " of " + name if unit
        else "{} {}".format(amount, name)
        for name, amount, unit in recipe[2]
    )


def scaled_amount(recipe, index, servings):
    """One ingredient's amount for the requested number of servings."""
    _, base_servings, ingredients = recipe
    _, amount, _ = ingredients[index]
    return Fraction(amount) * Fraction(servings, base_servings)


def batches_possible(p):
    """The largest whole number of batches the available amounts allow.

    Each ingredient permits its own number of batches; the smallest of
    those is the limit, which is the whole point of the question.
    """
    recipe = RECIPES[p["recipe"]]
    available = p["available"]
    limits = []
    for index, amount in enumerate(available):
        _, needed, _ = recipe[2][index]
        limits.append(Fraction(amount) / needed)
    smallest = min(limits)
    return int(smallest), limits


def answer_value(p):
    recipe = RECIPES[p["recipe"]]
    form = p["form"]

    if form in ("scale_up", "scale_part"):
        return scaled_amount(recipe, p["ingredient"], p["servings"])
    if form == "backwards":
        # How many servings the stated amount of one ingredient supports.
        _, base_servings, ingredients = recipe
        _, needed, _ = ingredients[p["ingredient"]]
        return Fraction(p["amount"]) * base_servings / needed
    return Fraction(batches_possible(p)[0])


def presentation(p):
    recipe = RECIPES[p["recipe"]]
    name, base_servings, ingredients = recipe
    listed = ingredient_list(recipe)
    form = p["form"]

    if form in ("scale_up", "scale_part"):
        ingredient_name, _, unit = ingredients[p["ingredient"]]
        plural = ingredient_name in PLURAL_INGREDIENTS
        question_word = "How many" if plural else "How much"
        verb = "are" if plural else "is"
        return Content(
            "A recipe for {} serves {} people and uses {}. "
            "{} {} {} needed to serve {} people?".format(
                name, base_servings, listed,
                question_word, ingredient_name, verb, p["servings"]
            )
        )

    if form == "backwards":
        ingredient_name, _, unit = ingredients[p["ingredient"]]
        return Content(
            "A recipe for {} serves {} people and uses {}. "
            "A cook has {} of {} and plenty of everything else. "
            "How many people can be served?".format(
                name, base_servings, listed,
                quantity(p["amount"], unit), ingredient_name
            )
        )

    stated = ", ".join(
        quantity(amount, ingredients[index][2]) + " of " + ingredients[index][0]
        if ingredients[index][2]
        else "{} {}".format(decimal_text(Fraction(amount)), ingredients[index][0])
        for index, amount in enumerate(p["available"])
    )
    return Content(
        "One batch of {} serves {} people and uses {}. "
        "A cook has {}. How many complete batches can be made?".format(
            name, base_servings, listed, stated
        )
    )


def answer_for(p):
    value = answer_value(p)
    recipe = RECIPES[p["recipe"]]
    form = p["form"]

    if form == "batches":
        answer = {"kind": "integer", "value": int(value)}
        return answer, Content("{} batches".format(int(value)))
    if form == "backwards":
        answer = {"kind": "integer", "value": int(value)}
        return answer, Content("{} people".format(int(value)))

    _, _, ingredients = recipe
    _, _, unit = ingredients[p["ingredient"]]
    answer = {
        "kind": "quantity", "value": rational_text(value), "unit": unit,
    }
    return answer, Content(quantity(value, unit))


class Recipes:
    info = INFO

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        require(not context.settings, "This generator accepts no settings")
        rng = context.rng
        recipe_index = rng.randrange(len(RECIPES))
        recipe = RECIPES[recipe_index]
        _, base_servings, ingredients = recipe

        if difficulty == 1:
            multiple = rng.randint(2, 4)
            p = {
                "form": "scale_up", "recipe": recipe_index,
                "ingredient": rng.randrange(len(ingredients)),
                "servings": base_servings * multiple,
            }
        elif difficulty == 2:
            # Countable ingredients are excluded here: a non-whole multiple
            # would ask for half an onion, which is not a sensible quantity
            # even though the arithmetic is exact.
            measured = [
                index for index, (_, _, unit) in enumerate(ingredients) if unit
            ]
            for attempt in range(200):
                servings = rng.randint(2, 3 * base_servings)
                if servings % base_servings == 0:
                    continue
                candidate = {
                    "form": "scale_part", "recipe": recipe_index,
                    "ingredient": rng.choice(measured),
                    "servings": servings,
                }
                value = answer_value(candidate)
                if value > 0 and terminates(value):
                    p = candidate
                    break
            else:
                raise ValueError("Could not construct a scalable serving count")
        elif difficulty == 3:
            index = rng.randrange(len(ingredients))
            _, needed, _ = ingredients[index]
            multiple = rng.randint(2, 5)
            p = {
                "form": "backwards", "recipe": recipe_index,
                "ingredient": index,
                "amount": rational_text(Fraction(needed) * multiple),
            }
        else:
            # One ingredient is deliberately the limiting one, and it leaves
            # a remainder so the leftover is visible.
            limiting = rng.randrange(len(ingredients))
            batches = rng.randint(2, 5)
            available = []
            for index, (_, needed, _) in enumerate(ingredients):
                if index == limiting:
                    extra = Fraction(needed, 2)
                    available.append(rational_text(
                        Fraction(needed) * batches + extra
                    ))
                else:
                    available.append(rational_text(
                        Fraction(needed) * (batches + rng.randint(1, 3))
                    ))
            p = {
                "form": "batches", "recipe": recipe_index,
                "available": available,
            }

        prompt = presentation(p)
        answer, display = answer_for(p)
        question = Question(
            id=context.identity, generator_id=self.info.id,
            generator_version=self.info.version, topic=self.info.topic,
            subtopic=self.info.subtopic, difficulty=difficulty, seed=seed,
            settings=context.settings, prompt=prompt, answer=answer,
            answer_display=display, worked_solution=(),
            marks=2 if difficulty <= 2 else 4 if difficulty == 4 else 3,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=3 if difficulty <= 2 else 5),
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
        require(p["recipe"] in range(len(RECIPES)), "Unknown recipe")
        recipe = RECIPES[p["recipe"]]
        _, base_servings, ingredients = recipe

        expected = {
            1: "scale_up", 2: "scale_part", 3: "backwards", 4: "batches",
        }[level]
        require(p["form"] == expected, "Form does not match difficulty")

        if level in (1, 2):
            require(p["ingredient"] in range(len(ingredients)),
                    "Unknown ingredient")
            servings = p["servings"]
            require(type(servings) is int and servings > 0,
                    "Servings must be positive")
            if level == 1:
                require(servings % base_servings == 0,
                        "Level 1 scales by a whole multiple")
                require(servings > base_servings, "Level 1 scales up")
            else:
                require(servings % base_servings != 0,
                        "Level 2 should not be a whole multiple")
                _, _, unit = ingredients[p["ingredient"]]
                require(unit, "A countable ingredient cannot take a part share")
            value = answer_value(p)
            require(value > 0 and terminates(value),
                    "Scaled amount is not an exact decimal")
        elif level == 3:
            require(p["ingredient"] in range(len(ingredients)),
                    "Unknown ingredient")
            amount = Fraction(p["amount"])
            require(p["amount"] == rational_text(amount), "Non-canonical amount")
            require(amount > 0, "Amount must be positive")
            value = answer_value(p)
            require(value == int(value), "Servings should be whole")
            require(value > base_servings, "The question should scale up")
        else:
            available = p["available"]
            require(isinstance(available, list)
                    and len(available) == len(ingredients),
                    "Every ingredient needs an available amount")
            amounts = [Fraction(value) for value in available]
            require(available == [rational_text(v) for v in amounts],
                    "Non-canonical available amounts")
            require(all(value > 0 for value in amounts),
                    "Available amounts must be positive")

            batches, limits = batches_possible(p)
            require(batches >= 2, "There should be at least two batches")
            smallest = min(limits)
            require(sum(1 for value in limits if value == smallest) == 1,
                    "Exactly one ingredient should be the limiting one")
            require(smallest != int(smallest),
                    "The limiting amount should leave a remainder")

        answer, display = answer_for(p)
        require(q.answer == answer, "Incorrect answer")
        require(q.answer_display == display, "Display mismatch")
        require(q.prompt == presentation(p), "Prompt mismatch")
        require(q.visual_assets("questions") == ()
                and q.visual_assets("answers") == (),
                "This family uses no visual assets")
        return True

    def validate_independently(self, q):
        """Scale by unit quantities, or count batches one at a time.

        Working out the amount for ONE serving and multiplying up is a
        different route from scaling by a ratio, and for the batch problem
        the check subtracts ingredients batch by batch until something runs
        out, which is what the question describes rather than what it
        computes.
        """
        from fractions import Fraction as F

        p = q.parameters
        recipe = RECIPES[p["recipe"]]
        _, base_servings, ingredients = recipe
        form = p["form"]

        if form in ("scale_up", "scale_part"):
            _, needed, _ = ingredients[p["ingredient"]]
            per_serving = F(needed, base_servings)
            expected = per_serving * p["servings"]
            require(F(q.answer["value"]) == expected,
                    "Independent per-serving scaling disagrees")
            return True

        if form == "backwards":
            _, needed, _ = ingredients[p["ingredient"]]
            per_serving = F(needed, base_servings)
            expected = F(p["amount"]) / per_serving
            require(q.answer["value"] == expected,
                    "Independent per-serving count disagrees")
            return True

        remaining = [F(value) for value in p["available"]]
        made = 0
        while True:
            if any(remaining[index] < needed
                   for index, (_, needed, _) in enumerate(ingredients)):
                break
            for index, (_, needed, _) in enumerate(ingredients):
                remaining[index] -= needed
            made += 1
            require(made <= 50, "Batch count did not terminate")

        require(q.answer["value"] == made,
                "Independent batch-by-batch count disagrees")
        return True