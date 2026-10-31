# P0_QA_REPORT — Independent acceptance review of `BITS_Draft_Phishing_URL_Leakage_v9_P0.docx`

- Date: 2026-10-28. Reviewer: QA worker (task_66113521e770), read-only on all inputs; writes confined to `revision_v9_p0/05_qa/`.
- Inputs: `phishing/BITS_Draft_Phishing_URL_Leakage_v8_final.docx` (source), `phishing/BITS_Draft_Phishing_URL_Leakage_v9_P0.docx` (output), `revision_v9_stage1_audit/05_stage1_gate/STAGE1_ACTION_REGISTER.csv` (P0 register), `revision_v9_p0/04_integrated_manuscript/*` (APPLIED_CHANGES.csv, INTEGRATION_REPORT.md, VALIDATOR_CORRECTION.md, apply_p0_revisions.py, verify_package_relationships.py, verification_summary.json), proposal folders `01_claim_language`, `02_methods_numbers`, `03_scope_availability`.
- Coordinator directive honored: `docx_validate.py` treated as known-nondeterministic; manuscript not failed on it; independent relationship verification performed.

## Verdict

**PASS — P0 scope.** All 12 P0 actions (A01–A12) verified semantically and by exact text; 57/57 applied rows and 5/5 absent dispositions in `APPLIED_CHANGES.csv` reconcile exactly against v8→v9 text; no contradictory residual echoes found; source and output hashes unchanged from the published build; package health confirmed by two independent checkers; rebuild reproducible at package-member level; rendered layout shows no corruption. Zero P0-blocking defects. Four non-blocking observations recorded below (one external tool defect, three cosmetic), none of which alter any A01–A12 disposition.

## 1. Hash preservation

| File | SHA-256 | Matches published record |
|---|---|---|
| v8_final (source) | `65c8909be07a17427a0367306d3c9502cbe27ee36705e92c2234d61fc6896ccf` | yes (INTEGRATION_REPORT/VALIDATOR_CORRECTION) |
| v9_P0 (output) | `16478b6e2844dfcaa5c1599238d18dab37b943be12963c3565a15168512362ec` | yes |

Both files verified read-only during QA (no writes; Word render ran on QA-folder copies only). Source log: `logs/hashes.txt`.

## 2. Package health and validator behavior

**Independent deterministic checker** (`verify_package_relationships.py`, run by QA on both files): `{"ok": true, "issues": []}`, exit 0 — v8: `logs/verify_rels_v8.txt`, v9: `logs/verify_rels_v9.txt`.

**Official `docx_validate.py`** swept under `PYTHONHASHSEED=0..9` by QA (raw logs `logs/docx_validate_seed*.json`, `logs/docx_validate_v8_seed*.json`):

| seed | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| v9_P0 | FAIL | ok | ok | FAIL | FAIL | FAIL | ok | FAIL | FAIL | ok |
| v8_final | FAIL | ok | ok | FAIL | FAIL | FAIL | ok | FAIL | FAIL | ok |

Identical pattern on both files (4/10 pass each in this QA sample, consistent with the documented ~1-in-3 collision probability). QA independently confirmed the defect mechanism is external to the package: QA's own relationship resolution — keyed by real source part, all five `.rels` files, every `r:id`/`r:embed`/`r:link` in `word/*.xml`, content-type coverage, dangling-target scan (`STRUCTURE_DIFF.json` → `resolution_issues_output`: empty; `logs/content_alignment.json` → `dangling_internal_targets`: empty) — finds **zero** unresolved references in v9_P0. All four media parts, styles, settings, header/footer relationships resolve. `python-docx` opens v9_P0 and reads 181 paragraphs, 9 tables, 2 inline shapes, 1 section, header/footer text, page setup (`logs/docx_openability.log`); zip integrity `testzip()` clean.

Conclusion: matches `VALIDATOR_CORRECTION.md`. The package is healthy; the shared validator has a header/footer relationship-map key collision. Advisory (not a manuscript defect): any future gate must not trust a single `docx_validate.py` exit code on documents with `word/_rels/header1.xml.rels`; use multi-seed runs or `verify_package_relationships.py`.

## 3. Structure diff source → output (see `STRUCTURE_DIFF.json`)

