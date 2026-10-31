"""Reproducible preflight evidence for reusing the frozen PhreshPhish temporal run.

    python -m src.preflight_check            # full check (~3 min)
    python -m src.preflight_check --urls 500 # feature parity only

Two claims are tested against `Experiment/4 - PhreshPhish Temporal Audit`:

1. feature parity  - `src.features.url_features` reproduces the legacy
   `run_temporal.url_features` values. The legacy module is a script whose
   top-level code trains, so only its extractor definitions are loaded (AST
   subset, no side effects).
2. probability parity - our A2 + LightGBM seed-13 probabilities equal the
   legacy `predictions_seed_13.csv.gz` for the same test rows.

Nothing here is part of the 70-fit matrix; the run is registered as a preflight
check so it can never be mistaken for a result.
"""

from __future__ import annotations

import argparse
import ast
import functools
import ipaddress
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import data, evaluate
from .provenance import (EXPERIMENT_DIR, WORKSPACE, Registry, new_run_dir,
                         utc_now, write_json)
from .run_experiment import extract_features, fit_and_predict, prepare_phresh

LEGACY_DIR = WORKSPACE / "Experiment" / "4 - PhreshPhish Temporal Audit"
LEGACY_SCRIPT = LEGACY_DIR / "run_temporal.py"
LEGACY_OUT = LEGACY_DIR / "outputs" / "20261022T170935017991Z"
LEGACY_FUNCS = {"parse_url", "canonical_url", "host_parts", "url_features", "domain_for"}
LEGACY_CONSTS = {"EXT", "SPEC"}


def load_legacy_extractor():
    """Return the legacy `url_features` without executing the legacy runner."""
    import tldextract
    from urllib.parse import urlsplit, urlunsplit

    tree = ast.parse(LEGACY_SCRIPT.read_text(encoding="utf-8"))
    body = [n for n in tree.body
            if (isinstance(n, ast.FunctionDef) and n.name in LEGACY_FUNCS)
            or (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in LEGACY_CONSTS)]
    found = {n.name for n in body if isinstance(n, ast.FunctionDef)}
    if found != LEGACY_FUNCS:
        raise RuntimeError(f"legacy extractor functions changed: missing {sorted(LEGACY_FUNCS - found)}")
    ns = {"re": re, "ipaddress": ipaddress, "lru_cache": functools.lru_cache,
          "tldextract": tldextract, "urlsplit": urlsplit, "urlunsplit": urlunsplit}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(LEGACY_SCRIPT), "exec"), ns)
    return ns["url_features"], ns["domain_for"]


def feature_parity(urls: pd.Series) -> dict:
    from .features import url_features

    legacy, _ = load_legacy_extractor()
    ours = pd.DataFrame([url_features(u) for u in urls], columns=data.A2)
    theirs = pd.DataFrame([legacy(u) for u in urls], columns=data.A2)
    diff = ours != theirs
    per_feature = {c: int(diff[c].sum()) for c in data.A2 if diff[c].any()}
    if per_feature:
        raise AssertionError(f"feature parity broken: {per_feature}")
    return {"urls": len(urls), "features": len(data.A2), "cells": int(ours.size),
            "differing_cells": int(diff.to_numpy().sum())}


def probability_parity(threads: int, out_dir: Path) -> dict:
    train_raw = data.load_phresh("train")
    test_raw = data.load_phresh("test")
    train, test, ledger, _ = prepare_phresh(train_raw, test_raw, out_dir)
    ledger.to_csv(out_dir / "row_ledger.csv", index=False)

    Xtr, Xte = extract_features(train.url), extract_features(test.url)
    seed = data.PRIMARY_SEED_PHRESH
    prob, fit_s, _ = fit_and_predict("lightgbm", Xtr, train.y_phish.to_numpy(), Xte, seed, threads)

    legacy = pd.read_csv(LEGACY_OUT / f"predictions_seed_{seed}.csv.gz",
                         usecols=["row_id", "y_phish", "p_phish"])
    ours = pd.DataFrame({"row_id": test.row_id.to_numpy(),
                         "y_phish": test.y_phish.to_numpy(), "p_phish": prob})
    merged = ours.merge(legacy, on="row_id", how="outer", suffixes=("_ours", "_legacy"),
                        indicator=True)
    unmatched = int((merged._merge != "both").sum())
    if unmatched:
        raise AssertionError(f"{unmatched} test row_ids do not match the legacy predictions")
    label_mismatch = int((merged.y_phish_ours != merged.y_phish_legacy).sum())
    if label_mismatch:
        raise AssertionError(f"{label_mismatch} labels differ from the legacy run")
    max_diff = float((merged.p_phish_ours - merged.p_phish_legacy).abs().max())

    def score(frame):
        return evaluate.metrics(frame.y_phish, frame.p_phish)

    a, b = score(merged[["y_phish_ours", "p_phish_ours"]].rename(
        columns={"y_phish_ours": "y_phish", "p_phish_ours": "p_phish"})), score(merged[["y_phish_legacy", "p_phish_legacy"]].rename(
        columns={"y_phish_legacy": "y_phish", "p_phish_legacy": "p_phish"}))
    counts_equal = all(a[k] == b[k] for k in ("tn", "fp", "fn", "tp"))
    if not counts_equal:
        raise AssertionError(f"confusion counts differ: {a} vs {b}")
    return {"seed": seed, "rows": len(merged), "max_abs_prob_diff": max_diff,
            "f1_ours": a["f1_phish"], "f1_legacy": b["f1_phish"],
            "confusion": {k: a[k] for k in ("tn", "fp", "fn", "tp")},
            "fit_s": round(fit_s, 2), "threads": threads}


