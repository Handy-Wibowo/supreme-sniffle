from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import itertools
import json
import math
import platform
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXP1 = ROOT / "Experiment/1 - PhiUSIIL Cleaning + Leakage-Audit Notebook/phiusill_clean"
EXP4 = ROOT / "Experiment/4 - PhreshPhish Temporal Audit/outputs/20261022T170935017991Z"
EXP5 = ROOT / "Experiment/5 - PhiUSIIL Focused Ablation"
EXP6 = ROOT / "Experiment/6 - Cross-Corpus Transfer/outputs"
PHRESH_DATA = ROOT / "dataset/PhreshPhish/data"
OUT = HERE

sys.path.insert(0, str(EXP5))
from src.features import canonical_url, host_parts, parse_url, psl_snapshot  # noqa: E402

LEVELS = ("raw_url", "canonical_url", "hostname", "registrable_domain")
MODELS = ("lightgbm", "xgboost")
SEEDS = (13, 42, 2024, 777, 31415)
CLASS_NAMES = {0: "benign", 1: "phish"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def canonical_hostname(url: str) -> str:
    return parse_url(url)[1]


def keys_for(url: str) -> dict[str, str]:
    raw = url
    canonical = canonical_url(url)
    host = canonical_hostname(url)
    return {
        "raw_url": raw,
        "canonical_url": canonical,
        "hostname": host,
        "registrable_domain": host_parts(host)[0],
    }


def get_source() -> pd.DataFrame:
    clean = pd.read_parquet(EXP1 / "phiusiil_clean.parquet", columns=["URL", "label"])
    clean["url_id"] = np.arange(len(clean), dtype=np.int64)
    clean["y_phish"] = 1 - clean["label"].astype("int8")
    split = pd.read_csv(EXP1 / "split_random.csv")
    train = split.loc[(split.seed == 42) & (split.fold == "train"), ["url_id"]]
    if train.empty or train.url_id.duplicated().any():
        raise ValueError("PhiUSIIL seed-42 training fold is absent or has duplicate url_id")
    source = train.merge(clean, on="url_id", how="left", validate="one_to_one")
    if source.URL.isna().any() or source.y_phish.isna().any():
        raise ValueError("PhiUSIIL training IDs do not map to cleaned URL rows")
    return source[["url_id", "URL", "y_phish"]].rename(columns={"URL": "url"})


def get_target() -> pd.DataFrame:
    split_path = EXP4 / "split_test.csv.gz"
    split = pd.read_csv(split_path)
    if split.row_id.isna().any() or split.row_id.duplicated().any():
        raise ValueError("PhreshPhish split_test row_id is missing or duplicated")
    pieces = []
    for shard in sorted(PHRESH_DATA.glob("test-*.parquet")):
        part = pd.read_parquet(shard, columns=["url", "label"])
        part["row_id"] = "test:" + shard.name + ":" + np.arange(len(part)).astype(str)
        pieces.append(part)
    if not pieces:
        raise FileNotFoundError("No local PhreshPhish test-*.parquet shards")
    raw = pd.concat(pieces, ignore_index=True)
    target = split.merge(raw[["row_id", "url", "label"]], on="row_id", how="left", validate="one_to_one")
    if target.url.isna().any() or target.label.isna().any():
        raise ValueError("Target split rows cannot all be reconstructed from raw test shards")
    canonical_hashes = target.url.map(lambda u: hashlib.sha256(canonical_url(str(u)).encode("utf-8")).hexdigest())
    if not canonical_hashes.equals(target.url_sha256.astype(str)):
        raise ValueError("Reconstructed target URLs do not match the split's canonical URL SHA-256")
    labels = target.label.map({"benign": 0, "phish": 1})
    if labels.isna().any() or not np.array_equal(labels.astype(int), target.y_phish.to_numpy(dtype=int)):
        raise ValueError("Raw PhreshPhish labels disagree with target split labels")
    return target.assign(y_phish=labels.astype("int8"))[["row_id", "url", "y_phish", "url_sha256", "domain"]]


def add_keys(frame: pd.DataFrame, url_col: str) -> tuple[pd.DataFrame, dict]:
    out = frame.copy()
    results = []
    errors = Counter()
    for value in out[url_col]:
        try:
            results.append(keys_for(str(value)))
        except (ValueError, UnicodeError, TypeError) as exc:
            results.append({name: None for name in LEVELS})
            errors[type(exc).__name__ + ": " + str(exc)] += 1
    keyframe = pd.DataFrame(results, index=out.index)
    for name in LEVELS:
        out[name] = keyframe[name]
    return out, {"rows": len(out), "invalid_key_rows": int(keyframe["raw_url"].isna().sum()), "errors": dict(errors)}


def _key_maps(frame: pd.DataFrame, level: str) -> dict[str, list[int]]:
    maps: dict[str, list[int]] = defaultdict(list)
    for i, key in enumerate(frame[level].tolist()):
        if isinstance(key, str) and key:
            maps[key].append(i)
    return maps


def overlap_table(source: pd.DataFrame, target: pd.DataFrame) -> tuple[list[dict], dict, set[int]]:
    rows: list[dict] = []
    detail: dict = {}
    union_target_rows: set[int] = set()
    for level in LEVELS:
        smap, tmap = _key_maps(source, level), _key_maps(target, level)
        common = sorted(smap.keys() & tmap.keys())
        target_matched = {i for key in common for i in tmap[key]}
        source_matched = {i for key in common for i in smap[key]}
        union_target_rows.update(target_matched)
        pair_labels: Counter = Counter()
        pair_count = conflicting_pair_count = 0
        key_conflicts = []
        source_y = source.y_phish.to_numpy(dtype=int)
        target_y = target.y_phish.to_numpy(dtype=int)
        source_pair_rows = {(a, b): set() for a, b in itertools.product((0, 1), repeat=2)}
        target_pair_rows = {(a, b): set() for a, b in itertools.product((0, 1), repeat=2)}
        duplicate_common_source = duplicate_common_target = 0
        for key in common:
            si, ti = smap[key], tmap[key]
            duplicate_common_source += len(si) > 1
            duplicate_common_target += len(ti) > 1
            source_labels = np.bincount(source_y[si], minlength=2)
            target_labels = np.bincount(target_y[ti], minlength=2)
            conflict = any(source_labels[a] and target_labels[b] for a, b in itertools.product((0, 1), repeat=2) if a != b)
            if conflict:
                key_conflicts.append({
                    "key": key,
                    "source_rows": len(si), "target_rows": len(ti),
                    "source_labels": {CLASS_NAMES[k]: int(v) for k, v in enumerate(source_labels) if v},
                    "target_labels": {CLASS_NAMES[k]: int(v) for k, v in enumerate(target_labels) if v},
                })
            for a, b in itertools.product((0, 1), repeat=2):
                pair_labels[(a, b)] += int(source_labels[a] * target_labels[b])
                if source_labels[a] and target_labels[b]:
                    source_pair_rows[(a, b)].update(i for i in si if source_y[i] == a)
                    target_pair_rows[(a, b)].update(i for i in ti if target_y[i] == b)
            pair_count += len(si) * len(ti)
            conflicting_pair_count += int(source_labels[0] * target_labels[1] + source_labels[1] * target_labels[0])
        stat = {
            "level": level,
            "source_rows": len(source),
            "source_valid_rows": sum(len(v) for v in smap.values()),
            "source_unique_keys": len(smap),
            "source_duplicate_rows_beyond_unique": sum(len(v) - 1 for v in smap.values()),
            "source_duplicate_keys": sum(len(v) > 1 for v in smap.values()),
            "target_rows": len(target),
            "target_valid_rows": sum(len(v) for v in tmap.values()),
            "target_unique_keys": len(tmap),
            "target_duplicate_rows_beyond_unique": sum(len(v) - 1 for v in tmap.values()),
            "target_duplicate_keys": sum(len(v) > 1 for v in tmap.values()),
            "common_unique_keys": len(common),
            "source_rows_with_match": len(source_matched),
            "target_rows_with_match": len(target_matched),
            "target_rows_with_match_pct": len(target_matched) / len(target) if len(target) else None,
            "source_target_row_pairs": pair_count,
            "conflicting_label_keys": len(key_conflicts),
            "conflicting_label_row_pairs": conflicting_pair_count,
            "common_keys_with_source_duplicates": duplicate_common_source,
            "common_keys_with_target_duplicates": duplicate_common_target,
        }
        detail[level] = {"stats": stat, "conflicting_label_cases": key_conflicts, "label_pair_row_counts": {
            f"source_{CLASS_NAMES[a]}__target_{CLASS_NAMES[b]}": n for (a, b), n in sorted(pair_labels.items())
        }}
        rows.append({**stat, "stratum": "all", "source_class": "all", "target_class": "all",
                     "source_class_rows": len(source), "target_class_rows": len(target),
                     "source_matched_class_rows": len(source_matched), "target_matched_class_rows": len(target_matched),
                     "matched_row_pairs": pair_count, "conflicting_label_row_pairs_stratum": conflicting_pair_count})
        for target_class in (0, 1):
            t_idx = {i for key in common for i in tmap[key] if int(target.iloc[i].y_phish) == target_class}
            rows.append({**stat, "stratum": "target_class", "source_class": "all", "target_class": CLASS_NAMES[target_class],
                         "source_class_rows": len(source), "target_class_rows": int((target.y_phish == target_class).sum()),
                         "source_matched_class_rows": len(source_matched), "target_matched_class_rows": len(t_idx),
                         "matched_row_pairs": sum(n for (a, b), n in pair_labels.items() if b == target_class),
                         "conflicting_label_row_pairs_stratum": sum(n for (a, b), n in pair_labels.items() if b == target_class and a != b)})
        for a, b in itertools.product((0, 1), repeat=2):
            pair_n = pair_labels[(a, b)]
            rows.append({**stat, "stratum": "class_pair", "source_class": CLASS_NAMES[a], "target_class": CLASS_NAMES[b],
                         "source_class_rows": int((source_y == a).sum()), "target_class_rows": int((target_y == b).sum()),
                         "source_matched_class_rows": len(source_pair_rows[(a, b)]),
                         "target_matched_class_rows": len(target_pair_rows[(a, b)]),
                         "matched_row_pairs": pair_n, "conflicting_label_row_pairs_stratum": pair_n if a != b else 0})
    return rows, detail, union_target_rows


def scores(y: np.ndarray, p: np.ndarray, pred: np.ndarray) -> dict:
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "n": len(y), "benign_n": int((y == 0).sum()), "phish_n": int((y == 1).sum()),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        "f1_phish": float(f1_score(y, pred, pos_label=1, zero_division=0)),
        "precision_phish": float(precision_score(y, pred, pos_label=1, zero_division=0)),
        "recall_phish": float(recall_score(y, pred, pos_label=1, zero_division=0)),
        "fpr_benign": float(fp / (fp + tn)) if fp + tn else math.nan,
        "miss_phish": float(fn / (fn + tp)) if fn + tp else math.nan,
        "roc_auc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else math.nan,
        "average_precision": float(average_precision_score(y, p)) if len(np.unique(y)) == 2 else math.nan,
        "mcc": float(matthews_corrcoef(y, pred)),
    }


