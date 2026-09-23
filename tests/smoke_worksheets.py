"""Exercise real mixed worksheets, balancing, reproducibility and rejection."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

import contextlib
import io
import json
from collections import Counter

from mathsgen_cli import main as run_cli


def main():
    command = [
        "worksheet", "--spec", "worksheet_specs/pipeline_demo.json",
        "--seed", "20260918", "--json",
    ]

    def request():
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = run_cli(command)
        if status:
            raise AssertionError(output.getvalue())
        return json.loads(output.getvalue())

    first = request()
    assert request() == first
    questions = first["questions"]
    assert len(questions) == 12
    assert Counter(question["topic"] for question in questions) == {
        "algebra": 6, "ratio": 6,
    }
    for topic in ("algebra", "ratio"):
        assert Counter(
            question["difficulty"] for question in questions
            if question["topic"] == topic
        ) == {2: 2, 3: 2, 4: 2}
    assert len({question["prompt"]["text"] for question in questions}) == 12

    from mathsgen.worksheets import build_worksheet, quick_spec
    from mathsgen.catalogue import build_registry

    registry = build_registry()
    spec = quick_spec(count=21, difficulty="2:4", profile="pipeline-demo")
    for seed in range(20):
        worksheet = build_worksheet(spec, seed)
        assert len(worksheet.questions) == 21
        assert len({q.prompt.text for q in worksheet.questions}) == 21
        for question in worksheet.questions:
            registry.get(question.generator_id).validate_independently(question)

    bad_specs = [
        {"sections": [{"topic": "geometry", "count": 2}]},
        {"sections": [{"topic": "ratio", "count": 0}]},
        {"sections": [{"topic": "ratio", "count": 2, "dificulties": [2]}]},
        {"sections": [{"topic": "ratio", "count": 2, "difficulties": [9]}]},
    ]
    for specification in bad_specs:
        try:
            build_worksheet(specification)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid worksheet specification was accepted")

    print("PASS: worksheet CLI and JSON reproduction.")
    print("PASS: exact topic quotas, balanced levels and no duplicate prompts.")
    print("PASS: 420 independent solution checks across 20 mixed worksheets.")
    print("PASS: unavailable coverage, invalid counts and specification typos rejected.")


if __name__ == "__main__":
    main()