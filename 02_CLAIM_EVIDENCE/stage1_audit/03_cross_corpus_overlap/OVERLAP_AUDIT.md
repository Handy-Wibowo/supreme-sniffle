# Cross-corpus overlap audit

## Scope and reproducibility

The source is the **141,222-row PhiUSIIL cleaned random-split seed-42 training fold** used to fit the frozen Experiment 6 models. The target is the **PhreshPhish temporal test cohort** reconstructed from the raw test shards and joined to the Experiment 4 cleaned split by immutable `row_id`; the split cutoff is 2025-09-08 00:00 UTC. These are the source/target cohorts used by the transfer analysis, not all rows in either original corpus.

Input SHA-256 values, byte sizes, raw shard revisions, the transfer manifest comparisons, local execution environment, and PSL snapshot identity are in `OVERLAP_RESULTS.json`. All raw shards, predictions, split files, and model artifacts were read-only. No network access or downloads are used. The script imports the shared Experiment 5 canonical URL/hostname/PSL implementation.

## Overlap results and denominators

Source denominator: 141,222 rows; target denominator: 168,035 rows. Each target match proportion below is matched target rows divided by all 168,035 target rows. Unique key counts count distinct normalized values; matched-row pairs count the Cartesian pairs for common keys, so duplicate keys can produce more pairs than rows.

| Match level | Common unique keys | Source rows matched / denominator | Target rows matched / denominator | Matched row pairs | Conflicting-label keys | Conflicting-label row pairs |
|---|---:|---:|---:|---:|---:|---:|
| raw_url | 2 | 2 / 141,222 | 2 / 168,035 (0.0012%) | 2 | 2 | 2 |
| canonical_url | 262 | 262 / 141,222 | 262 / 168,035 (0.1559%) | 262 | 2 | 2 |
| hostname | 2,748 | 4,509 / 141,222 | 7,157 / 168,035 (4.2592%) | 91,004 | 45 | 4,508 |
| registrable_domain | 3,752 | 26,059 / 141,222 | 40,670 / 168,035 (24.2033%) | 1,947,144 | 159 | 181,418 |

`overlap_summary.csv` contains overall, target-class, and source/target class-pair strata for every overlap level, with row and class denominators, matched rows/pairs, and conflicting label pairs. Source label 1 is benign and source label 0 is phish; all output labels are converted to phishing-positive (`y_phish=1`). Duplicate keys within either cohort and duplicate keys among the common keys are separately counted. Full conflicting-label key cases and class-pair counts are in the JSON.

## Conservative no-overlap evaluation

A target row is excluded if it matches any source training row at any of the four levels. This removes 40,670 target rows (24.2033%); the remaining denominator is 127,365, with classes {'benign': 80369, 'phish': 46996}. This union rule is conservative: no retained row shares a raw URL, canonical URL, hostname, or registrable domain with source training data.

All 10 saved frozen prediction files (two model families × five seeds) joined one-to-one to all target row IDs and had labels verified against the cleaned target split. No model was refit, threshold changed, or target row scored anew. `no_overlap_metrics.csv` reports unchanged predictions/threshold 0.5 scored only on the strict no-overlap subset; both classes are present for these metrics.

