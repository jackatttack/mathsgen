"""Edexcel-style exam papers: exact marks, tiered, weighted by strand, easiest first.

The blueprint (paper_blueprints/edexcel_1ma1.json) maps every generator level
to a strand, an approximate grade and whether it needs a calculator. This
module turns it into a paper:

1. Candidates are generator levels whose grade lies in the tier's range.
   A non-calculator paper uses only levels that do not need a calculator.
2. Selection fills the paper's marks exactly. Each pick is the candidate that
   best closes the largest shortfall: strand marks first (from the tier's
   weighting), then grade-band marks (GRADE_PROFILE), preferring teaching
   families not yet on the paper. Until MINIMUM_LONG_QUESTIONS is met,
   questions worth LONG_QUESTION_MARKS or more come first.
3. Questions are ordered by grade and shuffled within a grade.

Marks are the generators' own indicative marks, so strand balance is
approximate to within one question. Grade 9 content does not exist yet; its
share of the profile simply stays unfilled until it does.
"""
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

from .core import canonical_json, require
from .mini_paper import allocate, unique_question
from .worksheets import Worksheet, derived_seed


BLUEPRINT_PATH = (Path(__file__).resolve().parent.parent
                  / "paper_blueprints" / "edexcel_1ma1.json")
BUILDER_VERSION = 2


# ------------------------------------------------------------ editable policy

# Share of the paper's marks aimed at each grade, per tier.
GRADE_PROFILE = {
    "foundation": {1: 10, 2: 15, 3: 25, 4: 25, 5: 25},
    "higher": {4: 15, 5: 20, 6: 20, 7: 20, 8: 15, 9: 10},
}
MINIMUM_LONG_QUESTIONS = {"foundation": 3, "higher": 5}
LONG_QUESTION_MARKS = 4
# On calculator papers, prefer levels that genuinely need a calculator until
# they carry this share of the marks. A preference, not a rule: strand balance
# still decides when the two conflict.
CALCULATOR_SHARE = {"foundation": 0.4, "higher": 0.5}
TIER_TITLES = {"foundation": "Foundation", "higher": "Higher"}


# ------------------------------------------------------------ blueprint access

def load_blueprint(path=BLUEPRINT_PATH):
    return json.loads(Path(path).read_text())


def strand_for(info, blueprint):
    """Longest matching id prefix wins; otherwise the generator's topic decides."""
    for prefix, strand in sorted(blueprint["strand_by_prefix"].items(),
                                 key=lambda item: -len(item[0])):
        if info.id.startswith(prefix):
            return strand
    return blueprint["strand_by_topic"][info.topic]


def level_facts(info, blueprint):
    """[(level, grade, needs_calculator)] for every level of one generator."""
    entry = blueprint["generators"].get(info.id)
    require(entry is not None, "Generator missing from the blueprint: " + info.id)
    levels = sorted(info.difficulty_descriptions)
    flag = entry.get("calculator", False)
    flags = list(flag) if isinstance(flag, list) else [flag] * len(levels)
    require(len(entry["grades"]) == len(levels) == len(flags),
            "Blueprint level count mismatch: " + info.id)
    return list(zip(levels, entry["grades"], flags))


def paper1_flags(info, blueprint):
    """[paper-1-only?] per level: skills that are pointless with a calculator."""
    entry = blueprint["generators"][info.id]
    levels = sorted(info.difficulty_descriptions)
    flag = entry.get("paper1_only", False)
    flags = list(flag) if isinstance(flag, list) else [flag] * len(levels)
    require(len(flags) == len(levels), "Blueprint paper1_only mismatch: " + info.id)
    return flags


def candidate_pool(registry, blueprint, tier, calculator_allowed):
    low, high = blueprint["tiers"][tier]["grades"]
    pool = []
    for info in registry.list():
        strand = strand_for(info, blueprint)
        generator = registry.get(info.id)
        for (level, grade, needs), only in zip(level_facts(info, blueprint),
                                               paper1_flags(info, blueprint)):
            if calculator_allowed and only:
                continue
            if low <= grade <= high and (calculator_allowed or not needs):
                pool.append({
                    "id": info.id, "level": level, "grade": grade, "strand": strand,
                    "needs": needs,
                    "family": (info.topic, info.subtopic),
                    "typical_marks": generator.generate(0, level).marks,
                })
    return pool


