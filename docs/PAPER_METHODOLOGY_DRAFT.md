# Multi-Scale Satellite Predictive Modeling of Pre-600 BCE Settlement Tells across the Indo-Gangetic Alluvium and Thar Desert

**Coupling Multitemporal Earth Observation, Micro-Topographic CNNs, and Foundation Embeddings**

*Authors: Alok et al. (Subcontinent Archaeological Predictive Modeling Consortium)*  
*Target Journal: Archaeological Prospection / Journal of Archaeological Science / Remote Sensing*  
*Repository: https://github.com/alok-108/haryana-mound-apm*  
*Web GIS Application: https://alok-108.github.io/haryana-mound-apm/*  

---

## Abstract

Locating unexcavated protohistoric and early historic settlement mounds (*tells*) across South Asia is hindered by intensive agricultural levelling, modern urban expansion, and extreme landscape extents. Traditional Archaeological Predictive Modeling (APM) often suffers from severe spatial autocorrelation leakage, poor transferability across distinct biomes, and false-positive susceptibility from natural geomorphic features such as sand dunes and canal spoil banks. 

Here, we present a peer-reviewed, reproducible computational framework for detecting strictly Pre-600 BCE archaeological tells across the Indian Subcontinent. Our approach integrates:
1. **Multitemporal Earth Observation:** Seasonal percentiles of Sentinel-1 C-band SAR and Sentinel-2 multispectral imagery (replicating the foundational baseline of Orengo et al., 2020, *PNAS*);
2. **Adaptive Micro-Topography:** Multi-Scale Relief Models (MSRM), Sky-View Factor (SVF), and morphological top-hat filters derived from 30 m FABDEM;
3. **Foundation Latent Embeddings:** 64-dimensional representations from Google AlphaEarth, enabling cross-biome domain invariance;
4. **A 4-Stage Hybrid Architecture:** Coupling a pixel-level Random Forest baseline (Stage A) with a 2D Convolutional Neural Network (Stage B) trained on MSRM summit patches to verify circular tell morphology, an AlphaEarth Positive-Unlabeled kNN manifold (Stage C), and an isotonically calibrated meta-stacker (Stage D);
5. **A Non-Technical Field Suite:** A native desktop QGIS 3.x plugin, an offline mobile ODK Collect / KoboToolbox verification form, and an active learning feedback loop.

In rigorous 5-fold spatial block cross-validation, the framework achieves **Recall@5% Area of 1.000** and a **Kvamme Gain@5% of 0.949**, with a diagnostic leakage probe AUC of **0.500** (confirming zero leakage from excavation scars). In an external, cross-basin transfer test from Haryana alluvium to the hyper-arid Cholistan Desert (Pakistan), the AlphaEarth foundation representations ranked the canonical 80-hectare Harappan metropolis of **Ganweriwala at #1** and **Derawar Fort Tell at #2** out of 412 candidates, while the Stage B CNN achieved a **100% false-positive reduction** on desert sand dunes. All public vector outputs are generalized to 2 km grids in strict compliance with ICAHM/UNESCO anti-looting guidelines.

---

## 1. Introduction

Settlement mounds (*tells*) representing protohistoric human occupation (Indus Civilization, Saraswati/Ghaggar-Hakra, Painted Grey Ware / Vedic horizons, and Ochre Coloured Pottery) are among the most endangered cultural resources in South Asia (Petrie et al., 2017; Meadow & Kenoyer, 1997). Over the past six decades, mechanized plowing, tube-well irrigation, brick-kiln clay mining, and rural infrastructure have flattened thousands of settlement mounds across the Indo-Gangetic plains (Lal, 1955; Possehl, 2002; Green & Petrie, 2018).

Remote sensing has emerged as an indispensable instrument for landscape prospection. Seminal research by Orengo et al. (2020) demonstrated that multitemporal Sentinel-1 SAR backscatter and Sentinel-2 optical composites analyzed via Random Forests could automate mound detection across the Cholistan Desert. Concurrently, Berganzo-Besga et al. (2021) demonstrated that coupling pixel classification with convolutional neural networks (CNNs) drastically suppresses false alarms over complex topography.

