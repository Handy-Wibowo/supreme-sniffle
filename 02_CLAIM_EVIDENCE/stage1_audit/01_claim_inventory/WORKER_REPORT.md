# Stage-1 Evidence Audit — Worker Report

## Executive verdict

**Not fully evidence-clean.** Local primary artifacts substantiate the principal final benchmark, temporal point metrics, zero-shot transfer, threshold outcomes and selected taxonomy counts. The critical exception is Table 5 inferential provenance: reported temporal confidence limits match an E5 bootstrap run whose RNG seed is 42, while §2.6 states seed 13; E4's seed-13 intervals are different. Other blockers: the generated E1 leakage report reverses four keep/drop labels; the wide E8 platform-cluster interval lacks a located primary computation file; and the review package omits E1-E5 and numerous source/prediction artifacts despite §5.2 availability wording. The manuscript generally limits causal/SOTA interpretations correctly.

## Deliverables written

- CLAIM_EVIDENCE_MATRIX.csv — 73 structured claims; artifact paths, table/field/code location, verification method, status and caveat.
- CLAIM_EVIDENCE_MATRIX.md — same rows in reviewable form.
- ARTIFACT_INVENTORY.md — required/present/missing E1-E8 artifacts, review-package coverage and selected hashes.
- WORKER_REPORT.md — this summary and exact checks.

Only these files were written, inside phishing/revision_v9_stage1_audit/01_claim_inventory/. No manuscript, experiment source or prior evidence was edited. No notebook was created.

## Coverage

Manuscript inspected directly. Structure check found 180 body paragraphs, 9 DOCX tables and 2 figures. Matrix covers all RQ1-RQ5, abstract/conclusion, all result tables and the uncaptained feature configuration table, both figures, data/method claims, every material numerical result, novelty boundaries, ceiling effect, transfer, threshold and error-taxonomy claims.

## Findings

- E1 raw/clean sizes, AUCs, deduplication, domain statistics and split evidence reproduce; its generated report has a keep/drop verdict defect inconsistent with its code and cleaned parquet.
- E5 is the final A0/A1/A2 result source, and supports the benchmark means and paired A1−A0 bootstrap. E3.1 is legacy and differs in feature families and metric polarity.
- E4 temporal point metrics/cohort/month counts align. Table 5 CI values match E5 output but the stated bootstrap RNG seed is wrong (42 vs 13); E4's seed-13 CI differs.
- E6 saved predictions/metrics and independent check support transfer tables. Evidence is limited to tested dataset pair and does not isolate cause.
- E7 supports validation-only thresholds and test tradeoffs; validation caps are not guaranteed on test.
- E8 category table supports reported short URL/non-HTTPS/platform errors; overlap/confounding and prior test inspection limit interpretation. The cluster bootstrap interval is narrative-only in available E8 folder.
- Table 1 literature claims are outside the local E1-E8 primary-artifact boundary and are marked unverifiable here.

## Exact commands and checks exercised

1. Command: python -c "from docx import Document; p=r'E:\Kuliah\Tugas Akhir\phishing\BITS_Draft_Phishing_URL_Leakage_v8_final.docx'; d=Document(p); print('paragraphs',len(d.paragraphs),'tables',len(d.tables)); print('TABLES'); [print(i, len(t.rows), len(t.columns), repr(' | '.join(c.text.replace(chr(10),' ') for c in t.rows[0].cells)[:300])) for i,t in enumerate(d.tables)]; print('FIGURES',sum(1 for p in d.paragraphs for r in p.runs if r._element.xpath('.//w:drawing')))"
Observed: 180 paragraphs, 9 tables, 2 figures.
2. sha256sum over selected E1, E3, E4 repeat, E5, E6, E7, E8 and DOCX files. Actual hashes are recorded in ARTIFACT_INVENTORY.md. Manuscript hash 65c8909be07a17427a0367306d3c9502be27ee36705e92c2234d61fc6896ccf matches existing package verification record.
3. Direct inspection of manuscript DOCX text; E1 notebook cells/code/output and audit report; E5 final per-run/summary/paired bootstrap/summary manifest; E4 design, metrics, ledger, bootstrap; E6 metrics, manifest, row-level check and verifier code; E7 split/threshold/test/PPV artifacts and source; E8 table/code/execution status/README; package file index.
4. Independent inspection results supplied by direct source checks: chunked pandas scan of raw PhiUSIIL; direction-free single-column AUC recomputation; parquet duplicate/schema/null verification; split joins/domain isolation/exposure calculation; E5 final metric and paired bootstrap comparison; E6 260 metric checks; E7 validation freeze and test mapping; E8 confusion/category checks. No costly model/notebook rerun was performed.

## Unresolved blockers

- Correct Table 5 seed provenance or regenerate intervals under seed 13 and update manuscript limits.
- Correct E1 report verdict labels in a future evidence refresh; source edits were out of scope.
- Store E8 platform-cluster bootstrap code and machine-readable output or withdraw/relabel that estimate.
- Align §5.2 data-availability wording with package contents, or distribute the missing source artifacts.
- Record exact E1/E4 tldextract/PSL snapshot provenance if exact domain replication is intended.
- Clarify 85 as designated main fits, excluding the additional E5 temporal parity run.
- Independently verify external literature citations; not possible from listed local artifacts.
