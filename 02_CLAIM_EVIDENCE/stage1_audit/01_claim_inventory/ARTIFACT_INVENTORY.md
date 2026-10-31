# Artifact Inventory — Manuscript v8 and Experiments E1–E8

Audit root: E:\Kuliah\Tugas Akhir. Paths relative to this root. Primary = directly inspected raw output/source; review-package content is separately identified. Required means needed to independently reproduce claims, not necessarily redistribute third-party raw datasets.

## Manuscript and review package

| Artifact | Status | Details / SHA-256 |
|---|---|---|
| Final manuscript | Present | phishing/BITS_Draft_Phishing_URL_Leakage_v8_final.docx; SHA-256 65c8909be07a17427a0367306d3c9502be27ee36705e92c2234d61fc6896ccf |
| Structure check | Present | python-docx: 180 body paragraphs, 9 tables, 2 figures; Tables 1-8 plus one uncaptained feature table |
| Review package | Present, incomplete vs §5.2 wording | phishing/AI_Review_SINTA2_Package_v8/DAFTAR_BERKAS.md lists only selected E6-E8 artifacts; no E1-E5 directories/artifacts in package |

## E1 — PhiUSIIL cleaning, label-recoverability and splits

Present primary artifacts: dataset/PhiUSIIL Phishing/PhiUSIIL_Phishing_URL_Dataset.csv; Experiment/1 - PhiUSIIL Cleaning + Leakage-Audit Notebook/01_phiusiil_cleaning_audit.ipynb; phiusill_clean/phiusiil_clean.parquet; phiusiil_leakage_audit.md; split_random.csv; split_sitedisjoint.csv; split_temporal_manifest.json; splits_manifest.json.

Required/missing/limited: tldextract version/effective bundled PSL snapshot hash is not recorded. Notebook uses TLDExtract(suffix_list_urls=()) and exact suffix-list provenance is unavailable. No separate per-feature provenance CSV; raw source and executed notebook exist. Generated audit verdict defect: leakage report lines 14-18 labels LineOfCode/NoOfExternalRef DROP and title-match columns kept, while notebook DROP_COLS and actual parquet are opposite and agree with manuscript.

| Artifact | SHA-256 |
|---|---|
| 01_phiusiil_cleaning_audit.ipynb | 2a226702f9ec007f83b608c6b1fe8b16111af5435c9df1a7fe880639206a5eef |
| phiusill_clean/phiusiil_clean.parquet | 4c86b580ddc694c1a6bd2b0f249b43550508b2935be85c09b34dbaf67273468f |
| phiusill_clean/split_random.csv | 9520d9bd891c2fe443732a64d0484d52f32c434afa1cc61bd1c21f669a117ab3 |
| phiusill_clean/split_sitedisjoint.csv | be6f046d300aeeb443057d7172962ed9f4a8c6458c588ed069bd5cbf34999044 |

## E2 — UCI cleaning (not used for v8 claims)

Present: Experiment/2 - UCI Cleaning/02_uci_cleaning-run.ipynb, uci_clean.parquet, uci_manifest.json, uci_cleaning_report.md and source ZIP. Report says 11,055 rows, no raw URL, old static data, pre-binarized features. Manuscript does not use UCI, and E2 cannot support the listed PhiUSIIL/PhreshPhish claims. The displayed report includes a truncated parquet hash prefix 8cc37e4a109fc27b; this audit did not compute a new E2 hash.

## E3.1 — Legacy benchmark pipeline

Present: Experiment/3.1 - evaluation pipeline v2/03_evaluation_pipeline_v2_run_complete.ipynb, results_random.csv, results_sitedisjoint.csv, results_mcnemar.csv and ZIP. SHA-256 random results 262e538866c6461367cd2398d6c0f4ac90d66c9f74b0dd399d72dc0af09d41ef; site results 2b5453e9fde5aadbe2ef73d834f4dfde682364f981ed171d8118a8273b482abc.

Limits: no per-row predictions in this legacy output set; positive metric polarity is legitimate, not phishing (dataset label 0=phish,1=legit; sklearn metric default positive=1). Families are 47 all-features, 26 content, 21 lexical+host, not final A0/A1/A2. Do not use E3.1 as evidence against or in place of E5 final result files.

## E4 — PhreshPhish temporal audit

Present in local Experiment tree: 04_PhreshPhish_Temporal_Audit.ipynb; run_temporal.py; verify_end_to_end.py; report/verification docs; complete dated outputs including primary run outputs/20261022T170935017991Z and later deterministic repeat outputs/20261022T235747896241Z. Primary run contains design, input/output manifests, split metadata, row ledger, exclusions, unparseable URL, feature schema, five saved predictions, five models/parameter JSONs, per-seed metrics, monthly metrics, bootstrap and domain exposure. Input raw corpus is local at dataset/PhreshPhish/data, not bundled in review package. E4 primary point metrics match; its seed13 bootstrap limits differ from Table 5 limits. No separate PSL snapshot/checksum; HASIL_RUN_TEMPORAL.md:290-298 explicitly notes this limitation. E4 is absent from review package.

