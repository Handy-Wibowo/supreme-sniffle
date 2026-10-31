"""Input paths, feature manifests, dataset loaders and split handling.

No training happens on import; loading functions only read files.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .features import FEATURE_ORDER
from .provenance import WORKSPACE

# --------------------------------------------------------------------- inputs
CLEAN_DIR = WORKSPACE / "Experiment" / "1 - PhiUSIIL Cleaning + Leakage-Audit Notebook" / "phiusill_clean"
PHIUSIIL_CLEAN = CLEAN_DIR / "phiusiil_clean.parquet"
SPLIT_RANDOM = CLEAN_DIR / "split_random.csv"
SPLIT_SITEDISJOINT = CLEAN_DIR / "split_sitedisjoint.csv"
PHIUSIIL_RAW = WORKSPACE / "dataset" / "PhiUSIIL Phishing" / "PhiUSIIL_Phishing_URL_Dataset.csv"
PHRESH_DIR = WORKSPACE / "dataset" / "PhreshPhish" / "data"

# ------------------------------------------------------------------- design
SEEDS = [13, 42, 2024, 777, 31415]
PRIMARY_SEED_PHIUSIIL = 42   # protocol section 7.1
PRIMARY_SEED_PHRESH = 13     # protocol section 7.6 (matches legacy pipeline)
THRESHOLD = 0.5
CUTOFF_UTC = pd.Timestamp("2025-09-08", tz="UTC")
BOOTSTRAP_REPLICATES = 1000
BOOTSTRAP_SEED = 42
DEFAULT_THREADS = 4

# ------------------------------------------------------- feature manifests
# A0: the legacy pipeline's "all-features" family, 47 columns.
LEXICAL = [
    "URLLength", "DomainLength", "TLDLength", "NoOfSubDomain", "NoOfObfuscatedChar",
    "ObfuscationRatio", "NoOfLettersInURL", "LetterRatioInURL", "NoOfDegitsInURL",
    "DegitRatioInURL", "NoOfEqualsInURL", "NoOfQMarkInURL", "NoOfAmpersandInURL",
    "NoOfOtherSpecialCharsInURL", "SpacialCharRatioInURL", "CharContinuationRate",
    "TLDLegitimateProb", "URLCharProb", "IsHTTPS", "HasObfuscation",
]
HOST = ["IsDomainIP"]
CONTENT = [
    "LineOfCode", "LargestLineLength", "HasTitle", "HasFavicon", "Robots",
    "IsResponsive", "NoOfURLRedirect", "NoOfSelfRedirect", "HasDescription",
    "NoOfPopup", "NoOfiFrame", "HasExternalFormSubmit", "HasSocialNet",
    "HasSubmitButton", "HasHiddenFields", "HasPasswordField", "Bank", "Pay",
    "Crypto", "HasCopyrightInfo", "NoOfImage", "NoOfCSS", "NoOfJS",
    "NoOfSelfRef", "NoOfEmptyRef", "NoOfExternalRef",
]
ABLATED = ["LineOfCode", "NoOfExternalRef", "NoOfImage", "NoOfSelfRef", "NoOfJS", "NoOfCSS"]

A0 = LEXICAL + HOST + CONTENT
A1 = [f for f in A0 if f not in ABLATED]
A2 = list(FEATURE_ORDER)

assert len(A0) == 47, len(A0)
assert len(A1) == 41, len(A1)
assert len(A2) == 18, len(A2)
assert len(set(A0)) == 47 and len(set(A2)) == 18

CONFIGS = {"A0": A0, "A1": A1, "A2": A2}
PROTOCOLS_PHIUSIIL = ["random", "sitedisjoint"]
MODELS = ["lightgbm", "xgboost"]

MODEL_PARAMS = {
    "lightgbm": dict(n_estimators=300, learning_rate=0.05, num_leaves=63, verbose=-1),
    "xgboost": dict(n_estimators=300, learning_rate=0.05, max_depth=8,
                    eval_metric="logloss", tree_method="hist"),
}


def feature_groups() -> dict:
    """Machine-readable feature manifest, written into every run directory."""
    return {
        "A0": {"n_features": len(A0), "features": A0,
               "source": "precomputed columns of phiusiil_clean.parquet",
               "role": "reference configuration (legacy 'all-features')"},
        "A1": {"n_features": len(A1), "features": A1,
               "source": "A0 minus the six content features",
               "removed": ABLATED,
               "role": "six-content-feature ablation"},
        "A2": {"n_features": len(A2), "features": A2,
               "source": "src/features.py url_features(), computed from the raw URL",
               "role": "URL-only representation, also used for PhreshPhish",
               "note": "not a one-factor ablation of A0: feature count, source and "
                       "definitions all change"},
    }


A2_DEFINITIONS = {
    "URLLength": "len(url) after stripping whitespace",
    "DomainLength": "len(registrable domain from tldextract, PSL private domains off)",
    "TLDLength": "len(public suffix)",
    "NoOfSubDomain": "count of non-empty dot-separated subdomain labels",
    "NoOfObfuscatedChar": "count of %HH escapes",
    "ObfuscationRatio": "NoOfObfuscatedChar / URLLength",
    "NoOfLettersInURL": "count of alphabetic characters",
    "LetterRatioInURL": "NoOfLettersInURL / URLLength",
    "NoOfDegitsInURL": "count of digit characters (name kept for parity with the source schema)",
    "DegitRatioInURL": "NoOfDegitsInURL / URLLength",
    "NoOfEqualsInURL": "count of '='",
    "NoOfQMarkInURL": "count of '?'",
    "NoOfAmpersandInURL": "count of '&'",
    "NoOfOtherSpecialCharsInURL": "count of characters outside [A-Za-z0-9]",
    "SpacialCharRatioInURL": "NoOfOtherSpecialCharsInURL / URLLength",
    "IsHTTPS": "1 if the parsed scheme is https",
    "HasObfuscation": "1 if any %HH escape is present",
    "IsDomainIP": "1 if the host is an IP literal",
}
_UPSTREAM = "upstream column of phiusiil_clean.parquet; definition not re-derived here"

def feature_provenance() -> pd.DataFrame:
    """Per-feature provenance table for A0/A1/A2 (protocol section 8 artifact)."""
    rows = []
    for config, info in feature_groups().items():
        for feature in info["features"]:
            rows.append({
                "config": config,
                "feature": feature,
                "source": info["source"],
                "definition": A2_DEFINITIONS.get(feature, _UPSTREAM) if config == "A2" else _UPSTREAM,
                "known": config == "A2",
            })
    return pd.DataFrame(rows)

# ------------------------------------------------------------------ loaders
def load_phiusiil() -> pd.DataFrame:
    """Cleaned PhiUSIIL table. `url_id` equals the physical row position (audited)."""
    df = pd.read_parquet(PHIUSIIL_CLEAN)
    df["y_phish"] = 1 - df["label"].astype("int8")  # source: benign=1, phish=0
    return df


def load_split(protocol: str, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (train_ids, test_ids) for one protocol/seed.

    The `val` fold exists in the frozen split files but is not used by the
    protocol; it is reported in split_audit.csv and never trained on.
    """
    path = {"random": SPLIT_RANDOM, "sitedisjoint": SPLIT_SITEDISJOINT}[protocol]
    sp = pd.read_csv(path)
    sub = sp[sp.seed == seed]
    if sub.empty:
        raise ValueError(f"seed {seed} missing from {path.name}")
    if sub.url_id.duplicated().any():
        raise ValueError(f"duplicate url_id in {path.name} seed {seed}")
    train = sub[sub.fold == "train"].sort_values("url_id")
    test = sub[sub.fold == "test"].sort_values("url_id")
    return train, test


