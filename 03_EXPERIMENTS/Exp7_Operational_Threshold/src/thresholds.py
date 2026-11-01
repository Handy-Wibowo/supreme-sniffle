"""Operating-point selection on validation, and the metrics reported on test.

Two hard rules hold everywhere in this module:

* a threshold is a function of validation labels and validation scores only;
* test scores are read only by ``binary_metrics`` after the threshold is frozen.

Selection rules, all pre-declared in ``config.py``:

``default_0p5``   the fixed 0.5 rule Experiment 4 published.
``fpr_le_1pct``   smallest threshold whose validation benign FPR is <= 1 %.
``fpr_le_0p5pct`` smallest threshold whose validation benign FPR is <= 0.5 %.
``max_val_f1``    threshold maximising validation phishing-positive F1.

"Smallest threshold subject to an FPR cap" maximises recall under that cap,
because benign FPR is non-increasing in the threshold. Ties in F1 resolve to the
smaller threshold, which favours recall; the tie-break is deterministic and
recorded in ``thresholds_frozen.csv``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import matthews_corrcoef


def _confusion(y: np.ndarray, pred: np.ndarray):
    tp = int(np.sum((y == 1) & (pred == 1)))
    fp = int(np.sum((y == 0) & (pred == 1)))
    fn = int(np.sum((y == 1) & (pred == 0)))
    tn = int(np.sum((y == 0) & (pred == 0)))
    return tn, fp, fn, tp


def binary_metrics(y, p, threshold: float) -> dict:
    """Full operating-point report for one frozen threshold."""
    y = np.asarray(y).astype("int8")
    p = np.asarray(p, dtype="float64")
    pred = (p >= threshold).astype("int8")
    tn, fp, fn, tp = _confusion(y, pred)
    n_benign, n_phish = tn + fp, tp + fn

    def div(a, b):
        return float(a) / float(b) if b else float("nan")

    precision = div(tp, tp + fp)
    recall = div(tp, tp + fn)
    fpr = div(fp, n_benign)
    return dict(
        n=len(y), n_benign=n_benign, n_phish=n_phish,
        prevalence=div(n_phish, len(y)),
        tn=tn, fp=fp, fn=fn, tp=tp,
        f1_phish=div(2 * precision * recall, precision + recall),
        precision_phish=precision, ppv=precision,
        recall_phish=recall, tpr_phish=recall,
        fpr_benign=fpr, miss_rate=div(fn, n_phish),
        specificity=div(tn, n_benign),
        accuracy=div(tn + tp, len(y)),
        false_alarms_per_10k_benign=div(fp, n_benign) * 10_000,
        mcc=float(matthews_corrcoef(y, pred)) if len(np.unique(y)) == 2 else float("nan"),
    )


def ppv_projection(recall: float, fpr: float, prevalence: float) -> float:
    """PPV at a hypothetical prevalence, from the frozen operating point's TPR/FPR.

    Bayes form: pi*TPR / (pi*TPR + (1-pi)*FPR). Assumes the same TPR/FPR hold at
    that prevalence, which is the assumption being projected, not measured.
    """
    num = prevalence * recall
    den = num + (1 - prevalence) * fpr
    return float(num / den) if den else float("nan")


def _curve(y: np.ndarray, p: np.ndarray):
    """Cumulative confusion counts for every distinct threshold, plus reject-all."""
    y = np.asarray(y).astype("int8")
    p = np.asarray(p, dtype="float64")
    values, inverse = np.unique(p, return_inverse=True)
    pos = np.bincount(inverse, weights=y, minlength=len(values))
    neg = np.bincount(inverse, weights=(1 - y), minlength=len(values))
    # p >= values[k] means the whole block k and every higher block.
    tp = np.cumsum(pos[::-1])[::-1].astype("int64")
    fp = np.cumsum(neg[::-1])[::-1].astype("int64")
    thresholds = np.append(values, np.nextafter(values[-1], np.inf))
    return (thresholds, np.append(tp, 0), np.append(fp, 0),
            int(y.sum()), int((1 - y).sum()))


def select_fpr_rule(y, p, target_fpr: float) -> dict:
    """Smallest threshold whose validation benign FPR <= target_fpr."""
    thresholds, tp, fp, n_pos, n_neg = _curve(y, p)
    fpr = fp / n_neg
    ok = np.flatnonzero(fpr <= target_fpr)
    if not len(ok):
        raise ValueError(f"No validation threshold reaches FPR <= {target_fpr}.")
    k = int(ok[0])
    return dict(threshold=float(thresholds[k]),
                achieved_val_fpr=float(fpr[k]),
                val_tp=int(tp[k]), val_fp=int(fp[k]),
                reject_all=bool(tp[k] == 0 and fp[k] == 0))


def select_max_f1(y, p) -> dict:
    """Threshold maximising validation F1 for the phishing class; ties -> smaller."""
    thresholds, tp, fp, n_pos, _ = _curve(y, p)
    fn = n_pos - tp
    denom = 2 * tp + fp + fn
    f1 = np.divide(2 * tp, denom, out=np.zeros(len(tp), dtype="float64"), where=denom > 0)
    k = int(np.argmax(f1))
    return dict(threshold=float(thresholds[k]), achieved_val_f1=float(f1[k]),
                val_tp=int(tp[k]), val_fp=int(fp[k]),
                reject_all=bool(tp[k] == 0 and fp[k] == 0))


def freeze_thresholds(val_y, val_p, rules, default_threshold: float) -> pd.DataFrame:
    """Resolve every rule on validation and return the frozen table."""
    val_y = np.asarray(val_y).astype("int8")
    if len(np.unique(val_y)) != 2:
        raise ValueError("Validation needs both classes; threshold selection is undefined.")
    rows = []
    for rule, kind, param in rules:
        if kind == "default":
            thr = float(default_threshold)
            sel = dict(threshold=thr, reject_all=False)
            basis = f"fixed at {thr} (inherited from Experiment 4); not selected on data"
        elif kind == "fpr":
            sel = select_fpr_rule(val_y, val_p, param)
            basis = (f"smallest validation threshold with benign FPR <= {param:.4%} "
                     f"(max recall under the cap)")
        elif kind == "f1":
            sel = select_max_f1(val_y, val_p)
            basis = "validation F1 maximum (ties -> smaller threshold)"
        else:  # pragma: no cover - guards a typo in config
            raise ValueError(f"Unknown selection kind {kind!r}")
        val_metrics = binary_metrics(val_y, val_p, sel["threshold"])
        rows.append(dict(
            rule=rule, threshold=sel["threshold"], selection_basis=basis,
            val_n=val_metrics["n"], val_benign=val_metrics["n_benign"],
            val_phish=val_metrics["n_phish"],
            val_fp=val_metrics["fp"], val_tp=val_metrics["tp"],
            val_fn=val_metrics["fn"], val_tn=val_metrics["tn"],
            val_fpr=val_metrics["fpr_benign"],
            val_recall=val_metrics["recall_phish"],
            val_precision=val_metrics["precision_phish"],
            val_f1=val_metrics["f1_phish"],
            val_false_alarms_per_10k_benign=val_metrics["false_alarms_per_10k_benign"],
            reject_all=bool(sel.get("reject_all", False)),
        ))
    frozen = pd.DataFrame(rows)
    if frozen.threshold.duplicated().any():
        # Two rules landing on the same threshold is legitimate; report it once
        # per rule but make the duplication visible rather than silently merged.
        frozen["shares_threshold_with_other_rule"] = frozen.threshold.duplicated(keep=False)
    else:
        frozen["shares_threshold_with_other_rule"] = False
    return frozen