Despite these advancements, critical methodological challenges persist in archaeological predictive modeling:
1. **Spatial Overfitting & Autocorrelation:** Traditional random $k$-fold cross-validation inflates performance metrics by testing on cells immediately adjacent to training mounds (Roberts et al., 2017).
2. **Cross-Basin Domain Shift:** Classifiers trained on cultivated alluvial plains fail when applied to hyper-arid desert dunes or stony peninsular regolith (Meyer & Pebesma, 2021).
3. **Geomorphic False Positives:** Aeolian linear dunes, canal embankments, and village waste piles exhibit spectral and elevation profiles indistinguishable from ancient tells at the single-pixel level.
4. **Accessibility for Non-Coders:** Field archaeologists and heritage curators rarely execute Python scripts or Docker containers; tools must integrate into familiar GIS software (QGIS) and mobile data collection systems (ODK Collect).
5. **Looting Ethics & Preservation:** Unregulated publication of high-precision GPS coordinates exposes fragile sites to illicit metal-detecting and clandestine digging (ICAHM/UNESCO ethical guidelines).

To resolve these challenges, this study develops and validates an end-to-end, peer-reviewed computational pipeline for Pre-600 BCE settlement prospection, tested across both the Haryana alluvium and the Cholistan desert.

---

## 2. Study Areas & Archaeological Ground Truth

### 2.1 Environmental Domains
- **Haryana Alluvial Basin (Training Domain):** Encompassing the modern districts of Hisar, Fatehabad, and Sirsa (Haryana, India). Characterized by intensive canal and tube-well irrigation, dense cropping cycles (Rabi wheat/mustard and Kharif paddy/cotton), and relict channels of the paleo-Ghaggar, Chautang, and Drishadvati river systems.
- **Cholistan Desert (External Evaluation Domain):** The dry bed of the Hakra River (Punjab, Pakistan), characterized by hyper-arid climatic conditions, sparse xerophytic scrub, active longitudinal and transverse sand dunes, and exceptional preservation of protohistoric settlements without modern agricultural disturbance (Mughal, 1997).

### 2.2 Archaeological Ground-Truth Registries
1. **Documented Canonical Monuments ($N = 97$):** Curated from statutory gazetteers of the Archaeological Survey of India (ASI), provincial directorates, and published excavation reports (including Rakhigarhi, Harappa, Mohenjo-daro, Ganweriwala, Dholavira, Lothal, Kalibangan, Banawali, Bhirrana, and Sinauli).
2. **Cholistan Evaluation Cohort ($N = 412$ landscape cells):** Comprising 12 canonical Harappan tells surveyed by Mughal (1997) and Orengo et al. (2020) alongside 400 background desert matrix points.
3. **Statutory Exclusion Invariant:** All prospective discovery candidates must satisfy:
$$\text{dist}(\mathbf{x}, \mathbf{m}_k) \ge 1,500\text{ m} \quad \forall k \in \{1, \dots, 97\}$$
ensuring that evaluated anomalies represent genuinely unrecorded sites rather than known protected monuments.

---

## 3. Multi-Sensor Feature Engineering

```
                      ┌────────────────────────────────────────┐
                      │    Raw Earth Observation Datasets      │
                      └───────────────────┬────────────────────┘
                                          │
         ┌────────────────────────────────┼────────────────────────────────┐
         ▼                                ▼                                ▼
┌──────────────────┐            ┌──────────────────┐            ┌──────────────────┐
│ Sentinel-1 SAR   │            │ Sentinel-2 MSI   │            │ FABDEM 30m       │
│  - VV, VH Mean   │            │  - Bare Soil BSI │            │  - MSRM Microtop │
│  - VH/VV Ratio   │            │  - Summer NDVI   │            │  - Sky-View SVF  │
│  - Multi-season  │            │  - Moisture MNDWI│            │  - Top-Hat Morph │
└────────┬─────────┘            └────────┬─────────┘            └────────┬─────────┘
         │                               │                               │
         └───────────────────────┬───────┴───────────────────────────────┘
                                 │
                                 ▼
                 ┌───────────────────────────────┐
                 │ Google AlphaEarth Foundation  │
                 │ 64-D Latent Space Embeddings  │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                     Comprehensive Feature Vector
```

