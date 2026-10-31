# A16 — References, Related Work, and Comparative Novelty

Date: 2026-11-01. Access date for every source: 2026-11-01.

## 1. Target and journal-rule evidence

The user has confirmed that **BITS is used only as a formatting template** and that journal grade is not the
objective; the objective is a manuscript that would be *worth* a SINTA-2 placement on substance. This changes what
"journal rules" means for this phase:

- No journal-fit claim is made anywhere in the manuscript.
- BITS-specific editorial requirements (volume/DOI placeholders, template header) are treated as template furniture
  and were **not** rewritten, because the target venue is undecided.
- The rules that were checked are the accreditation instrument's article-level substance indicators, which are what
  an author can actually control.

| Rule checked | Source | Access date | What it implies for this phase |
|---|---|---|---|
| Accreditation ranking scale (SINTA 1–6; Sinta 2 = total score 70 ≤ n < 85) | `https://sinta.kemdikbud.go.id/home/faq` | 2026-11-01 | Grade is a property of the **journal**, not of a single article; an article can only be made compatible with that bar |
| Journal-level requirements (peer review, EISSN, DOI, scheduling, ethics statement) | Permenristekdikti No. 9/2018, Art. 4–6 (copy at `lldikti3.kemdiktisaintek.go.id`) | 2026-11-01 | Not author-controlled in this phase |
| Substance indicators: reference recency and primary-source ratio (instrument thresholds at >80 %) | Arjuna assessment summary (Dirjen Risbang instrument slide deck, mirrored copy) | 2026-11-01 | Author-controlled: recency and primary-source share were measured and raised |

Measured on the v10 candidate (computed from `SOURCE_LEDGER.csv`):

| Metric | Value | Instrument threshold referenced above |
|---|---|---|
| Total references | 24 | no fixed count in the instrument; 24 is conventional for this venue class |
| Published 2016 or later | 22 / 24 = **91.7 %** | > 80 % |
| Primary empirical sources (journal article, conference, workshop) | 21 / 24 = **87.5 %** | > 80 % |
| Non-primary sources | 3 ([2] preprint, [7] SoK, [16] SLR) | must stay a minority; it does |
| References added in P1 | 12 ([13]–[24]) | each has a defined role in `SOURCE_LEDGER.csv` |
| References removed | 0 | P0 citation order for [1]–[12] preserved |
| Unverifiable sources retained | 0 | all 24 resolved to a primary record |

Note on the instrument: the exact Arjuna scoring weights are applied to a journal's whole submission history, not
to one manuscript, and the slide deck used here is a **secondary** rendering of the instrument. The numbers above
are therefore reported as *compatibility measurements*, not as a predicted score. No acceptance probability is
claimed.

## 2. Independent diagnosis (formed before consulting the old review)

Reading only the v9_P0 manuscript, the literature gap was:

1. Twelve references, no dedicated related-work section. §1.1 was a single table mapping "role of each source",
   which explains why each citation exists but does not show what each study's **design** was.
2. The nearest work was cited but not differentiated at the level of protocol: `[9]` (feature trust across
   datasets) was cited once, and there was no citation at all for temporal-bias methodology in security ML.
3. The novelty claim ("audit chain") was stated, not argued against specific designs.
4. One formatting defect: a table with no number, no caption and no in-text reference.
5. Reference composition: two of twelve were Indonesian-venue classifier papers, and the newest source was 2025 —
   no 2026 source, in a field where a directly competing integrated-evaluation protocol appeared in 2026.

Cross-check against the v8 reviewer report (consulted afterwards): it independently raised the same two
substantive points — "Tabel 1 perlu diubah dari peta peran sumber menjadi perbandingan desain" and "kebaruan belum
dibedakan dari studi terdekat" — and named **Ahamed et al. (2026)** as a near-neighbour that the manuscript had not
cited. That source was therefore verified and added as `[24]`. The agreement is recorded as convergence, not as
adoption: the diagnosis above was written from the manuscript before that file was opened.

## 3. Verification of the inherited references

