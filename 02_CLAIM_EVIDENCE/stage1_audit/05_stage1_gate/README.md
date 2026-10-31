# Stage-1 gate outputs

This directory contains the final evidence gate synthesis for the v9 manuscript revision. The verdict is conditional pass for manuscript-only revision after P0 actions; it is not provenance certification and does not support blind/prospective, causal-ceiling, or SOTA claims.

- `STAGE1_GATE_REPORT.md` — scope, overall verdict, claim evidence/dispositions, rerun boundary, binary gate checklist, and reviewer-facing novelty narrative.
- `STAGE1_ACTION_REGISTER.csv` — prioritized P0/P1/P2 actions with owner type, acceptance criterion, and dependency.
- `CLAIM_STATUS_FINAL.csv` — final status, source artifact/locator, and disposition for reconciled claims.

CSV schemas are in the headers. IDs are unique within each register; claim statuses use accepted, limited, contradicted, and unsupported/unverifiable. Artifact paths/locators are relative to the audit root unless the locator refers to an experiment artifact explicitly named by the source audit. The action register distinguishes editorial/package actions from provenance investigation and future rerun requirements. A P2 rerun is required only if the associated stronger claim is retained; it is not needed for a correctly narrowed manuscript.
