"""Data for the Build editor: the skill library, default blocks and labels.

No Pythonista imports, so everything here can be tested anywhere. The views
in build_ui.py only draw what this module decides.
"""
import json
import re
from collections import defaultdict

from .blocks import MAXIMUM_QUESTIONS_PER_BLOCK, checked_block
from .curriculum import TAGS_PATH
from .drill import DEFAULT_APPLY_ITEMS, MAXIMUM_ITEMS_PER_STAGE, drill_skills


# ------------------------------------------------------------ editable policy

# Library sections, in the order the specification tells the story.
STRANDS = (
    ("N", "Number"),
    ("A", "Algebra"),
    ("R", "Ratio, proportion and rates of change"),
    ("G", "Geometry and measures"),
    ("P", "Probability"),
    ("S", "Statistics"),
)
# A newly added block: questions at every level the skill has, this many.
DEFAULT_COUNT = 4

CODE = re.compile(r"^([NARGPS])(\d+)$")
STRAND_ORDER = {letter: index for index, (letter, _) in enumerate(STRANDS)}


# ------------------------------------------------------------ skills and levels

def drill_levels_by_skill(registry):
    """{generator id: drill levels} for every skill with a drill form."""
    return {info.id: tuple(sorted(levels)) for info, levels in drill_skills(registry)}


def supported_levels(info, drill_levels, kind):
    """Levels a block of this kind can use for this skill."""
    if kind == "drill":
        return drill_levels.get(info.id, ())
    return tuple(sorted(info.difficulty_descriptions))


def maximum_count(kind):
    return MAXIMUM_ITEMS_PER_STAGE if kind == "drill" else MAXIMUM_QUESTIONS_PER_BLOCK


def default_block(info):
    """A new questions block at every level. apply only matters for drill."""
    return {
        "generator_id": info.id,
        "kind": "questions",
        "levels": sorted(info.difficulty_descriptions),
        "count": DEFAULT_COUNT,
        "apply": True,
    }


def usable_blocks(saved, registry):
    """Saved blocks that are still valid, in order; others are dropped."""
    infos = {info.id: info for info in registry.list()}
    drill_levels = drill_levels_by_skill(registry)
    usable = []
    for number, block in enumerate(saved if isinstance(saved, list) else [], 1):
        try:
            usable.append(checked_block(block, number, infos, drill_levels))
        except (ValueError, TypeError, AttributeError):
            continue
    return usable


# ------------------------------------------------------------ labels

def level_text(levels):
    """L3, L1–4 for a run, or L1, 3 otherwise."""
    levels = sorted(levels)
    if len(levels) == 1:
        return "L{}".format(levels[0])
    if levels == list(range(levels[0], levels[-1] + 1)):
        return "L{}–{}".format(levels[0], levels[-1])
    return "L" + ", ".join(str(level) for level in levels)


def block_size(block):
    """How many questions the block puts on the sheet."""
    if block["kind"] == "drill":
        applied = DEFAULT_APPLY_ITEMS if block.get("apply", True) else 0
        return block["count"] * len(block["levels"]) + applied
    return block["count"]


def block_summary(block):
    """One line for the sheet list, e.g. 'Drill · L1, 3 · 4 per level + applied'."""
    levels = level_text(block["levels"])
    if block["kind"] == "drill":
        applied = " + applied" if block.get("apply", True) else ""
        return "Drill · {} · {} per level{}".format(levels, block["count"], applied)
    noun = "question" if block["count"] == 1 else "questions"
    return "{} {} · {}".format(block["count"], noun, levels)


def span_text(prefix, values, plural=None):
    low, high = min(values), max(values)
    if low == high:
        return "{} {}".format(prefix, low) if plural else "{}{}".format(prefix, low)
    if plural:
        return "{} {}–{}".format(plural, low, high)
    return "{}{}–{}{}".format(prefix, low, prefix, high)


# ------------------------------------------------------------ library

def code_key(code):
    match = CODE.match(code)
    if not match:
        return (len(STRANDS), 0)
    return (STRAND_ORDER[match.group(1)], int(match.group(2)))


def library_sections(registry, level_tags, drill_levels, tags_path=TAGS_PATH):
    """[(strand title, [entry, ...])] in specification order.

    Each skill sits under the strand of its first spec code. An entry is a
    dict with generator_id, title, detail (codes, years, grades, drill) and a
    lowercase search string.
    """
    tags = json.loads(tags_path.read_text(encoding="utf-8"))["generators"]
    levels_by_skill = defaultdict(list)
    for tag in level_tags:
        levels_by_skill[tag.generator_id].append(tag)
    grouped = defaultdict(list)
    for info in registry.list():
        codes = sorted(tags[info.id]["spec"], key=code_key)
        placed = levels_by_skill[info.id]
        years = [tag.year for tag in placed]
        grades = [tag.grade for tag in placed]
        parts = [", ".join(codes), span_text("Y", years), span_text("Grade", grades, "Grades")]
        if info.id in drill_levels:
            parts.append("Drill " + level_text(drill_levels[info.id]))
        grouped[codes[0][0]].append({
            "generator_id": info.id,
            "title": info.title,
            "detail": " · ".join(parts),
            "search": " ".join([info.title, info.id, info.topic] + codes).lower(),
            "grades": sorted(set(grades)),
            "years": sorted(set(years)),
            "order": (code_key(codes[0]), min(years), info.title),
        })
    return [
        (title, sorted(grouped[letter], key=lambda entry: entry["order"]))
        for letter, title in STRANDS if grouped[letter]
    ]


def filter_sections(sections, query):
    """Sections keeping only entries that contain every word of the query."""
    words = query.strip().lower().split()
    if not words:
        return sections
    filtered = []
    for title, entries in sections:
        kept = [entry for entry in entries
                if all(word in entry["search"] for word in words)]
        if kept:
            filtered.append((title, kept))
    return filtered