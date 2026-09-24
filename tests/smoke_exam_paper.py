"""Exam papers: exact marks, tier grades, calculator rules, ordering and PDFs."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

import tempfile
from pathlib import Path

from launch_mathsgen import load_engine


SEEDS = (0, 1)
SPECIMENS = (("foundation", 1), ("higher", 2))


def main():
    registry = load_engine()
    from mathsgen import exam_paper
    from mathsgen.pdf import render_pdf

    blueprint = exam_paper.load_blueprint()
    facts, paper1 = {}, set()
    for info in registry.list():
        flags = exam_paper.paper1_flags(info, blueprint)
        for (level, grade, needs), only in zip(exam_paper.level_facts(info, blueprint), flags):
            facts[(info.id, level)] = (grade, needs)
            if only:
                paper1.add((info.id, level))

    for tier in ("foundation", "higher"):
        low, high = blueprint["tiers"][tier]["grades"]
        for paper in (1, 2, 3):
            for seed in SEEDS:
                sheet = exam_paper.build_exam_paper(registry, tier, paper, seed, blueprint)
                questions = sheet.questions
                assert sum(q.marks for q in questions) == blueprint["paper_marks"], "Marks"
                grades = [facts[(q.generator_id, q.difficulty)][0] for q in questions]
                assert all(low <= g <= high for g in grades), "Grade outside tier"
                assert grades == sorted(grades), "Not ordered by grade"
                if not blueprint["calculator_papers"][str(paper)]:
                    assert not any(facts[(q.generator_id, q.difficulty)][1]
                                   for q in questions), "Calculator question on paper 1"
                else:
                    assert not any((q.generator_id, q.difficulty) in paper1
                                   for q in questions), "Paper-1-only question on a calculator paper"
                calc_marks = sum(q.marks for q in questions
                                 if facts[(q.generator_id, q.difficulty)][1])
                long_questions = sum(q.marks >= exam_paper.LONG_QUESTION_MARKS
                                     for q in questions)
                assert long_questions >= exam_paper.MINIMUM_LONG_QUESTIONS[tier], "Too few long"
                again = exam_paper.build_exam_paper(registry, tier, paper, seed, blueprint)
                assert [q.id for q in again.questions] == [q.id for q in questions], "Not reproducible"
                spec = sheet.specification
                print("{} P{} s{}: {} questions, {} long, {} calc marks | strands {} vs {} | grades {}".format(
                    tier[0].upper(), paper, seed, len(questions), long_questions, calc_marks,
                    spec["strand_marks"], spec["strand_targets"], spec["grade_marks"]))

    export_root = Path(__file__).resolve().parent.parent / "exports"
    export_root.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="exam_paper_specimen_", dir=str(export_root)))
    for tier, paper in SPECIMENS:
        sheet = exam_paper.build_exam_paper(registry, tier, paper, 0, blueprint)
        print(sheet.title)
        for number, q in enumerate(sheet.questions, 1):
            print("  {:>2}. [{}m] {} L{}".format(number, q.marks, q.generator_id, q.difficulty))
        for mode in ("questions", "answers"):
            print(render_pdf(sheet, directory / "{}_p{}_{}.pdf".format(tier, paper, mode), mode))
    print("PASS: six paper types x two seeds, exact marks, grades, calculator rules, order.")


if __name__ == "__main__":
    main()