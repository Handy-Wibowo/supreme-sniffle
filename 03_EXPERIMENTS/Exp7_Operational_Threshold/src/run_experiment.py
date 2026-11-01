"""Experiment 7 runner: leakage-safe operational threshold study.

Order of operations (the leakage-safety argument in one list):

 1. load url/label/date from the PhreshPhish shards, hash every shard
 2. apply Experiment 4's cleaning protocol unchanged; split the training period
    into fit (< VAL_START) and validation (>= VAL_START)
 3. extract the 18 URL features from the three partitions
 4. fit one LightGBM per seed on the fit block only
 5. score validation and test; write both prediction files
 6. select thresholds on validation only; write ``thresholds_frozen.csv``
 7. evaluate the frozen thresholds on test exactly once; write the report CSVs

Step 6 never reads a test score, and step 7 never changes a threshold.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from . import config as C
from .data import file_sha256, load_partition, prepare
from .features import FEATURE_ORDER, domain_for, feature_frame
from .provenance import psl_snapshot
from .thresholds import binary_metrics, freeze_thresholds, ppv_projection

PACKAGES = ["numpy", "pandas", "pyarrow", "scikit-learn", "lightgbm", "tldextract"]


def _versions() -> dict:
    out = {}
    for name in PACKAGES:
        try:
            out[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            out[name] = "unknown"
    return out


def rules() -> list:
    """(rule name, kind, parameter) in the order they are reported."""
    out = [(C.DEFAULT_RULE, "default", C.DEFAULT_THRESHOLD)]
    out += [(name, "fpr", target) for name, target in C.FPR_TARGETS]
    out.append((C.F1_RULE, "f1", None))
    return out


def run(out_root=None, seeds=None) -> str:
    import lightgbm as lgb

    seeds = list(seeds or C.SEEDS)
    out_root = C.OUTPUT_ROOT if out_root is None else out_root
    out_root.mkdir(parents=True, exist_ok=True)
    out = out_root / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out.mkdir(parents=True, exist_ok=False)
    wall0 = time.perf_counter()
    print("Output:", out, flush=True)

    design = dict(
        experiment="7 - operational threshold evaluation",
        protocol="temporal_split_fit_validation_test",
        training_corpus="PhreshPhish",
        evaluation_corpus="PhreshPhish",
        label_mapping=C.LABEL_MAP,
        split=dict(
            fit_start=str(None), fit_end=str(C.VAL_START),
            validation_start=str(C.VAL_START), validation_end=str(C.CUTOFF),
            test_start=str(C.CUTOFF),
        ),
        cutoff=str(C.CUTOFF),
        validation_start=str(C.VAL_START),
        seeds=seeds,
        primary_seed=C.PRIMARY_SEED,
        default_threshold=C.DEFAULT_THRESHOLD,
        threshold_rules=[dict(rule=n, kind=k, parameter=v) for n, k, v in rules()],
        fpr_targets=dict(C.FPR_TARGETS),
        ppv_projection_prevalences=C.PPV_PREVALENCES,
        model_params=C.MODEL_PARAMS,
        tuning="none; model parameters and seeds inherited from Experiment 4",
        test_usage=("test scores are produced once, after the model is fit on the fit "
                    "block and the thresholds are frozen on validation"),
        unparseable_url_policy=C.UNPARSEABLE_POLICY,
        unparseable_url_max_share=C.UNPARSEABLE_MAX_SHARE,
        environment=_versions(),
        psl_snapshot=psl_snapshot(),
        code_sha256={name: file_sha256(C.EXPERIMENT_DIR / "src" / name) for name in (
            "config.py", "data.py", "features.py", "thresholds.py",
            "run_experiment.py", "provenance.py")},
        python=sys.version, platform=platform.platform(), logical_cpus=os.cpu_count(),
    )
    (out / "design.json").write_text(json.dumps(design, indent=2), encoding="utf-8")

    # ---------------------------------------------------------------- load
    t0 = time.perf_counter()
    tr_raw, tr_manifest = load_partition(C.DATA_DIR, "train")
    te_raw, te_manifest = load_partition(C.DATA_DIR, "test")
    load_s = time.perf_counter() - t0
    (out / "input_manifest.json").write_text(
        json.dumps(tr_manifest + te_manifest, indent=2), encoding="utf-8")
    print(f"loaded train={len(tr_raw)} test={len(te_raw)} in {load_s:.1f}s", flush=True)

    t0 = time.perf_counter()
    fit, val, test, ledger, excluded, unparseable = prepare(tr_raw, te_raw)
    clean_s = time.perf_counter() - t0
    ledger.to_csv(out / "row_ledger.csv", index=False)
    excluded.to_csv(out / "excluded_rows.csv", index=False)
    if len(unparseable):
        unparseable.to_csv(out / "unparseable_urls.csv", index=False)
    design["split"]["fit_start"] = str(fit.date.min())
    design["rows"] = dict(fit=len(fit), validation=len(val), test=len(test))
    (out / "design.json").write_text(json.dumps(design, indent=2), encoding="utf-8")
    print(ledger.to_string(index=False), flush=True)

    # ------------------------------------------------------------- features
    t0 = time.perf_counter()
    Xfit, Xval, Xtest = (feature_frame(df.url) for df in (fit, val, test))
    feature_s = time.perf_counter() - t0
    for name, X in (("fit", Xfit), ("validation", Xval), ("test", Xtest)):
        if not np.isfinite(X.to_numpy()).all():
            raise ValueError(f"{name}: non-finite feature value.")
    assert list(Xfit.columns) == FEATURE_ORDER
    (out / "feature_schema.json").write_text(json.dumps(dict(
        names=FEATURE_ORDER, count=len(FEATURE_ORDER),
        source="deterministic URL-only; no target encoding",
        semantics="Experiment 4 extractor, ported verbatim; Experiment 5 configuration A2",
        fit_extract_s=None, validation_extract_s=None, test_extract_s=None,
    ), indent=2), encoding="utf-8")
    print(f"features {Xfit.shape} in {feature_s:.1f}s", flush=True)

    for part, df in (("fit", fit), ("validation", val), ("test", test)):
        export = df[["row_id", "date", "y_phish"]].copy()
        export["domain"] = df.url.map(domain_for)
        export["url_sha256"] = df.url_key.map(
            lambda u: hashlib.sha256(u.encode()).hexdigest())
        export.to_csv(out / f"split_{part}.csv.gz", index=False)

    # -------------------------------------------------------------- fitting
    print("fitting per seed on the fit block only ...", flush=True)
    per_seed = {}
    for seed in seeds:
        model = lgb.LGBMClassifier(**C.MODEL_PARAMS, random_state=seed)
        t0 = time.perf_counter()
        model.fit(Xfit, fit.y_phish)
        fit_s = time.perf_counter() - t0
        pos = int(np.flatnonzero(model.classes_ == 1)[0])
        t0 = time.perf_counter()
        p_val = model.predict_proba(Xval)[:, pos]
        val_s = time.perf_counter() - t0
        t0 = time.perf_counter()
        p_test = model.predict_proba(Xtest)[:, pos]
        test_s = time.perf_counter() - t0
        model.booster_.save_model(str(out / f"model_seed_{seed}.txt"))
        (out / f"model_params_seed_{seed}.json").write_text(
            json.dumps(model.get_params(), indent=2, default=str), encoding="utf-8")

        for part, df, p in (("validation", val, p_val), ("test", test, p_test)):
            pf = df[["row_id", "date", "y_phish"]].copy()
            pf["domain"] = df.url.map(domain_for)
            pf["p_phish"] = p
            pf.to_csv(out / f"predictions_{part}_seed_{seed}.csv.gz", index=False)

        per_seed[seed] = dict(val_y=val.y_phish.to_numpy(), val_p=p_val,
                              test_y=test.y_phish.to_numpy(), test_p=p_test,
                              fit_s=fit_s, val_predict_s=val_s, test_predict_s=test_s,
                              n_trees=int(model.booster_.num_trees()))
        print(f"  seed {seed}: fit {fit_s:.1f}s, "
              f"predict val {val_s:.2f}s test {test_s:.2f}s", flush=True)

    # --------------------------------------------------- freeze on validation
    frozen_frames = []
    for seed in seeds:
        s = per_seed[seed]
        f = freeze_thresholds(s["val_y"], s["val_p"], rules(), C.DEFAULT_THRESHOLD)
        f.insert(0, "seed", seed)
        frozen_frames.append(f)
    frozen = pd.concat(frozen_frames, ignore_index=True)
    frozen.to_csv(out / "thresholds_frozen.csv", index=False)
    print("\nfrozen thresholds (validation only):", flush=True)
    print(frozen[["seed", "rule", "threshold", "val_fpr", "val_recall",
                  "val_precision", "val_f1"]].to_string(index=False), flush=True)

    # ------------------------------------------------------ evaluate on test
    rows, proj_rows = [], []
    for seed in seeds:
        s = per_seed[seed]
        for rule in frozen.loc[frozen.seed == seed, "rule"]:
            thr = float(frozen.loc[(frozen.seed == seed) & (frozen.rule == rule),
                                   "threshold"].iloc[0])
            m = binary_metrics(s["test_y"], s["test_p"], thr)
            rows.append(dict(seed=seed, rule=rule, threshold=thr, **m))
            for prev in C.PPV_PREVALENCES:
                proj_rows.append(dict(
                    seed=seed, rule=rule, threshold=thr, assumed_prevalence=prev,
                    test_recall=m["recall_phish"], test_fpr=m["fpr_benign"],
                    projected_ppv=ppv_projection(m["recall_phish"], m["fpr_benign"], prev),
                    projected_false_alarms_per_10k_benign=(1 - prev) * m["fpr_benign"] * 10_000,
                    note=("projection assumes the measured TPR/FPR transfer to this "
                          "prevalence; not measured on data at that prevalence")))
    test_metrics = pd.DataFrame(rows)
    test_metrics.to_csv(out / "test_metrics.csv", index=False)
    pd.DataFrame(proj_rows).to_csv(out / "ppv_projections.csv", index=False)

    metric_cols = ["f1_phish", "precision_phish", "recall_phish", "fpr_benign",
                   "miss_rate", "false_alarms_per_10k_benign", "mcc"]
    across = (test_metrics.groupby("rule")[metric_cols]
              .agg(["mean", "std", "min", "max"]).round(6))
    across.to_csv(out / "test_metrics_across_seeds.csv")
    primary = test_metrics[test_metrics.seed == C.PRIMARY_SEED].copy()
    primary.to_csv(out / "test_metrics_primary_seed.csv", index=False)

    runtime = dict(
        load_s=round(load_s, 3), clean_s=round(clean_s, 3),
        feature_extract_s=round(feature_s, 3),
        fits={str(k): dict(fit_s=round(v["fit_s"], 3),
                           val_predict_s=round(v["val_predict_s"], 3),
                           test_predict_s=round(v["test_predict_s"], 3),
                           n_trees=v["n_trees"]) for k, v in per_seed.items()},
        wall_s=None, executor="local runner, sequential fits, notebook-driven",
    )
    design["runtime"] = runtime
    design["rows"] = dict(fit=len(fit), validation=len(val), test=len(test))
    (out / "design.json").write_text(json.dumps(design, indent=2), encoding="utf-8")

    fs = json.loads((out / "feature_schema.json").read_text())
    fs["fit_extract_s"] = round(feature_s, 3)
    (out / "feature_schema.json").write_text(json.dumps(fs, indent=2))

    print("\ntest metrics, primary seed:", flush=True)
    print(primary[["rule", "threshold", "f1_phish", "precision_phish", "recall_phish",
                   "fpr_benign", "miss_rate", "mcc",
                   "false_alarms_per_10k_benign"]].to_string(index=False), flush=True)
    print("\nacross seeds (mean):", flush=True)
    print(across.xs("mean", axis=1, level=1).to_string(), flush=True)

    runtime["wall_s"] = round(time.perf_counter() - wall0, 3)
    design["runtime"] = runtime
    (out / "design.json").write_text(json.dumps(design, indent=2), encoding="utf-8")

    files = [dict(file=p.name, sha256=file_sha256(p), bytes=p.stat().st_size)
             for p in sorted(out.iterdir())
             if p.is_file() and p.name != "output_manifest.json"]
    (out / "output_manifest.json").write_text(json.dumps(files, indent=2), encoding="utf-8")
    print(f"\nDone in {runtime['wall_s']}s.", flush=True)
    return str(out)
