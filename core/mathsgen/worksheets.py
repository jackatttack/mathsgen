"""Deterministic worksheet assembly, independent of every renderer."""
from dataclasses import dataclass
import hashlib
import json
import random

from .catalogue import build_registry
from .core import canonical_json, require


@dataclass(frozen=True)
class Worksheet:
    id: str
    title: str
    seed: int
    specification: dict
    questions: tuple

    def to_dict(self):
        """Teacher export: contains answers, steps and validation parameters."""
        return {
            "schema_version": 1,
            "id": self.id,
            "title": self.title,
            "seed": self.seed,
            "specification": self.specification,
            "questions": [question.to_dict() for question in self.questions],
        }


def derived_seed(seed, *parts):
    payload = canonical_json([seed] + list(parts)).encode("utf-8")
    return int(hashlib.sha256(payload).hexdigest()[:16], 16)


def difficulty_levels(text):
    """Parse one level or an inclusive range such as 2:4."""
    pieces = text.split(":")
    if len(pieces) == 1:
        levels = [int(pieces[0])]
    elif len(pieces) == 2:
        start, end = map(int, pieces)
        require(1 <= start <= end <= 4, "Difficulty range must lie within 1:4")
        levels = list(range(start, end + 1))
    else:
        raise ValueError("Use a difficulty such as 3 or 2:4")
    require(all(1 <= level <= 4 for level in levels), "Difficulty must lie within 1:4")
    return levels


def quick_spec(count=20, difficulty="1:4", topic=None, profile=None):
    """Create a balanced spec using currently implemented coverage only."""
    require(type(count) is int and count > 0, "count must be positive")
    levels = difficulty_levels(difficulty)
    require(not (topic and profile), "Choose a topic or a profile, not both")
    if profile:
        require(profile == "pipeline-demo", "Unknown profile: " + profile)
    if topic:
        sections = [{"topic": topic, "count": count, "difficulties": levels}]
        title = topic.replace("_", " ").title() + " Practice"
    else:
        algebra_count = (count + 1) // 2
        ratio_count = count // 2
        sections = [
            {"topic": "algebra", "count": algebra_count, "difficulties": levels}
        ]
        if ratio_count:
            sections.append({
                "topic": "ratio", "count": ratio_count, "difficulties": levels,
            })
        title = "Algebra and Ratio Practice"
    return {"title": title, "shuffle": True, "sections": sections}


