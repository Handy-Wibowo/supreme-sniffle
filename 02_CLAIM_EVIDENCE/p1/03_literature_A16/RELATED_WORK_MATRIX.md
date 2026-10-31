# Related work design matrix (A16)

Purpose: compare **designs**, not scores. No score is compared across corpora anywhere in this table.
"Tidak dilaporkan pada abstrak" means the information is not available in the abstract examined; it does not
assert that the study did not do it.

| Ref | Study | Corpus / domain | Split unit | Temporal design | Cross-corpus adaptation | Threshold protocol | Uncertainty | Error analysis | Nearest limitation for this paper |
|---|---|---|---|---|---|---|---|---|---|
| [3] | Marchal & Asokan (CSET 18) | Phishing webpages, real-world framing | Not reported in abstract | Discussed as a design requirement | None | Not reported in abstract | Not reported | No | Establishes protocol-as-claim; gives no cross-corpus numbers |
| [4] | El Aassal et al. (PhishBench) | Many phishing datasets, uniform conditions | Benchmark harness, dataset-dependent | No temporal design | None (harness, not transfer) | Not reported in abstract | Not reported | No | This paper does not use the PhishBench harness |
| [5] | Arp et al. | Cross-domain ML security | Entity-level independence as a principle | Time-aware sampling as a principle | None | None | None | No | Principles only; no effect size for phishing URLs |
| [6] | Kapoor & Narayanan | Cross-field ML science | Leakage taxonomy (8 types) | Time leakage as one type | None | None | None | No | Taxonomy, not an empirical phishing study |
| [7] | Das et al. (SoK) | Phishing & spear phishing | Security challenges framing | Temporal validity named | None | Base-rate fallacy named | None | No | Framework, no measurement on PhiUSIIL/PhreshPhish |
| [8] | Hannousse & Yahiouche | Website-phishing benchmark construction | Dataset-construction choices | No | None | None | No | No | Benchmark construction; not an evaluation chain |
| [9] | Mia et al. (NSysS 24) | Phishing features across diverse datasets | Dataset boundaries | No | **Yes — feature transfer across datasets** | Not reported in abstract | Not reported | XAI feature attribution | Closest transfer study; does not freeze a pipeline+threshold |
| [10] | Odeh et al. (JISIS 23) | URL phishing, boosted trees | Within-corpus | No | None | Not reported in abstract | Not reported | No | Model-family comparison only |
| [11] | Nabila et al. (BITS 25) | URL phishing, NLP + SVM | Within-corpus | No | None | Not reported in abstract | Not reported | No | Indonesian-venue context; no protocol contrast |
| [12] | Yoga et al. (BITS 25) | Website phishing, XGBoost + undersampling | Within-corpus | No | None | Not reported in abstract | Not reported | No | Indonesian-venue context; no protocol contrast |
| [13] | Pendlebury et al. (TESSERACT, USENIX 19) | Android malware, 129K apps over 3 years | Spatial and temporal constraints | **Yes — explicit time splits** | None | Not reported in abstract | Expected-robustness metric | No | Shows F1≈0.99 can be a design artefact; malware domain |
| [14] | Jordaney et al. (Transcend, USENIX 17) | Android + Windows malware | Deployment vs training samples | **Yes — drift detected in vivo** | None | Not reported in abstract | Statistical comparison | No | Detects drift; does not evaluate cross-corpus portability |
| [15] | Barbero et al. (S&P 22) | Malware, concept drift | Formal time-aware protocol | **Yes** | None | Rejection via conformal prediction | Conformal guarantee | No | Protocol-dependent conclusions; malware domain |
| [16] | Safi & Singh (JKSU-CIS 23) | Phishing website detection, 80 papers | SLR | No | No | No | No | No | Field map only; not primary evidence |
| [17] | Karim et al. (IEEE Access 23) | URL phishing, hybrid ML | Within-corpus | No | None | Not reported in abstract | Not reported | No | Very high in-corpus scores; no portability test |
| [18] | Gupta et al. (Comput. Commun. 21) | URL phishing, lexical features | Within-corpus, real-time | No | None | Feature reduction | Not reported | No | Lexical pipeline; no temporal or transfer evaluation |
| [19] | Sánchez-Paniagua et al. (IEEE Access 22) | Login-page URLs, real case | Within-corpus | No | None | **FPR-focused** | Not reported | Partial (FP behaviour) | Shows test composition changes FPR; no cross-corpus transfer |
| [20] | Aljofey et al. (Electronics 20) | URL-only, char-level CNN | Within-corpus | No | None | Not reported in abstract | Not reported | No | URL-only representation, no protocol contrast |
| [21] | Axelsson (TISSEC 00) | Intrusion detection | n/a | n/a | n/a | Base-rate argument | n/a | No | Principle only; predates phishing ML |
| [22] | Saito & Rehmsmeier (PLoS ONE 15) | Imbalanced binary classification | n/a | n/a | n/a | Precision-recall vs ROC | n/a | No | Principle only |
| [23] | Trad & Chehab (MAKE 24) | Phishing URLs, LLMs | Within-corpus | No | None | Prompt vs fine-tune | Not reported | No | LLM axis explicitly **not** tested here |
| [24] | Ahamed et al. (Front. Comput. Sci. 26) | **PhiUSIIL 235,370 URLs** + PhishTank external | Within-corpus + leave-one-family-out | No temporal split | External validation on a different source | Clean-test baseline | Robustness Degradation Index | Robustness/explanation stability | **Nearest integrated study**: robustness axis, no temporal evaluation, no operating-threshold analysis, no frozen cross-corpus transfer |

## What this paper adds, stated narrowly

1. A single auditable chain that keeps five contexts separate: benchmark saturation, within-corpus temporal
   evaluation, one-direction frozen cross-corpus transfer, validation-selected operating thresholds, and a
   descriptive error taxonomy.
2. A frozen-transfer protocol (extractor, feature order, model, threshold all fixed before the target corpus is
   touched) on the PhiUSIIL -> PhreshPhish pair, which the nearest studies do not report for this pair.
3. Explicit separation of descriptive saturation from causal claims, and of FPR from operational usefulness
   (PPV projections reported as arithmetic scenarios).

## What this paper does not add

- No new model family, architecture, or training procedure.
- No state-of-the-art claim; no cross-corpus score comparison.
- No causal mechanism for saturation or drift.
- No prospective or blind evaluation: the temporal cohort was inspected in earlier exploratory work.
- No universal generalisation from two corpora and one transfer direction.
- No adversarial-robustness evaluation (the axis of [24]) and no LLM evaluation (the axis of [23]).