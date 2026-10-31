# Hasil Eksekusi Evaluasi Temporal PhreshPhish

Dokumen ini mencatat eksekusi nyata notebook **AUTHOR_RUN_PhreshPhish_Temporal.ipynb**
(Jalur 2 pada `AUDIT_KEPUTUSAN_DATASET.md`) pada data mentah PhreshPhish di mesin lokal.
Seluruh angka di bawah berasal dari berkas keluaran yang dihasilkan run ini, bukan dari
laporan, probe, atau korpus lain.

| Item | Nilai |
|---|---|
| Folder run | `outputs/20261022T170935017991Z/` |
| Waktu eksekusi (dilaporkan penulis) | 194,2 detik (seluruh C0–C6) |
| Jumlah berkas keluaran | 29 berkas, 59,12 MB |
| Status keluar | `exit 0` |
| Runner | `run_temporal.py` (port lokal dari sel C0–C6) |
| Integritas input | 77 shard, 666.315 baris, 36.576.373.578 byte, sha256 per berkas di `input_manifest.json` |
| Integritas output | 28 berkas di-hash sha256 di `output_manifest.json` |
| Verifikasi independen | `VERIFIKASI_HASIL_TEMPORAL.md`: 134 pemeriksaan lulus, 0 gagal, selisih numerik maksimum 0 |

> **Catatan revisi.** Angka pada dokumen ini telah diperiksa ulang oleh verifikator
> independen. Tujuh koreksi yang diberikannya sudah diterapkan pada versi ini:
> penyebut kebijakan URL tak terurai, interpretasi Desember, deskripsi berkas split,
> deskripsi port runner, pencatatan PSL, klaim dampak satu eksklusi, dan status waktu
> eksekusi. Ringkasan koreksi ada di §8.

---

## 1. Lingkungan dan pembekuan parameter

`design.json` ditulis **sebelum** fitting pertama, sesuai syarat C1.

| Parameter | Nilai |
|---|---|
| `protocol` | `modified_temporal_url_deduplicated` |
| `training_corpus` | PhreshPhish |
| `evaluation_corpus` | PhreshPhish |
| `cutoff` | `2025-09-08 00:00:00+00:00` |
| `seeds` | `[13, 42, 2024, 777, 31415]` |
| `primary_seed` | 13 |
| `threshold` | 0.5 (tidak dituning pada test) |
| `tuning` | `none` |
| `bootstrap_replicates` | 1000 |
| `include_psl_private_domains` | `false` |
| `test_status` | `previously inspected in exploratory probes` |
| `train_shard_limit` / `test_shard_limit` | `null` / `null` (korpus penuh) |

Model LightGBM dibekukan pada `n_estimators=300, learning_rate=0.05, num_leaves=63,
n_jobs=-1, verbosity=-1`.

Versi pustaka tercatat di `design.json`: numpy 2.5.3, pandas 3.1.0, pyarrow 26.0.0,
scikit-learn 1.9.1, lightgbm 4.7.0, tldextract 5.4.0. Python 3.14.7.

---

## 2. Ledger baris: setiap baris dipertanggungjawabkan

`row_ledger.csv` mencatat setiap tahap penyaringan. Tidak ada baris yang hilang tanpa
alasan tercatat.

| Tahap | Baris | Benign | Phish | Tanggal min | Tanggal max |
|---|---:|---:|---:|---|---|
| `train_raw` | 498.255 | 276.729 | 221.526 | 2024-07-02 | 2025-09-08 |
| `test_raw` | 168.060 | 91.260 | 76.800 | 2025-09-08 | 2025-12-16 |
| `train_after_boundary_purge` | 497.574 | 276.316 | 221.258 | 2024-07-02 | 2025-09-07 |
| `train_after_unparseable_purge` | 497.573 | 276.316 | 221.257 | 2024-07-02 | 2025-09-07 |
| `train_unique` | **497.359** | 276.315 | 221.044 | 2024-07-02 | 2025-09-07 |
| `test_after_seen_url_purge` | 168.057 | 91.259 | 76.798 | 2025-09-08 | 2025-12-16 |
| `test_unique` | **168.035** | 91.259 | 76.776 | 2025-09-08 | 2025-12-16 |

`excluded_rows.csv` memuat 921 baris dengan alasan:

