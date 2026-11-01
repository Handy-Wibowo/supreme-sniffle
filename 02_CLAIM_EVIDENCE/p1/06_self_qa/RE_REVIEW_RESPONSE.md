# Response to the second independent review (REVIEW_ULANG_v10_P1_31dc1c21)

Date: 2026-11-01
Review received: `ai review/v10 review/result/REVIEW_ULANG_v10_P1_31dc1c21.md`
Reviewed artifact: `31dc1c21…` — the reviewer independently confirmed that hash and verified all 181 manifest entries.
Candidate after this response: `cc7eebeb81d85724e2273f03dba187272c60aa5f098bf13c33ea4aea9224a4e2` — 15 pages, 10,587 words, 57 registered changes, package 191 files.
Verdict received: BLOCK / MAJOR REVISION / 40–55 %.

This review was materially better than the first: it fetched the archive, read the code, and found errors that were mine, not artefacts of a text extraction. Six of its findings are confirmed defects and are fixed below.

## 1. Confirmed defects, fixed

| # | Finding | Verification | Fix |
|---|---|---|---|
| 1 | **Table 10 rows 1–2 cite the wrong files**: `results_random.csv` / `results_sitedisjoint.csv` come from the old pipeline, whose `family` values are `all-features`/`content`/`lexical+host` with a different positive-class convention; the deltas actually come from `summary.csv` of Experiment 5 | **CONFIRMED.** The delta values reproduce only from `Experiment/5 .../summary.csv`, not from the old pipeline tables. | Both rows now cite `summary.csv (eksperimen 5)` and show the two terms being subtracted. |
| 2 | **Minimum delta is misreported**: 0,000163 was obtained by subtracting already-rounded means; the exact value is 0,000162456 → 0,000162 | **CONFIRMED.** `0.999811573 − 0.999649117 = 0.000162455746`. | Table 10 now reads 0,000162. |
| 3 | **AUC row mislabels feature membership**: `URLSimilarityIndex` is one of the four *dropped* columns, not an A0 column | **CONFIRMED.** The manuscript's own DROP_COLS statement lists it as removed. | Row now reads "tiga kolom sumber: URLSimilarityIndex (dibuang); LineOfCode dan NoOfExternalRef (dipertahankan dalam A0)". |
| 4 | **§3.7 overreaches**: "mekanisme yang berbeda" and "sehingga" attribute a mechanism and imply calibration repair would help | Accepted. The reviewer's own counter-argument is sound: at scores ≥0,5 the mean predicted probability must be ≥0,5 while the observed phishing share is 0,409503, so miscalibration *is* indicated — but mechanism is not established. | Paragraph rewritten to the reviewer's proposed framing: ranking pattern differs, operating point is mismatched, discrimination and calibration are not separated, no cause claimed, no repair promised. Bootstrap intervals for the reverse arm added (they existed in the artefact). |
| 5 | **"Protokol yang sama" is inaccurate**: E9 used exact-URL dedup inside date blocks, not the canonical key + purge chain; 372.380 vs 372.213 fit rows; 168.060 vs 168.035 test rows; LightGBM only | **CONFIRMED** against both `design.json` files and the row ledgers. | §3.7 now says "prinsip yang sama" and names the representation, frozen model and threshold; Table 7 caption states the 3 seen URLs **and 22 duplicates**, the 372.380/168.060 figures for E9, the canonical purge for the forward arm, and the LightGBM-only scope of the reverse arm. |
| 6 | **Experiment 9 not integrated into the methods**: 85-fit count, one-direction description, "PhreshPhish only as target" | **CONFIRMED.** | 85 → **90 fits** (60+10+10+5+5); Figure 1 caption now says it depicts the forward arm and that the reverse arm is in Experiment 9. |
| 7 | **Lampiran A extractor hash does not match the shipped `features.py`** | **CONFIRMED, and this was my error.** `c98b119c…` is Experiment 7's copy per its `design.json`; the shipped `Experiment/5 .../src/features.py` hashes `81822b4f…`, and Experiment 9 reports the latter. | Lampiran A now names **both** copies with their hashes and states explicitly that value-level equivalence between them was not verified — only the 18-feature contract and order. |
| 8 | **§2.1 determinism contradiction**: full determinism asserted, then said to be unverified | **CONFIRMED.** The appended caveat sat beside the original claim. | The claim itself is replaced: "mencatat konfigurasi dan seed untuk replikasi". |
| 9 | **§3.6 vendor confound contradiction**: vendor named as a within-corpus temporal confound, then denied at the paragraph end | **CONFIRMED.** | The sentence now scopes the vendor confound to the PhiUSIIL–PhreshPhish comparison and states why it does not apply between months inside PhreshPhish. |
| 10 | **Lampiran A label row overgeneralised**; E9 compares to the string `phish` without an explicit rejection check | Accepted. | Label row now separates PhreshPhish (string mapping, with rejection in the temporal/threshold pipelines) from PhiUSIIL (numeric source coding), and records that E9 only printed label domains. |
| 11 | **"Split resmi apa adanya"** hides the 681-row boundary purge | **CONFIRMED** in `excluded_rows.csv`. | Snapshot row now states the official split was used as a frame, with 681 fit-block rows removed at the cutoff. |
| 12 | **Hardware "not recorded" too absolute**: metadata has `logical_cpus=16`, `n_jobs=-1`, generic CPU id | **CONFIRMED** in the temporal `design.json`. | Timing row now states what *is* recorded and what is not (effective threads, RAM, load). |
| 13 | **"Lebih tipis" unsupported** by any quantitative survey | Accepted. | Bounded: "lebih sedikit dijumpai ... pada penelusuran terarah yang dilakukan di sini; pernyataan ini tidak didasarkan pada survei kuantitatif". |
| 14 | **"Di atas 0,988"** cannot be inferred from a 4-decimal display | Accepted. | Now reads "sekitar 0,988 atau lebih". |

