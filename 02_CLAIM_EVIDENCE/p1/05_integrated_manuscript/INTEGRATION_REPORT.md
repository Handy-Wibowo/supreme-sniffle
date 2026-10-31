# P1 Integration Report

Date: 2026-11-01
Builder: `05_integrated_manuscript/apply_p1_revisions.py`
Source: `BITS_Draft_Phishing_URL_Leakage_v9_P0.docx` (SHA-256 `16478b6e…362ec`, asserted before any write)
Output: `BITS_Draft_Phishing_URL_Leakage_v10_P1_candidate.docx` (SHA-256 `b9c39091…1f66196`)

## 1. Integration rules applied

1. The source hash is asserted; a mismatch aborts before anything is written.
2. Every edit asserts its own locator (exact paragraph prefix or exact run text). A missing or duplicated locator
   aborts the build.
3. All text edits are additive except six explicitly listed replacements (Table 1 intro, Table 1 caption,
   reference [12] tail, §5.2 availability paragraph, core properties, app.xml statistics).
4. No P0-corrected sentence was rewritten. The P0 corpus of corrections (A01–A12) is re-verified afterwards by
   `06_self_qa/regression_p0.py`.
5. Only `word/document.xml`, `word/media/image3.png` and `docProps/*` are touched. Styles, numbering, headers,
   footers, sections, tables 2–9, Figure 2 and every other media part are byte-preserved.

## 2. Order of operations (matters)

1. **Table renumbering first.** `Tabel 8…2` is shifted to `Tabel 9…3` in descending order, so 2→3 cannot cascade
   into the freshly written 3→4. This must run before any new text that cites a table number.
2. Additive sentence edits (6).
3. Table 1 replacement: intro paragraph, caption, header, 10 data rows (row count 6 → 11).
4. New §1.2: heading + 5 paragraphs, cloned from existing body/heading paragraphs so formatting is inherited.
5. Reference [12] page range; then 12 new reference paragraphs [13]–[24], cloned from [12] to inherit the
   three-run (normal/italic-venue/normal) structure.
6. Config-table caption inserted before table 2.
7. §5.2 availability paragraph replaced.
8. Core properties; ZIP post-processing (Figure 1 media, picture name/title, app.xml statistics).

## 3. Registered changes

`CHANGE_REGISTER.csv` — **19 rows**, one per material change, each with locator, exact before/after, evidence path,
reason, and a P0-interaction field. Types used: `APPEND_TEXT` (6), `REPLACE_PARA` (2), `REPLACE_CAPTION` (1),
`REPLACE_TABLE` (1), `INSERT_SECTION` (1), `REPLACE_REF_TAIL` (1), `INSERT_REFERENCES` (1), `RENUMBER_REFS` (1),
`INSERT_CAPTION` (1), `META` (3), `REPLACE_MEDIA` (1).

| ID | Action | What |
|---|---|---|
| P1-001 | A16 | [13] added to §1 ¶1 (F1≈0.99 can be a design artefact) |
| P1-002 | A16 | [14], [15] added to §1 ¶2 (drift, protocol dependence) |
| P1-003 | A16 | Table 1 intro rewritten as a design-comparison description |
| P1-004 | A16 | Table 1 caption rewritten |
| P1-005 | A16 | Table 1 rebuilt: 11 rows, 4 design-oriented columns |
| P1-006 | A16 | New §1.2 "Tinjauan Tematik" (heading + 5 paragraphs) |
| P1-007 | A16 | Reference [12] page range added |
| P1-008 | A16 | References [13]–[24] appended |
| P1-009 | A16 | In-text reference for the feature-configuration table |
| P1-010 | A16 | [21], [22] added to §2.6 (PPV projection) |
| P1-011 | A16 | [21], [22] added to §3.6 (prevalence) |
| P1-012 | A16 | [21], [22] added to §3.8 (threshold trade-off) |
| P1-013 | A16/QA | Table renumbering 2..8 → 3..9 |
| P1-014 | A16/QA | Caption for the previously uncaptioned configuration table |
| P1-015 | A13 | §5.2 availability paragraph replaced to match the new package |
| P1-016 | metadata | docProps title/subject/description corrected |
| P1-017 | A02 | `word/media/image3.png` replaced (corrected Figure 1) |
| P1-018 | metadata | Figure 1 `docPr` name/title de-versioned from v8 |
| P1-019 | metadata | app.xml Pages/Words refreshed (4/1998 → 13/8759) |

## 4. Deliberate non-changes

- Citation order for [1]–[12] is preserved exactly, matching the P0 invariant. The numbering convention is
  thematic rather than order-of-appearance; that was already true in v9_P0 and was not "fixed", because renumbering
  would rewrite every citation-bearing paragraph and create regression risk disproportionate to the benefit.
  New citations were appended as [13]+ in first-appearance order **within the new text**.
- Indonesian and English abstracts were left unchanged. Their claim boundaries were already correct after P0, and
  no new claim was introduced that would require an abstract edit.
- No metric, table value, figure value, or statistical computation was altered.
- No experiment artifact was regenerated.

## 5. Verification performed after integration

| Check | Result |
|---|---|
| `apply_p1_revisions.py --verify-only` (self-check) | candidate opens; 200 paragraphs, 9 tables, 2 shapes; no "ceiling effect"; 24 references; title current |
| `qa_structure.py` | 24/24 PASS |
| `regression_p0.py` | 16/16 PASS |
| `verify_package_relationships.py` on the candidate | `{"ok": true, "issues": []}` |
| Two builds from v9_P0 | members, media and text identical; only ZIP timestamps differ |
| Word render | 13 pages, 8 588 words, all pages inspected |

## 6. Reproducibility statement

A reviewer can rebuild the candidate from v9_P0 with a single command and obtain a semantically identical document.
Full command sequence and expected outcomes are in the package's `04_ENVIRONMENT/RUN_COMMANDS.md`.

`IMPLEMENTATION COMPLETE — PENDING CODEX REVIEW`.