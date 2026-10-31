# Worker report — cross-corpus overlap audit

Implemented and executed `overlap_audit.py` under this owned output folder. Results and all denominators are in `OVERLAP_AUDIT.md`, `OVERLAP_RESULTS.json`, and `overlap_summary.csv`; frozen no-overlap metrics are also in `no_overlap_metrics.csv`.

The audited cohorts contain 141,222 PhiUSIIL seed-42 training rows and 168,035 PhreshPhish temporal-test rows. The conservative no-overlap subset contains 127,365 target rows. Prediction row joins succeeded for all 10 model/seed files; source/target artifact hashes matched the existing Experiment 6 manifest.

Checks run: deterministic synthetic `--self-check`; full audit; target URL reconstruction checked by canonical URL SHA-256 for all 168,035 rows; output/schema/denominator/hash and prediction-join validation. All source and target inputs matched the recorded Experiment 6 manifest; no manuscript or source data was edited.
