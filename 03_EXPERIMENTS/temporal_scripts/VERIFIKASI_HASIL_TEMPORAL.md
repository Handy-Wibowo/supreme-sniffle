# Verifikasi hasil temporal PhreshPhish

**Keputusan: keluaran run penuh konsisten secara numerik dan dapat digunakan sebagai hasil eksploratif pada protokol yang dilaporkan.** Sebanyak 134 pemeriksaan lulus; tidak ada kegagalan. Metrik dihitung ulang dari prediksi individual, dan interval bootstrap direproduksi. Tidak ditemukan alasan numerik untuk mengulang pelatihan demi memperbaiki tabel hasil ini.

Run yang diaudit: `outputs/20261022T170935017991Z/` di dalam `outputs.zip`. Folder smoke test dan run yang berhenti tidak dicampur dengan run penuh. Laporan ini melengkapi `HASIL_RUN_TEMPORAL.md`; berkas asli tidak diubah.

## 1. Cakupan dan hasil pemeriksaan

| Pemeriksaan | Hasil |
|---|---|
| SHA-256 dan ukuran keluaran | 28 dari 28 berkas cocok dengan `output_manifest.json`; manifest mencakup seluruh berkas lain pada run |
| Rekonsiliasi identitas baris | 666.315 ID baris dari 77 shard yang tercantum pada manifest terhitung tepat sekali sebagai train, test, atau eksklusi |
| Partisi akhir | 497.359 train; 168.035 test; 921 eksklusi |
| Pemisahan waktu pada metadata | Maksimum train 7 September 2025; minimum test 8 September 2025; seluruh train sebelum cutoff dan seluruh test pada/setelah cutoff |
| Deduplikasi pada hash tersimpan | Tidak ada duplikat hash URL kanonis di masing-masing partisi; 0 hash bersama antara train dan test |
| Kesesuaian prediksi dengan test | Kelima berkas prediksi cocok pada ID, urutan, label, tanggal, domain, dan indikator domain terlihat; seluruh probabilitas valid |
| Metrik | Seluruh metrik dan confusion count pada 15 kombinasi seed × stratum cocok |
| Ringkasan | Mean/SD/min/max antar-seed, empat ringkasan bulanan, dan tabel exposure cocok |
| Bootstrap | Empat interval, masing-masing 1.000 replikasi valid, cocok |
| Model tersimpan | Header mencatat 18 fitur dengan nama yang sesuai dan 300 blok pohon berurutan pada masing-masing model; JSON parameter sesuai desain |

Perbandingan numerik menggunakan `rtol=atol=1e-12`, dengan NaN dicocokkan sebagai nilai hilang. Selisih absolut maksimum yang teramati pada perbandingan tersebut adalah **0** setelah pembacaan numerik. SD dihitung sebagai sample standard deviation, `ddof=1`.

Pemeriksaan checksum membuktikan konsistensi berkas dengan manifest yang menyertainya; pemeriksaan ini tidak mengautentikasi asal data atau proses pembuatannya. Rekonsiliasi baris menggunakan ID, metadata split, daftar eksklusi, dan jumlah baris pada manifest. Parquet sumber tidak disertakan, sehingga isi dan checksum input belum diverifikasi langsung. Hash URL kanonis dan tanggal juga diperiksa sebagai nilai tersimpan, tanpa menghitungnya ulang dari URL mentah.

## 2. Partisi dan eksklusi

| Tahap | Total | Benign | Phishing |
|---|---:|---:|---:|
| Train mentah menurut ledger | 498.255 | 276.729 | 221.526 |
| Setelah purge batas waktu | 497.574 | 276.316 | 221.258 |
| Setelah eksklusi URL tak terurai | 497.573 | 276.316 | 221.257 |
| Train akhir setelah deduplikasi | 497.359 | 276.315 | 221.044 |
| Test mentah menurut ledger | 168.060 | 91.260 | 76.800 |
| Setelah menghapus URL test yang sudah ada pada train | 168.057 | 91.259 | 76.798 |
| Test akhir setelah deduplikasi | 168.035 | 91.259 | 76.776 |

Sebanyak 921 eksklusi terdiri atas 681 baris train pada/setelah cutoff, 1 URL train tak terurai, 214 duplikat URL train, 3 URL test yang telah ada pada train, dan 22 duplikat URL test. Rentang train akhir adalah 2 Juli 2024–7 September 2025; rentang test akhir 8 September–16 Desember 2025, berdasarkan metadata UTC.

Protokol ini memodifikasi partisi asli dengan purge batas tanggal dan deduplikasi URL. Populasi evaluasinya adalah URL kanonis yang belum muncul pada train dan dipertahankan setelah pemrosesan tersebut. Domain boleh berulang lintas partisi.

## 3. Angka yang sudah diverifikasi

Model menggunakan threshold 0,5, label phishing = 1, dan lima seed: 13, 42, 2024, 777, 31415. Semua seed memakai satu partisi temporal yang sama.

