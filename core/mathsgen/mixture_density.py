"""Mixture density and mass, built from exact component masses and volumes.

When two liquids are combined, mass adds and volume adds, but density does
not: the mixture density is total mass over total volume. Averaging the two
densities is the standard misconception and gives a different answer
whenever the volumes differ, which is why every question here uses unequal
volumes. That wrong value is a ready-made distractor once multiple choice
is supported, but this generator does not produce choices.
"""
from fractions import Fraction

from .core import (
    Content, GeneratorInfo, LayoutHint, Question, make_context,
    rational_text, require,
)
from .rounding import decimal_text, terminates


LIQUIDS = (
    ("Liquid A", "Liquid B"),
    ("oil", "water"),
    ("syrup", "juice"),
)

# Densities that stay plausible for liquids and keep the arithmetic exact.
DENSITIES = {
    1: (Fraction(1), Fraction(2), Fraction(4), Fraction(5)),
    2: (Fraction(8, 10), Fraction(12, 10), Fraction(15, 10), Fraction(25, 10)),
    3: (Fraction(8, 10), Fraction(9, 10), Fraction(11, 10), Fraction(13, 10)),
    4: (Fraction(85, 100), Fraction(92, 100), Fraction(105, 100), Fraction(125, 100)),
}

VOLUMES = {
    1: (100, 200, 300, 400, 500),
    2: (100, 150, 200, 250, 300),
    3: (200, 300, 400, 600),
    # Level 4 pairs must total a volume that divides cleanly, so the
    # two-decimal-place densities still give an exact mixture density.
    4: (100, 200, 400, 500, 800),
}


def quantity(value, unit):
    return "{} {}".format(decimal_text(Fraction(value)), unit)


QUANTITY_UNITS = {"mass": "g", "volume": "cm³", "density": "g/cm³"}

# Which two quantities each liquid states. The third follows from
# mass = volume x density, so a question giving mass and density makes the
# student recover the volume before anything can be combined.
GIVEN_PAIRS = (("volume", "density"), ("mass", "volume"), ("mass", "density"))


def component_values(volume, density):
    """All three quantities for one liquid, from its volume and density."""
    volume = Fraction(volume)
    density = Fraction(density)
    return {"volume": volume, "density": density, "mass": volume * density}


def component_text(name, values, given):
    stated = [
        "a {} of {}".format(name_of, quantity(values[name_of], QUANTITY_UNITS[name_of]))
        for name_of in given
    ]
    return "{} has {} and {}".format(name, stated[0], stated[1])


def sentence_case(text):
    return text[0].upper() + text[1:] if text else text


def make_prompt(names, volumes, densities, givens, target):
    parts = [
        component_text(name, component_values(volume, density), tuple(given))
        for name, volume, density, given in zip(names, volumes, densities, givens)
    ]
    # Each component is its own sentence, so each one opens with a capital.
    parts = [sentence_case(part) for part in parts]
    if target == "density":
        question = "The two liquids are mixed. Find the density of the mixture."
    else:
        question = "The two liquids are mixed. Find the total mass of the mixture."
    return Content(". ".join(parts) + ". " + question)


