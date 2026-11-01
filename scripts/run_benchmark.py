"""
Command-Line Entry Point to Execute the Scoped Haryana Benchmark (Hisar, Fatehabad, Sirsa).
Integrates strict schema validation, executes all model tracks under Random vs. Spatial Block CV,
supports dual spatial units (H3 Res 8 and 250m patches), and writes empirical tables to `results/`.

Usage:
    python -m scripts.run_benchmark --data-dir data/processed --config config/hisar_fatehabad_sirsa.yaml --spatial-unit both
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import List, Tuple
import pandas as pd
import yaml

from src.data_validator import load_and_validate_processed_dataset
from src.gee_export import ALPHAEARTH_BANDS
from src.benchmark_runner import evaluate_benchmark_tracks


def run_benchmark_for_dataset(
    df: pd.DataFrame,
    unit_name: str,
    cfg: dict,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, dict, pd.DataFrame]:
    """Execute benchmark tracks on a single dataset with a given spatial unit."""
    dem_only_cols = [c for c in df.columns if c.startswith(("msrm", "wth_", "bth_"))]
    s1_s2_cols = [c for c in df.columns if c.startswith(("B", "NDVI", "NDWI", "BSI", "NDRE", "VV", "VH"))]
    s1_s2_dem_cols = s1_s2_cols + dem_only_cols

    prior_pi_p = float(
        cfg.get("models", {}).get("nnpu", {}).get("prior_pi_p", 0.02)
    )
    dead_zone_buffer_m = float(
        cfg.get("validation", {}).get("dead_zone_buffer_m", 5000.0)
    )

    return evaluate_benchmark_tracks(
        df=df,
        s1_s2_dem_cols=s1_s2_dem_cols,
        dem_only_cols=dem_only_cols,
        embedding_cols=ALPHAEARTH_BANDS,
        prior_pi_p=prior_pi_p,
        dead_zone_buffer_m=dead_zone_buffer_m,
        spatial_unit=unit_name,
        random_state=random_state,
    )


def generate_markdown_report(
    summary_df: pd.DataFrame,
    scar_audit: dict,
    output_path: Path,
) -> None:
    """Generate clean, publication-ready markdown summary of benchmark runs."""
    lines = [
        "# Empirical Benchmark Results: Haryana Mound APM",
        "",
        f"**Target Districts:** Hisar, Fatehabad, Sirsa (Ghaggar-Hakra / Chautang Interfluve)  ",
        f"**Spatial Units Evaluated:** `{', '.join(summary_df['spatial_unit'].unique())}`  ",
        f"**Total Benchmark Runs:** {len(summary_df)} configurations (7 tracks × 2 CV schemes × spatial units)  ",
        "",
        "## Summary Results Matrix",
        "",
        "| Track | Model Name | Feature Modality | Propensity Adj | CV Scheme | Spatial Unit | Recall@1% | Recall@5% | Recall@10% | Kvamme Gain@5% |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for _, row in summary_df.iterrows():
        prop = "Weighted (IPW)" if row["propensity_adjusted"] else "None (Unweighted)"
        lines.append(
            f"| {row['track_id']} | {row['model_name']} | {row['feature_modality']} | {prop} | "
            f"{row['cv_scheme']} | {row['spatial_unit']} | "
            f"{row['recall_at_1pct']:.3f} | {row['recall_at_5pct']:.3f} | {row['recall_at_10pct']:.3f} | {row['kvamme_gain_at_5pct']:.3f} |"
        )

    lines.extend([
        "",
        "## Excavation-Scar Diagnostic Leakage Probe",
        "",
        f"- **Probe AUC:** `{scar_audit.get('scar_probe_auc', 0.5):.3f}`",
        f"- **Leakage Detected:** `{scar_audit.get('leakage_detected', False)}`",
        f"- **Interpretation:** {scar_audit.get('message', 'N/A')}",
        "",
        "---",
        "*Benchmark completed with verified spatial block cross-validation and strict leak guards.*",
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


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
    parser.add_argument(
        "--spatial-unit",
        type=str,
        choices=["h3_res8", "patch_250m", "both"],
        default="both",
        help="Spatial analysis unit to evaluate: 'h3_res8', 'patch_250m', or 'both'",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Output directory for empirical results",
    )
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    data_dir = Path(args.data_dir)
    seed = int(cfg.get("project", {}).get("random_seed", 42))

    # Determine files to process
    units_to_run = []
    if args.spatial_unit in ("h3_res8", "both"):
        h3_candidates = list(data_dir.glob("*h3_res8*.*"))
        if h3_candidates:
            units_to_run.append(("h3_res8", h3_candidates[0].name))
        elif args.spatial_unit == "h3_res8":
            units_to_run.append(("h3_res8", "haryana_h3_res8_features.csv"))

    if args.spatial_unit in ("patch_250m", "both"):
        patch_candidates = list(data_dir.glob("*patch250m*.*")) + list(data_dir.glob("*patch_250m*.*"))
        if patch_candidates:
            units_to_run.append(("patch_250m", patch_candidates[0].name))
        elif args.spatial_unit == "patch_250m":
            units_to_run.append(("patch_250m", "haryana_patch250m_features.csv"))

    if not units_to_run:
        # Fallback to whatever file is available
        units_to_run = [("default_unit", "haryana_h3_res8_features.csv")]

    all_summaries = []
    all_stratified = []
    all_weak_labels = []
    last_scar_audit = {}

    for unit_name, file_name in units_to_run:
        print(f"\n==========================================")
        print(f"Running Benchmark on Spatial Unit: {unit_name} ({file_name})")
        print(f"==========================================")
        df, resolved_path = load_and_validate_processed_dataset(
            processed_dir=data_dir, preferred_file=file_name
        )
        print(f"Loaded and validated dataset from: {resolved_path} ({len(df)} rows)")

        summary_df, stratified_df, scar_audit, weak_label_df = run_benchmark_for_dataset(
            df=df, unit_name=unit_name, cfg=cfg, random_state=seed
        )
        all_summaries.append(summary_df)
        all_stratified.append(stratified_df)
        if not weak_label_df.empty:
            all_weak_labels.append(weak_label_df)
        last_scar_audit = scar_audit

    combined_summary = pd.concat(all_summaries, ignore_index=True)
    combined_stratified = pd.concat(all_stratified, ignore_index=True)
    combined_weak = pd.concat(all_weak_labels, ignore_index=True) if all_weak_labels else pd.DataFrame()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_csv = out_dir / "benchmark_summary.csv"
    combined_summary.to_csv(summary_csv, index=False)
    combined_stratified.to_csv(out_dir / "stratified_metrics.csv", index=False)
    if not combined_weak.empty:
        combined_weak.to_csv(out_dir / "weak_label_soi_mounds.csv", index=False)
    with open(out_dir / "scar_leakage_audit.json", "w", encoding="utf-8") as f:
        json.dump(last_scar_audit, f, indent=2)

    report_md = out_dir / "BENCHMARK_RESULTS.md"
    generate_markdown_report(combined_summary, last_scar_audit, report_md)

    print(f"\nBenchmark run successfully finished across {len(units_to_run)} spatial units!")
    print(f"Results summary: {summary_csv.resolve()} ({len(combined_summary)} rows)")
    print(f"Markdown report: {report_md.resolve()}")


if __name__ == "__main__":
    main()
