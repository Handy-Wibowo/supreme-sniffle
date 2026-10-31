"""Data audit: verified counts, hashes, label semantics, split alignment, PSL keys.

Every function returns plain Python objects so the audit notebook can display
them and write them to CSV/JSON. Nothing is trained here.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import data
from .features import canonical_url, domain_for, psl_snapshot
from .provenance import (EXPERIMENT_DIR, WORKSPACE, environment_snapshot,
                         file_entry, sha256_file, utc_now, write_json)


# ------------------------------------------------------------------- PhiUSIIL
def raw_csv_audit() -> dict:
    """Structure of the untouched source CSV (read-only)."""
    header = pd.read_csv(data.PHIUSIIL_RAW, nrows=0)
    df = pd.read_csv(data.PHIUSIIL_RAW, usecols=["URL", "label"])
    labels = df.label.value_counts().sort_index().to_dict()
    per_url = df.groupby("URL").label.nunique()
    return {
        "path": str(data.PHIUSIIL_RAW.relative_to(WORKSPACE)),
        "bytes": data.PHIUSIIL_RAW.stat().st_size,
        "sha256": sha256_file(data.PHIUSIIL_RAW),
        "n_columns": int(header.shape[1]),
        "columns": list(header.columns),
        "n_rows": int(len(df)),
        "label_counts": {int(k): int(v) for k, v in labels.items()},
        "label_meaning": {"1": "benign (source encoding)", "0": "phishing (source encoding)"},
        "duplicate_url_rows": int(df.URL.duplicated().sum()),
        "urls_with_conflicting_labels": int((per_url > 1).sum()),
        "null_urls": int(df.URL.isna().sum()),
    }


def domain_keys(df: pd.DataFrame) -> pd.Series:
    """Registrable domain recomputed with the frozen PSL, indexed by url_id."""
    keys = df["URL"].map(domain_for)
    keys.index = df.url_id.to_numpy()
    keys.name = "domain_psl"
    return keys


def clean_audit(df: pd.DataFrame, keys: pd.Series | None = None) -> dict:
    """Integrity of the cleaned table used for every PhiUSIIL fit."""
    per_url = df.groupby("URL").label.nunique()
    stored = df["registrable_domain"]
    recomputed = keys if keys is not None else domain_keys(df)
    mismatch = (stored.fillna("<NA>") != recomputed).sum()
    ip_rows = int(df.IsDomainIP.sum())
    return {
        "path": str(data.PHIUSIIL_CLEAN.relative_to(WORKSPACE)),
        "bytes": data.PHIUSIIL_CLEAN.stat().st_size,
        "sha256": sha256_file(data.PHIUSIIL_CLEAN),
        "n_rows": int(len(df)),
        "n_columns": int(df.shape[1]),
        "label_counts": {int(k): int(v) for k, v in df.label.value_counts().sort_index().items()},
        "y_phish_counts": {int(k): int(v) for k, v in df.y_phish.value_counts().sort_index().items()},
        "url_id_min": int(df.url_id.min()),
        "url_id_max": int(df.url_id.max()),
        "url_id_unique": int(df.url_id.nunique()),
        "url_id_equals_position": bool(np.array_equal(df.url_id.to_numpy(), np.arange(len(df)))),
        "duplicate_url_rows": int(df.URL.duplicated().sum()),
        "urls_with_conflicting_labels": int((per_url > 1).sum()),
        "null_cells_total": int(df.isna().sum().sum()),
        "domain_null": int(stored.isna().sum()),
        "domain_unique": int(stored.nunique()),
        "domain_key_mismatch_vs_psl": int(mismatch),
        "domain_key_mismatch_examples": stored[stored.fillna("<NA>") != recomputed].head(5).tolist(),
        "is_domain_ip_rows": ip_rows,
        "domain_exposure_true": int(df.domain_exposure.sum()),
        "psl": psl_snapshot(),
    }


def feature_missingness(df: pd.DataFrame) -> pd.DataFrame:
    """Per-feature nulls and dtypes for the three configurations."""
    rows = []
    for config, feats in data.CONFIGS.items():
        for feat in feats:
            if feat not in df.columns:
                rows.append({"config": config, "feature": feat, "present": False,
                             "dtype": "", "nulls": None})
                continue
            rows.append({
                "config": config, "feature": feat, "present": True,
                "dtype": str(df[feat].dtype), "nulls": int(df[feat].isna().sum()),
            })
    return pd.DataFrame(rows)


def a2_vs_source_agreement(df: pd.DataFrame, a2: pd.DataFrame,
                           ids=None, n: int = 20000,
                           seed: int = 42) -> pd.DataFrame:
    """Exact agreement between the new URL extractor and same-named source columns.

    A2 is a reimplementation (definitions taken from the legacy extractor, not from
    the parquet). This table quantifies the drift instead of asserting identity.
    ``ids`` lets a caller pass a precomputed sample of ``url_id`` values.
    """
    source = df.set_index("url_id")
    if ids is None:
        ids = source.index.to_series().sample(n=min(n, len(source)),
                                              random_state=seed).to_numpy()
    ids = pd.Index(ids).intersection(a2.index)
    rows = []
    for feature in data.A2:
        if feature not in source.columns:
            continue
        src = source.loc[ids, feature].to_numpy(dtype=float)
        new = a2.loc[ids, feature].to_numpy(dtype=float)
        diff = np.abs(src - new)
        rows.append({
            "feature": feature,
            "rows_compared": int(len(ids)),
            "exact_agreement": float((diff == 0).mean()),
            "max_abs_diff": float(diff.max()),
            "mean_abs_diff": float(diff.mean()),
        })
    return pd.DataFrame(rows).sort_values("exact_agreement")

SHARED_HOSTING_SUFFIXES = (
    # Registrable domains that host many independent tenants. The list is
    # illustrative, not exhaustive: it exists to label the largest keys, not to
    # classify the corpus. A domain key is NOT a tenant boundary.
    "web.app", "firebaseapp.com", "repl.co", "weeblysite.com", "ipfs.io",
    "workers.dev", "square.site", "dweb.link", "pantheonsite.io", "github.io",
    "blogspot.com", "wordpress.com", "netlify.app", "vercel.app", "pages.dev",
)

def domain_concentration(df: pd.DataFrame, keys: pd.Series | None = None,
                         top: int = 10) -> pd.DataFrame:
    """Row share of the largest domain keys and whether they host many tenants.

    "Site-disjoint" separates registrable domains, which for a shared-hosting
    suffix is not a tenant boundary; this table keeps that limit visible.
    """
    psl = keys if keys is not None else domain_keys(df)
    counts = psl.value_counts()
    rows = []
    for rank, (domain, n) in enumerate(counts.head(top).items(), start=1):
        rows.append({
            "rank": rank,
            "domain": domain,
            "rows": int(n),
            "share_of_corpus": round(float(n / len(psl)), 6),
            "shared_hosting_suspected": domain in SHARED_HOSTING_SUFFIXES,
        })
    rows.append({
        "rank": "total_top",
        "domain": f"top {top}",
        "rows": int(counts.head(top).sum()),
        "share_of_corpus": round(float(counts.head(top).sum() / len(psl)), 6),
        "shared_hosting_suspected": "",
    })
    return pd.DataFrame(rows)

def split_audit(df: pd.DataFrame, keys: pd.Series | None = None) -> pd.DataFrame:
    """Coverage, class balance and train/test overlap for every protocol/seed.

    Two domain-overlap columns are reported: the frozen ``registrable_domain``
    column and the PSL key this pipeline actually uses. For site-disjoint splits
    both must be zero.
    """
    rows = []
    domain = df.set_index("url_id")["registrable_domain"]
    psl = keys if keys is not None else domain_keys(df)
    y = df.set_index("url_id")["y_phish"]
    url = df.set_index("url_id")["URL"]
    canonical = pd.Series([canonical_url(u) for u in url.to_numpy()], index=url.index)
    for protocol in data.PROTOCOLS_PHIUSIIL:
        path = {"random": data.SPLIT_RANDOM, "sitedisjoint": data.SPLIT_SITEDISJOINT}[protocol]
        full = pd.read_csv(path)
        for seed in data.SEEDS:
            sub = full[full.seed == seed]
            tr = sub[sub.fold == "train"].url_id
            te = sub[sub.fold == "test"].url_id
            va = sub[sub.fold == "val"].url_id
            ids = sub.url_id
            tr_dom = set(domain.loc[tr])
            te_dom = set(domain.loc[te])
            tr_psl = set(psl.loc[tr])
            te_psl = set(psl.loc[te])
            rows.append({
                "protocol": protocol,
                "seed": seed,
                "file": path.name,
                "file_sha256": sha256_file(path),
                "rows_in_file": int(len(sub)),
                "unique_ids": int(ids.nunique()),
                "covers_all_rows": bool(ids.nunique() == len(df) and ids.min() == 0
                                        and ids.max() == len(df) - 1),
                "train_rows": int(len(tr)),
                "val_rows": int(len(va)),
                "test_rows": int(len(te)),
                "train_phish": int(y.loc[tr].sum()),
                "test_phish": int(y.loc[te].sum()),
                "train_phish_share": round(float(y.loc[tr].mean()), 6),
                "test_phish_share": round(float(y.loc[te].mean()), 6),
                "train_url_overlap": int(len(set(url.loc[tr]) & set(url.loc[te]))),
                # Exact-URL overlap is not the only leak surface: two different
                # strings can canonicalise to the same key (case, default port,
                # fragment). Reported, not silently removed - the frozen split
                # files are the protocol's split.
                "train_test_canonical_overlap": int(len(set(canonical.loc[tr]) & set(canonical.loc[te]))),
                "test_rows_sharing_canonical_key_with_train": int(
                    canonical.loc[te].isin(set(canonical.loc[tr])).sum()),
                "train_test_domain_overlap": int(len(tr_dom & te_dom)),
                "train_test_domain_overlap_psl": int(len(tr_psl & te_psl)),
                "train_domains": int(len(tr_dom)),
                "test_domains": int(len(te_dom)),
                "train_domains_psl": int(len(tr_psl)),
                "test_domains_psl": int(len(te_psl)),
                "val_used_for_training": False,
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------- PhreshPhish
def phresh_shard_manifest(hash_files: bool = True) -> pd.DataFrame:
    """One row per Parquet shard, read with the Parquet engine (not text)."""
    import pyarrow.parquet as pq

    rows = []
    for part in ("train", "test"):
        for path in data.phresh_shards(part):
            meta = pq.ParquetFile(path).metadata
            rows.append({
                "partition": part,
                "file": path.name,
                "bytes": path.stat().st_size,
                "rows": meta.num_rows,
                "row_groups": meta.num_row_groups,
                "columns": ",".join(pq.read_schema(path).names),
                "sha256": sha256_file(path) if hash_files else "",
            })
    return pd.DataFrame(rows)


def phresh_audit(train: pd.DataFrame, test: pd.DataFrame) -> dict:
    """Label semantics, dates, duplicates, cutoff behaviour and parseability."""
    out = {"captured_at": utc_now()}
    for name, df in (("train", train), ("test", test)):
        dates = pd.to_datetime(df.date, errors="coerce", utc=True)
        out[name] = {
            "rows": int(len(df)),
            "label_counts": {str(k): int(v) for k, v in df.label.value_counts().items()},
            "unknown_labels": sorted(set(df.label.unique()) - {"benign", "phish"}),
            "date_min": str(dates.min()),
            "date_max": str(dates.max()),
            "null_dates": int(dates.isna().sum()),
            "rows_before_cutoff": int((dates < data.CUTOFF_UTC).sum()),
            "rows_at_or_after_cutoff": int((dates >= data.CUTOFF_UTC).sum()),
            "duplicate_url_rows": int(df.url.duplicated().sum()),
        }
    # canonical keys are computed once and reused for the duplicate/conflict check
    tr_keys = train.url.map(_safe_canonical)
    te_keys = test.url.map(_safe_canonical)
    out["train"]["unparseable_urls"] = int(tr_keys.isna().sum())
    out["test"]["unparseable_urls"] = int(te_keys.isna().sum())
    # The dedup policy in prepare_phresh works on canonical keys, so exact-string
    # duplicate counts understate what gets removed; report both.
    out["train"]["duplicate_canonical_url_rows"] = int(tr_keys.duplicated().sum())
    out["test"]["duplicate_canonical_url_rows"] = int(te_keys.duplicated().sum())
    both = pd.concat([train.assign(key=tr_keys), test.assign(key=te_keys)], ignore_index=True)
    both = both[both.key.notna()]
    out["duplicate_canonical_urls_across_partitions"] = int(both.key.duplicated().sum())
    conflict = both.groupby("key").label.nunique()
    out["canonical_urls_with_conflicting_labels"] = int((conflict > 1).sum())
    out["cutoff_utc"] = str(data.CUTOFF_UTC)
    out["cutoff_effect"] = {
        "train_rows_removed_at_or_after_cutoff": int(
            (pd.to_datetime(train.date, utc=True) >= data.CUTOFF_UTC).sum()),
        "test_rows_before_cutoff": int(
            (pd.to_datetime(test.date, utc=True) < data.CUTOFF_UTC).sum()),
    }
    return out


def _safe_canonical(u):
    try:
        return canonical_url(u)
    except (ValueError, UnicodeError, AttributeError):
        return np.nan


# ------------------------------------------------------------------- writing
def write_audit_outputs(out_dir: Path, payload: dict) -> dict:
    """Persist the audit bundle; returns the file list for the report."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, obj in payload.items():
        path = out_dir / name
        if isinstance(obj, pd.DataFrame):
            obj.to_csv(path, index=False)
        else:
            write_json(path, obj)
        written.append({"file": str(path.relative_to(EXPERIMENT_DIR)),
                        "bytes": path.stat().st_size,
                        "sha256": sha256_file(path)})
    write_json(out_dir / "environment.json", environment_snapshot())
    written.append({"file": str((out_dir / "environment.json").relative_to(EXPERIMENT_DIR)),
                    "bytes": (out_dir / "environment.json").stat().st_size,
                    "sha256": sha256_file(out_dir / "environment.json")})
    return {"written": written}


def input_manifest(phresh_manifest: pd.DataFrame | None = None) -> dict:
    """Hashes and row counts of every input the experiment reads."""
    entries = [
        file_entry(data.PHIUSIIL_CLEAN, "PhiUSIIL cleaned table"),
        file_entry(data.SPLIT_RANDOM, "PhiUSIIL random split"),
        file_entry(data.SPLIT_SITEDISJOINT, "PhiUSIIL site-disjoint split"),
        file_entry(data.PHIUSIIL_RAW, "PhiUSIIL raw CSV (audit only, never trained on)"),
    ]
    manifest = {"captured_at": utc_now(), "files": entries}
    if phresh_manifest is not None:
        manifest["phreshphish"] = {
            "root": str(data.PHRESH_DIR.relative_to(WORKSPACE)),
            "shards": int(len(phresh_manifest)),
            "rows": int(phresh_manifest.rows.sum()),
            "bytes": int(phresh_manifest.bytes.sum()),
            "shards_by_partition": phresh_manifest.partition.value_counts().to_dict(),
            "detail_file": "phresh_shard_manifest.csv",
        }
    return manifest