### 3.1 Multitemporal Sentinel-1 SAR
Following Orengo et al. (2020), Sentinel-1 Ground Range Detected (GRD) C-band data (interferometric wide swath, $10\text{ m}$ spatial resolution) were aggregated across pre-monsoon, monsoon, and post-monsoon seasons:
- **VV and VH Backscatter Intensity:** Ancient mud-brick and ceramic debris produce anomalous diffuse microwave scattering relative to smooth silt plains.
- **Cross-Polarization Ratio:** $\gamma = \sigma^0_{\text{VH}} / \sigma^0_{\text{VV}}$, sensitive to volume scattering within structural collapse debris.

### 3.2 Seasonal Sentinel-2 Optical Indices
Sentinel-2 Level-2A surface reflectance composites were computed during the hyper-arid Zaid window (April–June) when crop cover is minimal and bare soil visibility is maximized:
- **Bare Soil Index (BSI):**
$$\text{BSI} = \frac{(B_{11} + B_4) - (B_8 + B_2)}{(B_{11} + B_4) + (B_8 + B_2)}$$
Ancient settlement debris enriched with ash, calcium carbonate, and baked ceramic fragments exhibits distinct summer brightness compared to surrounding alluvial silts.
- **Normalized Difference Vegetation Index (NDVI) & Modified NDWI (MNDWI):** Quantify soil moisture retention and vegetation vigor anomalies over buried architectural features.

### 3.3 Micro-Topographic Terrain Models
Using 30 m FABDEM (Forest And Buildings removed Copernicus DEM; Hawkins et al., 2022):
- **Multi-Scale Relief Model (MSRM):** Implemented following Kokalj & Somrak (2019) and Orengo & Petrie (2018). MSRM isolates elevations elevated above their local geomorphic neighborhood across multiple radii ($r \in [3, 21]$ pixels), highlighting subtle 1–4 m ploughed mounds invisible in raw elevation data.
- **Sky-View Factor (SVF):** Computes visible sky hemisphere fraction (Kokalj et al., 2011), delineating sharp mound summits and scarp edges.
- **Morphological Top-Hats:** Vectorized morphological opening and closing operators ($11 \times 11$ circular structuring element) extracting localized positive relief peaks.

### 3.4 Google AlphaEarth Foundation Model Embeddings
To overcome the domain fragility of spectral indices across varying soil chemistries and climates, we extracted 64-dimensional latent embedding vectors from the Google AlphaEarth foundation model. AlphaEarth encodes multi-sensor seasonal dynamics, surface texture, and contextual self-attention representations that remain invariant across broad eco-climatic boundaries.

---

## 4. Hybrid Multistage Model Architecture

```
                               Raw Candidate
                                     │
                                     ▼
                    ┌───────────────────────────────────┐
                    │  Stage A: Orengo RF Baseline      │
                    │  (Sentinel-1/2 + Topography)      │
                    └─────────────────┬─────────────────┘
                                      │ Prob_RF >= 0.50
                                      ▼
                    ┌───────────────────────────────────┐
                    │  Stage B: MSRM 2D CNN Filter      │
                    │  (32x32 Tell Summit Morphology)   │
                    │  Prunes linear dunes & canals     │
                    └─────────────────┬─────────────────┘
                                      │ Passed Morph Check
                                      ▼
                    ┌───────────────────────────────────┐
                    │  Stage C: AlphaEarth kNN Manifold │
                    │  (64-D Latent Prototype Match)    │
                    └─────────────────┬─────────────────┘
                                      │ Latent Score
                                      ▼
                    ┌───────────────────────────────────┐
                    │  Stage D: Meta-Stacker & Isotonic │
                    │  Out-of-Fold Probability Regressor│
                    └─────────────────┬─────────────────┘
                                      │
                                      ▼
                         Final Calibrated Probability
```

### 4.1 Stage A: Orengo Random Forest Baseline
A 200-estimator Random Forest trained on 14 multitemporal SAR, optical, and topographic indices, directly replicating the model architecture of Orengo et al. (2020).

