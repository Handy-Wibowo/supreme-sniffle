# Catatan: versi notebook dari audit temporal PhreshPhish

Berkas: `04_PhreshPhish_Temporal_Audit.ipynb` (38.308 B, sha256 `ce7a6d8e08184bed616bcc74d82c0a66…`)

## Apa yang dilakukan

Skrip `run_temporal.py` dipecah menjadi 9 sel (2 markdown + 7 kode) mengikuti banner
`C0`–`C6` yang sudah ada di dalam skrip itu sendiri:

| Sel | Isi | Waktu |
|---|---|---|
| 0 | Markdown: rancangan, cutoff, kebijakan baris tak-terurai | — |
| 1 | C0 — dependensi | 4,6 s |
| 2 | C1 — konfigurasi (path lokal, cutoff, seed, ambang) | 0,1 s |
| 3 | C2 — fungsi pemuatan, pemisahan, dan pembersihan | 0,0 s |
| 4 | C3 — audit data: pemuatan + ledger + eksklusi | 83,4 s |
| 5 | C4 — 18 fitur URL deterministik + eksposur domain | 78,7 s |
| 6 | C5 — fitting 5 seed + variasi antar-seed | 85,3 s |
| 7 | C6 — bootstrap klaster domain + bulanan + manifest | 9,0 s |
| 8 | Markdown: interpretasi dan batas klaim | — |
| | **Total** | **261 s** |

Keluaran tersimpan di dalam sel (stdout), sama seperti notebook 01–03.
Folder hasil: `outputs/20261022T235747896241Z/`.

## Perubahan yang diperlukan agar bisa jalan sebagai notebook

Hanya satu, dan itu memang keputusan yang sudah tercatat:

- `UNPARSEABLE_POLICY` bawaannya diubah dari `"raise"` menjadi `"exclude"`.
  Run yang dilaporkan memakai `exclude` (lihat `design.json` run
  `20261022T170935017991Z`, field `unparseable_url_policy`). Dengan `raise`,
  notebook berhenti pada baris latih `train:train-020.parquet:8668`.
  Batas 0,01% per partisi tetap berlaku, jadi regresi korpus tetap menggagalkan eksekusi.
- Path: `DATA_DIR` / `OUTPUT_ROOT` memakai path lokal Windows, bukan Google Drive.
  Blok `drive.mount` tidak ada.

## Bukti hasil tidak berubah

Dibandingkan dengan run skrip yang sudah dilaporkan (`20261022T170935017991Z`):

| Berkas | Verdict |
|---|---|
| `row_ledger.csv` | **identik byte-per-byte** |
| `seed_variation.csv` | **identik** |
| `cluster_bootstrap_primary_seed.csv` | **identik** |
| `actual_test_domain_exposure.csv` | **identik** |
| `monthly_descriptive_primary_seed.csv` | **identik** |
| `unparseable_urls.csv` | **identik** |
| `excluded_rows.csv` | **identik** |
| `input_manifest.json` | **identik** |
| `model_seed_{13,42,2024,777,31415}.txt` | **identik** (model LightGBM sama persis) |
| `results_per_seed.csv` | identik pada seluruh kolom metrik; berbeda hanya pada `fit_s`, `batch_predict_s`, `amortized_predict_ms_per_row` |
| `split_train.csv.gz`, `split_test.csv.gz`, `predictions_seed_*.csv.gz` | identik setelah didekompresi (isi sama; header gzip menyimpan waktu) |
| `feature_schema.json` | identik kecuali `train_extract_s` dan `test_extract_s` |

Uji determinisme terpisah: tiga kali fit LightGBM dengan `random_state=13` menghasilkan
prediksi bit-identik (`pred_sha = a346c7756dc1391f938072b3`) untuk `n_jobs` = 1, 4, dan −1.

## Angka yang dihasilkan notebook

Sama dengan yang sudah ada di naskah:

- F1 kelas phish, stratum `all`: **0,8005** (SD antar-seed 0,0012)
- Precision 0,9075 · Recall 0,7160 · FPR 0,0614 · MCC 0,6791
- Stratum `seen_domain` F1 0,7407 · `unseen_domain` F1 0,8449
- Bootstrap klaster domain (seed 13): F1 0,8018 [0,7311; 0,8496]
- Eksposur domain uji: benign 68,34% · phish 44,11%

## Catatan

`AUTHOR_RUN_PhreshPhish_Temporal.ipynb` (versi Colab) tetap ada dan tidak diubah.
Versi itu tidak memuat penanganan baris tak-terurai, sehingga akan berhenti pada
URL `train:train-020.parquet:8668` bila dijalankan apa adanya.
