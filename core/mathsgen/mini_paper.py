"""Mini paper: a balanced, reproducible selection that gets harder as it goes.

Selection, in priority order:
1. Difficulty slots are allocated from LEVEL_WEIGHTS, always summing exactly
   to the requested total.
2. Each slot is filled by the subject (topic) furthest below its even share,
   then the least-used teaching family (subtopic), then the least-used
   generator, preferring an unused generator/level pair.
3. Only generators supporting the slot's level are candidates. Duplicate
   displayed prompts are rejected exactly as in worksheets.build_worksheet;
   an exhausted candidate falls through to the next best one.
4. Questions are sorted by difficulty and shuffled within each level while
   avoiding adjacent repeats of a generator, then of a subject.

If the request cannot be met, a ValueError explains why. A paper never
silently contains fewer questions than requested.

Implementation notes:
- Difficulty levels are relative to each generator. A level-1 problem-solving
  question may be harder than a level-2 arithmetic question, so the
  progression is approximate until a cross-topic calibration exists.
- Question count does not guarantee exam duration or page count. This is a
  balanced practice paper, not an exam-board paper simulator.
"""
from collections import Counter
from fractions import Fraction
import hashlib
import random

from .core import canonical_json, require
from .worksheets import Worksheet, derived_seed


# ------------------------------------------------------------ editable policy

# Target proportions by number of selected levels, easiest level first.
LEVEL_WEIGHTS = {
    1: (1,),
    2: (1, 1),
    3: (3, 4, 3),
    4: (2, 3, 3, 2),
}
ATTEMPTS_PER_CANDIDATE = 100
BUILDER_VERSION = 1


# ---------------------------------------------------------------- allocation