def build_worksheet(specification, seed=0, registry=None):
    """Allocate balanced generator/level pairs within exact section quotas.

    Specifications reject unknown fields rather than silently ignoring typos.
    Duplicate prompts are retried with new derived seeds, up to 100 attempts
    per slot. Exhausted variation is reported, never silently duplicated.
    """
    require(type(seed) is int, "Worksheet seed must be an integer")
    require(isinstance(specification, dict), "Specification must be an object")
    specification = json.loads(canonical_json(specification))
    require(
        set(specification) <= {"title", "shuffle", "sections", "show_difficulty"},
        "Unknown worksheet specification field",
    )
    title = specification.get("title", "Maths Practice")
    require(isinstance(title, str) and bool(title.strip()), "A nonempty title is required")
    shuffle = specification.get("shuffle", True)
    require(type(shuffle) is bool, "shuffle must be true or false")
    show_difficulty = specification.get("show_difficulty", True)
    require(type(show_difficulty) is bool, "show_difficulty must be true or false")
    sections = specification.get("sections")
    require(isinstance(sections, list) and bool(sections), "At least one section is required")
    registry = registry or build_registry()
    questions = []
    seen_prompts = set()
    # Track generator usage across sections as well as within each section.
    # An explicitly single-generator section is still allowed to repeat.
    generator_uses = {}

    for section_index, section in enumerate(sections):
        require(isinstance(section, dict), "Each section must be an object")
        require(
            set(section) <= {"topic", "generator_ids", "count", "difficulties"},
            "Unknown section field",
        )
        require(
            ("topic" in section) != ("generator_ids" in section),
            "Each section needs exactly one of topic or generator_ids",
        )
        count = section.get("count")
        require(type(count) is int and count > 0, "Section count must be positive")
        levels = section.get("difficulties", [1, 2, 3, 4])
        require(
            isinstance(levels, list) and bool(levels)
            and all(type(level) is int and 1 <= level <= 4 for level in levels),
            "difficulties must be a nonempty list of levels 1 through 4",
        )
        require(len(set(levels)) == len(levels), "Duplicate difficulty levels")
        if "topic" in section:
            require(isinstance(section["topic"], str), "topic must be text")
            generator_ids = [info.id for info in registry.list(section["topic"])]
        else:
            generator_ids = section["generator_ids"]
            require(
                isinstance(generator_ids, list) and bool(generator_ids)
                and all(isinstance(item, str) for item in generator_ids),
                "generator_ids must be a nonempty list of IDs",
            )
            require(len(set(generator_ids)) == len(generator_ids), "Duplicate generator IDs")
        require(bool(generator_ids), "Section has no implemented generators")

        # Validate supported levels, then schedule generators rather than
        # generator/level pairs. This prevents premature question-type repeats.
        generator_ids = sorted(generator_ids)
        for generator_id in generator_ids:
            generator = registry.get(generator_id)
            for level in levels:
                require(
                    level in generator.info.difficulty_descriptions,
                    "{} does not support difficulty {}".format(generator_id, level),
                )

        rng = random.Random(derived_seed(seed, "section", section_index))
        schedule = []
        level_uses = {level: 0 for level in levels}

        # Choose the least-used eligible generators. Within a section, a
        # generator cannot repeat until all other eligible generators have
        # caught up. Existing usage from earlier sections is also considered.
        section_uses = {generator_id: 0 for generator_id in generator_ids}
        for _ in range(count):
            fewest_in_section = min(section_uses.values())
            candidates = [
                generator_id for generator_id in generator_ids
                if section_uses[generator_id] == fewest_in_section
            ]
            fewest_overall = min(generator_uses.get(gid, 0) for gid in candidates)
            candidates = [
                gid for gid in candidates
                if generator_uses.get(gid, 0) == fewest_overall
            ]
            generator_id = rng.choice(candidates)

            fewest_level = min(level_uses.values())
            level_candidates = [
                level for level in levels if level_uses[level] == fewest_level
            ]
            level = rng.choice(level_candidates)

            schedule.append((generator_id, level))
            section_uses[generator_id] += 1
            generator_uses[generator_id] = generator_uses.get(generator_id, 0) + 1
            level_uses[level] += 1

        for slot, (generator_id, level) in enumerate(schedule[:count]):
            generator = registry.get(generator_id)
            for attempt in range(100):
                question_seed = derived_seed(seed, section_index, slot, attempt)
                question = generator.generate(question_seed, level)
                generator.validate(question)
                fingerprint = canonical_json({
                    "text": question.prompt.text,
                    "math": question.prompt.math_tex,
                    "visuals": question.visual_assets("questions"),
                })
                if fingerprint not in seen_prompts:
                    seen_prompts.add(fingerprint)
                    questions.append(question)
                    break
            else:
                raise ValueError(
                    "Could not find a unique question for section {}, slot {}. "
                    "Reduce the count or broaden the specification.".format(section_index, slot)
                )

    if shuffle:
        random.Random(derived_seed(seed, "worksheet-order")).shuffle(questions)
    # Easier questions always come first, even in random order: the shuffle
    # decides the order within each difficulty band, not across bands.
    # Python's sort is stable, so the shuffled order survives inside a band.
    questions.sort(key=lambda question: question.difficulty)
    identity_payload = {
        "builder_version": 3,
        "seed": seed,
        "specification": specification,
        "question_ids": [question.id for question in questions],
    }
    identity = hashlib.sha256(canonical_json(identity_payload).encode("utf-8")).hexdigest()
    return Worksheet(identity, title, seed, specification, tuple(questions))