| Alasan | Baris |
|---|---:|
| `train_at_or_after_cutoff` | 681 |
| `duplicate_train_url` | 214 |
| `duplicate_test_url` | 22 |
| `test_url_seen_in_train` | 3 |
| `unparseable_url` | 1 |
| **Total** | **921** |

Urutan temporal tegas: `train.date.max = 2025-09-07` < `test.date.min = 2025-09-08`.
Tidak ada `row_id` maupun `url_key` yang beririsan antar-partisi (diassert di kode).

### 2.1 Satu baris yang tidak dapat diurai — keputusan terdokumentasi

C2 notebook menghentikan proses bila ada URL yang tidak dapat diurai, agar keputusan
tidak diambil diam-diam. Pada korpus penuh, tepat **satu** baris gagal:

```
row_id  : train:train-020.parquet:8668
label   : phish
tanggal : 2024-08-08
url     : https://npaiaajvaxrjmmhagh.com∕[-randomstring1-]∕[-randomstring2-]∕[-randomstring3-]@npaiaajvaxrjmmhagh.𝕧𝕚𝕣𝕡𝕞𝕠𝕛.cn/caonima=[-randomstring4-].co.jp/
error   : ValueError: 'npaiaajvaxrjmmhagh.𝕧𝕚𝕣𝕡𝕞𝕠𝕛.cn' does not appear to be an IPv4 or IPv6 address
```

Penyebabnya bukan bug kode: URL memakai `U+2215 DIVISION SLASH` (`∕`) alih-alih `/`,
huruf matematika-bold di host (`𝕧𝕚𝕣𝕡𝕞𝕠𝕛`), dan token placeholder literal
`[-randomstring1-]`. Tanda kurung siku pada userinfo membuat `urllib.parse.urlsplit`
memperlakukan netloc sebagai host ber-bracket lalu memanggil `ipaddress.ip_address`,
yang melempar `ValueError`.

**Keputusan:** baris **dikeluarkan** dengan alasan `unparseable_url`, dicatat di
`excluded_rows.csv` dan di berkas khusus `unparseable_urls.csv` (berisi url, label,
tanggal, dan pesan galat). Baris tidak "diperbaiki" karena karakter look-alike dan token
placeholder itu justru sinyal phishing; menormalkannya akan mengubah label menjadi
sesuatu yang tidak ada di korpus.

Agar keputusan ini tidak menyembunyikan regresi, runner memakai kebijakan berbatas
(`PHRESH_UNPARSEABLE_POLICY`, `PHRESH_UNPARSEABLE_MAX_SHARE`) dan **menghentikan proses**
bila proporsi baris gagal melebihi batas. Bukti dijalankan pada **smoke test** (21 shard
train, 1 shard test), bukan pada run penuh:

| Uji (smoke) | Hasil |
|---|---|
| `policy=exclude`, batas 0,01 % | 1 baris dikeluarkan (0,000583 % dari 171.657), run selesai `exit 0` |
| `policy=exclude`, batas 0 % | `ValueError: train: 1 unparseable URLs (0.000583% > cap 0.000000%)`, `exit 1` |
| `policy=raise` (default notebook) | berhenti seperti perilaku asli |

Untuk **run penuh**, proporsi yang berlaku adalah
`1 / 497.574 × 100 = 0,000201 %` (penyebut = train setelah purge batas waktu, sebelum
eksklusi URL) — masih jauh di bawah batas 0,01 %.

**Dampak pada hasil:** satu baris phishing dikeluarkan secara tercatat. Sensitivitas
kesimpulan terhadap cara penanganan baris tersebut **belum diuji**; ukuran eksklusi yang
kecil tidak membuktikan dampaknya nol. Yang dapat dinyatakan adalah bahwa baris itu
tercatat dan dapat dikembalikan bila diperlukan.

---

## 3. Fitur

`feature_schema.json`: **18 fitur URL deterministik**, tanpa target encoding.

```
URLLength, DomainLength, TLDLength, NoOfSubDomain, NoOfObfuscatedChar,
ObfuscationRatio, NoOfLettersInURL, LetterRatioInURL, NoOfDegitsInURL,
DegitRatioInURL, NoOfEqualsInURL, NoOfQMarkInURL, NoOfAmpersandInURL,
NoOfOtherSpecialCharsInURL, SpacialCharRatioInURL, IsHTTPS,
HasObfuscation, IsDomainIP
```

