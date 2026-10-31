# VALIDATOR_CORRECTION — v9_P0 `docx_validate.py` discrepancy

Corrects the previous false claim in `INTEGRATION_REPORT.md` / `verification_summary.json` that
`docx_validate.py` returned `{"ok": true, "issues": []}`. The claim was not reproducible: the
official validator is **not deterministic**, and its reported `rId9/rId10/rId13/rId14`
`unresolved-reference` errors are a **validator defect, not a package defect**.

**The published DOCX was not modified.** Its bytes and SHA-256 are exactly what the previous build
produced; no relationship was added, removed or renumbered, and no archive metadata was rewritten.
Only the build driver, a new checker script and these reports changed.

Environment: Windows 10.0.22631, Python 3.14.7, lxml 6.1.3, python-docx 1.2.0.

## 1. Commands used

```powershell
# Official (Hermes docx skill) validator
python "C:/Users/NITRO 5/.agents/skills/docx/scripts/docx_validate.py" `
  "phishing/BITS_Draft_Phishing_URL_Leakage_v9_P0.docx"

# Same validator with a pinned string-hash seed (shows the nondeterminism)
$env:PYTHONHASHSEED = "0"   # then 1, 2, ... 9
python "C:/Users/NITRO 5/.agents/skills/docx/scripts/docx_validate.py" `
  "phishing/BITS_Draft_Phishing_URL_Leakage_v9_P0.docx"

# Deterministic replacement, same checks plus header/footer/endnote references
python "phishing/revision_v9_p0/04_integrated_manuscript/verify_package_relationships.py" `
  "phishing/BITS_Draft_Phishing_URL_Leakage_v9_P0.docx"

# Re-verify the published artifact in place (never rewrites it)
python "phishing/revision_v9_p0/04_integrated_manuscript/apply_p0_revisions.py" --verify-only

