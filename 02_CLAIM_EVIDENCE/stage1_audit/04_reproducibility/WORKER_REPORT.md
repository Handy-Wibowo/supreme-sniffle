# Worker report — reproducibility audit

## Conclusion

Local reproducibility is strongest at **saved-artifact replay**, not fresh full training. E4's saved models reproduced all stored probabilities on the current raw test rows (25/25 checks; max probability delta zero); E6's workspace metrics replayed across all 20 prediction files (260 checks); E7's threshold, metric, split, and hash verification passed 126/126 checks; E5 saved prediction metrics selfchecked with zero F1 difference for 60+10 fits; E8 seed-13 confusion counts recomputed exactly. E1 and E2 cleaned artifacts matched their declared SHA-256 manifests. No expensive model fitting was performed.

The PhreshPhish test period is explicitly documented as previously inspected in E4–E8 source records. E7's thresholds were selected from validation scores only, but that only protects threshold choice—it does not establish a blind/prospective test. Do not claim blind evaluation, future-period generalization, or independently replicated time periods based on the five seeds. E4's exact PSL snapshot is not recorded. The v8 package is intentionally a review subset and omits critical raw inputs, source implementation and row-level E6/E7 predictions, so it is not standalone reproducible.

E3 remains weakest for numerical re-audit: only aggregate score rows are available, without row-level predictions or saved models. E3 v1 McNemar code uses mismatched test cohorts; v2 contains corrected shared-test comparisons. The E3 temporal branches are a stub/dry-run, not full scoring. E5 has a permanent notebook-execution-history gap for its original PhiUSIIL training execution, while stored run artifacts and logs remain.

## Deliverables

- `REPRODUCIBILITY_MATRIX.csv` — explicit status and evidence paths for E1–E8.
- `REPRODUCIBILITY_AUDIT.md` — detailed lineage, reproducibility level, inspection/blindness, limitations.
- `COMMAND_LOG.md` — exact safe checks, cwd, observed exit, logs, and side effects.
- `MISSING_ARTIFACTS.md` — gaps per experiment and blind-evaluation ledger.
- `WORKER_REPORT.md` — this summary.
- Supporting logs and `e4_end_to_end_report.json` reside alongside these files.

## Verification and scope

Executed verification: E1/E2 SHA checks, E4 output-manifest check and bounded end-to-end prediction replay, E5 saved metric selfchecks, E6 saved-prediction verification, E7 saved-run verifier, E8 confusion replay, notebook metadata inspection, and v8 package notebook/manifest inventory. All direct commands exited 0. Evidence was written to this owned output directory except that the E6 verifier updates its existing independent-metrics CSV and manifest as documented in `COMMAND_LOG.md`. No experiment code, datasets, notebooks, manuscript, or existing evidentiary output was intentionally edited; no notebook was created or executed.

No E3 training, E4 retraining, E5 retraining, E6 training, E7 training, E1/E2 notebook rerun, or E8 output-producing script run. These would be unnecessary for current artifact replay and/or write into source experiment folders. Full-training reproducibility is accordingly reported as historical or conditional, not as newly verified.
