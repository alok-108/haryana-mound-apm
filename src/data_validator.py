"""
Strict Data-Schema Validator for the Scoped Haryana Mound APM Pipeline.

Fails loudly when:
1. `data/processed/` directory does not exist or contains no Parquet/CSV files.
2. Required columns are missing.
3. Ground-truth boolean flags (`is_ground_confirmed`, `is_protected_or_excavated`) are missing.
4. Positive samples contain 0 confirmed sites.
5. Coordinates fall outside the plausible bounding box for Haryana (EPSG:32643).
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Tuple
import pandas as pd

from src.gee_export import ALPHAEARTH_BANDS


MANDATORY_METADATA_COLUMNS = [
    "x_m",
    "y_m",
    "y_obs",
    "is_ground_confirmed",
    "is_protected_or_excavated",
    "discovery_modality",
    "relief_class",
]

MANDATORY_FEATURE_COLUMNS = [
    "msrm",
    "wth_150m",
    "bth_150m",
    "NDVI_p50",
    "BSI_zaid_med",
    "VH_p50",
] + ALPHAEARTH_BANDS

# Approximate metric coordinate bounds for Hisar, Fatehabad, Sirsa (EPSG:32643)
HARYANA_UTM43N_BOUNDS = {
    "x_min": 400000.0,
    "x_max": 700000.0,
    "y_min": 3150000.0,
    "y_max": 3350000.0,
}


def validate_processed_dataframe(
    df: pd.DataFrame,
    source_name: str = "dataset",
    check_coordinate_bounds: bool = True,
) -> pd.DataFrame:
    """Validate schema, types, and values of a processed dataset DataFrame."""
    if df.empty:
        raise ValueError(f"Processed dataset '{source_name}' is completely empty (0 rows).")

    all_mandatory = MANDATORY_METADATA_COLUMNS + MANDATORY_FEATURE_COLUMNS
    missing_cols = [c for c in all_mandatory if c not in df.columns]
    if missing_cols:
        raise KeyError(
            f"Processed dataset '{source_name}' is missing {len(missing_cols)} mandatory columns: {missing_cols[:10]}... "
            f"Refer to data/README.md for exact schema requirements."
        )

    # Validate ground-truth label sanity
    if not (df["y_obs"].isin([0, 1])).all():
        raise ValueError(f"Column 'y_obs' in '{source_name}' must be strictly binary integers (0 or 1).")

    n_pos = int((df["y_obs"] == 1).sum())
    n_unl = int((df["y_obs"] == 0).sum())
    if n_pos == 0:
        raise ValueError(f"Dataset '{source_name}' contains ZERO positive samples (y_obs == 1). Cannot run benchmark.")
    if n_unl == 0:
        raise ValueError(f"Dataset '{source_name}' contains ZERO unlabelled samples (y_obs == 0). Cannot run benchmark.")

    n_confirmed = int(((df["y_obs"] == 1) & (df["is_ground_confirmed"] == True)).sum())
    if n_confirmed == 0:
        raise ValueError(
            f"Dataset '{source_name}' contains {n_pos} positive records, but ZERO are marked 'is_ground_confirmed == True'. "
            f"Unverified historical map symbols cannot be used as training positives!"
        )

    if check_coordinate_bounds:
        xs = df["x_m"].to_numpy()
        ys = df["y_m"].to_numpy()
        b = HARYANA_UTM43N_BOUNDS
        out_of_bounds = (xs < b["x_min"]) | (xs > b["x_max"]) | (ys < b["y_min"]) | (ys > b["y_max"])
        pct_oob = float(out_of_bounds.mean() * 100.0)
        if pct_oob > 20.0:
            raise ValueError(
                f"Over {pct_oob:.1f}% of coordinates in '{source_name}' fall outside the expected "
                f"EPSG:32643 bounds for Haryana. Check CRS projection (expected EPSG:32643)."
            )

    return df


def load_and_validate_processed_dataset(
    processed_dir: Path | str = "data/processed",
    preferred_file: str = "haryana_h3_res8_features.parquet",
) -> Tuple[pd.DataFrame, Path]:
    """
    Search `data/processed/` for the feature table, failing loudly if directory is empty
    or file is missing/invalid.
    """
    pdir = Path(processed_dir)
    if not pdir.exists():
        raise FileNotFoundError(
            f"Directory '{pdir}' does not exist. Create '{pdir}' and place the processed feature tables "
            f"as described in data/README.md."
        )

    target_file = pdir / preferred_file
    if not target_file.exists():
        # Look for any .parquet or .csv in data/processed
        candidates = list(pdir.glob("*.parquet")) + list(pdir.glob("*.csv"))
        if not candidates:
            raise FileNotFoundError(
                f"Directory '{pdir}' exists but is completely empty. No Parquet or CSV feature tables found. "
                f"Export Sentinel/DEM features via GEE and join with MAHSA labels before running the benchmark. "
                f"See data/README.md."
            )
        target_file = candidates[0]

    df = pd.read_parquet(target_file) if target_file.suffix == ".parquet" else pd.read_csv(target_file)
    validated_df = validate_processed_dataframe(df, source_name=str(target_file.name))
    return validated_df, target_file
