# PACKAGE_INVENTORY.md — Actual contents of `AI_Review_SINTA2_Package_v8`

Audit date: 2026-10-28. Read-only; nothing in the package was modified. All hashes and sizes computed directly from the on-disk tree.

## 1. Package identity

- Root: `E:\Kuliah\Tugas Akhir\phishing\AI_Review_SINTA2_Package_v8`
- Declared self-description: `DAFTAR_BERKAS.md` states "Total isi paket: 22 berkas, terdiri atas 19 salinan artefak proyek dan 3 berkas panduan baru."
- Observed on disk: **24 files** — the 22 declared files plus two undeclared items (`REVIEW_INDEPENDEN_KELAYAKAN_SINTA2_v8.md`, a previous AI review the package guide says to exclude; and `01 02 03.zip`, an archive mirroring the 19 artifact copies without the three guide files).
- Manuscript copy inside package: `01_Draft/BITS_Draft_Phishing_URL_Leakage_v8_final.docx`, SHA-256 `65c8909be07a17427a0367306d3c9502cbe27ee36705e92c2234d61fc6896ccf` — **identical** to the working manuscript `phishing/BITS_Draft_Phishing_URL_Leakage_v8_final.docx`.

## 2. Complete file listing with SHA-256

### Guides (3, declared)

| File | Size (B) | SHA-256 |
|---|---|---|
| `DAFTAR_BERKAS.md` | 1,839 | `a79a03f89cc0dba2d5f49ce7e35c2966af1b52e33f3f3fe0f5cfb6f3914f6040` |
| `PROMPT_REVIEW_KELAYAKAN_SINTA2.md` | 9,621 | `3c69de8918f28be061f7a327cacf0486ecce53ec5a331233d8ba2cf516e5f435` |
| `README_PACKAGE.md` | 2,110 | `bb61fa3cbb6c8356b259233919ff8e8b505505ac5e76aee76344a717d4e44b2e` |

### Draft (2)

| File | Size (B) | SHA-256 |
|---|---|---|
| `01_Draft/BITS_Draft_Phishing_URL_Leakage_v8_final.docx` | 319,294 | `65c8909be07a17427a0367306d3c9502cbe27ee36705e92c2234d61fc6896ccf` |
| `01_Draft/BITS_Draft_Phishing_URL_Leakage_v8_final_preview.pdf` | 561,668 | `89b0919acfea74ab2a4da663ed99f26a842524d567b7277d3f379d94fbdf5210` |

### Evidence maps (3)

| File | Size (B) | SHA-256 |
|---|---|---|
| `02_Evidence/CLAIM_EVIDENCE_GATE.md` | 1,311 | `562e95f3f397005038da06268fee06e5d19573257340b59d5687b3cf3075ba4f` |
| `02_Evidence/EXPERIMENT_LOG.md` | 4,697 | `452902cd48a430509a1182fa1ad449a0649358099d8a41622143d909c7b22518` |
| `02_Evidence/FINAL_VERIFICATION_v8.md` | 2,310 | `73c48fcbf8adeb7daf06d545a79aec02f7ba468beae0a8ce9ecf41e4062b0b2b` |

### Experiment 6 — Cross-Corpus Transfer (4)

| File | Size (B) | SHA-256 |
|---|---|---|
| `03_Experiments/Exp6_Cross_Corpus/transfer.executed.ipynb` | 64,728 | `26301de0861646b2461c3c03e30c3051bc31ac2e4061c41922e4aeac949b1a1e` |
| `03_Experiments/Exp6_Cross_Corpus/metrics.csv` | 5,094 | `e0f2e6861f99f8204b2285d8d1c2a47a1a33b7eccb6f82f8a27520ba7e0a67d4` |
| `03_Experiments/Exp6_Cross_Corpus/primary_seed_domain_bootstrap.csv` | 2,134 | `03ef7e76dfadc36cdae113dd1455c201b7bcdb07dd2791fb2dc0c47582937cda` |
| `03_Experiments/Exp6_Cross_Corpus/manifest.json` | 9,213 | `105a73dce8669180b3f0978ddd2d8a860b00e05a85c43aeee98cadb4c690e0df` |

### Experiment 7 — Operational Threshold (7)

| File | Size (B) | SHA-256 |
|---|---|---|
| `03_Experiments/Exp7_Operational_Threshold/01_operational_thresholds.executed.ipynb` | 56,990 | `0c66dedc073ce3522d686a42efce8107b0460afeeaa27835a775ae00556c0516` |
| `03_Experiments/Exp7_Operational_Threshold/design.json` | 3,791 | `a4af9c764f66224e1a0b6545876a81f88ca3701be8fc5770ae34918061e552bc` |
| `03_Experiments/Exp7_Operational_Threshold/thresholds_frozen.csv` | 5,245 | `9d144ce027c2647cbcb4d70c01b63722016aad36a373662d9ac75536153597b0` |
| `03_Experiments/Exp7_Operational_Threshold/test_metrics_primary_seed.csv` | 1,399 | `3473f282277004f00bb5d600c89baf2820beb8aa976d12822ab2e38a5586019b` |
| `03_Experiments/Exp7_Operational_Threshold/test_metrics_across_seeds.csv` | 1,592 | `791f7ce7d2059ee30c08d3970c6fa6c027b8310fc08a91a00e6a0703a7a19495` |
| `03_Experiments/Exp7_Operational_Threshold/ppv_projections.csv` | 9,054 | `5f337b1d36a278d04b39cd18b3845df9195dbc92761fb4f80058c8eac04d8aae` |
| `03_Experiments/Exp7_Operational_Threshold/row_ledger.csv` | 843 | `8e9ea00586dca4fab222fc9cc21d482d0984213c7d05c5520ea7c16331837e4e` |

