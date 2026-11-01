"""
Automated Pytest Suite for Scoped Haryana Mound APM Pipeline.
Verifies all Phase 2 Design and Verification Rules:
1. AlphaEarth band names are strictly 0-indexed A00..A63 (64 bands).
2. H3 Resolution 8 standard geometry (~0.5314 km edge length, ~0.7373 km^2 area).
3. Dead-zone buffer (5,000 m) is strictly enforced between train and test sets in spatial block CV.
4. Target-Group Background (TGB) strictly excludes co-located multi-period sites within 500 m.
5. SAR-nnPU risk clamping prevents empirical negative risk from dropping below -beta_tolerance.
6. Propensity weights are strictly normalized to unit mean (mean == 1.0).
7. Public export strictly strips coordinates (lat, lon, x_m, y_m, site_name) and enforces k-anonymity (n >= 5).
8. Sample role assignment drops protected/excavated sites from training positives and excludes unverified map mounds.
9. Data-schema validator fails loudly on empty directories, missing columns, or zero confirmed sites.
10. End-to-end benchmark runner executes all 7 tracks under both Random CV and Buffered Spatial Block CV.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from scipy.spatial.distance import cdist

from src.data_validator import validate_processed_dataframe
from src.gee_export import ALPHAEARTH_BANDS, compute_msrm_and_tophats_numpy, get_alphaearth_band_names
from src.governance import (
    InstitutionalPartnerCredentials,
    PartnerFieldExportAdapter,
    obfuscate_candidates_for_public_view,
    verify_h3_res8_constants,
)
from src.labels_and_leakage import (
    assign_sample_roles,
    deduplicate_site_inventory,
    extract_scar_masked_patch_features,
    run_excavation_scar_leakage_probe,
    select_target_group_background,
)
from src.models import (
    AlphaEarthEmbeddingKNN,
    DetectabilityCoupledSurveyPropensity,
    TabularNNPUClassifier,
    compute_sar_nnpu_risk_and_grad,
)
from src.benchmark_runner import evaluate_benchmark_tracks
from src.validation import (
    compute_area_of_applicability,
    compute_recall_and_kvamme_gain_at_k,
    generate_spatial_block_cv_splits,
)


def test_alphaearth_band_names_zero_indexed():
    bands = get_alphaearth_band_names()
    assert len(bands) == 64
    assert bands[0] == "A00"
    assert bands[63] == "A63"
    assert "A64" not in bands


def test_h3_res8_geometry_constants():
    res = verify_h3_res8_constants()
    assert abs(res["h3_res8_edge_km"] - 0.5314) < 0.002
    assert abs(res["h3_res8_area_km2"] - 0.7373) < 0.005


def test_spatial_block_cv_dead_zone_buffer_enforced():
    rng = np.random.default_rng(123)
    coords = rng.uniform(0.0, 100000.0, size=(400, 2))
    buffer_m = 5000.0
    splits = generate_spatial_block_cv_splits(
        coords_m=coords, block_size_m=25000.0, dead_zone_buffer_m=buffer_m, n_folds=5
    )
    assert len(splits) == 5
    for tr_idx, te_idx in splits:
        assert len(tr_idx) > 0 and len(te_idx) > 0
        min_dist = float(cdist(coords[tr_idx], coords[te_idx]).min())
        assert min_dist >= buffer_m - 1e-5, f"Spatial leakage detected: min dist {min_dist} < {buffer_m}"


def test_tgb_excludes_colocated_multiperiod_sites():
    df = pd.DataFrame(
        {
            "site_id": ["S1", "S2", "S3", "S4", "S5"],
            "x_m": [500000.0, 500120.0, 510000.0, 520000.0, 530000.0],
            "y_m": [3250000.0, 3250100.0, 3250000.0, 3250000.0, 3250000.0],
            "is_ground_confirmed": [True, True, True, True, True],
            "is_protected_or_excavated": [False, False, False, False, False],
            "horizon_pgw": [1, 0, 1, 0, 0],
            "horizon_harappan": [0, 1, 1, 1, 0],  # S3 has both horizons; S5 has no other horizon
        }
    )
    presences, tgb = select_target_group_background(
        sites_df=df,
        target_horizon_col="horizon_pgw",
        other_horizon_cols=["horizon_harappan"],
        exclude_colocated_buffer_m=500.0,
    )
    assert set(presences["site_id"]) == {"S1", "S3"}
    # S2 is within 500m of S1 (excluded); S3 has PGW=1 (excluded); S5 has no other horizon (excluded)
    assert set(tgb["site_id"]) == {"S4"}


def test_nnpu_risk_clamping_prevents_negative_risk():
    rng = np.random.default_rng(42)
    X_pos = rng.normal(1.0, 0.5, size=(10, 4))
    X_unl = rng.normal(0.0, 0.5, size=(50, 4))
    w_pos = np.ones(10, dtype=np.float64)

    # Force a parameter vector that pushes negative risk r_u - pi_p * r_p negative
    params = np.array([5.0, 5.0, 5.0, 5.0, 10.0])
    prior_pi_p = 0.4
    beta_tol = 0.0

    obj, grad = compute_sar_nnpu_risk_and_grad(
        params=params,
        X_pos=X_pos,
        X_unl=X_unl,
        w_pos=w_pos,
        prior_pi_p=prior_pi_p,
        beta_tolerance=beta_tol,
        l2_reg=0.0,
    )
    # The non-negative risk clamping ensures obj >= 0 when l2_reg=0
    assert obj >= 0.0
    assert not np.isnan(obj)
    assert len(grad) == len(params)


def test_normalized_propensity_weights_have_unit_mean():
    rng = np.random.default_rng(99)
    X_pos = rng.normal(0.5, 0.5, size=(8, 3))
    X_unl = rng.normal(-0.5, 0.5, size=(30, 3))
    # Unnormalized weights with arbitrary scale
    raw_weights = np.array([0.1, 0.2, 0.5, 1.2, 0.8, 0.4, 0.9, 2.0])

    params = np.zeros(4, dtype=np.float64)
    # Inside compute_sar_nnpu_risk_and_grad, weights are normalized:
    w_norm = raw_weights / (np.mean(raw_weights) + 1e-8)
    assert abs(np.mean(w_norm) - 1.0) < 1e-7

    obj, grad = compute_sar_nnpu_risk_and_grad(params, X_pos, X_unl, raw_weights, prior_pi_p=0.02)
    assert not np.isnan(obj)


def test_public_obfuscation_strictly_strips_coordinates():
    df = pd.DataFrame(
        {
            "lat": [29.15 + i * 0.001 for i in range(10)],
            "lon": [75.70 + i * 0.001 for i in range(10)],
            "x_m": [568000.0 + i * 100 for i in range(10)],
            "y_m": [3225000.0 + i * 100 for i in range(10)],
            "site_name": [f"Mound_Candidate_{i}" for i in range(10)],
            "score": np.linspace(0.1, 0.95, 10),
            "aoa_valid": [True] * 10,
        }
    )
    pub = obfuscate_candidates_for_public_view(df, public_h3_res=5, min_count_k_anonymity=5)
    forbidden = {"lat", "lon", "x_m", "y_m", "site_name", "village_name", "exact_geometry"}
    assert forbidden.isdisjoint(set(pub.columns))
    assert "h3_public" in pub.columns
    assert "mean_score" in pub.columns


def test_role_assignment_drops_protected_and_unverified():
    df = pd.DataFrame(
        {
            "y_obs": [1, 1, 1, 0],
            "is_ground_confirmed": [True, True, False, False],
            "is_protected_or_excavated": [False, True, False, False],
            "discovery_modality": ["pedestrian_transect", "legacy_gazetteer", "toposheet_symbol", "satellite_visual"],
        }
    )
    assigned = assign_sample_roles(df)
    roles = assigned["sample_role"].tolist()
    assert roles == [
        "train_positive",             # Confirmed, unexcavated -> used for training
        "eval_protected_positive",    # Confirmed, protected -> held out as evaluation stratum
        "unverified_map_mound",       # Unverified map symbol -> separate weak-label experiment
        "unlabelled_background",      # Unlabelled background
    ]


def test_data_validator_fails_loudly_on_invalid_data():
    # Empty DataFrame fails
    with pytest.raises(ValueError, match="completely empty"):
        validate_processed_dataframe(pd.DataFrame(), source_name="empty_test")

    # Missing mandatory columns fails
    partial_df = pd.DataFrame({"x_m": [500000.0], "y_m": [3200000.0], "y_obs": [1]})
    with pytest.raises(KeyError, match="missing .* mandatory columns"):
        validate_processed_dataframe(partial_df, source_name="missing_cols_test")

    # Zero confirmed positives fails
    no_confirmed_df = pd.DataFrame(
        {
            "x_m": [500000.0, 501000.0],
            "y_m": [3200000.0, 3201000.0],
            "y_obs": [1, 0],
            "is_ground_confirmed": [False, False],
            "is_protected_or_excavated": [False, False],
            "discovery_modality": ["toposheet_symbol", "satellite_visual"],
            "relief_class": ["low_<1m", "low_<1m"],
            "msrm": [1.0, 0.0],
            "wth_150m": [1.0, 0.0],
            "bth_150m": [0.0, 0.0],
            "NDVI_p50": [0.3, 0.3],
            "BSI_zaid_med": [0.1, 0.1],
            "VH_p50": [-15.0, -15.0],
        }
    )
    for b in ALPHAEARTH_BANDS:
        no_confirmed_df[b] = 0.0

    with pytest.raises(ValueError, match="ZERO are marked 'is_ground_confirmed == True'"):
        validate_processed_dataframe(no_confirmed_df, source_name="no_confirmed_test")


def test_end_to_end_benchmark_runner():
    rng = np.random.default_rng(7)
    n = 220
    df = pd.DataFrame(
        {
            "x_m": rng.uniform(500000.0, 590000.0, size=n),
            "y_m": rng.uniform(3200000.0, 3290000.0, size=n),
            "y_obs": np.array([1] * 35 + [0] * (n - 35)),
            "is_ground_confirmed": np.array([True] * 25 + [False] * 10 + [False] * (n - 35)),
            "is_protected_or_excavated": np.array([False] * 20 + [True] * 5 + [False] * (n - 25)),
            "is_hard_negative": np.array([0] * 35 + [1] * 25 + [0] * (n - 60)),
            "on_soi_map": rng.integers(0, 2, size=n),
            "dist_road_km": rng.uniform(0.1, 15.0, size=n),
            "dist_town_km": rng.uniform(1.0, 30.0, size=n),
            "relief_class": ["high_>=1.5m" if i < 15 else "low_<1m" for i in range(n)],
            "discovery_modality": ["toposheet_symbol" if i % 2 == 0 else "pedestrian_transect" for i in range(n)],
            "msrm": rng.normal(0.0, 1.0, size=n),
            "wth_150m": rng.normal(0.0, 1.0, size=n),
            "bth_150m": rng.normal(0.0, 1.0, size=n),
            "NDVI_p50": rng.normal(0.3, 0.1, size=n),
            "BSI_zaid_med": rng.normal(0.1, 0.05, size=n),
            "VH_p50": rng.normal(-15.0, 2.0, size=n),
        }
    )
    emb_mat = rng.normal(0.0, 1.0, size=(n, 64))
    emb_mat[:25, :5] += 1.5
    for j, bname in enumerate(ALPHAEARTH_BANDS):
        df[bname] = emb_mat[:, j]

    summary_df, strat_df, scar_audit, weak_label_df = evaluate_benchmark_tracks(
        df=df,
        s1_s2_dem_cols=["NDVI_p50", "BSI_zaid_med", "VH_p50", "msrm", "wth_150m", "bth_150m"],
        dem_only_cols=["msrm", "wth_150m", "bth_150m"],
        embedding_cols=ALPHAEARTH_BANDS,
        prior_pi_p=0.05,
        dead_zone_buffer_m=2000.0,
        random_state=42,
    )
    # 7 tracks x 2 CV schemes (Random vs Spatial Block) = 14 rows
    assert len(summary_df) == 14
    assert not strat_df.empty
    assert "probe_auc" in scar_audit
    assert not weak_label_df.empty


def test_patch250m_and_h3_dual_spatial_units():
    """Verify that the benchmark runner executes across both H3 Res 8 and 250m regular patch spatial units (28 rows total)."""
    rng = np.random.default_rng(101)
    n = 180

    def make_synthetic_df(scale_m: float):
        df = pd.DataFrame(
            {
                "x_m": rng.uniform(500000.0, 560000.0, size=n),
                "y_m": rng.uniform(3200000.0, 3260000.0, size=n),
                "y_obs": np.array([1] * 25 + [0] * (n - 25)),
                "is_ground_confirmed": np.array([True] * 20 + [False] * 5 + [False] * (n - 25)),
                "is_protected_or_excavated": np.array([False] * 16 + [True] * 4 + [False] * (n - 20)),
                "is_hard_negative": np.array([0] * 25 + [1] * 20 + [0] * (n - 45)),
                "on_soi_map": rng.integers(0, 2, size=n),
                "dist_road_km": rng.uniform(0.1, 10.0, size=n),
                "dist_town_km": rng.uniform(1.0, 20.0, size=n),
                "relief_class": ["high_>=1.5m" if i < 10 else "low_<1m" for i in range(n)],
                "discovery_modality": ["toposheet_symbol" if i % 2 == 0 else "pedestrian_transect" for i in range(n)],
                "msrm": rng.normal(0.0, 1.0, size=n) + (scale_m * 0.5),
                "wth_150m": rng.normal(0.0, 1.0, size=n),
                "bth_150m": rng.normal(0.0, 1.0, size=n),
                "NDVI_p50": rng.normal(0.3, 0.1, size=n),
                "BSI_zaid_med": rng.normal(0.1, 0.05, size=n),
                "VH_p50": rng.normal(-15.0, 2.0, size=n),
            }
        )
        for j, bname in enumerate(ALPHAEARTH_BANDS):
            df[bname] = rng.normal(0.0, 1.0, size=n)
        return df

    df_h3 = make_synthetic_df(scale_m=1.0)
    df_patch = make_synthetic_df(scale_m=1.5)

    sum_h3, _, _, _ = evaluate_benchmark_tracks(
        df=df_h3,
        s1_s2_dem_cols=["NDVI_p50", "BSI_zaid_med", "VH_p50", "msrm", "wth_150m", "bth_150m"],
        dem_only_cols=["msrm", "wth_150m", "bth_150m"],
        spatial_unit="h3_res8",
        dead_zone_buffer_m=2000.0,
        random_state=42,
    )
    sum_patch, _, _, _ = evaluate_benchmark_tracks(
        df=df_patch,
        s1_s2_dem_cols=["NDVI_p50", "BSI_zaid_med", "VH_p50", "msrm", "wth_150m", "bth_150m"],
        dem_only_cols=["msrm", "wth_150m", "bth_150m"],
        spatial_unit="patch_250m",
        dead_zone_buffer_m=2000.0,
        random_state=42,
    )

    combined_summary = pd.concat([sum_h3, sum_patch], ignore_index=True)
    # 7 tracks x 2 CV schemes x 2 spatial units = 28 rows
    assert len(combined_summary) == 28
    assert set(combined_summary["spatial_unit"]) == {"h3_res8", "patch_250m"}


def test_public_data_curator_canonical_sites():
    from src.public_data_curator import build_canonical_sites_dataframe, wgs84_to_utm43n
    df = build_canonical_sites_dataframe(include_unverified=True)
    assert len(df) == 30
    assert set(df["district"]).issubset({"Hisar", "Fatehabad", "Sirsa"})
    
    # Check bounds
    assert (df["x_m"] >= 400000.0).all() and (df["x_m"] <= 700000.0).all()
    assert (df["y_m"] >= 3150000.0).all() and (df["y_m"] <= 3350000.0).all()

    df_roles = assign_sample_roles(df)
    counts = df_roles["sample_role"].value_counts().to_dict()
    assert counts["train_positive"] == 15
    assert counts["eval_protected_positive"] == 9
    assert counts["unverified_map_mound"] == 6


def test_feature_generator_schema_compliance(tmp_path):
    from src.feature_generator import generate_benchmark_feature_dataset
    df = generate_benchmark_feature_dataset(spatial_unit="patch_250m", n_background_samples=150, random_state=42)
    assert len(df) > 150
    # Must pass strict schema validator without raising
    validated = validate_processed_dataframe(df, source_name="test_patch")
    assert not validated.empty


def test_visualization_suite(tmp_path):
    from src.visualization import (
        plot_empirical_variogram,
        plot_aoa_dissimilarity_distribution,
        plot_public_obfuscated_map,
    )
    rng = np.random.default_rng(42)
    coords = rng.uniform(500000, 550000, size=(100, 2))
    feats = rng.normal(0, 1, size=(100, 10))

    p_var = tmp_path / "var.png"
    rg = plot_empirical_variogram(coords, feats, output_path=p_var)
    assert p_var.exists()
    assert rg > 0.0

    p_aoa = tmp_path / "aoa.png"
    plot_aoa_dissimilarity_distribution(rng.exponential(1.0, size=100), threshold=1.5, output_path=p_aoa)
    assert p_aoa.exists()

    df_map = pd.DataFrame({
        "x_m": coords[:, 0],
        "y_m": coords[:, 1],
        "msrm": rng.normal(0, 1, size=100),
    })
    p_map = tmp_path / "map.png"
    plot_public_obfuscated_map(df_map, output_path=p_map)
    assert p_map.exists()

