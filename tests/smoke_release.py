"""Check the public layout, PDF action routes and installer extraction offline."""
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent.parent
CORE = str(ROOT / "core")
if CORE not in sys.path:
    sys.path.insert(0, CORE)


def main():
    from mathsgen.catalogue import build_registry
    from mathsgen.question_actions import action_url

    registry = build_registry()
    question = registry.get("algebra.expressions.like_terms").generate(7, 4)
    link = action_url(question, "answer")
    assert link.startswith("pythonista3://mathsgen/tools/mathsgen_action.py?")
    assert "root=local" in link and "argv=answer" in link

    pdf = ROOT / "examples" / "questions.pdf"
    answers = ROOT / "examples" / "answers.pdf"
    assert pdf.read_bytes().startswith(b"%PDF-")
    assert answers.read_bytes().startswith(b"%PDF-")
    assert b"mathsgen/tools/mathsgen_action.py" in pdf.read_bytes()
    assert b"root=local" in pdf.read_bytes()

    installer_path = ROOT / "install_mathsgen.py"
    spec = importlib.util.spec_from_file_location("release_installer", str(installer_path))
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)

    with tempfile.TemporaryDirectory() as temporary:
        old = Path(temporary) / "old"
        new = Path(temporary) / "new"
        (old / "exports").mkdir(parents=True)
        (old / "exports" / "saved.pdf").write_bytes(b"saved")
        (old / "worksheet_ui_settings.json").write_text('{"mode":"mini"}')
        new.mkdir()
        installer.preserve_user_data(old, new)
        assert (new / "exports" / "saved.pdf").read_bytes() == b"saved"
        assert (new / "worksheet_ui_settings.json").is_file()

        archive_bytes = io.BytesIO()
        with ZipFile(archive_bytes, "w") as archive:
            archive.writestr(
                "mathsgen-main/launch_mathsgen.py",
                (ROOT / "launch_mathsgen.py").read_bytes(),
            )
            archive.writestr(
                "mathsgen-main/core/mathsgen/catalogue.py",
                (ROOT / "core" / "mathsgen" / "catalogue.py").read_bytes(),
            )
            archive.writestr(
                "mathsgen-main/core/mathsgen/question_actions.py",
                (ROOT / "core" / "mathsgen" / "question_actions.py").read_bytes(),
            )
            archive.writestr(
                "mathsgen-main/tools/mathsgen_action.py",
                (ROOT / "tools" / "mathsgen_action.py").read_bytes(),
            )
            archive.writestr("mathsgen-main/README.md", (ROOT / "README.md").read_bytes())
        archive_bytes.seek(0)
        with ZipFile(archive_bytes) as archive:
            count = installer.unpack_release(archive, Path(temporary) / "unpacked")
        assert count == 5

    print("PASS: catalogue, local PDF links, user data, archive extraction and Python syntax")
    print("Catalogue:", len(registry.list()), "generators")
    print("Sample PDFs:", pdf.stat().st_size, answers.stat().st_size, "bytes")


if __name__ == "__main__":
    main()