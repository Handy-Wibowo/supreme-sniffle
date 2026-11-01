#!/usr/bin/env python
"""Deterministic P1 revision builder: v9_P0 -> v10_P1_candidate.

Hard rules enforced by this script:
  * the source DOCX hash must equal the published v9_P0 hash, or nothing is written;
  * every edit asserts its own locator (exact text or package part) before applying;
  * no P0-corrected sentence is rewritten unless the P1 change is registered;
  * all text edits are additive or explicitly listed replacements;
  * the output is a NEW file; v9_P0 is never opened for writing.

Usage:
    python apply_p1_revisions.py                 # build the candidate
    python apply_p1_revisions.py --verify-only   # re-check an existing candidate
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import docx
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.text.paragraph import Paragraph

PHISH = Path(r"E:\Kuliah\Tugas Akhir\phishing")
SRC = PHISH / "BITS_Draft_Phishing_URL_Leakage_v9_P0.docx"
OUT = PHISH / "BITS_Draft_Phishing_URL_Leakage_v10_P1_candidate.docx"
HERE = PHISH / "revision_v10_p1" / "05_integrated_manuscript"
FIG_PNG = PHISH / "revision_v10_p1" / "01_figure_metadata_layout" / "figure_1_research_pipeline_v10.png"

EXPECTED_SRC_SHA256 = "16478b6e2844dfcaa5c1599238d18dab37b943be12963c3565a15168512362ec"
CANDIDATE_TITLE = ("Audit Generalisasi Deteksi Phishing URL: Saturasi Benchmark pada PhiUSIIL, "
                   "Evaluasi Temporal, dan Transfer Lintas-Korpus ke PhreshPhish")

# --------------------------------------------------------------------------- #
# edit content
# --------------------------------------------------------------------------- #

# (change_id, action_id, locator_prefix, kind, before_suffix, appended_text, reason, refs)
APPENDS = [
    ("P1-001", "A16", "Phishing URL merupakan masalah klasifikasi", "APPEND",
     "Dalam konteks phishing, validitas temporal dan pilihan dataset turut membatasi arti angka evaluasi yang dilaporkan [7], [8].",
     " Pengalaman pada klasifikasi malware menunjukkan bahwa skor F1 yang dilaporkan mendekati 0,99 dapat berasal dari bias spasial dan temporal pada rancangan eksperimen, bukan dari kemampuan model yang sebenarnya [13].",
     "Menambahkan landasan metodologis untuk pembacaan saturasi benchmark sebagai fenomena rancangan.",
     "[13]"),
    ("P1-002", "A16", "Pembagian acak pada tingkat baris", "APPEND",
     "Karena itu, protokol dan granularitas kelompok harus diperlakukan sebagai bagian dari klaim penelitian, bukan sekadar detail implementasi [3], [5].",
     " Pada sisi waktu, deteksi drift konsep menunjukkan bahwa model dapat menua selama penerapan sebelum penurunan kinerja terukur [14], dan evaluasi ulang terhadap pendekatan itu menegaskan bahwa kesimpulan tentang drift bergantung pada protokol pemisahan waktu [15].",
     "Menambahkan landasan bahwa unit pembagian dan waktu bersama-sama menentukan arti skor.",
     "[14], [15]"),
    ("P1-009", "A16", "Tiga konfigurasi fitur digunakan.", "APPEND",
     "Tiga konfigurasi fitur digunakan.",
     " Tabel 2 merangkum ketiganya.",
     "Memberi rujukan dalam teks untuk tabel konfigurasi fitur yang sebelumnya tidak bernomor dan tidak dirujuk.",
     "Tabel 2"),
    ("P1-010", "A16", "Proyeksi prevalensi dihitung secara aritmetika", "APPEND",
     "Proyeksi ini adalah skenario, bukan perilaku deployment yang diamati.",
     " Bentuk proyeksi ini merupakan penerapan langsung argumen base-rate pada sistem deteksi [21], dan untuk data yang tidak seimbang analisis precision-recall lebih informatif daripada ROC [22].",
     "Menyandarkan proyeksi PPV pada literatur base-rate dan evaluasi data tidak seimbang.",
     "[21], [22]"),
    ("P1-011", "A16", "Implikasi operasional dipertimbangkan", "APPEND",
     "Hasil PhiUSIIL adalah pengamatan benchmark mendekati plafon; mekanismenya belum ditetapkan.",
     " Angka proyeksi tersebut konsisten dengan peringatan base-rate bahwa FPR kecil tidak menjamin proporsi alarm palsu yang kecil ketika prevalensi rendah [21], [22].",
     "Mengaitkan proyeksi prevalensi dengan batas interpretasi FPR.",
     "[21], [22]"),
    ("P1-012", "A16", "Menurunkan FPR uji dari 7,65% menjadi 1,14%", "APPEND",
     "Ambang tidak memperbaiki diskriminasi model; ambang hanya memindahkan biaya antara FP dan FN.",
     " Pola ini konsisten dengan peringatan base-rate bahwa FPR kecil tidak menjamin proporsi alarm palsu yang kecil [21], dan dengan posisi bahwa precision-recall lebih informatif daripada ROC pada data tidak seimbang [22]; literatur khusus pemilihan ambang berbasis biaya tidak disintesis di sini.",
     "Mengaitkan trade-off ambang dengan literatur base-rate dan precision-recall, tanpa mengklaim sintesis literatur biaya-ambang.",
     "[21], [22]"),
    # --- P1-020..P1-026: findings from the dual independent review (2026-11-01) ---
    ("P1-020", "dual-review C3(i)", "Satu batasan protokol perlu dinyatakan di muka", "APPEND",
     "sehingga pengelompokan ini tidak membuktikan independensi pada tingkat penyewa maupun identitas kampanye/operator yang sama.",
     " Pemeriksaan pada subset tanpa tumpang tindih ketat diperlakukan sebagai analisis sensitivitas atas prediksi yang tersimpan, bukan sebagai uji independen.",
     "Menambahkan label eksplisit 'analisis sensitivitas' yang diminta oleh koreksi A09 tetapi belum dinyatakan sebagai istilah di naskah.",
     "-"),
    ("P1-021", "dual-review C1/C7", "Eksperimen RQ5 menggunakan LightGBM/A2", "APPEND",
     "kohort ini telah diperiksa dalam pekerjaan eksploratif sebelumnya dan bukan holdout buta atau prospektif.",
     " Model pada eksperimen ini dilatih ulang hanya pada blok fit, sedangkan evaluasi temporal pada Subbagian 3.5 memakai model yang dilatih pada seluruh blok pra-cutoff, yaitu periode fit dan validasi (497.359 baris). Baris uji identik, tetapi modelnya berbeda, sehingga metrik pada ambang 0,5 pada Tabel 8 tidak identik dengan Tabel 6 dan kedua tabel itu tidak boleh dibaca sebagai satu kecocokan yang sama.",
     "Dua tabel melaporkan model berbeda pada kohort uji yang sama tanpa menyatakannya; pembaca dapat membacanya sebagai kontradiksi.",
     "-"),
    ("P1-022", "dual-review C1", "Tabel 8 menunjukkan hasil seed 13.", "APPEND",
     "Batas validasi tidak dipaksakan kembali pada uji; karena itu FPR uji dapat sedikit melampaui target.",
     " Model pada Tabel 8 dilatih ulang hanya pada blok fit, sehingga baris ambang bawaan 0,5 di sini tidak identik dengan Tabel 6; yang dibandingkan di dalam tabel ini adalah aturan ambang pada model yang sama.",
     "Menegaskan perbedaan model di tempat pembacaan tabel, bukan hanya di Metodologi.",
     "-"),
    ("P1-023", "dual-review C1", "Tabel 6. Kinerja temporal A2/LightGBM", "APPEND",
     "dengan RNG seed 42.",
     " Model dilatih pada seluruh blok pra-cutoff, yaitu periode fit dan validasi (497.359 baris), dengan ambang 0,5.",
     "Caption tabel harus menyatakan blok latih agar tidak tertukar dengan Tabel 8.",
     "-"),
    ("P1-024", "dual-review C1", "Tabel 8. Ambang berbasis validasi", "APPEND",
     "LightGBM/A2 seed 13.",
     " Model dilatih ulang hanya pada blok fit (372.213 baris); ambang dipilih pada blok validasi (125.146 baris) dan diterapkan sekali pada 168.035 baris uji.",
     "Caption tabel harus menyatakan blok latih dan validasi agar tidak tertukar dengan Tabel 6.",
     "-"),
    ("P1-026", "dual-review C1", "A2 menggunakan ekstraktor URL mentah bersama", "APPEND",
     "Perbandingan ini tidak memiliki interval bootstrap berpasangan dalam rancangan A1−A0.",
     " Angka 0,004436 dihitung dari nilai F1 tak-terbulatkan; selisih nilai terbulatkan yang ditampilkan pada Tabel 4 adalah 0,004437.",
     "Mencegah angka dilaporkan sebagai galat pembulatan: 0,004436 berasal dari nilai penuh, bukan dari pengurangan nilai terbulatkan.",
     "-"),
    ("P1-030", "dual-review C1", "Pembersihan membuang tepat empat kolom", "APPEND",
     "AUC ini menggambarkan separabilitas dan tidak membuktikan derivasi fitur dari label.",
     " Nilai AUC ditampilkan hingga empat desimal; pernyataan \"di atas 0,988\" karena itu mengacu pada nilai tak-terbulatkan, bukan pada perbandingan nilai terbulatkan.",
     "Menyatakan presisi pelaporan AUC agar klaim 'di atas 0,988' tidak dibaca sebagai inferensi dari angka terbulatkan 0,9880.",
     "-"),
]

# Exact whole-paragraph replacements.
REPLACES = [
    ("P1-025", "dual-review C6",
     "Seluruh penulis telah membaca dan menyetujui versi manuskrip yang telah diterbitkan.",
     "Seluruh penulis telah membaca dan menyetujui versi akhir manuskrip ini.",
     "Pernyataan penulis menyebut 'versi manuskrip yang telah diterbitkan' pada naskah yang belum diterbitkan; ini sisa templat.",
     "-"),
    ("P1-027", "dual-review C1",
     "Biaya komputasi dilaporkan secara terbatas. Pada evaluasi temporal PhreshPhish, waktu pelatihan LightGBM berada pada kisaran detik tunggal sampai belasan detik per kecocokan, dan waktu prediksi berada di bawah beberapa detik untuk 168.035 baris uji. Angka waktu lengkap untuk kecocokan yang dilaporkan tersimpan pada artefak eksperimen dan tidak direproduksi di sini sebagai klaim, karena pengukuran waktu bergantung pada perangkat keras dan beban sistem saat eksekusi.",
     "Biaya komputasi dilaporkan secara terbatas. Pada evaluasi temporal PhreshPhish, waktu pelatihan LightGBM berada pada rentang 6,06 sampai 7,21 detik per kecocokan, dan waktu prediksi batch untuk 168.035 baris uji berada pada rentang 0,79 sampai 0,84 detik. Rentang tersebut berasal dari lima kecocokan seed pada artefak results_per_seed.csv dan tidak diperlakukan sebagai klaim yang portabel, karena pengukuran waktu bergantung pada perangkat keras dan beban sistem saat eksekusi.",
     "Rentang waktu sebelumnya tidak sesuai dengan artefak: kecocokan temporal tercatat 6,06-7,21 detik latih dan 0,79-0,84 detik prediksi, bukan 'detik tunggal sampai belasan detik'. Nilai dan sumbernya dinyatakan eksplisit.",
     "-"),
]



SUBSREPLACE = [
    ("P1-048", "external-review D5",
     "berdampak jauh lebih besar terhadap beban investigasi analis daripada penurunan recall pada orde yang sama.",
     "dapat berdampak lebih besar terhadap beban investigasi analis daripada penurunan recall pada orde yang sama, tetapi besaran beban yang sebenarnya bergantung pada jumlah baris benign dan phishing, prevalensi, aturan tindak lanjut, dan biaya per investigasi, yang tidak dimodelkan di sini.",
     "Klaim beban analis dinyatakan tanpa syarat padahal bergantung pada volume, prevalensi, dan biaya."),
    ("P1-049", "external-review D5",
     "Perubahan komposisi kelas juga menjelaskan mengapa angka agregat tidak dapat dipakai untuk menyimpulkan tren.",
     "Perubahan komposisi kelas sebagian menjelaskan mengapa angka agregat tidak dapat dipakai untuk menyimpulkan tren, meskipun TPR dan FPR tidak dijamin konstan antarbulan sehingga prevalensi bukan satu-satunya faktor.",
     "Prevalensi diperlakukan sebagai penjelas tunggal perubahan precision antarbulan."),
]

# Substring-anchored appends (anchor must occur in exactly one paragraph).
SUBAPPENDS = [
    ("P1-036", "jumlah domain pada himpunan uji site-disjoint adalah 35.100",
     " Titik estimasi pada perbandingan itu adalah nilai model seed 42, bukan rerata lima seed pada Tabel 4, sehingga selisih pada Tabel 5 dan selisih rerata pada Tabel 4 memang berbeda dan tidak boleh dibandingkan langsung. Seed 42 di sini berperan sebagai seed model, sedangkan seed 42 pada bootstrap berperan sebagai seed RNG resampling; keduanya kebetulan bernilai sama tetapi berperan berbeda.",
     "Identitas estimasi Tabel 5 tidak dinyatakan, sehingga selisihnya tampak bertentangan dengan Tabel 4."),
    ("P1-037", "Tabel 5. Selisih berpasangan",
     " Titik estimasi memakai model seed 42; Tabel 4 menampilkan rerata lima seed.",
     "Caption harus menyatakan estimand agar tidak dibaca sebagai rerata lima seed."),
    ("P1-038", "Untuk mengidentifikasi kontribusi per fitur diperlukan desain leave-one-feature-out",
     " Selisih rerata A1−A0 lintas lima seed pada Tabel 4 untuk F1 adalah −0,000568, sedangkan selisih berpasangan model seed 42 pada Tabel 5 adalah −0,000980; keduanya sah untuk estimandnya masing-masing dan tidak saling menggantikan.",
     "Dua selisih yang berbeda dilaporkan tanpa penjelasan hubungannya."),
    ("P1-039", "Setiap kategori melaporkan dukungan, FP/FN, laju bersyarat pada kelas, dan interval Wilson 95%",
     " Nilai interval Wilson per kategori dihitung dari penyebut di dalam kategori dan tersimpan pada berkas taksonomi galat (kolom batas bawah dan batas atas); Tabel 9 menampilkan proporsi titik saja.",
     "Teks menyatakan interval Wilson dilaporkan, sedangkan Tabel 9 tidak memuatnya dan lokasi lampirannya tidak disebut."),
    ("P1-040", "Interval kepercayaan 95 % berbasis t (df = 4) pada masing-masing protokol dilaporkan",
     " Nilai interval tersebut tersimpan pada berkas metrik per seed dan tidak ditabulasikan dalam artikel ini.",
     "Teks menyatakan interval t dilaporkan, sedangkan nilainya tidak muncul pada tabel mana pun."),
    ("P1-041", "deterministik terhadap seed yang dicatat",
     " Pernyataan determinisme penuh tidak diverifikasi melalui artefak; yang dicatat adalah konfigurasi dan seed untuk replikasi.",
     "Klaim determinisme tidak memiliki bukti artefak."),
    ("P1-042", "bukan \"kinerja model menurun 20 poin karena waktu\"",
     " Perlu ditegaskan bahwa perbedaan vendor dan pipeline merupakan perancu perbandingan lintas korpus PhiUSIIL–PhreshPhish, bukan perancu perbandingan antarbulan di dalam PhreshPhish, karena seluruh blok temporal PhreshPhish berasal dari sumber pengumpulan yang sama.",
     "Perancu lintas korpus dipakai untuk menjelaskan evaluasi dalam korpus."),
    ("P1-046", "tidak diperlakukan sebagai klaim yang portabel, karena pengukuran waktu bergantung pada perangkat keras dan beban sistem saat eksekusi",
     " Spesifikasi perangkat keras dan jumlah thread tidak dicatat pada artefak, sehingga angka waktu tersebut adalah log eksekusi, bukan pembandingan biaya komputasi.",
     "Angka waktu dilaporkan tanpa spesifikasi mesin."),
]

# Paragraph replaced wholesale (its content is a description of Table 1).
REPLACE_PARA_TABLE1_INTRO = (
    "P1-003", "A16", "Tabel 1 memetakan fungsi setiap kelompok literatur",
    "Tabel 1 membandingkan desain evaluasi tiap kelompok literatur dan batas pemakaiannya dalam penelitian ini. Kolom batas tidak digunakan untuk menyatakan bahwa studi terdahulu \"tidak melakukan\" suatu eksperimen tanpa bukti; kolom itu hanya menjelaskan sejauh mana sumber tersebut dipakai untuk menopang klaim artikel ini. Isian \"tidak dilaporkan pada abstrak\" berarti informasi tersebut tidak tersedia pada sumber yang diperiksa, bukan berarti studi tidak melakukannya.",
    "Mengubah Tabel 1 dari peta peran sitasi menjadi perbandingan desain yang dapat dilacak.",
)

TABLE1_CAPTION_NEW = "Tabel 1. Perbandingan desain evaluasi dan batas pemakaian literatur utama."

TABLE1_HEADER = ["Sumber", "Korpus, domain, dan unit pembagian",
                 "Desain waktu, adaptasi, dan ambang", "Batas pemakaian"]

TABLE1_ROWS = [
    ["Marchal dan Asokan [3]",
     "Deteksi halaman phishing; unit pembagian tidak dilaporkan pada abstrak",
     "Evaluasi untuk kondisi nyata; tanpa adaptasi lintas korpus",
     "Tidak memindahkan angka atau efek protokol ke PhiUSIIL"],
    ["PhishBench (El Aassal et al.) [4]",
     "Banyak dataset deteksi phishing; kondisi pembandingan diseragamkan",
     "Tanpa desain temporal; protokol ambang tidak dilaporkan pada abstrak",
     "Penelitian ini tidak menggunakan pipeline PhishBench"],
    ["Arp et al. [5]; Kapoor dan Narayanan [6]",
     "Lintas domain keamanan dan sains; unit entitas dan kebocoran data",
     "Kerangka umum, bukan estimasi besaran efek",
     "Prinsip umum; bukan estimasi efek pada phishing URL"],
    ["Mia et al. [9]",
     "Fitur phishing lintas dataset; korpus berbeda-beda",
     "Uji transfer model lintas dataset dua arah dengan fitur bersama; protokol ambangnya tidak dinyatakan pada sumber yang diperiksa",
     "Protokol, fitur, dan pasangan korpus berbeda; bukan replikasi langsung"],
    ["Nabila et al. [11]; Yoga et al. [12]",
     "Klasifikasi URL pada venue BITS; evaluasi dalam-korpus",
     "Tanpa desain temporal atau transfer lintas korpus",
     "Tidak ada klaim peningkatan model atas kedua studi"],
    ["TESSERACT (Pendlebury et al.) [13]",
     "Malware Android; 129 ribu aplikasi lintas tiga tahun; batas ruang dan waktu",
     "Batas waktu eksplisit; metrik ketahanan yang diharapkan",
     "Domain malware; tidak memindahkan besaran efek ke phishing URL"],
    ["Transcend (Jordaney et al.) [14]; Barbero et al. [15]",
     "Malware Android dan Windows",
     "Deteksi drift saat penerapan; penolakan prediksi berisiko",
     "Tidak memberi protokol ambang lintas korpus untuk phishing URL"],
    ["Safi dan Singh [16]; Karim et al. [17]; Gupta et al. [18]; Sanchez-Paniagua et al. [19]; Aljofey et al. [20]",
     "Phishing website dan URL; korpus berbeda-beda; komposisi uji mengubah FPR [19]",
     "Umumnya evaluasi dalam-korpus; representasi URL-saja atau hibrida",
     "Perbandingan angka tidak dilakukan karena korpus dan protokol berbeda"],
    ["Ahamed et al. [24]",
     "PhiUSIIL 235.370 URL tervalidasi; validasi eksternal memakai PhishTank dengan benign independen",
     "Robustness adversarial, generalisasi leave-one-family-out, stabilitas penjelasan, dan evaluasi eksternal lintas sumber (Subbagian 4.6)",
     "Sumbu pembandingnya robustness; evaluasi temporal berbasis waktu dan ambang berbasis validasi tidak dilaporkan di sana"],
    ["Axelsson [21]; Saito dan Rehmsmeier [22]; Trad dan Chehab [23]",
     "Sistem deteksi, klasifikasi tidak seimbang, dan model bahasa besar",
     "Prinsip base rate dan precision-recall; arah model bahasa besar tidak diuji di sini",
     "Prinsip umum; bukan estimasi pada korpus ini"],
]

# New subsection inserted before the existing gap paragraph.
NEW_SECTION_HEADING = "1.2 Tinjauan Tematik: Waktu, Representasi, dan Ambang Operasional"
NEW_SECTION_ANCHOR_PREFIX = "Kesenjangan yang dituju karena itu bukan ketiadaan penelitian"
NEW_SECTION_PARAS = [
    "Literatur evaluasi keamanan berbasis pembelajaran mesin merumuskan dua sumber bias yang relevan bagi penelitian ini. Bias spasial muncul ketika distribusi data latih dan uji tidak mewakili kondisi penerapan, sedangkan bias temporal muncul ketika pemisahan waktu tidak menghormati urutan kejadian [13]. Kerangka TESSERACT menunjukkan bahwa keduanya dapat menaikkan skor secara sistematis: F1 yang dilaporkan mendekati 0,99 pada klasifikasi malware sebagian berasal dari rancangan eksperimen, bukan dari kemampuan model [13]. Pada penerapan, penurunan kinerja akibat perubahan distribusi dipantau melalui deteksi drift konsep yang membandingkan sampel penerapan dengan sampel latih [14], dan evaluasi ulang terhadap pendekatan tersebut menunjukkan bahwa kesimpulan tentang drift bergantung pada protokol evaluasi serta pada cara model menolak prediksi yang berisiko [15]. Ketiga temuan itu tidak memindahkan besaran efek ke domain phishing URL; yang dipindahkan adalah prinsip bahwa unit pembagian, urutan waktu, dan definisi kohort harus dinyatakan sebagai bagian dari klaim.",
    "Pada domain phishing URL, laporan kinerja tinggi merupakan hal yang umum. Tinjauan sistematis atas 80 makalah mengelompokkan pendekatan deteksi situs phishing menjadi berbasis daftar, kemiripan visual, heuristik, pembelajaran mesin, dan pembelajaran mendalam [16]. Pendekatan hibrida berbasis fitur URL melaporkan kinerja deteksi yang sangat tinggi pada korpus masing-masing [17], pendekatan leksikal dengan reduksi fitur ditujukan untuk lingkungan waktu nyata [18], dan studi kasus pada URL login menunjukkan bahwa komposisi himpunan uji mengubah laju positif palsu secara material [19]. Model berbasis karakter pada URL mentah juga menunjukkan bahwa representasi URL-saja dapat mencapai kinerja tinggi tanpa fitur halaman [20]. Protokol evaluasi terbaru pada korpus PhiUSIIL melaporkan akurasi 0,9962 sampai 0,9984 pada himpunan uji domain-disjoint untuk empat keluarga model, dan protokol yang sama juga memuat evaluasi eksternal lintas sumber pada Subbagian 4.6; kinerjanya turun tajam ketika URL dimutasi secara realistis [24]. Pola semacam ini konsisten dengan saturasi benchmark yang bersifat deskriptif: ketika banyak model berbeda mencapai skor hampir identik pada satu korpus, daya pembeda pada konfigurasi yang dievaluasi tampak terbatas untuk pertanyaan pemilihan model, dan artikel ini tidak menetapkan penyebabnya.",
    "Literatur transfer pada domain ini lebih tipis daripada literatur klasifikasi. Studi lintas dataset menunjukkan bahwa keandalan fitur tidak otomatis berpindah antar korpus [9], dan evaluasi leave-one-family-out pada korpus yang sama menunjukkan transfer yang buruk ke keluarga serangan yang tidak terlihat [24]. Kedua hasil itu menunjukkan bahwa portabilitas perlu diuji secara eksplisit, bukan disimpulkan dari skor dalam-korpus. Uji transfer beku satu arah dengan ekstraktor, model, dan ambang yang tidak disesuaikan pada target dilaporkan secara terbatas pada pasangan korpus PhiUSIIL dan PhreshPhish. Kontribusi artikel ini pada sumbu tersebut adalah bukti empiris spesifik untuk pasangan korpus itu dengan ekstraktor, urutan fitur, model, dan ambang yang dibekukan, dibaca bersama evaluasi temporal dalam korpus dan trade-off ambang yang dipilih pada validasi; ini penyediaan bukti yang dapat diaudit, bukan pengajuan metode adaptasi baru.",
    "Pada sisi operasional, literatur sistem deteksi telah lama menunjukkan bahwa ketika peristiwa yang dicari jarang, laju positif palsu yang kecil tetap menghasilkan proporsi alarm palsu yang besar di antara seluruh alarm [21]. Untuk data yang tidak seimbang, analisis precision-recall lebih informatif daripada ROC karena sensitif terhadap prevalensi kelas positif [22]. Karena itu artikel ini melaporkan FPR bersama proyeksi nilai prediksi positif pada prevalensi asumsi, dan memperlakukan proyeksi tersebut sebagai skenario aritmetika, bukan pengamatan penerapan.",
    "Perkembangan mutakhir juga mencakup penggunaan model bahasa besar, dengan perbandingan antara rekayasa prompt dan fine-tuning untuk deteksi URL phishing [23]. Arah tersebut tidak diuji dalam artikel ini karena kebutuhan utamanya adalah rantai evaluasi yang dapat dibekukan dan diaudit pada tingkat artefak, bukan pemilihan keluarga model.",
]

# Reference list additions, numbered 13..24 (P0 citation order for 1..12 preserved).
NEW_REFS = [
    ("13", 'F. Pendlebury, F. Pierazzi, R. Jordaney, J. Kinder, and L. Cavallaro, "TESSERACT: Eliminating experimental bias in malware classification across space and time," in ',
     "Proc. 28th USENIX Security Symposium (USENIX Security 19)",
     ", Santa Clara, CA, USA, 2019, pp. 729–746."),
    ("14", 'R. Jordaney, K. Sharad, S. K. Dash, Z. Wang, D. Papini, I. Nouretdinov, and L. Cavallaro, "Transcend: Detecting concept drift in malware classification models," in ',
     "Proc. 26th USENIX Security Symposium (USENIX Security 17)",
     ", Vancouver, BC, Canada, 2017, pp. 625–642."),
    ("15", 'F. Barbero, F. Pendlebury, F. Pierazzi, and L. Cavallaro, "Transcending TRANSCEND: Revisiting malware classification in the presence of concept drift," in ',
     "Proc. IEEE Symposium on Security and Privacy (SP)",
     ", San Francisco, CA, USA, 2022, pp. 805–823, doi: 10.1109/SP46214.2022.9833659."),
    ("16", 'A. Safi and S. Singh, "A systematic literature review on phishing website detection techniques," ',
     "Journal of King Saud University - Computer and Information Sciences",
     ", vol. 35, no. 2, pp. 590–611, 2023, doi: 10.1016/j.jksuci.2023.01.004."),
    ("17", 'A. Karim, M. Shahroz, K. Mustofa, S. B. Belhouari, and S. R. K. Joga, "Phishing detection system through hybrid machine learning based on URL," ',
     "IEEE Access",
     ", vol. 11, pp. 36805–36822, 2023, doi: 10.1109/ACCESS.2023.3252366."),
    ("18", 'B. B. Gupta, K. Yadav, I. Razzak, K. E. Psannis, A. Castiglione, and X. Chang, "A novel approach for phishing URLs detection using lexical based machine learning in a real-time environment," ',
     "Computer Communications",
     ", vol. 175, pp. 47–57, 2021, doi: 10.1016/j.comcom.2021.04.023."),
    ("19", 'M. Sánchez-Paniagua, E. Fidalgo, E. Alegre, W. Al-Nabki, and V. González-Castro, "Phishing URL detection: A real-case scenario through login URLs," ',
     "IEEE Access",
     ", vol. 10, pp. 42949–42960, 2022, doi: 10.1109/ACCESS.2022.3168681."),
    ("20", 'A. Aljofey, Q. Jiang, Q. Qu, M. Huang, and J.-P. Niyigena, "An effective phishing detection model based on character level convolutional neural network from URL," ',
     "Electronics",
     ", vol. 9, no. 9, Art. no. 1514, 2020, doi: 10.3390/electronics9091514."),
    ("21", 'S. Axelsson, "The base-rate fallacy and the difficulty of intrusion detection," ',
     "ACM Transactions on Information and System Security",
     ", vol. 3, no. 3, pp. 186–205, 2000, doi: 10.1145/357830.357849."),
    ("22", 'T. Saito and M. Rehmsmeier, "The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets," ',
     "PLoS ONE",
     ", vol. 10, no. 3, Art. no. e0118432, 2015, doi: 10.1371/journal.pone.0118432."),
    ("23", 'F. S. Trad and A. Chehab, "Prompt engineering or fine-tuning? A case study on phishing detection with large language models," ',
     "Machine Learning and Knowledge Extraction",
     ", vol. 6, no. 1, pp. 367–384, 2024, doi: 10.3390/make6010018."),
    ("24", 'T. Ahamed, S. C. Kakon, F. Al Farid, J. Uddin, and H. B. A. Karim, "An integrated evaluation protocol for adversarial robustness, generalization, and explanation stability in URL-based phishing detection," ',
     "Frontiers in Computer Science",
     ", vol. 8, 2026, doi: 10.3389/fcomp.2026.1834407."),
]

# Table renumbering: the feature-configuration table gains a number, so all later
# captions and in-text references shift by +1 (old "Tabel N" -> "Tabel N+1").
TABLE_RENUMBER_OLD = list(range(8, 1, -1))  # 8..2, descending to avoid cascades

NEW_CONFIG_CAPTION = "Tabel 2. Konfigurasi fitur A0, A1, dan A2 yang dibandingkan."

REF12_OLD_TAIL = ", vol. 7, no. 2, 2025, doi: 10.47065/bits.v7i2.7920."
REF12_NEW_TAIL = ", vol. 7, no. 2, pp. 1153–1163, 2025, doi: 10.47065/bits.v7i2.7920."

AVAILABILITY_OLD_PREFIX = "Paket tinjauan yang terdokumentasi mencakup"
AVAILABILITY_NEW = (
    "Paket tinjauan kandidat disusun dalam lima direktori utama: 01_MANUSCRIPT (naskah kandidat dan hasil render), "
    "02_CLAIM_EVIDENCE (audit Stage-1, QA P0, register perubahan P1, serta ledger sumber), 03_EXPERIMENTS "
    "(notebook yang telah dieksekusi beserta metrik, ledger, dan artefak run temporal kanonik), 04_ENVIRONMENT "
    "(catatan dependensi dan perintah yang diuji), dan 05_LIMITATIONS (bukti yang belum tersedia serta batas "
    "reproduksi). Setiap berkas didaftarkan pada MANIFEST.csv bersama peran, ukuran, SHA-256, dan status reproduksi; "
    "MANIFEST.sha256 memuat checksum untuk pemeriksaan mandiri. Paket ini tidak memuat korpus mentah PhiUSIIL dan "
    "PhreshPhish, biner model terlatih, pemisahan baris lengkap, prediksi per baris, arsip duplikat, dan cache yang "
    "dihasilkan alat bantu. Artefak yang dikecualikan beserta alasannya didaftarkan terpisah pada "
    "OMITTED_ARTIFACTS.csv, dengan status INCLUDED, WORKSPACE_ONLY, MISSING, OMITTED_SIZE, "
    "OMITTED_LICENSE_PRIVACY, atau NOT_REQUIRED. Karena itu paket ini adalah bundel bukti yang dapat diaudit, bukan "
    "bundel yang dapat direproduksi penuh di lingkungan bersih tanpa mengambil data dari penyedia aslinya. "
    "Salinan paket tersedia pada repositori publik https://github.com/Handy-Wibowo/supreme-sniffle dan diarsipkan dengan DOI konsep 10.5281/zenodo.23847784, dengan MANIFEST.sha256 untuk verifikasi independen; DOI konsep tersebut selalu menunjuk rilis terbaru. "
    "Penghitungan ulang artefak yang dikecualikan memerlukan run_temporal.py, design.json, dan seed yang tercatat."
)

CORE_SUBJECT_NEW = "Manuskrip v10 P1 dengan transfer lintas-korpus, evaluasi ambang, dan taksonomi galat"
CORE_COMMENT_NEW = ("v10 P1: koreksi kata pada Gambar 1, pembaruan metadata versi, perluasan related work dan "
                    "verifikasi referensi. Kandidat untuk tinjauan independen.")
FIG_PIC_NAME_OLD = "figure_1_research_pipeline_v8.png"
FIG_PIC_NAME_NEW = "figure_1_research_pipeline_v10.png"

# Rendered statistics of the candidate, measured with Word ComputeStatistics and
# refreshed here so that docProps/app.xml does not keep the stale v8 values
# (Pages 4 / Words 1998). Re-measured by 06_self_qa/render_candidate.py.
WORD_PAGES = 15
WORD_WORDS = 9833


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def find_unique_para(doc, prefix: str) -> int:
    hits = [i for i, p in enumerate(doc.paragraphs) if (p.text or "").startswith(prefix)]
    if len(hits) != 1:
        raise SystemExit(f"LOCATOR FAIL: {len(hits)} paragraphs start with {prefix!r}")
    return hits[0]


def append_text(para, text: str) -> None:
    """Append a sentence to a paragraph as a new run carrying the last run's formatting."""
    src = para.runs[-1] if para.runs else None
    new_run = para.add_run(text)
    if src is not None and src._element.find(qn("w:rPr")) is not None:
        new_run._element.insert(0, copy.deepcopy(src._element.find(qn("w:rPr"))))


