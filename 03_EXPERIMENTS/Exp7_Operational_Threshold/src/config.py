"""Paths, split dates and pre-declared threshold rules for Experiment 7.

Everything a reader needs to reproduce a run is a module constant here; the run
itself copies this file's resolved values into ``design.json``.

Chronology (inherited from Experiment 4, unchanged):

    fit       2024-07-02 .. 2025-06-30   (training period, earliest block)
    validation 2025-07-01 .. 2025-09-07  (training period, latest block)
    test      2025-09-08 .. 2025-12-16   (vendor test partition, untouched)

The cutoff and the purge order are Experiment 4's; only the internal split of
the training period is new.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

WORKSPACE = Path(__file__).resolve().parents[3]
EXPERIMENT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = WORKSPACE / "dataset" / "PhreshPhish" / "data"
OUTPUT_ROOT = EXPERIMENT_DIR / "outputs"

# Experiment 4's valid full run: source of the cleaning protocol and of the
# lineage check (identical test row set expected).
EXP4_RUN = (WORKSPACE / "Experiment" / "4 - PhreshPhish Temporal Audit"
            / "outputs" / "20261022T170935017991Z")

# Experiment 5's shared A2 extractor, used to prove feature parity.
EXP5_FEATURES = (WORKSPACE / "Experiment" / "5 - PhiUSIIL Focused Ablation"
                 / "src" / "features.py")

CUTOFF = pd.Timestamp("2025-09-08", tz="UTC")
VAL_START = pd.Timestamp("2025-07-01", tz="UTC")

LABEL_MAP = {"benign": 0, "phish": 1}
SEEDS = [13, 42, 2024, 777, 31415]
PRIMARY_SEED = 13

# Experiment 4's parameters, unchanged: no tuning anywhere in this experiment.
MODEL_PARAMS = dict(n_estimators=300, learning_rate=0.05, num_leaves=63,
                    n_jobs=-1, verbosity=-1)

# Prediction rule: positive iff p_phish >= threshold (same convention as Exp 4).
DEFAULT_THRESHOLD = 0.5

# Pre-declared operating rules. Fixed before any test-set score is looked at.
FPR_TARGETS = [("fpr_le_1pct", 0.01), ("fpr_le_0p5pct", 0.005)]
F1_RULE = "max_val_f1"
DEFAULT_RULE = "default_0p5"

# Prevalence projections for PPV, reported alongside the observed test PPV.
PPV_PREVALENCES = [0.01, 0.05]

UNPARSEABLE_POLICY = "exclude"
UNPARSEABLE_MAX_SHARE = 1e-4
