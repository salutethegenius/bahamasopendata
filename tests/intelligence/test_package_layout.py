"""Smoke tests: intelligence package layout is importable from repo root."""
import importlib


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
        "ingestion.intelligence.social.youtube",
        "ingestion.intelligence.social.instagram",
        "ingestion.intelligence.social.facebook",
        "ingestion.intelligence.social.tiktok",
        "ingestion.intelligence.social.twitter",
        "ingestion.intelligence.social.socialblade",
        "ingestion.intelligence.web.similarweb",
        "ingestion.intelligence.web.bing_serp",
    ]
    for dotted in modules:
        importlib.import_module(dotted)
