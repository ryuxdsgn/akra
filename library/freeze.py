"""Freeze the library into an episode project so later library edits cannot change a rendered episode."""
import shutil
from pathlib import Path

from library.lib import find_repo_root

_IGNORE = shutil.ignore_patterns("previews", "catalog.json", "__pycache__")


def freeze(project_dir, refresh=False):
    project = Path(project_dir)
    if not (project / ".lib_used.json").is_file():
        return False
    dst = project / "_lib_frozen"
    if dst.exists() and not refresh:
        return False
    root = find_repo_root(project)
    tmp = project / "_lib_frozen.tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(root / "library", tmp / "library", ignore=_IGNORE)
    local = root / "channels" / "_library"
    if local.is_dir():
        shutil.copytree(local, tmp / "_library", ignore=_IGNORE)
    if dst.exists():
        shutil.rmtree(dst)
    tmp.rename(dst)
    return True


def library_root_for(project_dir):
    frozen = Path(project_dir) / "_lib_frozen"
    return frozen if frozen.is_dir() else find_repo_root(project_dir)