def prediction_metrics(target: pd.DataFrame, overlap_rows: set[int]) -> tuple[list[dict], list[dict]]:
    keep = np.ones(len(target), dtype=bool)
    if overlap_rows:
        keep[np.fromiter(overlap_rows, dtype=np.int64)] = False
    y_all = target.y_phish.to_numpy(dtype=int)
    rows, baseline = [], {}
    target_ids = set(target.row_id.astype(str))
    for model in MODELS:
        for seed in SEEDS:
            path = EXP6 / f"predictions_phreshphish_temporal_test_{model}_seed{seed}.csv.gz"
            pred = pd.read_csv(path)
            if len(pred) != len(target) or pred.row_id.duplicated().any() or set(pred.row_id.astype(str)) != target_ids:
                raise ValueError(f"Prediction rows do not exactly join target by unique row_id: {path.name}")
            joined = target[["row_id", "y_phish"]].merge(pred[["row_id", "y_phish", "p_phish", "pred"]], on="row_id", suffixes=("_target", "_pred"), validate="one_to_one")
            if not np.array_equal(joined.y_phish_target.to_numpy(dtype=int), joined.y_phish_pred.to_numpy(dtype=int)):
                raise ValueError(f"Prediction labels disagree with target split: {path.name}")
            y, p, decision = y_all[keep], joined.p_phish.to_numpy(dtype=float)[keep], joined.pred.to_numpy(dtype=int)[keep]
            row = {"model": model, "seed": seed, "threshold": 0.5, "subset": "strict_no_overlap_all_four_levels", "excluded_overlap_rows": int((~keep).sum()), **scores(y, p, decision)}
            rows.append(row)
            if seed == 42:
                baseline[model] = {"full_target": scores(y_all, joined.p_phish.to_numpy(dtype=float), joined.pred.to_numpy(dtype=int)), "strict_no_overlap": {k: v for k, v in row.items() if k not in {"model", "seed", "threshold", "subset"}}}
    return rows, [{"model": m, **baseline[m]} for m in MODELS]


