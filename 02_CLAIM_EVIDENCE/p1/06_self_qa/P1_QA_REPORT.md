# P1 Self-QA Report

Date: 2026-11-01
Candidate: `phishing/BITS_Draft_Phishing_URL_Leakage_v10_P1_candidate.docx`
Candidate SHA-256: `5595d765471af00f1374a570c8519c60640ebea0e85bcce463fd8461e3106be6`
Baseline: `BITS_Draft_Phishing_URL_Leakage_v9_P0.docx`, SHA-256 `16478b6e2844dfcaa5c1599238d18dab37b943be12963c3565a15168512362ec` (unchanged)

## 1. Gate summary

| Gate | Verdict | Basis |
|---|---|---|
| G0 Baseline integrity | **PASS** | v9_P0 hash matches the published record before and after the build; v8_final and v9_P0 were opened read-only; all new files are confined to `revision_v10_p1/`, the candidate DOCX and the new package folder |
| G1 P0 regression | **PASS** | 16/16 semantic checks (`P0_REGRESSION_MATRIX.csv`); no A01–A12 criterion regressed |
| G2 Figure, metadata, visual | **PASS** | no "ceiling effect" in SVG, PNG, embedded media, OOXML or prose; metadata current; 15 pages inspected |
| G3 A13 package | **PASS (declared gaps)** | manifest covers every file; 161 files hash-verified; omissions enumerated |
| G4 A16 references/novelty | **PASS** | 24 sources, all verified; 91.7 % within 10 years; 87.5 % primary; no SOTA or superiority claim |
| G5 A14/A15 conditional | **PASS** | A14 `PARTIAL`, A15 `NOT RECOVERED`; both recorded without strengthening the manuscript |
| G6 DOCX/package health | **PASS** | ZIP clean, 27 package members, relationships verified, two builds semantically identical |
| G7 Scientific consistency | **PASS** | no metric changed; terminology consistent; ID/EN abstracts untouched and mutually consistent |
| G8 Handoff | **PASS** | `07_handoff/FINAL_HANDOFF_TO_CODEX.md` complete and requests review |
| G9 Dual independent review | **BLOCK** | Final round: `gpt-6-luna` BLOCK (C1–C5 PASS; C6/C7 block on disclosed provenance/cohort limits and user-owned repository+metadata), `glm-5-3-flash` APPROVE. Gate requires both to approve. See `dual_review/DUAL_REVIEW_REPORT.md`. |

## 2. Structural checks (`QA_CHECKS.json`, 24/24 PASS)

| Check | Result |
|---|---|
| Paragraphs | v9 = 181, v10 = 207 (+26: 2 headings, 7 added paragraphs, 12 references, 3 captions, 1 lead-in, 1 appendix intro) |
| Tables / inline shapes / sections / styles | 11 / 2 / 1 / 83 — Tabel 10 and Tabel A1 added |
| Table captions | 9 captions for 9 tables, ascending 1..9 |
| In-text table references | all resolve to an existing caption |
| Reference list | 24 entries, contiguous 1..24, none dangling, none uncited |
| Prohibited wording | 0 affirmative occurrences (negated corrective statements excluded by sentence-level check) |
| Figure 1 raster | replaced (`bf7befe2…`); no v8 filename token remains in `word/document.xml` |
| Package members | 27 in both v9 and v10 |
| Core properties | title/subject/description current; no v8 marker |

## 3. P0 regression (`P0_REGRESSION_MATRIX.csv`, 16/16 PASS)

A01 class semantics · A02 descriptive saturation · A03 seed 42 vs seed 13 · A04 no unverified cluster CI ·
A05 no blind/prospective claim · A06 truthful availability statement · A07 DROP_COLS · A08 85 = selected fits ·
A09 no leakage proof · A10 bounded verifier claim · A11 A2 contract ≠ equality · A12 provenance unknown —
plus four cross-cutting checks (Table 6 caption names both seeds; zero-shot ≠ temporal refit; no SOTA; two-corpus limit).

Note: A03's in-text pointer to the temporal-CI table moved from "Tabel 5" to "Tabel 6" because of the table
renumbering. The semantic criterion (seed 42 named separately from model seed 13) is unchanged and verified.

## 4. Rendering and visual QA

