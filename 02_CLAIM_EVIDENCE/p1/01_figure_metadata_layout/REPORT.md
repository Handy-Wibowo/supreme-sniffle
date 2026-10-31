# 01 — Figure, Metadata, and Layout (P1)

Date: 2026-11-01

## 1. Figure 1 wording correction

| Item | Value |
|---|---|
| Source (read-only) | `phishing/manuscript_v8_work/figure_1_research_pipeline_v8.svg` |
| Source SHA-256 | `64f4c8855a655cc50fb525d5acca178b87419726dde810dea3b214e5ebc18f15` |
| Output SVG | `revision_v10_p1/01_figure_metadata_layout/figure_1_research_pipeline_v10.svg` |
| Output SVG SHA-256 | `6854571054674a37f066b9fafdb308a9df990461a8785b8f09afe05681086add` |
| Output PNG | `figure_1_research_pipeline_v10.png` (2580x2460, 3x) |
| Output PNG SHA-256 | `bf7befe28c1cfd807e6403a2750c018a9629e1673c8ade3d9cb32fb5af4717c5` |
| Renderer | resvg (via `resvg-py`), zoom=3, white background |

Exact change (the only changed line in the SVG):

```
BEFORE  <text class="ts" x="215" y="437" text-anchor="middle">ceiling effect, paired domain bootstrap,</text>
AFTER   <text class="ts" x="215" y="437" text-anchor="middle">saturasi benchmark, bootstrap domain berpasangan,</text>
```

Guard applied by `fix_figure_1.py`: re-substituting the new segment with the old one reproduces the source
byte-for-byte, i.e. no other geometry, colour, font, arrow, or label changed. Verified: `svg_geometry_identical: True`.

Legibility: the replacement line is 46 characters at the same 12 px font inside a 300 px-wide box. The rendered
3x PNG was inspected at final size; the line fits inside the box with margin on both sides and is legible at the
manuscript's display width (5.984 in), where the source was 143.7 dpi and the new asset is ~431 dpi.

## 2. Embedded media replacement

| Item | Value |
|---|---|
| DOCX part | `word/media/image3.png` |
| Before SHA-256 | `221d628fd0be38a08d0ca45bd7279e5a8774ff2b446c9a4c2511a78c3eae2004` (byte-identical to the v8 PNG) |
| After SHA-256 | `bf7befe28c1cfd807e6403a2750c018a9629e1673c8ade3d9cb32fb5af4717c5` |
| Display size | unchanged: `wp:extent cx="5472000" cy="5217488"` (same aspect ratio 1.0488) |

The raster was replaced inside the ZIP package, so the relationship `rId13 -> media/image3.png` and all
other drawing properties are untouched. `word/media/image4.png` (Figure 2) was not modified.

## 3. Alt text and picture name

- Alt text (`wp:docPr/@descr`) for Figure 1 was already free of the stale wording
  ("Pipeline audit generalisasi PhiUSIIL dan PhreshPhish dengan jembatan transfer zero-shot yang dibekukan.") and was left unchanged.
- `wp:docPr/@name` and `@title` previously referenced `figure_1_research_pipeline_v8`; both now reference
  `figure_1_research_pipeline_v10`. No v8 token remains in `word/document.xml`.

## 4. Metadata correction (docProps)

| Field | v9_P0 | v10 candidate |
|---|---|---|
| `dc:title` | `Audit Generalisasi Deteksi Phishing URL pada PhiUSIIL dan PhreshPhish — v8` | `Audit Generalisasi Deteksi Phishing URL: Saturasi Benchmark pada PhiUSIIL, Evaluasi Temporal, dan Transfer Lintas-Korpus ke PhreshPhish` |
| `dc:subject` | `Manuskrip v8 dengan transfer lintas-korpus, evaluasi ambang, dan taksonomi galat` | `Manuskrip v10 P1 dengan transfer lintas-korpus, evaluasi ambang, dan taksonomi galat` |
| `dc:description` | `v8 menambahkan eksperimen transfer zero-shot, ...; v7 tidak diubah.` | `v10 P1: koreksi kata pada Gambar 1, pembaruan metadata versi, perluasan related work dan verifikasi referensi. Kandidat untuk tinjauan independen.` |
| `Pages` / `Words` | `4` / `1998` (stale) | `13` / `9015` (refreshed from Word statistics) |

Not touched: `dc:creator` (`Mesran.M.Kom`), `cp:lastModifiedBy`, `cp:revision`, dates, keywords.
Author identity, affiliation, email, CRediT, funding and AI-disclosure text remain the user's to complete;
nothing was invented (see §6).

Method note: `Pages`/`Words` were refreshed by rewriting only those two elements in `docProps/app.xml` after
measuring the rendered document with Word (`ComputeStatistics(2)` and `(0)`). This is recorded in
`RENDER_LOG.json`; the DOCX was re-rendered afterwards so the delivered PDF matches the delivered DOCX.

## 5. Layout findings

- The candidate renders to **13 pages** (v9_P0: 12). The growth is the new §1.2 (heading + 5 paragraphs) and the
  expanded Table 1.
- The formerly sparse final page now carries references [12]–[24]; there is no near-empty page.
- No clipped text, no missing table, no figure overflow, no unexpected blank page was found on any of the 13 pages
  (page images in `06_self_qa/pages/`).
- The paper was **not** compressed to remove whitespace, per the handoff rule.

## 6. User-input blockers (not fabricated)

| Item | Current state | Owner |
|---|---|---|
| Author names, affiliations, emails | placeholders `[Nama Penulis 1]`, `[Program Studi]`, `[email penulis 1]` | user |
| CRediT / author contributions | placeholder block | user |
| Funding statement | "self-funded" — confirm or replace | user |
| AI-use disclosure | present, generic Indonesian wording — confirm | user |
| Journal, volume, DOI, page numbers in header | template placeholders (`Volume 99, No 99, ... DOI 10.47065/bits.v9i9.999`) | user / editor |

## 7. Termination note

Table numbering was normalised because the feature-configuration table had no number, no caption and no in-text
reference. That table became Table 2 and every later table shifted by one (`Tabel 2..8` -> `Tabel 3..9`), with
8 existing captions and 8 existing in-text references updated in one deterministic pass (the ninth caption and the
ninth in-text reference are the ones added for the new Table 2). Verified afterwards: 9 captions for 9 tables,
ascending 1..9, and every in-text `Tabel N` resolves to an existing caption (`06_self_qa/QA_CHECKS.json`).