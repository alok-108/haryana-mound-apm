"""
Command-Line Archaeological Discovery Tool for Pre-600 BCE Sites.
Scans landscape feature data to predict unrecorded archaeological settlement mounds
with calibrated posterior probabilities (including Tier 1: 95%-100% confidence).

Targets:
- Indus Valley & Harappan Civilization (Early, Mature, Late Harappan, Hakra Ware)
- Saraswati-Ghaggar & Drishadvati (Chautang) Basin settlements
- Painted Grey Ware (PGW) & Vedic Riverine settlements
- Ochre Coloured Pottery (OCP) / Copper Hoard horizon in the Yamuna-Ganga doab

Usage:
    python -m scripts.discover_sites --features data/processed/haryana_patch250m_features.csv --top-k 30
"""

from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd

from src.discovery_engine import Pre600BCEDiscoveryEngine


def generate_dossier_markdown(candidates_df: pd.DataFrame, output_path: Path) -> None:
    """Generate comprehensive, field-actionable Archaeological Discovery Dossier."""
    n_tier1 = int((candidates_df["calibrated_probability"] >= 0.95).sum())
    n_tier2 = int(((candidates_df["calibrated_probability"] >= 0.85) & (candidates_df["calibrated_probability"] < 0.95)).sum())
    n_tier3 = int((candidates_df["calibrated_probability"] < 0.85).sum())

    lines = [
        "# Pre-600 BCE Archaeological Discovery Dossier: Prospective Unrecorded Sites",
        "",
        "**Target Cultures:** Indus Valley (Early/Mature/Late Harappan), Saraswati/Ghaggar Basin, Painted Grey Ware (PGW) / Vedic, and Ganga-Yamuna OCP Horizons  ",
        f"**Total Discovery Candidates:** {len(candidates_df)}  ",
        f"**Tier 1 Ultra-High Confidence (95%–100%):** `{n_tier1}` candidates  ",
        f"**Tier 2 High Priority (85%–95%):** `{n_tier2}` candidates  ",
        f"**Tier 3 Ploughed/Low-Relief (70%–85%):** `{n_tier3}` candidates  ",
        "",
        "---",
        "",
        "## Top Discovery Candidates Matrix",
        "",
        "| ID | WGS84 Coords (Lat, Lon) | District | Calibrated Prob | Confidence Tier | Est Height | Predicted Culture | Paleo Dist | Gates Passed |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for _, row in candidates_df.iterrows():
        lat_lon = f"`{row['latitude']:.4f}, {row['longitude']:.4f}`"
        lines.append(
            f"| {row['candidate_id']} | {lat_lon} | {row['district']} | "
            f"**{row['calibrated_probability']*100:.1f}%** | {row['confidence_tier'].split(':')[0]} | "
            f"{row['estimated_height_m']:.1f} m | {row['predicted_culture']} | "
            f"{row['dist_paleochannel_km']:.1f} km | {row['evidence_gate_count']}/7 |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Detailed Candidate Archaeological Profiles",
        "",
    ])

    for _, row in candidates_df.head(10).iterrows():
        lines.extend([
            f"### Candidate: `{row['candidate_id']}` ({row['confidence_tier']})",
            f"- **GPS Waypoint:** Latitude `{row['latitude']:.5f}° N`, Longitude `{row['longitude']:.5f}° E` (UTM 43N: `{row['x_m']:.1f}m E, {row['y_m']:.1f}m N`)",
            f"- **Administrative Location:** District {row['district']}",
            f"- **Calibrated Posterior Probability:** `{row['calibrated_probability']*100:.2f}%`",
            f"- **Estimated Mound Relief:** `{row['estimated_height_m']:.1f} meters` (MSRM index: `{row['msrm_relief_score']:.2f}`, White Top-Hat: `{row['wth_tophat_m']:.2f}m`)",
            f"- **Predicted Cultural Horizon:** **{row['predicted_culture'].upper()}** (Model Confidence: `{row['culture_confidence']*100:.1f}%`)",
            f"- **Cultural Rationale:** {row['cultural_rationale']}",
            f"- **Paleohydrology:** `{row['dist_paleochannel_km']:.2f} km` from primary relict paleochannel levee (Prior: `{row['fluvial_prior_score']:.3f}`)",
            f"- **Remote Sensing Spectral Signature:** Summer Zaid Bare Soil Index: `{row['bsi_summer_score']:.3f}` | Sentinel-1 SAR VH: `{row['sar_vh_db']:.1f} dB` | AlphaEarth Foundation Cosine Sim: `{row['alphaearth_similarity']:.3f}`",
            f"- **Historical Toposheet Corroboration:** `{row['on_historical_soi_map']}`",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## Statutory & Ethical Field Verification Protocol",
        "> [!IMPORTANT]",
        "> Under the **Ancient Monuments and Archaeological Sites and Remains (AMASR) Act 1958**, non-invasive pedestrian reconnaissance, visual inspection, and photography on public ground do not require an excavation license, but **systematic artifact collection or excavation strictly requires prior permission from the Archaeological Survey of India (ASI) or State Directorate of Archaeology** and a recognized institutional partner.",
        "",
        "### Pre-Field Verification Checklist:",
        "1. **High-Resolution Satellite Visual Confirmation:** Inspect candidates in Google Earth / ESRI World Imagery for visible circular soil-color anomalies (*theh* soil), ceramic scatters, or crop-mark discoloration.",
        "2. **Archival Map Corroboration:** Check colonial Survey of India 1-inch toposheet series (1905–1935) to confirm absence of modern railway spoil or post-1950 canal infrastructure.",
        "3. **GPS Field Ground-Truthing:** Navigate to waypoint centroids, inspect ploughed margins for diagnostic pre-600 BCE ceramic sherds (Hakra Ware, Sothi-Siswal bichrome, Mature Harappan black-on-red, PGW grey ware).",
        "",
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict and Discover Undiscovered Pre-600 BCE Archaeological Sites")
    parser.add_argument(
        "--features",
        type=str,
        default="data/processed/haryana_patch250m_features.csv",
        help="Path to processed regional feature table (CSV or Parquet)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/candidates",
        help="Directory to save discovery candidate outputs",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=25,
        help="Maximum number of top prospective candidates to output",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.70,
        help="Minimum calibrated posterior probability threshold (0.70 to 0.95)",
    )
    args = parser.parse_args()

    feat_path = Path(args.features)
    if not feat_path.exists():
        raise FileNotFoundError(f"Features file not found at: {feat_path}")

    print(f"Loading landscape feature data from: {feat_path}")
    df = pd.read_parquet(feat_path) if feat_path.suffix == ".parquet" else pd.read_csv(feat_path)
    print(f"Loaded {len(df)} regional spatial cells.")

    engine = Pre600BCEDiscoveryEngine(tier3_threshold=args.min_confidence)
    candidates, cand_df = engine.scan_for_undiscovered_sites(df, top_k=args.top_k)

    if cand_df.empty:
        print("No candidates met the confidence threshold. Try lowering --min-confidence.")
        return

    out_dir = Path(args.output_dir)
    csv_out, geojson_out = engine.export_candidates(cand_df, output_dir=out_dir)
    dossier_out = out_dir / "DISCOVERY_DOSSIER.md"
    generate_dossier_markdown(cand_df, dossier_out)

    print("\n========================================================")
    print(f"PRE-600 BCE DISCOVERY PROSPECTION COMPLETE!")
    print(f"Discovered {len(cand_df)} prospective unrecorded mound candidates.")
    print(f"Tier 1 (95%-100% Ultra-High): {(cand_df['calibrated_probability'] >= 0.95).sum()}")
    print(f"Tier 2 (85%-95% High): {((cand_df['calibrated_probability'] >= 0.85) & (cand_df['calibrated_probability'] < 0.95)).sum()}")
    print(f"Tier 3 (70%-85% Ploughed): {(cand_df['calibrated_probability'] < 0.85).sum()}")
    print(f"Outputs written to:")
    print(f"  - CSV:     {csv_out.resolve()}")
    print(f"  - GeoJSON: {geojson_out.resolve()}")
    print(f"  - Dossier: {dossier_out.resolve()}")
    print("========================================================\n")


if __name__ == "__main__":
    main()
