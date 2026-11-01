"""Frozen PSL snapshot identifier, so a feature change cannot hide in a bump.

``tldextract`` ships a PSL snapshot and this project forbids network fetches, so
the snapshot file's hash is the only thing that pins the domain parsing.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import tldextract


def psl_snapshot() -> dict:
    base = Path(tldextract.__file__).parent / ".tld_set_snapshot"
    if not base.exists():
        return {"path": None, "bytes": None, "sha256": None}
    return {"path": base.name, "bytes": base.stat().st_size,
            "sha256": hashlib.sha256(base.read_bytes()).hexdigest()}
