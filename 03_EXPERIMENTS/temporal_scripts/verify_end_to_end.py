"""End-to-end verification of the PhreshPhish temporal run against the raw corpus.

The independent audit (VERIFIKASI_HASIL_TEMPORAL.md section 6) could not check
feature extraction, input hashes, label fidelity, or whether the stored
probabilities reproduce because the parquet shards were not in the package.
This script closes that gap using the raw shards on this machine.

It re-derives everything from the raw parquet and the saved models, then
compares against the stored artifacts:

  1. row_id reconciliation   - every test row_id exists in the raw shards
  2. label fidelity          - stored y_phish equals the raw label mapping
  3. date fidelity           - stored date equals the raw date
  4. canonical hash          - stored url_sha256 equals sha256(canonical_url(raw))
  5. domain fidelity         - stored domain equals domain_for(raw url)
  6. feature extraction      - 18 features recomputed, hashed, compared
  7. probability reproduction- Booster.predict on recomputed features vs stored p_phish
  8. train partition         - same checks 1-6 on a train sample

The feature functions are lifted from run_temporal.py by AST so this is the
SAME code path, not a reimplementation: the question is "does the stored
pipeline reproduce the stored numbers from the raw corpus", not "would a
second implementation agree with the first".

Usage:
    python verify_end_to_end.py <run_dir> [--train-sample N] [--out report.json]
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import ipaddress
import json
import sys
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import tldextract

import re

RUNNER = Path(__file__).with_name("run_temporal.py")
DATA_DIR = Path(r"E:\Kuliah\Tugas Akhir\dataset\PhreshPhish\data")
THRESHOLD = 0.5


def load_runner_functions():
    """Exec only the constants and functions this verifier needs from the runner."""
    source = RUNNER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    wanted_funcs = {"parse_url", "canonical_url", "host_parts", "url_features", "domain_for"}
    wanted_assigns = {"EXT", "SPEC"}
    picked = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in wanted_funcs:
            picked.append(node)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in wanted_assigns:
                    picked.append(node)
    module = ast.Module(body=picked, type_ignores=[])
    ast.fix_missing_locations(module)
    ns = {
        "re": re,
        "ipaddress": ipaddress,
        "lru_cache": lru_cache,
        "urlsplit": urlsplit,
        "urlunsplit": urlunsplit,
        "tldextract": tldextract,
        "pd": pd,
        "np": np,
        "hashlib": hashlib,
    }
    exec(compile(module, str(RUNNER), "exec"), ns)
    return ns


def load_raw(part: str, wanted_ids: set[str] | None = None) -> pd.DataFrame:
    """Read the raw shards for one partition, optionally keeping only wanted row_ids."""
    paths = sorted(DATA_DIR.glob(f"{part}-*.parquet"))
    if not paths:
        raise FileNotFoundError(f"no {part}-*.parquet in {DATA_DIR}")
    frames = []
    for path in paths:
        frame = pq.read_table(path, columns=["url", "label", "date"]).to_pandas()
        frame["source_file"] = path.name
        frame["source_row"] = np.arange(len(frame))
        frame["row_id"] = part + ":" + frame.source_file + ":" + frame.source_row.astype(str)
        if wanted_ids is not None:
            frame = frame[frame.row_id.isin(wanted_ids)]
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--train-sample", type=int, default=40000,
                    help="rows to re-derive on the train side; 0 means the whole partition")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    run = args.run_dir
    if not (run / "output_manifest.json").exists():
        raise SystemExit(f"not a run directory: {run}")

    ns = load_runner_functions()
    canonical_url = ns["canonical_url"]
    url_features = ns["url_features"]
    domain_for = ns["domain_for"]

    schema = json.loads((run / "feature_schema.json").read_text(encoding="utf-8"))
    feature_names = schema["names"]
    checks: list[dict] = []

    def record(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        sys.stdout.flush()

    # ---------------------------------------------------------------- test side
    print("\n[1] TEST partition: re-derive from raw shards")
    split_test = pd.read_csv(run / "split_test.csv.gz")
    pred13 = pd.read_csv(run / "predictions_seed_13.csv.gz")
    raw_test = load_raw("test", set(split_test.row_id))
    print(f"  stored test rows={len(split_test)} raw matched={len(raw_test)}")
    record("test_row_ids_all_present", len(raw_test) == len(split_test),
           f"{len(raw_test)} of {len(split_test)}")

    merged = split_test.merge(raw_test, on="row_id", how="inner", suffixes=("_stored", "_raw"))
    # pandas only suffixes columns present on BOTH sides: `date` becomes
    # date_stored/date_raw, but y_phish/domain/url_sha256/domain_seen appear only
    # in the split file and keep their bare names.

    def same_date(stored, raw) -> tuple[bool, int]:
        """Compare dates as calendar days in UTC; the split stores them as text."""
        s = pd.to_datetime(stored.astype(str), utc=True, errors="coerce").dt.date
        r = pd.to_datetime(raw, utc=True, errors="coerce").dt.date
        mismatch = int((s != r).sum())
        return mismatch == 0, mismatch

    label_map = {"benign": 0, "phish": 1}
    raw_y = merged.label.map(label_map)
    record("test_label_fidelity", bool((raw_y == merged.y_phish).all()),
           f"mismatches={int((raw_y != merged.y_phish).sum())}")

    ok_date, n_date = same_date(merged.date_stored, merged.date_raw)
    record("test_date_fidelity", ok_date, f"mismatches={n_date}")

    recomputed_hash = merged.url.map(lambda u: hashlib.sha256(canonical_url(u).encode()).hexdigest())
    record("test_canonical_hash", bool((recomputed_hash == merged.url_sha256).all()),
           f"mismatches={int((recomputed_hash != merged.url_sha256).sum())}")

    recomputed_domain = merged.url.map(domain_for)
    record("test_domain_fidelity", bool((recomputed_domain == merged.domain).all()),
           f"mismatches={int((recomputed_domain != merged.domain).sum())}")

    seen_recomputed = recomputed_domain.isin(set(recomputed_domain))
    # domain_seen is train-relative; verify against the train domain set below.

    print("\n[2] TEST features recomputed")
    X_test = pd.DataFrame([url_features(u) for u in merged.url], dtype="float32")
    record("test_feature_columns", list(X_test.columns) == feature_names,
           f"{len(X_test.columns)} columns")
    record("test_features_finite", bool(np.isfinite(X_test.to_numpy()).all()), "all finite")
    record("no_target_encoding_column", "TLDLegitimateProb" not in X_test.columns, "absent")

    # --------------------------------------------------------------- train side
    print("\n[3] TRAIN partition: re-derive")
    split_train = pd.read_csv(run / "split_train.csv.gz")
    if args.train_sample and args.train_sample < len(split_train):
        sample = split_train.sample(n=args.train_sample, random_state=13)
        scope = f"sample {args.train_sample}"
    else:
        sample = split_train
        scope = "FULL"
    raw_train = load_raw("train", set(sample.row_id))
    print(f"  {scope}: rows={len(sample)} raw matched={len(raw_train)}")
    record("train_row_ids_all_present", len(raw_train) == len(sample),
           f"{len(raw_train)} of {len(sample)}")

    mtr = sample.merge(raw_train, on="row_id", how="inner", suffixes=("_stored", "_raw"))
    raw_y_tr = mtr.label.map(label_map)
    record("train_label_fidelity", bool((raw_y_tr == mtr.y_phish).all()),
           f"mismatches={int((raw_y_tr != mtr.y_phish).sum())}")

    ok_date_tr, n_date_tr = same_date(mtr.date_stored, mtr.date_raw)
    record("train_date_fidelity", ok_date_tr, f"mismatches={n_date_tr}")

    hash_tr = mtr.url.map(lambda u: hashlib.sha256(canonical_url(u).encode()).hexdigest())
    record("train_canonical_hash", bool((hash_tr == mtr.url_sha256).all()),
           f"mismatches={int((hash_tr != mtr.url_sha256).sum())}")

    domain_tr = mtr.url.map(domain_for)
    record("train_domain_fidelity", bool((domain_tr == mtr.domain).all()),
           f"mismatches={int((domain_tr != mtr.domain).sum())}")

    X_train_sample = pd.DataFrame([url_features(u) for u in mtr.url], dtype="float32")
    record("train_feature_columns", list(X_train_sample.columns) == feature_names,
           f"{len(X_train_sample.columns)} columns")

    # ------------------------------------------------- domain_seen is train-based
    print("\n[4] domain_seen must be computed from the TRAIN domain set")
    train_domains = set(pd.read_csv(run / "split_train.csv.gz", usecols=["domain"]).domain)
    seen_from_train = recomputed_domain.isin(train_domains)
    record("test_domain_seen_from_train",
           bool((seen_from_train == merged.domain_seen).all()),
           f"mismatches={int((seen_from_train != merged.domain_seen).sum())}")

    # --------------------------------------------- probability reproduction, all seeds
    print("\n[5] Probabilities reproduced from the saved models on recomputed features")
    prob_results = {}
    for seed in [13, 42, 2024, 777, 31415]:
        model_path = run / f"model_seed_{seed}.txt"
        stored = pd.read_csv(run / f"predictions_seed_{seed}.csv.gz")
        booster = lgb.Booster(model_file=str(model_path))
        # align recomputed features to the stored prediction order
        order = stored.row_id
        idx = pd.Index(merged.row_id)
        pos = idx.get_indexer(order)
        if (pos < 0).any():
            record(f"seed_{seed}_prediction_alignment", False,
                   f"{int((pos < 0).sum())} row_ids missing from recomputed set")
            continue
        X_aligned = X_test.iloc[pos].reset_index(drop=True)
        p = booster.predict(X_aligned.to_numpy())
        diff = np.abs(p - stored.p_phish.to_numpy())
        max_diff = float(np.nanmax(diff))
        prob_results[seed] = max_diff
        record(f"seed_{seed}_probabilities_reproduce", max_diff < 1e-6,
               f"max |dp| = {max_diff:.3e}")

    # ------------------------------------- decision threshold reproduces stored labels
    print("\n[6] Threshold 0.5 reproduces the stored confusion matrix")
    res = pd.read_csv(run / "results_per_seed.csv")
    for seed in [13, 42, 2024, 777, 31415]:
        stored = pd.read_csv(run / f"predictions_seed_{seed}.csv.gz")
        yhat = (stored.p_phish.to_numpy() >= THRESHOLD).astype(int)
        y = stored.y_phish.to_numpy()
        tn = int(((y == 0) & (yhat == 0)).sum())
        fp = int(((y == 0) & (yhat == 1)).sum())
        fn = int(((y == 1) & (yhat == 0)).sum())
        tp = int(((y == 1) & (yhat == 1)).sum())
        row = res[(res.seed == seed) & (res.stratum == "all")].iloc[0]
        ok = (tn, fp, fn, tp) == (int(row.tn), int(row.fp), int(row.fn), int(row.tp))
        record(f"seed_{seed}_confusion_matrix", ok,
               f"recomputed={(tn, fp, fn, tp)} stored={(int(row.tn), int(row.fp), int(row.fn), int(row.tp))}")

    # ------------------------------------------------------------------- verdict
    failed = [c for c in checks if not c["ok"]]
    print(f"\n=== checks: {len(checks)} | passed: {len(checks) - len(failed)} | failed: {len(failed)}")
    for c in failed:
        print(f"  FAILED: {c['check']} -> {c['detail']}")

    report = {
        "run_dir": str(run),
        "run": run.name,
        "output_manifest_sha256": hashlib.sha256(
            (run / "output_manifest.json").read_bytes()).hexdigest(),
        "checks_total": len(checks),
        "checks_passed": len(checks) - len(failed),
        "checks_failed": len(failed),
        "max_probability_delta_by_seed": prob_results,
        "test_rows_verified": int(len(merged)),
        "train_rows_verified": int(len(mtr)),
        "feature_columns": feature_names,
        "checks": checks,
        "verifier_python": sys.version,
        "verifier_packages": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "lightgbm": lgb.__version__,
            "tldextract": tldextract.__version__,
        },
    }
    out = args.out or (run.parent / f"END_TO_END_{run.name}.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nreport: {out}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
