"""Check launcher logic without opening its interface."""
import copy
from pathlib import Path
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from launch_mathsgen import (
    default_setup, load_engine, parse_levels, read_json,
    validate_setup, worksheet_spec, write_json,
)


def main():
    registry = load_engine()
    from mathsgen.core import require
    from mathsgen.worksheets import build_worksheet

    infos = registry.list()
    require(len(infos) >= 8, "Expected existing generators")
    setup = default_setup()
    setup["seed"] = "12345"
    setup["sections"] = [
        {
            "generator_ids": [info.id],
            "count": 2,
            "difficulties": [min(info.difficulty_descriptions)],
        }
        for info in infos
    ]
    validate_setup(setup, registry)
    worksheet = build_worksheet(worksheet_spec(setup), 12345, registry)
    require(len(worksheet.questions) == 2 * len(infos), "Incorrect total")
    for question in worksheet.questions:
        registry.get(question.generator_id).validate_independently(question)
    require(parse_levels("1,3:4", {1, 2, 3, 4}) == [1, 3, 4], "Level parsing failed")

    bad = copy.deepcopy(setup)
    bad["sections"][0]["generator_ids"] = ["missing.generator"]
    try:
        validate_setup(bad, registry)
    except ValueError:
        pass
    else:
        raise AssertionError("Unavailable generator was accepted")

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "setup.json"
        write_json(path, setup)
        require(read_json(path) == setup, "Saved setup round trip failed")
        changed = copy.deepcopy(setup)
        changed["title"] = "Another lesson"
        write_json(path, changed)
        require(read_json(path) == changed, "Settings replacement failed")

    print("PASS: discovered {} generators from the registry.".format(len(infos)))
    print("PASS: mixed selections, counts and independent answer checks.")
    print("PASS: difficulty parsing, missing-generator rejection and saved settings.")
    print("Next: run launch_mathsgen.py directly in Pythonista to check the interface.")


if __name__ == "__main__":
    main()