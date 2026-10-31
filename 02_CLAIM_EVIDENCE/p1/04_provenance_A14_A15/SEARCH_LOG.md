# Search log — A14/A15 read-only recovery

All commands were read-only. Working root: `E:\Kuliah\Tugas Akhir`.

| # | Command / path | Purpose | Result |
|---|---|---|---|
| 1 | `find . -path "*Exp8*" -type f` | Locate E8 evidence | 3 files under `phishing/AI_Review_SINTA2_Package_v8/03_Experiments/Exp8_Error_Taxonomy/` |
| 2 | `grep -rn -i "cluster" --include=*.py --include=*.ipynb --include=*.md .../Exp8_Error_Taxonomy` | Look for cluster resampling code | 0 hits |
| 3 | `grep -rln -i "TLDLegitimateProb" --include=*.md --include=*.py .` | Find any derivation of the stored statistical features | Only schema lists, audits, and notes; no derivation code |
| 4 | `grep -n -i "TLDLegitimateProb\|producer\|dihitung" "Experiment/5 - PhiUSIIL Focused Ablation/src/data.py"` | Check ablation data loader | Feature-name list only (line 40) |
| 5 | `zipfile.ZipFile('phiusiil+phishing+url+dataset.zip').infolist()` | Inspect the public distribution | One member: `PhiUSIIL_Phishing_URL_Dataset.csv` (56,854,345 bytes) |
| 6 | `head -1 PhiUSIIL_Phishing_URL_Dataset.csv` | Enumerate delivered columns | 56 columns; `CharContinuationRate` (9), `TLDLegitimateProb` (10), `URLCharProb` (11) are shipped |
| 7 | `find . -iname "*phiusiil*" -maxdepth 6` | Locate dataset copies and audits | `dataset/PhiUSIIL Phishing/`, `Experiment/1 .../phiusill_clean/phiusiil_leakage_audit.md` |
| 8 | `find . -path "*Exp8*" -o -iname "readme*" -path "*data*"` | Look for a data dictionary or producer readme | No PhiUSIIL-specific readme or data dictionary |
| 9 | `revision_v9_stage1_audit/02_label_feature_provenance/*` (read) | Reuse the canonical provenance audit | Rows 17–19 and page-derived rows are `UNKNOWN` |

Not done (deliberately): no model refit, no new bootstrap, no new interval computation, no dataset download.