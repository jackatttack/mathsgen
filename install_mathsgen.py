"""Install MathsGen from its public GitHub snapshot into Pythonista Documents."""
import io
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
from datetime import datetime
from urllib.request import urlopen
from zipfile import ZipFile


ARCHIVE_URL = "https://github.com/jackatttack/mathsgen/archive/refs/heads/main.zip"
INSTALL_NAME = "mathsgen"
MAX_DOWNLOAD_BYTES = 32 * 1024 * 1024
MAX_UNPACKED_BYTES = 80 * 1024 * 1024
MAX_FILE_BYTES = 12 * 1024 * 1024


def pythonista_documents():
    """Locate local Documents from the Pythonista script running this installer."""
    script = Path(__file__).resolve()
    for directory in script.parents:
        if directory.name == "Documents":
            return directory
    raise RuntimeError(
        "Save and run the bootstrap script inside Pythonista's local Documents folder."
    )


def check_dependencies():
    """Report missing PDF libraries before changing an existing installation."""
    missing = []
    for module in ("reportlab", "matplotlib", "sympy"):
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    if missing:
        raise RuntimeError(
            "Install these packages in Pythonista first: " + ", ".join(missing)
        )


def download_archive():
    """Bound the download so a mistaken response cannot fill device storage."""
    with urlopen(ARCHIVE_URL, timeout=60) as response:
        payload = response.read(MAX_DOWNLOAD_BYTES + 1)
    if len(payload) > MAX_DOWNLOAD_BYTES:
        raise RuntimeError("Download exceeds the expected size.")
    return ZipFile(io.BytesIO(payload))


def unpack_release(archive, destination):
    """Validate archive members, then copy regular files into a fresh folder."""
    members = [item for item in archive.infolist() if not item.is_dir()]
    prefixes = {item.filename.split("/", 1)[0] for item in members}
    if prefixes != {"mathsgen-main"}:
        raise RuntimeError("Unexpected repository archive layout: " + repr(prefixes))

    total = 0
    for item in members:
        parts = PurePosixPath(item.filename).parts
        if len(parts) < 2 or any(part in ("", ".", "..") for part in parts):
            raise RuntimeError("Unsafe path in repository archive.")
        if stat.S_ISLNK(item.external_attr >> 16):
            raise RuntimeError("Repository archive contains a symbolic link.")
        if item.file_size > MAX_FILE_BYTES:
            raise RuntimeError("A repository file exceeds the expected size.")
        total += item.file_size
        if total > MAX_UNPACKED_BYTES:
            raise RuntimeError("Repository archive exceeds the expected size.")
        target = destination.joinpath(*parts[1:])
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(item) as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)

    required = (
        "launch_mathsgen.py",
        "core/mathsgen/catalogue.py",
        "core/mathsgen/question_actions.py",
        "tools/mathsgen_action.py",
        "README.md",
    )
    if any(not (destination / name).is_file() for name in required):
        raise RuntimeError("The downloaded release is incomplete.")
    for source in destination.rglob("*.py"):
        compile(source.read_bytes(), str(source), "exec")
    return len(members)


def preserve_user_data(old_install, new_install):
    """Carry user files forward while leaving the old install as a backup."""
    for name in ("exports", "feedback", "saved_setups"):
        old = old_install / name
        if old.is_dir():
            shutil.copytree(str(old), str(new_install / name))
    for name in ("worksheet_ui_settings.json", "launcher_settings.json"):
        old = old_install / name
        if old.is_file():
            shutil.copy2(str(old), str(new_install / name))


def main():
    documents = pythonista_documents()
    check_dependencies()
    target = documents / INSTALL_NAME
    if target.exists():
        response = input(
            "MathsGen already exists. Back it up and install the new version? "
            "Type UPDATE to continue: "
        ).strip()
        if response != "UPDATE":
            print("Installation cancelled. Existing files were untouched.")
            return

    print("Downloading MathsGen...")
    archive = download_archive()
    temporary_root = Path(tempfile.mkdtemp(
        prefix=".mathsgen_install_", dir=str(documents)
    ))
    candidate = temporary_root / INSTALL_NAME
    backup = None
    try:
        candidate.mkdir()
        count = unpack_release(archive, candidate)
        if target.exists():
            preserve_user_data(target, candidate)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = documents / (INSTALL_NAME + "_backup_" + stamp)
            if backup.exists():
                raise RuntimeError("Backup name already exists; retry in one second.")
            os.replace(str(target), str(backup))
        try:
            os.replace(str(candidate), str(target))
        except Exception:
            if backup is not None:
                os.replace(str(backup), str(target))
            raise
    finally:
        archive.close()
        shutil.rmtree(str(temporary_root), ignore_errors=True)

    print("Installed {} files at {}".format(count, target))
    if backup is not None:
        print("Previous install backed up at {}".format(backup))
    print("Open mathsgen/launch_mathsgen.py in Pythonista and tap Run.")


if __name__ == "__main__":
    main()