"""Drill sheets: a progression for one skill per exercise, like a textbook.

Each exercise (block) names one generator and runs in stages:
- one drill stage per chosen level, easiest first: many short items;
- an optional final apply stage: worded and diagram problems on the same
  skill, given room to work.

Diagram skills (DIAGRAM_SKILLS) drill with their diagrams: each item is a
small drawing under a shared instruction. Every diagram must draw at
DRILL_DIAGRAM_WIDTH; a question whose labels collide at that size is
skipped while building, so rendering never meets it.

Displayed prompts are never repeated anywhere on the sheet. If a stage
cannot be filled, a ValueError explains why; a sheet never silently has
fewer items than requested.

The specification records every exercise's stages, so a renderer can
regroup the flat question list in order with drill_stages().
"""
import hashlib

from .core import canonical_json, require
from .worksheets import Worksheet, derived_seed


# ------------------------------------------------------------ editable policy

MAXIMUM_ITEMS_PER_STAGE = 60
MAXIMUM_APPLY_ITEMS = 12
DEFAULT_APPLY_ITEMS = 6
ATTEMPTS_PER_ITEM = 100
# Try this many times for the preferred kind of item before accepting another.
PREFERRED_ATTEMPTS = 40
# Diagrams in drill grids draw at this width (two columns on A4).
DRILL_DIAGRAM_WIDTH = 230
BUILDER_VERSION = 8