| Model | Seed | n | F1 (phish) | Precision | Recall | Benign FPR | Phish miss | ROC-AUC | AP | MCC | TN / FP / FN / TP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| lightgbm | 13 | 127,365 | 0.4974 | 0.3452 | 0.8895 | 0.9865 | 0.1105 | 0.4350 | 0.3523 | -0.2162 | 1,086 / 79,283 / 5,195 / 41,801 |
| lightgbm | 42 | 127,365 | 0.4974 | 0.3452 | 0.8895 | 0.9865 | 0.1105 | 0.4350 | 0.3523 | -0.2162 | 1,086 / 79,283 / 5,195 / 41,801 |
| lightgbm | 2024 | 127,365 | 0.4974 | 0.3452 | 0.8895 | 0.9865 | 0.1105 | 0.4350 | 0.3523 | -0.2162 | 1,086 / 79,283 / 5,195 / 41,801 |
| lightgbm | 777 | 127,365 | 0.4974 | 0.3452 | 0.8895 | 0.9865 | 0.1105 | 0.4350 | 0.3523 | -0.2162 | 1,086 / 79,283 / 5,195 / 41,801 |
| lightgbm | 31415 | 127,365 | 0.4974 | 0.3452 | 0.8895 | 0.9865 | 0.1105 | 0.4350 | 0.3523 | -0.2162 | 1,086 / 79,283 / 5,195 / 41,801 |
| xgboost | 13 | 127,365 | 0.4994 | 0.3475 | 0.8873 | 0.9742 | 0.1127 | 0.3188 | 0.2750 | -0.1798 | 2,070 / 78,299 / 5,298 / 41,698 |
| xgboost | 42 | 127,365 | 0.4994 | 0.3475 | 0.8873 | 0.9742 | 0.1127 | 0.3188 | 0.2750 | -0.1798 | 2,070 / 78,299 / 5,298 / 41,698 |
| xgboost | 2024 | 127,365 | 0.4994 | 0.3475 | 0.8873 | 0.9742 | 0.1127 | 0.3188 | 0.2750 | -0.1798 | 2,070 / 78,299 / 5,298 / 41,698 |
| xgboost | 777 | 127,365 | 0.4994 | 0.3475 | 0.8873 | 0.9742 | 0.1127 | 0.3188 | 0.2750 | -0.1798 | 2,070 / 78,299 / 5,298 / 41,698 |
| xgboost | 31415 | 127,365 | 0.4994 | 0.3475 | 0.8873 | 0.9742 | 0.1127 | 0.3188 | 0.2750 | -0.1798 | 2,070 / 78,299 / 5,298 / 41,698 |

## Canonicalization and PSL

URL whitespace stripped; missing scheme receives http://; HTTP(S) only; scheme and hostname lowercased; trailing hostname dot removed; path defaults to /; query retained byte-for-byte; fragment removed; userinfo and explicit port retained; invalid port/host rejected.

Experiment 5 parse_url: urllib hostname lowercased and trailing dot removed.

Experiment 5 host_parts with bundled tldextract PSL; IP literals remain the IP; unknown suffix falls back to e.domain or host.

Offline PSL: {'library': 'tldextract', 'suffix_list_urls': [], 'include_psl_private_domains': False, 'snapshot_file': '.tld_set_snapshot', 'snapshot_bytes': 318581, 'snapshot_sha256': 'b69315c085d53972724b8f2df111ffc329b0c84fe0a47d62c8c91655cc774a38'}.

## Known limits

The overlap unit is the frozen source training fold, because source validation/test rows did not contribute to the transfer model. Registrable-domain grouping follows the shared PSL snapshot and excludes private suffixes, so hosting-platform tenants may share one registrable key. Label conflict means the same key occurs with different binary labels across corpora; it is not proof either label is erroneous. `raw_url` is literal string equality; canonical URL matching follows the shared extractor rather than browser/network resolution.

## Rerun

From the workspace root, in Experiment 5's recorded Python environment:

```powershell
"Experiment/5 - PhiUSIIL Focused Ablation/.venv/Scripts/python.exe" "phishing/revision_v9_stage1_audit/03_cross_corpus_overlap/overlap_audit.py" --self-check
"Experiment/5 - PhiUSIIL Focused Ablation/.venv/Scripts/python.exe" "phishing/revision_v9_stage1_audit/03_cross_corpus_overlap/overlap_audit.py"
```

The script checks file hashes against Experiment 6's frozen input manifest and fails on any mismatch or unsafe/missing row join. `--self-check` exercises canonicalization, PSL parsing, overlap union, conflicting labels, and class strata using deterministic synthetic rows.