| Metrik seluruh test | Mean lima seed | SD antar-seed |
|---|---:|---:|
| F1 phishing | 0,800461 | 0,001184 |
| Precision phishing | 0,907461 | 0,000564 |
| Recall phishing | 0,716034 | 0,001744 |
| FPR benign | 0,061430 | 0,000387 |
| Miss rate phishing | 0,283966 | 0,001744 |
| ROC AUC | 0,913960 | 0,000815 |
| Average precision | 0,915500 | 0,000554 |
| MCC | 0,679127 | 0,001552 |

Untuk model utama **seed 13**, confusion matrix yang dihitung ulang adalah:

| Kelas aktual | Prediksi benign | Prediksi phishing |
|---|---:|---:|
| Benign | 85.629 (TN) | 5.630 (FP) |
| Phishing | 21.636 (FN) | 55.140 (TP) |

Bootstrap domain memakai 65.288 domain test, sampling domain dengan pengembalian, 1.000 replikasi, RNG seed 13, dan kuantil persentil 2,5%/97,5%. Verifikator membentuk confusion count tiap domain menggunakan integer encoding dan `bincount`, lalu mengulang sampling tersebut.

| Metrik seed 13 | Estimasi | Interval bootstrap domain 95% |
|---|---:|---:|
| F1 phishing | 0,801768 | [0,731138, 0,849622] |
| Precision phishing | 0,907356 | [0,896520, 0,917853] |
| Recall phishing | 0,718193 | [0,611474, 0,798910] |
| FPR benign | 0,061693 | [0,054385, 0,068172] |

**Pasangkan interval ini dengan estimasi seed 13, bukan mean lima seed.** Variasi antar-seed mengukur variasi model pada data tetap. Bootstrap di sini mengukur variasi resampling domain pada prediksi satu model dan satu periode test; pelatihan tidak diulang di dalam bootstrap. Keduanya tidak mengukur ketidakpastian terhadap semua periode masa depan.

## 4. Domain dan bulan: interpretasi deskriptif

Exposure train→test yang dihitung ulang adalah 62.363 dari 91.259 baris benign (**68,3363%**) dan 33.868 dari 76.776 baris phishing (**44,1127%**). Sebanyak 17.456 domain test terlihat di train dan 47.832 domain test tidak terlihat, dari 65.288 domain test total. Definisi kelompok mengikuti domain tersimpan oleh runner; private suffix tidak diaktifkan.

| Stratum | Baris test | Prevalensi phishing | Mean F1 | Mean FPR |
|---|---:|---:|---:|---:|
| Domain terlihat | 96.231 | 35,1945% | 0,740741 | 0,048429 |
| Domain tidak terlihat | 71.804 | 59,7571% | 0,844880 | 0,089486 |

Selisih kedua kelompok tidak mengisolasi efek domain. Komposisi kelas dan contoh berbeda. F1 yang lebih tinggi pada kelompok domain tidak terlihat tidak membuktikan bahwa ketidakkenalan domain membantu model; FPR kelompok itu juga lebih tinggi.

| Bulan test, seed 13 | Benign | Phishing | F1 phishing | Recall phishing | FPR benign |
|---|---:|---:|---:|---:|---:|
| September 2025 | 27.412 | 4.269 | 0,568027 | 0,547669 | 0,059281 |
| Oktober 2025 | 60.717 | 53.316 | 0,820909 | 0,745217 | 0,061795 |
| November 2025 | 2.113 | 19.191 | 0,807114 | 0,681048 | 0,059631 |
| Desember 2025 | 1.017 | 0 | 0,000000* | Tidak dapat dievaluasi* | 0,124877 |

*Desember memiliki TN = 890 dan FP = 127, tanpa TP/FN. Recall = TP/(TP+FN) tidak terdefinisi karena penyebutnya nol; nilai 0 dalam CSV merupakan konvensi `zero_division=0` pada runner. Precision = 0/127 = 0 dan F1 = 0/127 = 0 memiliki penyebut nonnol karena ada false positive. Karena itu, pernyataan bahwa semua nilai nol “bukan karena model gagal” perlu dihapus: terdapat 127 false positive nyata. FPR Desember adalah 12,4877%. Ketiadaan phishing membatasi penilaian deteksi phishing bulan tersebut. CSV hasil hitung ulang mempertahankan konvensi runner untuk kepentingan pencocokan; tabel laporan ini memberi interpretasi recall yang benar.*

Perubahan prevalensi bulanan sekitar 13,5% → 46,8% → 90,1% → 0% membuat rangkaian metrik bulanan tidak cukup untuk mengidentifikasi efek waktu secara terpisah.

## 5. Koreksi pada laporan eksekusi

