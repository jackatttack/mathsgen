"""Check bare and worded quadratic sequences at all four levels."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from launch_mathsgen import load_engine
from worded_smoke import run


def main():
    registry = load_engine()
    run(registry, "algebra.sequences.quadratic_nth", {
        1: {"equation", "square_grid"},
        2: {"equation", "growing_rectangle"},
        3: {"equation", "changing_width"},
        4: {"equation", "game_peak"},
    }, "Quadratic sequences: bare and worded forms",
        "quadratic_sequence_contexts_specimen_")


if __name__ == "__main__":
    main()