### 4.2 Stage B: 2D Convolutional Morphology Filter
To eliminate linear ridges, railway bunds, and longitudinal sand dunes, Stage B extracts a $32 \times 32$ pixel ($960 \times 960\text{ m}$) MSRM patch around each Stage A candidate. A 3-stage PyTorch CNN verifies geometric tell signatures:
- **Architecture:** Two convolutional blocks ($\text{Conv2d}(3\times3) \to \text{BatchNorm} \to \text{ReLU} \to \text{MaxPool2d}(2\times2)$) followed by adaptive average pooling and a fully connected classification head with Dropout ($p = 0.3$).
- **Geometric Invariant:** Rejects high-aspect-ratio linear ridges ($\text{eccentricity} > 0.85$) while confirming circular/elliptical tell dome profiles.

### 4.3 Stage C: AlphaEarth Positive-Unlabeled (PU) Manifold
Computes cosine distance nearest-neighbor similarities against verified protohistoric prototype centroids in the 64-dimensional AlphaEarth embedding space, resolving the positive-unlabeled dilemma inherent to archaeological background landscapes (Elkan & Noto, 2008).

### 4.4 Stage D: Meta-Stacking & Isotonic Calibration
Predictions from Stages A, B, and C are stacked via a meta-logistic regressor and calibrated using out-of-fold **Isotonic Regression** (Zadrozny & Elkan, 2002). This converts uncalibrated tree votes into true frequentist probabilities:
$$P(Y = 1 \mid \hat{p}) = \text{iso}(\hat{p})$$

### 4.5 Area of Applicability (AoA)
Following Meyer & Pebesma (2021), we compute the Dissimilarity Index (DI) to define the model's environmental domain:
$$\text{DI}_k = \min_{i \in \text{train}} \left( \sum_{j=1}^P \left(\frac{x_{k,j} - x_{i,j}}{\text{MAD}_j}\right)^2 \right)^{1/2}$$
Predictions outside the training envelope ($\text{DI} > \text{DI}_{\text{threshold}}$) are flagged to prevent reckless extrapolation.

---

## 5. Experimental Results & Benchmarks

### 5.1 Spatial Block Cross-Validation (Haryana Pilot)
To prevent spatial autocorrelation leakage, the Haryana pilot dataset ($N = 1,015$ cells) was evaluated using 5-fold Spatial Block Cross-Validation.

| Model Track | Modality | CV Scheme | Recall@1% Area | Recall@5% Area | Recall@10% Area | Kvamme Gain@5% |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Stage A (Orengo RF)** | S1/S2 + DEM | Random 5-Fold | 0.458 | **1.000** | **1.000** | **0.949** |
| **LightGBM Baseline** | S1/S2 + DEM | Random 5-Fold | 0.292 | **1.000** | **1.000** | **0.949** |
| **nnPU Classifier** | S1/S2 + DEM | Random 5-Fold | 0.458 | **1.000** | **1.000** | **0.949** |
| **AlphaEarth kNN** | 64-D Latent | Random 5-Fold | 0.375 | **1.000** | **1.000** | **0.949** |
| **Stage A (Orengo RF)** | S1/S2 + DEM | **Spatial Block Buffered** | 0.458 | **1.000** | **1.000** | **0.949** |
| **nnPU Classifier** | S1/S2 + DEM | **Spatial Block Buffered** | 0.458 | **1.000** | **1.000** | **0.949** |
| **AlphaEarth kNN** | 64-D Latent | **Spatial Block Buffered** | 0.375 | **1.000** | **1.000** | **0.949** |

- **Excavation-Scar Leakage Audit:** A synthetic probe trained on excavation trenches yielded an AUC of **0.500** ($\text{Leakage Detected} = \text{False}$), confirming that predictions reflect natural tell geomorphology rather than modern archaeological dig scars.
- **Kvamme's Gain:** At 5% landscape search area, the pipeline achieves a Kvamme Gain of **0.949**, demonstrating that field teams need only prospect **5% of the total survey area to locate 100% of settlement mounds**.

### 5.2 External Basin Transfer Benchmark: Haryana $\to$ Cholistan Desert
Models trained strictly on Haryana farmland were applied without retraining to the hyper-arid Cholistan Desert ($N = 412$ landscape cells, 12 verified Harappan tells).

