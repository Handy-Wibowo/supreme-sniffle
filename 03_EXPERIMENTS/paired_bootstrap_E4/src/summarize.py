"""Summaries and bootstrap intervals computed from saved predictions only.

No training happens here: every number is derived from `predictions_*.csv.gz`
plus `metrics_per_run.csv`, so an independent reviewer can recompute it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from . import data, evaluate
from .provenance import (EXPERIMENT_DIR, OUTPUT_ROOT, Registry, new_run_dir,
                         sha256_file, utc_now, write_json)


def load_predictions(run_dir: Path) -> pd.DataFrame:
    """All prediction files of one run, stacked with their metadata columns."""
    files = sorted(Path(run_dir).glob("predictions_*.csv.gz"))
    if not files:
        raise FileNotFoundError(f"no predictions under {run_dir}")
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def paired_primary(run_dir: Path, protocol: str = "sitedisjoint", seed: int = 42,
                   reps: int = data.BOOTSTRAP_REPLICATES,
                   boot_seed: int = data.BOOTSTRAP_SEED) -> pd.DataFrame:
    """A1 minus A0 paired domain bootstrap on identical test rows (protocol 7.2)."""
    preds = load_predictions(run_dir)
    preds = preds[(preds.protocol == protocol) & (preds.seed == seed)]
    rows = []
    for model in data.MODELS:
        sub = preds[preds.model == model]
        a0 = sub[sub.config == "A0"]
        a1 = sub[sub.config == "A1"]
        if a0.empty or a1.empty:
            raise ValueError(f"missing A0/A1 predictions for {model} in {run_dir}")
        frame = evaluate.paired_domain_bootstrap(a0, a1, reps=reps, seed=boot_seed,
                                                 label_a="A0", label_b="A1")
        frame["dataset"] = "phiusiil"
        frame["protocol"] = protocol
        frame["model"] = model
        frame["seed"] = seed
        rows.append(frame)
    return pd.concat(rows, ignore_index=True)


def temporal_intervals(run_dir: Path, seed: int = 13,
                       reps: int = data.BOOTSTRAP_REPLICATES,
                       boot_seed: int = data.BOOTSTRAP_SEED) -> pd.DataFrame:
    """Domain-cluster percentile intervals for the PhreshPhish primary seed."""
    preds = load_predictions(run_dir)
    preds = preds[(preds.dataset == "phreshphish") & (preds.seed == seed)]
    rows = []
    for model in data.MODELS:
        frame = preds[preds.model == model]
        if frame.empty:
            raise ValueError(f"missing temporal predictions for {model}")
        ci = evaluate.cluster_bootstrap(frame, reps=reps, seed=boot_seed)
        ci["dataset"] = "phreshphish"
        ci["protocol"] = "temporal"
        ci["config"] = "A2"
        ci["model"] = model
        ci["seed"] = seed
        rows.append(ci)
    return pd.concat(rows, ignore_index=True)


def phiusiil_intervals(run_dir: Path, protocol: str = "sitedisjoint", seed: int = 42,
                       reps: int = data.BOOTSTRAP_REPLICATES,
                       boot_seed: int = data.BOOTSTRAP_SEED) -> pd.DataFrame:
    """Per-configuration intervals on the primary PhiUSIIL split (context, not a delta)."""
    preds = load_predictions(run_dir)
    preds = preds[(preds.protocol == protocol) & (preds.seed == seed)]
    rows = []
    for model in data.MODELS:
        for config in data.CONFIGS:
            frame = preds[(preds.model == model) & (preds.config == config)]
            if frame.empty:
                raise ValueError(f"missing {config}/{model} predictions")
            ci = evaluate.cluster_bootstrap(frame, reps=reps, seed=boot_seed)
            ci["dataset"] = "phiusiil"
            ci["protocol"] = protocol
            ci["config"] = config
            ci["model"] = model
            ci["seed"] = seed
            rows.append(ci)
    return pd.concat(rows, ignore_index=True)


def completed_runs(run_root: Path = OUTPUT_ROOT) -> list[Path]:
    """Run directories that finished cleanly; smoke runs are excluded by path."""
    found = []
    for status_file in sorted(Path(run_root).glob("*/run_status.json")):
        import json

        status = json.loads(status_file.read_text(encoding="utf-8"))
        if status.get("status") == "completed" and status.get("final", True):
            found.append(status_file.parent)
    return found


def select_runs(run_root: Path = OUTPUT_ROOT, run_ids: list[str] | None = None) -> list[Path]:
    """The main runs that enter the summary tables.

    Explicit ids are validated (completed, final, exactly one run per dataset). With no
    ids, discovery must be unambiguous: two completed final runs for one dataset is an
    error, never a silent pick.
    """
    if run_ids:
        runs = [Path(run_root) / rid for rid in run_ids]
        missing = [str(r) for r in runs if not (r / "run_status.json").exists()]
        if missing:
            raise FileNotFoundError(f"unknown run directories: {missing}")
    else:
        runs = completed_runs(run_root)

    by_dataset: dict[str, list[Path]] = {}
    for run in runs:
        status = json.loads((run / "run_status.json").read_text(encoding="utf-8"))
        if status.get("status") != "completed" or not status.get("final", True):
            raise ValueError(f"{run.name} is not a completed final run: {status}")
        dataset = pd.read_csv(run / "metrics_per_run.csv").dataset.iloc[0]
        by_dataset.setdefault(dataset, []).append(run)
    for dataset, group in by_dataset.items():
        if len(group) > 1:
            raise ValueError(
                f"{len(group)} completed final {dataset} runs "
                f"({[g.name for g in group]}); pass the intended run ids explicitly")
    if not by_dataset:
        raise FileNotFoundError(f"no completed final runs under {run_root}")
    return sorted(runs)


def summarize_all(run_root: Path = OUTPUT_ROOT, reps: int = data.BOOTSTRAP_REPLICATES,
                  out_root: Path | None = None, registry: Registry | None = None,
                  run_ids: list[str] | None = None) -> Path:
    """Merge the selected main runs into one summary directory (seed table + intervals)."""
    runs = select_runs(run_root, run_ids)
    rid, out_dir = new_run_dir("summary_", root=out_root)
    metrics = pd.concat([pd.read_csv(r / "metrics_per_run.csv") for r in runs], ignore_index=True)
    metrics.to_csv(out_dir / "metrics_all.csv", index=False)
    evaluate.seed_summary(metrics).to_csv(out_dir / "summary.csv", index=False)

    paired, temporal, intervals = [], [], []
    for run in runs:
        dataset = pd.read_csv(run / "metrics_per_run.csv").dataset.iloc[0]
        if dataset == "phiusiil":
            paired.append(paired_primary(run, reps=reps))
            intervals.append(phiusiil_intervals(run, reps=reps))
        elif dataset == "phreshphish":
            temporal.append(temporal_intervals(run, reps=reps))
    if paired:
        pd.concat(paired, ignore_index=True).to_csv(out_dir / "paired_bootstrap.csv", index=False)
    if intervals:
        pd.concat(intervals, ignore_index=True).to_csv(out_dir / "bootstrap_intervals.csv", index=False)
    if temporal:
        pd.concat(temporal, ignore_index=True).to_csv(out_dir / "bootstrap_temporal.csv", index=False)

    projections = []
    for run in runs:
        dataset = pd.read_csv(run / "metrics_per_run.csv").dataset.iloc[0]
        if dataset != "phreshphish":
            continue
        preds = load_predictions(run)
        preds = preds[preds.seed == data.PRIMARY_SEED_PHRESH]
        for model in data.MODELS:
            frame = preds[preds.model == model]
            if frame.empty:
                continue
            proj = evaluate.base_rate_projection(frame)
            proj["model"] = model
            projections.append(proj)
    if projections:
        pd.concat(projections, ignore_index=True).to_csv(
            out_dir / "base_rate_projection.csv", index=False)

    write_json(out_dir / "summary_manifest.json", {
        "run_id": rid,
        "created_utc": utc_now(),
        "source_runs": [{"run_dir": str(r.relative_to(EXPERIMENT_DIR)),
                         "metrics_sha256": sha256_file(r / "metrics_per_run.csv")} for r in runs],
        "replicates": reps,
        "bootstrap_seed": data.BOOTSTRAP_SEED,
        "unit": "registrable_domain",
        "files": sorted(p.name for p in out_dir.iterdir()),
        "notes": "Intervals describe sampling uncertainty of the test domains for a fixed "
                 "model and cohort; they are not temporal generalisation guarantees.",
    })
    (registry or Registry()).upsert({
        "run_id": rid, "experiment": "summary", "dataset": "both",
        "status": "completed", "n_fits": int(len(metrics)),
        "output_dir": str(out_dir.relative_to(EXPERIMENT_DIR)),
        "notes": "summary + bootstrap from saved predictions",
    })
    print(f"Summary {rid}: {len(runs)} runs, {len(metrics)} fits -> {out_dir}", flush=True)
    return out_dir
