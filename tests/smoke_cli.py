"""Check machine-readable CLI behaviour and validation failure reporting."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

import contextlib
import io
import json

from mathsgen_cli import main as run_cli


def request(arguments):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        status = run_cli(arguments)
    return status, json.loads(output.getvalue())


def main():
    generator_id = "algebra.linear.two_sided"
    status, result = request(["topics", "--json"])
    assert status == 0 and {"algebra", "ratio"}.issubset(result["topics"])

    status, result = request(["generators", "algebra", "--json"])
    assert status == 0
    assert generator_id in [item["id"] for item in result["generators"]]

    arguments = [
        "sample", generator_id, "--count", "3",
        "--difficulty", "3", "--seed", "42", "--json",
    ]
    status, result = request(arguments)
    assert status == 0
    assert [item["seed"] for item in result["questions"]] == [42, 43, 44]
    assert request(arguments) == (status, result)

    status, result = request(["sample", generator_id, "--difficulty", "99", "--json"])
    assert status == 2 and "error" in result

    status, result = request(["info", "missing.generator", "--json"])
    assert status == 2 and "error" in result

    # Import after the final entrypoint refresh to use the current modules.
    from mathsgen.catalogue import build_registry
    from mathsgen.validation import validate_many

    actual = build_registry().get(generator_id)

    class BrokenGenerator:
        info = actual.info

        def generate(self, seed, difficulty):
            raise ValueError("Deliberate test failure")

    report = validate_many(BrokenGenerator(), runs=12, seed=100)
    assert report["failed"] == 12
    assert len(report["failure_examples"]) == 10
    assert report["failure_examples"][0]["seed"] == 100
    assert report["difficulty_counts"] == {"1": 3, "2": 3, "3": 3, "4": 3}
    print("PASS: CLI JSON, seed sequencing, reproducibility and request errors.")
    print("PASS: bulk validation counts failures and bounds reproducible reports.")


if __name__ == "__main__":
    main()