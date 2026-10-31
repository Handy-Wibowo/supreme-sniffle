"""Shared raw-URL feature extractor (configuration A2, 18 features).

Ported verbatim from ``Experiment/4 - PhreshPhish Temporal Audit/run_temporal.py``
(lines 184-206 and 331-368) so that PhiUSIIL and PhreshPhish are featurised by
one implementation. Importing this module performs no work: no file reads, no
network access, no training.

Definitions (see ``feature_groups.json`` for the machine-readable copy):

* ``parse_url``  - adds ``http://`` when no scheme is present, requires an
  http/https scheme and a host, rejects invalid ports and whitespace in the
  host, lowercases the host and strips a trailing dot.
* domain key      - ``tldextract`` with ``suffix_list_urls=()`` (bundled PSL
  snapshot, never fetched) and ``include_psl_private_domains=False``; an
  ``ipaddress`` literal is its own key and yields empty TLD/subdomain.
* ratios          - divided by ``len(stripped url)`` (minimum 1).
* ``NoOfOtherSpecialCharsInURL`` counts characters outside ``[A-Za-z0-9]``.
* ``NoOfObfuscatedChar`` counts percent-escapes ``%HH``.
"""

from __future__ import annotations

import ipaddress
import re
from functools import lru_cache
from urllib.parse import urlsplit, urlunsplit

import tldextract

# Frozen PSL snapshot: tldextract ships the snapshot and we forbid fetching.
EXT = tldextract.TLDExtract(suffix_list_urls=(), include_psl_private_domains=False)
SPEC = re.compile(r"[^A-Za-z0-9]")

# Order is part of the contract: predictions and models rely on it.
FEATURE_ORDER = [
    "URLLength",
    "DomainLength",
    "TLDLength",
    "NoOfSubDomain",
    "NoOfObfuscatedChar",
    "ObfuscationRatio",
    "NoOfLettersInURL",
    "LetterRatioInURL",
    "NoOfDegitsInURL",
    "DegitRatioInURL",
    "NoOfEqualsInURL",
    "NoOfQMarkInURL",
    "NoOfAmpersandInURL",
    "NoOfOtherSpecialCharsInURL",
    "SpacialCharRatioInURL",
    "IsHTTPS",
    "HasObfuscation",
    "IsDomainIP",
]


def parse_url(u: str):
    """Return (SplitResult, host). Raises ValueError on an unusable URL."""
    u = u.strip()
    p = urlsplit(u if "://" in u else "http://" + u)
    if p.scheme.lower() not in {"http", "https"} or not p.hostname:
        raise ValueError("URL requires a host and a parseable HTTP(S) scheme.")
    _ = p.port  # rejects an invalid port
    host = p.hostname.lower().rstrip(".")
    if any(c.isspace() for c in host):
        raise ValueError("Space inside host.")
    return p, host


def canonical_url(u: str) -> str:
    """Deduplication key: scheme+host lowercased, path/query kept, fragment dropped."""
    p, host = parse_url(u)
    host_netloc = "[" + host + "]" if ":" in host else host
    if p.port is not None:
        host_netloc += ":" + str(p.port)
    auth = p.netloc.rsplit("@", 1)[0] + "@" if "@" in p.netloc else ""
    return urlunsplit((p.scheme.lower(), auth + host_netloc, p.path or "/", p.query, ""))


@lru_cache(maxsize=None)
def host_parts(host: str):
    """Return (registrable_domain, subdomain, suffix, is_ip)."""
    try:
        ipaddress.ip_address(host)
        return host, "", "", True
    except ValueError:
        e = EXT(host)
        reg = e.domain + "." + e.suffix if e.suffix else (e.domain or host)
        return reg, e.subdomain or "", e.suffix or "", False


def url_features(u: str) -> dict:
    """The 18 A2 features for one URL. Raises ValueError if the URL cannot be parsed."""
    u = u.strip()
    p, host = parse_url(u)
    reg, sub, suffix, is_ip = host_parts(host)
    length = len(u) or 1
    letters = sum(c.isalpha() for c in u)
    digits = sum(c.isdigit() for c in u)
    obfuscated = len(re.findall(r"%[0-9A-Fa-f]{2}", u))
    special = len(SPEC.findall(u))
    return {
        "URLLength": length,
        "DomainLength": len(reg),
        "TLDLength": len(suffix),
        "NoOfSubDomain": len([s for s in sub.split(".") if s]),
        "NoOfObfuscatedChar": obfuscated,
        "ObfuscationRatio": obfuscated / length,
        "NoOfLettersInURL": letters,
        "LetterRatioInURL": letters / length,
        "NoOfDegitsInURL": digits,
        "DegitRatioInURL": digits / length,
        "NoOfEqualsInURL": u.count("="),
        "NoOfQMarkInURL": u.count("?"),
        "NoOfAmpersandInURL": u.count("&"),
        "NoOfOtherSpecialCharsInURL": special,
        "SpacialCharRatioInURL": special / length,
        "IsHTTPS": int(p.scheme.lower() == "https"),
        "HasObfuscation": int(obfuscated > 0),
        "IsDomainIP": int(is_ip),
    }


def domain_for(u: str) -> str:
    """Registrable domain key used for the site-disjoint audit and bootstrap."""
    _, host = parse_url(u)
    return host_parts(host)[0]


def psl_snapshot() -> dict:
    """Identify the bundled PSL snapshot without touching the network."""
    from pathlib import Path

    import tldextract as _te

    snap = Path(_te.__file__).parent / ".tld_set_snapshot"
    return {
        "library": "tldextract",
        "suffix_list_urls": [],
        "include_psl_private_domains": False,
        "snapshot_file": snap.name,
        "snapshot_bytes": snap.stat().st_size if snap.exists() else None,
        "snapshot_sha256": _sha256(snap) if snap.exists() else None,
    }


def _sha256(path) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