def phiushiil_timing(threads: int) -> dict:
    """One full-size fit per configuration, timed. Not a result: sizes the 60-fit run."""
    df = data.load_phiusiil()
    y = df.y_phish
    tr, te = data.load_split("sitedisjoint", data.PRIMARY_SEED_PHIUSIIL)
    rows = []
    for config in ("A0", "A1", "A2"):
        X = df[data.CONFIGS[config]].astype("float64")
        if not np.isfinite(X.to_numpy()).all():
            raise ValueError(f"{config} has non-finite values; probe would not match the real run")
        prob, fit_s, predict_s = fit_and_predict(
            "lightgbm", X.loc[tr.url_id], y.loc[tr.url_id].to_numpy(),
            X.loc[te.url_id], data.PRIMARY_SEED_PHIUSIIL, threads)
        m = evaluate.metrics(y.loc[te.url_id].to_numpy(), prob)
        rows.append({"config": config, "n_features": len(data.CONFIGS[config]),
                     "protocol": "sitedisjoint", "model": "lightgbm",
                     "seed": data.PRIMARY_SEED_PHIUSIIL, "threads": threads,
                     "n_train": len(tr), "n_test": len(te),
                     "fit_s": round(fit_s, 2), "predict_s": round(predict_s, 2),
                     "f1_phish": m["f1_phish"], "mcc": m["mcc"],
                     "fpr_benign": m["fpr_benign"]})
    return {"probe": "one lightgbm fit per configuration on full data",
            "warning": "diagnostic only; not part of the 60-fit matrix",
            "configs": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--urls", type=int, default=5000, help="rows used for feature parity")
    ap.add_argument("--threads", type=int, default=data.DEFAULT_THREADS)
    ap.add_argument("--feature-only", action="store_true")
    ap.add_argument("--time-phiushiil", action="store_true",
                    help="also time one full-size PhiUSIIL fit (never part of the matrix)")
    args = ap.parse_args(argv)

    rid, out_dir = new_run_dir("parity_", root=EXPERIMENT_DIR / "outputs" / "preflight_phresh")
    registry = Registry()
    started = utc_now()
    registry.upsert({"run_id": rid, "experiment": "preflight_check", "dataset": "phreshphish",
                     "configs": "A2", "protocols": "temporal", "models": "lightgbm",
                     "seeds": str(data.PRIMARY_SEED_PHRESH), "threads": args.threads,
                     "started_utc": started, "status": "running",
                     "output_dir": str(out_dir.relative_to(EXPERIMENT_DIR)),
                     "notes": "reuse evidence for Experiment 4; never cite as a result"})

    test_raw = data.load_phresh("test", limit=5)
    result = {"run_id": rid, "legacy_run": str(LEGACY_OUT), "final": False,
              "feature_parity": feature_parity(test_raw.url.head(args.urls))}
    if not args.feature_only:
        result["probability_parity"] = probability_parity(args.threads, out_dir)
    write_json(out_dir / "parity.json", result)
    registry.upsert({"run_id": rid, "status": "completed", "finished_utc": utc_now(),
                     "n_fits": 0 if args.feature_only else 1})
    print(pd.Series(result).to_string(), flush=True)

    if args.time_phiushiil:
        rid2, out_dir2 = new_run_dir("timing_",
                                     root=EXPERIMENT_DIR / "outputs" / "preflight_phiusiil")
        registry.upsert({"run_id": rid2, "experiment": "preflight_timing",
                         "dataset": "phiusiil", "configs": "A0",
                         "protocols": "sitedisjoint", "models": "lightgbm",
                         "seeds": str(data.PRIMARY_SEED_PHIUSIIL), "threads": args.threads,
                         "started_utc": utc_now(), "status": "running",
                         "output_dir": str(out_dir2.relative_to(EXPERIMENT_DIR)),
                         "notes": "single timing fit; not part of the 60-fit matrix"})
        timing = phiushiil_timing(args.threads)
        write_json(out_dir2 / "timing.json", timing)
        registry.upsert({"run_id": rid2, "status": "completed", "finished_utc": utc_now(),
                         "n_fits": 1})
        print(pd.Series(timing).to_string(), flush=True)

    print(f"PREFLIGHT PARITY PASS -> {out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
