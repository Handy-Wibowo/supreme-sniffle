# P0 integrated manuscript report

## Output and reproducibility

- Source: `phishing/BITS_Draft_Phishing_URL_Leakage_v8_final.docx` (read-only).
- New output: `phishing/BITS_Draft_Phishing_URL_Leakage_v9_P0.docx`.
- Deterministic driver: `apply_p0_revisions.py`; it verifies the audited source SHA-256, checks every source locator, writes to a temporary DOCX, verifies projected text/structure, then publishes the new output.
- Source SHA-256 before/after: `65c8909be07a17427a0367306d3c9502cbe27ee36705e92c2234d61fc6896ccf` / identical.
- Final output SHA-256: `16478b6e2844dfcaa5c1599238d18dab37b943be12963c3565a15168512362ec` (unchanged by the validator correction).
- Reproducibility: independent rebuilds produce all 27 package members byte-identical; the whole-file hash varies between builds only because `python-docx` stamps wall-clock time into the zip container.
- `APPLIED_CHANGES.csv` records applied/absent dispositions for all A01–A12 with exact before/after text for edits. It has 57 applied rows and five absent-search dispositions.
- Verification artifacts: `verification_summary.json`, `v9_P0_structure.json`, full body/table export `v9_P0_text.txt`, and `VALIDATOR_CORRECTION.md` (validator defect analysis and evidence).

Run from any working directory with Python and `python-docx`:

```powershell
python "phishing/revision_v9_p0/04_integrated_manuscript/apply_p0_revisions.py"
```

The default output is the new `BITS_Draft_Phishing_URL_Leakage_v9_P0.docx`; the script refuses to overwrite v8 and refuses an unexpected source hash.

## Conflict resolution and accepted boundaries

The Stage-1 gate and primary audit evidence govern over conflicting proposal wording. Coordinator decisions were applied: Indonesian manuscript language is preserved apart from the English abstract; Section 5.2 uses one concise inventory paragraph with no proposed Table 9; no E6 verifier side-effect narrative was inserted; 03_scope_availability supplied the package inventory/baseline while fuller maps supplied additional P0 echoes; only P0 issues were changed.

- **A01:** source PhiUSIIL labels are legitimate=1 and phishing=0; the current E5–E8 mapping is explicitly legitimate=0/phishing=1. E3 legacy metrics are excluded from phishing-positive interpretation. No E3 result/table existed, so no E3 number was relabeled.
- **A02:** title, abstracts, keywords, contribution, result/discussion echoes, Figure 2 caption and conclusion now describe benchmark saturation without assigning its cause. High single-feature AUCs remain separability measurements only.
- **A03:** bootstrap RNG seed 42 is distinct from model seed 13; Table 5 identifies model, unit, replicate count and RNG seed. The truncated Table 5 precision lower bound is rounded to `0,895662`.
- **A04:** the reported E8 cluster interval is removed from inferential use. The supported 37.1% cohort-specific share remains descriptive; Table 8/conclusion mark cluster uncertainty unverified.
- **A05:** the PhreshPhish temporal test partition is stated to have been previously inspected, not blind/prospective. Future prospective claims require a new cohort and documented access restriction.
- **A06:** Section 5.2 identifies the 22 listed review-package files by categories, notes two unlisted directory items, and distinguishes absent package artifacts from separate workspace artifacts.
- **A07:** Section 2.2 identifies the notebook's exact four-column `DROP_COLS`, confirms retained `LineOfCode` and `NoOfExternalRef`, and states the cleaned-schema/A0 feature count.
- **A08:** 85 is a selected reported-fit count, explicitly excluding the metric-identical 10-fit parity rerun and identifying the older E3 temporal branch as a stub/dry run. Timing is limited to reported fits.
- **A09:** domain overlap, site-disjoint keys, shared-hosting tenants and prior test inspection are described narrowly. No strict no-overlap metrics were added; they were absent from v8 and are not necessary to correct its extant claims.
- **A10:** existing P0063 wording is bounded to the feature order and threshold checked against the transfer output manifest. No verifier-write, immediate pre-run-byte, or no-side-effect claim was added.
- **A11:** A2 is a shared ordered 18-field URL-extractor contract, not equality with similarly named precomputed source values. Methods and Table 2 are consistent.
- **A12:** stored A0/A1 upstream producer, reference population, computation time and label dependency remain unknown. Historical target-encoding evidence is limited to those probe implementations; current stored fields are not called target-encoded or leakage-free.

## Structure and preservation checks