`CURRENT_REFERENCE_AUDIT.csv` — 12 rows. Result: 10 exact matches, 1 partial (missing page range, corrected in
P1), 1 year-attribution note.

| Ref | Issue found | Action |
|---|---|---|
| [1] PhiUSIIL | OpenAlex records 2023 online / 2024 issue | none — issue year 2024 is correct as cited |
| [2] PhreshPhish | v2 exists (2026-02-11); author list confirmed via the arXiv API | none — cited as 2025 (v1) |
| [3] Marchal & Asokan | workshop proceedings assign no page range | none |
| [7] Das et al. SoK | online 2019-12-05, issue 2020 | none — issue year 2020 as cited |
| [12] Yoga et al. | **page range absent** in v9_P0 | pages added: `pp. 1153–1163` |
| others | — | none |

No reference was found retracted, and none was found incorrect in title, authors, venue or volume.

## 4. Added sources and their roles

Twelve sources were added. Each is used for a specific sentence or comparison; none is decorative.

| Ref | Role | Used at |
|---|---|---|
| [13] TESSERACT | Spatial/temporal bias can inflate F1 to ~0.99 | §1 ¶1, §1 ¶2, §1.2 P1, Table 1 |
| [14] Transcend | Drift detected in vivo before metric decay | §1 ¶2, §1.2 P1, Table 1 |
| [15] Barbero et al. | Drift conclusions depend on the evaluation protocol | §1 ¶2, §1.2 P1, Table 1 |
| [16] Safi & Singh | Field map: 80 papers, five approach families | §1.2 P2, Table 1 |
| [17] Karim et al. | Representative recent URL-only hybrid classifier | §1.2 P2, Table 1 |
| [18] Gupta et al. | Lexical pipeline for real-time use | §1.2 P2, Table 1 |
| [19] Sánchez-Paniagua et al. | Test-set composition materially changes FPR | §1.2 P2, Table 1 |
| [20] Aljofey et al. | URL-only representation reaches high performance | §1.2 P2, Table 1 |
| [21] Axelsson | Base-rate argument for FPR interpretation | §2.6, §3.6, §3.8, §1.2 P4, Table 1 |
| [22] Saito & Rehmsmeier | PR/PPV more informative under imbalance | §2.6, §3.6, §3.8, §1.2 P4, Table 1 |
| [23] Trad & Chehab | LLM direction, explicitly not tested here | §1.2 P5, Table 1 |
| [24] Ahamed et al. | Nearest integrated study on the same corpus | §1.2 P2/P3, Table 1 |

## 5. Novelty, bounded

See `NOVELTY_CLAIM_MAP.csv` for the statement-to-source mapping. Summary:

- **Supported, not novel alone:** benchmark saturation on PhiUSIIL; FPR/PPV trade-offs under low prevalence;
  entity-disjoint splitting as a principle.
- **Partially novel:** the frozen one-direction transfer protocol on the PhiUSIIL→PhreshPhish pair with extractor,
  feature order, model and threshold all fixed before touching the target.
- **Novel as composition:** the five-context audit chain, held on one artifact, with explicit boundaries between
  descriptive and causal statements. The nearest integrated protocol `[24]` covers robustness, generalisation and
  explanation stability — not temporal evaluation, operating thresholds, or frozen cross-corpus transfer.
- **Not claimed:** model superiority, SOTA, causal mechanism, prospective/blind evaluation, universal
  generalisation, deployment readiness.

A direct consequence of `[24]` deserves emphasis: it independently reports clean-test performance of
0.9962–0.9984 on the same 235,370-URL PhiUSIIL corpus used here. That **corroborates** the saturation observation
from a second protocol while also narrowing the novelty claim — which is exactly the trade the sub-prompt asks to
report honestly rather than manufacture around.

## 6. What was not done

- No systematic-review claim. The search was targeted (OpenAlex topic search, citation-graph traversal, one
  systematic review as a map), not exhaustive, and the manuscript does not claim otherwise.
- No journal target fixed; no journal-fit statement added.
- No score comparison across corpora anywhere in the added text.
- No reference added to reach a count.
- No quotation, page number, or result was reproduced from a source without a verified record.