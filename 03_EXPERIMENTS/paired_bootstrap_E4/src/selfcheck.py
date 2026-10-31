"""Assert-based invariant check over a finished run directory.

    python -m src.selfcheck outputs/<run_id>

Recomputes every confusion matrix from the saved predictions and compares it with
`metrics_per_run.csv`, then checks the split/label invariants that the protocol
requires. Any mismatch raises AssertionError; nothing is written.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import audit, data, evaluate


def unit_checks() -> None:
    """Metric/bookkeeping edge cases that a run directory cannot exercise."""
    # F1 with zero true positives but a non-empty denominator is 0.0, not undefined.
    assert evaluate.metrics_from_counts(dict(tn=2, fp=0, fn=1, tp=0))["f1_phish"] == 0.0
    assert evaluate.metrics_from_counts(dict(tn=0, fp=1, fn=1, tp=0))["f1_phish"] == 0.0
    # F1 is undefined only when its own denominator is empty.
    assert np.isnan(evaluate.metrics_from_counts(dict(tn=5, fp=0, fn=0, tp=0))["f1_phish"])
    # Tied scores must not depend on row order.
    a = evaluate.metrics([1, 0], [0.5, 0.5])["average_precision"]
    b = evaluate.metrics([0, 1], [0.5, 0.5])["average_precision"]
    assert a == b, f"average_precision depends on row order ({a} vs {b})"
    # A partial registry update keeps the columns it did not send.
    import tempfile

    from .provenance import Registry

    with tempfile.TemporaryDirectory() as tmp:
        reg = Registry(Path(tmp) / "registry.csv")
        reg.upsert({"run_id": "r1", "status": "running", "threads": 4, "started_utc": "t0"})
        # A timestamp written into a column that pandas inferred as float64 used to
        # raise TypeError; failed -> completed transitions must survive.
        reg.upsert({"run_id": "r1", "status": "failed", "duration_s": 12.5,
                    "finished_utc": "t1"})
        reg.upsert({"run_id": "r1", "status": "completed", "n_fits": 60,
                    "finished_utc": "t2"})
        reg.upsert({"run_id": "r2", "status": "running", "started_utc": "t3"})
        row = reg._read().set_index("run_id").loc["r1"]
        assert row.status == "completed" and int(row.threads) == 4, row.to_dict()
        assert row.started_utc == "t0" and row.finished_utc == "t2", row.to_dict()
        assert float(row.duration_s) == 12.5 and float(row.n_fits) == 60, row.to_dict()
        assert len(reg._read()) == 2, "upsert duplicated a row"

def check_run(run_dir: Path) -> dict:
    run_dir = Path(run_dir)
    metrics = pd.read_csv(run_dir / "metrics_per_run.csv")
    assert len(metrics), f"{run_dir}: empty metrics_per_run.csv"
    assert metrics.status.eq("completed").all(), "incomplete fit recorded as completed"

    worst = 0.0
    for row in metrics.itertuples():
        path = (run_dir / f"predictions_{row.dataset}_{row.protocol}_{row.config}_"
                          f"{row.model}_seed{row.seed}.csv.gz")
        assert path.exists(), f"missing predictions for {row.model}/{row.config}/seed{row.seed}"
        pred = pd.read_csv(path)
        assert len(pred) == row.n, f"{path.name}: {len(pred)} rows vs metrics n={row.n}"
        assert pred.y_phish.isin([0, 1]).all(), "target is not canonical phishing=1"
        assert pred.p_phish.between(0, 1).all(), "probability outside [0, 1]"
        assert (pred.pred == (pred.p_phish >= data.THRESHOLD).astype(int)).all(), \
            "stored pred does not follow the fixed 0.5 threshold"
        recomputed = evaluate.metrics(pred.y_phish, pred.p_phish, data.THRESHOLD)
        for key in ("tn", "fp", "fn", "tp"):
            assert recomputed[key] == getattr(row, key), f"{path.name}: {key} mismatch"
        worst = max(worst, abs(recomputed["f1_phish"] - row.f1_phish))
        assert (recomputed["n"] == row.n == recomputed["tn"] + recomputed["fp"]
                + recomputed["fn"] + recomputed["tp"]), f"{path.name}: confusion total mismatch"
        undefined = set(filter(None, str(row.undefined).split(";"))) if pd.notna(row.undefined) else set()
        assert undefined == set(recomputed["undefined"]), \
            f"{path.name}: undefined metrics recorded as {undefined} vs {recomputed['undefined']}"
        assert pred.domain.notna().all(), "missing domain key on test rows"
    assert worst < 1e-9, f"F1 not reproducible from predictions (max diff {worst})"

    dataset = metrics.dataset.iloc[0]
    if (run_dir / "row_ledger.csv").exists():  # PhreshPhish only: PhiUSIIL keeps the frozen split
        ledger = pd.read_csv(run_dir / "row_ledger.csv").set_index("stage")
        excluded = pd.read_csv(run_dir / "excluded_rows.csv")
        excluded["partition"] = excluded.row_id.str.split(":").str[0]
        for part in ("train", "test"):
            raw = int(ledger.loc[f"{part}_raw", "rows"])
            final = int(ledger.loc[f"{part}_unique", "rows"])
            removed = int((excluded.partition == part).sum())
            assert raw - removed == final, f"{part}: {raw} raw - {removed} excluded != {final} kept"
            assert ledger.loc[f"{part}_raw", "benign"] + ledger.loc[f"{part}_raw", "phish"] == raw

    if dataset == "phiusiil":
        for protocol in data.PROTOCOLS_PHIUSIIL:
            assert set(metrics[metrics.protocol == protocol].config) == set(data.CONFIGS)
        pred = pd.read_csv(sorted(run_dir.glob("predictions_phiusiil_sitedisjoint_A0_lightgbm_seed*.csv.gz"))[0])
        train_ids, test_ids = data.load_split("sitedisjoint", int(pred.seed.iloc[0]))
        domains = audit.domain_keys(data.load_phiusiil()).to_dict()
        overlap = {domains[i] for i in train_ids.url_id} & {domains[i] for i in test_ids.url_id}
        assert not overlap, f"site-disjoint split shares {len(overlap)} domain keys"
        from .features import canonical_url

        url_by_id = data.load_phiusiil().set_index("url_id")["URL"]
        train_keys = {canonical_url(url_by_id[i]) for i in train_ids.url_id}
        straddle = [i for i in test_ids.url_id if canonical_url(url_by_id[i]) in train_keys]
        assert not straddle, f"site-disjoint split shares {len(straddle)} canonical URL keys"
        design = json.loads((run_dir / "design.json").read_text())
        if design.get("kind") == "smoke":  # smoke runs subsample rows on purpose
            assert set(pred.row_id) <= set(test_ids.url_id), "smoke test rows are not split test rows"
        else:
            assert set(pred.row_id) == set(test_ids.url_id), "test rows differ from the frozen split"
    else:
        assert set(metrics.config) == {"A2"}, "temporal run must use A2 only"
        assert len(metrics) == len(data.MODELS) * len(data.SEEDS)
        dates = pd.concat([pd.read_csv(p) for p in run_dir.glob("predictions_phreshphish_*.csv.gz")])
        assert pd.to_datetime(dates.date, utc=True).ge(data.CUTOFF_UTC).all(), \
            "test row before the temporal cutoff"
    return {"run_dir": str(run_dir), "fits": int(len(metrics)), "max_f1_diff": worst}


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    unit_checks()
    if not argv:
        print("UNIT CHECKS PASS (no run directory given)")
        return 0
    if len(argv) != 1:
        print(__doc__)
        return 2
    print(check_run(Path(argv[0])))
    print("SELFCHECK PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
