"""Metrics, confusion counts and bootstrap intervals with explicit NA handling.

Rules (protocol section 6):

* positive class is phishing (1), benign is 0;
* predictions are ``prob >= 0.5``; the probability column is selected through
  ``model.classes_`` by the caller, never by position;
* FPR = FP / (FP + TN), miss rate = FN / (FN + TP);
* a metric that cannot be computed (missing class, empty denominator, single
  class for AUC) is reported as ``nan`` *and* named in ``undefined`` - it is
  never silently replaced by a sklearn default.

Bootstrap: the resampling unit is the registrable domain, not the row.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from . import data

MAIN_METRICS = ["f1_phish", "recall_phish", "mcc", "fpr_benign"]
EXTRA_METRICS = ["precision_phish", "accuracy", "roc_auc", "miss_phish", "average_precision"]


def confusion(y, pred) -> dict:
    y = np.asarray(y).astype(int)
    pred = np.asarray(pred).astype(int)
    return {
        "tn": int(((y == 0) & (pred == 0)).sum()),
        "fp": int(((y == 0) & (pred == 1)).sum()),
        "fn": int(((y == 1) & (pred == 0)).sum()),
        "tp": int(((y == 1) & (pred == 1)).sum()),
    }


def _safe_div(num, den):
    return float(num) / float(den) if den else float("nan")


def metrics_from_counts(c: dict) -> dict:
    """Every metric derived from the four counts, so saved predictions can be re-scored."""
    tn, fp, fn, tp = c["tn"], c["fp"], c["fn"], c["tp"]
    n = tn + fp + fn + tp
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    # Direct count form: TP=0 with a non-empty denominator is 0.0, not "undefined".
    f1 = _safe_div(2 * tp, 2 * tp + fp + fn)
    denom = np.sqrt(float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)))
    mcc = (tp * tn - fp * fn) / denom if denom else float("nan")
    out = {
        "n": n,
        "n_benign": tn + fp,
        "n_phish": tp + fn,
        "tn": tn, "fp": fp, "fn": fn, "tp": tp,
        "prevalence_phish": _safe_div(tp + fn, n),
        "precision_phish": precision,
        "recall_phish": recall,
        "f1_phish": f1,
        "mcc": mcc,
        "accuracy": _safe_div(tp + tn, n),
        "fpr_benign": _safe_div(fp, fp + tn),
        "miss_phish": _safe_div(fn, fn + tp),
    }
    out["undefined"] = sorted(k for k in
                              ["precision_phish", "recall_phish", "f1_phish", "mcc",
                               "accuracy", "fpr_benign", "miss_phish", "prevalence_phish"]
                              if not np.isfinite(out[k]))
    return out


def metrics(y, prob, threshold: float = 0.5) -> dict:
    """Full metric row for one prediction vector, including confusion counts."""
    y = np.asarray(y).astype(int)
    prob = np.asarray(prob, dtype=float)
    pred = (prob >= threshold).astype(int)
    c = confusion(y, pred)
    out = metrics_from_counts(c)
    out["threshold"] = threshold
    if len(np.unique(y)) == 2:
        out["roc_auc"] = float(roc_auc_score(y, prob))
        out["average_precision"] = float(average_precision_score(y, prob))
    else:
        out["roc_auc"] = float("nan")
        out["average_precision"] = float("nan")
        out["undefined"] = sorted(set(out["undefined"]) | {"roc_auc", "average_precision"})
    return out


# ---------------------------------------------------------------- bootstrap
def _domain_counts(frame: pd.DataFrame) -> pd.DataFrame:
    """Per-domain confusion counts for one prediction frame."""
    y = frame.y_phish.to_numpy().astype(int)
    pred = (frame.p_phish.to_numpy() >= data.THRESHOLD).astype(int)
    out = pd.DataFrame({
        "domain": frame.domain.to_numpy(),
        "tn": ((y == 0) & (pred == 0)).astype(int),
        "fp": ((y == 0) & (pred == 1)).astype(int),
        "fn": ((y == 1) & (pred == 0)).astype(int),
        "tp": ((y == 1) & (pred == 1)).astype(int),
    })
    return out.groupby("domain")[["tn", "fp", "fn", "tp"]].sum()


def cluster_bootstrap(frame: pd.DataFrame, reps: int = 1000, seed: int = 42) -> pd.DataFrame:
    """Percentile interval for the main metrics, resampling domains with replacement."""
    counts = _domain_counts(frame)
    if len(counts) < 2:
        raise ValueError("fewer than two domains; a cluster bootstrap is undefined")
    rng = np.random.default_rng(seed)
    point = metrics_from_counts(counts.sum().to_dict())
    draws = {k: [] for k in MAIN_METRICS + ["precision_phish", "accuracy"]}
    n = len(counts)
    arr = counts.to_numpy()
    for _ in range(reps):
        idx = rng.integers(0, n, size=n)
        m = metrics_from_counts(dict(zip(["tn", "fp", "fn", "tp"], arr[idx].sum(axis=0).tolist())))
        for k in draws:
            draws[k].append(m[k])
    rows = []
    for k, values in draws.items():
        v = np.asarray(values, dtype=float)
        v = v[np.isfinite(v)]
        rows.append({
            "metric": k,
            "estimate": point[k],
            "lower95": float(np.quantile(v, 0.025)) if len(v) else float("nan"),
            "upper95": float(np.quantile(v, 0.975)) if len(v) else float("nan"),
            "valid_replicates": int(len(v)),
            "replicates": reps,
            "seed": seed,
            "unit": "registrable_domain",
        })
    return pd.DataFrame(rows)


def paired_domain_bootstrap(frame_a: pd.DataFrame, frame_b: pd.DataFrame,
                            reps: int = 1000, seed: int = 42,
                            label_a: str = "A0", label_b: str = "A1") -> pd.DataFrame:
    """Paired domain bootstrap of (B - A) on the SAME test rows.

    Domains are resampled once and the identical weights are applied to both
    configurations, which is what makes the interval paired.
    """
    a = frame_a.sort_values("row_id").reset_index(drop=True)
    b = frame_b.sort_values("row_id").reset_index(drop=True)
    if not a.row_id.equals(b.row_id):
        raise ValueError("paired bootstrap requires identical test rows in the same order")
    if not a.y_phish.equals(b.y_phish):
        raise ValueError("paired bootstrap requires identical labels per aligned row")
    if not a.domain.equals(b.domain):
        raise ValueError("paired bootstrap requires the same domain key per aligned row")
    ca = _domain_counts(a)
    cb = _domain_counts(b)
    if not ca.index.equals(cb.index):
        raise ValueError("domain sets differ between the paired configurations")
    arr_a = ca.to_numpy()
    arr_b = cb.to_numpy()
    n = len(ca)
    if n < 2:
        raise ValueError("fewer than two domains; a cluster bootstrap is undefined")
    keys = ["tn", "fp", "fn", "tp"]
    point_a = metrics_from_counts(dict(zip(keys, arr_a.sum(axis=0).tolist())))
    point_b = metrics_from_counts(dict(zip(keys, arr_b.sum(axis=0).tolist())))
    rng = np.random.default_rng(seed)
    deltas = {"f1_phish": [], "fpr_benign": [], "recall_phish": [], "mcc": []}
    for _ in range(reps):
        idx = rng.integers(0, n, size=n)
        ma = metrics_from_counts(dict(zip(keys, arr_a[idx].sum(axis=0).tolist())))
        mb = metrics_from_counts(dict(zip(keys, arr_b[idx].sum(axis=0).tolist())))
        for k in deltas:
            deltas[k].append(mb[k] - ma[k])
    rows = []
    for k, values in deltas.items():
        v = np.asarray(values, dtype=float)
        v = v[np.isfinite(v)]
        rows.append({
            "metric": k,
            "config_minus": f"{label_b}-{label_a}",
            "estimate_delta": point_b[k] - point_a[k],
            f"estimate_{label_a}": point_a[k],
            f"estimate_{label_b}": point_b[k],
            "lower95": float(np.quantile(v, 0.025)) if len(v) else float("nan"),
            "upper95": float(np.quantile(v, 0.975)) if len(v) else float("nan"),
            "valid_replicates": int(len(v)),
            "replicates": reps,
            "seed": seed,
            "unit": "registrable_domain",
            "n_domains": n,
        })
    return pd.DataFrame(rows)


def base_rate_projection(frame: pd.DataFrame,
                         base_rates: tuple[float, ...] = (5e-4, 1e-3, 5e-3, 1e-2, 5e-2),
                         threshold: float | None = None) -> pd.DataFrame:
    """PPV and false alarms per 10,000 at hypothetical base rates.

    TPR and FPR are taken from the fixed-threshold confusion matrix and held
    constant; only prevalence changes. This is a projection, not a reweighting
    of the test set, and it assumes the same TPR/FPR off-cohort.
    """
    thr = data.THRESHOLD if threshold is None else threshold
    y = frame.y_phish.to_numpy().astype(int)
    pred = (frame.p_phish.to_numpy() >= thr).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    tpr = _safe_div(tp, tp + fn)
    fpr = _safe_div(fp, fp + tn)
    rows = []
    for rate in base_rates:
        ppv = (rate * tpr) / (rate * tpr + (1 - rate) * fpr) if np.isfinite(tpr) and np.isfinite(fpr) else float("nan")
        rows.append({
            "base_rate": rate,
            "tpr": tpr,
            "fpr": fpr,
            "ppv_projected": ppv,
            "false_alarms_per_10000_benign": 10000 * fpr,
            "missed_per_10000_phish": 10000 * (1 - tpr),
            "observed_prevalence": float(y.mean()),
        })
    return pd.DataFrame(rows)

def seed_summary(metrics_df: pd.DataFrame, group_cols=("dataset", "protocol", "config", "model")) -> pd.DataFrame:
    """Mean/SD/min/max over the five seeds. Not a substitute for the bootstrap CI."""
    cols = [c for c in MAIN_METRICS + ["precision_phish", "accuracy", "roc_auc"]
            if c in metrics_df.columns]
    rows = []
    for key, frame in metrics_df.groupby(list(group_cols)):
        row = dict(zip(group_cols, key if isinstance(key, tuple) else (key,)))
        row["n_seeds"] = int(frame.seed.nunique())
        row["seeds"] = ",".join(str(s) for s in sorted(frame.seed.unique()))
        for c in cols:
            row[f"{c}_mean"] = float(frame[c].mean())
            row[f"{c}_sd"] = float(frame[c].std(ddof=1)) if len(frame) > 1 else float("nan")
            row[f"{c}_min"] = float(frame[c].min())
            row[f"{c}_max"] = float(frame[c].max())
        rows.append(row)
    return pd.DataFrame(rows)
