# A14 / A15 — Conditional Provenance Investigation (read-only)

Date: 2026-11-01
Scope: read-only recovery of already-existing evidence. No experiment, refit, or new interval was computed.

## Verdicts

| Action | Verdict | Consequence for the manuscript |
|---|---|---|
| A14 — A0/A1 producer provenance | `PARTIAL` (one new fact; core remains unknown) | No manuscript change proposed; the "unknown" limitation in §2.4 (paragraph 54 in v9, unchanged in v10) stays correct and is now better documented. |
| A15 — E8 platform-cluster interval | `NOT RECOVERED` | No change. The interval stays removed and the uncertainty stays labelled unverified (P0 A04). |

## A14 — what was searched and what was found

Search scope: the dataset distribution, the cleaning notebook, the cleaned parquet, the leakage audit, the
Stage-1 provenance audit, and every repository file mentioning `TLDLegitimateProb`.

Findings:

1. The public PhiUSIIL distribution in this workspace is a single archive containing one file:
   `PhiUSIIL_Phishing_URL_Dataset.csv` (56,854,345 bytes). It ships **no** codebook, derivation script,
   reference-population description, computation timestamp, or label-dependency statement.
   Evidence: `dataset/PhiUSIIL Phishing/phiusiil+phishing+url+dataset.zip` (single member), CSV header enumerated below.
2. `TLDLegitimateProb`, `URLCharProb`, and `CharContinuationRate` are **columns of that distributed CSV**
   (positions 10, 11, and 9). They were therefore not computed by this project; they arrive with the
   dataset as delivered by its authors.
3. `Experiment/5 - PhiUSIIL Focused Ablation/src/data.py` lists `TLDLegitimateProb` and `URLCharProb` only as
   feature names in a schema list. It contains no computation of them.
4. No file in the workspace contains a producer script, a reference corpus for those statistics, a fitting
   timeframe, or evidence about whether labels entered their computation.

What this does and does not establish:

- Established: the two fields are vendor-distributed columns, not project-derived.
- Not established: the reference population, the computation date, whether labels were used, and the
  train/test fitting scope. These remain `UNKNOWN`.
- Therefore the manuscript statement "producer hulu, populasi referensi, waktu komputasi, dan ketergantungan
  terhadap label belum diketahui" remains accurate, and no strengthening is permitted.

Decision: no manuscript edit. Rationale: the recovered fact narrows *where* the values come from (the
distribution) but does not resolve any of the four unknowns that the paragraph lists. Editing A12's paragraph
to add provenance detail would create a P0-regression risk for no evidential gain.

## A15 — what was searched and what was found

Search scope: `AI_Review_SINTA2_Package_v8/03_Experiments/Exp8_Error_Taxonomy/`, the canonical temporal run,
`Experiment/3.1 - evaluation pipeline v2`, and a repository-wide grep for `cluster` in `*.py` / `*.ipynb` / `*.md`.

Findings:

1. The E8 folder contains `error_taxonomy.executed.ipynb`, `category_error_table.csv`, and
   `execution_status.json`. None of them contains cluster-level resampling code: a grep for `cluster`
   across those three files returns no hits.
2. No script in the workspace computes a platform-cluster interval. `revision_v9_stage1_audit` records the
   same absence.
3. The manuscript's post-P0 state already (a) removed the interval `[1,6%; 66,7%]`, (b) keeps the 37,1 %
   platform-host share as a descriptive, cohort-scoped number, and (c) marks cluster uncertainty as unverified.

Verdict: `NOT RECOVERED`. Restoring the interval is not possible without a defined cluster unit, saved
row-level inputs, a reproducible computation, seeds, and an output artifact — none of which exist. No new
computation was attempted, because that would require explicit authorisation and a written analysis plan.

## Files

- `SEARCH_LOG.md` — commands and paths examined.
- `A14_PROVENANCE_LEDGER.csv` — evidence items with locators.
- `A15_INTERVAL_EVIDENCE.csv` — required elements, each marked present/absent.