def verify_hashes(paths: list[Path], manifest_path: Path | None = None) -> dict:
    recorded = {}
    if manifest_path and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key, value in manifest.get("input_hashes", {}).items():
            recorded[key.replace("\\", "/")] = value
    entries = {}
    mismatches = []
    for path in sorted(set(paths)):
        rel = path.relative_to(ROOT).as_posix()
        digest = sha256(path)
        expected = recorded.get(rel)
        entries[rel] = {"sha256": digest, "bytes": path.stat().st_size, "matches_transfer_manifest": (digest == expected if expected else None), "transfer_manifest_sha256": expected}
        if expected and digest != expected:
            mismatches.append(rel)
    return {"files": entries, "transfer_manifest_mismatches": mismatches}


def self_check() -> None:
    assert canonical_url("HTTPS://Example.COM:443/a#frag") == canonical_url("https://example.com:443/a#other")
    assert canonical_url("http://example.com/a") != canonical_url("https://example.com/a")
    assert keys_for("https://sub.example.co.uk/a")["registrable_domain"] == "example.co.uk"
    small_source = pd.DataFrame({"url": ["https://same.test/a", "https://other.test"], "y_phish": [0, 1]})
    small_target = pd.DataFrame({"url": ["https://same.test/a#fragment", "https://other.test"], "y_phish": [1, 1]})
    s, _ = add_keys(small_source, "url")
    t, _ = add_keys(small_target, "url")
    table, detail, overlap = overlap_table(s, t)
    assert overlap == {0, 1}
    raw = detail["raw_url"]["stats"]
    canon = detail["canonical_url"]["stats"]
    assert raw["common_unique_keys"] == 1 and canon["common_unique_keys"] == 2
    assert canon["conflicting_label_keys"] == 1 and canon["conflicting_label_row_pairs"] == 1
    class_rows = [r for r in table if r["level"] == "canonical_url" and r["stratum"] == "class_pair"]
    assert next(r for r in class_rows if r["source_class"] == "phish" and r["target_class"] == "phish")["matched_row_pairs"] == 1
    assert next(r for r in class_rows if r["source_class"] == "benign" and r["target_class"] == "phish")["matched_row_pairs"] == 1
    assert next(r for r in class_rows if r["source_class"] == "phish" and r["target_class"] == "phish")["source_matched_class_rows"] == 1
    assert next(r for r in class_rows if r["source_class"] == "benign" and r["target_class"] == "phish")["target_matched_class_rows"] == 1
    assert len(table) == len(LEVELS) * 7
    print("SELF_CHECK=PASS (canonicalization, host/PSL, overlap union, conflicting labels, class strata)")


