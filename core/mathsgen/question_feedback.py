"""Fast, persistent, question-specific feedback capture.

The database is kept outside exports and temporary action workspaces.
No Pythonista, PDF, clipboard or generator imports are needed here.
"""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

from .core import canonical_json, require


def feedback_database(project_root):
    return Path(project_root) / "feedback" / "questions.sqlite3"


def question_key(question):
    """Stable identity for the exact generated question and its presentation."""
    identity = {
        "generator_id": question.generator_id,
        "generator_version": question.generator_version,
        "seed": question.seed,
        "difficulty": question.difficulty,
        "settings": question.settings,
        "question_id": question.id,
        "prompt": asdict(question.prompt),
        "question_visuals": question.visual_assets("questions"),
        "choices": [asdict(choice) for choice in question.choices],
    }
    return hashlib.sha256(
        canonical_json(identity).encode("utf-8")
    ).hexdigest()


def flag_question(question, database_path):
    """Save one flag, or increment the count for an already flagged question.

    Return (is_new, tap_count). The connection is closed before returning.
    """
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    key = question_key(question)
    snapshot = canonical_json(asdict(question))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    connection = sqlite3.connect(str(database_path), timeout=5.0)
    try:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS question_flags (
                    question_key TEXT PRIMARY KEY,
                    generator_id TEXT NOT NULL,
                    generator_version INTEGER NOT NULL,
                    seed INTEGER NOT NULL,
                    difficulty INTEGER NOT NULL,
                    question_id TEXT NOT NULL,
                    question_snapshot TEXT NOT NULL,
                    first_flagged_at TEXT NOT NULL,
                    last_flagged_at TEXT NOT NULL,
                    tap_count INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'open',
                    reason TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT ''
                )
            """)
            existing = connection.execute(
                "SELECT tap_count FROM question_flags WHERE question_key = ?",
                (key,),
            ).fetchone()

            if existing is None:
                connection.execute("""
                    INSERT INTO question_flags (
                        question_key, generator_id, generator_version,
                        seed, difficulty, question_id, question_snapshot,
                        first_flagged_at, last_flagged_at, tap_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    key, question.generator_id, question.generator_version,
                    question.seed, question.difficulty, question.id,
                    snapshot, now, now,
                ))
                return True, 1

            count = existing[0] + 1
            connection.execute("""
                UPDATE question_flags
                SET last_flagged_at = ?, tap_count = ?
                WHERE question_key = ?
            """, (now, count, key))
            return False, count
    finally:
        connection.close()