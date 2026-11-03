"""
Command-Line Script to Harvest Real Multi-Sensor Features via Google Earth Engine (GEE).
Phase 1 Ingestion Pipeline:
1. Sentinel-2 L2A Multitemporal Composites: Rabi peak percentiles (10, 50, 90) & Zaid bare-soil median BSI.
2. Sentinel-1 C-band SAR GRD: IW VV/VH seasonal percentiles (10, 50, 90).
3. Copernicus GLO-30 / FABDEM: 30m Digital Elevation Model for MSRM & Top-Hats.
4. Google AlphaEarth Foundation: 64-D Latent Embeddings (A00..A63).

Usage:
    python scripts/export_gee_features.py --project your-gcp-project-id --aoi haryana
    python scripts/export_gee_features.py --help
"""

from __future__ import annotations
import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.gee_export import (
    ALPHAEARTH_BANDS,
    build_gee_s1_s2_orengo2020_composite,
    fetch_latest_alphaearth_embedding,
)
from src.dem_visualization import extract_microtopography_features
from src.public_data_curator import build_canonical_sites_dataframe

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("gee_export")

# Pilot Bounding Boxes (min_lon, min_lat, max_lon, max_lat)
AOI_BOUNDING_BOXES: Dict[str, List[float]] = {
    "haryana": [74.4, 29.0, 76.4, 30.0],
    "hisar_fatehabad_sirsa": [74.6, 29.1, 76.2, 29.8],
    "cholistan": [70.5, 27.5, 73.5, 29.5],
}


def initialize_earth_engine(project_id: Optional[str] = None) -> bool:
    """
    Attempt to initialize Google Earth Engine.
    Returns True if successful, False with helpful instructions if unauthenticated.
    """
    try:
        import ee
    except ImportError:
        logger.error("earthengine-api is not installed. Install with `pip install earthengine-api`")
        return False

    try:
        if project_id:
            ee.Initialize(project=project_id)
        else:
            ee.Initialize()
        logger.info(f"Successfully authenticated with Google Earth Engine (Project: {project_id or 'default'}).")
        return True
    except Exception as e:
        logger.warning(
            f"\n{'='*75}\n"
            f"[GEE AUTHENTICATION NOTICE]\n"
            f"Google Earth Engine session could not be initialized: {e}\n\n"
            f"To enable live multi-spectral extraction:\n"
            f"  1. Register for Google Earth Engine at: https://earthengine.google.com/signup/\n"
            f"  2. In your terminal, authenticate via:\n"
            f"       earthengine authenticate\n"
            f"     or\n"
            f"       gcloud auth application-default login\n"
            f"  3. Re-run this script specifying your GCP project:\n"
            f"       python scripts/export_gee_features.py --project <YOUR_GCP_PROJECT_ID>\n"
            f"{'='*75}\n"
        )
        return False


def sample_gee_at_coordinates(
    composite_image: "ee.Image",
    coords_df: pd.DataFrame,
    band_names: List[str],
    scale_m: float = 30.0,
) -> pd.DataFrame:
    """
    Sample Earth Engine composite raster at specific point coordinates.
    """
    import ee

    features = []
    for idx, row in coords_df.iterrows():
        pt = ee.Geometry.Point([float(row["longitude"]), float(row["latitude"])])
        feat = ee.Feature(pt, {"site_id": str(row["site_id"]), "point_idx": int(idx)})
        features.append(feat)

    fc = ee.FeatureCollection(features)
    sampled = composite_image.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.first(),
        scale=scale_m,
    )

    # Convert to Python list of dicts
    sampled_info = sampled.getInfo()["features"]
    records = []
    for f in sampled_info:
        rec = f["properties"]
        records.append(rec)

    return pd.DataFrame(records)


def export_pilot_features(
    project_id: Optional[str] = None,
    aoi_name: str = "haryana",
    output_dir: Optional[Path] = None,
    date_start: str = "2018-01-01",
    date_end: str = "2024-12-31",
) -> Optional[Path]:
    """
    Extract real multitemporal features for the designated AOI and canonical sites.
    """
    out_dir = output_dir or (REPO_ROOT / "data" / "processed")
    out_dir.mkdir(parents=True, exist_ok=True)

    bbox = AOI_BOUNDING_BOXES.get(aoi_name.lower())
    if not bbox:
        raise ValueError(f"Unknown AOI '{aoi_name}'. Choose from: {list(AOI_BOUNDING_BOXES.keys())}")

    is_online = initialize_earth_engine(project_id)
    if not is_online:
        logger.info(
            f"Operating in offline reference mode. Checking existing canonical datasets in {out_dir}..."
        )
        canonical_csv = out_dir / "haryana_h3_res8_features.csv"
        if canonical_csv.exists():
            logger.info(f"Verified pre-processed canonical feature dataset exists: {canonical_csv}")
            return canonical_csv
        else:
            logger.warning("No pre-existing processed dataset found. Run feature generator to build offline base.")
            return None

    import ee

    logger.info(f"Building Orengo et al. (2020) multitemporal S1/S2 composite for {aoi_name} ({bbox})...")
    s1_s2_img = build_gee_s1_s2_orengo2020_composite(bbox, date_start=date_start, date_end=date_end)

    logger.info("Querying Google AlphaEarth satellite embedding catalog...")
    alpha_img, resolved_year = fetch_latest_alphaearth_embedding(bbox)
    logger.info(f"AlphaEarth resolved to catalog year {resolved_year}.")

    # Load Copernicus DEM GLO-30
    roi = ee.Geometry.Rectangle(bbox)
    dem_img = ee.ImageCollection("COPERNICUS/DEM/GLO30").select("DEM").mosaic().clip(roi)

    # Combined master raster
    master_img = ee.Image.cat([s1_s2_img, alpha_img, dem_img])

    # Sample canonical ground truth sites
    sites_df = build_canonical_sites_dataframe(include_unverified=True)
    logger.info(f"Sampling real Earth Engine pixels across {len(sites_df)} canonical Pre-600 BCE reference sites...")
    sampled_df = sample_gee_at_coordinates(master_img, sites_df, band_names=master_img.bandNames().getInfo())

    # Merge coordinates & metadata
    merged_df = sites_df.merge(sampled_df, on="site_id", how="left")

    out_file = out_dir / f"{aoi_name}_real_gee_features.csv"
    merged_df.to_csv(out_file, index=False)
    logger.info(f"Successfully exported {len(merged_df)} feature records to: {out_file}")

    return out_file


def main():
    parser = argparse.ArgumentParser(description="Harvest Real Satellite Features via Google Earth Engine")
    parser.add_argument("--project", type=str, default=None, help="GCP Project ID for Earth Engine authentication")
    parser.add_argument("--aoi", type=str, default="haryana", choices=list(AOI_BOUNDING_BOXES.keys()), help="Target AOI")
    parser.add_argument("--date-start", type=str, default="2018-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--date-end", type=str, default="2024-12-31", help="End date (YYYY-MM-DD)")
    parser.add_argument("--out-dir", type=str, default="data/processed", help="Output directory")

    args = parser.parse_args()
    export_pilot_features(
        project_id=args.project,
        aoi_name=args.aoi,
        output_dir=Path(args.out_dir),
        date_start=args.date_start,
        date_end=args.date_end,
    )


if __name__ == "__main__":
    main()