# Skills offered in drill mode, with the levels that suit a dense grid.
# Chosen from dev/probes/probe_drill_candidates.py and probe_drill_visuals.py;
# tests/smoke_drill.py builds and renders every entry. Edit freely, then rerun it.
DRILL_SKILLS = {
    "algebra.sequences.linear_nth": (1, 2, 3, 4),
    "algebra.sequences.quadratic_nth": (1, 2, 3, 4),
    "algebra.sequences.geometric": (1, 2, 3, 4),
    "algebra.expressions.like_terms": (1, 2, 3, 4),
    "algebra.expanding.double_brackets": (1, 2, 3, 4),
    "algebra.factorising.common_factor": (1, 2, 3, 4),
    "algebra.factorising.difference_of_squares": (1, 2, 3, 4),
    "algebra.substitution.values": (1, 2, 3, 4),
    "algebra.linear.two_sided": (1, 2, 3, 4),
    "algebra.simultaneous.linear": (1, 2, 3, 4),
    "algebra.inequalities.linear": (1, 2, 3, 4),
    "algebra.quadratic.factorisable_monic": (1, 2, 3, 4),
    "algebra.quadratic.factorisable_non_monic": (1, 2, 3, 4),
    "algebra.quadratic.formula": (1, 2, 3, 4),
    "algebra.quadratic.completing_square": (1, 2, 3, 4),
    "algebra.quadratic.fractional_equation": (1, 2, 3, 4),
    "algebra.functions.evaluate": (1, 2, 3, 4),
    "algebra.fractions.manipulation": (1, 2, 3, 4),
    "algebra.graphs.circle_equations": (1, 2, 3, 4),
    "algebra.rearranging.changing_subject": (1, 2),
    "number.operations.order": (1, 2, 3, 4),
    "number.integers.negatives": (1, 2, 3, 4),
    "number.place_value.decimals": (1, 2, 3, 4),
    "number.fractions.addition": (1, 2, 3, 4),
    "number.fractions.multiplication": (1, 2, 3, 4),
    "number.fractions.division": (1, 2, 3, 4),
    "number.fractions.mixed_numbers": (1, 2, 3, 4),
    "number.fractions.of_amount": (1, 2, 3, 4),
    "number.fractions.recurring_decimals": (1, 2, 3, 4),
    "number.fdp.fraction_to_decimal": (1, 2, 3, 4),
    "number.percentages.of_amount": (1, 2, 3, 4),
    "number.percentages.multiplier": (1, 2, 3, 4),
    "number.percentages.interpret_multiplier": (1, 2, 3, 4),
    "number.percentages.reverse": (1, 2, 3, 4),
    "number.rounding.decimal_places": (1, 2, 3, 4),
    "number.standard_form.calculations": (1, 2, 3, 4),
    "number.surds.manipulation": (1, 2, 3, 4),
    "number.indices.rules": (1, 2, 3, 4),
    "number.primes.factorisation": (1, 2, 3, 4),
    "number.units.area_volume": (1, 2, 3, 4),
    "ratio.simplifying": (1, 2, 3, 4),
    "ratio.compound_measures.rates": (1, 2, 3),
    "ratio.money.problems": (1,),
    "geometry.trigonometry.exact_values": (1, 2, 3, 4),
    "geometry.vectors.column": (1, 2, 3, 4),
    # Diagram skills: a shared instruction, then one small diagram per item.
    "geometry.trigonometry.right_angled": (1, 2, 3, 4),
    "geometry.pythagoras.lengths": (1, 2, 3),
    "geometry.angles.basic_facts": (1, 2, 3, 4),
    "geometry.angles.triangle": (1, 2, 3, 4),
    "geometry.angles.parallel_lines": (1, 2, 3, 4),
    "geometry.area.basic_shapes": (1, 2, 3, 4),
    "geometry.area.compound_rectangles": (1, 2, 3, 4),
    "geometry.circles.measures": (1, 2, 3, 4),
    "geometry.circles.sectors": (1, 2, 3, 4),
    "geometry.volume.prisms": (1, 2, 3, 4),
    "geometry.surface_area.prisms": (1, 2, 3, 4),
    "geometry.angles.polygons": (1, 2, 3),
    "geometry.trigonometry.sine_rule": (1, 2, 3),
    "geometry.trigonometry.cosine_rule": (1, 2),
    "geometry.similarity.scale_factors": (1, 3),
    "geometry.circle_theorems.centre_angle": (1, 2, 3, 4),
    "geometry.circle_theorems.same_segment": (1, 2, 3, 4),
    "geometry.circle_theorems.cyclic_quadrilateral": (1, 2, 3, 4),
    "geometry.circle_theorems.tangents": (1, 2, 3, 4),
    "geometry.circle_theorems.alternate_segment": (1, 2, 3, 4),
    "geometry.circle_theorems.multi_step": (1, 2, 3),
    "algebra.graphs.straight_lines": (1, 2, 3),
}
DIAGRAM_SKILLS = frozenset({
    "geometry.trigonometry.right_angled",
    "geometry.pythagoras.lengths",
    "geometry.angles.basic_facts",
    "geometry.angles.triangle",
    "geometry.angles.parallel_lines",
    "geometry.area.basic_shapes",
    "geometry.area.compound_rectangles",
    "geometry.circles.measures",
    "geometry.circles.sectors",
    "geometry.volume.prisms",
    "geometry.surface_area.prisms",
    "geometry.angles.polygons",
    "geometry.trigonometry.sine_rule",
    "geometry.trigonometry.cosine_rule",
    "geometry.similarity.scale_factors",
    "geometry.circle_theorems.centre_angle",
    "geometry.circle_theorems.same_segment",
    "geometry.circle_theorems.cyclic_quadrilateral",
    "geometry.circle_theorems.tangents",
    "geometry.circle_theorems.alternate_segment",
    "geometry.circle_theorems.multi_step",
    "algebra.graphs.straight_lines",
})
# Dispatcher skills whose levels drill as one part per route (1a, 1b ...),
# so each part's items share a form and an instruction. Opt-in: splitting
# a skill whose forms are all prose only fragments the sheet.
SPLIT_ROUTE_SKILLS = frozenset({
    "algebra.graphs.straight_lines",
})
# A level splits only when every part gets at least this many items.
MINIMUM_PART_ITEMS = 3

