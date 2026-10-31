# Evidence package — phishing-URL generalisation audit (v10 P1 candidate)

Archived evidence bundle for the P1 candidate of an Indonesian empirical paper on phishing-URL detection
generalisation across two corpora (PhiUSIIL and PhreshPhish). This repository exists so that every claim in the
manuscript can be traced to a file and checked independently.

**Status: candidate, not accepted, not submission-ready.** The manuscript has not completed peer review.

## What is here

| Path | Content |
|---|---|
| `01_MANUSCRIPT/` | The candidate manuscript (DOCX) and its Word render (PDF) |
| `02_CLAIM_EVIDENCE/` | Stage-1 claim/provenance audit, P0 QA, P1 change register and literature ledgers |
| `03_EXPERIMENTS/` | Executed notebooks (E1–E8), metric tables, paired-bootstrap outputs, canonical temporal run artefacts |
| `04_ENVIRONMENT/` | Dependency record and the commands that were actually run |
| `05_LIMITATIONS/` | Known missing evidence and reproduction limits |
| `MANIFEST.csv` | Every file with role, byte size, SHA-256, origin path and reproduction status |
| `MANIFEST.sha256` | Checksums for independent verification |
| `OMITTED_ARTIFACTS.csv` | What is deliberately excluded, with reason, size and hash where computable |

## Verify the bundle

```bash
git clone https://github.com/Handy-Wibowo/supreme-sniffle
cd supreme-sniffle
sha256sum -c MANIFEST.sha256
```

All files must report `OK`. `.gitattributes` sets `* -text` so git performs no line-ending conversion; without
that, the checksums would not survive a clone.

## What is deliberately not here

- **Raw corpora.** PhiUSIIL and PhreshPhish are not redistributed. Obtain them from their providers:
  PhiUSIIL `doi:10.1016/j.cose.2023.103545`; PhreshPhish `arXiv:2507.10854` and Hugging Face
  `phreshphish/phreshphish`.
- **Trained model binaries, per-row predictions and full row splits.** Excluded by size; regeneration route is
  recorded per row in `OMITTED_ARTIFACTS.csv` (`run_temporal.py` + `design.json` + the recorded seeds).

## How the evidence is meant to be read

`INCLUDED` means the file is here and hash-verified. `WORKSPACE_ONLY`, `MISSING`, `OMITTED_SIZE`,
`OMITTED_LICENSE_PRIVACY` and `NOT_REQUIRED` appear in `MANIFEST.csv` and `OMITTED_ARTIFACTS.csv` with their
reasons. This is an **auditable** bundle, not a clean-room reproducible one, and the manuscript says so.

## Licence

MIT, as in `LICENSE`, covering the scripts and the evidence documents in this repository. The manuscript text
remains the authors' work.

## Archival copy

A release of this repository is connected to Zenodo, which mints a DOI per release. Cite the DOI (or this
repository at tag `v1.0.0`) when referring to the evidence bundle.