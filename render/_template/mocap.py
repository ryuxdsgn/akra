"""Shim: re-exports library/rig/mocap.py when the rig is present; without it, any helper raises a RuntimeError."""
import sys
from pathlib import Path


def _find_repo_root():
    here = Path(__file__).resolve().parent
    if (here / "_lib_frozen").is_dir():  # frozen copy wins once an episode is final
        return here / "_lib_frozen"
    for d in (here, *here.parents):
        if (d / "library").is_dir() and (d / "skills" / "akra").is_dir():
            return d
    raise RuntimeError("repo root (library/ + skills/akra/) not found above " + __file__)


_ROOT = str(_find_repo_root())
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

_RIG_MISSING = ("character rig not included in this distribution; draw characters in your scenes "
               "or add your own rig (see references/library.md)")


class _RigNotIncluded(RuntimeError):
    """Raised when a mocap helper is used but library/rig/ is not in this tree."""


_RigNotIncluded.__name__ = _RigNotIncluded.__qualname__ = "RigNotIncluded"


try:
    from library.rig import mocap as _mocap  # noqa: E402
except ModuleNotFoundError as _e:
    if _e.name not in ("library.rig", "library.rig.mocap"):
        raise
    _mocap = None

if _mocap is not None:
    from library.rig.mocap import *  # noqa: E402,F401,F403
else:
    def __getattr__(name):
        if name.startswith("__"):
            raise AttributeError(name)
        raise _RigNotIncluded(f"{name}: {_RIG_MISSING}")

if __name__ == "__main__":
    if _mocap is None:
        sys.exit(_RIG_MISSING)
    import runpy
    runpy.run_module("library.rig.mocap", run_name="__main__")