## E5 — Final A0/A1/A2 benchmark, paired bootstrap and temporal parity run

Present: Experiment/5 - PhiUSIIL Focused Ablation/README.md, source src/, run_registry.csv, final PhiUSIIL run outputs/20261025T050131000106Z (60 fits), temporal parity rerun outputs/20261025T050850736450Z (10 fits), summary outputs/summary_20261025T051222767276Z. Per-run predictions/models, feature-group/provenance files, input manifests, metrics, paired/bootstrap summaries and report are local. Review package has no E5 directory.

| Selected artifact | SHA-256 |
|---|---|
| outputs/20261025T050131000106Z/metrics_per_run.csv | 547e20865a0488789b8e36f2ea2bef4d0a3dbe7985f8de91756de326a09b5659 |
| outputs/summary_20261025T051222767276Z/summary.csv | 2262de43c529dbcfdf62b2eb839de49f65a75157c1f24927d8a3fcba8136ffe4 |
| outputs/summary_20261025T051222767276Z/paired_bootstrap.csv | 0bf34367d1a08d10a5152676149881012bc42c7b61e1b9dc07f46538a1c3f55f |
| outputs/summary_20261025T051222767276Z/bootstrap_temporal.csv | a8795edce5dffe549cc5001a93fbac7afd3e3068f7d52cf2c124f2b1fa581514 |

Temporal interval provenance: summary_manifest.json says bootstrap_seed=42; bootstrap_temporal.csv seed=13 is model seed assigned by summarizer. E5 README explicitly distinguishes primary arms and identifies temporal results as parity rerun. This makes manuscript 85 main fits a selected-arm count; not all executed model fits.

## E6 — Zero-shot cross-corpus transfer

Present: transfer.ipynb, README, verify_predictions.py, outputs/manifest.json, metrics.csv, 20 prediction files, primary_seed_domain_bootstrap.csv, independent_metrics_check.csv and execution_status.json. verify_predictions.py independently derives metrics and checks output hashes; independent_metrics_check.csv has 260 row-metric checks. Package contains a selected subset only: no prediction files, independent metric check or execution status.

| Selected artifact | SHA-256 |
|---|---|
| outputs/metrics.csv | e0f2e6861f99f8204b2285d8d1c2a47a1a33b7eccb6f82f8a27520ba7e0a67d4 |
| outputs/primary_seed_domain_bootstrap.csv | 03ef7e76dfadc36cdae113dd1455c201b7bcdb07dd2791fb2dc0c47582937cda |

## E7 — Operational thresholds

Present locally: source src/config.py, src/thresholds.py, src/run_experiment.py, verify_run.py, source/executed notebook, design/schema/row and input/output manifests, frozen thresholds, primary/across-seed test metrics, PPV projections, fit/validation/test predictions for five seeds, model and parameter files, splits, exclusions. Run directory: Experiment/7 - Operational Threshold Evaluation/outputs/20261026T064137272536Z. Package omits raw validation/test probabilities, fitted models and full source/provenance manifests.

| Selected artifact | SHA-256 |
|---|---|
| test_metrics_primary_seed.csv | 3473f282277004f00bb5d600c89baf2820beb8aa976d12822ab2e38a5586019b |
| thresholds_frozen.csv | 9d144ce027c2647cbcb4d70c01b63722016aad36a373662d9ac75536153597b0 |
| ppv_projections.csv | 5f337b1d36a278d04b39cd18b3845df9195dbc92761fb4f80058c8eac04d8aae |

## E8 — Error taxonomy

Present: error_taxonomy.py, executed notebook, README, category_error_table.csv (117 rows), redacted_examples.csv (16), execution_status.json with sequential counts 1-13, zero error outputs and hashes of 23 input files. Requires E4 predictions/split plus 21 raw test shards. Review package omits script, redacted examples and README. Cluster bootstrap CI [~1.6%,66.7%] appears in README but is not emitted by included code/table; no standalone bootstrap output/reproducer found in E8 folder.

| Selected artifact | SHA-256 |
|---|---|
| category_error_table.csv | ec2596e7b9f995b50ed91fb0c83344ff847c1c8a6d0442ab3fed8693437bcac7 |
| execution_status.json | 41a80064cf0c9a4657b7f56fbf7c7c675233f1722849adfd202a2fa8964a6c49 |

## Missing and unresolved evidence

1. Table 5 CI values match E5 summary output with bootstrap RNG seed42, but method says seed13; E4 seed13 output bounds are different.
2. E1 generated leakage report verdict column reverses dropped/kept status for four features; notebook and actual cleaned parquet support manuscript prose.
3. E8 platform-domain bootstrap result is not backed by a located machine-readable bootstrap output or re-executable bootstrap implementation.
4. External literature in Table 1 was not independently checked; papers are not part of E1-E8 local primary evidence.
5. Review package’s artifact scope is narrower than manuscript §5.2 availability statement: E1-E5 absent and source-level/per-row artifacts for E6-E8 omitted.
6. E1/E4 exact PSL snapshot provenance incomplete.
7. 85 model fits counts four designated main arms; E5 temporal parity rerun adds ten executed fits.
