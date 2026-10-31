"""
Google Earth Engine (GEE) & Local Relief Feature Extraction Pipeline.
Implements:
1. Orengo et al. (2020, PNAS, doi:10.1073/pnas.2005583117) multi-year Sentinel-1 & Sentinel-2 seasonal/harmonic composites.
2. Orengo & Petrie (2018, ESPL, doi:10.1002/esp.4317) Multi-Scale Relief Model (MSRM) + morphological White/Black Top-Hats on FABDEM/GLO-30.
3. Historical stereo CORONA reconnaissance reference: Casana & Cothren (2008, Antiquity 82(317):732-749, doi:10.1017/S0003598X00097349).
4. Dynamic query of Google AlphaEarth Foundations ('GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL') verifying 0-indexed bands A00..A63 and latest catalog year.
5. Spatial feature aggregation using max and p90/p95 (preventing 1-5 ha mound signal dilution inside ~74 ha H3 Res 8 cells)
   and supporting both H3 Resolution 8 and ~250 m regular spatial patch units.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Sequence, Tuple
import numpy as np
from scipy.ndimage import uniform_filter, grey_opening, grey_closing


ALPHAEARTH_BANDS: List[str] = [f"A{i:02d}" for i in range(64)]  # A00 through A63


def get_alphaearth_band_names() -> List[str]:
    """Return the verified 0-indexed 64 band names (A00..A63) for GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL."""
    assert len(ALPHAEARTH_BANDS) == 64
    assert ALPHAEARTH_BANDS[0] == "A00" and ALPHAEARTH_BANDS[-1] == "A63"
    return list(ALPHAEARTH_BANDS)


def build_gee_s1_s2_orengo2020_composite(
    bbox_wgs84: List[float],
    date_start: str = "2018-01-01",
    date_end: str = "2024-12-31",
) -> "ee.Image":
    """
    Construct the multi-sensor, multi-temporal Sentinel-2 + Sentinel-1 composite
    following Orengo et al. (2020, PNAS, doi:10.1073/pnas.2005583117).
    Requires an authenticated `ee.Initialize(project=...)` session.
    """
    import ee

    roi = ee.Geometry.Rectangle(bbox_wgs84)

    def mask_s2_clouds(image: "ee.Image") -> "ee.Image":
        scl = image.select("SCL")
        # Keep bare soil (5), vegetation (4), water (6); mask cloud/shadow/cirrus (3, 8, 9, 10, 11)
        valid = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11))
        return image.updateMask(valid).divide(10000.0).copyProperties(image, ["system:time_start"])

    def add_spectral_indices(image: "ee.Image") -> "ee.Image":
        ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
        ndwi = image.normalizedDifference(["B3", "B8"]).rename("NDWI")
        bsi = image.expression(
            "((B11 + B4) - (B8 + B2)) / ((B11 + B4) + (B8 + B2) + 1e-6)",
            {
                "B11": image.select("B11"),
                "B4": image.select("B4"),
                "B8": image.select("B8"),
                "B2": image.select("B2"),
            },
        ).rename("BSI")
        ndre = image.normalizedDifference(["B8A", "B5"]).rename("NDRE")
        return image.addBands([ndvi, ndwi, bsi, ndre])

    s2_col = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(roi)
        .filterDate(date_start, date_end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .map(mask_s2_clouds)
        .map(add_spectral_indices)
    )

    # Rabi peak-growth / late-grain stress window (Feb–March) vs. Zaid bare-soil window (April–May)
    s2_rabi = (
        s2_col.filter(ee.Filter.calendarRange(2, 3, "month"))
        .select(["B2", "B3", "B4", "B8", "B11", "B12", "NDVI", "NDWI", "BSI", "NDRE"])
        .percentile([10, 50, 90])
    )
    s2_zaid_bare = (
        s2_col.filter(ee.Filter.calendarRange(4, 5, "month"))
        .select(["B2", "B3", "B4", "B8", "B11", "B12", "BSI", "NDVI"])
        .median()
        .rename([f"{b}_zaid_med" for b in ["B2", "B3", "B4", "B8", "B11", "B12", "BSI", "NDVI"]])
    )

    # Sentinel-1 C-band IW VV and VH seasonal percentiles
    s1_col = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(roi)
        .filterDate(date_start, date_end)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select(["VV", "VH"])
    )
    s1_stats = s1_col.percentile([10, 50, 90])

    return ee.Image.cat([s2_rabi, s2_zaid_bare, s1_stats]).clip(roi)


def fetch_latest_alphaearth_embedding(
    bbox_wgs84: List[float], target_year: Optional[int] = None
) -> Tuple["ee.Image", int]:
    """
    Dynamically query GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL for the latest available year
    without hard-coding 'present'. Returns (ee.Image with bands A00..A63, resolved_year).
    """
    import ee

    roi = ee.Geometry.Rectangle(bbox_wgs84)
    col = ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL").filterBounds(roi)

    if target_year is None:
        latest_img = col.sort("system:time_start", False).first()
        resolved_year = int(ee.Date(latest_img.get("system:time_start")).get("year").getInfo())
    else:
        resolved_year = int(target_year)

    year_col = col.filterDate(f"{resolved_year}-01-01", f"{resolved_year}-12-31")
    mosaic = year_col.mosaic().select(ALPHAEARTH_BANDS).clip(roi)
    return mosaic, resolved_year


def compute_msrm_and_tophats_numpy(
    dem: np.ndarray,
    pixel_size_m: float = 30.0,
    f_min_m: float = 30.0,
    f_max_m: float = 300.0,
    step_m: float = 30.0,
    tophat_radii_m: Tuple[float, ...] = (60.0, 150.0, 300.0),
) -> Dict[str, np.ndarray]:
    """
    Local NumPy implementation of:
    1. Multi-Scale Relief Model (MSRM; Orengo & Petrie 2018, doi:10.1002/esp.4317)
    2. Morphological White Top-Hat (WTH, positive mound/rampart relief) and Black Top-Hat (BTH, moats/depressions).
    """
    if dem.ndim != 2:
        raise ValueError(f"Expected 2D DEM array, got shape {dem.shape}")

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

    outputs: Dict[str, np.ndarray] = {"msrm": msrm.astype(np.float32)}
    for r_m in tophat_radii_m:
        size_px = max(3, 2 * int(round(r_m / pixel_size_m)) + 1)
        opened = grey_opening(dem_f, size=(size_px, size_px))
        closed = grey_closing(dem_f, size=(size_px, size_px))
        outputs[f"wth_{int(r_m)}m"] = (dem_f - opened).astype(np.float32)
        outputs[f"bth_{int(r_m)}m"] = (closed - dem_f).astype(np.float32)

    return outputs


def aggregate_cell_pixels(
    pixels: np.ndarray,
    percentiles: Sequence[float] = (90.0, 95.0),
    include_max: bool = True,
) -> Dict[str, float]:
    """
    Aggregate 10m/30m pixel values within a spatial unit (H3 Res 8 ~74 ha, or 250m patch ~6.25 ha).
    Uses max and high percentiles (p90/p95) instead of simple mean, preventing the subtle 1-5 ha mound
    topographic and spectral signal from being averaged out by the surrounding agricultural background.
    """
    valid = pixels[~np.isnan(pixels)]
    if len(valid) == 0:
        res = {f"p{int(p)}": float("nan") for p in percentiles}
        if include_max:
            res["max"] = float("nan")
        return res

    res = {}
    if include_max:
        res["max"] = float(np.max(valid))
    for p in percentiles:
        res[f"p{int(p)}"] = float(np.percentile(valid, p))
    return res
