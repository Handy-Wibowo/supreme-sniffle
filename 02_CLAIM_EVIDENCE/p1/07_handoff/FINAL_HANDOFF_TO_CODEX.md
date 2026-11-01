# Final Handoff to Codex

## 1. Candidate identity

- Candidate path: `E:\Kuliah\Tugas Akhir\phishing\BITS_Draft_Phishing_URL_Leakage_v10_P1_candidate.docx`
- SHA-256: `31dc1c21b3ea11ce2f8711129f859455c9ec18c6b2521913b2953af8717cf6a0`
- Source path: `E:\Kuliah\Tugas Akhir\phishing\BITS_Draft_Phishing_URL_Leakage_v9_P0.docx`
- Source SHA-256: `16478b6e2844dfcaa5c1599238d18dab37b943be12963c3565a15168512362ec` (unchanged; verified before and after the build)
- Build script: `phishing/revision_v10_p1/05_integrated_manuscript/apply_p1_revisions.py`
- Build date/time: 2026-11-01, Asia/Jakarta (UTC+07:00)

## 2. Executive verdict

- Figure/metadata/layout: **PASS** — Figure 1 raster and SVG de-staled, picture name de-versioned, docProps corrected, table numbering normalised
- A13 package: **PASS (two declared gaps)** — 161 files, every file hashed, omissions enumerated
- A16 literature/novelty: **PASS** — 24 verified sources, 91.7 % within 10 years, 87.5 % primary, design comparison table added
- A14 provenance: **PARTIAL** — fields confirmed vendor-distributed; four unknowns remain `UNKNOWN`; no manuscript change
- A15 interval evidence: **NOT RECOVERED** — no cluster computation exists; interval stays removed
- Integration: **PASS** — 51 registered changes, deterministic, locator-asserted
- P0 regression: **PASS** — 16/16
- Visual QA: **PASS** — 15 pages rendered, 6 pages inspected at full resolution
- Dual independent review: **BLOCK** — `glm-5-3-flash` APPROVE (rounds 3–5); `gpt-6-luna` BLOCK (C1–C5 PASS, C6/C7 block on disclosed limits and user-owned metadata)
- Overall: `IMPLEMENTATION COMPLETE — PENDING CODEX REVIEW` (dual-review gate not cleared)

## 3. Exact changes

Row-level detail: `05_integrated_manuscript/CHANGE_REGISTER.csv` (51 rows). In brief:

- **A02 residual:** `word/media/image3.png` replaced with `figure_1_research_pipeline_v10.png`; the only wording change in the SVG is `ceiling effect, paired domain bootstrap,` → `saturasi benchmark, bootstrap domain berpasangan,`, proven to be the sole change by round-trip substitution.
- **Metadata:** `dc:title` de-versioned and aligned to the candidate title; `dc:subject` and `dc:description` corrected; `wp:docPr` name/title de-versioned; `docProps/app.xml` Pages/Words `4/1998` → `14/9300`.
- **A16 content:** two sentences added to §1 ¶1 and ¶2; a new §1.2 (heading + 5 paragraphs); Table 1 replaced (6 → 11 rows, design-oriented columns, new caption and intro); three sentences added in §2.6, §3.6, §3.8; reference [12] page range added; references [13]–[24] appended.
- **Table numbering:** the feature-configuration table (previously unnumbered, uncaptioned, uncited) became Table 2; `Tabel 2..8` → `Tabel 3..9` in 8 captions and 8 in-text references.
- **A13:** §5.2 availability paragraph replaced so it describes the actual package.
- **Dual-review fixes:** Table 6/Table 8 model provenance (P1-021…P1-024); timing values corrected from artifacts (P1-027); configuration paragraph with hyperparameters, library versions and PSL hash (P1-028); Tabel 10 traceability table (P1-029); AUC reporting precision (P1-030); threshold-literature attribution corrected (P1-012).

## 4. P0 regression results

All 16 checks PASS (`06_self_qa/P0_REGRESSION_MATRIX.csv`, one row per criterion with the exact substring evidence).

