# E6 verifier side-effect forensic audit

**Finding.** The executed transfer notebook preserves an earlier notebook-produced CSV digest (`368639…67e3d`); the later v8 package manifest records a different CSV digest (`9bac…9a42`) and is independently duplicated in its ZIP. Current files match the package snapshot exactly across the CSV and all output hashes, except the workspace manifest's verifier command field. This establishes a CSV format rewrite sometime after notebook execution but before the v8 package snapshot; it does **not** establish that this audit's verifier invocation changed the CSV bytes, since no immediate pre-invocation workspace copy exists. Current 260-row metric check has exact zero differences; no numerical prediction or metric change is evidenced.

## Scope and handling

Read-only forensic comparison; no verifier was run during this dispatch. Neither E6 target source file was edited, restored, copied, or otherwise touched. The only deliverables created by this task are this report and `SIDE_EFFECT_AUDIT.json`. Current timestamps and hashes below come from filesystem metadata/read-only hashing; timestamps are local filesystem metadata rendered as UTC, not trusted evidence of semantic content.

## Current E6 target files

| Path | Current size | Current filesystem mtime (UTC) | Current SHA-256 |
|---|---:|---|---|
| `Experiment/6 - Cross-Corpus Transfer/outputs/independent_metrics_check.csv` | 29,153 bytes | 2026-10-27T13:16:21.528198+00:00 | `9bac0a3fd018d5d7f8fa3340b49f9732b9aa76effe4a4dcdb5f2aaeef6a39a42` |
| `Experiment/6 - Cross-Corpus Transfer/outputs/manifest.json` | 9,144 bytes | 2026-10-27T13:16:21.611865+00:00 | `627c64b8b55d983ed3c51d1ab6d82e0cbeedeb3974b5d5709e000ff1bfba9dce` |

The sibling E6 `outputs/manifest.json` currently validates the CSV digest against the current CSV exactly. It records the rerun verifier environment command as `"C:\\Python314\\python.exe" "Experiment/6 - Cross-Corpus Transfer/verify_predictions.py"`, 260 checks, all passed, and the verifier source SHA-256 `565c34f66d982d793febeac351e51f5df6f4914e3d06635648335feeac260337`.

## Provenance and prior-state comparison

### CSV

- The completed notebook `Experiment/6 - Cross-Corpus Transfer/transfer.ipynb` has execution count 5 and captured output metadata timestamp `2026-10-26T06:43:06.706453Z` → idle `2026-10-26T06:43:26.670588Z`. Its printed, notebook-generated manifest records the then-current `independent_metrics_check.csv` SHA-256 as `368639c03d1cb25dd99d4d4666d6568e0707e0c64ec138139284acb896b67e3d`.
- The notebook source produces a CSV with columns `file, metric, saved_prediction_recompute, metrics_csv, absolute_difference, pass`; its earlier embedded digest is `368639…67e3d`. The current CSV uses columns `file, metric, independent_value, reported_value, absolute_difference, pass`, which matches the verifier source's exact `check_rows` keys. Since no pre-run CSV copy exists, it is **not proven** that this specific audit invocation performed the notebook-to-verifier schema rewrite. The later package snapshot proves that verifier-style CSV content already existed by 2026-10-26T06:47:40Z; format difference occurred after the notebook transcript and before that package snapshot.
- The later v8 package `manifest.json` and archived ZIP contain `output_hashes.independent_metrics_check.csv = 9bac0a3…9a42`, identical to the current CSV SHA-256. This is evidence that verifier-style CSV bytes existed by package time, before this 2026-10-27 audit. The notebook-versus-package digest mismatch proves that the file changed between notebook execution and packaging, but the exact time and action are unavailable. The current verifier invocation likely rewrote this same format to identical bytes; whether its write changed any bytes cannot be proven without an immediate pre-run workspace snapshot. The notebook/package mismatch is a handoff sequence gap, not evidence of changed predictions.

### Manifest

- Pre-run copy: `phishing/AI_Review_SINTA2_Package_v8/03_Experiments/Exp6_Cross_Corpus/manifest.json`, SHA-256 `105a73dce8669180b3f0978ddd2d8a860b00e05a85c43aeee98cadb4c690e0df`, filesystem mtime `2026-10-26T06:47:40.422005+00:00`.
- The `01 02 03.zip` archive contains a byte-identical copy of that same package manifest; its SHA-256 is also `105a73…0e0df`. The archive SHA-256 is `3be48649c5f8a7c107aaf4745aabcfaabc2c559c78ae5d72d4230683efe6b774`, archive filesystem mtime `2026-10-26T12:38:39.281218+00:00`. This corroborates an immutable, pre-audit manifest snapshot.
- Structured semantic diff shows only `independent_verification.command` differs: old value invokes Experiment 5's `.venv/Scripts/python.exe`; current value invokes `C:\Python314\python.exe`. All other top-level manifest fields match, including protocol, seeds, model parameters, inputs, all 25 output hashes, check count, `all_passed`, method, verifier script digest, environment, row counts, and executed notebook SHA.
- The workspace manifest's whole-file SHA differs from the package copy because this one JSON command field changed and pretty-printed bytes differ. It does not signal changes to model metrics or prediction artifacts.