| Aspect | Source (v8_final) | Output (v9_P0) | Verdict |
|---|---|---|---|
| Package members | 27 | 27 | identical set; **only `word/document.xml` changed** |
| Relationships | 24 across 5 `.rels` | identical | byte-equal |
| Body paragraphs | 180 | 181 | exactly one insertion: A12 provenance paragraph, output index 54, style Normal, after A2 paragraph (source P0053), before §2.5 |
| Tables | 9 (shapes 4x4, 4x5, 8x6, 5x9, 5x4, 6x8, 5x9, 6x4, 3x8) | 9, same shapes | all cell text identical except 3 recorded REPLACE_CELL edits |
| Styles | 83 | 83 | identical list |
| Inline figures | 2 | 2 | media part hashes unchanged (image1–image4 all byte-equal) |
| Sections | 1 | 1 | page size/margins/header/footer text identical |
| Citations `[n]` | 44 occurrences, 12 distinct | 44 occurrences, 12 distinct | **sequence identical** (paragraphs + table cells + header/footer) |
| Changed paragraphs | — | 39 | all map 1:1 to APPLIED_CHANGES rows (see §4) |

The single insertion is proven by exact-text mapping (`logs/row_text_map.json`): the INSERT row's after-text exists only in v9 at paragraph 54, and every APPLIED_CHANGES location ≥P0058 shifts +1 versus output index (19 rows offset 0, 34 rows offset 1; CSV P-numbers are source indices). difflib folds the insertion into the adjacent replace opcode; the naive block count is therefore 39 "changed", which reconciles to 39 distinct edited source paragraphs + 1 insertion with zero deletions and zero reorderings.

## 4. APPLIED_CHANGES.csv row-level verification

- 62 disposition rows total: **57 applied, 5 absent** (A01, A04, A09, A10, A11 each contribute one absent full-document search row). Matches INTEGRATION_REPORT and `--verify-only` output.
- All 57 applied REPLACE rows: `before` text present in v8 and absent in v9; `after` text present in v9 — exact string equality, 0 failures (`logs/A01_A12_probes.json` → `row_checks`).
- All 3 REPLACE_CELL rows match the 3 table-cell diffs by exact before/after values: T2 "A2 source" cell (A11), T5 precision lower bound `0,895661→0,895662` (A03; python-docx coordinates T6R4C3 due to merged-cell enumeration; manuscript label T5R3C2), T8 platform-FN cell (A04; manuscript label T8R1C6, python-docx T9R2C7).
- The INSERT row (A12) maps to output paragraph 54.
- `apply_p0_revisions.py --verify-only` re-run by QA on the published artifact: `PASS`, 181/9/2/1, 12 actions, 57/5 rows, source+output hashes unchanged, package check true (`logs/verify_only_run.log`).

## 5. A01–A12 acceptance matrix

Full detail: `P0_QA_MATRIX.csv` (one row per action: criterion, PASS/FAIL, evidence, exact-text checks, residual findings).

