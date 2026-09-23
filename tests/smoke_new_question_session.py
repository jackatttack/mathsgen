"""Check regeneration, difficulty controls and transactional clipboard state.

Actual cards are rasterised on Pythonista. An injected clipboard writer
prevents this Forge smoke from replacing the user's clipboard contents.
"""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))


import hashlib
import json
from pathlib import Path
import tempfile

from launch_mathsgen import load_engine


def main():
    from mathsgen.new_question_session import NewQuestionSession
    from mathsgen.question_actions import (
        encode_question, content_digest,
    )

    registry = load_engine()
    generator = registry.get(
        "algebra.quadratic.factorisable_monic"
    )
    source = generator.generate(20260921, difficulty=2)
    generator.validate(source)
    token = encode_question(source)

    copies = []

    def fake_copy(path):
        data = Path(path).read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        copies.append((str(path), hashlib.sha256(data).hexdigest()))

    with tempfile.TemporaryDirectory() as directory:
        session = NewQuestionSession(
            source, registry, token, directory,
            clipboard_writer=fake_copy,
        )
        assert session.levels == (1, 2, 3, 4)
        assert session.adjacent_level(-1) == 1
        assert session.adjacent_level(1) == 3

        first, first_path, first_size = session.copy_new()
        assert first.difficulty == 2
        assert session.current_question == first
        assert first_path.exists()
        assert first_size[0] > 0 and first_size[1] > 0

        first_digest = content_digest(first, True)
        first_state = json.loads(
            session.state_path.read_text(encoding="utf-8")
        )
        assert first_state["digest"] == first_digest

        repeated, repeated_path, repeated_size = session.copy_current()
        assert repeated == first
        assert repeated_path == first_path
        assert repeated_size == first_size
        assert copies[-1] == copies[-2]
        assert json.loads(
            session.state_path.read_text(encoding="utf-8")
        ) == first_state
        print("PASS: Copy repeats exactly the displayed PNG and state")

        harder, harder_path, _ = session.copy_new(3)
        assert harder.difficulty == 3
        assert session.level == 3
        assert harder.generator_id == source.generator_id
        assert harder.settings == source.settings
        assert content_digest(harder, True) != first_digest

        refreshed, refreshed_path, _ = session.copy_new()
        assert refreshed.difficulty == 3
        assert content_digest(refreshed, True) != content_digest(harder, True)
        assert refreshed_path != harder_path
        print("PASS: Harder and Refresh both generate and copy fresh questions")

        easier, easier_path, _ = session.copy_new(1)
        assert easier.difficulty == 1
        assert session.adjacent_level(-1) is None
        assert session.adjacent_level(1) == 2
        assert source.difficulty == 2
        print("PASS: difficulty controls respect generator boundaries")
        print("PASS: original worksheet question remains unchanged")

        successful_state = session.state_path.read_text(encoding="utf-8")
        successful_png = session.current_png

        def fail_copy(path):
            raise RuntimeError("Simulated clipboard failure")

        session.clipboard_writer = fail_copy
        try:
            session.copy_new(2)
        except RuntimeError as error:
            assert str(error) == "Simulated clipboard failure"
        else:
            raise AssertionError("Clipboard failure was not propagated")

        assert session.level == 1
        assert session.current_question == easier
        assert session.current_png == successful_png
        assert successful_png.exists()
        assert session.state_path.read_text(encoding="utf-8") == successful_state
        print("PASS: failed clipboard copy preserves previous preview and state")

    from mathsgen.new_question_ui import NewQuestionView, present_new_question
    assert callable(present_new_question)
    assert callable(NewQuestionView)
    print("PASS: Pythonista regeneration interface imports")
    print("PASS: new question session smoke complete")
    print("DEVICE UI AND REAL CLIPBOARD: manual verification pending")


if __name__ == "__main__":
    main()