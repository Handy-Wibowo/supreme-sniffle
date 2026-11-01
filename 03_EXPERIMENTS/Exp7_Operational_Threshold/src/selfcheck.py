"""Static and lineage checks. Run before trusting any number this experiment prints.

``python -m src.selfcheck``            threshold logic on synthetic data (no corpus)
``python -m src.selfcheck --lineage``  also compare against Experiment 4's published
                                       test split and Experiment 5's extractor

The lineage checks are the ones that make the leakage claim falsifiable: if the
test partition here differs from Experiment 4's, or if the features differ from
Experiment 5's audited extractor, this experiment is measuring something else.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys

import numpy as np
import pandas as pd

from . import config as C
from .thresholds import (binary_metrics, freeze_thresholds, ppv_projection,
                         select_fpr_rule, select_max_f1)


def check_threshold_logic() -> None:
    """Selection must obey its stated rule, and metrics must match a hand count."""
    y = np.array([0, 0, 0, 0, 1, 1, 1, 1], dtype="int8")
    p = np.array([0.9, 0.2, 0.05, 0.01, 0.95, 0.7, 0.3, 0.1])

    m = binary_metrics(y, p, 0.5)
    assert (m["tn"], m["fp"], m["fn"], m["tp"]) == (3, 1, 2, 2), m
    assert abs(m["precision_phish"] - 2 / 3) < 1e-12
    assert abs(m["recall_phish"] - 2 / 4) < 1e-12
    assert abs(m["fpr_benign"] - 1 / 4) < 1e-12
    assert abs(m["miss_rate"] - 2 / 4) < 1e-12
    assert abs(m["false_alarms_per_10k_benign"] - 2500.0) < 1e-9
    assert abs(m["f1_phish"] - 2 * (2 / 3) * (2 / 4) / (2 / 3 + 2 / 4)) < 1e-12

    # FPR cap 25 %: thresholds 0.9 and 0.7 and 0.3 all give benign FPR 0.25;
    # the rule must pick the smallest of them, 0.3 (max recall under the cap).
    sel = select_fpr_rule(y, p, 0.25)
    assert sel["threshold"] == 0.3, sel
    assert abs(sel["achieved_val_fpr"] - 0.25) < 1e-12
    # Tighter cap than any achievable point must not silently pass.
    try:
        select_fpr_rule(y, p, -0.1)
    except ValueError:
        pass
    else:
        raise AssertionError("select_fpr_rule accepted an unreachable FPR target")

    # F1 is maximised at 0.1: TP 4 of 4 phish, FP 2 of 4 benign -> 0.8.
    f1sel = select_max_f1(y, p)
    assert f1sel["threshold"] == 0.1, f1sel
    assert abs(f1sel["achieved_val_f1"] - 0.8) < 1e-12

    frozen = freeze_thresholds(y, p, [("default_0p5", "default", 0.5),
                                      ("fpr_le_1pct", "fpr", 0.01),
                                      ("max_val_f1", "f1", None)], 0.5)
    assert list(frozen.rule) == ["default_0p5", "fpr_le_1pct", "max_val_f1"]
    assert frozen.loc[frozen.rule == "fpr_le_1pct", "val_fpr"].iloc[0] <= 0.01 + 1e-12

    # Bayes projection: perfect separation at 1 % prevalence gives PPV 1.
    assert abs(ppv_projection(1.0, 0.0, 0.01) - 1.0) < 1e-12
    # Recall 0.5, FPR 0.01, prevalence 0.01 -> 0.005/(0.005+0.0099).
    assert abs(ppv_projection(0.5, 0.01, 0.01) - 0.005 / 0.0149) < 1e-12

    # A degenerate validation set must not be able to select a threshold.
    try:
        freeze_thresholds(np.zeros(10, dtype="int8"), np.linspace(0, 1, 10),
                          [("max_val_f1", "f1", None)], 0.5)
    except ValueError:
        pass
    else:
        raise AssertionError("single-class validation should raise")


def check_curve_matches_bruteforce() -> None:
    """The vectorised curve must equal a direct per-threshold recount."""
    rng = np.random.default_rng(7)
    y = rng.integers(0, 2, 500).astype("int8")
    p = np.round(rng.random(500), 3)
    for target in (0.01, 0.05, 0.1, 0.2):
        sel = select_fpr_rule(y, p, target)
        m = binary_metrics(y, p, sel["threshold"])
        assert abs(m["fpr_benign"] - sel["achieved_val_fpr"]) < 1e-12
        assert m["fpr_benign"] <= target + 1e-12
        lower = np.unique(p[p < sel["threshold"]])
        if len(lower):
            m2 = binary_metrics(y, p, float(lower[-1]))
            assert m2["fpr_benign"] > target + 1e-12, "a smaller threshold also met the cap"
    f1sel = select_max_f1(y, p)
    best = max(binary_metrics(y, p, float(t))["f1_phish"] for t in np.unique(p))
    assert abs(f1sel["achieved_val_f1"] - best) < 1e-12


def _load_exp5_features():
    spec = importlib.util.spec_from_file_location("exp5_features", C.EXP5_FEATURES)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_lineage() -> None:
    """Test partition and features must match the published upstream artifacts."""
    from .features import FEATURE_ORDER, feature_frame
    from .data import load_partition, prepare

    published = pd.read_csv(C.EXP4_RUN / "split_test.csv.gz")
    tr_raw, _ = load_partition(C.DATA_DIR, "train")
    te_raw, _ = load_partition(C.DATA_DIR, "test")
    _, _, test, ledger, _, _ = prepare(tr_raw, te_raw)
    del tr_raw, te_raw

    assert len(test) == len(published), (len(test), len(published))
    assert set(test.row_id) == set(published.row_id), "test row set differs from Experiment 4"
    merged = test[["row_id", "y_phish", "url_key"]].merge(
        published[["row_id", "y_phish", "url_sha256"]], on="row_id", how="inner",
        suffixes=("", "_exp4"))
    assert len(merged) == len(test)
    assert (merged.y_phish == merged.y_phish_exp4).all(), "test labels differ from Experiment 4"
    recomputed = merged.url_key.map(lambda u: hashlib.sha256(u.encode()).hexdigest())
    assert (recomputed == merged.url_sha256).all(), "test URL hashes differ from Experiment 4"
    print(f"lineage: test partition identical to Experiment 4 ({len(test)} rows)")

    exp5 = _load_exp5_features()
    sample = pd.concat([test.url.head(500), test.url.tail(200)]).reset_index(drop=True)
    mine = feature_frame(sample)
    theirs = pd.DataFrame([exp5.url_features(u) for u in sample], columns=exp5.FEATURE_ORDER)
    assert list(mine.columns) == list(theirs.columns) == FEATURE_ORDER
    assert mine.equals(theirs.astype("float64")), "feature values differ from Experiment 5"
    print(f"lineage: {len(sample)} URLs featurised identically to Experiment 5's extractor")
    print(ledger.to_string(index=False))


def main(argv) -> int:
    check_threshold_logic()
    print("selfcheck: threshold logic OK")
    check_curve_matches_bruteforce()
    print("selfcheck: curve matches brute force OK")
    if "--lineage" in argv:
        check_lineage()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
