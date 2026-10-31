# Haryana Mound APM (`haryana-mound-apm`)

Scoped, Leakage-Safe GeoAI Archaeological Mound Prospection & Spatial Evaluation Benchmark for the Haryana Ghaggar-Hakra / Chautang Interfluve (**Hisar, Fatehabad, and Sirsa** districts).

## Research Question
How much of published multi-sensor satellite mound-detection performance survives honest **buffered spatial block cross-validation** and **Area-of-Applicability (AoA)** masking once **excavation-scar leakage**, **label-provenance circularity**, and **detectability-coupled survey bias** are controlled—and do **Positive-Unlabelled (`SAR-nnPU`) learning** and **AlphaEarth 64-D embeddings (`A00`–`A63`)** improve recall on low-relief mounds?

## Repository Layout
- `config/hisar_fatehabad_sirsa.yaml` — CRS (`EPSG:32643`), H3 Resolution 8 (`0.531 km` edge), GEE asset IDs, and hyperparameter configuration.
- `src/gee_export.py` — Google Earth Engine export pipeline for Orengo et al. (2020) Sentinel-1/2 seasonal composites, Orengo & Petrie (2018) Multi-Scale Relief Model (`MSRM`) + White/Black Top-Hats (`WTH`/`BTH`) on FABDEM/GLO-30, dynamic year querying of `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` (`A00`–`A63`), and spatial feature aggregation (`max`, `p90`, `p95`).
- `src/labels_and_leakage.py` — Spatial-phonetic site deduplication, sample role assignment (`train_positive`, `eval_protected_positive`, `unverified_map_mound`, `unlabelled_background`), palimpsest-safe Target-Group Background (`TGB`) selection (500 m buffer exclusion), annular-halo excavation-scar masking, and the logistic excavation-scar leakage probe.
- `src/models.py` — `DetectabilityCoupledSurveyPropensity` (sensitivity analysis proxy), Random Forest baseline (`Orengo 2020`), `LightGBM / HistGB`, `TabularNNPUClassifier` with `SARNonNegativePULoss` (`Kiryo et al. 2017` + `Bekker & Davis 2020`), and `AlphaEarthEmbeddingKNN`.
- `src/validation.py` — Empirical variogram range estimation, buffered spatial block CV (5 km dead-zone buffer), `Meyer & Pebesma (2021)` Area of Applicability (`AoA`), and Recall@k% / Kvamme's Gain stratified by mound relief and discovery modality.
- `src/data_validator.py` — Strict dataset schema validator that fails loudly if `data/processed/` is empty or missing mandatory columns.
- `src/governance.py` — Public H3 Resolution 5/6 coordinate obfuscation with $k$-anonymity ($n \ge 5$) and `PartnerFieldExportAdapter` enforcing written permission from ASI/State Department and institutional partner before surface collection export.
- `scripts/run_benchmark.py` — End-to-end CLI benchmark runner.
- `tests/test_pipeline.py` — Automated pytest suite (10 unit & integration tests covering spatial buffer enforcement, TGB multi-period exclusion, nnPU risk clamping, normalized weights, coordinate stripping, role assignment, and schema validation).
- `data/README.md` — Specification of required MAHSA/TwoRains fields and acquisition instructions.
- `results/RESULTS_TEMPLATE.md` — Zero-fabrication results template with unpopulated (`[TBD]`) cells.

## Running Tests
```bash
python -m pytest -v
```

## Running the Benchmark
```bash
python -m scripts.run_benchmark --data-dir data/processed --config config/hisar_fatehabad_sirsa.yaml
```