Kode mengassert `'TLDLegitimateProb' not in Xtrain`, sehingga kolom yang pada D02
terbukti dihitung dari seluruh label tidak ikut. Ekstraksi: train 21,47 detik,
test 7,51 detik.

---

## 4. Hasil utama (lima seed, test 168.035 URL)

### 4.1 Keseluruhan test

| Seed | F1 phish | Precision | Recall | FPR benign | ROC AUC | Avg precision | MCC |
|---|---:|---:|---:|---:|---:|---:|---:|
| 13 | 0,801768 | 0,907356 | 0,718193 | 0,061693 | 0,914291 | 0,915765 | 0,680632 |
| 42 | 0,801412 | 0,908423 | 0,716956 | 0,060805 | 0,914974 | 0,916175 | 0,680698 |
| 2024 | 0,800504 | 0,907009 | 0,716383 | 0,061791 | 0,912810 | 0,914738 | 0,678968 |
| 777 | 0,798895 | 0,907103 | 0,713752 | 0,061495 | 0,913564 | 0,915182 | 0,677106 |
| 31415 | 0,799726 | 0,907417 | 0,714885 | 0,061364 | 0,914162 | 0,915640 | 0,678234 |
| **mean ± sd** | **0,800461 ± 0,001184** | 0,907461 ± 0,000564 | 0,716034 ± 0,001744 | 0,061430 ± 0,000387 | 0,913960 ± 0,000815 | 0,915500 ± 0,000554 | 0,679127 ± 0,001552 |

Rentang antar-seed sangat sempit (F1 0,798895–0,801768). Sesuai peringatan di C5,
**simpangan antar-seed bukan ketidakpastian lintas-periode** dan tidak boleh disebut
interval kepercayaan temporal.

### 4.2 Stratifikasi domain terlihat vs tidak terlihat

Subset ini adalah analisis deskriptif atas **prediksi model yang sama**, bukan
eksperimen training tambahan dan bukan estimasi kausal efek domain.

| Stratum | n | Benign | Phish | F1 | Precision | Recall | FPR | ROC AUC | Avg precision | MCC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `all` | 168.035 | 91.259 | 76.776 | 0,800461 | 0,907461 | 0,716034 | 0,061430 | 0,913960 | 0,915500 | 0,679127 |
| `seen_domain` | 96.231 | 62.363 | 33.868 | 0,740741 | 0,877821 | 0,640693 | 0,048429 | 0,904765 | 0,867546 | 0,647393 |
| `unseen_domain` | 71.804 | 28.896 | 42.908 | 0,844880 | 0,927894 | 0,775501 | 0,089486 | 0,914293 | 0,947561 | 0,672827 |

Domain unik pada test: 65.288; terlihat saat training 17.456, tidak terlihat 47.832.

### 4.3 Eksposur domain aktual

`actual_test_domain_exposure.csv` — proporsi baris test yang domainnya muncul di train:

| Kelas | Baris | Baris pada domain terlihat | Proporsi |
|---|---:|---:|---:|
| Benign | 91.259 | 62.363 | **68,34 %** |
| Phish | 76.776 | 33.868 | **44,11 %** |

Angka ini adalah overlap train→test yang sebenarnya, bukan frekuensi pengulangan
seluruh korpus. Karena itu klaim exposure 75,46 %/83,98 % pada draft lama tidak dipakai.

### 4.4 Bootstrap berbasis domain (seed 13, 1000 replikasi)

| Metrik | Estimasi | 95 % bawah | 95 % atas | Replikasi valid |
|---|---:|---:|---:|---:|
| F1 phish | 0,801768 | 0,731138 | 0,849622 | 1000 |
| Precision | 0,907356 | 0,896520 | 0,917853 | 1000 |
| Recall | 0,718193 | 0,611474 | 0,798910 | 1000 |
| FPR benign | 0,061693 | 0,054385 | 0,068172 | 1000 |

Resampling dilakukan pada **domain**, bukan baris. Interval ini berlaku untuk satu
model tetap pada satu periode test; ia bukan jaminan generalisasi temporal.

### 4.5 Ringkasan bulanan (seed 13, deskriptif)

