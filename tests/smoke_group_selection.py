"""Exercise group selection with real Pythonista controls and temporary settings."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from tempfile import TemporaryDirectory
from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.worksheet_ui import WorksheetBuilder

    with TemporaryDirectory() as directory:
        view = WorksheetBuilder(registry, directory)
        view.frame = (0, 0, 390, 844)
        group = next(g for g in view.groups
                     if any("circle_theorems" in i.id for i in g["infos"]))
        ids = {i.id for i in group["infos"]}
        outside = next(i.id for i in view.infos if i.id not in ids)
        control = view.group_selection_buttons[group["key"]]
        view.selected = {outside}
        view.refresh()

        control.action(control)
        assert view.selected == ids | {outside}
        assert group["key"] not in view.expanded_groups
        assert control.title == "Clear"
        control.action(control)
        assert view.selected == {outside}

        target = group["infos"][0].id
        view.selected = ids | {outside}
        view.search_field.text = target.replace("_", " ")
        view.refresh()
        assert control.title == "Clear shown"
        control.action(control)
        assert view.selected == (ids - {target}) | {outside}
        assert control.title == "All shown"
        control.action(control)
        assert view.selected == ids | {outside}

        restored = WorksheetBuilder(registry, directory)
        assert restored.selected == view.selected

        view.search_field.text = ""
        for width in (320, 390, 768):
            view.frame = (0, 0, width, 900)
            view.refresh()
            header = view.group_headers[group["key"]][0]
            assert header.x + header.width <= control.x
            assert control.x + control.width <= width
            assert control.height >= 44

    print("PASS: group select/clear, search isolation, unrelated selections,")
    print("collapsed groups, settings restore and control frames.")
    print("Native text fit and tap behaviour still need a launcher check.")


if __name__ == "__main__":
    main()