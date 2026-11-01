# Experiment 9 — Reverse transfer: PhreshPhish → PhiUSIIL

New experiment, run 2026-11-01. Authorised explicitly by the author. It does **not** modify any earlier
experiment, notebook, or artifact.

## Why

The manuscript reports a frozen one-direction transfer, PhiUSIIL → PhreshPhish (Table 7: LightGBM F1 0,599064,
benign FPR 0,986478, MCC −0,146445). That is a single direction. This experiment runs the mirror image so the
portability statement is symmetric rather than an anecdote.

## What this is, and what it is not

It is a **frozen cross-corpus transfer** in the opposite direction: train on PhreshPhish, freeze everything,
test on PhiUSIIL with no adaptation.

It is **not** a temporal evaluation. PhiUSIIL carries no collection dates, so it cannot be placed on a
timeline. Combining the two corpora into one temporal design would confound vendor/pipeline differences with
time — a confound the manuscript already states it cannot separate (§3.6).

## Design

| Component | Value |
|---|---|
| Training corpus | PhreshPhish **fit block only**: 2024-07-02 ≤ date < 2025-07-01 |
| Target corpus | cleaned PhiUSIIL, 235 370 rows, never seen by the model |
| In-source reference | same model on the PhreshPhish test block: 2025-09-08 ≤ date < 2025-12-17 |
| Representation | A2, 18 URL-only features, shared extractor from `Experiment/5 .../src/features.py` |
| Model | LightGBM, 300 estimators, lr 0,05, 63 leaves, `n_jobs=-1` |
| Seeds | 13, 42, 777, 2024, 31415; primary 42 |
| Threshold | 0,5 frozen; no calibration or tuning on the target |
| Uncertainty | percentile bootstrap, unit = registrable domain, 1 000 replicates, RNG seed 42 |
| Labels | PhiUSIIL `1 = legitimate → y_phish = 0`, `0 = phishing → y_phish = 1`; PhreshPhish `phish → 1`, `benign → 0` |

The design deliberately mirrors Experiment 7 (thresholds) and Experiment 4 (temporal run) in
hyperparameters, seeds, extractor and bootstrap protocol, so the reverse number is comparable to the
forward number without a second set of conventions.

## Files

```
reverse_transfer.ipynb            executed notebook, outputs retained (10 cells)
outputs/<run id>/design.json      full configuration, environment, extractor hash
outputs/<run id>/input_manifest.json
outputs/<run id>/metrics_per_seed.csv
outputs/<run id>/metrics_summary.csv
outputs/<run id>/bootstrap_target_primary_seed.csv
outputs/<run id>/overlap_train_vs_target.csv
outputs/<run id>/output_manifest.json
```

## Reproduce

```bash
cd "E:\Kuliah\Tugas Akhir"
C:\Python314\python.exe -m jupyter nbconvert --to notebook --execute --inplace \
  "Experiment\9 - Reverse Transfer PhreshPhish to PhiUSIIL\reverse_transfer.ipynb"
```

Environment used: Python 3.14.7, pandas 3.1.0, numpy 2.5.3, lightgbm 4.7.0, scikit-learn 1.9.1,
tldextract 5.4.0 (bundled PSL snapshot; `suffix_list_urls=()` so no network fetch).

## Overlap control

The model never sees PhiUSIIL during training. Exact-URL and registrable-domain overlap between the
training block and the target corpus is measured and written to `overlap_train_vs_target.csv`; it is
reported in the results section rather than assumed to be zero.

## Results

See `RESULTS.md` in this folder, written from the executed notebook.
