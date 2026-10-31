# Dual Independent Review — Gate Record

Date: 2026-11-01
Candidate reviewed: `BITS_Draft_Phishing_URL_Leakage_v10_P1_candidate.docx`, SHA-256 `9c5793609712fa03c74d9e0e76b22c4439b308f2118bc89e83b5d5b93f679089`

## 1. Reviewers and configuration

| Role | Model ID | Provider | Transport | Packet |
|---|---|---|---|---|
| Reviewer A | `gpt-6-luna` | Kenari (`https://kenari.id/v1`) | chat_completions, temp 0.2 | identical |
| Reviewer B | `glm-5-3-flash` | Kenari | chat_completions, temp 0.2 | identical |

Requested pair was `gpt-6-luna` + `glm-5.3`. Kenari's API key rejects `glm-5-3`:
`model 'glm-5-3' is not allowed by this key. Allowed models: deepseek-v4-1-flash, glm-5-3-flash,
mimo-v2-6-flash, gpt-5-6-luna, gpt-6-luna, deepseek-v4-flash`.
The GLM 5.3 family model permitted by this key is `glm-5-3-flash`, which was used. That substitution is
recorded here rather than silently made.

Both reviewers received the same system role, the same seven criteria (C1–C7), and the same manuscript
text extraction (200 paragraphs + 9 tables, 69,446 characters). Neither saw the other's output, and
neither saw any earlier review. Each call was independent and stateless.

## 2. Gate rule

Hard pass/block: both reviewers must return `OVERALL: APPROVE`; any `BLOCK` from either blocks the phase.

## 3. Round 1 (packet v1) — superseded

| Reviewer | Verdict | Notes |
|---|---|---|
| gpt-6-luna | BLOCK | C1, C3, C4, C6, C7 |
| glm-5-3-flash | *(API error)* | `glm-5-3` not permitted by key |

The round-1 packet did not state that the manuscript contains two embedded figures, so Reviewer A scored
"figures missing" against an extraction artefact. The packet was corrected for both reviewers equally and
both were re-run. Round-2 (pre-fix) outputs are archived under `v1_rejected/`; the round-1 Reviewer A file was overwritten by the corrected-packet run.

## 4. Round 2 (packet v2, corrected) — findings acted on

| Reviewer | Verdict | Criteria blocked |
|---|---|---|
| gpt-6-luna | BLOCK | C1, C3(i), C4, C6 |
| glm-5-3-flash | BLOCK | C1, C3(i) |

Reviewer B identified a substantive defect that Reviewer A had missed: **Table 6 and Table 8 reported
different metrics for what appeared to be the same run**. Verified against artifacts, both tables are
numerically correct but describe **different models**:

- Table 6 (Experiment 4 canonical run): model trained on the entire pre-cutoff block, 497,359 rows
  (fit **and** validation periods), threshold 0.5 → F1 0,801768, FP 5.630, FN 21.636.
- Table 8 (Experiment 7): model **retrained on the fit block only**, 372,213 rows, thresholds frozen on
  the 125,146-row validation block → at 0.5: F1 0,806999, FP 6,981, FN 20,119.
- Test rows are identical (168,035; 91,259 benign / 76,776 phishing).
- Table 9's confusion matrix reproduces Table 6 exactly, confirming the split between the two runs.

The manuscript never said this. Six corrections were integrated and registered as P1-020…P1-026:
explicit `analysis sensitivitas` label for the strict no-overlap subset (C3(i)); the fit-block vs
full-pre-cutoff distinction in §2.8, in §3.8, and in both table captions (C1); the "published version"
leftover in the author statement replaced with "versi akhir manuskrip ini" (C6); and a note that the
0,004436 F1 gap is computed from unrounded values (reviewer B's rounding objection is a reviewer error —
0,9996227538821021 − 0,9951863806364146 = 0,00443637).

## 5. Round 3–5 (packet v3, current) — final gate

| Round | gpt-6-luna | glm-5-3-flash | Blocked criteria (A) |
|---|---|---|---|
| 3 | BLOCK | APPROVE | C1, C4, C6, C7 |
| 4 | BLOCK | APPROVE | C1 (AUC precision), C4 (threshold-literature attribution), C6 |
| 5 | **BLOCK** | **APPROVE** | C6, C7 only — C1, C2, C3, C4, C5 all PASS |