| Bulan | n | Benign | Phish | Prevalensi phish | F1 | Precision | Recall | FPR | ROC AUC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2025-09 | 31.681 | 27.412 | 4.269 | 13,48 % | 0,568027 | 0,589957 | 0,547669 | 0,059281 | 0,797713 |
| 2025-10 | 114.033 | 60.717 | 53.316 | 46,75 % | 0,820909 | 0,913715 | 0,745217 | 0,061795 | 0,927333 |
| 2025-11 | 21.304 | 2.113 | 19.191 | 90,08 % | 0,807114 | 0,990452 | 0,681048 | 0,059631 | 0,906514 |
| 2025-12 | 1.017 | 1.017 | 0 | 0,00 % | 0,000000\* | 0,000000\* | tidak terdefinisi\* | **0,124877** | – |

\* **Desember 2025 wajib dibaca dengan hati-hati.** Bulan itu berisi 1.017 baris benign
dan **0 baris phishing**: TN = 890, FP = **127**, TP = 0, FN = 0.

- Recall = TP/(TP+FN) = 0/0 → **tidak terdefinisi**. Nilai `0.000000` pada CSV adalah
  konvensi `zero_division=0` di runner, bukan hasil pengukuran.
- Precision = 0/127 = 0 dan F1 = 0/127 = 0 **mempunyai penyebut bukan nol**, karena ada
  127 false positive nyata. Jadi tidak benar bila dikatakan seluruh nilai nol "bukan
  karena model gagal": model memang mengeluarkan 127 alarm palsu pada bulan itu.
- FPR Desember = **12,49 %**, jauh di atas bulan lain (±6 %). Ini angka nyata dan boleh
  dilaporkan.
- Yang tidak dapat dinilai hanyalah **kemampuan deteksi phishing** bulan itu, karena
  tidak ada positif sama sekali. Jangan memakai baris ini sebagai bukti penurunan
  performa, dan jangan pula menyebutnya nol yang tidak informatif — ada 127 FP.

**Komposisi kelas berubah drastis antar bulan** (13,5 % → 46,8 % → 90,1 % → 0 %).
Karena itu ringkasan bulanan tidak memisahkan drift waktu dari perubahan komposisi,
persis seperti diperingatkan audit §4.

---

## 5. Berkas keluaran dan kegunaannya

| Berkas | Isi |
|---|---|
| `design.json` | Pembekuan protokol, seed, cutoff, ambang, versi pustaka, kebijakan URL |
| `input_manifest.json` | 77 shard: nama, baris, byte, sha256 |
| `row_ledger.csv` | Jumlah baris per tahap penyaringan |
| `excluded_rows.csv` | 921 baris yang dikeluarkan beserta alasannya |
| `unparseable_urls.csv` | Baris URL tak terurai: url, label, tanggal, pesan galat |
| `split_train.csv.gz` / `split_test.csv.gz` | **Metadata split**, bukan matriks fitur: `row_id, date, y_phish, domain, url_sha256` (+ `domain_seen` pada test) |
| `feature_schema.json` | 18 nama fitur, waktu ekstraksi, catatan semantik |
| `actual_test_domain_exposure.csv` | Overlap domain train→test per kelas |
| `model_seed_*.txt` | Lima model LightGBM tersimpan |
| `model_params_seed_*.json` | Parameter efektif per seed |
| `predictions_seed_*.csv.gz` | Probabilitas per URL: `row_id, date, y_phish, domain, domain_seen, p_phish` |
| `results_per_seed.csv` | Metrik per seed × stratum (termasuk confusion matrix) |
| `seed_variation.csv` | mean/std/min/max per metrik per stratum |
| `cluster_bootstrap_primary_seed.csv` | Interval bootstrap berbasis domain |
| `monthly_descriptive_primary_seed.csv` | Ringkasan bulanan deskriptif |
| `output_manifest.json` | sha256 untuk 28 berkas keluaran |

---

## 6. Cara menjalankan ulang

```powershell
# korpus penuh, lima seed, 1000 bootstrap
$env:PHRESH_UNPARSEABLE_POLICY = "exclude"
python "run_temporal.py"

# uji asap cepat (3 shard, 1 seed, 50 bootstrap)
$env:PHRESH_TRAIN_SHARDS = "3"; $env:PHRESH_TEST_SHARDS = "3"
$env:PHRESH_SEEDS = "13"; $env:PHRESH_BOOTSTRAP = "50"
$env:PHRESH_OUTPUT_ROOT = "smoke"
python "run_temporal.py"
```