# Reproducibility: rebuild twice to throwaway targets and compare package members
python "phishing/revision_v9_p0/04_integrated_manuscript/apply_p0_revisions.py" --output ".omp_tmp/v9runs/det1.docx"
python "phishing/revision_v9_p0/04_integrated_manuscript/apply_p0_revisions.py" --output ".omp_tmp/v9runs/det2.docx"
```

Official validator hash: `66c1d307e940803e1505002477ced7ac156524566f16d29913807443a8d8826c`
(`docx_validate.py`, 6153 bytes, mtime 2026-10-12).

## 2. Exact validator output, before and after

**Before (v9_P0 as published at revision time, seed-dependent):**

```json
{"ok": false, "issues": [{"severity": "error", "code": "unresolved-reference", "detail": "document.xml references rId13 with no relationship"}, {"severity": "error", "code": "unresolved-reference", "detail": "document.xml references rId14 with no relationship"}, {"severity": "error", "code": "unresolved-reference", "detail": "document.xml references rId9 with no relationship"}, {"severity": "error", "code": "unresolved-reference", "detail": "document.xml references rId10 with no relationship"}]}
```
Exit code 1.

**Same command, same file, other seeds:**

```json
{"ok": true, "issues": []}
```
Exit code 0.

**Seeded sweep (`PYTHONHASHSEED` 0–9), identical on `v8_final` and `v9_P0`:**

| seed | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| result | FAIL | ok | ok | FAIL | FAIL | FAIL | ok | FAIL | FAIL | ok |

Unseeded samples of 30 consecutive invocations of the same command on the same file: **9 pass / 21 fail**, and on a repeat sample **13 pass / 17 fail** — consistent with the ~1-in-3 chance that
`document.xml.rels` happens to be the last `word/_rels/*.rels` part iterated, not with a fixed rate.

Both source and output fail in exactly the same pattern, so this is inherited, not introduced by v9.

**After (deterministic replacement), seeds 0–9, both files:**

```json
{"ok": true, "issues": []}
```
Exit code 0 in every run.

**Official validator on the published artifact:** unchanged behaviour, 3/8 ok across seeds 0–7 — recorded
verbatim in `verification_summary.json` → `package_validation.official_docx_validate`, which the
build script now populates by actually executing the validator instead of asserting the result.

## 3. Root cause

`docx_validate.py` derives the source part of a `.rels` file with:

```python
source_part = posixpath.normpath(
    posixpath.join(posixpath.dirname(rels_name), ".."))
```

For `word/_rels/document.xml.rels` this yields `word` — the **part filename is dropped**.
`word/_rels/header1.xml.rels` and `word/_rels/footer1.xml.rels` therefore collapse onto the same
key `word`:

```python
rel_ids_by_source[source_part or "_package"] = ids   # later parts overwrite earlier ones
...
doc_rels = rel_ids_by_source.get("word", {})         # whichever survived
```

`.rels` parts are iterated from a `set` of strings, so the survivor depends on Python's
per-process string-hash seed. When `header1.xml.rels` (which defines only `rId1`–`rId3`) wins, the
four `document.xml` references to `rId9` (header), `rId10` (footer), `rId13`/`rId14` (figures) look
unresolved. When `document.xml.rels` wins, the file passes.

Control test proving the mechanism: a copy of v9_P0 with `word/_rels/header1.xml.rels` and
`word/_rels/footer1.xml.rels` removed from the archive passes on all six seeds that previously
failed (0, 3, 4, 5, 7, 8). No relationship was added; the collision was simply removed.

## 4. XML context of the four "unresolved" references

All four are genuine, correctly declared relationships in `word/_rels/document.xml.rels`:

| rId | Relationship target | Reference site in `document.xml` |
|---|---|---|
| `rId9` | `header1.xml` | `<w:sectPr …><w:headerReference w:type="default" r:id="rId9"/><w:footerReference w:type="default" r:id="rId10"/>` |
| `rId10` | `footer1.xml` | same `w:sectPr` as above |
| `rId13` | `media/image3.png` | `<pic:cNvPr id="0" name="figure_1_research_pipeline_v8.png"/>…<a:blip r:embed="rId13"/>` |
| `rId14` | `media/image4.png` | `<pic:cNvPr id="0" name="figure_2_generalization_thresholds_v8.png"/>…<a:blip r:embed="rId14"/>` |

`word/_rels/document.xml.rels` declares 14 relationships (`rId1`–`rId14`); `rId9`, `rId10`, `rId13`
and `rId14` are all present, and their targets all exist in the package:

```
rId9  -> header1.xml     (word/header1.xml        present, 11766 bytes)
rId10 -> footer1.xml     (word/footer1.xml        present,  8763 bytes)
rId13 -> media/image3.png(word/media/image3.png   present, 60537 bytes, PNG magic)
rId14 -> media/image4.png(word/media/image4.png   present, 163965 bytes, PNG magic)
```

Independent audits of the whole package, for both `v8_final` and `v9_P0`:

- 24 relationships across five `.rels` parts; **0 dangling internal targets**; 3 external
  hyperlinks skipped correctly.
- Every `r:id`/`r:embed`/`r:link` in `document.xml`, `header1.xml` and `footer1.xml` resolves.
- `[Content_Types].xml` covers every member; no orphan overrides.
- All four media parts decode with known magic bytes; paragraph/run/table style ids all defined.
- python-docx opens the file and reads 181 paragraphs, 9 tables, 1 section, 2 inline shapes,
  header and footer text and page setup.

The package is well-formed; the validator's key collision is the only defect.

## 5. Decision

**Do not repair the DOCX.** There is nothing to repair in it. Deleting or renumbering `rId9`,
`rId10`, `rId13`, `rId14` would destroy the header, footer and both figures — i.e. it would
"fix" the report by damaging the manuscript. Editing `v8_final` was out of scope and is not needed,
since both files fail identically.

Chosen smallest defensible action:

1. **Do not fake PASS.** The build script no longer writes a hard-coded `{ok: true}`. It now
   executes the official validator 8 times over `PYTHONHASHSEED` 0–7 and records every report
   verbatim (`runs`, `runs_ok`, `runs_not_ok`, `deterministic: false`).
2. **Add a seed-independent check** (`verify_package_relationships.py`) that performs the same
   health checks with the relationship map keyed by the real source part, iterates deterministically,
   and additionally validates `r:id`/`r:embed`/`r:link` in every part (not just `document.xml`),
   content-type coverage, media magic bytes, styles, and python-docx openability of header/footer.
   The build script runs it and **fails hard** if it does not return `{"ok": true, "issues": []}`.
3. **Add `--verify-only`** so the published artifact can be re-verified in place without being
   rewritten, and state reproducibility at the package-member level rather than the container level.
4. **Disclose** the inherited validator failure in `INTEGRATION_REPORT.md` and
   `verification_summary.json` instead of claiming a clean pass.

This is a **non-P0 verification fix** (no package byte changed) and is recorded separately from A01–A12. No P0 action was
invented for it; all 12 P0 dispositions are unchanged (57 applied rows + 5 absent dispositions).

## 6. Changed package parts and hashes

| File | SHA-256 | Status |
|---|---|---|
| `phishing/BITS_Draft_Phishing_URL_Leakage_v8_final.docx` | `65c8909be07a17427a0367306d3c9502cbe27ee36705e92c2234d61fc6896ccf` | unchanged (read-only source) |
| `phishing/BITS_Draft_Phishing_URL_Leakage_v9_P0.docx` | `16478b6e2844dfcaa5c1599238d18dab37b943be12963c3565a15168512362ec` | **unchanged** |
| `.../apply_p0_revisions.py` | `8fa437eed22473ada35a3cd0aab8628e4acfa07af5a22dd8c4d58efee7a97e30` | corrected driver |
| `.../verify_package_relationships.py` | `acaf916960d255d79b2d2ef0f4f0a39261e1a9f73fd4676751c661c34552eddb` | new checker |

The output hash is unchanged from the previously published artifact (`16478b6e…62ec`), so this
correction altered no DOCX byte. Inside the DOCX, only `word/document.xml` differs from `v8_final`;
the other 26 parts — styles, numbering, theme, settings, webSettings, fontTable, header, footer,
endnotes, footnotes, all four media parts, customXml and docProps — are byte-identical to the source.

Reproducibility is at the package-member level, not the container level. Two independent rebuilds to
throwaway targets produced **all 27 members byte-identical** (same SHA-256, same order) to each
other and to the published file. The whole-file SHA-256 differs between builds because `python-docx`
stamps wall-clock time into the zip container; the published file was deliberately **not** rewritten
to force container-level equality.

## 7. Preservation and P0 re-verification (published artifact)

| Check | Result |
|---|---|
| Source SHA-256 unchanged | `65c8909b…96ccf` before and after |
| Body paragraphs | 181 (180 + the one documented A12 provenance insertion) |
| Tables / shapes / sections / styles | 9 / unchanged 9 shapes / 1 / 83 |
| Inline figures | 2, media part hashes unchanged |
| Header, footer, page setup | unchanged, read back correctly |
| Citation markers `[n]` | 44 occurrences, 12 distinct, exact match to source (none lost, none added) |
| P0 dispositions | A01–A12 all present; 57 applied rows, 5 absent dispositions |
| Changed parts vs source | `word/document.xml` only |
| Reproducible rebuild | 27/27 package members byte-identical across independent runs |

## 8. Residual risk

1. **The official validator still fails intermittently.** Any future gate that runs
   `docx_validate.py` once and reads the exit code can report a false failure on a healthy DOCX —
   and, symmetrically, can report a false pass on a document whose real `document.xml` relationships
   are broken, because the collision masks them. Do not treat a single `docx_validate.py` result as
   evidence for any DOCX that has both `word/_rels/header1.xml.rels` and `word/_rels/document.xml.rels`.
   Either run it under several `PYTHONHASHSEED` values, or use
   `verify_package_relationships.py`. The validator itself was **not** modified: it lives outside
   this task's ownership (`~/.agents/skills/docx`) and patching it would change shared tooling.
   A one-line upstream fix is `source_part = head + tail[:-len(".rels")]` and
   `doc_rels = rel_ids_by_source.get("word/document.xml", {})`.
2. **Whole-file SHA-256 is not reproducible across rebuilds.** `python-docx` writes wall-clock
   timestamps into the zip container, so a rebuild yields the same 27 package members but a different
   container hash. Verification therefore compares package members, and the published file is
   re-verified in place with `--verify-only` rather than rebuilt.
3. **A12 provenance remains unresolved**, E8 cluster uncertainty remains unverified, the temporal
   cohort was previously inspected, and the review package is still not self-contained — all
   unchanged from the accepted P0 boundaries.
4. **P1/P2 remain untouched**, including A13–A18.
