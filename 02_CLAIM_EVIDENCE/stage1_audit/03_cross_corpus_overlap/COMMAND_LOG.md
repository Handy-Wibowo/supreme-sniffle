# Command log

Commands executed from workspace root; all use the pre-existing Experiment 5 Python 3.14 environment.

```powershell
"Experiment/5 - PhiUSIIL Focused Ablation/.venv/Scripts/python.exe" "phishing/revision_v9_stage1_audit/03_cross_corpus_overlap/overlap_audit.py" --self-check
"Experiment/5 - PhiUSIIL Focused Ablation/.venv/Scripts/python.exe" "phishing/revision_v9_stage1_audit/03_cross_corpus_overlap/overlap_audit.py"
```
Both commands completed successfully. The final full audit has status `completed`, all input hashes matched the frozen transfer manifest, all 10 model/seed prediction joins passed, and output assertions passed for required artifacts, 28 overlap strata, and the 127,365-row strict no-overlap metrics denominator.
The self-check covers canonicalization, PSL parsing, overlap union, conflicting labels, and class strata; final outcomes and runtime are recorded in `OVERLAP_RESULTS.json` and `WORKER_REPORT.md`.
