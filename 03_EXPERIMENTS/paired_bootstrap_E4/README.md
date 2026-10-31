# Experiment 5 - PhiUSIIL Focused Ablation

Pipeline for the two-dataset ablation study in
`E:\Kuliah\Tugas Akhir\phishing\PROTOKOL_EKSPERIMEN_SINTA2_v1.md` (v1, 25 Oct 2026).

Status: **execution complete**. The data-audit notebook has been executed and the
60 + 10 fit matrix has been run once, self-checked, and summarised. Results are
citable as the pipeline's output; they are not a manuscript claim. See `report.md`
for the Indonesian summary and `preflight_report.md` §11 for the raw numbers.

## 1. What the experiment asks

Main question: how much does detection performance on PhiUSIIL depend on a group of
content features once train and test domains are separated?

| Arm | Dataset | Configs | Protocols | Models | Seeds | Fits |
|---|---|---|---|---|---|---|
| Ablation | PhiUSIIL (clean parquet) | A0 (47), A1 (41), A2 (18) | random, site-disjoint | lightgbm, xgboost | 13, 42, 2024, 777, 31415 | 60 |
| Temporal | PhreshPhish (URL-only) | A2 (18) | temporal (vendor split + cutoff purge) | lightgbm, xgboost | same 5 | 10 |

* `A0` = the 47 legacy PhiUSIIL columns as distributed in the cleaned parquet. They
  include precomputed page/content-derived fields (`LineOfCode`, `NoOfImage`,
  `HasPasswordField`, ...), so A0 is **not** computable from the URL alone.
* `A1` = A0 minus the six content features `LineOfCode`, `NoOfExternalRef`,
  `NoOfImage`, `NoOfSelfRef`, `NoOfJS`, `NoOfCSS` (41 columns).
* `A2` = 18 features recomputed from the raw URL by one shared extractor
  (`src/features.py`) used for both datasets. **A2 is a reimplementation, not the
  parquet columns.** Exact agreement with the source columns is not expected; the
  measured per-feature agreement is in
  `outputs/audit/audit_20261024T214912326638Z/a2_vs_source_agreement.csv`.
  Several features agree on 0% of rows by exact value (e.g. `NoOfLettersInURL`,
  `LetterRatioInURL`), so A2-vs-A0 comparisons mix a representation change with a
  definition change and must be described that way.
* Positive class is phishing in every artifact (`y_phish = 1`); threshold is fixed at
  `p_phish >= 0.5`, never tuned.

Primary comparison: paired domain bootstrap of **A1 − A0** on the site-disjoint arm,
primary seed 42 (PhiUSIIL) and seed 13 (PhreshPhish), 1000 replicates, seed 42.

## 2. Inputs (read-only)

| Input | Path | Verified |
|---|---|---|
| Clean PhiUSIIL table | `Experiment\1 - PhiUSIIL Cleaning + Leakage-Audit Notebook\phiusill_clean\phiusiil_clean.parquet` | 235,370 rows, 56 columns, sha256 `4c86b580ddc694c1a6bd2b0f249b43550508b2935be85c09b34dbaf67273468f` |
| Random split | same folder, `split_random.csv` | sha256 `9520d9bd891c2fe443732a64d0484d52f32c434afa1cc61bd1c21f669a117ab3` |
| Site-disjoint split | same folder, `split_sitedisjoint.csv` | sha256 `be6f046d300aeeb443057d7172962ed9f4a8c6458c588ed069bd5cbf34999044` |
| PhreshPhish shards | `dataset\PhreshPhish` (56 train + 21 test Parquet shards) | per-shard size/sha256/rows in `outputs/audit/audit_20261024T214912326638Z/phresh_shard_manifest.csv` |

PhreshPhish shards are read with the PyArrow Parquet engine, and only
`url`, `label`, `date` are loaded; the `html` column is never read.

Split files carry `train`/`val`/`test`; **`val` is not used for training** — models are
fit on `train` only and evaluated on `test` (`val_used_for_training = False` in
`split_audit.csv`).

## 3. Environment

Isolated venv, never global Python:

```sh
py -3.14 -m venv ".venv"
".venv/Scripts/python.exe" -m pip install -r env/pip_freeze.txt
```

Recorded environment: Python 3.14.7, Windows 11 (10.0.22631), 16 logical CPUs,
threads capped at 4 per fit and fits run **sequentially**.
Full versions in `env/pip_freeze.txt`; human summary in `env/ENVIRONMENT.md`;
per-run snapshot in each run's `environment.json`.

