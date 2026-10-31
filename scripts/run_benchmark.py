"""
Command-Line Entry Point to Execute the Scoped Haryana Benchmark (Hisar, Fatehabad, Sirsa).
Integrates strict schema validation, executes all model tracks under Random vs. Spatial Block CV,
and writes empirical numbers to `results/`.

Usage:
    python -m scripts.run_benchmark --data-dir data/processed --config config/hisar_fatehabad_sirsa.yaml
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import yaml

from src.data_validator import load_and_validate_processed_dataset
from src.gee_export import ALPHAEARTH_BANDS
from src.benchmark_runner import evaluate_benchmark_tracks


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Haryana Mound APM Spatial Benchmark")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/processed",
        help="Path to processed data directory containing feature Parquet/CSV tables",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/hisar_fatehabad_sirsa.yaml",
        help="Path to YAML configuration file",
    )
    parser.add_argument("--output-dir", type=str, default="results", help="Output directory for empirical results")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # 1. Strictly validate dataset schema & presence of ground-truth confirmation flags
    df, resolved_path = load_and_validate_processed_dataset(processed_dir=args.data_dir)
    print(f"Loaded and validated dataset from: {resolved_path} ({len(df)} rows)")

    dem_only_cols = [c for c in df.columns if c.startswith(("msrm", "wth_", "bth_"))]
    s1_s2_cols = [c for c in df.columns if c.startswith(("B", "NDVI", "NDWI", "BSI", "NDRE", "VV", "VH"))]
    s1_s2_dem_cols = s1_s2_cols + dem_only_cols

    summary_df, stratified_df, scar_audit, weak_label_df = evaluate_benchmark_tracks(
        df=df,
        s1_s2_dem_cols=s1_s2_dem_cols,
        dem_only_cols=dem_only_cols,
        embedding_cols=ALPHAEARTH_BANDS,
        prior_pi_p=float(cfg["models"]["nnpu"]["default_prior_pi_p"]),
        dead_zone_buffer_m=float(cfg["validation"]["dead_zone_buffer_m"]),
        random_state=int(cfg["project"]["random_seed"]),
    )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(out_dir / "benchmark_summary.csv", index=False)
    stratified_df.to_csv(out_dir / "stratified_metrics.csv", index=False)
    if not weak_label_df.empty:
        weak_label_df.to_csv(out_dir / "weak_label_soi_mounds.csv", index=False)
    with open(out_dir / "scar_leakage_audit.json", "w", encoding="utf-8") as f:
        json.dump(scar_audit, f, indent=2)

    print("Benchmark complete. Empirical outputs written to:", out_dir.resolve())


if __name__ == "__main__":
    main()