| Item | Value |
|---|---|
| Renderer | Microsoft Word (COM), `SaveAs2(FileFormat=17)` |
| Pages | **14** (v9_P0: 12) |
| Words | 9 833 |
| Page images | `06_self_qa/pages/page_01..13.png` |
| Inspected pages | 1, 2, 4, 5, 10, 13 (full-resolution visual review) |
| Findings | Figure 1 legible and carries the corrected wording; Table 1 fits with 11 rows; Table 2 caption correctly placed; Figure 2 and Table 9 both fit on page 10; references [12]–[24] complete and ordered |

No clipped text, no missing table or figure, no overflow, no unexpected blank page. Whitespace at the end of the
last page is normal document termination and was not "fixed" by compressing the paper.

## 5. Two-build reproducibility (`TWO_BUILD_COMPARISON.json`)

| Property | Result |
|---|---|
| Byte-identical builds | **No** (ZIP container timestamps differ) |
| Package members identical | Yes (27 members in both) |
| Media identical | Yes (all four media parts) |
| Semantic text identical | Yes (`9df7d4a2…`) |
| Paragraphs / tables | 200 / 9 in both |
| Delivered candidate equivalent to a fresh build | Yes for text, members and media |

This matches the G6 allowance: two builds must be "semantically and package-member equivalent, allowing only
documented container timestamp differences". The `docProps/app.xml` Pages/Words refresh is now part of the builder
itself (registered as P1-019), so a rebuild carries the same statistics; `render_candidate.py` re-measures them and
would overwrite the constants if the content changed.

## 6. Experiment and notebook disclosure

- **No model was trained, refitted, or re-evaluated in P1.** No new dataset was added. No new interval was computed.
- No notebook was executed or modified. The notebooks in the package are the previously executed ones, with their
  original execution counts; none is claimed to have been re-run.
- The only computations performed in P1 were document-level: hashing, structural extraction, Word statistics,
  PDF rendering, and bibliographic metadata retrieval.

## 7. Known limitations carried forward

1. A0/A1 producer provenance remains `UNKNOWN` (A14 `PARTIAL`: the fields are vendor-distributed, nothing more).
2. E8 cluster uncertainty remains unverified and the interval stays removed (A15 `NOT RECOVERED`).
3. The temporal cohort is not blind or prospective; this is stated in the manuscript and unchanged.
4. Figure 2's plotting script is workspace-only; the figure is regenerable from included evidence.
5. Author identity, affiliation, CRediT, funding confirmation, and the journal/volume/DOI furniture are user inputs.
6. The known `docx_validate.py` nondeterminism was not used as a gate; relationship health was checked with
   `verify_package_relationships.py` (`{"ok": true, "issues": []}`).

## 8. Verdict

`IMPLEMENTATION COMPLETE — PENDING CODEX REVIEW`

The candidate is not submission-ready and is not described as final. Two gates remain open:

1. **Dual independent review: BLOCK.** `glm-5-3-flash` approved in rounds 3, 4 and 5. `gpt-6-luna` passed
   C1–C5 in the final round and blocks only C6/C7, on (i) A0/A1 provenance remaining unknown, (ii) no public
   repository URL, (iii) the temporal cohort having been previously inspected, (iv) residual split detail, and
   (v) one-direction external validity. Items (i), (iii) and (v) are disclosed limitations that cannot be
   removed without a new prospective cohort or producer data — both outside this paper's authorised scope;
   (ii) is the user's decision; (iv) is partly addressed by the new configuration paragraph. Details and the
   full round history: `dual_review/DUAL_REVIEW_REPORT.md`.
2. **Codex review** has not yet been performed.

Three substantive defects were found by the dual review and fixed in this revision:

- Table 6 and Table 8 describe different models (full pre-cutoff training block vs fit-block-only retraining)
  on the same 168,035 test rows; both were numerically correct but the manuscript did not say so (P1-021…P1-024).
- The timing claim ("single-digit to teens of seconds") did not match the artifacts (6,06–7,21 s fit;
  0,79–0,84 s batch prediction) and was corrected, with its source named (P1-027).
- The threshold sentence attributed a cost-based thresholding view to [21]/[22], which support the base-rate
  argument and the precision-recall position respectively; the attribution was corrected (P1-012).

Additionally: Tabel 10 now maps every prose-only figure to its source artifact (P1-029), a configuration
paragraph records hyperparameters and library versions (P1-028), and the AUC reporting precision is stated
(P1-030).