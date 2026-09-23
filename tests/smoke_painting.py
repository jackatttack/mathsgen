"""Small prototype smoke: purchasing, budget decisions and corrupted answers."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from copy import deepcopy
from dataclasses import replace
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import require
    from mathsgen.topic_browser import groups_for, topic_style
    generator = registry.get("problem_solving.painting.budget")
    winners = set()
    for level in range(1, 5):
        outcomes = set()
        for seed in range(20):
            q = generator.generate(seed, level)
            generator.validate_independently(q)
            require(q.to_dict() == generator.generate(seed, level).to_dict(), "Not reproducible")
            outcomes.add(q.answer["affordable"])
            if level == 4:
                winners.add(q.answer["winner"])
            corruptions = []
            wrong = deepcopy(q.answer)
            wrong["purchases"][0]["tins"] += 1
            corruptions.append(wrong)
            wrong = deepcopy(q.answer)
            wrong["purchases"][0]["cost_pence"] += 100
            corruptions.append(wrong)
            wrong = deepcopy(q.answer)
            wrong["affordable"] = not wrong["affordable"]
            corruptions.append(wrong)
            for wrong in corruptions:
                for check in (generator.validate, generator.validate_independently):
                    try:
                        check(replace(q, answer=wrong))
                    except ValueError:
                        pass
                    else:
                        raise AssertionError("Corrupted answer accepted")
        require(outcomes == {False, True}, "Missing budget outcome")
        sample = generator.generate(12345, level)
        print("Level", level, sample.prompt.text)
        print("Answer:", sample.answer_display.text)
    require(winners == {0, 1}, "Both paints should sometimes win")
    require(topic_style("problem_solving")[0] == "Problem solving", "Missing topic")
    require(
        any(g["topic"] == "problem_solving" for g in groups_for(registry.list())),
        "Missing browser group",
    )
    print("PASS: 80 questions; independent whole-tin enumeration, reproducibility,")
    print("budget/paint-choice coverage, corruption rejection and topic grouping.")


if __name__ == "__main__":
    main()