Caveat: this venv has `include-system-site-packages true`, so most scientific
packages resolve from the global user site-packages rather than `.venv\Lib\site-packages`
(see `environment.json.package_origins`). Versions match the pins, but the venv is not
hermetic; `env/ENVIRONMENT.md` has the clean-venv reproduction command.

## 4. Reproduction order

All commands run from this directory with the venv interpreter.

```sh
# 0. static unit checks (no data, no training)
".venv/Scripts/python.exe" -m src.selfcheck

# 1. reuse evidence for the PhreshPhish arm (feature + probability parity, ~60 s)
".venv/Scripts/python.exe" -m src.preflight_check

# 2. data audit notebook, fresh kernel, outputs saved
".venv/Scripts/python.exe" _execute_notebook.py notebooks/01_data_audit.ipynb \
    notebooks/01_data_audit.executed.ipynb

# 3. plan the fit matrix without training
".venv/Scripts/python.exe" -m src.run_experiment plan --dataset phiusiil
".venv/Scripts/python.exe" -m src.run_experiment plan --dataset phreshphish

# 4. training, launched ONCE through the notebooks (on a clean tree each notebook runs
#    the fit matrix itself and analyses the run it just produced; with
#    outputs/main_run_ids.json already holding a completed/final run of the right fit
#    count the notebook reuses that run instead of retraining - do not also call
#    `run_experiment run` or the same 70 fits are paid for twice)
".venv/Scripts/python.exe" _execute_notebook.py notebooks/02_phiusiil_ablation.ipynb \
    notebooks/02_phiusiil_ablation.executed.ipynb
".venv/Scripts/python.exe" _execute_notebook.py notebooks/03_phreshphish_temporal.ipynb \
    notebooks/03_phreshphish_temporal.executed.ipynb

# 5. verify each finished run against its own predictions
".venv/Scripts/python.exe" -m src.selfcheck outputs/<run_id>

# 6. cross-run analysis notebook: it builds the summary itself from the two run
#    ids recorded in outputs/main_run_ids.json by notebooks 02 and 03
".venv/Scripts/python.exe" _execute_notebook.py notebooks/04_analysis_summary.ipynb \
    notebooks/04_analysis_summary.executed.ipynb
```

`run` writes `outputs/<run_id>/`; `summarize` writes `outputs/summary_<run_id>/`.
Notebooks 02 and 03 record the run id they just produced in `outputs/main_run_ids.json`
and reuse that run instead of retraining when it is still `completed` / `final` with the
expected fit count, so the analysed run is always the one that notebook produced - never
"the newest directory". Notebook 04 passes those two ids explicitly to
`summarize_all(run_ids=...)`, which is the same code path as the manual
`run_experiment summarize --phiusiil-run <id> --phresh-run <id>`; run only one of the
two, or two summary directories are written.
`select_runs` refuses to guess: two completed final runs for one dataset, a non-final
run, or an unknown id all raise instead of silently entering a table.
`--train-shards` / `--test-shards` produce diagnostic runs (`final: false`) that are
excluded from every summary and must never be cited.

## 5. Outputs per run

`design.json` (command, seeds, threshold, cutoff, code+protocol hashes),
`environment.json`, `input_manifest.json`, `feature_groups.json`,
`feature_provenance.csv`, `row_ledger.csv`, `excluded_rows.csv`,
`split_audit.csv`, `predictions_<dataset>_<protocol>_<config>_<model>_seed<seed>.csv.gz`,
`metrics_per_run.csv`, `report.md`, `execution.log`, `run_status.json`.
`run_registry.csv` at the experiment root logs every run's start/end, duration,
status, fit count and paths.

Undefined metrics (e.g. precision when no positive prediction exists) are written as
NaN with a reason string in `metrics_per_run.csv`; they are never silently replaced.

## 6. Known limits

* "Site-disjoint" separates registrable domains, which is not a tenant boundary:
  `web.app`, `firebaseapp.com`, `repl.co`, `weeblysite.com`, `ipfs.io` host many
  independent tenants. Top-10 domain keys hold 25,029 rows (10.63%); 120 keys carry
  both labels across 1,372 rows (0.58%). See `domain_concentration.csv`.
* The random split has 0 exact-URL overlap but **153-173 test rows per seed share a
  canonical URL key with train** (0.33-0.37%; 680 duplicate canonical keys survive in
  the clean table because cleaning deduplicated exact strings only). Site-disjoint is
  0 on both counts, which is why the paired A1-A0 analysis is only defined there.
  Reported as `train_test_canonical_overlap` / `test_rows_sharing_canonical_key_with_train`
  in `split_audit.csv`; the frozen split files are not modified.