| Action | Criterion (register) | Verdict | Key evidence (v9 output) |
|---|---|---|---|
| A01 | E3 excluded/relabeled; E5–E8 mapping correct | **PASS** | Output ¶40 states source polarity (legitim=1: 134,850 / phishing=0: 100,945); ¶58 states current mapping (legitim=0/phishing=1) + explicit sentence that legacy E3 metrics are not used as phishing-positive |
| A02 | No causal mechanism asserted | **PASS** | ID/EN titles, both keyword lists, both abstracts use "saturasi benchmark"/"benchmark saturation"; "ceiling effect" 5→0 occurrences in prose; ¶119 figure caption and ¶125/¶131 deny causal mechanism; no `kausal…saturasi` claims |
| A03 | Bootstrap RNG seed 42 ≠ model seed 13 | **PASS** | ¶57: temporal bootstrap = RNG seed 42 applied to model-seed-13 predictions, "angka 13 pada Tabel 5 menandai seed model, bukan seed RNG bootstrap"; Table 5 caption names model+unit+replicates+RNG seed; ¶62 names E6 RNG seed 42 over 65,288 domains; T5 value rounded 0,895662; legacy caption/truncated value absent |
| A04 | Unverified cluster CI absent or qualified | **PASS** | Legacy inferential CI `[1,6%; 66,7%]` removed (v9=0, v8=1); error-category cell marked "ketidakpastian klaster tidak terverifikasi"; conclusion ¶134: cluster uncertainty not reproducibly quantified, not used inferentially; 37,1% kept descriptive (4 occurrences, all cohort-scoped) |
| A05 | No blind/prospective description of extant test | **PASS** | 4 corrective statements "telah diperiksa dalam pekerjaan eksploratif sebelumnya … bukan holdout buta atau prospektif" (ID abstract, EN abstract, ¶21, ¶65); legacy frozen-cohort implication removed; "prospektif" only in future-work requirements |
| A06 | §5.2 matches package tree; package ≠ workspace | **PASS** | ¶155: 22 declared files (19 artifact copies + 3 guides) by category, 2 unlisted directory items, explicit omission list (raw data, splits, trained models, per-row predictions, implementation source, E1–E5 outputs); cross-checked against `03_scope_availability/PACKAGE_INVENTORY.md` (24 on-disk = 22 declared + 2 undeclared) — consistent |
| A07 | DROP_COLS account consistent; retained fields identified | **PASS** | ¶40: exact four DROP_COLS named, FILENAME marked collection artifact; retained LineOfCode/NoOfExternalRef stated (4 occurrences each, unchanged from v8 as intended); AUC-does-not-prove-derivation caveat added |
| A08 | 85 = selected fits, excluding parity rerun; E3 = stub/dry run | **PASS** | ¶33: "85 kecocokan terpilih", excludes 10-fit parity rerun + pre-flight/smoke runs, E3 branch "stub/uji kering" with aggregate-only output; ¶92 bounds timing to reported fits; residual "85" hits are the qualified count ×2 and unrelated "TN=85.629" |
| A09 | Overlap bounded; no leakage/inflation proof; confounds noted | **PASS** | ¶45: shared-hosting clusters not evidence of same campaign/operator; ¶46: 62.0%/2.6% asymmetry descriptive, label-provenance reading explicitly labeled inference; ¶84: site-disjoint excludes shared registrable-domain key only, "tidak … menyingkirkan semua bentuk tumpang tindih"; no strict no-overlap metrics added (consistent with absent disposition) |
| A10 | Side-effect statement bounded to manifest fields checked | **PASS** | No side-effect/no-write/pre-run-bytes claims anywhere (regex v9=0); ¶62 keeps artifact-bound wording for the specific output-manifest fields checked (feature order, threshold); package inventory (¶155) describes contents, no verifier claims |
| A11 | A2 = URL-only representation, shared contract | **PASS** | ¶53: shared ordered 18-feature raw-URL extractor contract; ¶95: A2−A0 reported as representation contrast, not "efek 29 fitur"; Table 2 A2-source cell: recomputed per URL, "tidak menyalin nilai sumber yang telah dihitung sebelumnya"; legacy "ekstraktor terpisah"/"subhimpunan" phrasing absent |
| A12 | No target-encoded / leakage-free assertion for stored fields | **PASS** | Inserted ¶54: upstream producer, reference population, computation time, label dependency "belum diketahui"; historical target-encoding proof limited to probe implementations; current fitting "tidak mensertifikasi provenance fitur hulu sebagai bebas kebocoran"; only regex hits for target-encoded/leakage-free are these denials |

## 6. Residual echo / contradiction scan

Systematic battery over full v9 text (paragraphs + all table cells + header/footer; `echo_scan.py`, log `logs/echo_scan_run.log`): 85, seed 13, ceiling, dibekukan, E3, class counts, 37,1, 47 fitur, holdout, cluster CI, 0,0002-only phrasing, target-encoded, leakage-free, SOTA, zero-day, deployment, bootstrap counts, T5 bound value, Tabel 9, Gambar refs. **No contradictory echoes.** Every hit is either a corrective denial (e.g., "bukan holdout buta", "tidak … terverifikasi", "tidak menunjukkan bahwa label diturunkan dari identitas domain"), a legitimate technical usage (frozen pipeline/thresholds, model seed 13 identifiers), or an explicitly scoped number. The old causal/saturation, blind-cohort, E3-metric, cluster-CI, seed-conflation, and A2-equality narratives are absent from prose.

## 7. Reproducibility (QA temporary outputs only)

Two independent builds into `05_qa/repro/det1.docx`, `det2.docx` (`logs/repro1.log`, `repro2.log`): both exit 0, both self-verify. Package-member comparison against the published file (`logs/repro_member_compare.log`): **27/27 members byte-identical across all three files**; whole-file SHA-256 differs (`c29b3a39…`, `feaa2ccd…` vs published `16478b6e…`) solely from zip container timestamps, as documented. The published artifact was not rewritten; QA re-verified it in place with `--verify-only`.