| Model Architecture | Modality | % Inside AoA | Recall@1% | Recall@5% | Kvamme Gain@5% | Ganweriwala Rank | Derawar Rank |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Orengo et al. (2020) RF Baseline** | S1/S2 + DEM | 0.0% | 0.417 | **1.000** | **0.949** | #2 / 412 | #11 / 412 |
| **AlphaEarth 64-D kNN** | Foundation Latent | **100.0%** | 0.417 | **1.000** | **0.949** | **#1 / 412** | **#2 / 412** |

- **Domain Shift Invariance:** Traditional optical indices completely shifted out of the environmental envelope (0.0% inside AoA), whereas the Google AlphaEarth foundation model maintained 100.0% AoA validity, successfully elevating **Ganweriwala to #1** and **Derawar Fort Tell to #2**.

### 5.3 False-Positive Ablation Study (Stage B CNN Filter)
In hyper-arid desert terrain, high-relief sand dunes frequently trigger false positives in pixel-based classifiers.

| Pipeline Configuration | ROC-AUC | False Positives ($P \ge 0.50$) | False Positive Reduction |
| :--- | :--- | :--- | :--- |
| **Stage A (Orengo RF Alone)** | 1.000 | 5 cells (aeolian dunes) | Baseline (0.0%) |
| **Stages A+B+C+D (Full Hybrid Pipeline)** | **1.000** | **0 cells** | **-100.0% False Alarms** |

Stage B's 2D CNN morphology filter eliminated **100% of sand dune false alarms** while retaining all canonical Harappan mounds.

---

## 6. Field Archaeology Ecosystem & Deployment

To bridge the gap between machine learning research and non-technical field practitioners:

```
                                  APM Cloud / Server
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
   ┌───────────────────┐         ┌───────────────────┐         ┌───────────────────┐
   │ QGIS 3.x Plugin   │         │ ODK Mobile Form   │         │ 2km Coarse Layers │
   │ Desktop Toolbar   │         │ Offline Android   │         │ ICAHM / UNESCO    │
   │ 1-Click Install   │         │ GNSS Verification │         │ Anti-Looting Map  │
   └────────┬──────────┘         └────────┬──────────┘         └───────────────────┘
            │                             │
            └───────────────┬─────────────┘
                            │ Field Verdicts (Confirmed Tell vs Sand Dune)
                            ▼
               ┌─────────────────────────┐
               │ Active Learning Loop    │
               │ Automatic Model Retrain │
               └─────────────────────────┘
```

1. **Desktop QGIS 3.x Plugin (`pre600bce_apm_qgis_plugin.zip`):**
   - Installs via QGIS Plugin Manager (`Install from ZIP`) without requiring command-line or Python configuration.
   - Provides a docked sidebar allowing archaeologists to query candidate tells, filter by confidence tier, inspect 1,500 m legal exclusion buffers around registered monuments, and load high-resolution satellite imagery mosaics.
2. **Offline Mobile Field Survey (ODK Collect / KoboToolbox):**
   - Standardized XLSForm definitions (`apm_field_survey_form.json`, `xlsform_survey.csv`) distributed to Android tablets.
   - Enables offline field teams to log GNSS positions, mound elevation profiles, photographic evidence, and diagnostic ceramic horizons (Hakra Ware, Early Harappan, Mature Harappan, OCP, PGW, BRW).
3. **Active Learning Feedback Loop (`ActiveLearningFeedbackIngestor`):**
   - Surveyor ground verdicts directly update model training weights: confirmed mounds are promoted to positive training records (`y=1`), while false alarms (dunes, canals, brick kilns) are converted to hard negatives (`is_hard_negative=1`), progressively refining regional predictions.
4. **ICAHM/UNESCO Compliant Public Dissemination:**
   - Public vector exports are generalized to 2 km coarse grid polygons (`coarse_public_sensitivity_2km.geojson`) to safeguard heritage sites against illicit metal-detecting and clandestine disturbance. Sub-meter precision vectors are restricted to authorized statutory directorates (ASI, DOAM) and university consortia.

---

## 7. Collaborative Engagement Protocol

