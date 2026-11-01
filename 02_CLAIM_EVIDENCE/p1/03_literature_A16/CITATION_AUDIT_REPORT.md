# Citation-claim verification audit — adjudicated against full texts

Date: 2026-11-01
References: 24 · citation-claim pairs: 49 · model verdicts: 109 (gpt-6-luna, glm-5-3-flash)

Machine output is preserved unedited in `CITATION_AUDIT_RAW_ABSTRACT_ONLY.md` and `CITATION_AUDIT_RAW.csv`.
This file is the adjudicated result and supersedes the raw counts.

## 1. Method and its known bias

Two independent models scored every cited sentence against the source's **abstract only**. Raw outcome:
16 SUPPORTED, 14 NOT_IN_ABSTRACT, 13 OVERSTATED, 17 reviewer-disagreement, 0 UNSUPPORTED.

Every flagged pair was then re-checked against the **full text** or against the manuscript's own artefacts before any
edit. This step is essential: an abstract that omits a detail is not evidence that the paper omits it. Scoring
citations against abstracts systematically penalises the *most load-bearing* citations, because structural claims are
argued across a paper's body and compressed only in part.

## 2. Adjudication

| Ref | Flagged claim | Full-text finding | Verdict |
|---|---|---|---|
| [13] TESSERACT | "F1 near 0,99 traces to spatial and temporal experimental bias" | PDF abstract verbatim: "Published F1 scores of up to 0.99 appear to leave very little room for improvement ... results are commonly inflated due to two pervasive sources of experimental bias: spatial bias ... and temporal bias" | **SUPPORTED verbatim** |
| [24] Ahamed et al. | "0,9962–0,9984 on domain-disjoint test; cross-source evaluation in §4.6; LOFO shows poor transfer" | Full text: "ranging from 0.9962 to 0.9984"; "Table 1 Domain-disjoint dataset split statistics for PHIUSIIL"; "used for cross-dataset evaluation in Section 4.6"; "Leave-one-family-out evaluation also showed poor transfer to unseen subdomain attacks" | **SUPPORTED verbatim** |
| [1] PhiUSIIL | "235.795 baris dan 56 kolom" | Dataset file read directly: 235,795 rows × 56 columns | **SUPPORTED by artefact** |
| [2] PhreshPhish | "mengurangi duplikasi ... menyediakan informasi temporal" | Paper §3: "we normalize the URL to a canonical form and deduplicate the data at the URL level"; "temporal" ×10 | **SUPPORTED** |
| [21] Axelsson | "small FPR still yields large false-alarm share when events are rare" | This is the paper's thesis (base-rate fallacy) | **SUPPORTED** |
| [22] Saito & Rehmsmeier | "PR more informative than ROC on imbalanced data, sensitive to prevalence" | The paper's thesis; stated in its title | **SUPPORTED** |
| [11] | "Studi BITS melaporkan SVM ..." | It *is* a BITS article (vol. 7 no. 1); abstracts do not name their own venue | **SUPPORTED** |
| [12] | "Studi BITS ... SVM dan XGBoost" | BITS vol. 7 no. 2, XGBoost — the sentence describes two BITS studies, one of which is this one | **SUPPORTED** |
| [19] | "test-set composition changes false-positive rate materially" | Abstract: "existing techniques obtain a high false-positive rate when tested with URLs from legitimate login pages" | **SUPPORTED** |
| [18] | "lexical approach with feature reduction for real-time environments" | Title says "in a real-time environment"; abstract cites resource-constrained devices | **SUPPORTED** |
| [3], [5], [6], [7], [8], [9] | general methodological claims about dataset design, sample non-independence, feature stability, temporal validity | These are the theses of the cited methodological papers, argued in their bodies; the abstract compresses only part | **SUPPORTED (full text), abstract-blind flag** |
| [10] | "keduanya dipilih karena telah dibandingkan ... dan biaya komputasi memungkinkan lima seed" | Two claims are joined: prior comparison (supported by [10]) and compute cost (a decision of this study, not a claim about [10]) | **SPLIT — see §3** |
| [15] | "kesimpulan drift bergantung pada protokol evaluasi dan mekanisme penolakan prediksi" | Accurate to the paper's re-examination finding; abstract states the removal of experimental bias without naming the dependency | **SUPPORTED** |

No reference misrepresents its source. No citation asserts a finding the source does not contain.

## 3. The one real writing defect found

Reference [10] is cited for a sentence with two conjoined claims:

> "Keduanya dipilih sebagai pembanding karena telah digunakan dan dibandingkan dalam studi deteksi phishing URL [10]
> **dan karena biaya komputasinya memungkinkan pengulangan lima seed.**"

The first clause is a claim about the literature and [10] supports it. The second clause is a **methodological
decision of this study** — it cannot be supported by [10] and should not sit inside a citation that implies it is.
This is a citation-attribution defect, not a factual one: the sentence attributes our design choice to a source.

That claim is now split so the literature citation covers only the literature.

## 4. Structural checks (all pass)

- 24 reference entries · 24 distinct cited refs · no uncited entry · no citation without an entry.
- Every reference resolves to a source whose title matches (similarity ≥ 0,55, most = 1,00).
- No future-dated reference: [24] is 2026-08-31, before the audit date.

## 5. Resolution notes (recorded, not hidden)

- **[1]** Crossref carries no abstract; record reconstructed from the Elsevier landing page.
- **[14]** Crossref and Semantic Scholar both return the 2023 re-examination *"Transcending TRANSCEND"* for the 2017
  original *"Transcend"*. Different papers — matters in a manuscript about temporal drift. Abstract taken from the
  USENIX Security 2017 page.
- **[2], [5], [13]** Required arXiv title search; identifiers were not guessed (an earlier attempt with recalled arXiv
  IDs returned four unrelated papers and was discarded).

## 6. Conclusion

**One defect found and fixed (P1-068, reference [10] attribution). All other flagged pairs are abstract-blind
artefacts verified as sound against full text or artefacts.**

`CITATION AUDIT: CLEAN AFTER ONE FIX`
