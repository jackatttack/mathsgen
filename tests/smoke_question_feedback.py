"""Portable feedback tests: no iCloud writes, clipboard or Pythonista UI."""
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from launch_mathsgen import load_engine


def main():
    from mathsgen.core import require
    from mathsgen.question_actions import (
        action_url, available_actions, encode_question, source_question,
    )
    from mathsgen.question_feedback import flag_question, question_key

    registry = load_engine()
    generator = registry.get("algebra.quadratic.factorisable_monic")
    original = generator.generate(seed=20260922, difficulty=1)
    source = source_question(encode_question(original), registry)

    require(("flag", "Flag") in available_actions(source),
            "Flag action is missing from the question heading")
    require("pythonista3://" in action_url(source, "flag"),
            "Flag action URL was not generated")

    with tempfile.TemporaryDirectory(prefix="mathsgen_feedback_") as folder:
        database = Path(folder) / "feedback" / "questions.sqlite3"
        require(not database.exists(), "Unexpected existing feedback database")

        first = flag_question(source, database)
        require(first == (True, 1), "First flag was not inserted")
        require(database.exists(), "Feedback database was not created")

        second = flag_question(source, database)
        require(second == (False, 2), "Repeated flag was not counted")

        other = generator.generate(seed=20260923, difficulty=1)
        require(question_key(source) != question_key(other),
                "Different questions have the same feedback identity")
        require(flag_question(other, database) == (True, 1),
                "Second question was not saved independently")

        with sqlite3.connect(str(database)) as connection:
            rows = connection.execute("""
                SELECT question_key, generator_id, seed, difficulty,
                       question_snapshot, tap_count, status
                FROM question_flags ORDER BY seed
            """).fetchall()

        require(len(rows) == 2, "Expected two distinct flagged questions")
        require(rows[0][0] == question_key(source),
                "Source question identity was not preserved")
        require(rows[0][1] == source.generator_id,
                "Generator ID was not preserved")
        require(rows[0][2] == source.seed and rows[0][3] == source.difficulty,
                "Seed or difficulty was not preserved")
        require(rows[0][5] == 2 and rows[0][6] == "open",
                "Flag count or review status is incorrect")

        import json
        snapshot = json.loads(rows[0][4])
        require(snapshot["prompt"]["text"] == source.prompt.text,
                "Question text was not preserved")
        require(snapshot["answer_display"]["text"] == source.answer_display.text,
                "Answer was not preserved")

    print("PASS: Flag link appears in the question heading")
    print("PASS: exact question and answer stored persistently")
    print("PASS: repeat taps counted; different questions kept separate")
    print("PASS: test used temporary storage; no clipboard or iCloud writes")


if __name__ == "__main__":
    main()