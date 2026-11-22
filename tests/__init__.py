"""Lets `python3 -m unittest tests.test_x` run from the repo root: tests import `helpers` as a top-level module."""
import sys
from pathlib import Path

_HERE = str(Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
