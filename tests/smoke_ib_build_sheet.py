"""The Build sheet offers IB skills as a last, separate topic (no UI needed).

Checks: the sheet registry is GCSE plus IB; IB topics sort after every GCSE
topic; IB skills get board entries without grades; saved IB blocks survive
restore only through the sheet registry; a mixed GCSE + IB block sheet builds
and renders; the GCSE library sections still load from the GCSE registry.
"""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

import tempfile
from pathlib import Path
from types import SimpleNamespace


def main():
    from launch_mathsgen import load_engine
    gcse = load_engine()   # reloads the mathsgen package, so import after this
    from mathsgen.blocks import build_block_sheet
    from mathsgen.build_model import (
        default_block, drill_levels_by_skill, library_sections, usable_blocks,
    )
    from mathsgen.curriculum import load_level_tags
    from mathsgen.ib.catalogue import build_ib_registry, build_sheet_registry, library_entries
    from mathsgen.ib.common import TOPIC
    from mathsgen.pdf import render_pdf
    from mathsgen.topic_browser import groups_for, topic_style

    ib = build_ib_registry()
    sheet = build_sheet_registry(gcse)
    ib_ids = {info.id for info in ib.list()}
    assert len(sheet.list()) == len(gcse.list()) + len(ib_ids), "Sheet registry size"

    groups = groups_for(sheet.list())
    topics = [group["topic"] for group in groups]
    first_ib = topics.index(TOPIC)
    assert all(topic == TOPIC for topic in topics[first_ib:]), "IB must come last"
    assert topic_style(TOPIC)[0] == "IB Maths AI SL"
    print("IB groups:", [group["title"] for group in groups if group["topic"] == TOPIC])

    entries = library_entries(sheet)
    assert set(entries) == ib_ids and all(e["grades"] == [] for e in entries.values())

    library_sections(gcse, load_level_tags(gcse), drill_levels_by_skill(gcse))

    gcse_info = gcse.list()[0]
    ib_info = ib.list()[0]
    blocks = [dict(default_block(gcse_info), count=2), dict(default_block(ib_info), count=2)]
    assert len(usable_blocks(blocks, sheet)) == 2, "Sheet registry keeps both blocks"
    assert len(usable_blocks(blocks, gcse)) == 1, "GCSE registry drops the IB block"

    worksheet = build_block_sheet(sheet, usable_blocks(blocks, sheet), "Mixed check", 7)
    assert len(worksheet.questions) == 4
    export_root = Path(__file__).resolve().parent.parent / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="ib_build_sheet_", dir=str(export_root)))
    print(render_pdf(worksheet, directory / "questions.pdf", "questions"))
    print("PASS: IB on the Build sheet only, last topic, mixed sheet renders.")


if __name__ == "__main__":
    main()