# Diagram-only stages: one instruction line for the stage, then each item
# is just its diagram, no words. Only for levels whose diagrams carry every
# given value (area level 4 states the area in words, so it is not here).
DRILL_INSTRUCTIONS = {
    ("geometry.angles.basic_facts", 1): "Work out the size of each angle marked x.",
    ("geometry.angles.basic_facts", 2): "Work out each missing angle.",
    ("geometry.angles.basic_facts", 3): "Work out the value of x.",
    ("geometry.angles.basic_facts", 4): "Work out the value of x.",
    ("geometry.angles.triangle", 2): "Find the size of angle x.",
    ("geometry.angles.triangle", 3): "Find the size of angle x.",
    ("geometry.angles.triangle", 4): "Find the value of x.",
    ("geometry.area.basic_shapes", 1): "Work out the area of each shape.",
    ("geometry.area.basic_shapes", 2): "Work out the area of each shape.",
    ("geometry.area.basic_shapes", 3): "Work out the area of each shape.",
    # Added 2026-10-07 after dev/probes/probe_diagram_carries_values.py showed
    # every given number on the diagram (12/12 per level). Premises a drawing
    # cannot state (tangent, centre, right angles) stay in the instruction.
    ("geometry.angles.parallel_lines", 1): "The marked lines are parallel. Find the value of x.",
    ("geometry.angles.parallel_lines", 2): "The marked lines are parallel. Find the value of x.",
    ("geometry.angles.parallel_lines", 3): "The marked lines are parallel. Find the value of x.",
    ("geometry.angles.parallel_lines", 4): "The marked lines are parallel. Find the value of x.",
    ("geometry.angles.triangle", 1): "Find the size of angle x.",
    ("geometry.area.compound_rectangles", 1): "All corners are right angles. Work out the shaded area of each shape.",
    ("geometry.area.compound_rectangles", 2): "All corners are right angles. Work out the shaded area of each shape.",
    ("geometry.area.compound_rectangles", 3): "All corners are right angles. Work out the shaded area of each shape.",
    ("geometry.circle_theorems.centre_angle", 1): "O is the centre of each circle. Find the value of x.",
    ("geometry.circle_theorems.centre_angle", 2): "O is the centre of each circle. Find the value of x.",
    ("geometry.circle_theorems.centre_angle", 3): "O is the centre of each circle. Find the value of x.",
    ("geometry.circle_theorems.same_segment", 1): "Find the value of x.",
    ("geometry.circle_theorems.same_segment", 3): "Find the value of x.",
    ("geometry.circle_theorems.cyclic_quadrilateral", 1): "Find the value of x.",
    ("geometry.circle_theorems.cyclic_quadrilateral", 2): "Find the value of x.",
    ("geometry.circle_theorems.cyclic_quadrilateral", 3): "Find the value of x.",
    ("geometry.circle_theorems.tangents", 1): "O is the centre of each circle. Lines that touch a circle at one point are tangents. Find the value of x.",
    ("geometry.circle_theorems.tangents", 2): "O is the centre of each circle. Lines that touch a circle at one point are tangents. Find the value of x.",
    ("geometry.circle_theorems.tangents", 3): "O is the centre of each circle. Lines that touch a circle at one point are tangents. Find the value of x.",
    ("geometry.circle_theorems.alternate_segment", 1): "Lines that touch a circle at one point are tangents; O marks the centre where shown. Find the value of x.",
    ("geometry.circle_theorems.alternate_segment", 2): "Lines that touch a circle at one point are tangents; O marks the centre where shown. Find the value of x.",
    ("geometry.circle_theorems.alternate_segment", 3): "Lines that touch a circle at one point are tangents; O marks the centre where shown. Find the value of x.",
    ("geometry.circle_theorems.multi_step", 1): "O marks the centre where shown; lines that touch a circle at one point are tangents. Find the value of x, giving a reason for each step.",
    ("geometry.circle_theorems.multi_step", 2): "O marks the centre where shown; lines that touch a circle at one point are tangents. Find the value of x, giving a reason for each step.",
    ("geometry.circle_theorems.multi_step", 3): "O marks the centre where shown; lines that touch a circle at one point are tangents. Find the value of x, giving a reason for each step.",
    ("geometry.volume.prisms", 1): "Work out the volume of each prism. Leave answers involving π in terms of π.",
    ("geometry.volume.prisms", 2): "Work out the volume of each prism. Leave answers involving π in terms of π.",
    ("geometry.volume.prisms", 3): "Work out the volume of each prism. Leave answers involving π in terms of π.",
    ("geometry.surface_area.prisms", 1): "Work out the total surface area of each closed shape. Leave answers involving π in terms of π.",
    ("geometry.surface_area.prisms", 2): "Work out the total surface area of each closed shape. Leave answers involving π in terms of π.",
    ("geometry.similarity.scale_factors", 1): "The shapes in each pair are similar. Find the value of x.",
}


def drill_skills(registry):
    """(GeneratorInfo, drill levels) for every registered drill skill, by title."""
    known = {info.id: info for info in registry.list()}
    skills = [
        (known[generator_id], levels)
        for generator_id, levels in DRILL_SKILLS.items()
        if generator_id in known
    ]
    return sorted(skills, key=lambda pair: (pair[0].topic, pair[0].title))


# ------------------------------------------------------------- item kinds

def looks_worded(parameters):
    """True when a question's parameters carry a story context anywhere."""
    if isinstance(parameters, dict):
        return "context" in parameters or any(
            looks_worded(value) for value in parameters.values()
        )
    if isinstance(parameters, (list, tuple)):
        return any(looks_worded(value) for value in parameters)
    return False