### Experiment 8 — Error Taxonomy (3)

| File | Size (B) | SHA-256 |
|---|---|---|
| `03_Experiments/Exp8_Error_Taxonomy/error_taxonomy.executed.ipynb` | 49,872 | `51296a0b5b3e6c8a4df5507419cef9da8b69303290a3e609c8a1531bfc5ae2ac` |
| `03_Experiments/Exp8_Error_Taxonomy/category_error_table.csv` | 8,158 | `ec2596e7b9f995b50ed91fb0c83344ff847c1c8a6d0442ab3fed8693437bcac7` |
| `03_Experiments/Exp8_Error_Taxonomy/execution_status.json` | 3,516 | `41a80064cf0c9a4657b7f56fbf7c7c675233f1722849adfd202a2fa8964a6c49` |

### Undeclared on-disk items (2)

| File | Size (B) | SHA-256 | Note |
|---|---|---|---|
| `REVIEW_INDEPENDEN_KELAYAKAN_SINTA2_v8.md` | 54,663 | `9cc16b20e3abc48f015e2ebdeb97bb5cb0041474ee8ed6ad1dc3e3c0fe45442b` | Prior AI review; package guide says to withhold such reviews for independence. Not listed in DAFTAR_BERKAS. |
| `01 02 03.zip` | 887,731 | `3be48649c5f8a7c107aaf4745aabcfaabc2c559c78ae5d72d4230683efe6b774` | ZIP mirroring the 19 artifact copies (draft + evidence + Exp6–E8); no guide files inside. |

## 3. What the package contains per experiment (verified by direct inspection)

- **E6 (transfer):** executed notebook; `metrics.csv` with per-cohort/per-seed/per-model metrics (confusion counts, F1, precision, recall, FPR, ROC-AUC, AP, MCC); seed-42 domain bootstrap; `manifest.json` declaring protocol "A2 zero-shot PhiUSIIL train → cleaned PhreshPhish temporal test", threshold 0.5, positive label phishing=1, 5 seeds (primary 42), the 18-feature ordered list, model params, bootstrap unit/replicates/RNG, input hashes, output hashes, environment, and `independent_prediction_metric_checks = 260`. The 20 per-row prediction files and the verifier output themselves are **not** in the package (manifest declares hashes for them; the target files are absent).
- **E7 (thresholds):** executed notebook; `design.json`; frozen thresholds; primary-seed and across-seed test metrics; PPV projections; row ledger (fit 372,213 / validation 125,146 / test 168,035; test 2025-09-08→2025-12-16, 91,259 benign + 76,776 phishing). Per-seed validation/test prediction files, model binaries, and source implementation are **not** in the package.
- **E8 (taxonomy):** executed notebook; `category_error_table.csv`; `execution_status.json` (task provenance, environment, hashes). Raw E4 predictions it consumes are **not** in the package.
- **Evidence maps:** three narrative MD files; these are recorded worker/reviewer claims, not independent audit output (per Stage-1 audit).

## 4. What the package does NOT contain (defensible omission list)

- Raw datasets: PhiUSIIL CSV, UCI ARFF, PhreshPhish shards (E1/E2/E4 inputs).
- E1 outputs: cleaned parquet, split files (random/site-disjoint), leakage-audit report.
- E2 and E3/E3.1 artifacts entirely (legacy; unused by v8 claims).
- E4 outputs: models, per-URL predictions, split manifests, bootstrap files.
- E5 outputs: benchmark summary, paired bootstrap, per-run predictions/models; the whole E5 tree.
- E6: the 20 per-row prediction files, `independent_metrics_check.csv`, `execution_status.json`, verifier script.
- E7: per-seed prediction files, model binaries, `src/` implementation, input manifests.
- E8: input prediction/split files it reads; no PSL snapshot.
- Any PSL snapshot or full environment lock (venvs in the workspace are non-hermetic per Stage-1 audit).

Consequence (matches Stage-1 audit): the package is a **review subset** sufficient for reviewing claims and spot-checking headline numbers, **not** a self-contained reproduction package. Sentence-level wording in EDIT_MAP E1 respects this exactly.

## 5. Correspondence to manuscript Section 5.2 (P0156) claims

| §5.2 (current) claim | In reviewer package? | In author workspace? |
|---|---|---|
| pembagian data (splits) | No | Yes (E1 split files; E4/E7 manifests) |
| konfigurasi fitur (feature configs) | Only the 18-name list inside E6 `manifest.json` | Yes (E5 feature files) |
| prediksi per baris | No | Yes (E4 five-seed, E6 20 files, E7 per-seed) |
| model (trained models) | No | Yes (E4, E7; E5 absent per audit) |
| metrik | Yes (E6 metrics.csv; E7 test metrics; E8 category table) | Yes |
| bootstrap | Partial (E6 primary-seed bootstrap only) | Yes |
| manifest checksum | Partial (E6 manifest in package; others absent) | Yes |
| notebook yang telah dieksekusi | Yes, for E6/E7/E8 only | Yes |
| coverage "untuk benchmark PhiUSIIL, evaluasi temporal, … taksonomi galat" (all five arms) | No — benchmark (E5) and temporal-primary (E4) arms have zero files in package | Yes |

This mismatch is C-054 / A06; the correction drafted in EDIT_MAP E1–E2 names only what is present and states the main omissions.