def allocate(total, keys, weights, tie_order):
    """Largest-remainder split of total across keys; always sums to total.

    tie_order ranks keys when remainders are equal (earlier wins).
    """
    weight_sum = sum(weights)
    shares = {key: Fraction(total * weight, weight_sum) for key, weight in zip(keys, weights)}
    counts = {key: share.numerator // share.denominator for key, share in shares.items()}
    leftover = total - sum(counts.values())
    ranked = sorted(keys, key=lambda key: (-(shares[key] - counts[key]), tie_order.index(key)))
    for key in ranked[:leftover]:
        counts[key] += 1
    return counts


def level_allocation(total, levels):
    """Questions per level. Rounding ties favour middle levels, then easier."""
    levels = sorted(levels)
    centre = (len(levels) - 1) / 2
    tie_order = sorted(levels, key=lambda level: (abs(levels.index(level) - centre), level))
    return allocate(total, levels, LEVEL_WEIGHTS[len(levels)], tie_order)


def subject_targets(total, subjects, rng):
    """Even share per subject; the seed decides who gets rounding extras."""
    order = list(subjects)
    rng.shuffle(order)
    return allocate(total, order, [1] * len(order), order)


def interleaved(level_counts):
    """Level slots in round-robin order, so no level is filled all at once."""
    remaining = dict(level_counts)
    slots = []
    while any(remaining.values()):
        for level in sorted(remaining):
            if remaining[level]:
                slots.append(level)
                remaining[level] -= 1
    return slots


# ----------------------------------------------------------------- selection

def selection_cost(info, level, usage, targets):
    """Lower is better. Subject balance first, then variety."""
    subject = info.topic
    return (
        usage["subject"][subject] - targets[subject],
        usage["subject_level"][(subject, level)],
        usage["family"][(subject, info.subtopic)],
        usage["generator"][info.id],
        usage["pair"][(info.id, level)],
    )


def unique_question(generator, level, seed, slot, seen_prompts):
    """A validated question with an unseen displayed prompt, or None."""
    for attempt in range(ATTEMPTS_PER_CANDIDATE):
        question_seed = derived_seed(seed, "mini", slot, generator.info.id, attempt)
        question = generator.generate(question_seed, level)
        generator.validate(question)
        fingerprint = canonical_json({
            "text": question.prompt.text,
            "math": question.prompt.math_tex,
            "visuals": question.visual_assets("questions"),
        })
        if fingerprint not in seen_prompts:
            seen_prompts.add(fingerprint)
            return question
    return None


# ------------------------------------------------------------------ ordering

def arrange(questions, rng):
    """Easier to harder; shuffle within a level, avoiding adjacent repeats."""
    ordered = []
    previous = None
    for level in sorted({question.difficulty for question in questions}):
        remaining = [question for question in questions if question.difficulty == level]
        rng.shuffle(remaining)
        while remaining:
            choice = next_question(remaining, previous)
            remaining.remove(choice)
            ordered.append(choice)
            previous = choice
    return ordered


def next_question(remaining, previous):
    if previous is None:
        return remaining[0]
    tests = (
        lambda q: q.generator_id != previous.generator_id and q.topic != previous.topic,
        lambda q: q.generator_id != previous.generator_id,
    )
    for test in tests:
        for question in remaining:
            if test(question):
                return question
    return remaining[0]


# ---------------------------------------------------------------------- build

def build_mini_paper(registry, total, levels, subjects, title="Mini Paper", seed=0):
    """Build a reproducible mini paper. Raises ValueError with a reason."""
    require(type(seed) is int, "Seed must be an integer.")
    require(type(total) is int and total >= 1, "Total questions must be a positive whole number.")
    levels = sorted(set(levels))
    require(bool(levels) and all(level in (1, 2, 3, 4) for level in levels),
            "Choose difficulty levels from 1 to 4.")
    require(isinstance(title, str) and bool(title.strip()), "Enter a worksheet title.")
    subjects = sorted(set(subjects))
    require(bool(subjects), "Include at least one subject.")

    pool = [
        info for info in registry.list()
        if info.topic in subjects and set(levels) & set(info.difficulty_descriptions)
    ]
    require(bool(pool), "No skill in the chosen subjects supports the chosen difficulty levels.")
    for level in levels:
        require(
            any(level in info.difficulty_descriptions for info in pool),
            "No skill in the chosen subjects supports difficulty {}.".format(level),
        )

    rng = random.Random(derived_seed(seed, "mini-paper"))
    available = sorted({info.topic for info in pool})
    targets = subject_targets(total, available, rng)
    slots = interleaved(level_allocation(total, levels))

    usage = {name: Counter() for name in ("subject", "subject_level", "family", "generator", "pair")}
    seen_prompts = set()
    questions = []
    for slot, level in enumerate(slots):
        candidates = [info for info in pool if level in info.difficulty_descriptions]
        ranked = sorted(
            candidates,
            key=lambda info: selection_cost(info, level, usage, targets) + (rng.random(),),
        )
        for info in ranked:
            question = unique_question(registry.get(info.id), level, seed, slot, seen_prompts)
            if question is not None:
                break
        else:
            raise ValueError(
                "Could not build {} distinct questions: after {}, no skill in the chosen "
                "subjects produced a new difficulty {} question. Reduce the total, include "
                "more subjects or allow more difficulty levels.".format(total, len(questions), level)
            )
        usage["subject"][info.topic] += 1
        usage["subject_level"][(info.topic, level)] += 1
        usage["family"][(info.topic, info.subtopic)] += 1
        usage["generator"][info.id] += 1
        usage["pair"][(info.id, level)] += 1
        questions.append(question)

    questions = arrange(questions, rng)
    specification = {
        "mode": "mini_paper", "title": title.strip(), "total": total,
        "difficulties": levels, "subjects": subjects,
    }
    identity = hashlib.sha256(canonical_json({
        "builder": "mini_paper", "builder_version": BUILDER_VERSION,
        "seed": seed, "specification": specification,
        "question_ids": [question.id for question in questions],
    }).encode("utf-8")).hexdigest()
    return Worksheet(identity, title.strip(), seed, specification, tuple(questions))