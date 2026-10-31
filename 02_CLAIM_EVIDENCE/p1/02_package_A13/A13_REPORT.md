# A13 — Reviewer Package and Evidence Links

Date: 2026-11-01

Package: `phishing/AI_Review_SINTA2_Package_v10_candidate/`
Built by: `revision_v10_p1/02_package_A13/build_package.py` (idempotent; copy-only; no source file moved or deleted)

## 1. What changed relative to the v8 package

The v8 package had 22 declared files plus two unlisted directory items, and it omitted E1–E5, raw inputs, per-row
evidence, implementation source, and model/prediction artefacts. The v10 candidate package closes the largest of
those gaps and states the remainder explicitly.

| Aspect | v8 package | v10 candidate package |
|---|---|---|
| Declared files | 22 (+2 unlisted) | every file listed; state recorded per file |
| Manifest | `DAFTAR_BERKAS.md` (prose list) | `MANIFEST.csv` (path, role, bytes, SHA-256, origin, origin SHA-256, reproduction status, state) + `MANIFEST.sha256` |
| Stage-1 audit | absent | complete (67 files under `02_CLAIM_EVIDENCE/stage1_audit/`) |
| P0 QA + change log | absent | `p0/P0_QA_REPORT.md`, `P0_QA_MATRIX.csv`, `APPLIED_CHANGES.csv`, `VALIDATOR_CORRECTION.md` |
| E1–E5 | absent | `03_EXPERIMENTS/E1_E5_pipeline/` (executed notebook + 3 metric tables) |
| Table 5 paired bootstrap | absent | `03_EXPERIMENTS/paired_bootstrap_E4/` — **recovered in P1**; `paired_bootstrap.csv` records seed 42, 1000 replicates, `registrable_domain`, `n_domains=35100` and matches the manuscript row for row |
| Temporal run | partial | `03_EXPERIMENTS/temporal_canonical_run/` (small artefacts) + scripts + notebooks + run log |
| Omissions | implicit | `OMITTED_ARTIFACTS.csv` with reason, state, size and SHA-256 where computable |

## 2. Manifest states used

`INCLUDED` (distributed, hash-verified), `WORKSPACE_ONLY` (exists, deliberately not distributed),
`MISSING` (known absent), `OMITTED_SIZE` (too large to distribute), `OMITTED_LICENSE_PRIVACY` (distribution
constraint), `NOT_REQUIRED` (not evidence).

Two rows are intentionally `WORKSPACE_ONLY`: the v9_P0 baseline manuscript and the v8 independent review prose.
The raw corpora are `OMITTED_LICENSE_PRIVACY` with provider pointers (PhiUSIIL DOI, PhreshPhish Hugging Face).
Model binaries, per-row predictions and full splits are `OMITTED_SIZE` with the exact regeneration route.

## 3. Claim coverage

`CLAIM_TO_FILE_MAP.csv` maps 24 claims/objects (9 tables, 2 figures, 7 prose claims, references, experiment
provenance, P0 corrections, A14/A15) to a package file or to an explicit omission state.

| State | Count | Meaning |
|---|---:|---|
| INCLUDED | 22 | evidence present and hash-verified |
| OMITTED_LICENSE_PRIVACY | 1 | raw corpora |
| OMITTED_SIZE | 1 | model binaries and row-level splits/predictions |
| MISSING | 0 | — |
| WORKSPACE_ONLY | 0 | — |

Total mapped objects: 24 (9 tables, 2 figures, references, experiment provenance, P0 corrections, A14/A15).

Two residual gaps are stated rather than hidden:

1. Figure 2's plotting script is workspace-only; the figure is regenerable from the included Table 6–8 evidence.
2. E1–E3 legacy outputs are not shipped because P0 established they are not used as phishing-positive metrics;
   their status is recorded in the Stage-1 audit, which is included.

## 4. Integrity and reproducibility

- `sha256sum -c MANIFEST.sha256` inside the package: **all files OK** (verified after the final build).
- The package is **not** claimed to be clean-room reproducible. `00_README/README.md` states this explicitly and
  names what cannot be reproduced without the external corpora.
- `04_ENVIRONMENT/RUN_COMMANDS.md` records the four commands that were actually executed in P1, with their
  real outcomes reported in `06_self_qa/P1_QA_REPORT.md`.
- Notebooks are included as evidence with their original execution counts; none was re-executed in P1 and none is
  claimed to have been.

## 5. Manuscript alignment

§5.2 of the candidate was replaced so that it describes this package and nothing else: the five top-level
directories, the two manifest files, the omission list by category, and the explicit statement that the bundle is
auditable rather than fully reproducible. No file count is asserted in the prose, so the statement cannot drift out
of sync with the tree; the manifest is the authority for counts.

## 6. Verdict

`PASS — A13 scope`, with the two residual gaps above declared. The package statement in the manuscript matches the
actual tree, every included file carries a hash, and every omission carries a reason and a regeneration route.
