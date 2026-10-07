"""Focused sequence dispatch and portable question-action integration checks."""
import sys
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "tests"))
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from smoke_dispatch_families import check_family
    from mathsgen.sequence_practice import (
        ArithmeticSequences, QuadraticSequences, GeometricSequenceFamily,
    )
    from mathsgen.question_actions import (
        encode_question, source_question, new_question, content_digest,
    )
    for family in (ArithmeticSequences, QuadraticSequences, GeometricSequenceFamily):
        check_family(family(), [])
    print("PASS: current sequence dispatch routes and corruption checks.")

    identifiers = (
        "algebra.sequences.linear_nth",
        "algebra.sequences.quadratic_nth",
        "algebra.sequences.geometric",
        "algebra.linear.two_sided",
        "ratio.changing.algebra",
    )
    count = 0
    for identifier in identifiers:
        generator = registry.get(identifier)
        for level in (1, 2, 3, 4):
            for seed in range(4):
                original = generator.generate(seed, level)
                restored = source_question(encode_question(original), registry)
                assert restored.to_dict() == original.to_dict()
                seeds = iter(range(1000, 1100))
                fresh = new_question(original, registry, seed_source=lambda: next(seeds))
                assert fresh.generator_id == original.generator_id
                assert fresh.difficulty == original.difficulty
                assert content_digest(fresh, True) != content_digest(original, True)
                generator.validate(fresh)
                assert source_question(
                    encode_question(fresh), registry).to_dict() == fresh.to_dict()
                count += 1
            if generator.info.version > 1:
                stale = replace(original, generator_version=generator.info.version - 1)
                try:
                    source_question(encode_question(stale), registry)
                except ValueError as error:
                    assert "Generate a new worksheet" in str(error)
                else:
                    raise AssertionError("Old generator-version link was accepted")
    print("PASS: {} source/answer reconstructions and New round trips.".format(count))
    print("PASS: changed-version links give the expected regeneration message.")
    print("Physical clipboard and UI interactions still need device review.")


if __name__ == "__main__":
    main()