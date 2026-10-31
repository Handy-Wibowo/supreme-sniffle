"""Command line entry points for the PhiUSIIL ablation and PhreshPhish temporal runs.

Usage (from the experiment directory, with the verified interpreter):

    python -m src.run_experiment plan --dataset phiusiil
    python -m src.run_experiment run  --dataset phiusiil --threads 4
    python -m src.run_experiment run  --dataset phreshphish --threads 4
    python -m src.run_experiment summarize
    python -m src.run_experiment smoke --threads 2

Nothing is trained at import time; `main()` is only reached through the CLI.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import audit, data, evaluate, summarize as summary_lib
from .features import canonical_url, domain_for, psl_snapshot, url_features
from .provenance import (EXPERIMENT_DIR, OUTPUT_ROOT, Registry, code_manifest,
                         environment_snapshot, new_run_dir, sha256_file, utc_now,
                         write_json)

EXCLUDED_COLUMNS = ["row_id", "reason"]
UNPARSEABLE_POLICY = "exclude"
UNPARSEABLE_MAX_SHARE = 1e-4


class _Tee:
    """Mirror stdout into execution.log so the run keeps its own log."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.stream = sys.stdout

    def write(self, text):
        self.stream.write(text)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(text)
        return len(text)

    def flush(self):
        self.stream.flush()