## 8. Visual QA (renderer available: Microsoft Word 16 COM as LibreOffice substitute)

LibreOffice absent on this host; PDFs produced with Word (the format's reference implementation) from QA-owned copies — published DOCX untouched. Artifacts: `render/v9_P0_render_copy.pdf` (12 pp), `render/v8_final_render_copy.pdf` (11 pp), `render/qa_v9_page1_title.png`, `qa_v9_page3_fig1.png`, `qa_v9_page9_fig2.png`, `qa_v9_page12_end.png`, `logs/visual_qa_report.json`, `logs/word_render.log`.

- No near-blank body pages, no text overflow beyond page bounds on any page (word-bbox check), no missing tables: captions Tabel 1–8 and Gambar 1–2 all present and rendered with content.
- Both figures render completely (Figure 1 pipeline diagram, Figure 2 two-panel chart); captions correct (T5 caption names model seed 13 + RNG seed 42; corrected value 0,895662 renders; legacy 0,895661 absent).
- Header (BITS banner), footer (copyright/page numbers), CC badge render on every page; title page correct with new saturation title.
- **Observation (cosmetic, non-P0):** v9 renders one page longer than v8 (12 vs 11); the last page contains only reference [12]. Cause: A12 paragraph insertion reflow, not corruption — all 12 references present and ordered in both renders; no content loss.
- **Observation (cosmetic, non-P0):** the Figure 1 PNG bitmap itself still contains the words "ceiling effect" inside the diagram box "Hasil PhiUSIIL". Media assets are byte-identical to v8 by design (P0 changed prose only); the bitmap text is not a manuscript claim, but reviewers may notice it. Candidate for P1 figure regeneration; no manuscript edit required for P0 acceptance.

## 9. Observations and P1 candidates (later work; not applied)

1. **Shared validator defect (external tool):** `docx_validate.py` header/footer rels key collision (see §2). Upstream one-line fix proposed in VALIDATOR_CORRECTION.md §8; validator lives outside this task's ownership and was not modified.
2. **Figure 1 bitmap wording** "ceiling effect" (P1 candidate: regenerate figure with "saturasi benchmark" label; media change only).
3. **Sparse final page** after reflow (cosmetic; optionally tighten spacing or accept).
4. **Stale docProps metadata** (inherited from v8 build): `dc:title` still says "v8", `app.xml` Pages/Words counts reflect an old Word save. Not visible in print layout; P1 candidate.
5. **P1/P2 register items untouched by design:** A13 (package inventory/evidence links), A14 (A0/A1 producer recovery), A15 (E8 cluster interval recovery), A16 (external references/comparative novelty), A17–A18 (optional reruns). Residual risks remain as documented in INTEGRATION_REPORT §"Residual risks": A0/A1 provenance unknown, E8 cluster uncertainty unverified, temporal cohort previously inspected, package not self-contained.

## 10. Corrective actions required

**None for the manuscript.** All P0 acceptance criteria are met in the published artifact; no byte of v8_final or v9_P0 was modified by QA. Tooling advisory only: do not gate any DOCX on a single `docx_validate.py` run (§2).

## 11. QA artifact inventory (all under `revision_v9_p0/05_qa/`)

- `P0_QA_MATRIX.csv` — 12 rows, A01–A12, verdict/evidence/exact-text/residuals
- `STRUCTURE_DIFF.json` — full source↔output structure comparison (regenerate with `final_qa.py`)
- `P0_QA_REPORT.md` — this report
- `logs/` — hashes.txt, struct_diff_run.log, content_align_run.log, content_alignment.json, verify_rels_v8.txt, verify_rels_v9.txt, docx_validate_seed0-9.json (v9), docx_validate_v8_seed0-9.json, verify_only_run.log, repro1.log, repro2.log, repro_member_compare.log, A01_A12_probes.json, row_text_map.json, verify_p0_run.log, echo_scan_run.log, visual_qa_report.json, visual_qa_run.log, word_render.log, docx_openability.log, v9_P0_full_text.txt, v8_final_full_text.txt
- `repro/` — det1.docx, det2.docx (throwaway rebuilds)
- `render/` — v9/v8 render copies (docx+pdf) + 4 QA page PNGs
- scripts: `struct_diff.py` (draft, superseded), `content_align.py`, `verify_p0.py`, `echo_scan.py`, `render_qa.py`, `final_qa.py`
