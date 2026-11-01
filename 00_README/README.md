# AI Review Package — v10 P1 candidate

Built: 2026-11-01T20:20:49Z (UTC)
Included files: 194  |  total bytes: 41,420,164  |  omitted/limited entries: 18

## What this package is

Evidence bundle for the P1 candidate of an empirical phishing-URL generalization paper.
It is a *candidate* package: the manuscript has not been accepted and the P1 phase is not closed.

## What it contains

| Directory | Files | Content |
|---|---:|---|
| `01_MANUSCRIPT/` | 2 | P1 candidate DOCX and its Word render |
| `02_CLAIM_EVIDENCE/` | 102 | Stage-1 audit, P0 QA, P1 registers and literature ledgers |
| `03_EXPERIMENTS/` | 89 | Executed notebooks, metrics, ledgers and canonical temporal run artefacts |
| `05_LIMITATIONS/` | 1 | Known missing evidence and reproduction limits |

## What it does NOT contain

See `OMITTED_ARTIFACTS.csv`. In summary: raw datasets (public, obtain from the providers),
trained model binaries and per-row prediction/split archives (regenerable from the recorded
design and seeds), generated caches, and historical reviewer prose.

## Reproducibility claim

This package is **not** a clean-room reproducible bundle. It is an auditable evidence bundle:
every included file has a SHA-256 and a recorded origin path, and the manifest distinguishes
`INCLUDED`, `WORKSPACE_ONLY`, `MISSING`, `OMITTED_SIZE`, `OMITTED_LICENSE_PRIVACY`, and `NOT_REQUIRED`.

## Integrity

Verify with:

```
python -c "import csv,hashlib,pathlib;[print(r['path']) for r in csv.DictReader(open('MANIFEST.csv'))]"
sha256sum -c MANIFEST.sha256
```

`MANIFEST.sha256` covers every included file.
