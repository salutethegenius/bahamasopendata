"""Smoke tests: intelligence package layout is importable from repo root."""
import importlib
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


def test_intelligence_package_imports():
    pkg = importlib.import_module("ingestion.intelligence")
    assert pkg.__doc__


def test_intelligence_subpackages():
    for name in ("social", "web", "capture"):
        mod = importlib.import_module(f"ingestion.intelligence.{name}")
        assert mod.__doc__


def test_key_modules_importable():
    modules = [
        "ingestion.intelligence.types",
        "ingestion.intelligence.logging_config",
        "ingestion.intelligence.capture.registry",
        "ingestion.intelligence.social.wayback",
        "ingestion.intelligence.web.similarweb",
    ]
    for dotted in modules:
        importlib.import_module(dotted)
