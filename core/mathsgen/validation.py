"""Bulk validation with bounded, reproducible failure reports."""
import time

from .core import canonical_json


def validate_many(generator, runs=1000, seed=0, difficulty=None, independent=False):
    """Cycle supported difficulties unless one is explicitly requested.

    Retain at most ten detailed failures while counting every failure.
    Independent validation is optional because symbolic solving costs time.
    """
    if type(runs) is not int or runs < 1:
        raise ValueError("runs must be a positive integer")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    difficulties = sorted(generator.info.difficulty_descriptions)
    if difficulty is not None:
        if difficulty not in difficulties:
            raise ValueError("Unsupported difficulty: {}".format(difficulty))
        difficulties = [difficulty]
    independent_check = getattr(generator, "validate_independently", None)
    if independent and not callable(independent_check):
        raise ValueError("This generator has no independent validator")

    started = time.monotonic()
    failed = 0
    failures = []
    counts = {str(level): 0 for level in difficulties}

    for index in range(runs):
        question_seed = seed + index
        level = difficulties[index % len(difficulties)]
        counts[str(level)] += 1
        try:
            question = generator.generate(question_seed, level)
            generator.validate(question)
            if independent:
                independent_check(question)
            repeated = generator.generate(question_seed, level)
            if canonical_json(question.to_dict()) != canonical_json(repeated.to_dict()):
                raise ValueError("Deterministic reproduction failed")
        except Exception as error:
            failed += 1
            if len(failures) < 10:
                failures.append({
                    "generator_id": generator.info.id,
                    "generator_version": generator.info.version,
                    "seed": question_seed,
                    "difficulty": level,
                    "settings": {},
                    "error": "{}: {}".format(type(error).__name__, error),
                })

    return {
        "generator_id": generator.info.id,
        "generator_version": generator.info.version,
        "runs": runs,
        "passed": runs - failed,
        "failed": failed,
        "difficulty_counts": counts,
        "independent": independent,
        "reproducibility_checked": True,
        "failure_examples": failures,
        "seconds": round(time.monotonic() - started, 3),
    }