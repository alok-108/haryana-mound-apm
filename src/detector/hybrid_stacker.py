"""
Stage D: Multi-Stage Hybrid Stacking & Isotonic Probability Calibration.
Combines:
- Stage A: Orengo et al. (2020) Random Forest baseline probability (P_RF)
- Stage B: 2D MSRM-Patch CNN Morphology filter (P_CNN)
- Stage C: Google AlphaEarth Foundation embedding match (P_Alpha)
- Stage D: Logistic stacking meta-learner + out-of-fold Isotonic Regression calibration.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold

from src.detector.cnn_morphology_filter import TellMorphologyCNN
from src.detector.msrm_patch_extractor import MSRMPatchExtractor
from src.models import AlphaEarthEmbeddingKNN, build_rf_orengo2020_baseline


@dataclass
class HybridPrediction:
    site_id: str
    stage_a_rf_score: float
    stage_b_cnn_score: float
    stage_c_alpha_score: float
    stacked_raw_logit: float
    calibrated_probability: float
    is_false_positive_pruned: bool
    confidence_tier: str


class HybridStackedDetector:
    """
    Multistage Hybrid Detector for Pre-600 BCE Tells.
    Integrates pixel spectral percentiles, 2D convolutional shape verification,
    latent foundation embeddings, and isotonic probability calibration.
    """

    def __init__(
        self,
        cnn_filter_threshold: float = 0.18,
        random_state: int = 42,
    ) -> None:
        self.cnn_filter_threshold = cnn_filter_threshold
        self.random_state = random_state

        # Models
        self.rf_stage_a = build_rf_orengo2020_baseline(random_state=random_state)
        self.cnn_stage_b = TellMorphologyCNN(random_state=random_state)
        self.knn_stage_c = AlphaEarthEmbeddingKNN(k_positives=5)
        self.meta_learner = LogisticRegression(C=1.0, max_iter=200, random_state=random_state)
        self.calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.01, y_max=0.99)
        self.is_fitted = False

    def fit(
        self,
        X_s1s2_dem: np.ndarray,
        X_alpha: np.ndarray,
        patches_msrm: np.ndarray,
        y: np.ndarray,
        n_splits: int = 5,
    ) -> "HybridStackedDetector":
        """
        Fit all stages with out-of-fold stacking and isotonic calibration.
        """
        y_int = y.astype(int)
        n_samples = len(y_int)

        # 1. Fit Stage A and Stage C on full data for inference
        self.rf_stage_a.fit(X_s1s2_dem, y_int)
        self.knn_stage_c.fit(X_alpha[y_int == 1])

        # 2. Out-of-fold cross-validation to generate unbiased meta-features for Stage D
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=self.random_state)
        oof_stage_a = np.zeros(n_samples)
        oof_stage_b = np.zeros(n_samples)
        oof_stage_c = np.zeros(n_samples)

        # Stage B CNN features (pre-computed over patches)
        p_cnn_all = self.cnn_stage_b.predict_batch(patches_msrm)

        for train_idx, val_idx in kf.split(X_s1s2_dem, y_int):
            # Fit RF fold
            rf_fold = build_rf_orengo2020_baseline(random_state=self.random_state)
            rf_fold.fit(X_s1s2_dem[train_idx], y_int[train_idx])
            oof_stage_a[val_idx] = rf_fold.predict_proba(X_s1s2_dem[val_idx])[:, 1]

            # CNN fold predictions
            oof_stage_b[val_idx] = p_cnn_all[val_idx]

            # AlphaEarth kNN fold
            pos_train = X_alpha[train_idx][y_int[train_idx] == 1]
            if len(pos_train) > 0:
                knn_fold = AlphaEarthEmbeddingKNN(k_positives=min(5, len(pos_train)))
                knn_fold.fit(pos_train)
                oof_stage_c[val_idx] = knn_fold.score(X_alpha[val_idx])
            else:
                oof_stage_c[val_idx] = 0.5

        # 3. Fit Meta-Learner on out-of-fold features
        meta_features = np.column_stack([oof_stage_a, oof_stage_b, oof_stage_c])
        self.meta_learner.fit(meta_features, y_int)
        raw_meta_preds = self.meta_learner.predict_proba(meta_features)[:, 1]

        # 4. Fit Isotonic Calibrator on out-of-fold meta predictions
        self.calibrator.fit(raw_meta_preds, y_int)
        self.is_fitted = True
        return self

    def predict(
        self,
        X_s1s2_dem: np.ndarray,
        X_alpha: np.ndarray,
        patches_msrm: np.ndarray,
        site_ids: Optional[List[str]] = None,
    ) -> List[HybridPrediction]:
        """
        Execute multistage inference:
        Stage A -> Stage B -> Stage C -> Stage D -> Calibration.
        """
        if not self.is_fitted:
            raise RuntimeError("HybridStackedDetector must be fitted before predict()")

        p_a = self.rf_stage_a.predict_proba(X_s1s2_dem)[:, 1]
        p_b = self.cnn_stage_b.predict_batch(patches_msrm)
        p_c = self.knn_stage_c.score(X_alpha)

        meta_X = np.column_stack([p_a, p_b, p_c])
        raw_meta_probs = self.meta_learner.predict_proba(meta_X)[:, 1]
        calibrated_probs = self.calibrator.transform(raw_meta_probs)

        n = len(X_s1s2_dem)
        ids = site_ids if site_ids is not None else [f"CAND_{i:04d}" for i in range(n)]

        results: List[HybridPrediction] = []
        for i in range(n):
            score_a = float(p_a[i])
            score_b = float(p_b[i])
            score_c = float(p_c[i])
            raw_p = float(raw_meta_probs[i])
            cal_p = float(calibrated_probs[i])

            # Stage B False-Positive Pruning rule:
            # If CNN morphology filter flags non-mound shape (< cnn_filter_threshold),
            # damp the posterior probability to eliminate false alarm
            is_pruned = score_b < self.cnn_filter_threshold
            if is_pruned:
                cal_p = min(cal_p, 0.45)

            # Assign Confidence Tier
            if cal_p >= 0.90:
                tier = "Tier 1: 90%-100% (Ultra-High Confidence)"
            elif cal_p >= 0.75:
                tier = "Tier 2: 75%-90% (High Confidence)"
            elif cal_p >= 0.50:
                tier = "Tier 3: 50%-75% (Moderate Confidence)"
            else:
                tier = "Low / Non-Target (<50%)"

            results.append(
                HybridPrediction(
                    site_id=ids[i],
                    stage_a_rf_score=round(score_a, 4),
                    stage_b_cnn_score=round(score_b, 4),
                    stage_c_alpha_score=round(score_c, 4),
                    stacked_raw_logit=round(raw_p, 4),
                    calibrated_probability=round(cal_p, 4),
                    is_false_positive_pruned=is_pruned,
                    confidence_tier=tier,
                )
            )

        return results
