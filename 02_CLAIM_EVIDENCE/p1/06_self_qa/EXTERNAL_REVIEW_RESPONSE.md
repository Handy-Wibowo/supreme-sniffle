# Response to the external review (REVIEW_INDEPENDEN_v10_P1)

Date: 2026-11-01
Review received: `ai review/v10 review/result/REVIEW_INDEPENDEN_v10_P1.md` — verdict BLOCK, SINTA2 FIT MAJOR REVISION, band 20–35 %.
Candidate reviewed by that report: `f312e95d…` (hash matches the artifact sent; no mismatch).
Candidate after this response: `d2ffef6726f50f9f174fec11901a02d32a6c63605adbce5a02f07d628e3f86f1`, 14 pages, 9 746 words, 39 registered changes.

The review was high quality: it verified the hash, read the primary sources [9] and [24], and found two defects the
internal dual review had missed. Every finding was checked against artifacts before acting.

## 1. Confirmed defects — fixed in P1-031…P1-041

| Review item | Verification | Action |
|---|---|---|
| **C1 / D3 — Table 5 estimand unidentified; its values differ from Table 4** | **CONFIRMED.** `metrics_all.csv` gives site-disjoint LightGBM **seed 42** A0 F1 = 0,9998559700417687 and A1 = 0,9988757242930035, which are exactly the `paired_bootstrap.csv` point estimates. Table 4 reports **5-seed means** (0,9996228 / 0,9990550). Both are correct for different estimands; the manuscript never said so. | P1-036 states the estimand (model seed 42, 35 100 domains, 1 000 bootstrap replicates, bootstrap RNG seed 42) and that it is not a 5-seed mean; P1-037 marks the caption; P1-038 gives the two numbers side by side (−0,000568 vs −0,000980) and says they are not interchangeable. |
| **C4 / D1 — Table 1 mischaracterises [9]** | **CONFIRMED** from the author version of [9]: the paper explicitly trains on one dataset and tests on the other, so "transfer fitur; tanpa pembekuan model" asserts a negative that the source contradicts. | Cell now reads "Uji transfer model lintas dataset dua arah dengan fitur bersama; protokol ambangnya tidak dinyatakan pada sumber yang diperiksa". |
| **C4 / D1 — [24] has an external cross-dataset evaluation not acknowledged; 0,9962–0,9984 is accuracy** | **CONFIRMED** from the publisher full text: Table 5 of [24] lists "External cross-dataset — 4.6 — LR, XGB, BERT", and the 0,9962–0,9984 range is test-set accuracy. | Table 1 row rewritten (external validation named, negative withdrawn); §1.2 now says **akurasi** and cites the external evaluation. |
| **C5 — "masih jarang dilaporkan" without search coverage** | Accepted. | Replaced with a positive statement of what this paper contributes on the tested corpus pair. |
| **C2 / D5 — "daya pembeda korpus tersebut habis"** | Accepted as over-strong. | Now "daya pembeda pada konfigurasi yang dievaluasi tampak terbatas". |
| **C1 / D4 — §3.2 claims t-intervals are reported but none appear; §2.9 claims Wilson intervals but Table 9 has none** | **CONFIRMED.** `category_error_table.csv` does carry `fp_ci95_lo/hi` and `fn_ci95_lo/hi`; no table in the manuscript shows them. | P1-039 and P1-040 now state where those intervals are stored and that they are not tabulated. |
| **D5 — §3.6 mixes the cross-corpus vendor confound into the within-corpus temporal argument** | Accepted. | P1-042 adds the scope correction: vendor/pipeline is a cross-corpus confound, not a between-month confound inside PhreshPhish. |
| **D5 — §2.1 "deterministik terhadap seed"** | Accepted: determinism was not verified from artifacts. | P1-041 replaces the claim with "konfigurasi dan seed dicatat untuk replikasi". |
| **D2 — timing reported without machine specification** | Accepted. | P1-046 states that hardware and thread count are not recorded, so the numbers are an execution log, not a cost comparison. |

## 2. Findings accepted but NOT actioned here — and why

| Review item | Why not | Owner |
|---|---|---|
| **C6 / D2 — full protocol recovery** | **DONE in P1-047.** Lampiran A + Tabel A1 now record, from artifacts: the frozen PhiUSIIL split manifests with per-fold counts at seed 13; the PhreshPhish snapshot (77 parquet shards, 666 315 rows, per-file SHA-256 in `input_manifest.json`, official train/test split used as-is); the 921-row exclusion ledger with reason breakdown (681 post-cutoff, 214 train duplicates, 22 test duplicates, 3 seen-in-train, 1 unparseable) and both stage totals; the string label mapping with out-of-domain rejection; A0/A1/A2 definitions; the A2 extractor file hash; both model configurations; the full environment including xgboost 3.4.1 and the PSL hash; the percentile bootstrap with domain resampling; the threshold rule (score >= t, candidates = unique validation probabilities); the 14-domain platform set and 7 binary categories; and the statement that hardware was not recorded. | agent — completed |
| **C1 / D4 — complete Table 10 mapping** | **Partly done in this pass.** Four rows added: the two 5-seed threshold summaries (verified against `test_metrics_across_seeds.csv`: 0,700739/0,546658/0,011365 and 0,646167/0,480645/0,005843), FN in the host-platform category (8 035, of which pages.dev 7 341), and FP/FN in the query category (52/13) from `category_error_table.csv`. Not added: the univariate AUCs (source not located) and the 175 509-domain / 636-IP figures (they appear in the Stage-1 claim matrix, not in a raw artifact I could verify). | agent |
| **C6 — access route in §5.2** | There is no public repository. A supplement route or a DOI deposit is the author's decision; inventing a URL would be worse than the current honest statement. | user |
| **Author metadata, CRediT** | Reserved by the user. | user |
| **D2 — PhreshPhish 498 255/168 060 vs 497 359/168 035** | Correctly flagged as UNVERIFIABLE, not an error. Needs the dataset revision used at run time; `input_manifest.json` in the canonical run may resolve it. | agent |

## 3. Where this leaves the manuscript

The review's scientific verdict — BLOCK, MAJOR REVISION, 20–35 % — was issued on `f312e95d…`. The two defects that
most damaged the scientific reading (Table 5 estimand, Table 1 mischaracterisation of [9] and [24]) are now fixed
and registered. The remaining block is dominated by protocol recovery (C6/D2) and the access route, not by claim
accuracy.

Priority for the next pass: (1) D2 protocol recovery in one dedicated sweep; (2) Table 10 completion for the
artifacts that exist; (3) author metadata and an access route; then (4) a fresh review on the new hash.
