## C1 Claim-evidence consistency — BLOCK

Most headline numbers reproduce from tables (37.1% FN = 8.035/21.636; 21.8% FPR = 1.761/8.082; PPV projections at P115 recompute correctly; Table 7 counts 90.025/91.259 and 71.327/76.776 match). However, **Table 6 and Table 8 cannot both be correct for the same run**. Table 6 claims seed 13 LightGBM temporal, and Table 8's "Bawaan 0,5" row claims seed 13 LightGBM on the identical test cohort (168.035 rows, confirmed at P074/P106/P123) at the same threshold 0.5 — yet Table 6 reports F1 0,801768 / FPR 0,061693 / recall 0,718193 while Table 8 reports F1 0,806999 / FPR 0,076497 / recall 0,737952. The taxonomy confusion matrix at P130 (TN=85.629, FP=5.630, FN=21.636, TP=55.140) is consistent with Table 6 and inconsistent with Table 8 (FN 20.119, FP 6.981). One of the three is mislabeled or miscomputed; as written the manuscript contradicts itself. Also a minor rounding error: P104 states the A0−A2 F1 gap as 0,004436, but 0,999623−0,995186 = 0,004437.

Evidence: [P107] vs [P123] vs [P130]; Table 6, Table 8, Table 9.

## C2 Boundary discipline — PASS

The manuscript is unusually disciplined: saturation is repeatedly labelled descriptive without causal mechanism ([P009], [P081], [P091], [P135]); the temporal cohort is explicitly stated not to be blind/prospective ([P009], [P029], [P074]); no SOTA, new-model, or deployment-readiness claim appears ([P031], [P138], [P144]); PPV figures are labelled arithmetic scenarios ([P069], [P115]). No boundary-crossing sentence found.

## C3 Preserved corrections — BLOCK

Items (a)–(h) verified: polarity mapping and E3 disclaimers at [P046]/[P066]; bootstrap seed 42 vs model seed 13 distinguished at [P067]; platform-cluster interval absent and labelled unverified at [P133]/[P143]; 37.1% descriptive at [P133]/T9; 85 as selected reported fits at [P041]; A0/A1 producer provenance unknown at [P061]/[P083]; A2 as contract not value equality at [P060]. However, item (i) is **not** satisfied: the strict no-overlap subset is mentioned only as an object sharing the platform-key limitation ([P053]: "subset tanpa tumpang tindih ketat berbasis kunci registrable domain… penyewa independen pada platform bersama dapat memiliki kunci yang sama") and is nowhere framed as a sensitivity analysis. This required corrective statement is missing from the text.

## C4 Literature use — PASS

Citations are attached to supportable statements and Table 1 carefully bounds what each source is used for, explicitly refusing to assert "did not do" claims ([P019]). Comparative claims are bounded by corpus/protocol differences ([P135]). No obviously missing near-neighbour: cross-dataset transfer [9], PhiUSIIL-specific evaluation [24], temporal malware methodology [13]–[15], and LLM detection [23] cover the expected neighbourhood.

## C5 Novelty framing — PASS

The contribution is stated as an auditable, evidence-bounded evaluation chain, explicitly "bukan model baru atau klaim state-of-the-art" ([P009], [P031], [P141]–[P144]). Defensible against [9] and [24], both of which are distinguished on protocol and corpus pair ([T1], [P025]).

## C6 Internal consistency and presentation — PASS

Figure/Table numbering is sequential; Gambar 1/2 captions present with appropriate disclaimers; bilingual abstracts agree in content and numbers; limitations section is substantive ([P139]); CRediT, funding, data-availability, ethics and AI-use statements all present (Section 5). Minor notes: reference [24] carries a 2026 publication year (verify with the editor); the data-availability section describes an audit bundle that is explicitly not fully reproducible ([P164]), which the reviewer accepts as disclosed but flags for editorial awareness.

## C7 Rejection risk — five highest-risk issues

1. **High** — Contradictory metrics for the nominally identical run (LightGBM/A2 seed 13, threshold 0.5, same 168.035-row test cohort): F1 0,801768/FPR 0,061693/recall 0,718193 (Table 6, P107) vs F1 0,806999/FPR 0,076497/recall 0,737952 (Table 8, P123–P126); the abstract quotes recall 0,7380 at threshold 0.5, i.e., the Table 8 version. Fix: identify the actual seed/configuration of each table, relabel, and reconcile with the P130 confusion matrix before resubmission.
2. **High** — Missing required corrective statement that strict no-overlap scoring is a sensitivity analysis; only a limitation mention exists ([P053]). Fix: add one sentence in §2.3 or §3.1 framing the strict-subset scoring explicitly as a sensitivity analysis.
3. **Medium** — Rounding inconsistency 0,004436 vs 0,004437 ([P104]). Fix: recompute and report 0,004437 or state rounding convention.
4. **Medium** — Reference [24] dated 2026, a future-dated citation ([P199]). Fix: verify volume/year with the publisher and correct.
5. **Low** — Abstract states test FPR "1,1352%" while Table 8 shows 0,011352 (=1,1352%); consistent, but the mixed percentage/fraction conventions across abstract, §2.6 and tables invite misreading ([P009], [P066], T8). Fix: adopt one convention per section.

OVERALL: BLOCK