"""Make the flat service modules importable from the repository layout.

In the repository the modules live in collector/ and inference/; on the
deployed GPU host they sit next to the tests, so missing folders are skipped.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for name in ("collector", "inference"):
    folder = ROOT / name
    if folder.is_dir() and str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
