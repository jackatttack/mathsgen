"""Frequency-tree mathematics, calibration, diagrams and registration."""
from fractions import Fraction
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mathsgen.catalogue import build_registry
from mathsgen.frequency_trees import (
    FrequencyTrees, counts, hidden_for, diagram,
)

generator = FrequencyTrees()
assert build_registry().get(generator.info.id).info.id == generator.info.id

expected_hidden = {
    2: ("a", "a1"),
    4: ("a", "a2"),
}

for level in (1, 2, 3, 4):
    for seed in range(250):
        q = generator.generate(seed, difficulty=level)
        p = q.parameters
        values = counts(p)
        assert generator.validate(q)
        assert generator.validate_independently(q)
        assert generator.generate(seed, difficulty=level) == q
        assert values["a1"] + values["a2"] == values["a"]
        assert values["b1"] + values["b2"] == values["b"]
        assert values["a"] + values["b"] == values["total"]

        hidden = hidden_for(level, p)
        if level in expected_hidden:
            assert hidden == expected_hidden[level]
        else:
            assert len(hidden) == 1

        student = diagram(p, level, student=True)
        teacher = diagram(p, level, student=False)
        student_labels = [
            node["text"] for node in student["nodes"]
            if node["type"] == "label"
        ]
        teacher_labels = [
            node["text"] for node in teacher["nodes"]
            if node["type"] == "label"
        ]
        assert student_labels.count("") == len(hidden)
        assert "" not in teacher_labels

        if level == 4:
            conditional = Fraction(values["a1"], values["a"])
            assert values["a1"] / conditional == values["a"]
            assert q.answer["value"] == str(
                Fraction(values["b1"], values["total"]).numerator
            ) if Fraction(values["b1"], values["total"]).denominator == 1 else (
                q.answer["value"] == "{}/{}".format(
                    Fraction(values["b1"], values["total"]).numerator,
                    Fraction(values["b1"], values["total"]).denominator,
                )
            )

    example = generator.generate(42, difficulty=level)
    print("LEVEL", level)
    print("QUESTION:", example.prompt.text)
    print("ANSWER:", example.answer_display.text)
    print("HIDDEN:", hidden_for(level, example.parameters))

print("PASS: 1,000 frequency trees; maths, calibration, diagram counts, "
      "determinism and catalogue registration")