A01 class semantics · A02 descriptive saturation · A03 seed 42 vs model seed 13 · A04 no unverified cluster CI ·
A05 no blind/prospective claim · A06 truthful availability · A07 DROP_COLS · A08 85 = selected fits ·
A09 no leakage proof · A10 bounded verifier claim · A11 A2 contract ≠ value equality · A12 provenance unknown ·
plus 4 cross-cutting checks.

Changed locators caused by insertions (for Codex's own checks):

| Action | Locator in v9_P0 | Locator in v10 |
|---|---|---|
| A12 provenance paragraph | ¶54 | ¶54 (before the insertion point, unchanged) |
| A03 "Tabel 5" seed pointer | ¶60 | ¶60, now reads "Tabel 6" (renumbering) |
| A04 conclusion | ¶134 | ¶134 (unchanged; insertion is at ¶22) |
| A06/§5.2 | ¶157 | ¶157, content replaced by A13 |
| Figure 1 caption | ¶119 | ¶119 (unchanged) |

## 5. Evidence and reference status

- **Added references (12):** [13] TESSERACT · [14] Transcend · [15] Barbero et al. · [16] Safi & Singh · [17] Karim et al. · [18] Gupta et al. · [19] Sánchez-Paniagua et al. · [20] Aljofey et al. · [21] Axelsson · [22] Saito & Rehmsmeier · [23] Trad & Chehab · [24] Ahamed et al.
- **Corrected references (1):** [12] pages `pp. 1153–1163` added.
- **Removed/unverified references:** none. All 24 resolve to a primary record (DOI via OpenAlex/Crossref, USENIX BibTeX, or the arXiv API). Access date 2026-11-01.
- **Official journal requirements checked:** none as a submission target — the user confirmed BITS is a template only and that journal grade is not the objective. Accreditation **substance indicators** (reference recency > 80 %, primary-source share > 80 %) were checked against the SINTA FAQ, Permenristekdikti 9/2018, and an Arjuna instrument summary; the instrument itself is a secondary rendering and no score is claimed.
- **Remaining bibliographic uncertainty:** [2] is a preprint with a v2 (2026-02-11); it is cited as 2025 (v1). [3] and [5] are USENIX papers without DOI, cited with official URLs.

## 6. Reviewer package status

- Package path: `E:\Kuliah\Tugas Akhir\phishing\AI_Review_SINTA2_Package_v10_candidate`
- Manifest: `MANIFEST.csv` (161 rows) + `MANIFEST.sha256`; `sha256sum -c` verified all files OK
- Included categories: candidate DOCX + render; Stage-1 audit (67 files); P0 QA and change log; P1 registers, ledgers and QA; E1–E5 pipeline; E4 paired bootstrap (Table 5 source); E6/E7/E8 executed notebooks and metrics; canonical temporal run artefacts and scripts; environment record; limitations
- Workspace-only items: v9_P0 baseline manuscript; v8 independent review prose
- Missing/omitted items: raw corpora (`OMITTED_LICENSE_PRIVACY`, provider pointers given); model binaries, per-row predictions and full splits (`OMITTED_SIZE`, regeneration route given); generated caches (`NOT_REQUIRED`)
- Clean-package test outcome: read-back and hash verification passed; the package is **not** claimed to be clean-room reproducible and says so in its README

## 7. A14/A15 disposition

- **A14 `PARTIAL`.** Recovered: `TLDLegitimateProb`, `URLCharProb`, `CharContinuationRate` are columns of the public PhiUSIIL CSV (the distribution ships no code, data dictionary, reference population, timestamp or label-dependency statement). Not recovered: producer script, reference population, computation time, label dependency, fitting scope. The manuscript's "belum diketahui" limitation is retained unchanged; no edit was made because none of the four listed unknowns was resolved.
- **A15 `NOT RECOVERED`.** No cluster-level resampling code exists in `Exp8_Error_Taxonomy`, the canonical temporal run, or anywhere in the workspace. The interval remains removed and cluster uncertainty remains labelled unverified. No new computation was attempted.

## 8. Tests and commands

| Command | Working directory | Exit | Outcome | Log |
|---|---|---:|---|---|
| `python apply_p0_revisions.py --verify-only` | `phishing/revision_v9_p0/04_integrated_manuscript` | 0 | `PASS`; 181/9/2/1; 57 applied rows; package_check true | `06_self_qa/QA_CHECKS.json` |
| `python verify_package_relationships.py …v9_P0.docx` | same | 0 | `{"ok": true, "issues": []}` | `00_intake/baseline.json` |
| `python apply_p1_revisions.py` | `phishing/revision_v10_p1/05_integrated_manuscript` | 0 | 19 changes registered; candidate written | `CHANGE_REGISTER.csv`, `change_log.json` |
| `python apply_p1_revisions.py --verify-only` | same | 0 | 207 ¶ / 11 tables / 2 shapes; no "ceiling effect"; 24 refs | printed JSON |
| `python qa_structure.py` | `phishing/revision_v10_p1/06_self_qa` | 0 | 24/24 PASS | `QA_CHECKS.json` |
| `python regression_p0.py` | same | 0 | 16/16 PASS | `P0_REGRESSION_MATRIX.csv` |
| `python two_build_test.py` | same | 0 | two builds from v9_P0: package members, media and semantic text identical; bytes differ only by ZIP container timestamps (G6 allowance) | `TWO_BUILD_COMPARISON.json` |
| `python render_candidate.py` | same | 0 | 15 pages, 10 076 words; 13 page PNGs | `RENDER_LOG.json` |
| `python verify_package_relationships.py …v10_P1_candidate.docx` | `phishing/revision_v9_p0/04_integrated_manuscript` | 0 | `{"ok": true, "issues": []}` | printed JSON |
| `sha256sum -c MANIFEST.sha256` | package root | 0 | all files OK | `MANIFEST.sha256` |

## 9. Structural and visual QA

- Paragraphs 181 → 207; tables 11; inline figures 2; sections 1; styles 83; package members 27 (unchanged set except `word/document.xml`, `word/media/image3.png`, `docProps/core.xml`, `docProps/app.xml`).
- ZIP integrity clean; relationship check `ok: true` with zero issues on both v9_P0 and the candidate.
- Renderer: Microsoft Word 16 via COM, `SaveAs2(FileFormat=17)`.
- Rendered page count: **13** (v9_P0: 12).
- Pages inspected at full resolution: 1, 2, 4, 5, 10, 13 (all 13 page images retained).
- Visual findings: Figure 1 legible with the corrected wording; Table 1 fits with 11 rows; Table 2 caption correctly placed above the configuration table; Figure 2 and Table 9 both fit on page 10; references [12]–[24] complete and ordered; no clipping, overflow, missing content, or unexpected blank page.

## 10. Notebook and experiment disclosure

- New experiments run: **no**
- Models trained/refit: **no**
- Datasets added/changed: **no**
- Notebooks created/modified: **none**
- Notebook execution history retained: **not applicable** (no notebook touched; packaged notebooks keep their original execution counts)

## 11. Known limitations and user decisions needed

1. Author names, affiliations, emails, CRediT, funding confirmation and the AI-disclosure wording are placeholders the user said they will fill in later. Nothing was invented.
2. Target journal is undecided; journal-fit claims are intentionally absent and the BITS header furniture (`Volume 99, No 99`, `DOI 10.47065/bits.v9i9.999`) is untouched.
3. A0/A1 provenance remains `UNKNOWN`; E8 cluster uncertainty remains unverified.
4. The temporal cohort is not blind or prospective (stated in the manuscript).
5. Figure 2's plotting script is workspace-only; the figure is regenerable from included evidence.
6. Citation numbering is thematic, not order-of-appearance — a pre-existing v9_P0 convention preserved deliberately.
7. `docx_validate.py` is nondeterministic for this document and was not used as a gate (documented defect).

## 12. Files created or modified

Created under `phishing/revision_v10_p1/`:

- `00_intake/` — `baseline_intake.py`, `baseline.json`, `BASELINE.md`
- `01_figure_metadata_layout/` — `fix_figure_1.py`, `figure_1_research_pipeline_v10.svg`, `figure_1_research_pipeline_v10.png`, `figure_1_research_pipeline_v8_ORIGINAL.png`, `figure_1_wording_diff.txt`, `REPORT.md`, `_probe_crop.png`, `_probe_full_1x.png`
- `02_package_A13/` — `build_package.py`, `CLAIM_TO_FILE_MAP.csv`, `A13_REPORT.md`, `PACKAGE_MANIFEST.csv`
- `03_literature_A16/` — `fetch_crossref.py`, `fetch_biblio.py`, `fetch_abstracts.py`, `build_ledger.py`, `crossref_metadata.json`, `biblio_metadata.json`, `abstracts.json`, `SOURCE_LEDGER.csv`, `CURRENT_REFERENCE_AUDIT.csv`, `NOVELTY_CLAIM_MAP.csv`, `RELATED_WORK_MATRIX.md`, `A16_REPORT.md`
- `04_provenance_A14_A15/` — `REPORT.md`, `SEARCH_LOG.md`, `A14_PROVENANCE_LEDGER.csv`, `A15_INTERVAL_EVIDENCE.csv`
- `05_integrated_manuscript/` — `apply_p1_revisions.py`, `CHANGE_REGISTER.csv`, `change_log.json`, `INTEGRATION_REPORT.md`
- `06_self_qa/` — `qa_structure.py`, `regression_p0.py`, `two_build_test.py`, `render_candidate.py`, `QA_CHECKS.json`, `P0_REGRESSION_MATRIX.csv`, `TWO_BUILD_COMPARISON.json`, `RENDER_LOG.json`, `P1_QA_REPORT.md`, `rendered_candidate.pdf`, `pages/page_01..13.png`
- `07_handoff/FINAL_HANDOFF_TO_CODEX.md` (this file)

Created outside that tree:

- `phishing/BITS_Draft_Phishing_URL_Leakage_v10_P1_candidate.docx`
- `phishing/AI_Review_SINTA2_Package_v10_candidate/` (161 files + manifest)

Modified: none. `v8_final`, `v9_P0`, `revision_v9_p0`, `revision_v9_stage1_audit`, `AI_Review_SINTA2_Package_v8`, the experiment folders and the handed-off copy tree were all opened read-only.

## 12b. Documented deviation from the handoff write scope

Handoff §6 requires new files to be confined to `revision_v10_p1/`, the candidate DOCX and a new
reviewer-package folder. One additional tree was created at the author's explicit instruction:

- `Experiment/9 - Reverse Transfer PhreshPhish to PhiUSIIL/` — the reverse-transfer experiment
  (executed notebook, README, RESULTS, run outputs). Authorised in chat; it adds a new claim to the
  manuscript, so it is recorded here rather than left implicit. No existing experiment folder was modified.

Also outside the original scope, by author decision: the public archive at
`https://github.com/Handy-Wibowo/supreme-sniffle` (Zenodo concept DOI `10.5281/zenodo.23847784`).

## 13. Requested independent Codex checks

1. Re-hash the candidate and confirm `b9c39091…1f66196`; re-hash v9_P0 and confirm `16478b6e…` unchanged.
2. Re-run `apply_p1_revisions.py` from v9_P0 into a scratch location and confirm semantic/package-member equivalence with the delivered candidate.
3. Re-run `verify_package_relationships.py` on the candidate; confirm 27 members and `ok: true`.
4. Spot-check at least 6 rows of `CHANGE_REGISTER.csv` against the DOCX text, including P1-005 (Table 1), P1-006 (§1.2), P1-013 (table renumbering) and P1-015 (§5.2).
5. Re-verify P0 regression independently: at minimum A01, A03 (with the Tabel 5→6 pointer change), A05, and A11.
6. Sample 5 rows of `SOURCE_LEDGER.csv` and resolve each DOI/official URL independently; confirm no "ceiling effect" in `word/media/image3.png`.
7. Sample `MANIFEST.csv` rows, recompute their SHA-256, and confirm the omissions in `OMITTED_ARTIFACTS.csv` are genuinely absent from the package.
8. Inspect the rendered pages, especially 2 (Table 1), 4 (Figure 1), 5 (Table 2 caption) and 13 (references).

**This candidate has not been accepted as final or submission-ready. Independent Codex review is required.**