def is_plain(question):
    """No story context and no answer options; diagrams allowed."""
    return not looks_worded(question.parameters) and not question.choices


def is_bare(question):
    """Short-form practice: plain, and no diagram either."""
    return is_plain(question) and not question.visual_assets("questions")


def is_applied(question):
    return not is_bare(question)


def is_worded(question):
    return looks_worded(question.parameters)


def stage_preference(generator_id, kind):
    """Which items a stage prefers for this skill."""
    diagram = generator_id in DIAGRAM_SKILLS
    if kind == "drill":
        return is_plain if diagram else is_bare
    return is_worded if diagram else is_applied


def renders_in_drill(question):
    """Every diagram (question and answer) draws at drill width.

    Labels that fit at full size can collide when a drawing is small; such
    a question is skipped while building rather than failing at export.
    """
    assets = tuple(question.visual_assets("questions")) + tuple(question.visual_assets("answers"))
    if not assets:
        return True
    from .visuals import VisualFlowable
    try:
        for asset in assets:
            VisualFlowable(asset, preferred_width=DRILL_DIAGRAM_WIDTH).wrap(
                DRILL_DIAGRAM_WIDTH, 10000)
    except ValueError:
        return False
    return True


# ------------------------------------------------------------------- blocks

def require_levels(info, levels, number, purpose):
    unsupported = [level for level in levels if level not in info.difficulty_descriptions]
    require(
        bool(levels) and not unsupported,
        "Block {} ({}) does not support {} difficulty {}.".format(
            number, info.title, purpose,
            ", ".join(str(level) for level in unsupported) or "(none chosen)",
        ),
    )


def level_routes(generator, level):
    """A dispatcher's routes for one level, or [None] for a plain generator.

    Dispatch families mix several forms within a level (draw a line, or find
    its equation). Drilling each route as its own part keeps every part's
    items the same form, so they share one instruction.
    """
    practice_routes = getattr(generator, "drill_routes", None)
    if practice_routes is not None:
        return [list(route) for route in practice_routes[level]]
    routes = getattr(generator, "routes", None)
    if (
        generator.info.id in SPLIT_ROUTE_SKILLS
        and isinstance(routes, dict) and len(routes.get(level, ())) > 1
    ):
        return [list(route) for route in routes[level]]
    return [None]


def drill_parts(generator, level, count):
    """Drill stages for one level: one per route, sharing count between them."""
    routes = level_routes(generator, level)
    dedicated_practice = getattr(generator, "drill_routes", None) is not None
    if routes == [None] or (not dedicated_practice and count < MINIMUM_PART_ITEMS * len(routes)):
        stage = {"kind": "drill", "level": level, "count": count}
        instruction = DRILL_INSTRUCTIONS.get((generator.info.id, level))
        if instruction:
            stage["instruction"] = instruction
        return [stage]
    stages = []
    for index, route in enumerate(routes):
        part_count = count // len(routes) + (1 if index < count % len(routes) else 0)
        if part_count:
            stages.append({
                "kind": "drill", "level": level, "count": part_count,
                "route": route, "part": "abcdefgh"[len(stages)],
            })
    return stages


def on_route(question, route):
    """Whether a dispatched question came through the given route."""
    if route is None:
        return True
    parameters = question.parameters
    return [parameters.get("source"), parameters.get("source_level")] == route


def normalised_block(registry, block, number):
    """Check one requested exercise and return it as a list of stages.

    Request keys: generator_id, levels, count (items per level), and
    optionally apply (number of applied items) and apply_levels.
    """
    require(isinstance(block, dict), "Block {} must be an object.".format(number))
    info = registry.get(block.get("generator_id")).info
    levels = sorted(set(block.get("levels") or [1]))
    require_levels(info, levels, number, "drill")
    count = block.get("count")
    require(
        type(count) is int and 1 <= count <= MAXIMUM_ITEMS_PER_STAGE,
        "Block {} needs a count from 1 to {}.".format(number, MAXIMUM_ITEMS_PER_STAGE),
    )
    generator = registry.get(info.id)
    stages = []
    for level in levels:
        stages.extend(drill_parts(generator, level, count))
    apply = block.get("apply", 0)
    require(
        type(apply) is int and 0 <= apply <= MAXIMUM_APPLY_ITEMS,
        "Block {} needs an apply count from 0 to {}.".format(number, MAXIMUM_APPLY_ITEMS),
    )
    if apply:
        apply_levels = sorted(set(block.get("apply_levels") or levels))
        require_levels(info, apply_levels, number, "applied")
        stages.append({"kind": "apply", "levels": apply_levels, "count": apply})
    return {
        "generator_id": info.id,
        "title": block.get("title") or info.title,
        "stages": stages,
    }


