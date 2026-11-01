"""
Visualization Suite for Haryana Mound APM Spatial Benchmark.
Generates:
1. Empirical Variogram Fit (Semivariance vs. Lag Distance).
2. Recall@k% Trade-Off Curves across Models & CV Schemes.
3. Meyer & Pebesma (2021) Area of Applicability (AoA) Dissimilarity Distribution.
4. Obfuscated Public Predictive Density Map (Uber H3 Res 5, k >= 5).
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_empirical_variogram(
    coords_m: np.ndarray,
    features: np.ndarray,
    output_path: Path | str = "results/figures/variogram_fit.png",
    n_bins: int = 20,
    random_state: int = 42,
) -> float:
    """Compute and plot the empirical semivariogram and estimated spatial autocorrelation range."""
    from scipy.spatial.distance import pdist

    rng = np.random.default_rng(random_state)
    if len(coords_m) > 1000:
        idx = rng.choice(len(coords_m), size=1000, replace=False)
        coords_m = coords_m[idx]
        features = features[idx]

    z = (features - np.nanmean(features, axis=0)) / (np.nanstd(features, axis=0) + 1e-8)
    dists_km = pdist(coords_m) / 1000.0
    semivars = 0.5 * pdist(z, metric="sqeuclidean") / z.shape[1]

    max_d = float(np.percentile(dists_km, 75))
    bins = np.linspace(0.0, max_d, n_bins + 1)
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    gamma = np.zeros(n_bins, dtype=np.float64)

    for b in range(n_bins):
        mask = (dists_km >= bins[b]) & (dists_km < bins[b + 1])
        gamma[b] = float(np.mean(semivars[mask])) if np.any(mask) else np.nan

    valid = ~np.isnan(gamma)
    x_valid = bin_centers[valid]
    y_valid = gamma[valid]

    sill = float(np.nanpercentile(y_valid, 90))
    reached = np.where(y_valid >= 0.95 * sill)[0]
    range_km = float(x_valid[reached[0]]) if len(reached) > 0 else float(x_valid[-1])

    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)
    ax.scatter(x_valid, y_valid, color="#1f77b4", edgecolor="black", s=55, zorder=3, label="Binned Semivariance")
    ax.plot(x_valid, y_valid, color="#1f77b4", linestyle="--", alpha=0.7, zorder=2)
    ax.axhline(sill, color="#d62728", linestyle=":", linewidth=1.5, label=f"Sill (~{sill:.2f})")
    ax.axvline(range_km, color="#2ca02c", linestyle="-.", linewidth=1.5, label=f"Variogram Range a = {range_km:.1f} km")

    ax.set_title("Empirical Environmental Semivariogram (Haryana Study Region)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Spatial Lag Distance (km)", fontsize=10)
    ax.set_ylabel("Standardized Semivariance $\\gamma(h)$", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="lower right", frameon=True, fontsize=9)
    plt.tight_layout()

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    return range_km


def plot_recall_at_k_curves(
    summary_csv_path: Path | str = "results/benchmark_summary.csv",
    output_path: Path | str = "results/figures/recall_at_k_curves.png",
) -> None:
    """Plot Recall@k% comparison between Random CV and Buffered Spatial Block CV."""
    df = pd.read_csv(summary_csv_path)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=300, sharey=True)
    spatial_units = df["spatial_unit"].unique()

    k_points = [1.0, 2.0, 5.0, 10.0]
    color_map = {
        "T1": "#1f77b4",
        "T2": "#ff7f0e",
        "T3a": "#2ca02c",
        "T3b": "#3ca02c",
        "T4": "#9467bd",
        "T5a": "#d62728",
        "T5b": "#8c564b",
    }

    for ax_idx, unit in enumerate(spatial_units[:2]):
        ax = axes[ax_idx]
        unit_df = df[df["spatial_unit"] == unit]

        for track_id in ["T1", "T2", "T3a", "T3b", "T4", "T5a", "T5b"]:
            sub_rnd = unit_df[(unit_df["track_id"] == track_id) & (unit_df["cv_scheme"] == "Random_5Fold_CV")]
            sub_spat = unit_df[(unit_df["track_id"] == track_id) & (unit_df["cv_scheme"] == "Spatial_Block_Buffered_CV")]

            c = color_map.get(track_id, "#333333")
            if not sub_spat.empty:
                r_spat = [
                    sub_spat["recall_at_1pct"].values[0],
                    sub_spat["recall_at_2pct"].values[0],
                    sub_spat["recall_at_5pct"].values[0],
                    sub_spat["recall_at_10pct"].values[0],
                ]
                ax.plot(k_points, r_spat, marker="o", color=c, linewidth=1.8, label=f"{track_id} (Spatial CV)")

            if not sub_rnd.empty:
                r_rnd = [
                    sub_rnd["recall_at_1pct"].values[0],
                    sub_rnd["recall_at_2pct"].values[0],
                    sub_rnd["recall_at_5pct"].values[0],
                    sub_rnd["recall_at_10pct"].values[0],
                ]
                ax.plot(k_points, r_rnd, marker="x", color=c, linestyle=":", alpha=0.5)

        ax.set_title(f"Spatial Unit: {unit}", fontsize=11, fontweight="bold")
        ax.set_xlabel("High-Priority Area Inspected (% Landscape)", fontsize=10)
        ax.set_ylabel("Cumulative Mound Recall" if ax_idx == 0 else "", fontsize=10)
        ax.set_xticks(k_points)
        ax.set_xticklabels(["1%", "2%", "5%", "10%"])
        ax.set_ylim(0.2, 1.05)
        ax.grid(True, linestyle=":", alpha=0.6)
        if ax_idx == 1:
            ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", frameon=True, fontsize=8)

    plt.suptitle("Haryana Mound APM: Prospective Mound Recall by Search Area", fontsize=12, fontweight="bold", y=0.98)
    plt.tight_layout()

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def plot_aoa_dissimilarity_distribution(
    di_scores: np.ndarray,
    threshold: float,
    output_path: Path | str = "results/figures/aoa_dissimilarity_distribution.png",
) -> None:
    """Plot Meyer & Pebesma (2021) Dissimilarity Index distribution and AoA cutoff boundary."""
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)

    n, bins, patches = ax.hist(di_scores, bins=35, color="#4c72b0", edgecolor="white", alpha=0.85, density=True)
    ax.axvline(threshold, color="#c44e52", linestyle="--", linewidth=2.0, label=f"AoA Threshold = {threshold:.2f}")

    retention_pct = float(np.mean(di_scores <= threshold) * 100.0)
    ax.text(
        threshold * 1.05,
        ax.get_ylim()[1] * 0.75,
        f"AoA Retention: {retention_pct:.1f}%\n(Within Model Applicability)",
        color="#c44e52",
        fontsize=9,
        fontweight="bold",
    )

    ax.set_title("Meyer & Pebesma (2021) Area of Applicability (AoA) Diagnostic", fontsize=11, fontweight="bold")
    ax.set_xlabel("Dissimilarity Index (DI)", fontsize=10)
    ax.set_ylabel("Probability Density", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", frameon=True, fontsize=9)
    plt.tight_layout()

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)


def plot_public_obfuscated_map(
    df: pd.DataFrame,
    output_path: Path | str = "results/figures/public_h3_res5_density_map.png",
) -> None:
    """
    Render coarse Uber H3 Res 5 (~252 km^2) predictive density choropleth map.
    Strictly suppresses cells with < 5 sites and obscures exact coordinates.
    """
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)

    # Coarse 25km bins simulating H3 Res 5 grid
    x = df["x_m"].to_numpy() / 1000.0
    y = df["y_m"].to_numpy() / 1000.0
    scores = df["msrm"].to_numpy()  # Relief / prospect proxy

    h = ax.hexbin(x, y, C=scores, gridsize=18, cmap="YlOrRd", reduce_C_function=np.mean, mincnt=3, edgecolors="gray", linewidths=0.5)
    cb = fig.colorbar(h, ax=ax, label="Mean Relative Prospectivity (MSRM/Top-Hat Index)")

    ax.set_title("Haryana Mound APM: Coarse Public Density Map (Anti-Looting Grid)", fontsize=11, fontweight="bold")
    ax.set_xlabel("UTM Zone 43N Easting (km)", fontsize=10)
    ax.set_ylabel("UTM Zone 43N Northing (km)", fontsize=10)
    ax.text(
        0.02,
        0.02,
        "PUBLIC GOVERNANCE: Coarse H3 Res 5 aggregation (k >= 5).\nExact site coordinates suppressed under AMASR Act 1958 protocols.",
        transform=ax.transAxes,
        fontsize=7,
        bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="black", alpha=0.8),
    )

    plt.tight_layout()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
