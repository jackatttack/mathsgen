"""External circle chains: measured geometry, corruption and specimen."""
import sys
from pathlib import Path
from dataclasses import replace

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
for name in list(sys.modules):
    if name == "mathsgen" or name.startswith("mathsgen."):
        del sys.modules[name]


def main():
    from mathsgen.catalogue import build_registry
    from mathsgen.core import require
    from mathsgen import external_circle_contexts as forms
    from mathsgen.circle_figures import labels_clear, CHECK_WIDTHS
    from mathsgen.visuals import drawing_for
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    generator = build_registry().get("geometry.circle_theorems.multi_step")
    specimens = []
    for level in (3, 4):
        checked, seed, orientations = 0, 0, set()
        while checked < 40 and seed < 1000:
            q = generator.generate(seed, level)
            seed += 1
            if not forms.is_applied(q):
                continue
            generator.validate(q)
            generator.validate_independently(q)
            orientations.add(tuple(q.parameters["orientation"]))
            scene = q.visual_assets("questions")[0]
            require(labels_clear(scene), "Label crosses a line")
            for width in CHECK_WIDTHS:
                drawing_for(scene, width)
            for checker in (generator.validate, generator.validate_independently):
                bad = replace(q, answer=dict(q.answer, value=q.answer["value"] + 1))
                try:
                    checker(bad)
                except ValueError:
                    pass
                else:
                    raise ValueError("Wrong answer accepted")
            for key in ("centre_angle", "other_angle", "constant"):
                bad = replace(q, parameters=dict(q.parameters,
                              **{key: q.parameters[key] + 1}))
                try:
                    generator.validate(bad)
                except ValueError:
                    pass
                else:
                    raise ValueError("Changed given accepted: " + key)
            if checked < 3:
                print("L{}: {} -> {}".format(level, q.prompt.text, q.answer_display.text))
                specimens.append(q)
            checked += 1
        require(checked == 40, "Insufficient applied questions")
        require(len(orientations) >= 3, "Insufficient diagram variety")
        print("L{}: {} applied questions; {} orientations".format(
            level, checked, len(orientations)))
    destination = ROOT / "exports" / "specimens"
    destination.mkdir(parents=True, exist_ok=True)
    report = export_worksheet(Worksheet(
        id="external-circle-chain-v3", title="Circle theorems: outside angles",
        seed=20261002, specification={"specimens": True},
        questions=tuple(specimens)), destination, answers=True)
    print("Specimen:", report["directory"])
    print("PASS: external circle chains, both levels, measured givens and answers, "
          "corruption rejection, clearance, widths and PDF")


if __name__ == "__main__":
    main()