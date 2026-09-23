
"""Pythonista/Forge entrypoint; supply commands using Forge RUN's ARGS."""
import sys
from pathlib import Path


def main(argv=None):
    project_root = str(Path(__file__).resolve().parent.parent / "core")
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Refresh only this package so Forge executes edited source.
    for name in list(sys.modules):
        if name == "mathsgen" or name.startswith("mathsgen."):
            del sys.modules[name]

    from mathsgen.cli import main as run_cli
    return run_cli(argv)


if __name__ == "__main__":
    raise SystemExit(main())
