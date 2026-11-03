"""
Cross-Basin External Model Transfer & Area of Applicability (AoA) Validator.
Evaluates model generalizability:
- Training: Haryana Pilot (Hisar, Fatehabad, Sirsa) in the eastern Saraswati/Ghaggar-Hakra alluvium.
- Testing: Cholistan Desert (Hakra River bed, Pakistan) with hyper-arid dune/playa background.
- Benchmarks against: Orengo et al. (2020, PNAS) published archaeological mound detections.
- Implements: Meyer & Pebesma (2021, MEE) Area of Applicability & Dissimilarity Index (DI).
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.gee_export import ALPHAEARTH_BANDS
from src.labels_and_leakage import assign_sample_roles
from src.models import (
    AlphaEarthEmbeddingKNN,
    TabularNNPUClassifier,
    build_rf_orengo2020_baseline,
)
from src.validation import (
    compute_area_of_applicability,
    compute_recall_and_kvamme_gain_at_k,
)

ORENGO_FEATURE_COLS = [
    "msrm", "wth_150m", "bth_150m",
    "NDVI_p50", "BSI_zaid_med",
    "VH_p50", "VV_p50",
    "B2", "B3", "B4", "B8", "B11", "B12",
]


@dataclass
class CrossBasinTransferResult:
    model_name: str
    feature_modality: str
    n_train_haryana: int
    n_test_cholistan: int
    n_cholistan_known_sites: int
    aoa_threshold: float
    pct_cholistan_inside_aoa: float
    overall_recall_at_1pct: float
    overall_recall_at_5pct: float
    overall_recall_at_10pct: float
    kvamme_gain_at_5pct: float
    aoa_filtered_recall_at_5pct: float
    aoa_filtered_kvamme_gain_at_5pct: float
    ganweriwala_rank: int
    derawar_rank: int
    kudwala_rank: int


class CrossBasinValidator:
    """
    Executes cross-basin transfer testing from Haryana training to Cholistan testing.
    """

    def __init__(
        self,
        haryana_data_path: Path,
        cholistan_data_path: Path,
        random_state: int = 42,
    ) -> None:
        self.haryana_df = pd.read_csv(haryana_data_path)
        self.cholistan_df = pd.read_csv(cholistan_data_path)
        self.random_state = random_state

        # Ensure sample roles assigned for Haryana
        if "sample_role" not in self.haryana_df.columns:
            self.haryana_df = assign_sample_roles(self.haryana_df)

        # Prepare training data (positives = ground-confirmed, unexcavated sites only)
        train_mask = self.haryana_df["sample_role"] == "train_positive"
        unl_mask = self.haryana_df["sample_role"] == "unlabelled_background"
        self.haryana_train = self.haryana_df[train_mask | unl_mask].copy()

    def run_orengo_rf_transfer(self) -> Tuple[CrossBasinTransferResult, pd.DataFrame]:
        """
        Train Orengo RF on Haryana, evaluate on Cholistan with AoA masking.
        """
        X_train = self.haryana_train[ORENGO_FEATURE_COLS].to_numpy(dtype=float)
        y_train = (self.haryana_train["sample_role"] == "train_positive").to_numpy(dtype=int)

        X_test = self.cholistan_df[ORENGO_FEATURE_COLS].to_numpy(dtype=float)
        y_test = self.cholistan_df["is_ground_confirmed"].to_numpy(dtype=int)

        # 1. Compute Area of Applicability
        di_query, aoa_mask, threshold = compute_area_of_applicability(X_train, X_test)
        pct_inside_aoa = float(np.mean(aoa_mask) * 100.0)

        # 2. Fit Orengo RF Baseline
        rf = build_rf_orengo2020_baseline(random_state=self.random_state)
        rf.fit(X_train, y_train)

        # 3. Predict presence scores on Cholistan
        scores = rf.predict_proba(X_test)[:, 1]

        # 4. Evaluation Metrics (Unfiltered)
        metrics_all = compute_recall_and_kvamme_gain_at_k(scores, y_test, [1.0, 5.0, 10.0])

        # 5. Evaluation Metrics (Inside AoA only)
        if np.any(aoa_mask & (y_test == 1)):
            scores_aoa = scores[aoa_mask]
            y_test_aoa = y_test[aoa_mask]
            metrics_aoa = compute_recall_and_kvamme_gain_at_k(scores_aoa, y_test_aoa, [5.0])
            aoa_rec_5 = metrics_aoa["recall_at_5pct"]
            aoa_gain_5 = metrics_aoa["kvamme_gain_at_5pct"]
        else:
            aoa_rec_5 = float("nan")
            aoa_gain_5 = float("nan")

        # 6. Check individual ranks of canonical megasites
        order = np.argsort(-scores)
        ranks = {self.cholistan_df.iloc[idx]["site_id"]: rank + 1 for rank, idx in enumerate(order)}

        res = CrossBasinTransferResult(
            model_name="RandomForest_Orengo2020_Baseline",
            feature_modality="Sentinel1_2_and_DEM",
            n_train_haryana=len(X_train),
            n_test_cholistan=len(X_test),
            n_cholistan_known_sites=int(np.sum(y_test == 1)),
            aoa_threshold=round(threshold, 3),
            pct_cholistan_inside_aoa=round(pct_inside_aoa, 1),
            overall_recall_at_1pct=round(metrics_all["recall_at_1pct"], 3),
            overall_recall_at_5pct=round(metrics_all["recall_at_5pct"], 3),
            overall_recall_at_10pct=round(metrics_all["recall_at_10pct"], 3),
            kvamme_gain_at_5pct=round(metrics_all["kvamme_gain_at_5pct"], 3),
            aoa_filtered_recall_at_5pct=round(aoa_rec_5, 3),
            aoa_filtered_kvamme_gain_at_5pct=round(aoa_gain_5, 3),
            ganweriwala_rank=ranks.get("CHOL_001", -1),
            derawar_rank=ranks.get("CHOL_003", -1),
            kudwala_rank=ranks.get("CHOL_002", -1),
        )

        # Output predictions DataFrame
        preds_df = self.cholistan_df.copy()
        preds_df["predicted_score"] = scores
        preds_df["dissimilarity_index"] = di_query
        preds_df["inside_aoa"] = aoa_mask
        preds_df["detection_rank"] = [ranks[sid] for sid in preds_df["site_id"]]

        return res, preds_df

    def run_alphaearth_knn_transfer(self) -> Tuple[CrossBasinTransferResult, pd.DataFrame]:
        """
        Train AlphaEarth kNN prototype matcher on Haryana, evaluate on Cholistan.
        """
        E_train = self.haryana_train[ALPHAEARTH_BANDS].to_numpy(dtype=float)
        y_train = (self.haryana_train["sample_role"] == "train_positive").to_numpy(dtype=int)

        E_test = self.cholistan_df[ALPHAEARTH_BANDS].to_numpy(dtype=float)
        y_test = self.cholistan_df["is_ground_confirmed"].to_numpy(dtype=int)

        # AoA
        di_query, aoa_mask, threshold = compute_area_of_applicability(E_train, E_test)
        pct_inside_aoa = float(np.mean(aoa_mask) * 100.0)

        # Fit AlphaEarth kNN
        knn = AlphaEarthEmbeddingKNN(k_positives=5)
        knn.fit(E_train[y_train == 1])
        scores = knn.score(E_test)

        metrics_all = compute_recall_and_kvamme_gain_at_k(scores, y_test, [1.0, 5.0, 10.0])

        order = np.argsort(-scores)
        ranks = {self.cholistan_df.iloc[idx]["site_id"]: rank + 1 for rank, idx in enumerate(order)}

        res = CrossBasinTransferResult(
            model_name="AlphaEarth_Foundation_kNN",
            feature_modality="AlphaEarth_64D_Embeddings",
            n_train_haryana=len(E_train),
            n_test_cholistan=len(E_test),
            n_cholistan_known_sites=int(np.sum(y_test == 1)),
            aoa_threshold=round(threshold, 3),
            pct_cholistan_inside_aoa=round(pct_inside_aoa, 1),
            overall_recall_at_1pct=round(metrics_all["recall_at_1pct"], 3),
            overall_recall_at_5pct=round(metrics_all["recall_at_5pct"], 3),
            overall_recall_at_10pct=round(metrics_all["recall_at_10pct"], 3),
            kvamme_gain_at_5pct=round(metrics_all["kvamme_gain_at_5pct"], 3),
            aoa_filtered_recall_at_5pct=round(metrics_all["recall_at_5pct"], 3),
            aoa_filtered_kvamme_gain_at_5pct=round(metrics_all["kvamme_gain_at_5pct"], 3),
            ganweriwala_rank=ranks.get("CHOL_001", -1),
            derawar_rank=ranks.get("CHOL_003", -1),
            kudwala_rank=ranks.get("CHOL_002", -1),
        )

        preds_df = self.cholistan_df.copy()
        preds_df["predicted_score"] = scores
        preds_df["dissimilarity_index"] = di_query
        preds_df["inside_aoa"] = aoa_mask
        preds_df["detection_rank"] = [ranks[sid] for sid in preds_df["site_id"]]

        return res, preds_df
