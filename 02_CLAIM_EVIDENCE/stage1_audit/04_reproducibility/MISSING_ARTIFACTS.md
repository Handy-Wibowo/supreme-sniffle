# Missing artifacts and reproducibility limits

Gaps are stated relative to independent regeneration of manuscript claims, not as a claim that no historical run occurred.

| Experiment | Missing or incomplete evidence | Reproducibility consequence |
|---|---|---|
| E1 | Dataset release/revision ID; pinned Colab Python/package environment; PSL snapshot checksum; original notebook execution has counts 4–9 rather than a restart/run-all history. | Cleaning/split pipeline is readable and output hashes verify, but raw-data revision and runtime cannot be fixed exactly from E1 alone. No trained models involved. |
| E2 | Raw ARFF input and its checksum/release identifier are not in the experiment directory; no dependency lock/runtime version; saved outputs are prior history, no fresh rerun. | Cleaned parquet integrity is checked, but ARFF→parquet regeneration is not independently demonstrated. |
| E3 | Per-row prediction probabilities/labels, saved fitted models, input/split hashes bound to result CSVs, pinned runtime, PSL snapshot identity, full timing provenance. UCI/Tranco data inputs also vary across Colab. | Aggregate metrics cannot be independently recalculated or precisely traced to input rows. The temporal claim remains a dry run/stub, not scored. v1 McNemar outputs compare unpaired test rows; v2 corrected this. |
| E4 | No PSL snapshot/checksum or full transitive dependency lock; external raw corpus release ID beyond shard-level hashes; clean full five-seed retrain not run in this audit. | Excellent saved model/prediction replay, but exact PSL-dependent domain identities and full training bit-for-bit reproducibility are not established. Test data was previously inspected. |
| E5 | Trained model binary artifacts absent from run package; original E5 PhiUSIIL training notebook's executed transcript was overwritten by reuse run; environment is not hermetic (system site packages); no external immutable dataset release label. | Saved metrics can be reconstructed from predictions, but model-level prediction replay/retrain needs the full source+input stack. Test data previously inspected. |
| E6 workspace | No full exact cross-run PSL identity; training model binaries aren't in transfer outputs; full train/test notebook was not rerun in this audit. | Workspace supports metric replay from 20 serialized prediction files; does not alone reproduce model fitting. Test data previously inspected. |
| E6 v8 package | Omits raw inputs, E5 feature source, E4 split/test data, per-row prediction CSVs, independent metrics check, and source notebook builder. Manifest declares 53 hashes but most target files are absent from package. | Package is useful for review but not a self-contained E6 numerical replay or executable reproduction package. |
| E7 workspace | Python venv shares global user site packages; full training was not repeated in this audit; test period known to earlier work. | 126/126 checks establish artifact-level replay and threshold lineage, not fresh retraining or blind evaluation. |
| E7 v8 package | Omits split prediction files/model binaries/source implementation and full raw data. | Package can show results/history but cannot regenerate threshold/test predictions independently by itself. |
| E8 | Full dependency lock not included; no PSL for taxonomy subdomain-depth labels (explicitly approximate); deterministic generated-table rerun not repeated during this audit. | Confusion counts replayed; category table historical hash recorded but was not independently rebuilt during this audit. Categories are descriptive and not causal. |
| Whole study | No maintained immutable release manifest binding manuscript claims to source code revision, dataset releases, all environment locks, PSL snapshot identity, full run commands and all prediction artifacts in one self-contained archive. | “Fully reproducible end-to-end from v8 package alone” is unsupported. Preserve distinction between reported historical run, arithmetic replay, artifact replay, executable reproduction, and full retraining. |

## Inspection/blindness ledger

- E1 planned temporal split manifest is explicitly a placeholder/collection-in-progress; no prospective test claim.
- E3 v1 temporal holdout is a stub; v2 fetches PhishTank URLs but halts before feature scoring. Not evidence of a scored blind temporal test.
- E4 design and reports say test was previously inspected in exploratory probes.
- E5 run designs say PhreshPhish test data was previously inspected.
- E6 README says target cohort was previously inspected and labels results exploratory.
- E7 README/HANDOFF say E4 test period was previously inspected. Validation-only threshold freezing is supported; blindness is not.
- E8 README says same test partition was previously inspected; it is descriptive post-hoc error analysis.

Therefore, **no blind/prospective claim is supportable for this PhreshPhish period**. A new dated corpus snapshot collected after protocol/model/threshold freeze, with auditable access controls and no prior test probes, would be needed for that claim.
