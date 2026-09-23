"""Stable project paths for scripts run from any subdirectory."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENGINE_ROOT = PROJECT_ROOT / "core" / "mathsgen"
TESTS_ROOT = PROJECT_ROOT / "tests"
DEV_ROOT = PROJECT_ROOT / "dev"
DOCS_ROOT = PROJECT_ROOT / "docs"
EXPORTS_ROOT = PROJECT_ROOT / "exports"
SPECS_ROOT = PROJECT_ROOT / "worksheet_specs"


def project_path(*parts):
    """Return an absolute path inside the MathsGen project."""
    return PROJECT_ROOT.joinpath(*parts)