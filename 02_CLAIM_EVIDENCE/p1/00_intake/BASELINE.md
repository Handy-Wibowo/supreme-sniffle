# P1 Intake Baseline (Phase 0)

Date: 2026-11-01
Captured by: `baseline_intake.py` → `baseline.json` (machine-readable)

## 1. Hash gate

| File | SHA-256 | Expected | Match |
|---|---|---|---|
| `BITS_Draft_Phishing_URL_Leakage_v9_P0.docx` | `16478b6e2844dfcaa5c1599238d18dab37b943be12963c3565a15168512362ec` | same | **YES** |
| `BITS_Draft_Phishing_URL_Leakage_v8_final.docx` | `65c8909be07a17427a0367306d3c9502cbe27ee36705e92c2234d61fc6896ccf` | same | **YES** |

## 2. Structure captured from v9_P0

| Property | Value |
|---|---|
| Body paragraphs | 181 |
| Tables | 9 |
| Inline figures | 2 |
| Sections | 1 |
| Styles | 83 |
| Package members | 27 |
| Citation occurrences (body) | 37 |
| Distinct citation ids | 12 |
| Media parts | `image1.png` (13 257 B), `image2.png` (1 249 B), `image3.png` (60 537 B), `image4.png` (163 965 B) |
| `image3.png` SHA-256 | `221d628f…eae2004` — identical to `figure_1_research_pipeline_v8.png` |
| Core title | `… — v8` (stale) |
| app.xml Pages/Words | `4` / `1998` (stale) |

## 3. Verification commands executed at intake

| Command | Working directory | Exit | Result |
|---|---|---|---|
| `python apply_p0_revisions.py --verify-only` | `phishing/revision_v9_p0/04_integrated_manuscript` | 0 | `PASS`; 181/9/2/1; 12 actions; 57 applied rows; 5 absent rows; package_check true |
| `python verify_package_relationships.py …v9_P0.docx` | same | 0 | `{"ok": true, "issues": []}` |
| Word COM open + PDF export | scratch copy | 0 | 12 pages, 579 236 B PDF |

The P0 verifier's own field `official_docx_validate_ok_runs` was `3/8`, consistent with the documented
nondeterministic `docx_validate.py` defect. It was not used as a gate.

## 4. Intake decision

Baseline integrity confirmed → Phase 1 authorised. No discrepancy was found between the published verified state
and the artifacts on disk. The handed-off copy tree (`Hermes_Handoff_v9_P1_FULL`) was used as a read-only reference
only; all execution ran against the original workspace paths, because the P0 scripts resolve inputs relative to
their own location and therefore fail inside the flattened copy layout.

## 5. Environment used for P1

- Python 3.12.5 in `E:\Kuliah\Tugas Akhir\.venv_p1` (uv-created; `python-docx 1.2.0`, `lxml 6.1.3`,
  `PyMuPDF 2.0`, `pywin32`, `resvg-py`, `pillow 13.0.0`).
- The `python` on PATH is a Hermes-managed venv without pip; it was not used.
- No LibreOffice on this host; Microsoft Word 16 COM automation was used for rendering (12 pages at intake,
  13 pages for the candidate).