Variabel lingkungan yang tersedia: `PHRESH_DATA_DIR`, `PHRESH_OUTPUT_ROOT`,
`PHRESH_TRAIN_SHARDS`, `PHRESH_TEST_SHARDS`, `PHRESH_SEEDS`, `PHRESH_BOOTSTRAP`,
`PHRESH_UNPARSEABLE_POLICY`, `PHRESH_UNPARSEABLE_MAX_SHARE`. Default menghasilkan
perilaku notebook asli (korpus penuh, lima seed, 1000 replikasi, `policy=raise`).

### 6.1 Perbedaan runner terhadap notebook

Port ini **bukan** salinan identik. Tiga perbedaan, semuanya disengaja dan tercatat:

1. **Lokasi path.** `DATA_DIR` dan `OUTPUT_ROOT` menunjuk path lokal, bukan Google Drive;
   blok `drive.mount` tidak dijalankan.
2. **Override uji asap.** Variabel `PHRESH_*` memungkinkan pembatasan shard/seed/bootstrap
   agar bisa diuji cepat sebelum run penuh.
3. **Kebijakan URL tak terurai.** Notebook asli **selalu berhenti**. Runner menambahkan
   mode `exclude` yang mencatat setiap baris ke `excluded_rows.csv` dan
   `unparseable_urls.csv`, dengan batas proporsi per partisi yang tetap menghentikan
   proses bila terlampaui. Default tetap `raise`, sehingga perilaku asli dapat
   direproduksi persis.

Protokol, cutoff, urutan purge, deduplikasi, 18 fitur, parameter LightGBM, threshold, dan
bootstrap domain **tidak diubah**.

### 6.2 Pencatatan PSL — batas yang harus diakui

`design.json` mencatat versi `tldextract` (5.4.0) dan
`include_psl_private_domains=false`. Runner juga memanggil
`tldextract.TLDExtract(suffix_list_urls=(), include_psl_private_domains=False)`.

**Tidak ada snapshot PSL tersendiri maupun checksum-nya di paket keluaran.** Karena itu
jangan menyatakan bahwa identitas snapshot PSL telah dicatat lengkap. Yang dapat
dinyatakan hanyalah versi pustaka dan fakta bahwa private suffix tidak diaktifkan.

---

## 7. Batas yang harus dipatuhi saat menulis naskah

1. Hasil ini **melatih model baru pada PhreshPhish**; ia **bukan** transfer model
   PhiUSIIL dan **bukan** bukti penuaan model PhiUSIIL. Tabel 2 dan Tabel 3 tetap
   berisi angka PhiUSIIL.
2. Angka temporal masuk ke **tabel terpisah**, bukan menggantikan Tabel 2–3.
3. Partisi test PhreshPhish sudah pernah dilihat pada probe eksploratif; perbaikan ini
   tidak menciptakan holdout konfirmatori baru. Cantumkan di §2.1 dan batasan.
4. Purge seam dan deduplikasi mengubah benchmark asli: target evaluasi adalah URL yang
   belum terlihat pada periode berikutnya, bukan seluruh lalu lintas masa depan.
   Sertakan `row_ledger.csv`, `excluded_rows.csv`, dan kedua manifest.
5. Temporal bukan site-disjoint dan bukan zero-day; domain dapat berulang lintas waktu
   (lihat §4.3).
6. Interval bootstrap berlaku untuk satu model dan satu periode, bukan seluruh periode
   masa depan; seed bukan sampel waktu independen.
7. Fitur baru bukan padanan terverifikasi fitur PhiUSIIL; tidak ada fitur konten.
8. Satu batas temporal tidak mengisolasi efek waktu dari sumber, komposisi, platform,
   dan kebijakan pelabelan. Jangan menyebut selisih antar-korpus sebagai "temporal decay".
9. Sufiks privat tldextract tidak diaktifkan; yang tercatat hanyalah versi pustaka dan
   `include_psl_private_domains=false`. Snapshot PSL dan checksum-nya **tidak** tersedia
   di paket keluaran — jangan mengklaim identitas PSL tercatat lengkap.
