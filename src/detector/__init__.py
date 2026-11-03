"""
Multistage Hybrid APM Detector:
Stage A: Orengo et al. (2020) Random Forest baseline
Stage B: 2D MSRM-Patch CNN Morphology filter (Berganzo-Besga et al. 2021)
Stage C: Google AlphaEarth Foundation Latent kNN
Stage D: Logistic Stacking & Out-of-Fold Isotonic Probability Calibration
"""

from src.detector.msrm_patch_extractor import MSRMPatchExtractor
from src.detector.cnn_morphology_filter import TellMorphologyCNN
from src.detector.hybrid_stacker import HybridPrediction, HybridStackedDetector

__all__ = [
    "MSRMPatchExtractor",
    "TellMorphologyCNN",
    "HybridPrediction",
    "HybridStackedDetector",
]
