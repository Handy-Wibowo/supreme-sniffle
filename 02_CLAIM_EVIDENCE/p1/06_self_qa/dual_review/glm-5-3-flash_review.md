# Struktur Review

**C1 Claim-evidence consistency — PASS**
Setiap angka utama dapat dilacak ke tabel: F1 site-disjoint 0.999623 (Tabel 3/4), temporal 0.800461 (P110), transfer 0.599064/FPR 0.986478/ROC-AUC 0.382566/MCC −0.146445 (Tabel 7), ambang 0.884705 → FPR uji 1.1352% dan recall 0.5440 (Tabel 8, konsisten dengan abstrak). Uji aritmetika internal lulus: Tabel 8 (FN 20.119/76.776 = recall 0.738; FP 1.036/91.259 = 0.011352), Tabel 9 (8.035/21.636 = 37,1%; 1.761/8.082 = 21,79%), dan total kohort 91.259+76.776 = 168.035 konsisten dengan P107, P075, dan P131. Selisih pembulatan 0.004436 vs 0.004437 dijelaskan eksplisit (P105).
Evidence: [P107], [P125], [P131], [P134], [P105].

**C2 Boundary discipline — PASS**
Tidak ditemukan pelanggaran batas. Kalimat pembatas eksplisit dan berulang: "bukan model baru atau klaim state-of-the-art" [P009], [P031]; "bukan holdout buta atau prospektif" [P009], [P075]; "tidak mengidentifikasi penyebab temporal" [P009], [P115]; "proyeksi … skenario, bukan pengamatan deployment" [P070], [P116]; "tidak membuktikan … kebocoran" [P084], [P094]; "ketidakpastian klaster platform tidak terverifikasi" [P009], [P134].

**C3 Preserved corrections — PASS**
(a) polaritas sumber legitim=1/phishing=0 dan pemetaan analisis phishing=1: [P046], [P067]. (b) E3 bukan metrik positif-phishing: [P046], [P067]. (c) bootstrap seed 42 dibedakan dari model seed 13: [P068] ("angka 13 pada Tabel 6 menandai seed model, bukan seed RNG bootstrap"). (d) interval klaster platform absen dan dilabeli tidak terverifikasi: [P134], [P146]. (e) 37,1% deskriptif: [P134], Tabel 9. (f) 85 = kecocokan terpilih: [P041]. (g) provenance A0/A1 tidak diketahui: [P061], [P084]. (h) A2 kontrak, bukan kesamaan nilai: [P060], [P072]. (i) no-overlap ketat = analisis sensitivitas: [P053].

**C4 Literature use — PASS**
Setiap sitasi menopang kalimat yang dilekatinya; Tabel 1 secara eksplisit membatasi klaim ke "batas pemakaian" dan menandai "tidak dilaporkan pada abstrak" alih-alih menuduh studi terdahulu [P019]. Klaim komparatif dibatasi ("tidak dibandingkan secara numerik dengan studi yang menggunakan korpus atau protokol berbeda", [P138]). Near-neighbour yang akan saya minta penulis diskusikan satu kalimat: kritik/audit publik lain terhadap PhiUSIIL selain [24] (jika ada) — UNVERIFIABLE apakah ada, jadi hanya disarankan, bukan diwajibkan.

**C5 Novelty framing — PASS**
Kontribusi dinyatakan sebagai "rantai audit yang dapat ditelusuri melalui artefak tersimpan" [P147], bukan superioritas model; "Nilai model tidak melampaui state of the art" [P141]. Dapat dipertahankan terhadap [24] karena sumbu temporal/ambang/transfer beku memang tidak diuji di sana (Tabel 1, baris Ahamed et al.).

**C6 Internal consistency and presentation — PASS** (dengan catatan wajib revisi minor)
Penomoran tabel 1–10 dan rujukan silang konsisten; referensi [1]–[24] semuanya terkutip; abstrak Indonesia–Inggris sejalan angka dan klausul pembatasnya. Kelemahan: (i) Gambar 2 hanya memiliki kapsi [P129] dan tidak pernah dirujuk dalam teks badan (Gambar 1 dirujuk di [P042]); (ii) Bagian 5.2 mendeskripsikan paket audit internal tetapi tidak mencantumkan repositori publik/DOI, padahal klaim sentral paper adalah "dapat diaudit"; (iii) placeholder identitas penulis/afiliasi masih ada ([P002]–[P006]).

**C7 Rejection risk — five highest-risk issues**

1. **Medium** — Tidak ada ketersediaan artefak publik (repositori/DOI) meski kontribusi inti adalah "rantai bukti yang dapat diaudit"; paket di [P167] eksplisit "bukan bundel yang dapat direproduksi penuh" dan tidak memuat prediksi per baris, padahal taksonomi galat diklaim "dapat direproduksi dari prediksi tersimpan" [P036]. Fix terkecil: deposit paket (atau prediksi per baris + manifest) ke Zenodo/OSF dengan DOI, dan kutip DOI di 5.2.
2. **Medium** — Gambar 2 tidak dirujuk di badan teks; pembaca tidak tahu di mana panel (a) dan (b) dibahas. Fix: tambahkan rujukan "Gambar 2a" di [P093]/[P114] dan "Gambar 2b" di [P123].
3. **Low** — CI temporal hanya untuk seed model 13 ([P068]) sementara rerata lima seed dilaporkan tanpa CI ([P110]); berpotensi disalahbaca. Fix: satu kalimat yang menyatakan CI Tabel 6 berlaku pada seed 13 saja.
4. **Low** — Placeholder identitas penulis, afiliasi, dan email [P002]–[P006] harus diisi sebelum penerbitan.
5. **Low** — Site-disjoint merata-ratakan lima partisi uji berbeda ([P090]); sudah diakui, tetapi sebaiknya ditambahkan juga sebagai catatan di kapsi Tabel 3 agar tidak terlewat.

Semua masalah bersifat revisi minor; tidak ada inkonsistensi angka, pelanggaran batas klaim, atau klaim tanpa dukungan.

OVERALL: APPROVE