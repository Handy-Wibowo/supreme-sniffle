# Audit environment

The overlap audit runs in the existing local Experiment 5 Python environment; no new packages, datasets, PSL files, or network downloads are required.

- Python executable: `Experiment/5 - PhiUSIIL Focused Ablation/.venv/Scripts/python.exe`
- Python, installed package versions, OS, input paths/sizes/SHA-256 values, transfer-manifest comparisons, and PSL snapshot identity are captured in `OVERLAP_RESULTS.json`.
- All corpus, prediction, manifest, and source utility files are read-only. This output directory is the only write destination.

Reproducible invocation from workspace root:

```powershell
"Experiment/5 - PhiUSIIL Focused Ablation/.venv/Scripts/python.exe" "phishing/revision_v9_stage1_audit/03_cross_corpus_overlap/overlap_audit.py" --self-check
"Experiment/5 - PhiUSIIL Focused Ablation/.venv/Scripts/python.exe" "phishing/revision_v9_stage1_audit/03_cross_corpus_overlap/overlap_audit.py"
```
