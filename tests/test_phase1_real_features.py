"""
Tests for Phase 1 Real Feature Extraction & Micro-Topography Engine:
1. Multi-Scale Relief Model (MSRM) calculation on 2D elevation models.
2. Sky-View Factor (SVF) calculation and hemispherical bounding.
3. Morphological White/Black Top-Hats at 60m, 150m, 300m scales.
4. GEE export CLI parameter verification and offline fallback resilience.
"""

from pathlib import Path
import numpy as np
import pytest

from src.dem_visualization import (
    compute_msrm,
    compute_sky_view_factor,
    compute_morphological_tophats,
    extract_microtopography_features,
)
from scripts.export_gee_features import (
    AOI_BOUNDING_BOXES,
    initialize_earth_engine,
    export_pilot_features,
)


@pytest.fixture
def synthetic_mound_dem():
    """Create a 100x100 2D DEM with a 3.0 m high Gaussian mound at the center."""
    dem = np.full((100, 100), 215.0, dtype=np.float32)
    # Add an artificial tell mound at center (50, 50) with 3m peak and radius ~6 pixels (180m)
    y, x = np.ogrid[:100, :100]
    dist_sq = (x - 50)**2 + (y - 50)**2
    mound = 3.0 * np.exp(-dist_sq / (2.0 * (6.0**2)))
    dem += mound.astype(np.float32)
    return dem


def test_msrm_detects_mound_peak(synthetic_mound_dem):
    """Verify that MSRM yields a prominent positive standardized peak at mound center."""
    msrm = compute_msrm(synthetic_mound_dem, pixel_size_m=30.0)
    assert msrm.shape == synthetic_mound_dem.shape
    assert not np.isnan(msrm).any()
    
    # Summit (50, 50) must have significantly higher MSRM than plain corner (5, 5)
    peak_msrm = msrm[50, 50]
    plain_msrm = msrm[5, 5]
    assert peak_msrm > plain_msrm
    assert peak_msrm > 0.5


def test_sky_view_factor_bounds_and_mound(synthetic_mound_dem):
    """Verify Sky-View Factor (SVF) values are bounded in [0, 1] and summit has high visibility."""
    svf = compute_sky_view_factor(synthetic_mound_dem, pixel_size_m=30.0, max_search_radius_px=8)
    assert svf.shape == synthetic_mound_dem.shape
    assert (svf >= 0.0).all() and (svf <= 1.0).all()
    # Summit has open sky view
    assert svf[50, 50] >= 0.90


def test_morphological_tophats(synthetic_mound_dem):
    """Verify White Top-Hat isolates positive mound relief."""
    tophats = compute_morphological_tophats(
        synthetic_mound_dem, pixel_size_m=30.0, radii_m=(60.0, 150.0, 300.0)
    )
    assert "wth_60m" in tophats
    assert "wth_150m" in tophats
    assert "wth_300m" in tophats
    assert "bth_150m" in tophats

    # Mound summit should have positive White Top-Hat
    assert tophats["wth_150m"][50, 50] > 1.0
    # Flat landscape should have near-zero Top-Hat
    assert tophats["wth_150m"][5, 5] < 0.2


def test_extract_microtopography_features_bundle(synthetic_mound_dem):
    """Verify complete microtopography feature extractor bundle."""
    bundle = extract_microtopography_features(synthetic_mound_dem, pixel_size_m=30.0, dem_source="FABDEM")
    assert "msrm" in bundle
    assert "sky_view_factor" in bundle
    assert "wth_150m" in bundle
    assert "bth_150m" in bundle
    assert isinstance(bundle["msrm"], np.ndarray)


def test_gee_export_aoi_and_offline_handling(tmp_path):
    """Verify AOI bounding boxes and offline graceful fallback."""
    assert "haryana" in AOI_BOUNDING_BOXES
    assert "cholistan" in AOI_BOUNDING_BOXES
    
    bbox = AOI_BOUNDING_BOXES["haryana"]
    assert len(bbox) == 4
    # min_lon < max_lon and min_lat < max_lat
    assert bbox[0] < bbox[2]
    assert bbox[1] < bbox[3]

    # Offline mode test when ee credentials are not configured
    res_path = export_pilot_features(project_id="nonexistent-dummy-test-project", aoi_name="haryana", output_dir=tmp_path)
    # When unauthenticated, either returns path to pre-existing file or None with clean warning log
    assert res_path is None or isinstance(res_path, Path)