10. AUC tinggi bukan bukti asal-usul label; ladder L0–L4 belum dijalankan.
11. Waktu 194,2 detik adalah waktu yang dilaporkan penulis; nilai itu tidak dapat
    direproduksi dari berkas keluaran. Waktu yang tersimpan di `results_per_seed.csv`
    adalah mean fit **6,663250 detik**, mean batch prediction **0,817467 detik** untuk
    168.035 baris, dan amortized **0,004865 ms/baris**. Angka amortized itu **tidak**
    memasukkan ekstraksi fitur dan **bukan** latensi satu permintaan URL.
12. Pasangkan interval bootstrap dengan estimasi **seed 13**, bukan dengan mean lima seed.

---

## 8. Ringkasan koreksi dari verifikasi independen

`VERIFIKASI_HASIL_TEMPORAL.md` menjalankan 134 pemeriksaan (28 hash keluaran, rekonsiliasi
666.315 ID baris, pemisahan waktu, deduplikasi, kecocokan prediksi, seluruh metrik dan
confusion count pada 15 kombinasi seed × stratum, ringkasan, empat interval bootstrap, dan
metadata model). Hasilnya: **134 lulus, 0 gagal**, selisih numerik maksimum **0** pada
`rtol=atol=1e-12`. Tujuh koreksi terhadap dokumen ini sudah diterapkan:

| # | Koreksi | Status di dokumen ini |
|---|---|---|
| 1 | Angka 0,000583 % adalah milik **smoke run**; run penuh = **0,000201 %** (1/497.574) | §2.1 diperbaiki, tabel diberi label smoke |
| 2 | Klaim "tidak mengubah kesimpulan" diganti: sensitivitas belum diuji | §2.1 diperbaiki |
| 3 | Desember: recall tidak terdefinisi, **ada 127 FP**, FPR 12,4877 % | §4.5 diperbaiki |
| 4 | `split_*.csv.gz` adalah **metadata split**, bukan matriks fitur | §5 diperbaiki |
| 5 | Port runner mengubah kebijakan URL tak terurai, bukan hanya path | §6.1 ditambahkan |
| 6 | Snapshot/checksum PSL **tidak** tercatat | §6.2 ditambahkan |
| 7 | Waktu 194,2 detik tidak dapat direproduksi dari keluaran | header dan §7 diperbaiki |

Batas yang tetap berlaku dan tidak dapat ditutup oleh audit mana pun atas paket ini:
parquet mentah dan matriks fitur tidak disertakan, sehingga ekstraksi fitur, hash input,
ketepatan label terhadap sumber, dan kesesuaian probabilitas dengan eksekusi ulang model
**belum diverifikasi end-to-end**. Model tersimpan hanya diperiksa metadata teks dan
jumlah blok pohon; model tidak dijalankan.

> **Pembaruan.** Keterbatasan di paragraf ini sudah **ditutup** oleh verifikasi
> end-to-end yang dijalankan di mesin penulis, karena korpus mentah dan model tersimpan
> tersedia secara lokal. Lihat §9.

---

## 9. Verifikasi end-to-end terhadap korpus mentah

Audit independen (§8) bekerja hanya dari paket keluaran. Karena korpus mentah
(`E:\Kuliah\Tugas Akhir\dataset\PhreshPhish\data`) dan model tersimpan ada di mesin ini,
gap terbesarnya dapat ditutup: **apakah keluaran tersimpan benar-benar berasal dari data
mentah melalui pipeline yang diklaim.**

Verifikator: `verify_end_to_end.py` (skrip terpisah, tidak mengubah `run_temporal.py`).
Fungsi `parse_url`, `canonical_url`, `host_parts`, `url_features`, dan `domain_for`
diambil dari runner **lewat AST**, sehingga yang diuji adalah jalur kode yang sama —
bukan implementasi kedua yang kebetulan mirip.

Perintah:

```bash
python verify_end_to_end.py outputs/20261022T170935017991Z --train-sample 0
```

`--train-sample 0` berarti seluruh partisi train diverifikasi, bukan sampel.

### 9.1 Hasil: 25 pemeriksaan, 25 lulus, 0 gagal

