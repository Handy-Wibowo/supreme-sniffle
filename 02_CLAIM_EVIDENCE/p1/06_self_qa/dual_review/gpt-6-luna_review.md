C1 **PASS**. Klaim kuantitatif utama dapat ditelusuri ke tabel, gambar, atau paragraf yang menyebut artefak sumbernya, dan tidak tampak kontradiksi aritmetika yang fatal. Perbedaan antara nilai seed tunggal dan rerata lima seed dijelaskan secara eksplisit, demikian pula perbedaan Tabel 6 dan Tabel 8 karena model yang dilatih berbeda; namun klaim rentang selisih antarprotokol sebagian bergantung pada Tabel 10 dan berkas artefak yang tidak tersedia dalam naskah.  
**Evidence:** [P086]–[P090], [P108]–[P110], [P124]–[P127], [TABLE 10].

C2 **PASS**. Manuskrip secara konsisten menyatakan bahwa penelitian tidak mengusulkan model baru, tidak mengklaim state of the art, tidak membuktikan mekanisme kausal, tidak melakukan evaluasi buta/prospektif, dan tidak menggeneralisasi hasil ke seluruh korpus phishing. Klaim deployment juga dibatasi sebagai proyeksi skenario dan trade-off ambang, bukan jaminan FPR produksi atau kesiapan operasional.  
**Evidence:** [P009], [P012], [P029]–[P031], [P069]–[P070], [P114]–[P116], [P142]–[P147].

C3 **PASS**. Seluruh koreksi khusus yang diminta dipertahankan: polaritas sumber PhiUSIIL dan pemetaan analisis, pengecualian metrik E3, pembedaan seed bootstrap 42 dan seed model 13, ketidaktersediaan interval klaster platform, status deskriptif 37,1%, cakupan 85 fit terpilih, provenance A0/A1 yang tidak diketahui, A2 sebagai kontrak, serta status analisis tanpa-overlap sebagai sensitivitas. Tidak ditemukan pernyataan yang mengubah salah satu koreksi tersebut menjadi klaim yang lebih kuat.  
**Evidence:** [P041], [P046], [P053], [P060]–[P061], [P067]–[P068], [P073], [P083]–[P084], [P131]–[P146].

C4 **PASS**. Sitasi umumnya ditempelkan pada klaim yang sesuai dan klaim komparatif dibatasi sebagai prinsip metodologis, bukan pemindahan angka antar-korpus. Namun, literatur tentang pemilihan ambang berbasis biaya, kalibrasi di bawah perubahan prevalensi, dan domain adaptation/transfer phishing URL masih kurang eksplisit; [21]–[22] hanya mendukung dasar base-rate dan precision–recall, bukan keseluruhan literatur operating-point selection. Kesesuaian rinci beberapa klaim terhadap isi sumber, khususnya [2] dan [24], **UNVERIFIABLE** dari manuskrip saja karena hanya metadata sitasi yang tersedia.  
**Evidence:** [P015]–[P028], [P063], [P070], [P127], [P179]–[P202].

C5 **PASS**. Kebaruan dirumuskan sebagai rantai evaluasi terintegrasi—audit benchmark, pembagian berbasis domain, ablasi, evaluasi temporal, transfer beku satu arah, pemilihan ambang, dan taksonomi galat—bukan sebagai keunggulan model. Framing ini defensible terhadap literatur terdekat karena penulis secara eksplisit tidak memindahkan angka dari studi lain dan membatasi kontribusi pada pasangan korpus serta desain yang diuji.  
**Evidence:** [P025], [P028], [P031]–[P036], [P138]–[P142].

C6 **BLOCK**. Struktur naskah, penomoran tabel/gambar, kesesuaian abstrak bilingual, daftar referensi, batasan, kontribusi penulis, konflik kepentingan, pendanaan, dan pernyataan AI secara umum lengkap. Masalah utama adalah pernyataan ketersediaan data/artefak tidak memberikan URL repositori, DOI, atau lokasi paket yang dapat diperiksa, sementara paket tersebut juga tidak memuat data mentah, split lengkap, prediksi per baris, atau model; akibatnya klaim “dapat diaudit” tidak dapat diverifikasi oleh pembaca dari naskah ini. Pernyataan IRB dan informed consent “Tidak Berlaku” juga tidak diberi justifikasi khusus untuk penggunaan korpus URL publik, meskipun hal ini bukan cacat utama dibandingkan masalah akses artefak.  
**Evidence:** [P167] menyatakan paket dan manifest tetapi tidak mencantumkan lokasi akses; [P170]–[P175] memberikan pernyataan etik tanpa alasan metodologis; [P037] dan [P178]–[P202] menunjukkan struktur serta referensi yang tersedia.

