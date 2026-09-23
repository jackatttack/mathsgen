"""Focused construction, validation and independent checks."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mathsgen.catalogue import build_registry
from mathsgen.quadratic_inequalities import QuadraticInequalities

generator = QuadraticInequalities()

for level in (1, 2, 3, 4):
    sample = generator.generate(20260922 + level, level)
    generator.validate_independently(sample)
    print("LEVEL", level)
    print("QUESTION:", sample.prompt.text)
    print("ANSWER:", sample.answer_display.text)

for level in (1, 2, 3, 4):
    for seed in range(250):
        question = generator.generate(seed, level)
        assert generator.validate(question)
        assert generator.validate_independently(question)
        assert generator.generate(seed, level) == question

registry = build_registry()
assert registry is not None, "Catalogue failed to build"

catalogue_source = (ROOT / "mathsgen" / "catalogue.py").read_text()
assert "from .quadratic_inequalities import QuadraticInequalities" in catalogue_source
assert "registry.register(QuadraticInequalities())" in catalogue_source

print("PASS: 1,000 quadratic inequalities; independent solution sets, "
      "difficulty constraints, determinism and catalogue registration")