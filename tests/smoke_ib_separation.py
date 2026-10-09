"""IB and GCSE stay separate content models.

Fails if any IB generator reaches the GCSE registry (and so GCSE papers,
drills, quick start or curriculum tags), or if the IB registry contains
anything that is not IB.
"""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))


def main():
    from launch_mathsgen import load_engine
    from mathsgen.catalogue import build_registry
    from mathsgen.curriculum import load_level_tags
    from mathsgen.ib.catalogue import build_ib_registry
    from mathsgen.ib.common import TOPIC

    gcse, engine, ib = build_registry(), load_engine(), build_ib_registry()
    for label, registry in (("build_registry", gcse), ("load_engine", engine)):
        leaked = [info.id for info in registry.list()
                  if info.id.startswith(TOPIC) or info.topic == TOPIC]
        assert not leaked, "{} contains IB generators: {}".format(label, leaked)

    ib_infos = ib.list()
    assert ib_infos, "IB registry is empty"
    for info in ib_infos:
        assert info.id.startswith(TOPIC + ".") and info.topic == TOPIC, info.id
    overlap = {info.id for info in ib_infos} & {info.id for info in gcse.list()}
    assert not overlap, overlap

    load_level_tags(gcse)  # raises if the GCSE registry gained an untagged generator
    print("PASS: {} IB generators, {} GCSE generators, no overlap or leak.".format(
        len(ib_infos), len(gcse.list())))


if __name__ == "__main__":
    main()