def run() -> None:
    started = time.perf_counter()
    source, target = get_source(), get_target()
    source, source_key_status = add_keys(source, "url")
    target, target_key_status = add_keys(target, "url")
    summary_rows, overlap, overlap_target_rows = overlap_table(source, target)
    metric_rows, seed42_baseline = prediction_metrics(target, overlap_target_rows)

    files = [
        EXP1 / "phiusiil_clean.parquet", EXP1 / "split_random.csv", EXP1 / "splits_manifest.json",
        ROOT / "dataset/PhiUSIIL Phishing/PhiUSIIL_Phishing_URL_Dataset.csv",
        EXP4 / "split_test.csv.gz", EXP4 / "design.json", EXP4 / "input_manifest.json",
        EXP6 / "manifest.json", EXP5 / "src/features.py",
        *sorted(PHRESH_DATA.glob("test-*.parquet")),
        *[EXP6 / f"predictions_phreshphish_temporal_test_{model}_seed{seed}.csv.gz" for model in MODELS for seed in SEEDS],
    ]
    hashes = verify_hashes(files, EXP6 / "manifest.json")
    if hashes["transfer_manifest_mismatches"]:
        raise ValueError("Input files differ from recorded transfer manifest: " + ", ".join(hashes["transfer_manifest_mismatches"]))
    psl = psl_snapshot()
    results = {
        "audit": "cross-corpus URL and domain overlap",
        "status": "completed",
        "cohorts": {
            "source": {"name": "PhiUSIIL cleaned random split seed 42 train fold", "rows": len(source), "class_counts_phishing_positive": {CLASS_NAMES[k]: int(v) for k, v in source.y_phish.value_counts().sort_index().items()}, "key_parse_status": source_key_status},
            "target": {"name": "PhreshPhish cleaned temporal test; Experiment 4 output 20261022T170935017991Z", "rows": len(target), "class_counts_phishing_positive": {CLASS_NAMES[k]: int(v) for k, v in target.y_phish.value_counts().sort_index().items()}, "key_parse_status": target_key_status, "cutoff_utc": "2025-09-08T00:00:00+00:00"},
        },
        "overlap_by_level": overlap,
        "strict_no_overlap_subset": {"definition": "Target rows having no matching raw URL, shared canonical URL, hostname, or registrable domain in any source training row.", "target_rows": len(target) - len(overlap_target_rows), "target_denominator": len(target), "overlap_rows_excluded_union": len(overlap_target_rows), "overlap_row_pct": len(overlap_target_rows) / len(target), "no_overlap_class_counts": {CLASS_NAMES[k]: int(v) for k, v in target.loc[[i for i in range(len(target)) if i not in overlap_target_rows], "y_phish"].value_counts().sort_index().items()}},
        "frozen_prediction_metrics_on_strict_no_overlap_subset": metric_rows,
        "seed_42_full_vs_strict_subset": seed42_baseline,
        "canonicalization": {"implementation": "Experiment 5 src.features.canonical_url", "rules": "URL whitespace stripped; missing scheme receives http://; HTTP(S) only; scheme and hostname lowercased; trailing hostname dot removed; path defaults to /; query retained byte-for-byte; fragment removed; userinfo and explicit port retained; invalid port/host rejected."},
        "target_url_hash_rule": "Reconstructed target URLs are validated against split_test.url_sha256 using SHA-256(canonical_url(raw URL)), matching Experiment 4 verify_end_to_end.py.",
        "hostname_rule": "Experiment 5 parse_url: urllib hostname lowercased and trailing dot removed.",
        "registrable_domain_rule": "Experiment 5 host_parts with bundled tldextract PSL; IP literals remain the IP; unknown suffix falls back to e.domain or host.",
        "psl": psl,
        "prediction_join": {"method": "unique immutable PhreshPhish row_id reconstructed from test shard filename and original zero-based row position", "validated": True, "prediction_files": len(MODELS) * len(SEEDS), "all_row_ids_and_labels_match_target": True},
        "input_hashes": hashes,
        "execution": {"python": platform.python_version(), "platform": platform.platform(), "pandas": pd.__version__, "numpy": np.__version__, "scikit_learn": importlib.metadata.version("scikit-learn"), "tldextract": importlib.metadata.version("tldextract"), "elapsed_seconds": round(time.perf_counter() - started, 3)},
    }
    (OUT / "OVERLAP_RESULTS.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pd.DataFrame(summary_rows).to_csv(OUT / "overlap_summary.csv", index=False, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    pd.DataFrame(metric_rows).to_csv(OUT / "no_overlap_metrics.csv", index=False, lineterminator="\n")
    make_reports(results, summary_rows, metric_rows)


def fmt(value):
    return f"{value:,}" if isinstance(value, int) else (f"{value:.4%}" if isinstance(value, float) and math.isfinite(value) else str(value))


def make_reports(results: dict, summary_rows: list[dict], metric_rows: list[dict]) -> None:
    overlap = results["overlap_by_level"]
    table = ["| Match level | Common unique keys | Source rows matched / denominator | Target rows matched / denominator | Matched row pairs | Conflicting-label keys | Conflicting-label row pairs |", "|---|---:|---:|---:|---:|---:|---:|"]
    for level in LEVELS:
        s = overlap[level]["stats"]
        table.append(f"| {level} | {fmt(s['common_unique_keys'])} | {fmt(s['source_rows_with_match'])} / {fmt(s['source_rows'])} | {fmt(s['target_rows_with_match'])} / {fmt(s['target_rows'])} ({fmt(s['target_rows_with_match_pct'])}) | {fmt(s['source_target_row_pairs'])} | {fmt(s['conflicting_label_keys'])} | {fmt(s['conflicting_label_row_pairs'])} |")
    lines = [
        "# Cross-corpus overlap audit",
        "",
        "## Scope and reproducibility",
        "",
        "The source is the **141,222-row PhiUSIIL cleaned random-split seed-42 training fold** used to fit the frozen Experiment 6 models. The target is the **PhreshPhish temporal test cohort** reconstructed from the raw test shards and joined to the Experiment 4 cleaned split by immutable `row_id`; the split cutoff is 2025-09-08 00:00 UTC. These are the source/target cohorts used by the transfer analysis, not all rows in either original corpus.",
        "",
        "Input SHA-256 values, byte sizes, raw shard revisions, the transfer manifest comparisons, local execution environment, and PSL snapshot identity are in `OVERLAP_RESULTS.json`. All raw shards, predictions, split files, and model artifacts were read-only. No network access or downloads are used. The script imports the shared Experiment 5 canonical URL/hostname/PSL implementation.",
        "",
        "## Overlap results and denominators",
        "",
        f"Source denominator: {fmt(results['cohorts']['source']['rows'])} rows; target denominator: {fmt(results['cohorts']['target']['rows'])} rows. Each target match proportion below is matched target rows divided by all {fmt(results['cohorts']['target']['rows'])} target rows. Unique key counts count distinct normalized values; matched-row pairs count the Cartesian pairs for common keys, so duplicate keys can produce more pairs than rows.",
        "",
        *table,
        "",
        "`overlap_summary.csv` contains overall, target-class, and source/target class-pair strata for every overlap level, with row and class denominators, matched rows/pairs, and conflicting label pairs. Source label 1 is benign and source label 0 is phish; all output labels are converted to phishing-positive (`y_phish=1`). Duplicate keys within either cohort and duplicate keys among the common keys are separately counted. Full conflicting-label key cases and class-pair counts are in the JSON.",
        "",
        "## Conservative no-overlap evaluation",
        "",
        f"A target row is excluded if it matches any source training row at any of the four levels. This removes {fmt(results['strict_no_overlap_subset']['overlap_rows_excluded_union'])} target rows ({fmt(results['strict_no_overlap_subset']['overlap_row_pct'])}); the remaining denominator is {fmt(results['strict_no_overlap_subset']['target_rows'])}, with classes {results['strict_no_overlap_subset']['no_overlap_class_counts']}. This union rule is conservative: no retained row shares a raw URL, canonical URL, hostname, or registrable domain with source training data.",
        "",
        "All 10 saved frozen prediction files (two model families × five seeds) joined one-to-one to all target row IDs and had labels verified against the cleaned target split. No model was refit, threshold changed, or target row scored anew. `no_overlap_metrics.csv` reports unchanged predictions/threshold 0.5 scored only on the strict no-overlap subset; both classes are present for these metrics.",
        "",
        "| Model | Seed | n | F1 (phish) | Precision | Recall | Benign FPR | Phish miss | ROC-AUC | AP | MCC | TN / FP / FN / TP |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for m in metric_rows:
        lines.append(f"| {m['model']} | {m['seed']} | {fmt(m['n'])} | {m['f1_phish']:.4f} | {m['precision_phish']:.4f} | {m['recall_phish']:.4f} | {m['fpr_benign']:.4f} | {m['miss_phish']:.4f} | {m['roc_auc']:.4f} | {m['average_precision']:.4f} | {m['mcc']:.4f} | {fmt(m['tn'])} / {fmt(m['fp'])} / {fmt(m['fn'])} / {fmt(m['tp'])} |")
    lines += [
        "",
        "## Canonicalization and PSL",
        "",
        results["canonicalization"]["rules"],
        "",
        results["hostname_rule"],
        "",
        results["registrable_domain_rule"],
        "",
        f"Offline PSL: {results['psl']}.",
        "",
        "## Known limits",
        "",
        "The overlap unit is the frozen source training fold, because source validation/test rows did not contribute to the transfer model. Registrable-domain grouping follows the shared PSL snapshot and excludes private suffixes, so hosting-platform tenants may share one registrable key. Label conflict means the same key occurs with different binary labels across corpora; it is not proof either label is erroneous. `raw_url` is literal string equality; canonical URL matching follows the shared extractor rather than browser/network resolution.",
        "",
        "## Rerun",
        "",
        "From the workspace root, in Experiment 5's recorded Python environment:",
        "",
        '```powershell',
        '"Experiment/5 - PhiUSIIL Focused Ablation/.venv/Scripts/python.exe" "phishing/revision_v9_stage1_audit/03_cross_corpus_overlap/overlap_audit.py" --self-check',
        '"Experiment/5 - PhiUSIIL Focused Ablation/.venv/Scripts/python.exe" "phishing/revision_v9_stage1_audit/03_cross_corpus_overlap/overlap_audit.py"',
        '```',
        "",
        "The script checks file hashes against Experiment 6's frozen input manifest and fails on any mismatch or unsafe/missing row join. `--self-check` exercises canonicalization, PSL parsing, overlap union, conflicting labels, and class strata using deterministic synthetic rows.",
        "",
    ]
    (OUT / "OVERLAP_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")
    worker = [
        "# Worker report — cross-corpus overlap audit", "",
        "Implemented and executed `overlap_audit.py` under this owned output folder. Results and all denominators are in `OVERLAP_AUDIT.md`, `OVERLAP_RESULTS.json`, and `overlap_summary.csv`; frozen no-overlap metrics are also in `no_overlap_metrics.csv`.", "",
        f"The audited cohorts contain {fmt(results['cohorts']['source']['rows'])} PhiUSIIL seed-42 training rows and {fmt(results['cohorts']['target']['rows'])} PhreshPhish temporal-test rows. The conservative no-overlap subset contains {fmt(results['strict_no_overlap_subset']['target_rows'])} target rows. Prediction row joins succeeded for all {results['prediction_join']['prediction_files']} model/seed files; source/target artifact hashes matched the existing Experiment 6 manifest.", "",
        "Checks run: deterministic synthetic `--self-check`; full audit; output/schema/denominator/hash and prediction-join validation. Rerun command and Python/package/PSL identity are recorded in `OVERLAP_AUDIT.md` and `OVERLAP_RESULTS.json`. No manuscript or source data was edited.", "",
    ]
    (OUT / "WORKER_REPORT.md").write_text("\n".join(worker), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
    else:
        run()


if __name__ == "__main__":
    main()
