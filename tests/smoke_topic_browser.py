"""Check grouping and real native view state without presenting a window."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from pathlib import Path
import tempfile

from launch_mathsgen import load_engine


def main():
    registry = load_engine()
    from mathsgen.core import require
    from mathsgen.topic_browser import groups_for, matches
    from mathsgen.worksheet_ui import WorksheetBuilder, make_spec

    infos = registry.list()
    groups = groups_for(infos)
    ids = [info.id for group in groups for info in group["infos"]]
    require(len(ids) == len(set(ids)) == len(infos), "Lost or duplicated skills")
    require(set(ids) == {info.id for info in infos}, "Registry coverage mismatch")
    require(all(matches(info, group["title"])
                for group in groups for info in group["infos"]), "Group search failed")

    with tempfile.TemporaryDirectory() as folder:
        view = WorksheetBuilder(registry, Path(folder))
        view.frame = (0, 0, 390, 844)
        view.layout()
        require(all(row.hidden for _, row, _, _, _ in view.rows),
                "New browser should start collapsed")
        group = groups[0]
        header = view.group_headers[group["key"]][0]
        view.toggle_group(header)
        require(all(not view.row_lookup[info.id][1].hidden for info in group["infos"]),
                "Expansion failed")
        chosen = group["infos"][0].id
        view.toggle_generator(view.row_lookup[chosen][1])
        view.toggle_group(header)
        require(chosen in view.selected and view.row_lookup[chosen][1].hidden,
                "Collapse changed selections")
        require(view.group_headers[group["key"]][2].text.startswith("1/"),
                "Collapsed selection count missing")

        view.search_field.text = "perpendicular"
        view.textfield_did_change(view.search_field)
        expected = {info.id for info in infos if matches(info, "perpendicular")}
        require(bool(expected), "Search fixture found nothing")
        displayed = {info.id for info, row, _, _, _ in view.rows if not row.hidden}
        require(displayed == expected, "Search displayed the wrong skills")
        before = set(view.selected)
        view.select_everything(view.select_all)
        require(view.selected == before | expected, "Filtered select-all lost selections")

        view.search_field.text = "zzzz-no-skill"
        view.refresh()
        require(not view.empty_label.hidden, "Missing empty-search message")
        require(view.selected == before | expected, "Search changed selections")
        view.clear_search(None)

        spec = make_spec(registry, view.selected, 3, {1, 2}, "Browser test", False)
        require({s["generator_ids"][0] for s in spec["sections"]} == view.selected,
                "Hidden selections missing from worksheet specification")

        view.expanded_groups.add(group["key"])
        view.save()
        restored = WorksheetBuilder(registry, Path(folder))
        restored.frame = (0, 0, 320, 700)
        restored.layout()
        require(restored.selected == view.selected, "Selections failed to restore")
        require(restored.expanded_groups == view.expanded_groups, "Expansion failed to restore")
        require(all(row.x >= 0 and row.x + row.width <= restored.width
                    for _, row, _, _, _ in restored.rows if not row.hidden),
                "Visible row outside narrow screen")

    print("PASS: {} skills in {} groups, with complete registry coverage.".format(
        len(infos), len(groups)
    ))
    print("PASS: collapse, search, filtered selection and hidden selection preservation.")
    print("PASS: settings restore and narrow-screen row bounds.")
    print("Device check: launch_mathsgen.py; expand a group, search, select and clear search.")


if __name__ == "__main__":
    main()