def apply_level_order(count, levels):
    """Spread applied items across levels, easiest first."""
    return [levels[index * len(levels) // count] for index in range(count)]


def drill_question(generator, level, seed, key, seen_prompts, prefer, accept=renders_in_drill):
    """A validated, drawable question with an unseen displayed prompt, or None.

    accept() is a hard filter. Among accepted questions, those passing
    prefer() are taken first; another kind is kept only as a fallback,
    used if none appears within PREFERRED_ATTEMPTS.
    """
    fallback = None
    for attempt in range(ATTEMPTS_PER_ITEM):
        question_seed = derived_seed(seed, "drill", *key, generator.info.id, attempt)
        question = generator.generate(question_seed, level)
        generator.validate(question)
        fingerprint = canonical_json({
            "text": question.prompt.text,
            "math": question.prompt.math_tex,
            "visuals": question.visual_assets("questions"),
        })
        if fingerprint not in seen_prompts and accept(question):
            if prefer(question):
                seen_prompts.add(fingerprint)
                return question
            if fallback is None:
                fallback = (question, fingerprint)
        if fallback is not None and attempt + 1 >= PREFERRED_ATTEMPTS:
            break
    if fallback is None:
        return None
    seen_prompts.add(fallback[1])
    return fallback[0]


# -------------------------------------------------------------------- build

def build_drill(registry, blocks, title="Drill", seed=0):
    """Build a reproducible drill sheet. Raises ValueError with a reason."""
    require(type(seed) is int, "Seed must be an integer.")
    require(isinstance(title, str) and bool(title.strip()), "Enter a worksheet title.")
    require(isinstance(blocks, (list, tuple)) and bool(blocks), "Add at least one block.")

    normalised = []
    questions = []
    seen_prompts = set()
    for block_index, block in enumerate(blocks):
        canonical = normalised_block(registry, block, block_index + 1)
        generator = registry.get(canonical["generator_id"])
        for stage_index, stage in enumerate(canonical["stages"]):
            prefer = stage_preference(canonical["generator_id"], stage["kind"])
            if stage["kind"] == "drill":
                levels = [stage["level"]] * stage["count"]
            else:
                levels = apply_level_order(stage["count"], stage["levels"])
            route = stage.get("route")

            def accept(question, route=route, kind=stage["kind"]):
                # Level 4 mixes rationalising with rectangle applications.
                # Keep the drill section focused even when retries fall back.
                if (kind == "drill"
                        and question.generator_id == "number.surds.manipulation"
                        and question.difficulty == 4
                        and "denominator" not in question.parameters):
                    return False
                return on_route(question, route) and renders_in_drill(question)

            for level in levels:
                question = drill_question(
                    generator, level, seed,
                    (block_index, stage_index, len(questions)), seen_prompts, prefer,
                    accept,
                )
                require(
                    question is not None,
                    "Block {} ({}) ran out of distinct difficulty {} questions. "
                    "Reduce its count or choose more levels.".format(
                        block_index + 1, canonical["title"], level
                    ),
                )
                questions.append(question)
        normalised.append(canonical)

    specification = {"mode": "drill", "title": title.strip(), "blocks": normalised}
    identity = hashlib.sha256(canonical_json({
        "builder": "drill", "builder_version": BUILDER_VERSION,
        "seed": seed, "specification": specification,
        "question_ids": [question.id for question in questions],
    }).encode("utf-8")).hexdigest()
    return Worksheet(identity, title.strip(), seed, specification, tuple(questions))


def drill_stages(worksheet):
    """Regroup a drill worksheet as [(block, [(stage, questions), ...]), ...]."""
    blocks = worksheet.specification.get("blocks", ())
    total = sum(stage["count"] for block in blocks for stage in block["stages"])
    require(total == len(worksheet.questions),
            "Drill stages do not match the worksheet's questions.")
    start = 0
    result = []
    for block in blocks:
        stages = []
        for stage in block["stages"]:
            stages.append((stage, worksheet.questions[start:start + stage["count"]]))
            start += stage["count"]
        result.append((block, stages))
    return result