## Numerical result and output integrity

- The pre-audit package manifest records 25 E6 outputs. Every one of those 25 current workspace output paths has the same SHA-256 as the package manifest; no mismatch or missing output was found. That set includes all 20 prediction CSVs, `metrics.csv`, `primary_seed_domain_bootstrap.csv`, the independent check CSV, execution status and executed transfer notebook.
- Current check CSV has 260 rows, 20 distinct prediction files, 13 metrics per prediction file, all `pass=True`, every `absolute_difference=0.0`. Current `manifest.json` agrees with the CSV hash.
- `metrics.csv` is unchanged against its pre-audit hash (`e0f2e6861f99f8204b2285d8d1c2a47a1a33b7eccb6f82f8a27520ba7e0a67d4`); each of the 20 prediction files' pre-audit hashes match current files. Therefore stored numerical predictions and metric summaries did not change between the immutable package snapshot and current workspace state.
- The prior executed notebook's manifest output listed 23 output hashes and recorded the earlier notebook-schema CSV digest; the package manifest later lists 25 hashes including verifier metadata/check artifacts. This shows a follow-up verification/packaging step happened after original notebook execution and before this audit. It does not identify exactly when the CSV rewrite occurred.

## Exact verifier write behavior (source evidence)

`Experiment/6 - Cross-Corpus Transfer/verify_predictions.py` lines 13–32 loads `metrics.csv` and 20 prediction files, independently recomputes predictions/metrics, and appends 260 checks. Lines 33–34 write `independent_metrics_check.csv`. Lines 35–42 load the existing manifest and validate listed output hashes excluding the check CSV that is about to be rewritten. Lines 43–45 set/refresh the CSV hash and `independent_verification` record, then overwrite `manifest.json`. It changes `independent_verification.command` based on `sys.executable`; it does not write predictions, model files, or `metrics.csv`.

The source establishes what a successful verifier run is designed to write. The earlier dispatch record in `04_reproducibility/COMMAND_LOG.md` records that the verifier was run and returned exit 0 (20 prediction files, 260 metric checks, 24 hashes). This forensic dispatch did not re-run it.

## What is proven vs. unverifiable

**Proven from retained bytes/logs:** Current SHA and timestamps above; pre-run package and ZIP manifest are identical; prior notebook embedded CSV digest is `368639…67e3d`; package-time manifest expected CSV digest `9bac…9a42`; current CSV digest is `9bac…9a42`; all 25 packaged E6 output digests match current files; only manifest semantic field changed is the verifier command; current numerical checks all equal exactly; verifier source's write locations and fields.

**Not directly proven:** The exact bytes/hash/mtime of the CSV and workspace manifest immediately before the 2026-10-27 audit invocation. The workspace manifest was not copied before that run. The prior notebook output is a digest, not a preserved CSV copy; the package copy is an immutable manifest snapshot but not the workspace manifest. Therefore the strongest conclusion is: the current CSV equals the earlier package-recorded CSV digest and current numerical outputs match the pre-audit package; the run's invocation is documented to rewrite the CSV and workspace manifest; whether the CSV bytes changed during that invocation cannot be distinguished from “rewrite identical bytes.” The manifest did change in one field relative to the pre-audit package copy, matching the active interpreter used by the audit verifier. No prediction, metric summary, or score change is evidenced.

## Evidence paths and commands

- Current target hashes, sizes and filesystem mtimes: read-only metadata probe in the audit session (values above).
- Pre-audit notebook CSV hash and execution timestamp: `Experiment/6 - Cross-Corpus Transfer/transfer.ipynb`, executed code cell 9 / stream output; notebook SHA-256 `26301de0861646b2461c3c03e30c3051bc31ac2e4061c41922e4aeac949b1a1e`.
- Pre-audit immutable package manifest: `phishing/AI_Review_SINTA2_Package_v8/03_Experiments/Exp6_Cross_Corpus/manifest.json`; matching archived member in `phishing/AI_Review_SINTA2_Package_v8/01 02 03.zip`.
- Current output manifest and metrics: `Experiment/6 - Cross-Corpus Transfer/outputs/manifest.json`, `outputs/metrics.csv`, `outputs/predictions_*.csv.gz`, `outputs/independent_metrics_check.csv`.
- Verifier source: `Experiment/6 - Cross-Corpus Transfer/verify_predictions.py` (read-only inspected; no rerun).
- Logged execution and exit: `04_reproducibility/COMMAND_LOG.md` C07; `e6_verify.log` reports `status=passed`, 20 files, 260 checks, 24 hash checks.
- Prior workspace-file hashes independently captured by prior cross-corpus audit: `phishing/revision_v9_stage1_audit/03_cross_corpus_overlap/OVERLAP_RESULTS.json`; note its workspace manifest digest is current-state `627c64…` and it explicitly has `transfer_manifest_sha256=null`, so it is not pre-run evidence.