| Pemeriksaan | Cakupan | Hasil |
|---|---|---|
| `test_row_ids_all_present` | 168.035 baris test | semua `row_id` ditemukan di shard mentah |
| `test_label_fidelity` | 168.035 | `label` mentah → `y_phish` cocok, 0 beda |
| `test_date_fidelity` | 168.035 | tanggal mentah = tanggal tersimpan, 0 beda |
| `test_canonical_hash` | 168.035 | `sha256(canonical_url(raw))` = `url_sha256`, 0 beda |
| `test_domain_fidelity` | 168.035 | `domain_for(raw)` = `domain` tersimpan, 0 beda |
| `test_feature_columns` | – | 18 kolom, urutan sesuai `feature_schema.json` |
| `test_features_finite` | 168.035 × 18 | seluruh nilai berhingga |
| `no_target_encoding_column` | – | `TLDLegitimateProb` tidak ada |
| `train_row_ids_all_present` | **497.359 baris train** | semua ditemukan |
| `train_label_fidelity` | 497.359 | 0 beda |
| `train_date_fidelity` | 497.359 | 0 beda |
| `train_canonical_hash` | 497.359 | 0 beda |
| `train_domain_fidelity` | 497.359 | 0 beda |
| `train_feature_columns` | 497.359 × 18 | 18 kolom, urutan sama |
| `test_domain_seen_from_train` | 168.035 | dihitung dari himpunan domain train, 0 beda |
| `seed_{13,42,2024,777,31415}_probabilities_reproduce` | 168.035 × 5 | **max abs(dp) = 0,000e+00** |
| `seed_{...}_confusion_matrix` | 168.035 × 5 | TN/FP/FN/TP identik dengan `results_per_seed.csv` |

Confusion matrix yang dihitung ulang dari ambang 0,5, kelima seed:

| Seed | TN | FP | FN | TP |
|---|---:|---:|---:|---:|
| 13 | 85.629 | 5.630 | 21.636 | 55.140 |
| 42 | 85.710 | 5.549 | 21.731 | 55.045 |
| 2024 | 85.620 | 5.639 | 21.775 | 55.001 |
| 777 | 85.647 | 5.612 | 21.977 | 54.799 |
| 31415 | 85.659 | 5.600 | 21.890 | 54.886 |

### 9.2 Apa yang sekarang terbukti dan apa yang belum

**Terbukti (sebelumnya hanya diasumsikan):**

1. Seluruh 168.035 baris test dan 497.359 baris train benar-benar berasal dari shard
   mentah yang tercatat di `input_manifest.json` — tidak ada baris sintetis.
2. Label tersimpan sesuai sumber; tidak ada label yang digeser atau dibalik.
3. Tanggal tersimpan sesuai sumber; pemisahan waktu bukan hasil penyuntingan metadata.
4. Hash URL kanonis dapat dihitung ulang dari URL mentah dengan fungsi runner sendiri.
5. Ekstraksi 18 fitur deterministik dan reprodusibel dari URL mentah.
6. **Probabilitas tersimpan dapat direproduksi persis** dari model tersimpan + fitur yang
   dihitung ulang: selisih maksimum **0,0** pada kelima seed, bukan sekadar "dalam
   toleransi".
7. Ambang 0,5 memetakan probabilitas itu ke confusion matrix yang identik dengan laporan.

**Tetap belum terbukti (dan tidak dapat dibuktikan dengan data ini):**

1. Bahwa `canonical_url` dan `url_features` **seharusnya** didefinisikan seperti itu.
   Verifikasi ini menguji konsistensi pipeline, bukan kebenaran desain fitur.
2. Bahwa label PhreshPhish sendiri benar. Sumber label tidak diaudit di sini.
3. Generalisasi ke periode setelah 16 Desember 2025.
4. Bahwa hasil ini mengukur penuaan model PhiUSIIL. Model di sini dilatih ulang pada
   PhreshPhish; tidak ada model PhiUSIIL yang diuji.
5. Identitas snapshot PSL (lihat §6.2).

Laporan mesin: `outputs/END_TO_END_20261022T170935017991Z.json` (memuat 25 entri
pemeriksaan, versi pustaka verifikator, dan fingerprint manifest
`911a0691c8606bed0ad666e1d35f87ed15b7af326dd8ad2d23d7867877de9c1f`).
