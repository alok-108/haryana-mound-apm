"""
Micro-Topography & Relief Visualization Toolbox Integration.
Implements:
1. Multi-Scale Relief Model (MSRM; Kokalj & Somrak 2019 / Orengo & Petrie 2018, ESPL, doi:10.1002/esp.4317).
2. Sky-View Factor (SVF; Zaksek et al. 2011, doi:10.3390/rs3030398).
3. Morphological White Top-Hat (WTH, positive tell relief) & Black Top-Hat (BTH, moats/depressions).
4. Adaptive fallback: Uses `rvt-py` (Relief Visualization Toolbox) if available;
   otherwise executes pure vectorized NumPy/SciPy reference implementation without requiring GDAL C binaries.
5. Supports FABDEM 30m, Copernicus GLO-30 30m, CartoDEM, and TanDEM-X.
"""

from __future__ import annotations
import logging
from typing import Dict, List, Optional, Sequence, Tuple
import numpy as np
from scipy.ndimage import uniform_filter, grey_opening, grey_closing

logger = logging.getLogger(__name__)

# Check for rvt-py installation
try:
    import rvt.vis as rvt_vis  # type: ignore
    HAS_RVT = True
    logger.info("Found rvt-py (Relief Visualization Toolbox). Using native C/raster acceleration.")
except ImportError:
    HAS_RVT = False
    logger.info("rvt-py not installed (or GDAL unavailable). Using pure NumPy/SciPy reference implementations.")


def compute_msrm(
    dem: np.ndarray,
    pixel_size_m: float = 30.0,
    f_min_m: float = 30.0,
    f_max_m: float = 300.0,
    step_m: float = 30.0,
) -> np.ndarray:
    """
    Compute Multi-Scale Relief Model (MSRM) from a 2D Digital Elevation Model.
    Emphasizes subtle 0.5m-3m archaeological mounds across alluvial plains.

    If `rvt-py` is installed, delegates to `rvt.vis.msrm`.
    Otherwise computes via multi-scale standardized low-pass subtraction.
    """
    if dem.ndim != 2:
        raise ValueError(f"Expected 2D DEM array, got shape {dem.shape}")

    if HAS_RVT:
        try:
            # rvt.vis.msrm accepts dem array and spatial parameters
            res = rvt_vis.msrm(
                dem=dem.astype(np.float32),
                feature_min=int(round(f_min_m / pixel_size_m)),
                feature_max=int(round(f_max_m / pixel_size_m)),
                scaling_factor=int(round(step_m / pixel_size_m)),
            )
            return res.astype(np.float32)
        except Exception as e:
            logger.warning(f"rvt.vis.msrm raised {e}; falling back to reference NumPy MSRM.")

    # Pure NumPy / SciPy reference formulation (Orengo & Petrie 2018)
    dem_f = np.nan_to_num(dem.astype(np.float64), nan=np.nanmedian(dem))
    radii_px = [
        max(1, int(round((r - pixel_size_m) / (2.0 * pixel_size_m))))
        for r in np.arange(f_min_m, f_max_m + step_m, step_m)
    ]
    unique_radii = list(dict.fromkeys(radii_px))

    lowpass_surfaces = [uniform_filter(dem_f, size=2 * r + 1, mode="nearest") for r in unique_radii]
    if len(lowpass_surfaces) < 2:
        msrm = dem_f - lowpass_surfaces[0]
    else:
        acc = np.zeros_like(dem_f)
        count = 0
        for i in range(len(lowpass_surfaces) - 1):
            diff = lowpass_surfaces[i] - lowpass_surfaces[i + 1]
            std = float(np.std(diff))
            if std > 1e-8:
                acc += (diff - float(np.mean(diff))) / std
                count += 1
        msrm = acc / max(1, count)

    return msrm.astype(np.float32)


