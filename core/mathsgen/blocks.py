"""Block sheets: one worksheet built from an ordered list of blocks.

A block is one skill with its own settings, for example:

    {"generator_id": "algebra.simultaneous.linear", "kind": "questions",
     "levels": [3], "count": 6}
    {"generator_id": "number.fractions.addition", "kind": "drill",
     "levels": [1, 2], "count": 6, "apply": True}

Question blocks use the normal worksheet builder in set order. Drill blocks
use the staged drill builder: one stage per level, then applied problems when
apply is on. Blocks keep the teacher's order. specification["segments"]
records which run of questions belongs to which block, so the renderer can
lay out each block in its own style on one continuous document.
"""
import hashlib

from .core import canonical_json, require
from .drill import DEFAULT_APPLY_ITEMS, MAXIMUM_ITEMS_PER_STAGE, build_drill, drill_skills
from .worksheets import Worksheet, build_worksheet


BUILDER_VERSION = 1
BLOCK_KINDS = ("questions", "drill")

# ------------------------------------------------------------ editable policy

MAXIMUM_QUESTIONS_PER_BLOCK = 40


# ------------------------------------------------------------ building

def build_block_sheet(registry, blocks, title="Worksheet", seed=0):
    """Build a reproducible sheet from blocks, in order.

    Raises ValueError naming the first block with a problem, in words that
    can be shown to the teacher directly.
    """
    require(type(seed) is int, "Seed must be an integer.")
    require(isinstance(title, str) and bool(title.strip()), "Enter a worksheet title.")
    require(isinstance(blocks, (list, tuple)) and bool(blocks), "Add at least one block.")
    title = title.strip()
    infos = {info.id: info for info in registry.list()}
    drill_levels = {info.id: tuple(levels) for info, levels in drill_skills(registry)}
    checked = [
        checked_block(block, number, infos, drill_levels)
        for number, block in enumerate(blocks, 1)
    ]

    questions, segments = [], []
    for index, block in enumerate(checked):
        part = build_one_block(registry, block, title, block_seed(seed, index))
        segment = {"kind": block["kind"], "start": len(questions),
                   "count": len(part.questions)}
        if block["kind"] == "drill":
            segment["drill_blocks"] = part.specification["blocks"]
        segments.append(segment)
        questions.extend(part.questions)

    specification = {"mode": "blocks", "title": title,
                     "blocks": checked, "segments": segments}
    identity = hashlib.sha256(canonical_json({
        "builder": "blocks", "builder_version": BUILDER_VERSION,
        "seed": seed, "specification": specification,
        "question_ids": [question.id for question in questions],
    }).encode("utf-8")).hexdigest()
    return Worksheet(identity, title, seed, specification, tuple(questions))


def checked_block(block, number, infos, drill_levels):
    """A validated, complete copy of one block."""
    name = "Block {}".format(number)
    require(isinstance(block, dict), name + " is not a block.")
    info = infos.get(block.get("generator_id"))
    require(info is not None, name + ": this skill is no longer available.")
    kind = block.get("kind", "questions")
    require(kind in BLOCK_KINDS, "{}: unknown block kind {!r}.".format(name, kind))
    count = block.get("count")
    require(type(count) is int and count >= 1, name + ": enter a positive count.")
    levels = block.get("levels")
    require(isinstance(levels, (list, tuple)) and bool(levels),
            name + ": choose at least one difficulty.")
    levels = sorted(set(levels))

    if kind == "drill":
        require(info.id in drill_levels,
                "{}: {} has no drill form.".format(name, info.title))
        supported = drill_levels[info.id]
        require(count <= MAXIMUM_ITEMS_PER_STAGE,
                "{}: use at most {} drill items per level.".format(
                    name, MAXIMUM_ITEMS_PER_STAGE))
    else:
        supported = tuple(sorted(info.difficulty_descriptions))
        require(count <= MAXIMUM_QUESTIONS_PER_BLOCK,
                "{}: use at most {} questions.".format(
                    name, MAXIMUM_QUESTIONS_PER_BLOCK))
    unsupported = [level for level in levels if level not in supported]
    require(not unsupported, "{}: {} {} at difficulty {} only.".format(
        name, info.title, "drills" if kind == "drill" else "runs",
        ", ".join(str(level) for level in supported)))

    return {
        "generator_id": info.id,
        "title": info.title,
        "kind": kind,
        "levels": levels,
        "count": count,
        "apply": bool(block.get("apply", True)) if kind == "drill" else False,
    }


def build_one_block(registry, block, title, seed):
    """The questions for one block, as a worksheet from the matching builder."""
    if block["kind"] == "drill":
        return build_drill(registry, [{
            "generator_id": block["generator_id"],
            "levels": block["levels"],
            "count": block["count"],
            "apply": DEFAULT_APPLY_ITEMS if block["apply"] else 0,
            "apply_levels": block["levels"],
        }], title, seed)
    return build_worksheet({
        "title": title,
        "shuffle": False,
        "sections": [{
            "generator_ids": [block["generator_id"]],
            "count": block["count"],
            "difficulties": block["levels"],
        }],
    }, seed, registry)


def block_seed(seed, index):
    """An independent, reproducible seed for one block of a sheet."""
    digest = hashlib.sha256("{}:{}".format(seed, index).encode("utf-8")).hexdigest()
    return int(digest[:13], 16)