"""Render the same mixed worksheet in every theme, with and without source lines."""
import sys as _mathsgen_test_sys
from pathlib import Path as _MathsGenTestPath
_MATHSGEN_PROJECT_ROOT = _MathsGenTestPath(__file__).resolve().parent.parent
if str(_MATHSGEN_PROJECT_ROOT) not in _mathsgen_test_sys.path:
    _mathsgen_test_sys.path.insert(0, str(_MATHSGEN_PROJECT_ROOT))

from launch_mathsgen import load_engine


SAMPLE = (
    ("algebra.expressions.like_terms", 4),
    ("algebra.rearranging.changing_subject", 3),
    ("geometry.trigonometry.cosine_rule", 2),
    ("geometry.circle_theorems.centre_angle", 2),
    ("probability.venn.probabilities", 3),
)


def main():
    registry = load_engine()
    from mathsgen.core import require
    from mathsgen.theme import THEMES
    from mathsgen.pdf import source_line, generator_title
    from mathsgen.worksheets import Worksheet
    from mathsgen.export import export_worksheet

    questions = tuple(registry.get(gid).generate(7, level) for gid, level in SAMPLE)
    for q in questions:
        require(generator_title(q.generator_id) == registry.get(q.generator_id).info.title,
                "Title lookup disagrees for " + q.generator_id)
        print("  " + source_line(q))
    require(generator_title("no.such.generator") == "no.such.generator",
            "Unknown generator must fall back to its ID")

    for name in THEMES:
        for show in (True, False):
            report = export_worksheet(
                Worksheet(
                    id="theme-{}-{}".format(name, "source" if show else "plain"),
                    title="Theme check: {}".format(name), seed=7,
                    specification={"theme": name, "show_source": show},
                    questions=questions,
                ),
                _MATHSGEN_PROJECT_ROOT / "exports", answers=True,
            )
            if show:
                print("{:9} {}".format(name, report["directory"]))

    try:
        export_worksheet(
            Worksheet(id="theme-bad", title="Bad", seed=7,
                      specification={"theme": "neon"}, questions=questions),
            _MATHSGEN_PROJECT_ROOT / "exports", answers=False,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown theme accepted")
    print("PASS: {} themes, source lines on and off, unknown theme refused".format(len(THEMES)))


if __name__ == "__main__":
    main()