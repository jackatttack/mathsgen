"""Portable action checks. No clipboard writes or app switching."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from dataclasses import replace
from pathlib import Path
import random
import sys
import tempfile
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from launch_mathsgen import load_engine


def rejected(function):
    try:
        function()
    except ValueError:
        return
    raise AssertionError("Expected rejection")


def main():
    registry = load_engine()
    from mathsgen.core import require
    from mathsgen.pdf import render_pdf
    from mathsgen.question_actions import (
        action_url, available_actions, content_digest, encode_question,
        source_question, new_question, render_question_card, render_support_card,
        decode_question,
    )
    from mathsgen.question_support import (
        LINEAR, QUADRATIC, TRIG, card_for, supports,
    )

    out = ROOT / "exports" / "question_actions"
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(210921)
    checked = 0
    failures = []
    specimens = []
    trig_pairs = set()

    with tempfile.TemporaryDirectory(prefix="mathsgen_cards_") as temporary:
        card_path = Path(temporary) / "card.pdf"
        for info in registry.list():
            for level in sorted(info.difficulty_descriptions):
                try:
                    generator = registry.get(info.id)
                    q = generator.generate(seed=20260921 + level, difficulty=level)
                    generator.validate(q)
                    token = encode_question(q)
                    rebuilt = source_question(token, registry)
                    require(rebuilt.to_dict() == q.to_dict(), "Source round-trip mismatch")
                    url = action_url(q, "another")
                    query = parse_qs(urlsplit(url).query)
                    require(query["argv"] == ["another", token], "URL argument mismatch")
                    require(query["root"] == ["icloud"], "Wrong URL root")

                    candidate = new_question(
                        q, registry, seed_source=lambda: rng.getrandbits(53)
                    )
                    require(candidate.generator_id == q.generator_id, "Generator changed")
                    require(candidate.difficulty == q.difficulty, "Difficulty changed")
                    require(candidate.settings == q.settings, "Settings changed")
                    require(content_digest(candidate, True) != content_digest(q, True),
                            "Repeated question")
                    render_question_card(candidate, card_path)

                    if supports(q):
                        require(len(available_actions(q)) == 3, "Missing support actions")
                        for action in ("facts", "hint"):
                            render_support_card(card_for(q, action), card_path)
                        specimens.append(q)
                    else:
                        require(available_actions(q) == [("another", "Another like this")],
                                "Unsupported support link")
                    checked += 1
                except Exception as error:
                    failures.append("{} L{}: {}".format(info.id, level, error))
            print("CHECKED:", info.id)

        # Exercise all six directed side-finding cases, including unknown denominators.
        trig = registry.get(TRIG)
        for seed in range(100):
            q = trig.generate(seed=seed, difficulty=1)
            pair = (q.parameters["known"], q.parameters["wanted"])
            if pair not in trig_pairs:
                render_support_card(card_for(q, "hint"), card_path)
                trig_pairs.add(pair)
            if len(trig_pairs) == 6:
                break
        require(len(trig_pairs) == 6, "Did not cover all six trig side cases")

    rejected(lambda: decode_question("not-a-token!"))
    example = specimens[0] if specimens else registry.get(LINEAR).generate(1, 1)
    rejected(lambda: source_question(
        encode_question(replace(example, generator_version=999999)), registry
    ))
    rejected(lambda: source_question(
        encode_question(replace(example, prompt=replace(
            example.prompt, text=example.prompt.text + " altered"
        ))), registry
    ))

    if failures:
        print("\nCARD FAILURES:")
        for failure in failures:
            print(failure)
        raise AssertionError("{} generator/level checks failed".format(len(failures)))

    paper = SimpleNamespace(
        id="interactive-support-specimen",
        title="Interactive Mathsgen: Another, Facts and Hint",
        specification={"show_difficulty": True, "interactive_links": True},
        questions=tuple(specimens),
    )
    path = out / "interactive_specimen.pdf"
    print(render_pdf(paper, path))
    uri_count = path.read_bytes().count(b"/URI")
    require(uri_count == 3 * len(specimens), "Unexpected number of PDF links")

    hidden_path = out / "links_hidden_check.pdf"
    hidden = SimpleNamespace(
        id="links-hidden-check", title="Links hidden",
        specification={"interactive_links": False}, questions=(example,),
    )
    render_pdf(hidden, hidden_path)
    require(b"/URI" not in hidden_path.read_bytes(), "Hidden links still present")
    hidden_path.unlink()

    print("\nPASS:", checked, "generator/level action and card checks")
    print("PASS: source reconstruction, changed-source rejection, six trig side cases")
    print("PASS:", uri_count, "specimen links; renderer opt-out")
    print("SPECIMEN:", path)
    print("Device review pending: PDF link taps, card layout and clipboard paste.")


if __name__ == "__main__":
    main()