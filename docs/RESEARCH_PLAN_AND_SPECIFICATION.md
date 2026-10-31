# GeoAI Archaeological Predictive Modelling & Prospection Framework (Haryana Scoped Pilot)

## Executive Summary & Research Scope
This document specifies the research architecture, causal observation model, and spatial evaluation protocol for automated archaeological mound prospection and predictive modelling in the **Ghaggar-Hakra / Chautang interfluve** of northwest India, specifically focusing on **Hisar, Fatehabad, and Sirsa districts** of Haryana.

The framework answers a central methodological question:
> **How much of published satellite mound-detection performance survives honest buffered spatial block cross-validation and Area-of-Applicability (AoA) masking once excavation-scar leakage, label-provenance circularity, and detectability-coupled survey bias are controlled—and do Positive-Unlabelled (`SAR-nnPU`) learning and AlphaEarth 64-D embeddings (`A00`–`A63`) improve recall on low-relief mounds?**

---

## 1. Causal Observation Model & Mathematical Formalisation

We decompose the probability that cell $c$ appears as a recorded positive in the archaeological inventory into five conditionally sequential factors:

$$P\big(Y^{\text{obs}}_c=1 \mid \mathbf{x}_c\big) = \underbrace{P\big(E_c=1 \mid \mathbf{x}^{\text{env}}_c\big)}_{\text{1. Existed (Suitability)}} \cdot \underbrace{P\big(S_c=1 \mid E_c=1, \mathbf{x}^{\text{taph}}_c\big)}_{\text{2. Survived (Preservation)}} \cdot \underbrace{P\big(D_c=1 \mid S_c=1, \mathbf{x}^{\text{sens}}_c\big)}_{\text{3. Detectable (Visibility)}} \cdot \underbrace{P\big(V_c=1 \mid D_c=1, M^{\text{SOI}}_c, \mathbf{b}^{\text{access}}_c\big)}_{\text{4. Detectability-Dependent Survey Effort}} \cdot P\big(R_c=1 \mid V_c, D_c\big)$$

### Critical Causal Corrections:
1. **Coupling Survey Effort to Detectability:**
   Legacy surveyors and TwoRains field teams visited mounds preferentially because they were visible on Survey of India historical maps ($M^{\text{SOI}}_c=1$) or prominent in local topography ($\text{MSRM}_c$). Treating survey effort $V_c$ as independent of physical detectability $D_c$ creates backdoor bias. We model selection propensity $e(c) = P(V_c=1 \mid D_c=1, M^{\text{SOI}}_c, \mathbf{b}^{\text{access}}_c)$ as an explicit function of detectability and accessibility.
2. **Partial Identifiability & Sensitivity Framing:**
   Because survey effort and settlement suitability are only weakly separable from observational presence-only data, propensity weighting is framed as a **rigorous sensitivity analysis** comparing unweighted vs. weighted tracks.
3. **Palimpsest-Safe Target-Group Background (TGB):**
   Multi-period mounds (e.g. Harappan + PGW + Early Historic) cannot be treated as pseudo-absences for other horizons. A site is eligible as a TGB pseudo-absence only if it is confirmed for another horizon and located $> 500\text{ m}$ away from any target-horizon presence.

---

## 2. Multi-Sensor Physics & Feature Engineering

1. **Sentinel-2 Multispectral Time Series (2018–2024, `COPERNICUS/S2_SR_HARMONIZED`):**
   - Cloud masking via Scene Classification Layer (`SCL`).
   - Seasonal percentiles (10th, 50th, 90th) in the late-Rabi moisture stress window (February–March) capturing negative crop marks over buried walls and compacted floors.
   - Post-harvest bare-soil medians in the Zaid window (April–May) capturing anthrosol brightness and fired-brick iron oxide redness.
2. **Sentinel-1 C-Band SAR (`COPERNICUS/S1_GRD`):**
   - Multi-year seasonal percentiles of dual-polarization backscatter ($\sigma^0_{\text{VV}}, \sigma^0_{\text{VH}}$) capturing surface micro-roughness from potsherd scatters and soil dielectric moisture contrasts.
3. **Micro-Topographic Derivatives (`FABDEM` / `COPERNICUS/DEM/GLO30`):**
   - **Multi-Scale Relief Model (MSRM; Orengo & Petrie 2018, doi:10.1002/esp.4317):** Gaussian band-pass filter banks across $30\text{–}300\text{ m}$ scales.
   - **Morphological Top-Hat Transforms:** White Top-Hat ($\text{WTH}_r = Z - (Z \circ b_r)$) isolating positive mound relief and Black Top-Hat ($\text{BTH}_r = (Z \bullet b_r) - Z$) isolating silted moats and relict channels at radii $r \in \{60, 150, 300\}\text{ m}$.
