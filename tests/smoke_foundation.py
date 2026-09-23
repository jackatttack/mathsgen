"""Run directly or through Forge. No PDF or user interface is opened."""
import json
import random
import sys
from dataclasses import replace
from pathlib import Path


def main():
    project_root = str(Path(__file__).resolve().parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Forge shares a process across runs. Reload only our own package so
    # this smoke checks the edited source rather than cached old modules.
    for name in list(sys.modules):
        if name == "mathsgen" or name.startswith("mathsgen."):
            del sys.modules[name]

    import sympy
    from mathsgen.catalogue import build_registry
    from mathsgen.core import canonical_json, require

    registry = build_registry()
    generator = registry.get("algebra.linear.two_sided")
    symbol = sympy.Symbol("x")
    original_random_state = random.getstate()
    checked = 0

    for difficulty in range(1, 5):
        examples = set()
        for seed in range(250):
            question = generator.generate(seed, difficulty)
            generator.validate(question)
            # The generator's own independent check understands every form
            # (bare, bracketed, fractional and worded).
            generator.validate_independently(question)
            first = canonical_json(question.to_dict())
            repeated = canonical_json(generator.generate(seed, difficulty).to_dict())
            require(first == repeated, "Generation is not deterministic")
            require(json.loads(first)["id"] == question.id, "JSON round trip failed")
            examples.add(question.prompt.text)
            checked += 1

        require(len(examples) > 150, "Unexpectedly low variation")
        sample = generator.generate(12345, difficulty)
        print("Difficulty {}: {}".format(difficulty, sample.prompt.text))
        print("  Answer: " + sample.answer_display.text)
        print("  Unique prompts from 250 seeds: {}".format(len(examples)))

    question = generator.generate(17, 3)
    wrong_answer = {
        "kind": "variable_values",
        "values": {"x": "999"},
    }
    try:
        generator.validate(replace(question, answer=wrong_answer))
    except ValueError:
        pass
    else:
        raise AssertionError("Validator accepted an incorrect answer")

    for seed, difficulty, settings in ((1, 0, None), (1, 5, None), (1, 1, {"typo": 1})):
        try:
            generator.generate(seed, difficulty, settings)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid generation request was accepted")

    require(random.getstate() == original_random_state, "Global RNG was modified")
    print("PASS: {} independent mathematical checks and reproducibility checks.".format(checked))
    print("PASS: corrupted-answer rejection, invalid requests and global RNG isolation.")
    print("PDF and device layout verification remain pending.")


if __name__ == "__main__":
    main()