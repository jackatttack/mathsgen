"""Focused capture–recapture checks; no PDF or UI dependency."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mathsgen.capture_recapture import CaptureRecapture
from mathsgen.catalogue import build_registry

generator = CaptureRecapture()
assert build_registry().get(generator.info.id).info.id == generator.info.id

for level in (1, 2, 3, 4):
    for seed in range(250):
        q = generator.generate(seed, difficulty=level)
        assert generator.validate(q)
        assert generator.validate_independently(q)
        assert generator.generate(seed, difficulty=level) == q
        assert q.answer["value"] > 0
    example = generator.generate(42, difficulty=level)
    print("LEVEL", level)
    print("QUESTION:", example.prompt.text)
    print("ANSWER:", example.answer_display.text)

print("PASS: 1,000 generated questions; validation, independent checks, "
      "deterministic regeneration and catalogue registration")