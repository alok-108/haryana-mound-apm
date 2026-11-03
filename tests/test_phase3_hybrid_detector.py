"""
Pytest Suite for Phase 3 Multistage Hybrid APM Architecture:
1. MSRM Patch Extractor (border padding, tell synthesis, aspect ratio).
2. Tell Morphology CNN (PyTorch / Analytical forward pass).
3. Hybrid Stacked Detector (Orengo RF + CNN + AlphaEarth + Isotonic Calibration).
"""

import numpy as np
import pytest

from src.detector import (
    HybridPrediction,
    HybridStackedDetector,
    MSRMPatchExtractor,
    TellMorphologyCNN,
)


def test_msrm_patch_extractor():
    extractor = MSRMPatchExtractor(patch_size=32)
    
    # 1. Circular Tell patch
    tell_patch = extractor.synthesize_candidate_patch(estimated_relief_m=4.0, is_linear_embankment=False, is_sand_dune=False)
    assert tell_patch.shape == (32, 32)
    metrics_tell = extractor.compute_morphological_shape_metrics(tell_patch)
    assert metrics_tell["summit_prominence"] > 0.5
    assert metrics_tell["radial_symmetry_score"] >= 0.70

    # 2. Linear Embankment patch
    linear_patch = extractor.synthesize_candidate_patch(estimated_relief_m=3.0, is_linear_embankment=True)
    assert linear_patch.shape == (32, 32)
    metrics_linear = extractor.compute_morphological_shape_metrics(linear_patch)
    assert metrics_linear["aspect_ratio"] > 1.3

    # 3. Extraction from 2D raster with padding
    raster = np.zeros((50, 50), dtype=np.float32)
    raster[25, 25] = 5.0
    cropped = extractor.extract_patch_from_raster(raster, center_row=2, center_col=2)
    assert cropped.shape == (32, 32)


def test_tell_morphology_cnn():
    cnn = TellMorphologyCNN(random_state=42)
    extractor = MSRMPatchExtractor(patch_size=32)

    tell_patch = extractor.synthesize_candidate_patch(estimated_relief_m=5.0)
    flat_patch = np.zeros((32, 32), dtype=np.float32)

    score_tell = cnn.predict_patch_score(tell_patch)
    score_flat = cnn.predict_patch_score(flat_patch)

    assert 0.0 <= score_tell <= 1.0
    assert 0.0 <= score_flat <= 1.0

    # Batch evaluation
    batch = np.stack([tell_patch, flat_patch])
    batch_scores = cnn.predict_batch(batch)
    assert len(batch_scores) == 2


def test_hybrid_stacked_detector_end_to_end():
    rng = np.random.default_rng(42)
    n = 60

    # Simulated S1/S2 + DEM features (13 cols)
    X_s1s2 = rng.normal(0.0, 1.0, size=(n, 13))
    # Simulated AlphaEarth features (64 cols)
    X_alpha = rng.normal(0.0, 1.0, size=(n, 64))
    # Labels (10 positives, 50 background)
    y = np.array([1] * 10 + [0] * 50)
    # Add signal to positives
    X_s1s2[:10] += 1.5
    X_alpha[:10] += 1.2

    # Patches (32x32)
    extractor = MSRMPatchExtractor(patch_size=32)
    patches = np.array([
        extractor.synthesize_candidate_patch(estimated_relief_m=4.0 if i < 10 else 0.0, random_state=42 + i)
        for i in range(n)
    ])

    detector = HybridStackedDetector(cnn_filter_threshold=0.20, random_state=42)
    detector.fit(X_s1s2_dem=X_s1s2, X_alpha=X_alpha, patches_msrm=patches, y=y, n_splits=3)

    assert detector.is_fitted is True

    # Predict on test set
    preds = detector.predict(X_s1s2_dem=X_s1s2[:15], X_alpha=X_alpha[:15], patches_msrm=patches[:15])
    assert len(preds) == 15
    for p in preds:
        assert isinstance(p, HybridPrediction)
        assert 0.0 <= p.calibrated_probability <= 1.0
        assert p.confidence_tier != ""