def _canonical_keys(frame: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """Canonical URL keys plus a log of rows whose URL the parser rejects."""
    keys, bad = [], []
    for row_id, url in zip(frame.row_id.to_numpy(), frame.url.to_numpy()):
        try:
            keys.append(canonical_url(url))
        except (ValueError, UnicodeError, AttributeError) as error:
            keys.append(None)
            bad.append({"row_id": row_id, "url": url, "error": f"{type(error).__name__}: {error}"})
    return (pd.Series(keys, index=frame.index, name="url_key"),
            pd.DataFrame(bad, columns=["row_id", "url", "error"]))


# ------------------------------------------------------------------ helpers
def extract_features(urls: pd.Series) -> pd.DataFrame:
    """A2 features for every URL, in the shared order. Raises on an unparseable URL."""
    rows = [url_features(u) for u in urls]
    return pd.DataFrame(rows, columns=data.A2, dtype="float64")


def build_model(name: str, seed: int, threads: int):
    params = dict(data.MODEL_PARAMS[name])
    if name == "lightgbm":
        import lightgbm as lgb

        return lgb.LGBMClassifier(**params, random_state=seed, n_jobs=threads)
    if name == "xgboost":
        import xgboost as xgb

        return xgb.XGBClassifier(**params, random_state=seed, n_jobs=threads)
    raise ValueError(f"unknown model {name}")


def fit_and_predict(name: str, Xtr, ytr, Xte, seed: int, threads: int):
    """Fit one model and return (probability of phishing, fit seconds, predict seconds)."""
    model = build_model(name, seed, threads)
    t0 = time.perf_counter()
    model.fit(Xtr, ytr)
    fit_s = time.perf_counter() - t0
    classes = np.asarray(model.classes_)
    if not np.array_equal(classes, np.array([0, 1])):
        raise ValueError(f"{name}: expected both classes [0, 1], got {classes.tolist()}")
    phish_column = int(np.flatnonzero(classes == 1)[0])  # never assume column 1
    t0 = time.perf_counter()
    prob = model.predict_proba(Xte)[:, phish_column]
    predict_s = time.perf_counter() - t0
    return prob, fit_s, predict_s


def append_metrics(path: Path, row: dict) -> None:
    df = pd.DataFrame([row])
    header = not path.exists()
    df.to_csv(path, mode="a", header=header, index=False)


def prediction_frame(meta: dict, row_id, domain, y_phish, prob, date=None) -> pd.DataFrame:
    out = pd.DataFrame({
        "row_id": row_id,
        "domain": domain,
        "y_phish": np.asarray(y_phish, dtype=int),
        "p_phish": np.asarray(prob, dtype=float),
    })
    out["pred"] = (out.p_phish >= data.THRESHOLD).astype(int)
    for key in ("dataset", "protocol", "config", "model", "seed"):
        out[key] = meta[key]
    columns = ["dataset", "protocol", "config", "model", "seed",
               "row_id", "domain", "y_phish", "p_phish", "pred"]
    if date is not None:
        out["date"] = pd.to_datetime(pd.Series(date), utc=True).dt.strftime("%Y-%m-%d")
        columns.append("date")
    return out[columns]


def metric_row(meta: dict, y, prob, fit_s, predict_s, threads) -> dict:
    m = evaluate.metrics(y, prob, data.THRESHOLD)
    return {
        "run_id": meta["run_id"],
        "dataset": meta["dataset"],
        "protocol": meta["protocol"],
        "config": meta["config"],
        "model": meta["model"],
        "seed": meta["seed"],
        "threads": threads,
        "fit_s": round(fit_s, 4),
        "predict_s": round(predict_s, 4),
        "status": "completed",
        **{k: m[k] for k in ("n", "n_benign", "n_phish", "tn", "fp", "fn", "tp")},
        **{k: m[k] for k in ("prevalence_phish", "precision_phish", "recall_phish",
                             "f1_phish", "mcc", "accuracy", "fpr_benign", "miss_phish",
                             "roc_auc", "average_precision")},
        "undefined": ";".join(m["undefined"]),
    }


# ------------------------------------------------------------------ PhiUSIIL
def planned_phiusiil_fits() -> list[dict]:
    return [
        {"protocol": protocol, "config": config, "model": model, "seed": seed}
        for protocol in data.PROTOCOLS_PHIUSIIL
        for config in data.CONFIGS
        for model in data.MODELS
        for seed in data.SEEDS
    ]


def _stratified_ids(ids, y_all, n: int, seed: int):
    """Deterministic per-class subsample of a fold, preserving its class balance.

    Smoke runs are non-final, but a class-skewed prefix would make the smoke
    numbers unrepresentative of the cohort they stand in for.
    """
    y = y_all.loc[ids].to_numpy()
    rng = np.random.default_rng(seed)
    picked = []
    for cls in (0, 1):
        pool = ids[y == cls]
        take = min(int(round(n * len(pool) / len(ids))), len(pool))
        if take:
            picked.append(rng.choice(pool, size=take, replace=False))
    return np.sort(np.concatenate(picked))

def run_phiusiil(out_dir: Path, rid: str, threads: int, log_path: Path,
                 max_rows: int | None = None) -> pd.DataFrame:
    """60 fits: 3 configurations x 2 protocols x 2 models x 5 seeds."""
    df = data.load_phiusiil()
    domain = df.set_index("url_id")["registrable_domain"]
    y_all = df.set_index("url_id")["y_phish"]
    url_all = df.set_index("url_id")["URL"]

    a2 = extract_features(df.URL)
    a2.index = df.url_id.to_numpy()
    a2_path = out_dir / "features_a2.parquet"
    a2.to_parquet(a2_path, index=True)
    print(f"A2 features {a2.shape} -> {a2_path.name}", flush=True)
    agreement = audit.a2_vs_source_agreement(df, a2)
    agreement.to_csv(out_dir / "a2_vs_source_agreement.csv", index=False)
    print(agreement.to_string(index=False), flush=True)
    audit.split_audit(df, audit.domain_keys(df)).to_csv(out_dir / "split_audit.csv", index=False)
    keys = audit.domain_keys(df)
    audit.domain_concentration(df, keys).to_csv(out_dir / "domain_concentration.csv", index=False)

    features = {
        "A0": df.set_index("url_id")[data.A0].astype("float64"),
        "A1": df.set_index("url_id")[data.A1].astype("float64"),
        "A2": a2,
    }
    for config, frame in features.items():
        if frame.isna().any().any():
            raise ValueError(f"{config}: null feature values; decide explicitly before fitting")

    metrics_path = out_dir / "metrics_per_run.csv"
    for fit in planned_phiusiil_fits():
        tr, te = data.load_split(fit["protocol"], fit["seed"])
        tr_ids, te_ids = tr.url_id.to_numpy(), te.url_id.to_numpy()
        if max_rows:
            tr_ids = _stratified_ids(tr_ids, y_all, max_rows, fit["seed"])
            te_ids = _stratified_ids(te_ids, y_all, max_rows // 2 or 1, fit["seed"] + 1)
        meta = {"run_id": rid, "dataset": "phiusiil", **fit}
        Xtr = features[fit["config"]].loc[tr_ids]
        Xte = features[fit["config"]].loc[te_ids]
        ytr = y_all.loc[tr_ids].to_numpy()
        yte = y_all.loc[te_ids].to_numpy()
        prob, fit_s, predict_s = fit_and_predict(fit["model"], Xtr, ytr, Xte,
                                                 fit["seed"], threads)
        pred = prediction_frame(meta, te_ids, domain.loc[te_ids].to_numpy(), yte, prob)
        pred.to_csv(out_dir / f"predictions_phiusiil_{fit['protocol']}_{fit['config']}_"
                              f"{fit['model']}_seed{fit['seed']}.csv.gz", index=False)
        append_metrics(metrics_path, metric_row(meta, yte, prob, fit_s, predict_s, threads))
        print(f"  {fit['protocol']:<13} {fit['config']} {fit['model']:<9} seed={fit['seed']:<6}"
              f" n_test={len(te_ids):>6} fit_s={fit_s:6.2f}", flush=True)

    return pd.read_csv(metrics_path)


# --------------------------------------------------------------- PhreshPhish
def prepare_phresh(train_raw: pd.DataFrame, test_raw: pd.DataFrame,
                   out_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Cutoff purge, duplicate handling and label mapping; every removal is logged.

    The rules are the ones already frozen in the legacy temporal pipeline and
    restated in protocol section 5: training rows at/after the cutoff are
    dropped, duplicate training URLs keep the earliest row, test rows whose URL
    was seen in training are removed, and no training row is ever changed
    because of a test label.
    """
    ledger, excluded = [], []

    def record(stage, frame):
        ledger.append(dict(stage=stage, rows=len(frame),
                           benign=int((frame.y_phish == 0).sum()),
                           phish=int((frame.y_phish == 1).sum()),
                           min_date=str(frame.date.min()), max_date=str(frame.date.max())))

    train = train_raw.copy()
    test = test_raw.copy()
    unparseable = []
    bad_ids: dict[str, set] = {}
    for name in ("train", "test"):
        frame = train if name == "train" else test
        if not set(frame.label.unique()).issubset({"benign", "phish"}):
            raise ValueError(f"{name}: unknown label values {frame.label.unique()}")
        frame["y_phish"] = frame.label.map({"benign": 0, "phish": 1}).astype("int8")
        frame["date"] = pd.to_datetime(frame.date, errors="raise", utc=True)
        keys, bad = _canonical_keys(frame)
        share = len(bad) / max(len(frame), 1)
        if len(bad) and (UNPARSEABLE_POLICY == "raise" or share > UNPARSEABLE_MAX_SHARE):
            raise ValueError(
                f"{name}: {len(bad)} unparseable URLs ({share:.6%}); policy={UNPARSEABLE_POLICY} "
                f"cap={UNPARSEABLE_MAX_SHARE:.6%}; inspect the examples before proceeding")
        if len(bad):
            unparseable.append(bad.assign(partition=name, reason="unparseable_url"))
            excluded.append(pd.DataFrame({"row_id": bad.row_id.to_numpy(), "reason": "unparseable_url"}))
        frame["url_key"] = keys
        bad_ids[name] = set(bad.row_id)
        if name == "train":
            train = frame
        else:
            test = frame
    if unparseable:
        pd.concat(unparseable, ignore_index=True).to_csv(out_dir / "unparseable_urls.csv", index=False)
    record("train_raw", train)
    record("test_raw", test)

    if (test.date < data.CUTOFF_UTC).any():
        raise ValueError("test partition contains rows before the cutoff; do not move rows silently")

    late = train.date >= data.CUTOFF_UTC
    excluded.append(pd.DataFrame({"row_id": train.loc[late, "row_id"], "reason": "train_at_or_after_cutoff"}))
    train = train.loc[~late].copy()
    record("train_after_cutoff_purge", train)

    # Unparseable rows are removed after the cutoff purge and before dedup, per the
    # approved policy, so the ledger stages reconcile with the historical run.
    for name in ("train", "test"):
        frame = train if name == "train" else test
        frame = frame.loc[~frame.row_id.isin(bad_ids[name])].copy()
        record(f"{name}_after_unparseable_purge", frame)
        if name == "train":
            train = frame
        else:
            test = frame

    conflict = train.groupby("url_key").y_phish.nunique().gt(1)
    if conflict.any():
        raise ValueError(f"{int(conflict.sum())} training URLs carry conflicting labels; adjudicate first")
    train = train.sort_values(["date", "row_id"], kind="stable")
    dup = train.duplicated("url_key", keep="first")
    excluded.append(pd.DataFrame({"row_id": train.loc[dup, "row_id"], "reason": "duplicate_train_url"}))
    train = train.loc[~dup].copy()
    record("train_unique", train)

    # A canonical URL present in both partitions with different labels is reported,
    # not adjudicated: the frozen rule removes it from evaluation because it was
    # seen during training.
    merged = test[["row_id", "url_key", "y_phish"]].merge(
        train[["url_key", "y_phish"]], on="url_key", suffixes=("_test", "_train"))
    cross = merged[merged.y_phish_test != merged.y_phish_train]
    cross.to_csv(out_dir / "cross_partition_label_conflicts.csv", index=False)
    if len(cross):
        print(f"  cross-partition label conflicts (resolved by seen-URL purge): {len(cross)}", flush=True)

    seen = test.url_key.isin(set(train.url_key))
    excluded.append(pd.DataFrame({"row_id": test.loc[seen, "row_id"], "reason": "test_url_seen_in_train"}))
    test = test.loc[~seen].copy()
    record("test_after_seen_url_purge", test)

    conflict = test.groupby("url_key").y_phish.nunique().gt(1)
    if conflict.any():
        raise ValueError(f"{int(conflict.sum())} test URLs carry conflicting labels; adjudicate first")
    test = test.sort_values(["date", "row_id"], kind="stable")
    dup = test.duplicated("url_key", keep="first")
    excluded.append(pd.DataFrame({"row_id": test.loc[dup, "row_id"], "reason": "duplicate_test_url"}))
    test = test.loc[~dup].copy()
    record("test_unique", test)

    for name, frame in (("train", train), ("test", test)):
        if set(frame.y_phish.unique()) != {0, 1}:
            raise ValueError(f"{name}: both classes must remain after filtering")
    if not train.date.max() < test.date.min():
        raise ValueError("time order is not strict after cleaning")

    ledger_df = pd.DataFrame(ledger)
    excluded_df = pd.concat(excluded, ignore_index=True) if excluded else pd.DataFrame(columns=EXCLUDED_COLUMNS)
    ledger_df.to_csv(out_dir / "row_ledger.csv", index=False)
    excluded_df.to_csv(out_dir / "excluded_rows.csv", index=False)
    return (train.reset_index(drop=True), test.reset_index(drop=True),
            ledger_df, excluded_df)


def run_phreshphish(out_dir: Path, rid: str, threads: int, log_path: Path,
                    train_shards: int | None = None, test_shards: int | None = None) -> pd.DataFrame:
    """10 fits: one configuration x 2 models x 5 seeds."""
    train_raw = data.load_phresh("train", limit=train_shards)
    test_raw = data.load_phresh("test", limit=test_shards)
    print(f"loaded PhreshPhish train={len(train_raw)} test={len(test_raw)}", flush=True)

    train, test, ledger, excluded = prepare_phresh(train_raw, test_raw, out_dir)
    del train_raw, test_raw
    print(ledger.to_string(index=False), flush=True)

    Xtr = extract_features(train.url)
    Xte = extract_features(test.url)
    train["domain"] = train.url.map(domain_for)
    test["domain"] = test.url.map(domain_for)
    assert list(Xtr.columns) == list(Xte.columns) == data.A2
    assert np.isfinite(Xtr.to_numpy()).all() and np.isfinite(Xte.to_numpy()).all()

    exposure = (test.assign(domain_seen=test.domain.isin(set(train.domain)))
                .groupby(["y_phish", "domain_seen"]).size().rename("rows").reset_index())
    exposure.to_csv(out_dir / "test_domain_exposure.csv", index=False)

    metrics_path = out_dir / "metrics_per_run.csv"
    for model in data.MODELS:
        for seed in data.SEEDS:
            meta = {"run_id": rid, "dataset": "phreshphish", "protocol": "temporal",
                    "config": "A2", "model": model, "seed": seed}
            prob, fit_s, predict_s = fit_and_predict(model, Xtr, train.y_phish.to_numpy(),
                                                     Xte, seed, threads)
            pred = prediction_frame(meta, test.row_id.to_numpy(), test.domain.to_numpy(),
                                    test.y_phish.to_numpy(), prob, test.date.to_numpy())
            pred.to_csv(out_dir / f"predictions_phreshphish_temporal_A2_{model}_seed{seed}.csv.gz",
                        index=False)
            append_metrics(metrics_path, metric_row(meta, test.y_phish.to_numpy(), prob,
                                                    fit_s, predict_s, threads))
            print(f"  temporal {model:<9} seed={seed:<6} n_test={len(test):>7} fit_s={fit_s:6.2f}",
                  flush=True)

    return pd.read_csv(metrics_path)


# ------------------------------------------------------------------ commands
def cmd_run(args) -> int:
    rid, out_dir = new_run_dir()
    log_path = out_dir / "execution.log"
    started = utc_now()
    diagnostic = bool(args.train_shards or args.test_shards)
    if diagnostic:
        print("DIAGNOSTIC shard subset: excluded from main summaries", flush=True)
    registry = Registry()
    registry.upsert({
        "run_id": rid, "experiment": args.dataset, "dataset": args.dataset,
        "configs": "A0,A1,A2" if args.dataset == "phiusiil" else "A2",
        "protocols": "random,sitedisjoint" if args.dataset == "phiusiil" else "temporal",
        "models": "lightgbm,xgboost", "seeds": ",".join(map(str, data.SEEDS)),
        "threads": args.threads, "started_utc": started, "status": "running",
        "output_dir": str(out_dir.relative_to(EXPERIMENT_DIR)), "log_path": str(log_path.relative_to(EXPERIMENT_DIR)),
    })
    sys.stdout = _Tee(log_path)
    write_json(out_dir / "environment.json", environment_snapshot())
    write_json(out_dir / "feature_groups.json", data.feature_groups())
    data.feature_provenance().to_csv(out_dir / "feature_provenance.csv", index=False)
    write_json(out_dir / "input_manifest.json", audit.input_manifest())
    write_json(out_dir / "design.json", {
        "run_id": rid,
        "command": getattr(args, "command_line", ""),
        "diagnostic": diagnostic,
        "train_shards": args.train_shards,
        "test_shards": args.test_shards,
        "protocol_version": "PROTOKOL_EKSPERIMEN_SINTA2_v1 (25 Oct 2026)",
        "status": "exploratory; test data of PhreshPhish was inspected in earlier probes",
        "dataset": args.dataset,
        "threads": args.threads,
        "threshold": data.THRESHOLD,
        "seeds": data.SEEDS,
        "primary_seed_phiusiil": data.PRIMARY_SEED_PHIUSIIL,
        "primary_seed_phreshphish": data.PRIMARY_SEED_PHRESH,
        "cutoff_utc": str(data.CUTOFF_UTC),
        "model_params": data.MODEL_PARAMS,
        "tuning": "none; no early stopping, no SMOTE, no test-based selection",
        "psl": psl_snapshot(),
        "code": code_manifest(),
        "started_utc": started,
    })
    t0 = time.perf_counter()
    status = "completed"
    try:
        if args.dataset == "phiusiil":
            metrics = run_phiusiil(out_dir, rid, args.threads, log_path)
        else:
            metrics = run_phreshphish(out_dir, rid, args.threads, log_path,
                                      train_shards=args.train_shards,
                                      test_shards=args.test_shards)
    except Exception as error:  # recorded, then re-raised: no silent partial run
        status = "failed"
        (out_dir / "run_status.json").write_text(
            json.dumps({"run_id": rid, "status": status, "error": f"{type(error).__name__}: {error}"},
                       indent=2), encoding="utf-8")
        registry.upsert({"run_id": rid, "status": status, "finished_utc": utc_now(),
                         "duration_s": round(time.perf_counter() - t0, 2),
                         "notes": f"{type(error).__name__}: {error}"})
        raise
    duration = time.perf_counter() - t0
    write_json(out_dir / "run_status.json", {
        "run_id": rid, "status": status, "n_fits": int(len(metrics)),
        "final": not diagnostic,
        "duration_s": round(duration, 2), "finished_utc": utc_now(),
        "metrics_file": "metrics_per_run.csv",
    })
    registry.upsert({
        "run_id": rid, "experiment": args.dataset, "dataset": args.dataset,
        "configs": "A0,A1,A2" if args.dataset == "phiusiil" else "A2",
        "protocols": "random,sitedisjoint" if args.dataset == "phiusiil" else "temporal",
        "models": "lightgbm,xgboost", "seeds": ",".join(map(str, data.SEEDS)),
        "threads": args.threads, "started_utc": started, "finished_utc": utc_now(),
        "duration_s": round(duration, 2), "status": status, "n_fits": int(len(metrics)),
        "output_dir": str(out_dir.relative_to(EXPERIMENT_DIR)),
        "log_path": str(log_path.relative_to(EXPERIMENT_DIR)),
    })
    write_run_report(out_dir, rid, metrics, args.dataset, status, duration, args.threads)
    print(f"\nRun {rid} {status}: {len(metrics)} fits in {duration:.1f}s -> {out_dir}", flush=True)
    return 0 if status == "completed" else 1


def cmd_plan(args) -> int:
    if args.dataset == "phiusiil":
        fits = planned_phiusiil_fits()
        print(f"PhiUSIIL fits: {len(fits)}")
        print(pd.DataFrame(fits).groupby(["protocol", "config", "model"]).size().to_string())
    else:
        print(f"PhreshPhish fits: {len(data.MODELS) * len(data.SEEDS)} "
              f"({len(data.MODELS)} models x {len(data.SEEDS)} seeds)")
    print(f"threads={args.threads}")
    return 0


def cmd_summarize(args) -> int:
    run_ids = [r for r in (args.phiusiil_run, args.phresh_run) if r]
    summary_lib.summarize_all(OUTPUT_ROOT, reps=args.replicates, run_ids=run_ids or None)
    return 0


def cmd_smoke(args) -> int:
    """Small, clearly non-final end-to-end check written under outputs/smoke/<id>."""
    rid = f"smoke_{utc_now().replace(':', '').replace('-', '')}"
    out_dir = OUTPUT_ROOT / "smoke" / rid
    out_dir.mkdir(parents=True, exist_ok=False)
    log_path = out_dir / "execution.log"
    started = utc_now()
    sys.stdout = _Tee(log_path)
    write_json(out_dir / "environment.json", environment_snapshot())
    write_json(out_dir / "feature_groups.json", data.feature_groups())
    data.feature_provenance().to_csv(out_dir / "feature_provenance.csv", index=False)
    write_json(out_dir / "design.json", {
        "run_id": rid, "kind": "smoke", "final": False,
        "warning": "NON-FINAL smoke check on truncated data; never cite these numbers",
        "command": getattr(args, "command_line", ""),
        "threads": args.threads, "threshold": data.THRESHOLD,
        "model_params": data.MODEL_PARAMS,
        "code": code_manifest(), "started_utc": utc_now(),
    })
    print(f"SMOKE RUN (non-final): {out_dir}", flush=True)
    if args.dataset == "phiusiil":
        metrics = run_phiusiil(out_dir, rid, args.threads, log_path, max_rows=args.rows)
    else:
        metrics = run_phreshphish(out_dir, rid, args.threads, log_path,
                                  train_shards=args.train_shards,
                                  test_shards=args.test_shards)
    summary_table = summarize_run_dir(out_dir, write=False)
    summary_table.to_csv(out_dir / "summary_smoke.csv", index=False)
    write_json(out_dir / "run_status.json", {
        "run_id": rid, "status": "completed", "final": False,
        "n_fits": int(len(metrics)), "finished_utc": utc_now(),
    })
    Registry().upsert({
        "run_id": rid, "experiment": "smoke", "dataset": args.dataset,
        "configs": "A0,A1,A2" if args.dataset == "phiusiil" else "A2",
        "protocols": "random,sitedisjoint" if args.dataset == "phiusiil" else "temporal",
        "models": "lightgbm,xgboost", "seeds": ",".join(map(str, data.SEEDS)),
        "threads": args.threads, "started_utc": started, "finished_utc": utc_now(),
        "status": "smoke_non_final", "n_fits": int(len(metrics)),
        "output_dir": str(out_dir.relative_to(EXPERIMENT_DIR)),
        "log_path": str(log_path.relative_to(EXPERIMENT_DIR)),
        "notes": "NON-FINAL truncated smoke check; never cite",
    })
    print(f"SMOKE completed: {len(metrics)} fits, {len(summary_table)} summary rows", flush=True)
    return 0


def write_run_report(out_dir: Path, rid: str, metrics: pd.DataFrame, dataset: str,
                     status: str, duration: float, threads: int) -> Path:
    """`report.md` for one run: derived facts only, no interpretation."""
    by = metrics.groupby(["protocol", "config", "model"]).size()
    undefined = metrics.undefined.astype("string").fillna("").ne("").sum() if "undefined" in metrics else 0
    lines = [
        f"# Run report - {rid}", "",
        f"- dataset: `{dataset}`",
        f"- status: `{status}`",
        f"- duration: {duration:.1f} s (threads={threads}, sequential fits)",
        f"- threshold: p_phish >= {data.THRESHOLD} for every fit",
        f"- fits recorded: {len(metrics)}; fits with at least one undefined metric: {int(undefined)}",
        "", "## Fits per protocol / config / model", "",
        "| protocol | config | model | fits |", "|---|---|---|---|",
    ]
    lines += [f"| {p} | {c} | {m} | {n} |" for (p, c, m), n in by.items()]
    lines += [
        "", "## Artifacts in this directory", "",
        "| file | rows | sha256 (first 16) |", "|---|---|---|",
    ]
    for name in ["metrics_per_run.csv", "row_ledger.csv", "excluded_rows.csv",
                 "test_domain_exposure.csv", "split_audit.csv", "feature_provenance.csv"]:
        path = out_dir / name
        if path.exists():
            rows = len(pd.read_csv(path))
            lines.append(f"| `{name}` | {rows} | `{sha256_file(path)[:16]}` |")
    preds = sorted(out_dir.glob("predictions_*.csv.gz"))
    lines += ["", f"- prediction files: {len(preds)} (`predictions_*.csv.gz`)",
              "", "## Verification", "",
              f"    python -m src.selfcheck {Path(out_dir).resolve().relative_to(EXPERIMENT_DIR.resolve())}",
              "", "Selfcheck recomputes each confusion matrix from the stored predictions and",
              "checks split, label and threshold invariants. It is not run automatically here.",
              "", "## Claim limits", "",
              "- A1 - A0 isolates the six content features only; it does not identify per-feature",
              "  contributions and does not prove label leakage.",
              "- A0 vs A2 changes feature count, source and extraction together; the difference is",
              "  not a content-feature ablation effect.",
              "- Random and site-disjoint use different test rows; no per-row test across protocols.",
              "- No tuning, early stopping, resampling or threshold selection on test data.",
    ]
    path = out_dir / "report.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def summarize_run_dir(run_dir: Path, write: bool = True) -> pd.DataFrame:
    metrics = pd.read_csv(Path(run_dir) / "metrics_per_run.csv")
    summary = evaluate.seed_summary(metrics)
    if write:
        summary.to_csv(Path(run_dir) / "summary.csv", index=False)
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="train one dataset's full configuration set")
    p_run.add_argument("--dataset", choices=["phiusiil", "phreshphish"], required=True)
    p_run.add_argument("--threads", type=int, default=data.DEFAULT_THREADS)
    p_run.add_argument("--train-shards", type=int, default=None,
                       help="PhreshPhish only; diagnostic subset, never for final results")
    p_run.add_argument("--test-shards", type=int, default=None,
                       help="PhreshPhish only; diagnostic subset, never for final results")
    p_run.set_defaults(func=cmd_run)

    p_plan = sub.add_parser("plan", help="print the planned fit matrix without training")
    p_plan.add_argument("--dataset", choices=["phiusiil", "phreshphish"], required=True)
    p_plan.add_argument("--threads", type=int, default=data.DEFAULT_THREADS)
    p_plan.set_defaults(func=cmd_plan)

    p_sum = sub.add_parser("summarize", help="summaries and bootstrap from saved predictions")
    p_sum.add_argument("--replicates", type=int, default=data.BOOTSTRAP_REPLICATES)
    p_sum.add_argument("--phiusiil-run", default=None,
                       help="main PhiUSIIL run id; required when several exist")
    p_sum.add_argument("--phresh-run", default=None,
                       help="main PhreshPhish run id; required when several exist")
    p_sum.set_defaults(func=cmd_summarize)

    p_smoke = sub.add_parser("smoke", help="non-final truncated end-to-end check")
    p_smoke.add_argument("--threads", type=int, default=2)
    p_smoke.add_argument("--dataset", choices=["phiusiil", "phreshphish"], default="phiusiil")
    p_smoke.add_argument("--rows", type=int, default=4000)
    p_smoke.add_argument("--train-shards", type=int, default=2)
    p_smoke.add_argument("--test-shards", type=int, default=1)
    p_smoke.add_argument("--replicates", type=int, default=200,
                         help="bootstrap replicates for the smoke check only")
    p_smoke.set_defaults(func=cmd_smoke)

    args = parser.parse_args(argv)
    args.command_line = "python -m src.run_experiment " + " ".join(sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