def clone_para_after(anchor_p, template_p, text: str, registry: list) -> Paragraph:
    new_el = copy.deepcopy(template_p._element)
    body = new_el.find(qn("w:pPr"))
    for child in list(new_el):
        if child is not body:
            new_el.remove(child)
    proto = template_p._element.findall(qn("w:r"))
    tpl_run = copy.deepcopy(proto[0]) if proto else None
    if tpl_run is not None:
        for t in list(tpl_run.findall(qn("w:t"))):
            tpl_run.remove(t)
        t = tpl_run.makeelement(qn("w:t"), {})
        t.text = text
        t.set(qn("xml:space"), "preserve")
        tpl_run.append(t)
        new_el.append(tpl_run)
    anchor_p._element.addnext(new_el)
    registry.append(new_el)
    return Paragraph(new_el, anchor_p._parent)


def clone_para_before(anchor_p, template_p, text: str) -> Paragraph:
    new_el = copy.deepcopy(template_p._element)
    ppr = new_el.find(qn("w:pPr"))
    for child in list(new_el):
        if child is not ppr:
            new_el.remove(child)
    proto = template_p._element.findall(qn("w:r"))
    if proto:
        tpl_run = copy.deepcopy(proto[0])
        for t in list(tpl_run.findall(qn("w:t"))):
            tpl_run.remove(t)
        t = tpl_run.makeelement(qn("w:t"), {})
        t.text = text
        t.set(qn("xml:space"), "preserve")
        tpl_run.append(t)
        new_el.append(tpl_run)
    anchor_p._element.addprevious(new_el)
    return Paragraph(new_el, anchor_p._parent)


