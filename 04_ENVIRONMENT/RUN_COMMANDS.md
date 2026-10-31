# Tested commands

```
# 1. P0 regression verifier on the unchanged v9_P0 baseline
cd E:\Kuliah\Tugas Akhir\phishing\revision_v9_p0\04_integrated_manuscript
python apply_p0_revisions.py --verify-only

# 2. Deterministic relationship check
python verify_package_relationships.py ..\..\BITS_Draft_Phishing_URL_Leakage_v9_P0.docx

# 3. Rebuild the candidate from v9_P0
cd E:\Kuliah\Tugas Akhir\phishing\revision_v10_p1\05_integrated_manuscript
python apply_p1_revisions.py

# 4. Package integrity
cd E:\Kuliah\Tugas Akhir\phishing\AI_Review_SINTA2_Package_v10_candidate
sha256sum -c MANIFEST.sha256
```