def compute_sky_view_factor(
    dem: np.ndarray,
    pixel_size_m: float = 30.0,
    max_search_radius_px: int = 10,
    num_directions: int = 8,
) -> np.ndarray:
    """
    Compute Sky-View Factor (SVF) for micro-relief perception.
    Mound summits have SVF near 1.0 (unobstructed hemisphere); depressions/ditches have low SVF.
    """
    if dem.ndim != 2:
        raise ValueError(f"Expected 2D DEM array, got shape {dem.shape}")

    if HAS_RVT:
        try:
            res = rvt_vis.sky_view_factor(
                dem=dem.astype(np.float32),
                resolution=pixel_size_m,
                compute_svf=True,
                compute_asvf=False,
                compute_opns=False,
                min_bounding_radius=1,
                max_bounding_radius=max_search_radius_px,
                num_directions=num_directions,
            )
            if isinstance(res, dict) and "svf" in res:
                return res["svf"].astype(np.float32)
            elif isinstance(res, np.ndarray):
                return res.astype(np.float32)
        except Exception as e:
            logger.warning(f"rvt.vis.sky_view_factor raised {e}; falling back to NumPy SVF approximation.")

    # Vectorized horizon angle approximation for SVF
    dem_f = np.nan_to_num(dem.astype(np.float64), nan=np.nanmedian(dem))
    h, w = dem_f.shape
    angles = np.linspace(0, 2 * np.pi, num_directions, endpoint=False)
    horizon_cos_sum = np.zeros_like(dem_f)

    for ang in angles:
        dx = np.cos(ang)
        dy = np.sin(ang)
        max_tan = np.zeros_like(dem_f)
        for r in range(1, max_search_radius_px + 1):
            shift_x = int(round(r * dx))
            shift_y = int(round(r * dy))
            # Shifted DEM with border padding
            shifted = np.roll(np.roll(dem_f, -shift_y, axis=0), -shift_x, axis=1)
            dist_m = r * pixel_size_m
            slope = (shifted - dem_f) / dist_m
            max_tan = np.maximum(max_tan, slope)
        horizon_cos_sum += np.sin(np.arctan(max_tan))

    svf = 1.0 - (horizon_cos_sum / num_directions)
    return np.clip(svf, 0.0, 1.0).astype(np.float32)


def compute_morphological_tophats(
    dem: np.ndarray,
    pixel_size_m: float = 30.0,
    radii_m: Tuple[float, ...] = (60.0, 150.0, 300.0),
) -> Dict[str, np.ndarray]:
    """
    Compute morphological White Top-Hat (WTH: mound summits) and
    Black Top-Hat (BTH: peripheral depressions/drains).
    """
    if dem.ndim != 2:
        raise ValueError(f"Expected 2D DEM array, got shape {dem.shape}")

    dem_f = np.nan_to_num(dem.astype(np.float64), nan=np.nanmedian(dem))
    res: Dict[str, np.ndarray] = {}

    for r_m in radii_m:
        size_px = max(3, 2 * int(round(r_m / pixel_size_m)) + 1)
        opened = grey_opening(dem_f, size=(size_px, size_px))
        closed = grey_closing(dem_f, size=(size_px, size_px))
        res[f"wth_{int(r_m)}m"] = (dem_f - opened).astype(np.float32)
        res[f"bth_{int(r_m)}m"] = (closed - dem_f).astype(np.float32)

    return res


def extract_microtopography_features(
    dem: np.ndarray,
    pixel_size_m: float = 30.0,
    dem_source: str = "FABDEM",
    tophat_radii_m: Tuple[float, ...] = (60.0, 150.0, 300.0),
) -> Dict[str, np.ndarray]:
    """
    Extract a unified bundle of micro-topographic indices for archaeological tell prospection.
    Integrates MSRM, Sky-View Factor (SVF), and multi-radius White/Black Top-Hats.
    """
    msrm_layer = compute_msrm(dem, pixel_size_m=pixel_size_m)
    svf_layer = compute_sky_view_factor(dem, pixel_size_m=pixel_size_m)
    tophats = compute_morphological_tophats(dem, pixel_size_m=pixel_size_m, radii_m=tophat_radii_m)

    out = {
        "msrm": msrm_layer,
        "sky_view_factor": svf_layer,
        **tophats,
    }
    return out