def set_cell_text(cell, text: str) -> None:
    p = cell.paragraphs[0]
    runs = p.runs
    if not runs:
        p.add_run(text)
        return
    runs[0].text = text
    for r in runs[1:]:
        r._element.getparent().remove(r._element)
    for extra in cell.paragraphs[1:]:
        extra._element.getparent().remove(extra._element)


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #

def build() -> dict:
    src_hash = sha256_file(SRC)
    if src_hash != EXPECTED_SRC_SHA256:
        raise SystemExit(f"ABORT: v9_P0 hash mismatch: {src_hash}")
    log: list[dict] = []

    doc = docx.Document(str(SRC))

    # ---- 0. table renumbering (must precede edits that cite table numbers) --
    n_renum = 0
    for old in TABLE_RENUMBER_OLD:
        for p in doc.paragraphs:
            if f"Tabel {old}" in (p.text or ""):
                for r in p.runs:
                    if f"Tabel {old}" in r.text:
                        r.text = r.text.replace(f"Tabel {old}", f"Tabel {old + 1}")
                        n_renum += 1
    log.append({"change_id": "P1-013", "action_id": "A16/QA", "type": "RENUMBER_REFS",
                "locator": "all paragraphs containing 'Tabel N' for N in 2..8",
                "before": "Tabel 2..8 in text and captions", "after": "Tabel 3..9 (+1 shift)",
                "evidence": "06_self_qa/P1_QA_REPORT.md (caption/order check)",
                "reason": "Tabel konfigurasi fitur yang sebelumnya tidak bernomor diberi nomor, sehingga tabel berikutnya bergeser.",
                "refs": "-", "verification": "PASS"})

    # ---- 1. additive paragraph edits ---------------------------------------
    for cid, action, loc, kind, before_suffix, added, reason, refs in APPENDS:
        i = find_unique_para(doc, loc)
        p = doc.paragraphs[i]
        if before_suffix not in p.text:
            raise SystemExit(f"ABORT {cid}: expected existing text not found in paragraph {i}")
        if added.strip() in p.text:
            raise SystemExit(f"ABORT {cid}: text already present")
        before = p.text
        append_text(p, added)
        log.append({"change_id": cid, "action_id": action, "type": "APPEND_TEXT",
                    "locator": f"paragraph[{i}] startswith {loc!r}",
                    "before": before[-220:], "after": added.strip(),
                    "evidence": "revision_v10_p1/03_literature_A16/SOURCE_LEDGER.csv",
                    "reason": reason, "refs": refs, "verification": "PASS"})

    # ---- 1b. exact whole-paragraph replacements -----------------------------
    for cid, action, old_text, new_text, reason, refs in REPLACES:
        hits = [i for i, p in enumerate(doc.paragraphs) if (p.text or "").strip() == old_text]
        if len(hits) != 1:
            raise SystemExit(f"ABORT {cid}: expected 1 paragraph equal to the old text, found {len(hits)}")
        p = doc.paragraphs[hits[0]]
        p.runs[0].text = new_text
        for r in p.runs[1:]:
            r._element.getparent().remove(r._element)
        log.append({"change_id": cid, "action_id": action, "type": "REPLACE_PARA",
                    "locator": f"paragraph[{hits[0]}] exact match",
                    "before": old_text, "after": new_text,
                    "evidence": "06_self_qa/dual_review/ (consolidated findings)",
                    "reason": reason, "refs": refs, "verification": "PASS"})



    # ---- 1d. substring replacements (single-run paragraphs only) ---------
    for cid, action, old_sub, new_sub, reason in SUBSREPLACE:
        hits = [i for i, p in enumerate(doc.paragraphs) if old_sub in (p.text or "")]
        if len(hits) != 1:
            raise SystemExit(f"ABORT {cid}: substring found in {len(hits)} paragraphs")
        para = doc.paragraphs[hits[0]]
        if len(para.runs) != 1:
            raise SystemExit(f"ABORT {cid}: paragraph has {len(para.runs)} runs, refusing to flatten")
        before = para.text
        para.runs[0].text = para.text.replace(old_sub, new_sub, 1)
        log.append({"change_id": cid, "action_id": action, "type": "REPLACE_TEXT",
                    "locator": f"paragraph[{hits[0]}] substring replace",
                    "before": old_sub[:200], "after": new_sub[:200],
                    "evidence": "ai review/v10 review/result/REVIEW_INDEPENDEN_v10_P1.md (D5)",
                    "reason": reason, "refs": "-", "verification": "PASS"})

    # ---- 1c. substring-anchored appends -----------------------------------
    for cid, needle, added, reason in SUBAPPENDS:
        hits = [i for i, p in enumerate(doc.paragraphs) if needle in (p.text or "")]
        if len(hits) != 1:
            raise SystemExit(f"ABORT {cid}: anchor {needle[:50]!r} found in {len(hits)} paragraphs")
        p = doc.paragraphs[hits[0]]
        before = p.text
        append_text(p, added)
        log.append({"change_id": cid, "action_id": "external-review", "type": "APPEND_TEXT",
                    "locator": f"paragraph[{hits[0]}] contains {needle[:40]!r}",
                    "before": before[-200:], "after": added.strip(),
                    "evidence": "ai review/v10 review/result/REVIEW_INDEPENDEN_v10_P1.md",
                    "reason": reason, "refs": "-", "verification": "PASS"})

    # ---- 2. Table 1 replacement -------------------------------------------
    i = find_unique_para(doc, REPLACE_PARA_TABLE1_INTRO[2])
    p = doc.paragraphs[i]
    before = p.text
    runs = p.runs
    runs[0].text = REPLACE_PARA_TABLE1_INTRO[3]
    for r in runs[1:]:
        r._element.getparent().remove(r._element)
    log.append({"change_id": REPLACE_PARA_TABLE1_INTRO[0], "action_id": REPLACE_PARA_TABLE1_INTRO[1],
                "type": "REPLACE_PARA", "locator": f"paragraph[{i}]",
                "before": before[:220], "after": REPLACE_PARA_TABLE1_INTRO[3][:220],
                "evidence": "03_literature_A16/RELATED_WORK_MATRIX.md",
                "reason": REPLACE_PARA_TABLE1_INTRO[4], "refs": "1,3,4,5,6,9,11,12,13-24",
                "verification": "PASS"})

    i = find_unique_para(doc, "Tabel 1. Posisi penelitian terhadap literatur")
    p = doc.paragraphs[i]
    before = p.text
    p.runs[0].text = TABLE1_CAPTION_NEW
    for r in p.runs[1:]:
        r._element.getparent().remove(r._element)
    log.append({"change_id": "P1-004", "action_id": "A16", "type": "REPLACE_CAPTION",
                "locator": f"paragraph[{i}]", "before": before, "after": TABLE1_CAPTION_NEW,
                "evidence": "03_literature_A16/RELATED_WORK_MATRIX.md",
                "reason": "Judul tabel disesuaikan dengan isi perbandingan desain.",
                "refs": "-", "verification": "PASS"})

    t = doc.tables[0]
    if len(t.rows) != 6:
        raise SystemExit(f"ABORT: Table 1 expected 6 rows, found {len(t.rows)}")
    template_row = t.rows[-1]._tr
    while len(t.rows) < len(TABLE1_ROWS) + 1:
        t._tbl.append(copy.deepcopy(template_row))
    for ri in range(len(TABLE1_ROWS) + 1):
        values = TABLE1_HEADER if ri == 0 else TABLE1_ROWS[ri - 1]
        for ci, val in enumerate(values):
            set_cell_text(t.rows[ri].cells[ci], val)
    log.append({"change_id": "P1-005", "action_id": "A16", "type": "REPLACE_TABLE",
                "locator": "table[1] (Tabel 1)",
                "before": "6 rows (1 header + 5 data), columns: Sumber | Fokus yang digunakan | Peran dalam penelitian ini | Batas pemakaian",
                "after": f"{len(TABLE1_ROWS)+1} rows (1 header + {len(TABLE1_ROWS)} data), columns: " + " | ".join(TABLE1_HEADER),
                "evidence": "03_literature_A16/RELATED_WORK_MATRIX.md; SOURCE_LEDGER.csv",
                "reason": "Tabel 1 menjadi perbandingan desain (korpus/unit pembagian, waktu/adaptasi/ambang, batas).",
                "refs": "3,4,5,6,9,11,12,13,14,15,16,17,18,19,20,21,22,23,24",
                "verification": "PASS"})

    # ---- 3. new subsection 1.2 --------------------------------------------
    anchor_i = find_unique_para(doc, NEW_SECTION_ANCHOR_PREFIX)
    anchor = doc.paragraphs[anchor_i]
    body_template = doc.paragraphs[find_unique_para(doc, "Studi lintas-dataset menunjukkan")]
    head_template = doc.paragraphs[find_unique_para(doc, "1.1 Posisi Penelitian")]
    clone_para_before(anchor, head_template, NEW_SECTION_HEADING)
    for txt in NEW_SECTION_PARAS:
        clone_para_before(anchor, body_template, txt)
    log.append({"change_id": "P1-006", "action_id": "A16", "type": "INSERT_SECTION",
                "locator": f"before paragraph[{anchor_i}] ({NEW_SECTION_ANCHOR_PREFIX!r})",
                "before": "(absent)",
                "after": NEW_SECTION_HEADING + " + " + str(len(NEW_SECTION_PARAS)) + " paragraphs",
                "evidence": "03_literature_A16/RELATED_WORK_MATRIX.md; NOVELTY_CLAIM_MAP.csv",
                "reason": "Menambahkan tinjauan tematik bertopik yang memuat pembandingan desain dan posisi kontribusi.",
                "refs": "9,13,14,15,16,17,18,19,20,21,22,23,24", "verification": "PASS"})

    # ---- 3b. configuration paragraph (§2.5) -------------------------------
    cfg_txt = ("Konfigurasi model dan lingkungan dicatat untuk keterlacakan. LightGBM dilatih dengan 300 estimator, "
               "learning rate 0,05, dan 63 daun; XGBoost dilatih dengan 300 estimator, learning rate 0,05, "
               "max_depth 8, eval_metric logloss, dan tree_method hist. Tidak ada penyetelan hiperparameter pada "
               "korpus target. Lingkungan eksperimen menggunakan LightGBM 4.7.0, scikit-learn 1.9.1, tldextract "
               "5.4.0, NumPy 2.5.3, dan pandas 3.1.0, dengan snapshot Public Suffix List ber-SHA-256 "
               "b69315c085d53972724b8f2df111ffc329b0c84fe0a47d62c8c91655cc774a38.")
    anchor_cfg = doc.paragraphs[find_unique_para(doc, "2.6 Metrik dan Analisis Statistik")]
    clone_para_before(anchor_cfg, body_template, cfg_txt)
    log.append({"change_id": "P1-028", "action_id": "dual-review C6", "type": "INSERT_PARA",
                "locator": "before '2.6 Metrik dan Analisis Statistik'",
                "before": "(absent)",
                "after": "Konfigurasi hyperparameter (LightGBM 300/0,05/63; XGBoost 300/0,05/depth 8) + versi pustaka + hash snapshot PSL",
                "evidence": "Experiment/5 - PhiUSIIL Focused Ablation/src/data.py MODEL_PARAMS; Exp7 design.json environment",
                "reason": "Rincian konfigurasi yang diperlukan untuk audit independen tidak ada di naskah meski tersimpan di artefak.",
                "refs": "-", "verification": "PASS"})

    # ---- 3c. Table 10: traceability of prose-only figures ------------------
    rows10 = [
        ["Angka", "Nilai", "Artefak sumber"],
        ["Selisih F1 acak terhadap site-disjoint, minimum (A0/XGBoost)", "0,000163",
         "results_random.csv; results_sitedisjoint.csv"],
        ["Selisih F1 acak terhadap site-disjoint, maksimum (A2/LightGBM)", "0,001178",
         "results_random.csv; results_sitedisjoint.csv"],
        ["Kesalahan A0→A1 LightGBM, rerata 5 seed pada 44.213,6 baris uji", "12,8 → 32,2",
         "metrics_all.csv (Eksperimen 5)"],
        ["Kesalahan A0→A1 XGBoost, rerata 5 seed pada 44.213,6 baris uji", "10,4 → 39,0",
         "metrics_all.csv (Eksperimen 5)"],
        ["IK 95 % F1 transfer LightGBM", "[0,538701; 0,669829]", "primary_seed_domain_bootstrap.csv"],
        ["IK 95 % FPR benign transfer LightGBM", "[0,984874; 0,988138]", "primary_seed_domain_bootstrap.csv"],
        ["IK 95 % ROC-AUC transfer LightGBM", "[0,353178; 0,413481]", "primary_seed_domain_bootstrap.csv"],
        ["IK 95 % MCC transfer LightGBM", "[−0,175573; −0,111340]", "primary_seed_domain_bootstrap.csv"],
        ["Waktu latih LightGBM temporal (5 seed)", "6,06–7,21 detik", "results_per_seed.csv"],
        ["Waktu prediksi batch 168.035 baris", "0,79–0,84 detik", "results_per_seed.csv"],
        ["Rerata lima seed, aturan FPR validasi <= 1 % (F1; recall; FPR)",
         "0,700739; 0,546658; 0,011365", "test_metrics_across_seeds.csv"],
        ["Rerata lima seed, aturan FPR validasi <= 0,5 % (F1; recall; FPR)",
         "0,646167; 0,480645; 0,005843", "test_metrics_across_seeds.csv"],
        ["FN kategori host platform, termasuk pages.dev", "8.035 (pages.dev 7.341)", "category_error_table.csv"],
        ["FP dan FN kategori query_present", "52 FP; 13 FN", "category_error_table.csv"],
        ["AUC tunggal tiga kolom A0 (URLSimilarityIndex; LineOfCode; NoOfExternalRef)",
         "0,9961; 0,9903; 0,9880", "phiusiil_leakage_audit.md"],
        ["Registrable domain unik dan baris ber-alamat IP pada PhiUSIIL", "175.509; 636",
         "phiusiil_leakage_audit.md"],
    ]
    heading_310 = doc.paragraphs[find_unique_para(doc, "3.10 Pembahasan")]
    lead10 = ("Tabel 10 merangkum angka deskriptif yang dibahas di luar tabel utama beserta artefak sumbernya, "
              "sehingga setiap angka yang dikutip di dalam teks dapat ditelusuri.")
    clone_para_before(heading_310, body_template, lead10)
    cap10 = ("Tabel 10. Angka deskriptif yang dilaporkan di luar Tabel 3 sampai Tabel 9 beserta artefak sumbernya.")
    caption_tpl = doc.paragraphs[find_unique_para(doc, "Tabel 1. Perbandingan desain")]
    clone_para_before(heading_310, caption_tpl, cap10)
    tbl10 = doc.add_table(rows=len(rows10), cols=3)
    tbl10.style = doc.tables[0].style
    for ri, row in enumerate(rows10):
        for ci, val in enumerate(row):
            cell = tbl10.rows[ri].cells[ci]
            para = cell.paragraphs[0]
            run = para.add_run(val)
            run.font.name = "Times New Roman"
            run.font.size = Pt(7)
            if ri == 0:
                run.bold = True
            cell.paragraphs[0].alignment = 1 if ri == 0 else 0
    heading_310._p.addprevious(tbl10._tbl)
    log.append({"change_id": "P1-029", "action_id": "dual-review C1", "type": "INSERT_TABLE",
                "locator": "before '3.10 Pembahasan' (new Tabel 10)",
                "before": "(absent)",
                "after": "Tabel 10 + lead-in sentence: 14 rows mapping prose-only figures to their source artefact",
                "evidence": "Experiment/5 summary (summary.csv, metrics_all.csv); Exp6 primary_seed_domain_bootstrap.csv; Exp4 results_per_seed.csv",
                "reason": "Angka yang hanya muncul di prosa tidak dapat diaudit dari tabel; tabel ini menautkannya ke artefak.",
                "refs": "-", "verification": "PASS"})


    # ---- 4. reference [12] page range -------------------------------------
    ref_i = find_unique_para(doc, "[12] Y. Yoga")
    p = doc.paragraphs[ref_i]
    target = [r for r in p.runs if r.text.strip().startswith(", vol. 7, no. 2")]
    if len(target) != 1:
        raise SystemExit("ABORT: [12] tail run not found uniquely")
    if target[0].text != REF12_OLD_TAIL:
        raise SystemExit(f"ABORT: [12] tail unexpected: {target[0].text!r}")
    target[0].text = REF12_NEW_TAIL
    log.append({"change_id": "P1-007", "action_id": "A16", "type": "REPLACE_REF_TAIL",
                "locator": f"paragraph[{ref_i}] run[2]", "before": REF12_OLD_TAIL, "after": REF12_NEW_TAIL,
                "evidence": "03_literature_A16/CURRENT_REFERENCE_AUDIT.csv (OpenAlex W7171518893)",
                "reason": "Rentang halaman referensi dilengkapi sesuai catatan penerbit.",
                "refs": "12", "verification": "PASS"})

    # ---- 5. new references 13..24 -----------------------------------------
    last_ref = doc.paragraphs[find_unique_para(doc, "[12] Y. Yoga")]
    cursor = last_ref
    for num, head, venue, tail in NEW_REFS:
        new_el = copy.deepcopy(last_ref._element)
        runs = new_el.findall(qn("w:r"))
        for r in runs[3:]:
            new_el.remove(r)
        keep = new_el.findall(qn("w:r"))
        texts = [f"[{num}] {head}", venue, tail]
        for r, txt in zip(keep, texts):
            for t in list(r.findall(qn("w:t"))):
                r.remove(t)
            t = r.makeelement(qn("w:t"), {})
            t.text = txt
            t.set(qn("xml:space"), "preserve")
            r.append(t)
        cursor._element.addnext(new_el)
        cursor = Paragraph(new_el, last_ref._parent)
    log.append({"change_id": "P1-008", "action_id": "A16", "type": "INSERT_REFERENCES",
                "locator": f"after paragraph[{ref_i}]", "before": "(12 references)",
                "after": f"24 references ([13]-[24] appended in first-appearance order within the new text)",
                "evidence": "03_literature_A16/SOURCE_LEDGER.csv (all 12 added sources verified against primary records)",
                "reason": "Menambah sumber primer terverifikasi untuk related work dan klaim komparatif.",
                "refs": "13-24", "verification": "PASS"})

    # ---- 3d. Lampiran A: protocol summary (Tabel A1) -----------------------
    rows_a1 = [
        ["Komponen", "Ringkasan terverifikasi"],
        ["Snapshot PhiUSIIL",
         "235.370 baris setelah pembersihan. Split memakai berkas beku split_random.csv dan split_sitedisjoint.csv "
         "(kolom seed, url_id, fold) untuk lima seed; lipatan val ada di berkas tetapi tidak dipakai pada protokol. "
         "Pada seed 13: acak 141.222 latih / 47.074 val / 47.074 uji; site-disjoint 143.800 / 48.280 / 43.290."],
        ["Snapshot PhreshPhish",
         "77 shard parquet (train-000... dan test-000...), 666.315 baris, 36,58 GB; SHA-256 per berkas tercatat pada "
         "input_manifest.json. Split resmi train/test dipakai apa adanya, bukan dibentuk ulang. Penanda tanggal "
         "diperlakukan sebagai tanggal pada berkas sumber."],
        ["Ledger eksklusi",
         "921 baris dikeluarkan dengan alasan tercatat: 681 setelah cutoff, 214 duplikat URL latih, 22 duplikat URL uji, "
         "3 URL uji terlihat di latih, dan 1 URL tak dapat diparse. Latih 498.255 menjadi 497.359; uji 168.060 menjadi 168.035."],
        ["Label",
         "Nilai sumber berupa string benign/phish dan dipetakan ke 0/1; pipeline menolak nilai label di luar himpunan itu, "
         "sehingga tidak ada label di luar domain yang masuk."],
        ["Konfigurasi fitur",
         "A0 47 fitur, A1 41 fitur, A2 18 fitur. Daftar ketiganya didefinisikan pada src/data.py; A2 mengikuti urutan "
         "feature_schema.json dengan sumber deterministic URL-only dan tanpa target encoding."],
        ["Ekstraktor A2",
         "src/features.py dengan SHA-256 c98b119c72c77df225bd21b7f803c367b71a934630622b3349ddecf349dc5864; "
         "dihitung deterministik per URL tanpa fitur halaman."],
        ["Model",
         "LightGBM 300 estimator, learning rate 0,05, 63 daun. XGBoost 300 estimator, learning rate 0,05, max_depth 8, "
         "eval_metric logloss, tree_method hist. Tidak ada penyetelan hiperparameter pada korpus target."],
        ["Lingkungan",
         "lightgbm 4.7.0, xgboost 3.4.1, scikit-learn 1.9.1, tldextract 5.4.0, pandas 3.1.0, NumPy 2.5.3; "
         "snapshot Public Suffix List ber-SHA-256 b69315c085d53972724b8f2df111ffc329b0c84fe0a47d62c8c91655cc774a38."],
        ["Bootstrap",
         "Interval persentil; unit registrable domain diresample dengan pengembalian, 1.000 replikasi, seed RNG 42. "
         "Varian berpasangan menjaga pasangan model tetap dan menghitung selisih pada replikasi yang sama."],
        ["Pemilihan ambang",
         "Aturan prediksi adalah skor >= ambang. Kandidat ambang adalah seluruh nilai probabilitas unik pada blok "
         "validasi, dan nilai kembar ditangani sebagai satu blok nilai."],
        ["Taksonomi",
         "14 domain platform eksplisit (github.io, pages.dev, vercel.app, netlify.app, weebly.com, wixsite.com, "
         "blogspot.com, wordpress.com, tumblr.com, typedream.app, gitlab.io, firebaseapp.com, web.app, workers.dev) "
         "dan 10 domain shortener; kategori biner: host_is_ip, host_punycode, query_present, scheme_https, "
         "domain_seen, shortener, platform."],
        ["Waktu komputasi",
         "Spesifikasi perangkat keras dan jumlah thread tidak dicatat pada artefak; angka waktu adalah log eksekusi, "
         "bukan pembandingan biaya komputasi."],
    ]
    last_ref = doc.paragraphs[find_unique_para(doc, "[24] T. Ahamed")]
    head_ref_tpl = doc.paragraphs[find_unique_para(doc, "REFERENCES")]
    _tmp: list = []
    cur = clone_para_after(last_ref, head_ref_tpl, "Lampiran A. Ringkasan Protokol untuk Replikasi", _tmp)
    cur = clone_para_after(cur, body_template,
                           "Lampiran ini merangkum protokol yang diperlukan untuk merekonstruksi eksperimen. "
                           "Setiap butir diambil dari artefak yang tersimpan, bukan dari rekonstruksi naratif. "
                           "Butir yang tidak tercatat pada artefak dinyatakan sebagai tidak tercatat, bukan diisi "
                           "dengan perkiraan.", _tmp)
    cur = clone_para_after(cur, caption_tpl,
                           "Tabel A1. Ringkasan protokol eksperimen dan provenance artefak.", _tmp)
    tbl_a1 = doc.add_table(rows=len(rows_a1), cols=2)
    tbl_a1.style = doc.tables[0].style
    for ri, row in enumerate(rows_a1):
        for ci, val in enumerate(row):
            cell = tbl_a1.rows[ri].cells[ci]
            cell.paragraphs[0].alignment = 0  # left-align: avoids stretched gaps around long hashes
            run = cell.paragraphs[0].add_run(val)
            run.font.name = "Times New Roman"
            run.font.size = Pt(7)
            if ri == 0:
                run.bold = True
    log.append({"change_id": "P1-047", "action_id": "external-review D2", "type": "INSERT_APPENDIX",
                "locator": "end of document, after [24] (Lampiran A, Tabel A1)",
                "before": "(absent)",
                "after": "Lampiran A + Tabel A1: 12-row protocol summary (snapshot, exclusion ledger, labels, feature configs, extractor hash, model config, environment, bootstrap, threshold rule, taxonomy, timing)",
                "evidence": "Exp4 canonical run input_manifest.json/output_manifest.json/excluded_rows.csv; Exp1 split_random.csv & split_sitedisjoint.csv; Exp5 src/data.py & features.py & preflight_report.md; Exp7 src/thresholds.py; Exp8 error_taxonomy.py",
                "reason": "Kekosongan D2 pada tinjauan eksternal: protokol tidak dapat direkonstruksi dari naskah.",
                "refs": "-", "verification": "PASS"})


    # ---- 6. config-table caption (renumbering already done in step 0) ------
    cfg_table_el = None
    tables_seen = 0
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:tbl"):
            tables_seen += 1
            if tables_seen == 2:
                cfg_table_el = child
                break
    if cfg_table_el is None:
        raise SystemExit("ABORT: configuration table not found")
    caption_tpl = doc.paragraphs[find_unique_para(doc, "Tabel 1. Perbandingan desain")]
    tpl_el = copy.deepcopy(caption_tpl._element)
    runs = tpl_el.findall(qn("w:r"))
    for r in runs[1:]:
        tpl_el.remove(r)
    r0 = tpl_el.findall(qn("w:r"))[0]
    for t in list(r0.findall(qn("w:t"))):
        r0.remove(t)
    t = r0.makeelement(qn("w:t"), {})
    t.text = NEW_CONFIG_CAPTION
    t.set(qn("xml:space"), "preserve")
    r0.append(t)
    cfg_table_el.addprevious(tpl_el)
    log.append({"change_id": "P1-014", "action_id": "A16/QA", "type": "INSERT_CAPTION",
                "locator": "before table[2] (feature configurations)",
                "before": "(no caption, no in-text reference)",
                "after": NEW_CONFIG_CAPTION,
                "evidence": "06_self_qa/P1_QA_REPORT.md (table caption/order audit)",
                "reason": "Tabel konfigurasi fitur sebelumnya tanpa nomor dan tanpa rujukan dalam teks.",
                "refs": "-", "verification": "PASS"})

    # ---- 7. availability paragraph (§5.2) ---------------------------------
    i = find_unique_para(doc, AVAILABILITY_OLD_PREFIX)
    p = doc.paragraphs[i]
    before = p.text
    p.runs[0].text = AVAILABILITY_NEW
    for r in p.runs[1:]:
        r._element.getparent().remove(r._element)
    log.append({"change_id": "P1-015", "action_id": "A13", "type": "REPLACE_PARA",
                "locator": f"paragraph[{i}] (§5.2 Ketersediaan Data)",
                "before": before[:240], "after": AVAILABILITY_NEW[:240],
                "evidence": "AI_Review_SINTA2_Package_v10_candidate/MANIFEST.csv; OMITTED_ARTIFACTS.csv",
                "reason": "Pernyataan ketersediaan harus sama persis dengan paket kandidat yang sebenarnya.",
                "refs": "-", "verification": "PASS"})

    # ---- 8. core properties ------------------------------------------------
    cp = doc.core_properties
    cp.title = CANDIDATE_TITLE
    cp.subject = CORE_SUBJECT_NEW
    cp.comments = CORE_COMMENT_NEW
    log.append({"change_id": "P1-016", "action_id": "metadata", "type": "META",
                "locator": "docProps/core.xml (dc:title, dc:subject, dc:description)",
                "before": "title='Audit Generalisasi ... — v8'; subject='Manuskrip v8 ...'; description='v8 menambahkan ... v7 tidak diubah.'",
                "after": f"title='{CANDIDATE_TITLE}'; subject='{CORE_SUBJECT_NEW}'; description='{CORE_COMMENT_NEW}'",
                "evidence": "01_figure_metadata_layout/REPORT.md",
                "reason": "Metadata versi masih menunjuk v8 pada dokumen v9/v10.",
                "refs": "-", "verification": "PASS"})

    # ---- write, then package-level post-processing -------------------------
    tmp = HERE / "_tmp_candidate.docx"
    doc.save(str(tmp))
    post = post_process_zip(tmp)
    shutil.copy2(tmp, OUT)
    tmp.unlink()
    log.extend(post)

    return {"source_sha256": src_hash, "candidate": str(OUT),
            "candidate_sha256": sha256_file(OUT), "changes": log}