## 2. Archive gaps closed (C6)

The reviewer's C6 block rested on missing dependencies. Two are now in the archive:

- `03_EXPERIMENTS/E1_E5_pipeline/split_random.csv` and `split_sitedisjoint.csv` — the frozen ID–fold manifests
  (seed, url_id, fold) that every arm reads. 18,1 MB each; no URLs, so no sensitivity.
- `03_EXPERIMENTS/Exp7_Operational_Threshold/src/` — the eight modules the executed notebook imports
  (`config.py`, `data.py`, `features.py`, `provenance.py`, `run_experiment.py`, `selfcheck.py`, `thresholds.py`,
  `__init__.py`).

Package now 191 files, verified 191/191 from a clean clone.

## 3. Still open, and why

| Item | Reason |
|---|---|
| ~~Row-level attribution of the 167-row fit-block difference~~ | **RESOLVED and verified.** Recomputing the canonical key over the fit window gives exactly 372,213 rows: the 167-row gap is precisely the count of canonical-URL duplicates inside the window (exact-string dedup dropped 0). §3.7 now states this reconciliation explicitly instead of leaving it unverifiable. |
| ~~§5.2 single-script claim~~ | **RESOLVED.** §5.2 now carries a per-experiment map: E1–E5 by the evaluation pipeline notebook with the two split manifests as input; E4 by `run_temporal.py` + `design.json`; E7 by its executed notebook importing the Experiment 7 `src` package; E8 by `error_taxonomy.py`; E9 by `reverse_transfer.ipynb`. |
| ~~Table 5 estimand sentence placement in §2.6~~ | **RESOLVED by a different route.** Reordering the paragraph was unsafe (it spans eight runs), so the sentence now opens with an explicit back-reference — "Kembali ke perbandingan A1−A0:" — which removes the ambiguity the reviewer identified without moving nodes. |
| Author metadata | Reserved by the author; excluded from scoring by the brief. |

## 4. Verdict

The reviewer's five C7 items are now addressed as follows: item 2 (E9 mechanism claim) fixed, item 3 (protocol
equality) fixed, item 4 (Table 10 mapping and rounding) fixed, item 5 (integration contradictions: 85 fits,
Figure 1, determinism, vendor confound) fixed, item 1 (reconstruction dependencies) **substantially** closed by
adding the split manifests and Experiment 7 source, with the residual row-level reconciliation declared
unverifiable.

`IMPLEMENTATION COMPLETE — PENDING RE-REVIEW`
