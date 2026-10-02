"""Install or update MathsGen from its public GitHub snapshot.

Run it through the bootstrap script. Running the bootstrap again at any time
updates to the current GitHub release, with no questions asked:

- saved worksheets, settings, saved setups and feedback carry into the new
  install;
- the previous install is kept as a dated backup, and only the newest
  KEEP_BACKUPS backups are kept;
- if the installed version already matches GitHub, nothing is changed.

A new student needs only the bootstrap: the first run installs everything.
"""
import io
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tempfile
from datetime import datetime
from urllib.request import urlopen
from zipfile import ZipFile


# ------------------------------------------------------------ editable settings

ARCHIVE_URL = "https://github.com/jackatttack/mathsgen/archive/refs/heads/main.zip"
INSTALL_NAME = "mathsgen"
VERSION_FILE = "RELEASE_VERSION.txt"
KEEP_BACKUPS = 2
# User data carried from the old install into the new one.
USER_FOLDERS = ("exports", "feedback", "saved_setups")
USER_FILES = ("worksheet_ui_settings.json", "launcher_settings.json")

# ------------------------------------------------------------ safety limits

MAX_DOWNLOAD_BYTES = 32 * 1024 * 1024
MAX_UNPACKED_BYTES = 80 * 1024 * 1024
MAX_FILE_BYTES = 12 * 1024 * 1024
BACKUP_PREFIX = INSTALL_NAME + "_backup_"


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


def installed_version(folder):
    """The release stamp in a folder, or None if it has none."""
    path = folder / VERSION_FILE
    if path.is_file():
        text = path.read_text(encoding="utf-8").strip()
        return text or None
    return None


def preserve_user_data(old_install, new_install):
    """Carry user files forward while leaving the old install as a backup."""
    for name in USER_FOLDERS:
        old = old_install / name
        if old.is_dir():
            shutil.copytree(str(old), str(new_install / name), dirs_exist_ok=True)
    for name in USER_FILES:
        old = old_install / name
        if old.is_file():
            shutil.copy2(str(old), str(new_install / name))


def prune_backups(documents):
    """Delete all but the newest KEEP_BACKUPS backups. Returns how many went."""
    backups = sorted(
        path for path in documents.iterdir()
        if path.is_dir() and path.name.startswith(BACKUP_PREFIX)
    )
    stale = backups[:-KEEP_BACKUPS] if KEEP_BACKUPS else backups
    for path in stale:
        shutil.rmtree(str(path), ignore_errors=True)
    return len(stale)


def forget_loaded_code():
    """Drop MathsGen modules already loaded in this Pythonista session."""
    for name in list(sys.modules):
        if name in ("mathsgen", "launch_mathsgen") or name.startswith("mathsgen."):
            del sys.modules[name]


def main():
    documents = pythonista_documents()
    check_dependencies()
    target = documents / INSTALL_NAME
    old_version = installed_version(target) if target.exists() else None

    print("Checking GitHub for the latest MathsGen...")
    archive = download_archive()
    temporary_root = Path(tempfile.mkdtemp(
        prefix=".mathsgen_install_", dir=str(documents)
    ))
    candidate = temporary_root / INSTALL_NAME
    backup = None
    try:
        candidate.mkdir()
        count = unpack_release(archive, candidate)
        new_version = installed_version(candidate)
        if (target.exists() and new_version and new_version == old_version
                and (target / "core/mathsgen/catalogue.py").is_file()):
            print("MathsGen is already up to date ({}).".format(new_version))
            print("Open mathsgen/launch_mathsgen.py and tap Run.")
            return
        if target.exists():
            preserve_user_data(target, candidate)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = documents / (BACKUP_PREFIX + stamp)
            if backup.exists():
                raise RuntimeError("Backup name already exists; run again in a second.")
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

    removed = prune_backups(documents)
    forget_loaded_code()
    if backup is None:
        print("Installed MathsGen {} ({} files) at {}".format(
            new_version or "", count, target))
    else:
        print("Updated MathsGen from {} to {}.".format(
            old_version or "an earlier version", new_version or "the latest version"))
        print("Your saved worksheets and settings were kept.")
        print("Previous install backed up at {}".format(backup.name))
        if removed:
            print("Removed {} older backup{}.".format(removed, "" if removed == 1 else "s"))
    print("Open mathsgen/launch_mathsgen.py and tap Run.")
    print("If anything still looks old, close Pythonista fully and reopen it.")


if __name__ == "__main__":
    main()