| Bagian | Koreksi yang diperlukan |
|---|---|
| Tabel uji kebijakan URL tak terurai | Labeli sebagai **smoke test**. Angka 0,000583% cocok dengan 1/171.657 × 100 pada smoke run `20261022T170832746335Z`. Untuk run penuh, gunakan 1/497.574 × 100 = **0,000200975%**, dibulatkan 0,000201%. Penyebutnya adalah train setelah purge batas waktu, sebelum eksklusi URL. |
| “Tidak mengubah kesimpulan” akibat satu eksklusi | Ganti dengan fakta bahwa satu baris phishing dikeluarkan secara tercatat; sensitivitas kesimpulan terhadap alternatif penanganan baris tersebut belum diuji. Ukuran eksklusi yang kecil tidak membuktikan dampaknya nol. |
| Interpretasi Desember | Nyatakan recall tidak dapat dievaluasi, sertakan FP = 127 dan FPR = 12,4877%, serta beri catatan pada nilai nol yang tersimpan. |
| Deskripsi `split_train.csv.gz` / `split_test.csv.gz` | Sebut sebagai metadata split: ID, tanggal, label, domain, hash URL; test juga memuat indikator domain terlihat. Berkas ini tidak menyimpan 18 kolom matriks fitur. |
| Deskripsi port notebook pada runner | Catat perubahan kebijakan URL tak terurai dari berhenti menjadi eksklusi tercatat dengan batas proporsi. Pernyataan bahwa perbedaan hanya lokasi path dan override smoke test belum lengkap. |
| Pencatatan PSL | `design.json` mencatat versi tldextract dan `include_psl_private_domains=False`; runner mengatur `suffix_list_urls=()`. Tidak terdapat snapshot atau checksum PSL tersendiri di paket keluaran, sehingga jangan menyatakan bahwa identitas snapshot PSL lengkap telah dicatat. |
| Total waktu 194,2 detik | Tetap sebagai waktu yang dilaporkan penulis jika bukti pengukurannya tersedia; nilai itu tidak dapat direproduksi dari keluaran yang diaudit. |

Waktu tersimpan memiliki mean fit **6,663250 detik**, mean batch prediction **0,817467 detik** untuk 168.035 baris, dan mean amortized prediction **0,004864864 ms/baris**. Audit hanya memverifikasi aritmetika batch/ukuran test; waktu tidak diukur ulang. Nilai amortized tersebut tidak memasukkan ekstraksi fitur dan tidak sama dengan latensi satu permintaan URL.

## 6. Penggunaan dalam naskah

Hasil ini dapat dimasukkan sebagai tabel temporal terpisah untuk **model URL-only baru yang dilatih dan diuji pada PhreshPhish**, dengan protokol modifikasi yang disebutkan eksplisit. Pertahankan tabel PhiUSIIL sebagai hasil korpus dan eksperimen tersendiri.

Contoh kalimat hasil yang sesuai bukti:

> Pada evaluasi temporal PhreshPhish setelah purge batas tanggal dan deduplikasi URL, model LightGBM dengan 18 fitur URL menghasilkan F1 phishing rata-rata 0,800461 (SD antar-seed 0,001184) pada 168.035 URL test menggunakan lima seed model. Untuk seed utama 13, F1 sebesar 0,801768 dengan interval bootstrap domain 95% [0,731138; 0,849622]. Evaluasi ini bersifat eksploratif karena partisi test telah diperiksa pada probe sebelumnya; interval tersebut bersyarat pada satu model dan satu periode test.

Hasil ini tidak menguji penuaan model PhiUSIIL, transfer model antar-korpus, efek kausal pemisahan domain, atau kesiapan deployment. Lima seed bukan lima partisi waktu independen. Audit baru ini juga tidak memperbaiki angka gap 0,1311 dari probe lama yang memakai rancangan berbeda dan bermasalah.

Matriks fitur dan parquet mentah tidak tersedia dalam paket. Oleh sebab itu, ekstraksi fitur, hash input, ketepatan label terhadap sumber, serta kesesuaian probabilitas dengan eksekusi ulang model belum diverifikasi secara end-to-end. Model tersimpan hanya diperiksa pada metadata teks dan jumlah blok pohon; model tidak dijalankan. Batas ini tidak mengubah keberhasilan reproduksi metrik dari prediksi tersimpan.

## 7. Paket reproduksi audit

`PAKET_VERIFIKASI_TEMPORAL.zip` memuat verifikator, laporan ini, seluruh tabel hitung ulang, 134 hasil pemeriksaan, ringkasan JSON, fingerprint sumber, petunjuk pemakaian, dan versi dependensi verifikator. Prediksi serta model asli tidak diduplikasi; gunakan folder run penuh dari `outputs.zip` sebagai input.

Perintah dari folder paket setelah diekstrak:

```bash
python verify_temporal_outputs.py /path/ke/outputs/20261022T170935017991Z --output /path/ke/audit-baru
```

Direktori output wajib berada di luar direktori run input. Verifikator tidak melatih model, tidak mengakses URL dataset, dan tidak mengubah input. Versi audit: Python 3.12, NumPy 2.3.5, pandas 2.2.3, scikit-learn 1.8.0. Versi ini berbeda dari lingkungan runner yang tercatat; seluruh nilai yang dibandingkan tetap cocok.

Fingerprint `output_manifest.json` yang diaudit:

```text
911a0691c8606bed0ad666e1d35f87ed15b7af326dd8ad2d23d7867877de9c1f
```

Sumber bukti: berkas run penuh dalam `outputs.zip`, `run_temporal.py`, `full_run.log`, dan `HASIL_RUN_TEMPORAL.md` yang diberikan penulis. Tidak ada angka empiris baru yang diambil dari korpus lain.
