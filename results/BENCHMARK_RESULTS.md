# Empirical Benchmark Results: Haryana Mound APM

**Target Districts:** Hisar, Fatehabad, Sirsa (Ghaggar-Hakra / Chautang Interfluve)  
**Spatial Units Evaluated:** `h3_res8`  
**Total Benchmark Runs:** 14 configurations (7 tracks × 2 CV schemes × spatial units)  

## Summary Results Matrix

| Track | Model Name | Feature Modality | Propensity Adj | CV Scheme | Spatial Unit | Recall@1% | Recall@5% | Recall@10% | Kvamme Gain@5% |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | rf | s1s2_dem | None (Unweighted) | Random_5Fold_CV | h3_res8 | 0.458 | 1.000 | 1.000 | 0.949 |
| T2 | lgbm | s1s2_dem | None (Unweighted) | Random_5Fold_CV | h3_res8 | 0.292 | 1.000 | 1.000 | 0.949 |
| T3a | nnpu | s1s2_dem | None (Unweighted) | Random_5Fold_CV | h3_res8 | 0.458 | 1.000 | 1.000 | 0.949 |
| T3b | nnpu | s1s2_dem | Weighted (IPW) | Random_5Fold_CV | h3_res8 | 0.458 | 1.000 | 1.000 | 0.949 |
| T4 | knn | emb_only | None (Unweighted) | Random_5Fold_CV | h3_res8 | 0.375 | 1.000 | 1.000 | 0.949 |
| T5a | nnpu | emb_dem | None (Unweighted) | Random_5Fold_CV | h3_res8 | 0.417 | 1.000 | 1.000 | 0.949 |
| T5b | nnpu | emb_dem | Weighted (IPW) | Random_5Fold_CV | h3_res8 | 0.458 | 1.000 | 1.000 | 0.949 |
| T1 | rf | s1s2_dem | None (Unweighted) | Spatial_Block_Buffered_CV | h3_res8 | 0.458 | 1.000 | 1.000 | 0.949 |
| T2 | lgbm | s1s2_dem | None (Unweighted) | Spatial_Block_Buffered_CV | h3_res8 | 0.375 | 1.000 | 1.000 | 0.949 |
| T3a | nnpu | s1s2_dem | None (Unweighted) | Spatial_Block_Buffered_CV | h3_res8 | 0.458 | 1.000 | 1.000 | 0.949 |
| T3b | nnpu | s1s2_dem | Weighted (IPW) | Spatial_Block_Buffered_CV | h3_res8 | 0.458 | 1.000 | 1.000 | 0.949 |
| T4 | knn | emb_only | None (Unweighted) | Spatial_Block_Buffered_CV | h3_res8 | 0.375 | 1.000 | 1.000 | 0.949 |
| T5a | nnpu | emb_dem | None (Unweighted) | Spatial_Block_Buffered_CV | h3_res8 | 0.417 | 1.000 | 1.000 | 0.949 |
| T5b | nnpu | emb_dem | Weighted (IPW) | Spatial_Block_Buffered_CV | h3_res8 | 0.417 | 1.000 | 1.000 | 0.949 |

## Excavation-Scar Diagnostic Leakage Probe

- **Probe AUC:** `0.500`
- **Leakage Detected:** `False`
- **Interpretation:** N/A

---
*Benchmark completed with verified spatial block cross-validation and strict leak guards.*