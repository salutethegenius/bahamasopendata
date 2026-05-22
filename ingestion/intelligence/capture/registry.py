"""Read/write data/intelligence/registry.json (architecture §4).

Mirrors parser.load_metadata / save_metadata for the document pipeline.
Planned API: load_registry, save_registry, mark_capture, mark_validation.
Functions are implemented in a later commit per the build order.
"""
from pathlib import Path