* The temporal arm uses the vendor's own train/test split plus a cutoff purge; it
  measures temporal + population shift together and cannot separate them.
* PhreshPhish prevalence differs from PhiUSIIL; base-rate projection is reported
  separately and is a sensitivity analysis, not a corrected performance claim.
* A2 is a reimplementation (see §1); cross-dataset feature equality is not claimed.

## 7. Current state

Executed:

* `01_data_audit.executed.ipynb` - 18 code cells, execution counts 1-18, zero errors,
  run `audit_20261024T214912326638Z`.
* `python -m src.preflight_check` - PhreshPhish reuse evidence, run
  `parity_20261024T213905075671Z`: 0/90,000 differing feature cells against the legacy
  extractor and max abs probability difference 7.85e-14 against
  `Experiment/4 .../predictions_seed_13.csv.gz`.
* One smoke run (`outputs/smoke/smoke_20261024T215811.694719Z/`, 60 fits on a stratified
  subsample) verified by `python -m src.selfcheck` with `max_f1_diff = 0.0`; the run's
  `design.json` carries `final: false` and a do-not-cite warning.
* `outputs/smoke/smoke_20261025T045355.841559Z/` - a 300-row probe used to verify the
  stdout/exit-code contract before the main runs; `final: false`, never cited.

Two earlier smoke directories (`smoke_20261024T194610.106930Z`,
`smoke_20261024T200528.200104Z`) and their registry rows were deleted during preflight,
against the documentation requirement. They are not recoverable and no output from them
is reconstructed or cited; the incident, the reason and the surviving evidence are
recorded in `PREFLIGHT_INCIDENT.md`. From that point on no run directory, log or registry
row is removed: superseded runs are relabelled, never deleted.

* `02_phiusiil_ablation.executed.ipynb` - 8 code cells, counts 1-8, zero errors,
  `execution_seconds: 27.5`, `status: completed`. It did **not** train: it took the
  reuse branch and printed `reusing recorded main run 20261025T050131000106Z - no
  retraining`. The 60 PhiUSIIL fits were trained by the *first* execution of this
  notebook, in run `outputs/20261025T050131000106Z/` (251.03 s, 4 threads,
  `final: true`); that execution then failed in post-training run discovery and its
  `.executed.ipynb` / `.status.json` were overwritten by the 27.5 s reuse execution.
  The preservation instruction (`msg_aa2644949dd8`) arrived only after that overwrite, so
  the failed record could not be saved or reconstructed; the loss is permanent and no
  artifact here stands in for it. See `PREFLIGHT_INCIDENT.md` incident 2 and its
  "Recovery limit" section. `python -m src.selfcheck` on that run reports
  60 fits and `max_f1_diff = 0.0`.
* `03_phreshphish_temporal.executed.ipynb` - 7 code cells, counts 1-7, zero errors,
  single execution. It ran the fit matrix itself and trained the 10 temporal fits in run
  `outputs/20261025T050850736450Z/` (168.5 s, `final: true`); `selfcheck` reports 10
  fits, `max_f1_diff = 0.0`.
* `04_analysis_summary.executed.ipynb` - 6 code cells, counts 1-6, zero errors. Built
  `outputs/summary_20261025T051222767276Z/` from exactly those two run ids (70 fits:
  60 + 10), with `paired_bootstrap.csv` (site-disjoint A1-A0, 1000 replicates,
  35,100 domains) and `bootstrap_temporal.csv`.
* Both training notebooks read `outputs/main_run_ids.json` first and reuse the recorded
  run when it is still `completed` / `final` / correct fit count, so re-executing a
  notebook never pays for the matrix twice.

Diagnostic-only runs under `outputs/` (smoke, shard-limited, parity, timing) are labelled
`final: false` and excluded from summaries; none of them is a study result. The four
pre-existing PhreshPhish diagnostic runs are preserved and excluded by explicit id.

Fitted matrices are `float64`. `float32` rounding moved one phishing test row across the
0.5 threshold on the site-disjoint seed-42 A0 fit, so the dtype is fixed rather than
incidental; see `preflight_report.md` §5.

Readiness verdict, verified counts and the design decisions resolved before the main fits:
`preflight_report.md`.
Independent reviews: `reviews/preflight_review.md` (pre-execution) and
`reviews/final_review.md` (recomputed all 70 fits independently from saved predictions,
verdict PASS; its `reviews/scripts/` and `reviews/audit_outputs/` are kept).