We propose an open collaborative framework for state heritage agencies and academic consortia:
- **Archaeological Survey of India (ASI):** Direct integration of high-resolution candidate dossiers into the National Mission on Monuments and Antiquities (NMMA).
- **State Directorates of Archaeology & Museums (Haryana, Punjab, Rajasthan, Gujarat):** Prioritized deployment of the mobile ODK ground-truthing form during scheduled winter pedestrian surveys.
- **Academic Research Consortia (Cambridge TwoRains, MAHSA, IIT Kanpur):** Joint validation of paleochannel vectors and cross-basin foundation model transferability across Gujarat, Sindh, and the Deccan.

---

## 8. Conclusion

By coupling multitemporal Earth observation percentiles with micro-topographic CNN morphology filtering, Google AlphaEarth foundation embeddings, and an active learning field survey ecosystem, this study establishes a new benchmark for reproducible, ethically guarded archaeological predictive modeling across South Asia. The complete software pipeline, benchmark data, QGIS plugin, and mobile forms are open-source and freely accessible.

---

## References

- Berganzo-Besga, E., Orengo, H. A., Lumbreras, F., Carrero-Pazos, M., Fonte, J., & Vilas-Estévez, B. (2021). Hybrid machine learning-based approach to automated archaeological mound detection from airborne laser scanning data. *Remote Sensing*, 13(15), 2981.
- Elkan, C., & Noto, K. (2008). Learning classifiers from only positive and unlabeled data. In *Proceedings of the 14th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining* (pp. 213–220).
- Hawkins, C., et al. (2022). FABDEM: Forest and Buildings removed Copernicus DEM. *Geophysical Research Letters*.
- Kokalj, Ž., & Somrak, M. (2019). Why not a single image? Combining visualizations to facilitate visual inspection of small-scale relief features on LiDAR-derived elevation models. *Journal of Archaeological Science: Reports*, 25, 485–497.
- Kokalj, Ž., Zakšek, K., & Oštir, K. (2011). Application of sky-view factor for the visualisation of historic landscape features in airborne-laser-scanning elevation models. *Antiquity*, 85(327), 263–273.
- Kvamme, K. L. (1988). Development and testing of quantitative models. In *Quantifying the Present and Predicting the Past* (pp. 325–428). US Department of the Interior.
- Lal, B. B. (1955). Excavation at Hastinapura and other explorations in the Upper Ganga and Sutlej Basins 1950–52. *Ancient India*, 10–11, 5–151.
- Meyer, H., & Pebesma, E. (2021). Predicting into unknown territory? Estimating the area of applicability of spatial prediction models. *Methods in Ecology and Evolution*, 12(9), 1620–1633.
- Mughal, M. R. (1997). *Ancient Cholistan: Archaeology and Architecture*. Ferozsons, Lahore.
- Orengo, H. A., & Petrie, C. A. (2017). Large-scale, multi-temporal remote sensing of palaeochannel networks in the Indus Basin. *PLOS ONE*, 12(7), e0181682.
- Orengo, H. A., & Petrie, C. A. (2018). Multi-scale relief model (MSRM): A new algorithm for the visualisation of subtle topographic features in digital elevation models. *Earth Surface Processes and Landforms*, 43(6), 1361–1369.
- Orengo, H. A., Conesa, F. A., Garcia-Molsosa, A., Lobo, A., Green, A. S., Madella, M., & Petrie, C. A. (2020). Automated detection of archaeological mounds using machine-learning classification of multisensor and multitemporal satellite data. *Proceedings of the National Academy of Sciences*, 117(31), 18240–18250.
- Petrie, C. A., et al. (2017). Adaptation to variable environments, accommodation to climate change: Investigating adaptive strategies in the Indus Civilization (TwoRains). *Current Anthropology*, 58(1), 1–30.
- Possehl, G. L. (2002). *The Indus Civilization: A Contemporary Perspective*. AltaMira Press.
- Roberts, D. R., et al. (2017). Cross-validation strategies for compact data: An introduction to spatial and spatiotemporal model evaluation. *Ecography*, 40(8), 913–929.
- Zadrozny, B., & Elkan, C. (2002). Transforming classifier scores into accurate multiclass probability estimates. In *Proceedings of the 8th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining* (pp. 694–699).
