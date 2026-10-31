# Data Requirements & Schema Documentation for Haryana Scoped APM

This repository operates on processed tabular Parquet/CSV feature tables constructed from **Google Earth Engine (GEE)** exports joined with **MAHSA / TwoRains** archaeological site and historical map-mound records over **Hisar, Fatehabad, and Sirsa** districts (Haryana).

## 1. Directory Structure
```
data/
├── README.md               # This documentation
├── raw/                    # Raw institutional gazetteers & shapefiles (Restricted / Local only)
│   ├── mahsa_sites_haryana.csv
│   └── soi_map_mounds_haryana.geojson
└── processed/              # Formatted feature & label tables (Used by scripts/run_benchmark.py)
    ├── haryana_h3_res8_features.parquet
    └── haryana_patch250m_features.parquet
```

## 2. Required Fields for `data/processed/*.parquet`
Every processed table evaluated by `scripts/run_benchmark.py` must contain:

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `cell_id` (or `site_id`) | string | Unique spatial cell identifier (e.g. H3 index `886194...` or patch ID `patch_2891`) |
| `x_m` | float | Projected Easting in **EPSG:32643** (WGS 84 / UTM zone 43N, meters) |
| `y_m` | float | Projected Northing in **EPSG:32643** (WGS 84 / UTM zone 43N, meters) |
| `lat`, `lon` | float | Geographic coordinates in WGS 84 (used for H3 indexing & coarse public obfuscation) |
| `y_obs` | int (0 or 1) | Binary observation indicator (1 = positive sample, 0 = unlabelled/background) |
| `is_ground_confirmed` | bool | **Mandatory:** `True` ONLY if verified as an archaeological site via pedestrian survey or excavation. `False` for unverified historical map symbols! |
| `is_protected_or_excavated` | bool | **Mandatory:** `True` if monument is ASI/State protected or has open trenches/fences/sheds. These are **dropped from training positives** and evaluated as a separate stratum. |
| `discovery_modality` | string | One of: `'pedestrian_transect'`, `'toposheet_symbol'`, `'satellite_visual'`, `'chance_find_construction'`, `'legacy_gazetteer'` |
| `relief_class` | string | `'high_>=1.5m'` (prominent mound) or `'low_<1m'` (levelled / low-relief mound) |
| `dist_road_km` | float | Distance to nearest paved road in km (accessibility covariate) |
| `dist_town_km` | float | Distance to nearest district town/tehsil HQ in km (accessibility covariate) |
| `msrm` | float | Multi-Scale Relief Model score (from FABDEM / GLO-30) |
| `wth_150m` | float | Morphological White Top-Hat at 150m radius (positive mound relief) |
| `bth_150m` | float | Morphological Black Top-Hat at 150m radius (negative moat/depression) |
| `NDVI_p50` | float | Median late-Rabi NDVI from Sentinel-2 |
| `BSI_zaid_med` | float | Median Zaid bare-soil index from Sentinel-2 |
| `VH_p50` | float | Median cross-polarized backscatter ($\sigma^0_{\text{VH}}$) from Sentinel-1 |
| `A00` through `A63` | float | 64-dimensional unit-norm annual embedding from `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` |

## 3. How to Obtain / Request the Archaeological Ground-Truth Data
1. **MAHSA (Mapping Archaeological Heritage in South Asia):**
   - Platform: `mahsa.arch.cam.ac.uk` (University of Cambridge / ICAC / BHU).
   - Contains digitized TwoRains survey records (Petrie, Green, Singh, Alam et al.) across Haryana and Punjab.
   - Request access via an institutional research agreement or academic data-sharing request to the MAHSA PI team.
2. **Survey of India Historical 1-inch to 1-mile Maps:**
   - Map sheets for Hisar, Fatehabad, and Sirsa (pre-1947 SOI sheets 44 O, 44 P, 53 B, 53 C).
   - Scanned map collections are preserved at the British Library, Cambridge University Library, and National Library of Australia.
3. **Data Protection & Legal Notice:**
   - In compliance with Indian antiquities governance and anti-looting guidelines, exact geographic coordinates of unprotected candidate sites must **never** be committed to public repositories.
