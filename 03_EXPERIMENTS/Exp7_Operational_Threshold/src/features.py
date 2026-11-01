"""Deterministic URL-only feature extractor (A2, 18 features).

Ported verbatim from ``Experiment/4 - PhreshPhish Temporal Audit/run_temporal.py``
(the same definitions Experiment 5 reuses as configuration A2), so that this
experiment's model inputs are the already-audited ones. Importing does no I/O.
"""

from __future__ import annotations

import ipaddress
import re
from functools import lru_cache
from urllib.parse import urlsplit, urlunsplit

import pandas as pd
import tldextract

# Order is part of the contract: saved models rely on it.
FEATURE_ORDER = [
    "URLLength", "DomainLength", "TLDLength", "NoOfSubDomain",
    "NoOfObfuscatedChar", "ObfuscationRatio", "NoOfLettersInURL",
    "LetterRatioInURL", "NoOfDegitsInURL", "DegitRatioInURL",
    "NoOfEqualsInURL", "NoOfQMarkInURL", "NoOfAmpersandInURL",
    "NoOfOtherSpecialCharsInURL", "SpacialCharRatioInURL", "IsHTTPS",
    "HasObfuscation", "IsDomainIP",
]

# Bundled PSL snapshot only; never fetches.
EXT = tldextract.TLDExtract(suffix_list_urls=(), include_psl_private_domains=False)
SPEC = re.compile(r"[^A-Za-z0-9]")


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
    """Deduplication key: lower-case scheme/host, no fragment, path kept."""
    p, host = parse_url(u)
    host_netloc = "[" + host + "]" if ":" in host else host
    if p.port is not None:
        host_netloc += ":" + str(p.port)
    auth = p.netloc.rsplit("@", 1)[0] + "@" if "@" in p.netloc else ""
    return urlunsplit((p.scheme.lower(), auth + host_netloc, p.path or "/", p.query, ""))


@lru_cache(maxsize=None)
def host_parts(host: str):
    try:
        ipaddress.ip_address(host)
        return host, "", "", True
    except ValueError:
        e = EXT(host)
        reg = e.domain + "." + e.suffix if e.suffix else (e.domain or host)
        return reg, e.subdomain or "", e.suffix or "", False


def url_features(u: str) -> dict:
    u = u.strip()
    p, host = parse_url(u)
    reg, sub, suffix, is_ip = host_parts(host)
    length = len(u) or 1
    letters = sum(c.isalpha() for c in u)
    digits = sum(c.isdigit() for c in u)
    obfuscated = len(re.findall(r"%[0-9A-Fa-f]{2}", u))
    special = len(SPEC.findall(u))
    return {"URLLength": length, "DomainLength": len(reg), "TLDLength": len(suffix),
            "NoOfSubDomain": len([s for s in sub.split(".") if s]),
            "NoOfObfuscatedChar": obfuscated, "ObfuscationRatio": obfuscated / length,
            "NoOfLettersInURL": letters, "LetterRatioInURL": letters / length,
            "NoOfDegitsInURL": digits, "DegitRatioInURL": digits / length,
            "NoOfEqualsInURL": u.count("="), "NoOfQMarkInURL": u.count("?"),
            "NoOfAmpersandInURL": u.count("&"), "NoOfOtherSpecialCharsInURL": special,
            "SpacialCharRatioInURL": special / length,
            "IsHTTPS": int(p.scheme.lower() == "https"),
            "HasObfuscation": int(obfuscated > 0), "IsDomainIP": int(is_ip)}


def domain_for(u: str) -> str:
    _, host = parse_url(u)
    return host_parts(host)[0]


def feature_frame(urls) -> pd.DataFrame:
    """Feature matrix in FEATURE_ORDER; float64 to keep thresholds unambiguous."""
    rows = [url_features(u) for u in urls]
    return pd.DataFrame(rows, columns=FEATURE_ORDER, dtype="float64")
