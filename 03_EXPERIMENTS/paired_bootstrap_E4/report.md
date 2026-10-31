# Laporan eksperimen 5: ablasi terfokus PhiUSIIL + evaluasi temporal PhreshPhish

Tanggal: 25 Oktober 2026
Status: matriks 70 fit selesai dieksekusi, diverifikasi ulang secara independen, dan
dinyatakan **PASS** untuk dikutip ke naskah. Laporan ini **bukan** klaim kontribusi baru
dan bukan pernyataan kesiapan publikasi.

Semua angka di bawah berasal dari berkas hasil yang ada di disk dan dapat dihitung ulang
dengan perintah pada `README.md` §4. Tidak ada angka di laporan ini yang dibuat tanpa
artefak pendukung.

## 1. Run yang dipilih

| Dataset | Run | Fit | Waktu | Status |
|---|---|---|---|---|
| PhiUSIIL | `outputs/20261025T050131000106Z/` | 60 | 251,03 s | `completed`, `final: true` |
| PhreshPhish | `outputs/20261025T050850736450Z/` | 10 | 168,48 s | `completed`, `final: true` |
| Ringkasan | `outputs/summary_20261025T051222767276Z/` | 70 (dibaca) | 40,0 s | selesai |

Id kedua run tercatat di `outputs/main_run_ids.json` dan dipilih secara eksplisit oleh
notebook 04; `summarize.select_runs` menolak menebak bila ada run duplikat, run non-final,
atau id tak dikenal.

Matriks: PhiUSIIL 3 konfigurasi (A0, A1, A2) x 2 protokol (random, site-disjoint) x 2
model (LightGBM, XGBoost) x 5 seed (13, 42, 777, 2024, 31415) = 60 fit. PhreshPhish
temporal hanya A2 x 2 model x 5 seed = 10 fit.

## 2. Hasil utama PhiUSIIL (rata-rata 5 seed)

Site-disjoint (protokol utama anti-kebocoran):

| Konfigurasi | Model | F1 phish | MCC | FPR benign |
|---|---|---|---|---|
| A0 (fitur penuh) | LightGBM | 0,99962 | 0,99939 | 0,000111 |
| A0 | XGBoost | 0,99969 | 0,99950 | 0,000111 |
| A1 | LightGBM | 0,99906 | 0,99846 | 0,000296 |
| A1 | XGBoost | 0,99885 | 0,99813 | 0,000422 |
| A2 (hanya URL) | LightGBM | 0,99519 | 0,99218 | 0,000902 |
| A2 | XGBoost | 0,99489 | 0,99169 | 0,000814 |

Random split, untuk pembanding:

| Konfigurasi | Model | F1 phish | MCC | FPR benign |
|---|---|---|---|---|
| A0 | LightGBM | 0,99983 | 0,99970 | 0,000089 |
| A1 | LightGBM | 0,99933 | 0,99884 | 0,000304 |
| A2 | LightGBM | 0,99636 | 0,99368 | 0,000853 |

Pola yang terbaca: penghapusan fitur konten (A0→A1) dan pembatasan ke fitur URL saja
(A0→A2) menurunkan kinerja secara monoton, dan penurunan itu tetap ada pada pembagian
site-disjoint. Besarnya penurunan kecil dalam nilai absolut karena dataset ini sangat
mudah dipisahkan; arah dan interval kepercayaannya yang layak dilaporkan, bukan besaran desimal.

## 3. Bootstrap berpasangan A1−A0 (site-disjoint)

`outputs/summary_20261025T051222767276Z/paired_bootstrap.csv`: 1000 replikasi, seed 42,
unit `registrable_domain`, 35.100 domain, model LightGBM dan XGBoost.

| Model | Metrik | Selisih (A1−A0) | CI95% |
|---|---|---|---|
| LightGBM | F1 phish | −0,00098 | [−0,00195; −0,00032] |
| LightGBM | Recall phish | −0,00173 | [−0,00372; −0,00048] |
| LightGBM | MCC | −0,00161 | [−0,00324; −0,00052] |
| LightGBM | FPR benign | +0,00015 | [−0,00004; +0,00037] |
| XGBoost | F1 phish | −0,00118 | [−0,00223; −0,00044] |
| XGBoost | FPR benign | +0,00041 | [+0,00015; +0,00071] |

F1, recall, dan MCC mengecualikan nol pada kedua model: penghapusan fitur konten
menurunkan kinerja secara sistematis. FPR LightGBM **tidak** mengecualikan nol, jadi
pergeseran FPR untuk model itu tidak dapat diklaim sebagai efek nyata.

## 4. Hasil temporal PhreshPhish (A2, 5 seed)

| Model | F1 phish | Recall | MCC | FPR | Precision | Akurasi |
|---|---|---|---|---|---|---|
| LightGBM | 0,80046 | 0,71603 | 0,67913 | 0,06143 | 0,90746 | 0,83689 |
| XGBoost | 0,79963 | 0,71219 | 0,68003 | 0,05814 | 0,91154 | 0,83692 |

`outputs/summary_20261025T051222767276Z/bootstrap_temporal.csv` (seed 13, unit domain, 1000/1000 replikasi valid) memberi
LightGBM F1 [0,728; 0,850], MCC [0,574; 0,754], FPR [0,055; 0,069]. Interval lebar karena
jumlah domain uji kecil. Ini pembagian berbasis waktu antar-vendor, bukan jaminan
generalisasi temporal.

## 5. Verifikasi independen

`reviews/final_review.md` menyatakan **Verdict: PASS** dengan bukti:

