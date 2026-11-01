# Experiment 9 — Results

Run: `outputs/20261101T062209564437Z` · executed notebook: `reverse_transfer.ipynb` (8 code cells, outputs retained)
Date: 2026-11-01 · Direction: **PhreshPhish (fit block) → PhiUSIIL**, frozen, threshold 0,5

## 1. Headline

| Arm | Corpus | n | F1 phish | Precision | Recall | FPR benign | MCC | ROC-AUC | AP |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Reverse transfer** (seed 42) | PhiUSIIL target | 235 370 | **0,549564** | 0,409503 | 0,835237 | **0,897783** | **−0,092320** | 0,642939 | 0,682202 |
| Reverse, 5-seed mean | PhiUSIIL target | 235 370 | 0,550219 ± 0,000646 | — | — | 0,896436 ± 0,001885 | −0,089188 ± 0,003531 | 0,639278 | — |
| **In-source reference** (seed 42) | PhreshPhish test | 168 060 | **0,805958** | 0,889221 | 0,736953 | 0,077263 | 0,677473 | 0,909696 | 0,913361 |

Uncertainty on the target (percentile bootstrap, 175 509 registrable domains, 1 000 replicates, RNG seed 42):

| Metric | Estimate | 95 % interval |
|---|---:|---|
| F1 phish | 0,549564 | [0,512634; 0,586764] |
| Precision | 0,409503 | [0,368570; 0,455654] |
| Recall | 0,835237 | [0,798916; 0,869975] |
| FPR benign | 0,897783 | [0,895279; 0,900180] |
| MCC | −0,092320 | [−0,137850; −0,042795] |

## 2. Compared with the forward arm already in the manuscript

| Direction | Train → Test | F1 | FPR | MCC | ROC-AUC |
|---|---|---:|---:|---:|---:|
| Forward (Table 7, seed 42) | PhiUSIIL → PhreshPhish | 0,599064 | 0,986478 | −0,146445 | 0,382566 |
| **Reverse (this run, seed 42)** | PhreshPhish → PhiUSIIL | 0,549564 | 0,897783 | −0,092320 | 0,642939 |

**The failure is bidirectional, and it is not symmetric.**

- Both directions collapse relative to their in-source reference (forward in-domain F1 0,995985; reverse
  in-source 0,805958).
- Both directions produce a negative MCC at threshold 0,5.
- But the ranking behaviour differs. Forward ROC-AUC 0,3826 is **below** 0,5: the target scores are
  anti-ordered for most rows. Reverse ROC-AUC 0,6429 is **above** 0,5: the reverse model still ranks target
  rows weakly in the right order, and fails mainly on calibration — at a frozen 0,5 threshold it flags 89,8 %
  of benign PhiUSIIL URLs as phishing.
- So "the model fails" is true in both directions, but the *mechanism* is not the same, and the manuscript
  should not describe one as the mirror of the other without saying this.

## 3. Anchor against a trivial classifier

On the PhiUSIIL target the always-phishing classifier scores F1 = 2·100 520 / (235 370 + 100 520) = **0,598529**.
The reverse model's 0,549564 is **below** that trivial baseline. In the forward direction the equivalent
baseline on PhreshPhish is 0,627227 against the model's 0,599064 — also below.

Both directions therefore underperform a constant "everything is phishing" predictor on F1. That is the
cleanest available statement that the frozen transfer is not operationally useful, and it is computed from
the confusion matrix rather than from any new modelling.

## 4. Overlap control

| Measure | Train (fit block) | Target (PhiUSIIL) | Common | Share of target rows |
|---|---:|---:|---:|---:|
| Exact URL | 372 380 | 235 370 | 137 | 0,058 % |
| Registrable domain | 102 352 | 175 509 | 9 026 | **21,6 %** |

Exact-URL overlap is negligible, so the collapse is not memorisation of identical URLs. Domain overlap is
not negligible: 21,6 % of target rows share a registrable domain with the training block. That does not
rescue the model (FPR is still 89,8 %), but any interpretation of the reverse number must state it.

## 5. Deviations from Experiment 7 worth recording

- Fit block here: **372 380** usable rows (372 381 in-window, 1 unparseable). Exact-URL de-duplication dropped
  **zero** rows inside the window. Experiment 7 records 372 213 after its full cleaning pipeline, which applies a
  boundary purge, a seen-URL purge and a de-duplication step to the whole corpus *before* the date blocks are
  formed. The 167-row gap (0,045 %) therefore comes from those purges, not from exact-URL duplication.
- In-source test block here: **168 060** rows. Experiment 7 records 168 035 after its seen-URL purge and
  de-duplication (168 060 → 168 057 → 168 035 in its row ledger).
- Because this run skips those purges, its in-source reference is measured on 25 rows more than the
  manuscript's temporal evaluation. The difference cannot move the headline result (F1 differs by 0,004 between
  the two arms' corpora-level baselines), but it is recorded rather than glossed.
- Everything else matches Experiment 7: A2 extractor file and feature order, LightGBM hyperparameters, seeds,
  threshold rule, bootstrap unit/replicates/seed.

## 6. What this licenses in the manuscript

Supported, if the authors want it:

- A sentence that frozen transfer fails in both directions on this corpus pair, with the two confusion
  matrices and the trivial-classifier anchor as evidence.
- A sentence that the failure modes differ: anti-ordered scores in the forward direction, miscalibration in
  the reverse.
- A stated caveat that the reverse arm is **not temporal** — PhiUSIIL is undated — so it strengthens the
  portability claim, not the temporal one.

Not supported by this run: any claim about causal mechanism, about other corpus pairs, about deployment
performance, or any claim that the reverse direction is a symmetric replication of the forward one.

## 7. Files

```
reverse_transfer.ipynb                        executed, 8 code cells, outputs retained
outputs/20261101T062209564437Z/design.json
outputs/20261101T062209564437Z/input_manifest.json
outputs/20261101T062209564437Z/metrics_per_seed.csv         10 rows (5 seeds x 2 arms)
outputs/20261101T062209564437Z/metrics_summary.csv
outputs/20261101T062209564437Z/bootstrap_target_primary_seed.csv
outputs/20261101T062209564437Z/overlap_train_vs_target.csv
outputs/20261101T062209564437Z/output_manifest.json
```
