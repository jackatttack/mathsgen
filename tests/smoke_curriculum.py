"""Smoke: quick-start selection by year group and grade band.

Sweeps every year group and grade band against every single topic and all
topics together. Checks counts, filters, easier-first order, determinism and
topic balance, generates real questions from one spec, and reports how many
distinct skills each Year 7 topic offers.
"""
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from launch_mathsgen import load_engine
from mathsgen import curriculum

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def tag_lookup(level_tags):
    return {(tag.generator_id, tag.level): tag for tag in level_tags}


def check_spec(spec, count, lookup, label, year=None, grades=None, topics=()):
    sections = spec["sections"]
    check(sum(s["count"] for s in sections) == count, label + ": wrong total")
    previous = None
    for section in sections:
        tag = lookup[(section["generator_ids"][0], section["difficulties"][0])]
        check(tag.topic in topics, label + ": off-topic " + tag.generator_id)
        if year is not None:
            check(year - curriculum.RECAP_YEARS <= tag.year <= year,
                  label + ": wrong year " + tag.generator_id)
        if grades is not None:
            check(grades[0] <= tag.grade <= grades[1],
                  label + ": wrong grade " + tag.generator_id)
        if previous is not None:
            check((previous.year, previous.grade) <= (tag.year, tag.grade),
                  label + ": not easier first")
        previous = tag


def main():
    registry = load_engine()
    level_tags = curriculum.load_level_tags(registry)
    lookup = tag_lookup(level_tags)
    total_levels = sum(len(info.difficulty_descriptions) for info in registry.list())
    check(len(level_tags) == total_levels, "level tags do not cover every level")
    topics = sorted({tag.topic for tag in level_tags})

    choices = [("Y{}".format(year), {"year": year}) for year in curriculum.YEAR_GROUPS]
    choices += [(name, {"grades": band}) for name, band in curriculum.GRADE_BANDS.items()]
    built = empty = 0
    for label, choice in choices:
        for topic_set in [[topic] for topic in topics] + [topics]:
            name = "{} {}".format(label, "+".join(topic_set))
            try:
                spec = curriculum.quick_start_spec(
                    registry, topic_set, 12, "Starter", seed=7,
                    level_tags=level_tags, **choice)
            except ValueError as error:
                check("No questions suit" in str(error), name + ": " + str(error))
                empty += 1
                continue
            built += 1
            check_spec(spec, 12, lookup, name, topics=topic_set, **choice)

    first = curriculum.quick_start_spec(
        registry, ["algebra", "number"], 20, "Y10 mix", seed=3, year=10,
        level_tags=level_tags)
    again = curriculum.quick_start_spec(
        registry, ["algebra", "number"], 20, "Y10 mix", seed=3, year=10,
        level_tags=level_tags)
    check(first == again, "same seed gave a different spec")
    per_topic = Counter()
    for section in first["sections"]:
        per_topic[lookup[(section["generator_ids"][0],
                          section["difficulties"][0])].topic] += section["count"]
    check(per_topic["algebra"] == per_topic["number"] == 10,
          "topics not balanced: " + str(dict(per_topic)))

    generated = 0
    for index, section in enumerate(first["sections"]):
        generator = registry.get(section["generator_ids"][0])
        for offset in range(section["count"]):
            generator.generate(index * 100 + offset, section["difficulties"][0])
            generated += 1

    print("Level tags:", len(level_tags))
    print("Quick-start specs built: {}, empty choices: {}".format(built, empty))
    print("Questions generated from Y10 algebra+number:", generated)
    print("Distinct Year 7 skills per topic:")
    for topic in topics:
        pool = curriculum.suitable_levels(level_tags, {topic}, year=7)
        print("  {:<16}{}".format(topic, len({tag.generator_id for tag in pool})))
    for failure in failures:
        print("FAIL", failure)
    print("RESULT:", "FAIL" if failures else "PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())