- 60/60 fit PhiUSIIL dan 10/10 fit PhreshPhish direkomputasi ulang dari prediksi mentah:
  nol ketidakcocokan pada F1/precision/recall/MCC/FPR/akurasi/ROC-AUC
  (`reviews/audit_outputs/final_recompute_*.csv`).
- 0 registrable domain melintasi train/test pada site-disjoint; 808 baris melintas pada
  random split (memang begitu desainnya).
- Bootstrap independen (300 replikasi, seed 42) mengarah ke kesimpulan yang sama dengan
  pipeline; selaras dengan `outputs/summary_20261025T051222767276Z/paired_bootstrap.csv`.
- `python -m src.selfcheck` pada kedua run: **PASS**, `max_f1_diff = 0.0` (60 dan 10 fit).

## 6. Status eksekusi notebook

| Notebook | Eksekusi | Status |
|---|---|---|
| `notebooks/01_data_audit.executed.ipynb` | 18 sel, hitungan 1–18, nol error | selesai (tanpa `.status.json`, artefak legacy) |
| `notebooks/02_phiusiil_ablation.executed.ipynb` | 8 sel, 27,5 s | `completed`, **memakai ulang** run, tidak melatih |
| `notebooks/03_phreshphish_temporal.executed.ipynb` | 7 sel, sekali eksekusi | `completed`, melatih 10 fit sendiri |
| `notebooks/04_analysis_summary.executed.ipynb` | 6 sel, 40,0 s | `completed`, membaca 70 fit |

## 7. Dua insiden dokumentasi

Keduanya dicatat lengkap di `PREFLIGHT_INCIDENT.md`; tidak ada artefak yang direkonstruksi.

1. **Artefak smoke preflight dihapus.** Dua direktori smoke
   (`smoke_20261024T194610.106930Z`, `smoke_20261024T200528.200104Z`) beserta baris
   registry-nya dihapus saat preflight. Tidak dapat dipulihkan; tidak ada angka dari
   keduanya yang dikutip di sini. Registry lengkap hanya sejak
   `audit_20261024T214912326638Z`.
2. **Kegagalan eksekusi pertama notebook 02 tertimpa.** Eksekusi pertama melatih 60 fit
   dan selesai `05:05:43Z`, lalu gagal pada sel penemuan direktori run. Catatan
   kegagalannya ditulis `05:05:44.737Z`, kemudian tertimpa oleh eksekusi kedua
   (selesai `05:07:51Z`, 27,5 s, waktu mulai tidak tercatat di artefak mana pun) yang
   memakai cabang reuse. Karena itu
   `notebooks/02_phiusiil_ablation.executed.ipynb` yang ada sekarang menunjukkan `completed` tanpa
   pelatihan; run yang dibacanya adalah run hasil eksekusi yang gagal itu. Penyebab:
   himpunan "sebelum" memakai `p.name` alih-alih `p.parent.name`, sudah diperbaiki di
   `build_notebooks.py` baris 60/71 dan di notebook 02/03. `_execute_notebook.py` kini
   memindahkan `<dst>` lama ke `<name>.superseded-<utc>` sebelum menulis, sehingga
   kegagalan berikutnya tidak bisa menghapus rekaman sebelumnya. Batas pemulihan:
   instruksi penyimpanan (`msg_aa2644949dd8`) tiba setelah penimpaan terjadi, jadi
   tidak ada salinan yang bisa diselamatkan dan tidak ada yang direkonstruksi di sini.
   Tidak ada hasil yang terpengaruh: tidak ada fit yang dilatih ulang, tidak ada
   prediksi yang ditulis ulang.

## 8. Keterbatasan

- Dataset PhiUSIIL hampir terpisah sempurna, sehingga selisih absolut antar konfigurasi
  sangat kecil dan mudah salah dibaca; laporkan CI, bukan hanya rata-rata.
- "Site-disjoint" beroperasi pada level registrable domain; platform multi-tenant
  (mis. hosting bersama) membuat kunci grup tidak sepenuhnya independen.
- Fold `val` (20% tiap pembagian) tidak dipakai untuk pemilihan model maupun evaluasi.
- Split random memang membocorkan domain (808 baris); hanya site-disjoint yang layak
  disebut protokol anti-kebocoran.
- Temporal PhreshPhish adalah pembagian antar-vendor berbasis waktu, bukan desain
  temporal baru; FPR XGBoost identik lintas seed (sd = 0) pada split yang sama.
- Interval bootstrap menggambarkan ketidakpastian sampling domain uji untuk model tetap,
  bukan jaminan generalisasi.

## 9. Berkas rujukan

- `README.md` - lingkungan, urutan reproduksi, daftar artefak.
- `preflight_report.md` - bukti gate G1–G4, invarian hitungan confusions.
- `PREFLIGHT_INCIDENT.md` - kedua insiden, batas pemulihan, aturan ke depan.
- `env/ENVIRONMENT.md` - pin versi dan perintah venv bersih.
- `outputs/main_run_ids.json`, `run_registry.csv`, `outputs/summary_20261025T051222767276Z/`.
- `reviews/final_review.md`, `reviews/preflight_review.md`, `reviews/audit_outputs/`.

## 10. Putusan kesiapan

Langkah reproduksi dari nol telah didokumentasikan dan hasilnya dapat diaudit baris per baris.
Temuan ilmiahnya sah untuk dilaporkan sebagai bukti empiris ketergantungan model pada
representasi fitur, termasuk batas evaluasinya. Klaim kontribusi baru atau kesiapan
publikasi **tidak** didukung oleh artefak di direktori ini dan tidak boleh ditulis.
