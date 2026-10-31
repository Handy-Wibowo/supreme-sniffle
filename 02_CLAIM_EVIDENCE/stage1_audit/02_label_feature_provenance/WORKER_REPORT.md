# Stage 1 audit report — labels and feature provenance

## Bottom line

Current E5–E8 label mapping and confusion-matrix semantics are consistent: phishing is class 1, benign class 0, probability column is selected for `classes_ == 1`, and `[0,1]` confusion flattening yields TN, FP, FN, TP. Current estimator fitting is separated by the designated train IDs; the A2 extractor has no target or cross-row fitting stage. This does **not** certify upstream provenance of A0/A1 stored features.

The old E3 evaluation notebook is not label-semantic safe: the source PhiUSIIL label is `phish=0, benign=1`; it uses sklearn default positive class 1, reports benign F1/precision/recall, calls benign→phish errors `fp`, and uses `predict_proba[:,1]` as if it were phish. Do not reuse E3 result-column names as phishing-positive metrics without recalculation.

A2 identity is **PASS for exact ordered 18-field contract and shared raw-URL extractor**; **FAIL if “identity” means same values/semantics as source precomputed names**. A direct source-agreement sample shows 0% exact agreement for three A2 fields and 6.555% for `DomainLength`. A2 versus A0 is therefore a representation contrast, not a one-factor ablation.

The historical exploratory TLD target-encoding probe demonstrates leakage in that probe (PhiUSIIL: all label values are used before split; PhreshPhish: original train labels are used before a subsequent resplit). The current production A0/A1 `TLDLegitimateProb` values come from the upstream cleaned corpus. The exact producer is absent, and direct recomputation showed 0/235,370 values equal the historical clean-table mean of `y_phish` by `TLDLength`. Thus: leakage is proven for legacy probe implementations but **not** proven for the current stored column. Current A0/A1 statistical-feature provenance remains an unresolved high risk; A2 excludes both `TLDLegitimateProb` and `URLCharProb`.

High separability is established, especially `LineOfCode` solo direction-free AUC 0.990283 and `NoOfExternalRef` 0.988033; both remain in A0 despite the E1 report table’s conflicting DROP recommendations. These AUCs, very high F1, and small A1–A0 contrast do not identify what caused the ceiling. **Causal ceiling-effect support: FAIL.** The evidence supports a descriptive corpus-level saturation/ceiling interpretation only.

## Acceptance conclusions

| Criterion | Result | What passes / remains open |
|---|---|---|
| Label integrity | **PASS with scope limit** | Current mapping, positive class, `predict_proba`, and confusion matrix align. Source labels are not independently adjudicated. Legacy E3 label semantics fail. |
| A2 identity | **PASS for contract; FAIL for source-value equivalence** | Shared ordered feature list/extractor verified; several same-named values differ from source. |
| Train/test isolation | **PASS for model fit and A2; upstream A0/A1 provenance UNKNOWN** | `.fit` receives train only; E6 target is prediction-only. Legacy probe TLD encoding leaks. E1 all-row AUC is descriptive whole-dataset screening. |
| Causal ceiling-effect support | **FAIL** | Feature AUCs show high separability, but no intervention/provenance chain identifies a causal ceiling mechanism. |

## A0/A1/A2 reconstruction

- **A0:** 47 precomputed PhiUSIIL columns (`LEXICAL + HOST + CONTENT`); includes page/content fields and the two high-separability `LineOfCode` / `NoOfExternalRef` values.
- **A1:** 41 A0 fields, removing exactly `LineOfCode`, `NoOfExternalRef`, `NoOfImage`, `NoOfSelfRef`, `NoOfJS`, `NoOfCSS`.
- **A2:** 18 deterministic per-row URL fields from `src/features.py`; no target encoding, language model, learned dictionary, label-based statistic, or page-content feature. It is a reimplementation, not necessarily the same definition as source columns.
- The full member-level matrix is `FEATURE_PROVENANCE_MATRIX.csv`. Each A0/A1 entry whose upstream producer was unavailable is labelled unknown rather than inferred from the field name.

## E1–E8 trace

`LABEL_FLOW.md` covers dataset schemas and E1 cleaning, E2 UCI, E3 legacy evaluation, E4 Phresh temporal, E5 current focused runner, and v8 Exp6–8 transfer/threshold/error taxonomy. E-labels here denote local numbered experiments; the v8 package’s `Exp6`/`Exp7`/`Exp8` are separate experiment identities, and older `phishing/ARBITRATION.md` E1–E11 is an unrelated evidence-index.

## Verification performed

- Read full raw PhiUSIIL CSV and current clean Parquet directly; confirmed row/column counts, source label distribution, cleaned distribution, and schemas.
- Read actual local Phresh train/test Parquet schemas. Inspected pipeline loaders, transforms, fit/predict calls, metrics implementation, manifests, source/output rows and manuscripts rather than relying on filenames or report text.
- Recomputed direction-free AUCs directly on all raw PhiUSIIL rows and compared `TLDLegitimateProb` against the exact full cleaned-data `mean(y_phish | TLDLength)` candidate formula.
- Executed the actual current A2 extractor on two representative URLs (HTTPS DNS hostname, and HTTP IP-literal with percent escape); confirmed ordered 18-field output.
- Inspected stored notebook run history: E4 (7/7 code cells, zero errors), E5 executed ablation (8/8, zero), package Exp6 (5/5, zero), Exp7 (8/8, zero), Exp8 (13/13, zero). This audit did not execute or rewrite any existing notebook.
- Direct output evidence and per-check observations are in `VERIFICATION_LOG.json`; no claim beyond exercised checks is made.

## What remains unknown / not claimed

1. The upstream producing code, fitting corpus, time of computation, and label dependency for precomputed `TLDLegitimateProb`, `URLCharProb`, `CharContinuationRate`, and content fields.
2. Whether `URLCharProb`’s character-probability reference was fitted from an independent corpus or included evaluated rows.
3. Whether each page-derived A0 field was extracted before or after labeling, or what page snapshot was captured.
4. Whether original source labels are independently correct; this audit traces mappings, not external ground truth.
5. Whether a single mechanism (domain reuse, content proxy, corpus collection, source-label process) caused near-ceiling PhiUSIIL results.
6. Generalization/causal effects beyond the executed pair/cohorts; no new experiments were run.

Only these deliverables were created, in the assigned output folder: `LABEL_FLOW.md`, `FEATURE_PROVENANCE_MATRIX.csv`, `LEAKAGE_RISK_REGISTER.md`, `VERIFICATION_LOG.json`, and this report. No source experiment, raw data, manuscript, or pre-existing evidence was edited.
