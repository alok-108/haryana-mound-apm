# Haryana Mound APM: Benchmark Methodology & Evaluation Guide

This document describes the design, execution, and interpretation of the benchmark implemented in `scripts/run_benchmark.py`.

## 1. The 7 Evaluated Benchmark Tracks

All tracks are evaluated across two spatial validation schemes:
1. **Stratified 5-Fold Random CV:** Baseline machine-learning split (illustrating apparent performance under spatial autocorrelation).
2. **Buffered Spatial Block 5-Fold CV:** Blocks sized to $L_{\text{block}} = 1.25\,\hat{r}_{\text{eff}}$ (typically $\ge 25\text{ km}$) with a strict $5,000\text{ m}$ dead-zone buffer around test blocks.

### Track List:
- **`T1_RF_S1S2_FABDEM`:** Random Forest (500 trees, balanced subsampling) on multi-year Sentinel-1/2 percentiles and FABDEM (MSRM + Top-Hats). Directly replicates Orengo et al. (2020).
- **`T2_LGBM_S1S2_FABDEM`:** Gradient Boosted Decision Tree (LightGBM / HistGradientBoosting) with balanced class weights.
- **`T3a_SAR_nnPU_S1S2_FABDEM_Unweighted`:** Tabular neural non-negative PU learning with random Fourier feature expansion and Kiryo et al. (2017) risk clamping.
- **`T3b_SAR_nnPU_S1S2_FABDEM_PropensityWeighted`:** Sensitivity-analysis variant of T3 incorporating detectability-dependent selection propensity weights ($w_i = 1/e(c_i)$).
- **`T4_KNN_AlphaEarth_Only`:** Cosine similarity $k$-NN against unexcavated confirmed site prototypes using Google AlphaEarth 64-D annual embeddings (`A00`–`A63`), with hard-negative prototype subtraction.
- **`T5a_SAR_nnPU_AlphaEarth_FABDEM_Unweighted`:** Competing PU model combining AlphaEarth 64-D embeddings and FABDEM micro-relief.
- **`T5b_SAR_nnPU_AlphaEarth_FABDEM_PropensityWeighted`:** Sensitivity-analysis variant of T5 incorporating selection propensity weights.

---

## 2. Dual Spatial Units

The pipeline supports and evaluates two spatial resolution units:
1. **Uber H3 Resolution 8 Hexagons ($\sim 74\text{ ha}$, average edge $531.4\text{ m}$):**
   - High-level regional indexing unit.
   - Micro-topographic and spectral features aggregated using `max`, `p90`, and `p95` (never mean, which dilutes 1–5 ha mounds).
2. **Regular Spatial Patches ($250\text{ m} \times 250\text{ m} \approx 6.25\text{ ha}$):**
   - Centred closely on typical protohistoric South Asian mound footprints (1–5 ha).
   - Higher signal-to-background concentration for tractor-levelled tells.

---

## 3. Metrics Computed

1. **Recall@k% Area ($k \in \{1\%, 2\%, 5\%, 10\%\}$):**
   $$\text{Recall@}k\% = \frac{\sum_{i=1}^{N_{\text{top-}k\%}} \mathbb{I}(y_i = 1)}{N_{\text{positives}}}$$
2. **Kvamme's Gain ($G$):**
   $$G = 1 - \frac{\%\text{ Area}}{\%\text{ Sites Detected}}$$
3. **Random-to-Spatial CV Gap:**
   $$\Delta\text{Recall@5\%} = \text{Recall@5\%}_{\text{Random}} - \text{Recall@5\%}_{\text{Spatial}}$$
4. **Area of Applicability Retention (%):**
   Percentage of evaluation cells satisfying Meyer & Pebesma (2021) Dissimilarity Index threshold ($DI_c \le \tau_{\text{AoA}}$).
5. **Stratification Subsets:**
   - Relief: `high_>=1.5m` vs. `low_<1m`
   - Discovery Modality: `pedestrian_transect` vs. `toposheet_symbol`
   - Diagnostic Held-out Stratum: `eval_protected_positive`
   - Weak-Label Experiment: `unverified_map_mound`