**Gate: BLOCK** (one BLOCK is sufficient). Both reviewers converged on approval of the science; the
remaining block is concentrated in two criteria.

### What rounds 3–5 changed

- **P1-027** corrected a factual timing claim: the manuscript said temporal training took "single-digit to
  teens of seconds"; the artifact records 6,06–7,21 s fit and 0,79–0,84 s batch prediction.
- **P1-028** added the configuration paragraph that was missing from the manuscript but present in
  `design.json` / `data.py`: LightGBM 300 estimators / 0,05 / 63 leaves, XGBoost 300 / 0,05 / depth 8,
  library versions, and the Public Suffix List snapshot SHA-256.
- **P1-029** added **Tabel 10**, a traceability table mapping every prose-only figure (cross-protocol delta
  endpoints, A0→A1 error counts, transfer bootstrap intervals, timing ranges) to its source artifact.
- **P1-030** stated the reporting precision behind "di atas 0,988", after Reviewer A noted that the displayed
  value 0,9880 does not by itself prove "above 0,988".
- **P1-012 (revised)** fixed a real misattribution: the sentence claimed that "literatur ambang operasional"
  treats threshold choice as a cost decision, but [21] is the base-rate argument and [22] is precision-recall
  vs ROC. The sentence now attributes each source to what it actually supports and states that cost-sensitive
  threshold literature was not synthesised.

### Reviewer A's final C6/C7 objections

| # | Objection | Assessment | Owner |
|---|---|---|---|
| A-1 | A0/A1 producer provenance unknown | **Disclosed limitation**, not a defect. A14 recovered only that the fields ship with the public CSV; producer, reference population, timing and label dependency do not exist in any accessible artifact. Manufacturing certainty would be fabrication. | data provider |
| A-2 | No repository URL / artefact access route | **Valid**, but the package is local and publishing it is the author's decision. | user |
| A-3 | Temporal cohort was previously inspected | **Disclosed limitation**. Fixing it requires a genuinely new prospective cohort — an experiment the handoff explicitly forbids without authorization. | user (authorisation) |
| A-4 | Split-formation detail still incomplete in the text | Partly addressed by P1-028; the remaining detail is in `design.json` and the included pipeline source. | authors (optional) |
| A-5 | External validity narrow, one-direction transfer | **Disclosed limitation** and the paper's stated scope; adding the reverse direction is a new experiment. | user (authorisation) |

No actionable text defect remains that the agent may fix without either fabricating provenance or running an
unauthorised experiment. The reviewer is asking for work outside this paper's declared scope, plus inputs only
the author can supply.

### Reviewer B

Approved in rounds 3, 4 and 5 on the same artifacts, with no blocking criteria.

## 6. What this means

The manuscript improved materially as a result of the gate. Two genuine defects were found that the
single-agent QA pass had not detected: the Table 6 / Table 8 cross-model inconsistency (Reviewer B) and the
misattributed threshold literature (Reviewer A). A factual timing error was also found and corrected.

The phase is nevertheless **not cleared**, and the blocking items are not things the agent may decide:

1. **Provenance and cohort limits** are disclosed limitations of the bounded paper. Removing them requires a
   new prospective cohort or producer access — both excluded by the handoff without explicit authorisation.
2. **Repository/access route** and **author metadata** belong to the user.

Recorded reviewer errors (not acted on): reference [24] is not "future-dated" (published 2026-08-31; today is
2026-11-01); the 0,004436 value is exact from unrounded metrics rather than a rounding error; and the round-1
"figures absent" finding was an extraction artefact, corrected in the packet for both reviewers.

## 7. Remediation path

1. User fills author block, CRediT, funding confirmation, AI disclosure, and (if desired) a repository URL.
2. If a prospective claim or reverse-direction transfer is wanted, that requires explicit authorisation and a
   new experiment; otherwise the disclosed limitations stay.
3. Both reviewers re-run on the new candidate; the gate passes only if both return APPROVE.

## 8. Files

- `gpt-6-luna_review.md`, `glm-5-3-flash_review.md` — round-5 (final) outputs
- `VERDICTS.json` — machine-readable round-5 verdicts
- `v1_rejected/` — pre-fix outputs, retained for audit
- `MANUSCRIPT_TEXT.txt` — the exact packet text both reviewers saw
- `run_reviewers.py` — the harness (identical packet, separate calls)