C7 **BLOCK**. Lima isu risiko tertinggi adalah:

1. **High — Provenance fitur A0/A1 tidak diketahui, padahal hasil benchmark utama dan narasi saturasi bergantung padanya.** Manuskrip mengakui bahwa populasi referensi, waktu komputasi, producer hulu, dan ketergantungan label fitur tersimpan tidak diketahui, serta hanya membuktikan kebocoran pada probe historis, bukan pada kolom yang sekarang dipakai. **Fix minimum:** rerun hasil benchmark dengan fitur yang dihitung ulang melalui pipeline yang provenance-nya terdokumentasi, atau turunkan A0/A1 menjadi analisis eksploratif dan jangan menjadikannya dasar utama kesimpulan saturasi.  
   **Evidence:** [P047], [P061], [P081]–[P084], [P138]–[P144].

2. **High — Artefak yang diklaim dapat diaudit tidak dapat diakses atau diidentifikasi lokasinya dari naskah.** Tanpa repositori/DOI dan tanpa split, prediksi, model, serta data yang diperlukan, pembaca tidak dapat memeriksa angka transfer, bootstrap, taksonomi galat, atau klaim deterministik. **Fix minimum:** cantumkan URL repositori publik atau DOI beserta versi/commit, checksum paket, instruksi memperoleh data sumber, dan artefak minimum untuk mereproduksi seluruh tabel.  
   **Evidence:** [P040], [P041], [P135]–[P136], [P167].

3. **High — Kohort uji temporal telah diperiksa dalam pekerjaan eksploratif sebelumnya, sehingga statusnya bukan evaluasi independen atau holdout yang belum tersentuh.** Pengungkapan ini jujur, tetapi membuat angka temporal dan pemilihan ambang rentan terhadap seleksi atau pengetahuan sebelumnya, terutama karena kohort yang sama dipakai dalam beberapa analisis. **Fix minimum:** tambahkan kohort waktu baru yang belum pernah diperiksa dengan protokol akses label yang terdokumentasi; bila tidak memungkinkan, ubah semua klaim menjadi hasil eksploratif dan jelaskan bahwa interval yang dilaporkan bukan validasi eksternal.  
   **Evidence:** [P029], [P075], [P107], [P142], [P147].

4. **Medium — Detail reproducibility untuk pembentukan split dan pemrosesan waktu masih tidak cukup lengkap dalam teks.** Naskah menyebut seed dan kebijakan domain, tetapi tidak memberikan seluruh konfigurasi pembagian, prosedur penanganan timestamp yang tidak valid/duplikat lintas blok, atau artefak split yang dapat diperiksa. **Fix minimum:** sertakan algoritme/pseudocode split, daftar parameter lengkap, aturan timestamp dan timezone, serta hash atau berkas indeks setiap fold.  
   **Evidence:** [P050]–[P054], [P075], [P167].

5. **Medium — Validitas eksternal transfer tetap sangat sempit dan satu arah, sementara target PhreshPhish juga dipakai untuk evaluasi temporal dan thresholding.** Penulis telah membatasi klaimnya, tetapi pembaca belum memperoleh pengujian arah PhreshPhish→PhiUSIIL, korpus ketiga, atau periode tambahan untuk membedakan kegagalan pasangan tertentu dari pola yang lebih umum. **Fix minimum:** tambahkan setidaknya satu arah transfer balik atau korpus/periode eksternal baru; jika tidak, pindahkan hasil transfer ke status studi kasus eksploratif dan pertegasnya pada judul, abstrak, serta kesimpulan.  
   **Evidence:** [P048], [P072]–[P073], [P117]–[P122], [P142].

OVERALL: BLOCK