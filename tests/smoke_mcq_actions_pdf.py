"""Check MCQ links and regeneration, then export a small device specimen."""
import base64
from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
for name in list(sys.modules):
    if name == "mathsgen" or name.startswith("mathsgen."):
        del sys.modules[name]

from mathsgen.blocks import build_block_sheet
from mathsgen.catalogue import build_registry
from mathsgen.core import canonical_json, require
from mathsgen.export import export_worksheet
from mathsgen.multiple_choice import validate_multiple_choice
from mathsgen.new_question_session import NewQuestionSession
from mathsgen.question_actions import (
    content_digest, decode_question, encode_question, new_question, source_question,
)


def main():
    registry = build_registry()
    blocks = [
        {"generator_id": generator_id, "kind": "questions", "levels": [1, 2],
         "count": 2, "multiple_choice": True}
        for generator_id in (
            "number.fractions.addition",
            "number.fractions.multiplication",
            "number.fractions.division",
            "number.percentages.of_amount",
            "algebra.substitution.values",
        )
    ]
    sheet = build_block_sheet(registry, blocks, "Choose one answer", seed=10321)
    for question in sheet.questions:
        token = encode_question(question)
        recovered = source_question(token, registry)
        require(recovered == question, "Link did not reproduce exact MCQ")
        require(decode_question(token)["schema"] == 2, "MCQ link has wrong schema")
        seeds = iter(range(1000, 1200))
        fresh = new_question(question, registry, seed_source=lambda: next(seeds))
        require(bool(fresh.choices), "+ New lost MCQ mode")
        require(content_digest(fresh, True) != content_digest(question, True),
                "+ New repeated the source question")
        validate_multiple_choice(fresh, registry.get(fresh.generator_id))
        require(source_question(encode_question(fresh), registry) == fresh,
                "New MCQ does not round-trip")
        reversed_options = replace(question, choices=tuple(reversed(question.choices)))
        require(content_digest(reversed_options, True) == content_digest(question, True),
                "Option order disguises repeated mathematics")
        require(content_digest(reversed_options) != content_digest(question),
                "Exact display checksum ignores order")
        data = decode_question(token)
        data["display"] = "0" * 64
        broken = base64.urlsafe_b64encode(canonical_json(data).encode("utf-8")).decode("ascii")
        try:
            source_question(broken, registry)
        except ValueError:
            pass
        else:
            raise AssertionError("Corrupted display checksum accepted")

    ordinary = registry.get("number.fractions.addition").generate(12, 1)
    require(decode_question(encode_question(ordinary))["schema"] == 1,
            "Ordinary link compatibility lost")
    require(source_question(encode_question(ordinary), registry) == ordinary,
            "Ordinary link no longer works")
    percent = next(q for q in sheet.questions
                   if q.generator_id == "number.percentages.of_amount")
    session = NewQuestionSession(
        percent, registry, encode_question(percent),
        Path(tempfile.gettempdir()) / "mathsgen_mcq_session_smoke")
    require(session.levels == (1, 2), "New session advertises unsupported MCQ levels")

    result = export_worksheet(sheet, ROOT / "exports" / "specimens", answers=True)
    print("MCQ links, regeneration, difficulty limits and legacy links PASS")
    print(json.dumps(result, indent=2))
    print("MCQ PDF EXPORT PASS — visual review pending")


if __name__ == "__main__":
    main()