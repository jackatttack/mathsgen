"""Quick-start worksheets chosen by year group or grade band.

Reads two data files in paper_blueprints/:
- curriculum_tags.json: spec codes and intro year for every generator level.
- edexcel_1ma1.json: draft grade for every generator level (shared with
  exam_paper.py, so grades have one home).

quick_start_spec() returns an ordinary worksheet spec, the same shape that
worksheet_ui.make_spec builds, so export and PDF code need no changes.
"""
import json
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "paper_blueprints"
TAGS_PATH = DATA_DIR / "curriculum_tags.json"
BLUEPRINT_PATH = DATA_DIR / "edexcel_1ma1.json"


# ------------------------------------------------------------ editable policy

# A Year N sheet also uses levels introduced up to this many years earlier.
RECAP_YEARS = 1
YEAR_GROUPS = (7, 8, 9, 10, 11)
# Grade bands offered in the quick-start picker, as inclusive ranges.
GRADE_BANDS = {
    "Grades 1-3": (1, 3),
    "Grades 4-5": (4, 5),
    "Grades 6-7": (6, 7),
    "Grades 8-9": (8, 9),
}


# ------------------------------------------------------------ level data

@dataclass(frozen=True)
class LevelTag:
    """One difficulty level of one generator, with its curriculum placement."""
    generator_id: str
    topic: str
    level: int
    year: int
    grade: int
    spec: tuple


def load_level_tags(registry, tags_path=TAGS_PATH, blueprint_path=BLUEPRINT_PATH):
    """Every registered generator level with its intro year and draft grade.

    Raises ValueError if a generator is untagged or its level counts disagree,
    because a silently missing skill would quietly shrink quick-start sheets.
    """
    tags = json.loads(Path(tags_path).read_text(encoding="utf-8"))["generators"]
    blueprint = json.loads(Path(blueprint_path).read_text(encoding="utf-8"))["generators"]
    level_tags = []
    for info in registry.list():
        entry = tags.get(info.id)
        grades = blueprint.get(info.id)
        if entry is None or grades is None:
            raise ValueError("No curriculum tags or grades for " + info.id)
        levels = sorted(info.difficulty_descriptions)
        if not len(levels) == len(entry["years"]) == len(grades["grades"]):
            raise ValueError("Level count mismatch in tags for " + info.id)
        for level, year, grade in zip(levels, entry["years"], grades["grades"]):
            level_tags.append(LevelTag(
                info.id, info.topic, level, year, grade, tuple(entry["spec"])))
    return level_tags


def suitable_levels(level_tags, topics, year=None, grades=None):
    """Levels in the chosen topics that suit one year group or one grade band."""
    if (year is None) == (grades is None):
        raise ValueError("Choose a year group or a grade band.")
    pool = []
    for tag in level_tags:
        if tag.topic not in topics:
            continue
        if year is not None and not (year - RECAP_YEARS <= tag.year <= year):
            continue
        if grades is not None and not (grades[0] <= tag.grade <= grades[1]):
            continue
        pool.append(tag)
    return pool


# ------------------------------------------------------------ selection

def pick_levels(pool, count, rng):
    """Spread count picks across topics first, then across skills.

    Topics take turns so each chosen subject gets a fair share. Inside a
    topic the least-used skill goes next, so a skill repeats only after every
    skill in that topic has been used. Each pick takes one of the skill's
    suitable levels at random.
    """
    by_topic = defaultdict(lambda: defaultdict(list))
    for tag in pool:
        by_topic[tag.topic][tag.generator_id].append(tag)
    topic_order = sorted(by_topic)
    rng.shuffle(topic_order)
    uses = Counter()
    picks = []
    while len(picks) < count:
        skills = by_topic[topic_order[len(picks) % len(topic_order)]]
        fewest = min(uses[skill] for skill in skills)
        skill = rng.choice(sorted(s for s in skills if uses[s] == fewest))
        uses[skill] += 1
        picks.append(rng.choice(skills[skill]))
    return picks


def easier_first(picks, rng):
    """Order by intro year, then grade, then level; ties in random order."""
    keyed = [((tag.year, tag.grade, tag.level, rng.random()), tag) for tag in picks]
    return [tag for _, tag in sorted(keyed, key=lambda pair: pair[0])]


def as_sections(ordered):
    """One section per run of identical (skill, level) picks, keeping order."""
    sections = []
    for tag in ordered:
        last = sections[-1] if sections else None
        if (last and last["generator_ids"] == [tag.generator_id]
                and last["difficulties"] == [tag.level]):
            last["count"] += 1
        else:
            sections.append({
                "generator_ids": [tag.generator_id],
                "count": 1,
                "difficulties": [tag.level],
            })
    return sections


def quick_start_spec(registry, topics, count, title, seed,
                     year=None, grades=None, level_tags=None):
    """A mixed, easier-to-harder worksheet spec for a year group or grade band.

    topics are registry topic keys such as "number" or "algebra". Give exactly
    one of year (7-11) or grades (an inclusive (low, high) pair). The same
    inputs and seed always give the same spec.
    """
    if type(count) is not int or count < 1:
        raise ValueError("Enter a positive number of questions.")
    if not topics:
        raise ValueError("Choose at least one topic.")
    if not title.strip():
        raise ValueError("Enter a worksheet title.")
    if level_tags is None:
        level_tags = load_level_tags(registry)
    pool = suitable_levels(level_tags, set(topics), year=year, grades=grades)
    if not pool:
        raise ValueError("No questions suit that choice yet. "
                         "Try another year group, grade band or topic.")
    rng = random.Random(seed)
    picks = pick_levels(pool, count, rng)
    return {
        "title": title.strip(),
        "shuffle": False,
        "sections": as_sections(easier_first(picks, rng)),
    }