# ------------------------------------------------------------ building

def build_exam_paper(registry, tier, paper, seed=0, blueprint=None):
    """Build a reproducible Edexcel-style paper. Raises ValueError with a reason."""
    blueprint = blueprint or load_blueprint()
    require(tier in blueprint["tiers"], "Tier must be foundation or higher.")
    require(str(paper) in blueprint["calculator_papers"], "Paper must be 1, 2 or 3.")
    require(type(seed) is int, "Seed must be an integer.")
    total = blueprint["paper_marks"]
    calculator_allowed = blueprint["calculator_papers"][str(paper)]
    rng = random.Random(derived_seed(seed, "exam-paper", tier, paper))

    pool = candidate_pool(registry, blueprint, tier, calculator_allowed)
    require(bool(pool), "No generator levels suit this tier and paper.")
    weights = blueprint["tiers"][tier]["weights"]
    strands = list(weights)
    strand_target = allocate(total, strands, [weights[s] for s in strands], strands)
    profile = GRADE_PROFILE[tier]
    grades = sorted(profile)
    grade_target = allocate(total, grades, [profile[g] for g in grades], grades)

    marks_by_strand, marks_by_grade, family_uses = Counter(), Counter(), Counter()
    used_pairs, seen_prompts, picks = set(), set(), []
    remaining, long_count, calculator_marks = total, 0, 0

    while remaining > 0:
        need_long = long_count < MINIMUM_LONG_QUESTIONS[tier]

        def cost(candidate):
            strand_gap = strand_target[candidate["strand"]] - marks_by_strand[candidate["strand"]]
            grade_gap = grade_target.get(candidate["grade"], 0) - marks_by_grade[candidate["grade"]]
            want_calculator = (calculator_allowed
                               and calculator_marks < CALCULATOR_SHARE[tier] * total)
            return (
                need_long and candidate["typical_marks"] < LONG_QUESTION_MARKS,
                want_calculator and not candidate["needs"],
                strand_gap <= 0,
                family_uses[candidate["family"]],
                -strand_gap,
                -grade_gap,
                rng.random(),
            )

        options = [c for c in pool if (c["id"], c["level"]) not in used_pairs
                   and c["typical_marks"] <= remaining]
        for candidate in sorted(options, key=cost):
            question = unique_question(registry.get(candidate["id"]), candidate["level"],
                                       seed, len(picks), seen_prompts)
            if question is not None and question.marks <= remaining:
                break
        else:
            raise ValueError(
                "Could not fill exactly {} marks: {} marks placed, and no remaining "
                "question fits the last {}.".format(total, total - remaining, remaining))

        used_pairs.add((candidate["id"], candidate["level"]))
        marks_by_strand[candidate["strand"]] += question.marks
        marks_by_grade[candidate["grade"]] += question.marks
        family_uses[candidate["family"]] += 1
        long_count += question.marks >= LONG_QUESTION_MARKS
        calculator_marks += question.marks if candidate["needs"] else 0
        remaining -= question.marks
        picks.append((candidate, question))

    ordered = []
    for grade in sorted({candidate["grade"] for candidate, _ in picks}):
        group = [question for candidate, question in picks if candidate["grade"] == grade]
        rng.shuffle(group)
        ordered += group

    title = "Edexcel-style {} Paper {} ({})".format(
        TIER_TITLES[tier], paper, "Calculator" if calculator_allowed else "Non-calculator")
    specification = {
        "mode": "exam_paper", "board": blueprint["board"],
        "specification": blueprint["specification"], "tier": tier, "paper": paper,
        "calculator": calculator_allowed, "marks": total,
        "strand_marks": dict(sorted(marks_by_strand.items())),
        "strand_targets": dict(sorted(strand_target.items())),
        "grade_marks": {str(g): marks_by_grade[g] for g in sorted(marks_by_grade)},
    }
    identity = hashlib.sha256(canonical_json({
        "builder": "exam_paper", "builder_version": BUILDER_VERSION,
        "seed": seed, "specification": specification,
        "question_ids": [question.id for question in ordered],
    }).encode("utf-8")).hexdigest()
    return Worksheet(identity, title, seed, specification, tuple(ordered))