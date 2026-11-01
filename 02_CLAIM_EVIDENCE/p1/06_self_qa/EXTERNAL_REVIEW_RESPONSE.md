# Response to the external review (REVIEW_INDEPENDEN_v10_P1)

Date: 2026-11-01
Review received: `ai review/v10 review/result/REVIEW_INDEPENDEN_v10_P1.md` — verdict BLOCK, SINTA2 FIT MAJOR REVISION, band 20–35 %.
Candidate reviewed by that report: `f312e95d…` (hash matches the artifact sent; no mismatch).
Candidate after this response: `da460ce834ca4d1e899e073fbdf47eb0f385b49c69ced6a8e1cb03721f22235b`, 15 pages, 10 597 words, 59 registered changes.

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
| **D5 — §3.3 analyst-burden claim stated absolutely** | Accepted. | P1-048 makes it conditional: the real burden depends on benign and phishing row counts, prevalence, follow-up rules and cost per investigation, none of which is modelled. |
| **D5 — §3.5 prevalence treated as the sole explanation** | Accepted. | P1-049 adds "sebagian" and states that TPR/FPR are not guaranteed constant between months. |
| **D5 — §2.1 "deterministik terhadap seed"** | Accepted: determinism was not verified from artifacts. | P1-041 replaces the claim with "konfigurasi dan seed dicatat untuk replikasi". |
| **D2 — timing reported without machine specification** | Accepted. | P1-046 states that hardware and thread count are not recorded, so the numbers are an execution log, not a cost comparison. |

## 2. Findings accepted but NOT actioned here — and why

| Review item | Why not | Owner |
|---|---|---|
| **C6 / D2 — full protocol recovery** | **DONE in P1-047.** Lampiran A + Tabel A1 now record, from artifacts: the frozen PhiUSIIL split manifests with per-fold counts at seed 13; the PhreshPhish snapshot (77 parquet shards, 666 315 rows, per-file SHA-256 in `input_manifest.json`, official train/test split used as-is); the 921-row exclusion ledger with reason breakdown (681 post-cutoff, 214 train duplicates, 22 test duplicates, 3 seen-in-train, 1 unparseable) and both stage totals; the string label mapping with out-of-domain rejection; A0/A1/A2 definitions; the A2 extractor file hash; both model configurations; the full environment including xgboost 3.4.1 and the PSL hash; the percentile bootstrap with domain resampling; the threshold rule (score >= t, candidates = unique validation probabilities); the 14-domain platform set and 7 binary categories; and the statement that hardware was not recorded. | agent — completed |
| **C1 / D4 — complete Table 10 mapping** | **CLOSED in v1.2.0.** Two further rows added after locating the source: the three single-column AUCs (0,9961 / 0,9903 / 0,9880) and the domain counts (175 509 unique registrable domains, 636 IP rows), both verified in `phiusiil_leakage_audit.md`, which is now included in the archive. Previously added: the two 5-seed threshold summaries, platform FN, and query FP/FN. | Four rows added: the two 5-seed threshold summaries (verified against `test_metrics_across_seeds.csv`: 0,700739/0,546658/0,011365 and 0,646167/0,480645/0,005843), FN in the host-platform category (8 035, of which pages.dev 7 341), and FP/FN in the query category (52/13) from `category_error_table.csv`. Not added: the univariate AUCs (source not located) and the 175 509-domain / 636-IP figures (they appear in the Stage-1 claim matrix, not in a raw artifact I could verify). | agent |
| **C6 — access route in §5.2** | **CLOSED.** The evidence package is published at `https://github.com/Handy-Wibowo/supreme-sniffle` and archived on Zenodo under concept DOI `10.5281/zenodo.23847784` (v1.0.0 = version DOI `10.5281/zenodo.23847785`, v1.1.0 minted from the same concept). §5.2 now states the route, the archival DOI and the manifest verification. Verified from a clean clone: 170/170 manifest entries OK, 0 failures. | agent — completed |
| **Author metadata, CRediT** | Reserved by the user. | user |
| **D2 — PhreshPhish 498 255/168 060 vs 497 359/168 035** | Correctly flagged as UNVERIFIABLE, not an error. Needs the dataset revision used at run time; `input_manifest.json` in the canonical run may resolve it. | agent |

## 2b. New experiment integrated after this review (not a response to it)

Experiment 9 — frozen reverse transfer PhreshPhish → PhiUSIIL — was run and integrated after the review above:

- New paragraph in §3.7 with protocol, metrics, failure-mode contrast, trivial-baseline anchor (0,598529),
  overlap figures (0,058 % exact URL, 21,6 % registrable domain) and an explicit statement that it is not a
  temporal evaluation because PhiUSIIL is undated.
- Table 7 extended from 5 to 7 rows: `PhreshPhish→PhiUSIIL zero-shot` and `PhreshPhish dalam-sumber`.
- The "one direction" claim corrected in five places: Indonesian abstract, English abstract (two phrases),
  RQ4, contribution bullet 2, §1.2, and the limitations paragraph. A check confirms zero remaining
  "satu arah" / "one-direction" occurrences.
- Evidence archived: `03_EXPERIMENTS/Exp9_reverse_transfer/` (executed notebook, README, RESULTS, run outputs).

Result: the transfer failure is bidirectional but not symmetric — forward ROC-AUC 0,382566 (anti-ordered),
reverse 0,642939 (ordered but miscalibrated, 89,8 % benign FPR at the frozen threshold). Both directions fall
below the always-phishing F1 baseline of their target corpus.

## 3. Where this leaves the manuscript

The review's scientific verdict — BLOCK, MAJOR REVISION, 20–35 % — was issued on `f312e95d…`. The two defects that
most damaged the scientific reading (Table 5 estimand, Table 1 mischaracterisation of [9] and [24]) are now fixed
and registered. The remaining block is dominated by protocol recovery (C6/D2) and the access route, not by claim
accuracy.

Priority for the next pass: (1) D2 protocol recovery in one dedicated sweep; (2) Table 10 completion for the
artifacts that exist; (3) author metadata and an access route; then (4) a fresh review on the new hash.
