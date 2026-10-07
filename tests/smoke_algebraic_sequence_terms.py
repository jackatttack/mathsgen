"""Focused exact-root, corruption, reproducibility and rendering checks."""
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from launch_mathsgen import load_engine


def rejects(generator, question):
    try:
        generator.validate(question)
    except ValueError:
        return
    raise AssertionError("Corrupted algebraic sequence accepted")


def main():
    load_engine()
    from mathsgen.algebraic_sequence_terms import AlgebraicSequenceTerms
    from mathsgen.pdf import render_pdf
    samples = []
    for kind, level in (("arithmetic", 3), ("geometric", 4)):
        generator = AlgebraicSequenceTerms(kind)
        for seed in range(40):
            question = generator.generate(seed, level)
            generator.validate_independently(question)
            assert question.to_dict() == generator.generate(seed, level).to_dict()
            rejects(generator, replace(question, answer={}))
            rejects(generator, replace(question, prompt=replace(question.prompt, text="Altered")))
            if kind == "geometric":
                assert len(question.answer["values"]) == 2
                rejects(generator, replace(question, answer=dict(
                    question.answer, values=question.answer["values"][:1])))
            if seed < 3:
                samples.append(question)
                print(question.prompt.text, "->", question.answer_display.text)
    output = PROJECT_ROOT / "exports" / "specimens" / "algebraic_sequence_terms_v1"
    output.mkdir(parents=True, exist_ok=True)
    sheet = SimpleNamespace(
        title="Algebraic sequence terms", id="algebraic-sequence-terms-v1",
        specification={}, questions=tuple(samples))
    for mode in ("questions", "answers"):
        print(render_pdf(sheet, output / (mode + ".pdf"), mode))
    print("PASS: 80 independent checks, both geometric roots, rejection and exports.")


if __name__ == "__main__":
    main()