class MixtureQuestion:
    """Shared construction; each target quantity is registered separately."""

    def generate(self, seed, difficulty=1, settings=None):
        context = make_context(self.info, seed, difficulty, settings)
        if context.settings:
            raise ValueError("This generator currently accepts no settings")
        rng = context.rng
        names = rng.choice(LIQUIDS)

        for attempt in range(500):
            densities = list(rng.sample(DENSITIES[difficulty], 2))
            volumes = list(rng.sample(VOLUMES[difficulty], 2))
            masses = [
                Fraction(volume) * density
                for volume, density in zip(volumes, densities)
            ]
            total_mass = sum(masses)
            total_volume = Fraction(sum(volumes))
            mixture_density = total_mass / total_volume
            # Unequal volumes are what make the mixture density differ from
            # the average of the two densities, which is the misconception
            # this family is meant to expose.
            if volumes[0] == volumes[1]:
                continue
            if all(mass.denominator == 1 for mass in masses) and self.acceptable(
                mixture_density, total_mass
            ):
                break
        else:
            raise ValueError("Could not construct a suitable mixture")

        if difficulty == 1:
            # The easiest level states volume and density directly, so the
            # only skill tested is combining. Harder levels withhold one
            # quantity per liquid.
            givens = [list(GIVEN_PAIRS[0]), list(GIVEN_PAIRS[0])]
        else:
            givens = [list(rng.choice(GIVEN_PAIRS)), list(rng.choice(GIVEN_PAIRS))]

        if self.target == "density":
            result = mixture_density
            unit = "g/cm³"
        else:
            result = total_mass
            unit = "g"

        question = Question(
            id=context.identity,
            generator_id=self.info.id,
            generator_version=self.info.version,
            topic=self.info.topic,
            subtopic=self.info.subtopic,
            difficulty=difficulty,
            seed=seed,
            settings=context.settings,
            prompt=make_prompt(names, volumes, densities, givens, self.target),
            answer={
                "kind": "mixture",
                "value": rational_text(result),
                "unit": unit,
                "total_mass": rational_text(total_mass),
                "total_volume": rational_text(total_volume),
            },
            answer_display=Content(quantity(result, unit)),
            worked_solution=(),
            marks=3 if difficulty <= 2 else 4,
            tags=self.info.tags,
            layout_hint=LayoutHint(working_lines=6),
            parameters={
                "names": list(names),
                "volumes": volumes,
                "densities": [rational_text(value) for value in densities],
                "givens": givens,
            },
        )
        self.validate(question)
        return question

    def validate(self, question):
        require(question.generator_id == self.info.id, "Generator mismatch")
        require(question.generator_version == self.info.version, "Version mismatch")
        level = question.difficulty
        require(level in DENSITIES, "Invalid difficulty")
        names = tuple(question.parameters["names"])
        volumes = question.parameters["volumes"]
        densities = [Fraction(value) for value in question.parameters["densities"]]
        require(names in LIQUIDS, "Unknown liquid pair")
        require(len(volumes) == len(densities) == 2, "Expected two components")
        require(all(type(volume) is int and volume > 0 for volume in volumes),
                "Expected positive integer volumes")
        require(all(volume in VOLUMES[level] for volume in volumes),
                "Volume outside difficulty rules")
        require(all(density in DENSITIES[level] for density in densities),
                "Density outside difficulty rules")
        require(densities[0] != densities[1], "Expected two different densities")
        require(volumes[0] != volumes[1],
                "Equal volumes would make the mixture density equal the average")

        givens = question.parameters["givens"]
        require(len(givens) == 2, "Expected a stated pair for each liquid")
        require(all(tuple(given) in GIVEN_PAIRS for given in givens),
                "A liquid states a pair that does not determine the third quantity")
        if level == 1:
            require(all(tuple(given) == GIVEN_PAIRS[0] for given in givens),
                    "The first level states volume and density directly")

        masses = [Fraction(volume) * density for volume, density in zip(volumes, densities)]
        require(all(mass.denominator == 1 for mass in masses),
                "Each component mass must be exact")
        total_mass = sum(masses)
        total_volume = Fraction(sum(volumes))
        mixture_density = total_mass / total_volume
        average = (densities[0] + densities[1]) / 2
        require(mixture_density != average,
                "The mixture density must differ from the average of the densities")

        result = mixture_density if self.target == "density" else total_mass
        unit = "g/cm³" if self.target == "density" else "g"
        require(self.acceptable(mixture_density, total_mass), "Result outside bounds")
        require(question.answer["value"] == rational_text(result), "Incorrect result")
        require(question.answer["unit"] == unit, "Unexpected unit")
        require(question.answer["total_mass"] == rational_text(total_mass),
                "Incorrect total mass")
        require(question.answer["total_volume"] == rational_text(total_volume),
                "Incorrect total volume")
        require(question.prompt == make_prompt(
            names, volumes, densities, givens, self.target,
        ), "Prompt mismatch")
        require(question.answer_display == Content(quantity(result, unit)),
                "Displayed answer mismatch")
        return True

    def validate_independently(self, question):
        """Recompute from the component quantities with exact rationals.

        This also confirms the answer is not the average of the two
        densities, so a question solved by the common misconception would
        be rejected rather than quietly accepted.
        """
        import sympy

        # Rebuild each liquid from only the two quantities the question
        # actually states, which also confirms that stated pair is enough to
        # recover the third.
        masses = []
        volumes = []
        for given, volume, density in zip(
            question.parameters["givens"],
            question.parameters["volumes"],
            question.parameters["densities"],
        ):
            full = {
                "volume": sympy.Integer(volume),
                "density": sympy.Rational(density),
            }
            full["mass"] = full["volume"] * full["density"]
            stated = {name: full[name] for name in given}
            if "volume" in stated and "density" in stated:
                recovered_volume = stated["volume"]
                recovered_mass = stated["volume"] * stated["density"]
            elif "mass" in stated and "volume" in stated:
                recovered_volume = stated["volume"]
                recovered_mass = stated["mass"]
            else:
                require(stated["density"] != 0, "A stated density cannot be zero")
                recovered_volume = stated["mass"] / stated["density"]
                recovered_mass = stated["mass"]
            masses.append(recovered_mass)
            volumes.append(recovered_volume)

        total_mass = sum(masses)
        total_volume = sum(volumes)
        mixture_density = sympy.Rational(total_mass, total_volume)
        densities = [
            sympy.Rational(value) for value in question.parameters["densities"]
        ]

        expected = mixture_density if self.target == "density" else total_mass
        require(sympy.Rational(question.answer["value"]) == expected,
                "Independent mixture result disagrees")
        require(sympy.Rational(question.answer["total_mass"]) == total_mass,
                "Independent total mass disagrees")
        if self.target == "density":
            average = (densities[0] + densities[1]) / 2
            require(expected != average,
                    "The answer coincides with the average of the densities")
        return True

    @staticmethod
    def acceptable(mixture_density, total_mass):
        """The mixture density is a quotient, so it must terminate exactly.

        Total mass over total volume recurs whenever the total volume has a
        prime factor other than 2 or 5 that the mass does not cancel, and a
        recurring density cannot be stated exactly in the answer.
        """
        return (terminates(mixture_density)
                and Fraction(1, 2) <= mixture_density <= 5
                and total_mass <= 4000)


class MixtureDensity(MixtureQuestion):
    target = "density"
    info = GeneratorInfo(
        id="number.compound.mixture_density", version=2, topic="number",
        subtopic="compound_measures", title="Find the density of a mixture",
        difficulty_descriptions={
            1: "Volume and density stated for both liquids.",
            2: "Densities to one decimal place; each liquid states any two quantities.",
            3: "Densities close together; each liquid states any two quantities.",
            4: "Densities to two decimal places; each liquid states any two quantities.",
        },
        tags=("density", "compound_measures", "mixture"),
    )


class MixtureMass(MixtureQuestion):
    target = "mass"
    info = GeneratorInfo(
        id="number.compound.mixture_mass", version=2, topic="number",
        subtopic="compound_measures", title="Find the total mass of a mixture",
        difficulty_descriptions={
            1: "Volume and density stated for both liquids.",
            2: "Densities to one decimal place; each liquid states any two quantities.",
            3: "Densities close together; each liquid states any two quantities.",
            4: "Densities to two decimal places; each liquid states any two quantities.",
        },
        tags=("density", "compound_measures", "mixture", "mass"),
    )