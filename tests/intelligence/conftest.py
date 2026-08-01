"""Pytest configuration and shared fixtures for intelligence tests."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Module import time — required before collecting tests that import backend.app.*
for _path in (str(REPO_ROOT), str(REPO_ROOT / "backend")):
    if _path not in sys.path:
        sys.path.insert(0, _path)


@pytest.fixture(autouse=True)
def _repo_on_path():
    for path in (str(REPO_ROOT), str(REPO_ROOT / "backend")):
        if path not in sys.path:
            sys.path.insert(0, path)
    yield
