"""Mini paper: allocation, balance, reproducibility, ordering, preview, UI mode."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from collections import Counter
from itertools import combinations
import tempfile

from launch_mathsgen import load_engine


ALL_LEVELS = [1, 2, 3, 4]


def expect_error(action, label):
    try:
        action()
    except ValueError as error:
        print("  {} -> {}".format(label, error))
        return
    raise AssertionError(label + " was accepted")


def main():
    registry = load_engine()
    from mathsgen.core import require
    from mathsgen.mini_paper import build_mini_paper, level_allocation

    require(level_allocation(12, ALL_LEVELS) == {1: 2, 2: 4, 3: 4, 4: 2},
            "12 questions over four levels should be 2/4/4/2")
    for size in range(1, 5):
        for levels in combinations(ALL_LEVELS, size):
            for total in range(1, 41):
                counts = level_allocation(total, list(levels))
                require(sum(counts.values()) == total, "Allocation changed the total")
    print("allocation exact for every level subset, totals 1-40")

    subjects = sorted({info.topic for info in registry.list()})
    pool_size = len(registry.list())
    for total in (1, 5, 12, 20):
        for seed in range(3):
            paper = build_mini_paper(registry, total, ALL_LEVELS, subjects, "Mini", seed)
            qs = paper.questions
            require(len(qs) == total, "Wrong question count")
            difficulties = [q.difficulty for q in qs]
            require(difficulties == sorted(difficulties), "Not easier to harder")
            expected = {k: v for k, v in level_allocation(total, ALL_LEVELS).items() if v}
            require(dict(Counter(difficulties)) == expected, "Level split mismatch")
            ids = [q.generator_id for q in qs]
            if total <= pool_size:
                require(len(set(ids)) == total, "Repeated a generator unnecessarily")
            spread = Counter(q.topic for q in qs)
            if total >= len(subjects):
                require(
                    len(spread) == len(subjects)
                    and max(spread.values()) - min(spread.values()) <= 1,
                    "Subjects unbalanced: {}".format(dict(spread)),
                )
            again = build_mini_paper(registry, total, ALL_LEVELS, subjects, "Mini", seed)
            require([q.id for q in again.questions] == [q.id for q in qs], "Not reproducible")
    print("papers of 1/5/12/20: count, levels, balance, variety, order, reproducibility")

    paper = build_mini_paper(registry, 12, ALL_LEVELS, subjects, "Mini", 0)
    print("sample 12-question paper (seed 0):")
    for q in paper.questions:
        print("  L{} {:16} {}".format(q.difficulty, q.topic, q.generator_id))

    narrow = build_mini_paper(registry, 8, ALL_LEVELS, ["problem_solving"], "Mini", 1)
    require(len(narrow.questions) == 8, "Repeat case lost questions")
    adjacent = sum(a.generator_id == b.generator_id
                   for a, b in zip(narrow.questions, narrow.questions[1:]))
    print("problem solving only, 8 questions: generators {}, adjacent repeats {}".format(
        dict(Counter(q.generator_id for q in narrow.questions)), adjacent))

    print("error explanations:")
    expect_error(lambda: build_mini_paper(registry, 5, ALL_LEVELS, [], "Mini", 0), "no subjects")
    expect_error(lambda: build_mini_paper(registry, 5, ALL_LEVELS, ["nonsense"], "Mini", 0), "unknown subject")
    expect_error(lambda: build_mini_paper(registry, 0, ALL_LEVELS, subjects, "Mini", 0), "zero total")

    from mathsgen.preview import create_preview
    report = create_preview(paper, answers=True)
    print("preview: {} questions; {}".format(
        report["question_count"], [(item["mode"], item.get("pages")) for item in report["pdfs"]]))

    from mathsgen.worksheet_ui import WorksheetBuilder
    view = WorksheetBuilder(registry, tempfile.mkdtemp())
    view.frame = (0, 0, 390, 844)
    view.mode_control.selected_index = 1
    view.change_mode(view.mode_control)
    require(view.count_field.text == "12", "Mini total should default to 12")
    require(view.generate_button.title == "Generate mini paper", "Wrong button title")
    require(view.count_label.text == "Total questions", "Wrong count label")
    require(all(not row.hidden for row, _, _, _ in view.subject_rows.values()), "Subjects hidden")
    require(all(row.hidden for _, row, _, _, _ in view.rows), "Skill rows visible")
    require(view.order.hidden and not view.order_note.hidden, "Order control not replaced")
    view.mode_control.selected_index = 0
    view.change_mode(view.mode_control)
    require(view.count_field.text == "5", "Per-type count not preserved")
    require(view.generate_button.title == "Generate preview", "Button title not restored")
    print("UI mode switch: counts, labels, subject rows and order note")
    print("PASS: mini paper selection, ordering, errors, preview and UI mode.")


if __name__ == "__main__":
    main()