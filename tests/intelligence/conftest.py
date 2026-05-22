"""Pytest configuration and shared fixtures for intelligence tests."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _repo_on_path():
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    yield
