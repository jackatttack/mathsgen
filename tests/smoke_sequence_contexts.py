"""Check bare and worded arithmetic sequences across all four levels."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from launch_mathsgen import load_engine
from worded_smoke import run


def main():
    registry = load_engine()
    from mathsgen.catalogue import source_registry
    registry = source_registry(registry)
    run(registry, "algebra.sequences.linear_nth", {
        1: {"equation", "chair_rows"},
        2: {"equation", "linked_tables"},
        3: {"equation", "battery_readings"},
        4: {"equation", "travel_card"},
    }, "Arithmetic sequences: bare and worded forms",
        "sequence_contexts_specimen_")


if __name__ == "__main__":
    main()