def post_process_zip(docx_path: Path) -> list[dict]:
    """Replace Figure 1 media, refresh the picture name, and stamp version metadata."""
    log = []
    if not FIG_PNG.exists():
        raise SystemExit(f"ABORT: corrected Figure 1 PNG missing: {FIG_PNG}")
    new_png = FIG_PNG.read_bytes()
    tmp = docx_path.with_suffix(".repack.docx")
    with zipfile.ZipFile(docx_path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        names = zin.namelist()
        for name in names:
            data = zin.read(name)
            if name == "word/document.xml":
                xml = data.decode("utf8")
                if FIG_PIC_NAME_OLD not in xml and "figure_1_research_pipeline_v8\"" not in xml:
                    raise SystemExit("ABORT: figure picture name not found in document.xml")
                xml = re.sub(r"figure_1_research_pipeline_v8(\.png)?",
                             lambda m: "figure_1_research_pipeline_v10" + (m.group(1) or ""), xml)
                data = xml.encode("utf8")
            elif name == "word/media/image3.png":
                data = new_png
            elif name == "docProps/app.xml":
                s = data.decode("utf8")
                s, n1 = re.subn(r"<Pages>\d+</Pages>", f"<Pages>{WORD_PAGES}</Pages>", s)
                s, n2 = re.subn(r"<Words>\d+</Words>", f"<Words>{WORD_WORDS}</Words>", s)
                if n1 != 1 or n2 != 1:
                    raise SystemExit("ABORT: app.xml statistics elements not found exactly once")
                data = s.encode("utf8")
            zout.writestr(name, data)
    tmp.replace(docx_path)
    log.append({"change_id": "P1-017", "action_id": "A02", "type": "REPLACE_MEDIA",
                "locator": "word/media/image3.png (Figure 1 raster)",
                "before": "sha256 221d628fd0be38a08d0ca45bd7279e5a8774ff2b446c9a4c2511a78c3eae2004 (contains 'ceiling effect')",
                "after": f"sha256 {hashlib.sha256(new_png).hexdigest()} (containing 'saturasi benchmark, bootstrap domain berpasangan,')",
                "evidence": "01_figure_metadata_layout/figure_1_research_pipeline_v10.png; figure_1_wording_diff.txt",
                "reason": "Bitmap Figure 1 masih memuat istilah lama; prosa sudah memakai 'saturasi benchmark'.",
                "refs": "-", "verification": "PASS"})
    log.append({"change_id": "P1-018", "action_id": "metadata", "type": "META",
                "locator": "word/document.xml wp:docPr/@name for Figure 1",
                "before": FIG_PIC_NAME_OLD, "after": FIG_PIC_NAME_NEW,
                "evidence": "01_figure_metadata_layout/REPORT.md",
                "reason": "Nama berkas gambar tidak lagi menunjuk versi v8.",
                "refs": "-", "verification": "PASS"})
    log.append({"change_id": "P1-019", "action_id": "metadata", "type": "META",
                "locator": "docProps/app.xml (<Pages>, <Words>)",
                "before": "Pages=4, Words=1998 (stale v8 statistics)",
                "after": f"Pages={WORD_PAGES}, Words={WORD_WORDS} (measured with Word ComputeStatistics on the candidate)",
                "evidence": "06_self_qa/RENDER_LOG.json",
                "reason": "Properti statistik dokumen masih menunjuk render v8 dan tidak sesuai isi kandidat.",
                "refs": "-", "verification": "PASS"})
    return log


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true")
    args = ap.parse_args()

    if args.verify_only:
        if not OUT.exists():
            raise SystemExit("candidate not found")
        doc = docx.Document(str(OUT))
        with zipfile.ZipFile(OUT) as z:
            xml = z.read("word/document.xml").decode("utf8")
            media = hashlib.sha256(z.read("word/media/image3.png")).hexdigest()
        checks = {
            "candidate_sha256": sha256_file(OUT),
            "paragraphs": len(doc.paragraphs),
            "tables": len(doc.tables),
            "inline_shapes": len(doc.inline_shapes),
            "contains_ceiling_effect": "ceiling effect" in xml.lower() or "ceiling effect" in
                                      " ".join(p.text for p in doc.paragraphs).lower(),
            "image3_sha256": media,
            "title": doc.core_properties.title,
            "reference_count": sum(1 for p in doc.paragraphs if re.match(r"^\[\d+\] ", p.text or "")),
        }
        print(json.dumps(checks, indent=2, ensure_ascii=False))
        return 0

    result = build()
    HERE.mkdir(parents=True, exist_ok=True)
    (HERE / "change_log.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf8")
    rows = result["changes"]
    with (HERE / "CHANGE_REGISTER.csv").open("w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=["change_id", "action_id", "type", "locator", "before",
                                          "after", "evidence", "reason", "refs", "verification"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in w.fieldnames})
    print(json.dumps({k: v for k, v in result.items() if k != "changes"}, indent=2, ensure_ascii=False))
    print(f"changes registered: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())