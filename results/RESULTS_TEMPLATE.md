# Empirical Benchmark Results Template (Populate Only via `scripts/run_benchmark.py`)

> **Zero-Fabrication Notice:** All numeric cells below are intentionally left blank (`[TBD]`). Populate strictly by executing `python -m scripts.run_benchmark --data-dir data/processed --config config/hisar_fatehabad_sirsa.yaml` after placing processed GEE + MAHSA/TwoRains feature tables in `data/processed/`.

## 1. Excavation-Scar Leakage Diagnostic Probe (`results/scar_leakage_audit.json`)
*Trained on confirmed archaeological sites to test whether feature extraction can predict `is_protected_or_excavated`.*

| Feature Extraction Mode | $N_{\text{protected/excavated}}$ | $N_{\text{unexcavated}}$ | 5-Fold Stratified Probe ROC-AUC | Threshold ($\le 0.60$) | Diagnostic Status (`PASS`/`FAIL`) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Raw Unmasked Center ($0\text{–}75\text{ m}$) | `[TBD]` | `[TBD]` | `[TBD]` | $\le 0.60$ | `[TBD]` |
| Annular Agricultural Halo ($75\text{–}250\text{ m}$) | `[TBD]` | `[TBD]` | `[TBD]` | $\le 0.60$ | `[TBD]` |

---

## 2. Main Ablation Matrix: Random 5-Fold CV vs. Buffered Spatial Block 5-Fold CV (`results/benchmark_summary.csv`)
*Spatial block side length $L_{\text{block}} = 1.25 \times \hat{r}_{\text{eff}} =$ `[TBD]` $\text{km}$; Dead-zone buffer $= 5.0\text{ km}$.*
*Positives for training = Ground-confirmed, unexcavated sites ONLY (`is_ground_confirmed == True` & `is_protected_or_excavated == False`).*

| Track ID & Architecture | Feature Set & Aggregation | CV Scheme | Recall@1% | Recall@2% | Recall@5% | Recall@10% | Kvamme's Gain $G$@5% | AoA Retention (%) | Random $\to$ Spatial $\Delta\text{Recall@5\%}$ |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **T1: Random Forest (Orengo 2020)** | S1/S2 + FABDEM (max, p95) | Random 5-Fold | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | — |
| **T1: Random Forest (Orengo 2020)** | S1/S2 + FABDEM (max, p95) | Spatial Block (5 km Buffer) | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` |
| **T2: LightGBM / HistGB Baseline** | S1/S2 + FABDEM (max, p95) | Random 5-Fold | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | — |
| **T2: LightGBM / HistGB Baseline** | S1/S2 + FABDEM (max, p95) | Spatial Block (5 km Buffer) | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` |
| **T3a: SAR-nnPU (Unweighted)** | S1/S2 + FABDEM (max, p95) | Random 5-Fold | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | — |
| **T3a: SAR-nnPU (Unweighted)** | S1/S2 + FABDEM (max, p95) | Spatial Block (5 km Buffer) | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` |
| **T3b: SAR-nnPU (Propensity-Weighted)** | S1/S2 + FABDEM (Sensitivity Analysis) | Spatial Block (5 km Buffer) | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` |
| **T4: Prototype Cosine $k$-NN** | AlphaEarth (`A00`–`A63`) Only | Random 5-Fold | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | — |
| **T4: Prototype Cosine $k$-NN** | AlphaEarth (`A00`–`A63`) Only | Spatial Block (5 km Buffer) | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` |
| **T5a: SAR-nnPU (Unweighted)** | AlphaEarth (`A00`–`A63`) + FABDEM | Random 5-Fold | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | — |
| **T5a: SAR-nnPU (Unweighted)** | AlphaEarth (`A00`–`A63`) + FABDEM | Spatial Block (5 km Buffer) | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` |
| **T5b: SAR-nnPU (Propensity-Weighted)** | AlphaEarth + FABDEM (Sensitivity Analysis) | Spatial Block (5 km Buffer) | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` | `[TBD]` |

---

## 3. Stratified Evaluation by Mound Relief, Discovery Modality & Protected Status (`results/stratified_metrics.csv`)
*Evaluated on out-of-fold predictions from Buffered Spatial Block CV.*

| Track ID | Stratum Dimension | Stratum Value | $N_{\text{positives}}$ | Buffered Spatial Recall@5% | Buffered Spatial Gain $G$@5% |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **T1–T5** | `relief_class` | `high_>=1.5m` (Prominent / Unlevelled) | `[TBD]` | `[TBD]` | `[TBD]` |
| **T1–T5** | `relief_class` | `low_<1m` (Levelled / Low-Relief) | `[TBD]` | `[TBD]` | `[TBD]` |
| **T1–T5** | `discovery_modality` | `pedestrian_transect` (Ground-walked) | `[TBD]` | `[TBD]` | `[TBD]` |
| **T1–T5** | `discovery_modality` | `toposheet_symbol` (SOI 1-inch confirmed) | `[TBD]` | `[TBD]` | `[TBD]` |
| **T1–T5** | `held_out_protected_status` | `protected_or_excavated` (Held-out Stratum) | `[TBD]` | `[TBD]` | `[TBD]` |

---

## 4. Weak-Label Evaluation Experiment on Unverified Historical Map Mounds (`results/weak_label_soi_mounds.csv`)
*Evaluates how often models trained strictly on ground-confirmed sites independently flag unverified Survey of India 1-inch map mounds.*

| Track ID & Architecture | $N_{\text{unverified_mounds}}$ | Buffered Spatial Recall@5% on Map Mounds | Kvamme's Gain $G$@5% |
| :--- | :---: | :---: | :---: |
| **T1: Random Forest (Orengo 2020)** | `[TBD]` | `[TBD]` | `[TBD]` |
| **T2: LightGBM / HistGB Baseline** | `[TBD]` | `[TBD]` | `[TBD]` |
| **T3a: SAR-nnPU (S1/S2 + FABDEM)** | `[TBD]` | `[TBD]` | `[TBD]` |
| **T4: Prototype Cosine $k$-NN (AlphaEarth Only)** | `[TBD]` | `[TBD]` | `[TBD]` |
| **T5a: SAR-nnPU (AlphaEarth + FABDEM)** | `[TBD]` | `[TBD]` | `[TBD]` |

---

## 5. Spatial Unit Comparison: H3 Resolution 8 (~74 ha) vs. 250m Regular Patch (~6.25 ha)
| Spatial Unit | Median Mound Area (% of cell) | Feature Aggregation | Best Track | Spatial Block Recall@5% on `low_<1m` |
| :--- | :---: | :---: | :---: | :---: |
| **Uber H3 Resolution 8** | $\sim 1.3\%\text{ to }6.8\%$ | `max`, `p90`, `p95` | `[TBD]` | `[TBD]` |
| **Regular Spatial Patch ($250\text{ m} \times 250\text{ m}$)** | $\sim 16\%\text{ to }80\%$ | `max`, `p90`, `p95` | `[TBD]` | `[TBD]` |