def split_counts(protocol: str, seed: int) -> dict:
    path = {"random": SPLIT_RANDOM, "sitedisjoint": SPLIT_SITEDISJOINT}[protocol]
    sub = pd.read_csv(path)
    sub = sub[sub.seed == seed]
    return sub.fold.value_counts().to_dict()


def phresh_shards(part: str) -> list[Path]:
    paths = sorted(PHRESH_DIR.glob(f"{part}-*.parquet"))
    if not paths:
        raise FileNotFoundError(f"no {part}-*.parquet under {PHRESH_DIR}")
    return paths


def load_phresh(part: str, columns=("url", "label", "date"),
                limit: int | None = None) -> pd.DataFrame:
    """Read every shard of one partition with the Parquet engine.

    Only the requested columns are read; `html` is never loaded. `limit` exists
    for diagnostic subsets and must never be used for reported results.
    """
    import pyarrow.parquet as pq

    paths = phresh_shards(part)
    if limit:
        paths = paths[:limit]
    frames = []
    for path in paths:
        schema = pq.read_schema(path)
        missing = set(columns) - set(schema.names)
        if missing:
            raise ValueError(f"{path.name}: missing columns {sorted(missing)}")
        frame = pq.read_table(path, columns=list(columns)).to_pandas()
        frame["source_file"] = path.name
        frame["source_row"] = range(len(frame))
        frames.append(frame)
    df = pd.concat(frames, ignore_index=True)
    df["row_id"] = part + ":" + df.source_file + ":" + df.source_row.astype(str)
    return df
