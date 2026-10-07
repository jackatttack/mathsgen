"""Formula misconceptions for basic area questions at levels 1-2."""
from fractions import Fraction

from .core import Content, rational_text, rational_tex
from .multiple_choice import RationalCandidate


SUPPORTED_LEVELS = {"geometry.area.basic_shapes": (1, 2)}


def candidate(value, mistake, explanation):
    return RationalCandidate(Fraction(value), mistake, explanation)


def candidates(question):
    if question.difficulty not in SUPPORTED_LEVELS.get(question.generator_id, ()):
        return None
    p = question.parameters
    if p.get("unknown") != "area":
        return None
    base, height = Fraction(p["base"]), Fraction(p["height"])
    if p["shape"] == "triangle":
        return [
            candidate(base * height, "omit_half",
                      "Uses base times height without halving."),
            candidate((base + height) / 2, "add_instead_of_multiply",
                      "Adds the base and height before halving instead of multiplying them."),
            candidate(base * height / 4, "halve_twice",
                      "Halves both base and height before multiplying."),
        ]
    if p["shape"] == "parallelogram":
        return [
            candidate(base * height / 2, "use_triangle_formula",
                      "Halves base times height as if the shape were a triangle."),
            candidate(base + height, "add_dimensions",
                      "Adds the base and perpendicular height instead of multiplying."),
            candidate(2 * (base + height), "use_rectangle_perimeter_formula",
                      "Uses the rectangle perimeter shortcut with base and height instead of an area formula."),
        ]
    if p["shape"] == "trapezium":
        top = Fraction(p["top"])
        return [
            candidate((base + top) * height, "omit_half",
                      "Multiplies the sum of the parallel sides by the height without halving."),
            candidate(base * height / 2, "omit_short_parallel_side",
                      "Uses only the longer parallel side in the halved product."),
            candidate((base + top) / 2, "omit_height",
                      "Finds the average parallel-side length but does not multiply by the height."),
        ]
    return None


def format_candidate(question, entry):
    """All options use the requested square-centimetre unit."""
    return Content(
        rational_text(entry.value) + " cm²",
        rational_tex(entry.value) + r"\ \mathrm{cm}^{2}",
    )