4. **Google AlphaEarth Foundations (`GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`):**
   - Pre-computed 64-dimensional unit-norm annual embeddings (`A00` through `A63`).
   - **Strict Anti-Double-Counting Protocol:** Evaluated as an alternative representation against raw S1/S2 features by ablation, never naively concatenated with raw S1/S2 bands.
5. **Spatial Aggregation via `max`, `p90`, and `p95`:**
   - Evaluated across both **Uber H3 Resolution 8** (~74 ha) and **250 m regular spatial patches** (~6.25 ha) using extreme percentiles rather than arithmetic mean to prevent subtle 1–5 ha mounds from being averaged out by surrounding agricultural fields.

---

## 3. Label Roles, Leakage Protections & Competing Tracks

### Sample Role Assignment:
- **`train_positive`:** Ground-confirmed, unexcavated archaeological sites (`is_ground_confirmed == True` & `is_protected_or_excavated == False`).
- **`eval_protected_positive`:** Ground-confirmed sites with active protection or excavation trenches. Strictly held out from training; evaluated as an isolated diagnostic stratum.
- **`unverified_map_mound`:** Historical Survey of India map symbols without field confirmation. Strictly excluded from both training positives and background; evaluated in a separate weak-label experiment.
- **`unlabelled_background`:** Landscape cells with no recorded mound or map symbol.

### Competing Benchmark Tracks:
| Track ID | Architecture | Input Feature Representation | Objective Function |
| :--- | :--- | :--- | :--- |
| **`T1_RF_S1S2_FABDEM`** | Random Forest (500 trees) | S1/S2 + FABDEM (`max, p95`) | Replicating Orengo et al. (2020) baseline |
| **`T2_LGBM_S1S2_FABDEM`** | LightGBM / HistGB | S1/S2 + FABDEM (`max, p95`) | Balanced cross-entropy |
| **`T3a_SAR_nnPU_S1S2_FABDEM_Unweighted`** | Non-Negative PU Classifier | S1/S2 + FABDEM (`max, p95`) | Kiryo et al. (2017) nnPU risk clamp |
| **`T3b_SAR_nnPU_S1S2_FABDEM_PropensityWeighted`** | Non-Negative PU Classifier | S1/S2 + FABDEM (`max, p95`) | Bekker & Davis (2020) inverse propensity weighting |
| **`T4_KNN_AlphaEarth_Only`** | Prototype Cosine Similarity | AlphaEarth 64-D (`A00`–`A63`) | $k$-NN with hard-negative suppression |
| **`T5a_SAR_nnPU_AlphaEarth_FABDEM_Unweighted`** | Non-Negative PU Classifier | AlphaEarth 64-D + FABDEM | nnPU risk clamp combining embeddings & DEM |
| **`T5b_SAR_nnPU_AlphaEarth_FABDEM_PropensityWeighted`** | Non-Negative PU Classifier | AlphaEarth 64-D + FABDEM | Propensity-weighted sensitivity track |

---

## 4. Spatial Validation & Governance

1. **Variogram-Sized Spatial Block CV with 5 km Dead-Zone Buffer:**
   - Empirical semivariogram range $\hat{r}_{\text{eff}}$ determines block width $L_{\text{block}} = \max(25\text{ km}, 1.25\,\hat{r}_{\text{eff}})$.
   - All training cells within $5,000\text{ m}$ of any test cell in that fold are eliminated to prevent spatial autocorrelation leakage.
2. **Area of Applicability (AoA; Meyer & Pebesma 2021):**
   - Dissimilarity Index $DI_c \le \tau_{\text{AoA}}$ flags extrapolation beyond the environmental training envelope.
3. **Stratified Recall@k% and Kvamme's Gain:**
   - Stratified separately by **mound relief class** (`high_>=1.5m` vs. `low_<1m`) and **discovery modality** (`pedestrian_transect` vs. `toposheet_symbol`).
4. **Anti-Looting Coordinate Obfuscation:**
   - Public maps aggregate predictions strictly to **Uber H3 Resolution 5/6** with $k$-anonymity ($n \ge 5$). Raw coordinates (`lat, lon, x_m, y_m, site_name`) are stripped.
5. **Fieldwork & Surface Collection Governance:**
   - *No fieldwork or surface collection without written permission from ASI/the State Department and an institutional partner; legal basis to be confirmed with them.*