The audited source has 180 body paragraphs, nine tables, two inline figures, one section and 83 styles. The output has 181 paragraphs (one inserted A0/A1 provenance paragraph), nine tables with unchanged shapes/cells, two inline figures, one section and the same styles. Existing order is preserved except for that insertion after the A2 feature paragraph. Header/footer text, page setup, relationship targets, DOCX part names and all four media-part hashes were compared. Only `word/document.xml` changed.

## Residual risks and non-P0 scope

1. **A0/A1 provenance remains unresolved.** The upstream producer, reference population, computation time and label dependency for stored statistical/page/content fields were not established by Stage-1 evidence. The manuscript preserves that unknown; no provenance experiment was run.
2. **E8 platform-cluster uncertainty is unverified.** Its interval is not used. The remaining 37.1% is a descriptive share of the examined cohort, not cluster-generalizable inference.
3. **The temporal cohort was previously inspected.** Chronological ordering, validation-only threshold selection and artifact freezing do not establish blindness or prospectivity.
4. **The review package is not a self-contained reproduction package.** Section 5.2 lists its contents and omissions; this editorial correction does not supply missing raw inputs, code, models or predictions.
5. **Strict no-overlap sensitivity metrics remain absent from the manuscript.** Existing overlap claims are bounded; the separately audited subset result was not inserted.
6. **A10 is bounded to extant wording only.** Immediate pre-verifier bytes are unavailable; no no-write/no-side-effect conclusion is claimed.
7. **P1/P2 remain untouched.** Package consolidation/evidence link resolution (A13), producer recovery (A14), E8 interval recovery (A15), external reference/SOTA validation (A16), and optional prospective/causal studies (A17–A18) were not implemented.
8. **The shared docx validator is unreliable on any document with a header or footer.** `~/.agents/skills/docx/scripts/docx_validate.py` collapses all `word/_rels/*.rels` onto one key, so a single invocation can report a false failure (or mask a real broken reference) on a healthy DOCX. It was not patched because it is shared tooling outside this task's ownership; `verify_package_relationships.py` is the deterministic substitute. See `VALIDATOR_CORRECTION.md`.

## Verification

The deterministic build completed from v8 to a new output. Rereading the output returned 181 body paragraphs, all nine table shapes/cells, both inline figures and the unchanged section order; the build script's expected body/table projections passed. The source hash remained unchanged. Exact checks and final hashes are in `verification_summary.json`.

**Validator status — the official `docx_validate.py` result is not trustworthy on its own.** A previous version of this report claimed `{"ok": true, "issues": []}`. That claim was not reproducible: the same command on the same file returns either `{"ok": true, "issues": []}` or four `unresolved-reference` errors for `document.xml` `rId9`, `rId10`, `rId13` and `rId14`, depending on Python's string-hash seed (two 30-run unseeded samples: 9 pass / 21 fail and 13 pass / 17 fail, i.e. roughly the 1-in-3 chance that `document.xml.rels` is iterated last; both `v8_final` and `v9_P0` behave identically).

The failure is a defect in the validator, not in the document. `docx_validate.py` derives a `.rels` file's source part as `dirname(dirname(rels_name))`, which drops the part filename, so `word/_rels/document.xml.rels`, `word/_rels/header1.xml.rels` and `word/_rels/footer1.xml.rels` all collapse onto the key `word` and the last one iterated wins. When `header1.xml.rels` wins, the document's header/footer/figure references appear unresolved. All four `rId`s are declared in `word/_rels/document.xml.rels` and all four targets exist (`header1.xml`, `footer1.xml`, `media/image3.png`, `media/image4.png`); the package has 24 relationships and zero dangling internal targets.

Repairing the document was rejected because there is nothing to repair: deleting those references would remove the header, footer and both figures, so the published DOCX is byte-for-byte unchanged. Instead, the build script now executes the official validator over eight hash seeds and records every report verbatim (no hard-coded pass), and runs `verify_package_relationships.py`, a deterministic checker with the relationship map keyed by the real source part that also checks `r:id`/`r:embed` references in every part. That checker returns `{"ok": true, "issues": []}` for seeds 0–9 on both `v8_final` and `v9_P0`, and the build fails hard if it does not. `apply_p0_revisions.py --verify-only` re-checks the published artifact in place without rewriting it. Full evidence, XML contexts, seeds and the suggested upstream fix are in `VALIDATOR_CORRECTION.md`.

This validator correction is recorded as a non-P0 verification fix; it changes no A01–A12 disposition and no manuscript text.
