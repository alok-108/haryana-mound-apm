# Haryana Mound APM (`haryana-mound-apm`)

[![CI](https://github.com/alok-108/haryana-mound-apm/actions/workflows/ci.yml/badge.svg)](https://github.com/alok-108/haryana-mound-apm/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Scoped, Leakage-Safe GeoAI Archaeological Mound Prospection & Spatial Evaluation Benchmark for the Haryana Ghaggar-Hakra / Chautang Interfluve (**Hisar, Fatehabad, and Sirsa** districts).

---

## 🎯 Research Objective
How much of published multi-sensor satellite mound-detection performance survives honest **buffered spatial block cross-validation** and **Area-of-Applicability (AoA)** masking once **excavation-scar leakage**, **label-provenance circularity**, and **detectability-coupled survey bias** are controlled—and do **Positive-Unlabelled (`SAR-nnPU`) learning** and **Google AlphaEarth 64-D embeddings (`A00`–`A63`)** improve recall on low-relief mounds?

---

## 🏗️ Repository Architecture
```text
haryana-mound-apm/
├── .github/workflows/ci.yml           # Automated CI testing matrix (Python 3.11, 3.12, 3.13)
├── config/
│   └── hisar_fatehabad_sirsa.yaml     # Study region bbox, CRS (EPSG:32643), GEE assets, hyperparams
├── data/
│   ├── raw/
│   │   └── public_ground_truth_sites.csv  # Curated published archaeological sites & unverified map mounds
│   ├── processed/
│   │   ├── haryana_h3_res8_features.csv   # Uber H3 Res 8 feature table (~74 ha cells)
│   │   └── haryana_patch250m_features.csv # Regular 250m spatial patch feature table (~6.25 ha)
│   └── README.md                      # Detailed schema specification and data guidelines
├── docs/
│   ├── RESEARCH_PLAN_AND_SPECIFICATION.md # Full research proposal, literature audit, causal framework
│   ├── BENCHMARK_METHODOLOGY.md       # Spatial units, CV splits, AoA masking, evaluation tracks
│   ├── PUBLIC_DATA_SOURCES.md         # Open-access gazetteers, ASI monument lists, publications
│   └── MAHSA_DATA_REQUEST_TEMPLATE.md # Formal data access request for MAHSA/TwoRains teams
├── results/
│   ├── figures/                       # Publication-quality benchmark visualization plots
│   │   ├── variogram_fit.png
│   │   ├── recall_at_k_curves.png
│   │   ├── aoa_dissimilarity_distribution.png
│   │   └── public_h3_res5_density_map.png
│   ├── BENCHMARK_RESULTS.md           # Rendered empirical results across all 28 runs
│   ├── benchmark_summary.csv          # 28-row benchmark evaluation summary
│   ├── stratified_metrics.csv         # Relief-class & modality stratified performance
│   ├── scar_leakage_audit.json        # Logistic excavation-scar diagnostic probe audit
│   ├── weak_label_soi_mounds.csv      # Unverified historical map mound evaluation
│   └── RESULTS_TEMPLATE.md            # Blank template for external replication
├── scripts/
│   ├── run_benchmark.py               # End-to-end benchmark execution CLI
│   └── generate_plots.py              # Figure generation CLI
├── src/
│   ├── benchmark_runner.py            # 7-track dual CV benchmark execution engine
│   ├── data_validator.py              # Strict data-schema validator
│   ├── feature_generator.py           # Offline regional feature generator & extractor
│   ├── gee_export.py                  # Earth Engine export pipeline (Sentinel-1/2, AlphaEarth, DEM)
│   ├── governance.py                  # Uber H3 Res 5/6 coordinate obfuscation & statutory field checks
│   ├── labels_and_leakage.py          # Role assignment, deduplication, TGB exclusion, scar masking
│   ├── models.py                      # RF, LightGBM, SAR-nnPU loss, AlphaEarth k-NN, Propensity
│   ├── public_data_curator.py         # Canonical published archaeological sites database
│   ├── validation.py                  # Variogram range, buffered block CV, AoA, Recall@k%
│   └── visualization.py               # Scientific visualization functions
├── tests/
│   └── test_pipeline.py               # 14 unit & integration verification tests
└── pyproject.toml                     # Pytest and packaging configuration
```

---

## ⚡ Quickstart

### 1. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/alok-108/haryana-mound-apm.git
cd haryana-mound-apm
python -m pip install -r requirements.txt  # or install numpy, scipy, pandas, scikit-learn, matplotlib, pyyaml, pytest
```

### 2. Run Verification Suite (14 Tests)
```bash
python -m pytest -v
```

### 3. Immediate Run with Curated Public Data
No waiting for external data access requests required. Generate the feature tables and run the full benchmark immediately:
```bash
# Generate curated public archaeological records and feature tables
python -c "from src.feature_generator import build_and_save_benchmark_datasets; build_and_save_benchmark_datasets()"

# Run benchmark across both spatial units (H3 Res 8 and 250m patches)
python -m scripts.run_benchmark --data-dir data/processed --config config/hisar_fatehabad_sirsa.yaml --spatial-unit both

# Generate scientific visualization figures
python -m scripts.generate_plots
```

---

## 📊 Benchmark Tracks

The benchmark evaluates **7 model and sensitivity configurations** across **2 cross-validation schemes** and **2 spatial units** (28 runs total):

| Track ID | Model | Features | Propensity Adjustment | Primary Hypothesis |
| :--- | :--- | :--- | :--- | :--- |
| **T1** | Random Forest | Sentinel-1/2 + FABDEM | None | Baseline (following Orengo et al. 2020) |
| **T2** | LightGBM / HistGB | Sentinel-1/2 + FABDEM | None | Modern gradient boosting comparison |
| **T3a** | `SAR-nnPU` | Sentinel-1/2 + FABDEM | None (Unweighted) | Positive-Unlabelled learning on unlabelled background |
| **T3b** | `SAR-nnPU` | Sentinel-1/2 + FABDEM | Weighted (IPW) | Sensitivity analysis against detectability-coupled survey bias |
| **T4** | Embedding $k$-NN | AlphaEarth 64-D (`A00`–`A63`) | None | Unsupervised self-supervised representation retrieval |
| **T5a** | `SAR-nnPU` | AlphaEarth 64-D + FABDEM | None (Unweighted) | Foundation embedding + topography fusion |
| **T5b** | `SAR-nnPU` | AlphaEarth 64-D + FABDEM | Weighted (IPW) | Foundation embedding + topography with IPW sensitivity |

### Spatial Cross-Validation Schemes
1. **Random 5-Fold CV:** Baseline evaluation (subject to spatial autocorrelation over-optimism).
2. **Buffered Spatial Block 5-Fold CV:** Grid blocks sized by the empirical environmental variogram range ($a \ge 25\text{ km}$) with a strict **5,000 m dead-zone buffer** separating training and validation points to eliminate spatial leakage.

---

## 🏛️ Anti-Looting Data Governance
In compliance with the **Ancient Monuments and Archaeological Sites and Remains (AMASR) Act 1958** and international antiquities preservation standards:
- **No Public Coordinate Release:** Exact site coordinates (`latitude`, `longitude`, `x_m`, `y_m`) are strictly scrubbed from public outputs.
- **Coarse Obfuscation Grid:** Public heatmaps and predictions are aggregated strictly to **Uber H3 Resolution 5 hexagons ($\sim 252\text{ km}^2$)** with $k$-anonymity suppression ($k \ge 5$).
- **Fieldwork Permissions:** In-situ survey or surface collection requires prior statutory permission from the Archaeological Survey of India (ASI) / Haryana State Department of Archaeology and a recognized institutional partner.

---

## 📚 Documentation
- [Benchmark Methodology](docs/BENCHMARK_METHODOLOGY.md)
- [Public Archaeological Data Sources](docs/PUBLIC_DATA_SOURCES.md)
- [Full Research Plan & Specification](docs/RESEARCH_PLAN_AND_SPECIFICATION.md)
- [MAHSA / TwoRains Data Request Template](docs/MAHSA_DATA_REQUEST_TEMPLATE.md)
- [Empirical Benchmark Results](results/BENCHMARK_RESULTS.md)

---

## 📜 Citation
```bibtex
@software{haryana_mound_apm2026,
  author = {Pandey, Alok},
  title = {Haryana Mound APM: Scoped, Leakage-Safe GeoAI Archaeological Mound Prospection & Spatial Evaluation Benchmark},
  year = {2026},
  publisher = {GitHub},
  url = {https://github.com/alok-108/haryana-mound-apm}
}
```
