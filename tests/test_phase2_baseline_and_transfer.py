"""
Pytest Suite for Phase 2:
1. Baseline Model Replication (Orengo et al. 2020 Random Forest, AlphaEarth kNN).
2. Cholistan Cross-Basin Dataset Schema and Ground-Truth Integrity.
3. Cross-Basin External Transfer Execution (Haryana -> Cholistan).
4. Area of Applicability (AoA) & Dissimilarity Index (DI) evaluation.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

from src.cross_basin_validator import CrossBasinValidator, ORENGO_FEATURE_COLS
from src.models import build_rf_orengo2020_baseline, AlphaEarthEmbeddingKNN
from src.validation import compute_area_of_applicability, compute_recall_and_kvamme_gain_at_k


@pytest.fixture
def haryana_and_cholistan_paths():
    h_path = REPO_ROOT / "data" / "processed" / "haryana_h3_res8_features.csv"
    c_path = REPO_ROOT / "data" / "cholistan" / "cholistan_ground_truth_and_eval.csv"
    assert h_path.exists(), f"Haryana dataset missing: {h_path}"
    assert c_path.exists(), f"Cholistan dataset missing: {c_path}"
    return h_path, c_path


def test_cholistan_ground_truth_dataset_integrity(haryana_and_cholistan_paths):
    _, c_path = haryana_and_cholistan_paths
    df_chol = pd.read_csv(c_path)
    
    assert len(df_chol) >= 400
    # Must contain canonical megasites
    site_names = df_chol["site_name"].tolist()
    assert any("Ganweriwala" in s for s in site_names)
    assert any("Derawar" in s for s in site_names)
    assert any("Kudwala" in s for s in site_names)

    # Required feature columns must be present and finite
    for col in ORENGO_FEATURE_COLS:
        assert col in df_chol.columns
        assert not df_chol[col].isna().any()

    # AlphaEarth 64 bands present
    for j in range(64):
        col_name = f"A{j:02d}"
        assert col_name in df_chol.columns


def test_orengo_rf_cross_basin_transfer(haryana_and_cholistan_paths):
    h_path, c_path = haryana_and_cholistan_paths
    validator = CrossBasinValidator(h_path, c_path, random_state=42)
    
    res, preds_df = validator.run_orengo_rf_transfer()
    assert res.model_name == "RandomForest_Orengo2020_Baseline"
    assert res.overall_recall_at_5pct >= 0.80
    assert res.kvamme_gain_at_5pct > 0.80
    assert res.ganweriwala_rank <= 10
    
    # Check predictions dataframe
    assert "predicted_score" in preds_df.columns
    assert "dissimilarity_index" in preds_df.columns
    assert "inside_aoa" in preds_df.columns
    assert len(preds_df) == len(validator.cholistan_df)


def test_alphaearth_knn_cross_basin_transfer(haryana_and_cholistan_paths):
    h_path, c_path = haryana_and_cholistan_paths
    validator = CrossBasinValidator(h_path, c_path, random_state=42)
    
    res, preds_df = validator.run_alphaearth_knn_transfer()
    assert res.model_name == "AlphaEarth_Foundation_kNN"
    assert res.overall_recall_at_5pct >= 0.80
    assert res.ganweriwala_rank <= 5
    assert res.pct_cholistan_inside_aoa >= 90.0  # Latent embeddings invariant across biomes


def test_area_of_applicability_dissimilarity_index():
    rng = np.random.default_rng(42)
    X_train = rng.normal(0.0, 1.0, size=(100, 5))
    # Query with same distribution
    X_in = rng.normal(0.0, 1.0, size=(20, 5))
    # Query with distant outlier distribution
    X_out = rng.normal(10.0, 1.0, size=(20, 5))

    di_in, mask_in, th = compute_area_of_applicability(X_train, X_in)
    di_out, mask_out, _ = compute_area_of_applicability(X_train, X_out)

    assert mask_in.sum() > mask_out.sum()
    assert di_out.mean() > di_in.mean()
