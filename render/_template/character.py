"""Shim: puts the repo (or the episode's _lib_frozen/) on sys.path and, when library/rig/toon.py is present, re-exports
that rig, so episode build.py files keep `from character import ...`. Without the rig, any helper raises a RuntimeError."""
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
    """Raised when a character helper is used but library/rig/ is not in this tree."""


_RigNotIncluded.__name__ = _RigNotIncluded.__qualname__ = "RigNotIncluded"


try:
    from library.rig import toon as _toon  # noqa: E402
except ModuleNotFoundError as _e:  # the rig is optional: `import character` still sets up sys.path
    if _e.name not in ("library.rig", "library.rig.toon"):
        raise
    _toon = None

if _toon is not None:
    from library.rig.toon import *  # noqa: E402,F401,F403
    from library.rig.toon import _piv, _pivots  # noqa: E402,F401

    # Underscore helpers and constants that star-import skips; episode code may touch them.
    globals().update({k: v for k, v in vars(_toon).items() if k.startswith("_") and not k.startswith("__")})
else:
    def __getattr__(name):
        if name.startswith("__"):
            raise AttributeError(name)
        raise _RigNotIncluded(f"{name}: {_RIG_MISSING}")
