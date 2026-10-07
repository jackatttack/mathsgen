"""Exercise current inequality routes and reproducible worksheet actions."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "tests"))
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from smoke_dispatch_families import check_family
    from mathsgen.question_actions import (
        encode_question, source_question, new_question, content_digest,
    )
    generator = registry.get("algebra.inequalities.linear")
    assert generator.info.version == 4
    check_family(generator, [])
    seen = set()
    for seed in range(40):
        q = generator.generate(seed, 4)
        seen.add((q.parameters["source"], q.parameters["source_level"]))
        restored = source_question(encode_question(q), registry)
        assert restored.to_dict() == q.to_dict()
        seeds = iter(range(1000 + seed * 100, 1100 + seed * 100))
        fresh = new_question(q, registry, seed_source=lambda: next(seeds))
        assert fresh.generator_id == q.generator_id
        assert fresh.difficulty == q.difficulty
        assert content_digest(fresh, True) != content_digest(q, True)
        generator.validate(fresh)
        assert source_question(encode_question(fresh), registry).to_dict() == fresh.to_dict()
    assert seen == set(generator.routes[4])
    print("PASS: all inequality family routes, corruption checks,")
    print("40 source reconstructions and 40 New-question round trips.")


if __name__ == "__main__":
    main()