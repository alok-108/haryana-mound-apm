"""
Command-Line Script to Generate All Scientific Benchmark Visualizations.
Outputs figures to `results/figures/`:
1. variogram_fit.png
2. recall_at_k_curves.png
3. aoa_dissimilarity_distribution.png
4. public_h3_res5_density_map.png

Usage:
    python -m scripts.generate_plots
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

from src.data_validator import load_and_validate_processed_dataset
from src.validation import compute_area_of_applicability
from src.visualization import (
    plot_aoa_dissimilarity_distribution,
    plot_empirical_variogram,
    plot_public_obfuscated_map,
    plot_recall_at_k_curves,
)


def main() -> None:
    data_dir = Path("data/processed")
    results_dir = Path("results")
    fig_dir = results_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load feature dataset for variogram and AoA
    df, resolved = load_and_validate_processed_dataset(data_dir, preferred_file="haryana_h3_res8_features.csv")
    print(f"Loaded dataset: {resolved} ({len(df)} rows)")

    coords_m = df[["x_m", "y_m"]].to_numpy(dtype=float)
    dem_cols = [c for c in df.columns if c.startswith(("msrm", "wth_", "bth_"))]
    s1s2_cols = [c for c in df.columns if c.startswith(("B", "NDVI", "NDWI", "BSI", "NDRE", "VV", "VH"))]
    X_features = df[s1s2_cols + dem_cols].to_numpy(dtype=float)

    # 2. Plot variogram fit
    range_km = plot_empirical_variogram(
        coords_m=coords_m,
        features=X_features,
        output_path=fig_dir / "variogram_fit.png",
    )
    print(f"Generated: {fig_dir / 'variogram_fit.png'} (Estimated Range: {range_km:.1f} km)")

    # 3. Plot Recall@k% curves if benchmark summary exists
    summary_csv = results_dir / "benchmark_summary.csv"
    if summary_csv.exists():
        plot_recall_at_k_curves(
            summary_csv_path=summary_csv,
            output_path=fig_dir / "recall_at_k_curves.png",
        )
        print(f"Generated: {fig_dir / 'recall_at_k_curves.png'}")

    # 4. Compute and plot Meyer & Pebesma Area of Applicability (AoA)
    # Train on confirmed positives + unlabelled background subset, query on remaining
    is_confirmed = (df["is_ground_confirmed"] == True).to_numpy()
    tr_idx = np.where(is_confirmed)[0]
    qu_idx = np.where(~is_confirmed)[0]
    di_scores, _, threshold = compute_area_of_applicability(X_train=X_features[tr_idx], X_query=X_features[qu_idx])

    plot_aoa_dissimilarity_distribution(
        di_scores=di_scores,
        threshold=threshold,
        output_path=fig_dir / "aoa_dissimilarity_distribution.png",
    )
    print(f"Generated: {fig_dir / 'aoa_dissimilarity_distribution.png'}")

    # 5. Plot public obfuscated coarse H3 Res 5 density map
    plot_public_obfuscated_map(
        df=df,
        output_path=fig_dir / "public_h3_res5_density_map.png",
    )
    print(f"Generated: {fig_dir / 'public_h3_res5_density_map.png'}")

    print("\nAll scientific figures successfully generated in:", fig_dir.resolve())


if __name__ == "__main__":
    main()
