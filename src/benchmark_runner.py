"""
End-to-End Benchmark Runner for the Scoped Haryana Pilot (Hisar, Fatehabad, Sirsa).
Enforces Phase 2 Design Revisions:
1. Positives = Ground-confirmed, unexcavated sites ONLY (`train_positive`).
2. Unverified SOI map mounds are EXCLUDED from training positives & background, evaluated in a separate weak-label experiment.
3. Protected / excavated sites are DROPPED from training positives, evaluated as a separate diagnostic stratum.
4. Propensity weighting is evaluated as a sensitivity analysis: T3 and T5 are reported BOTH unweighted and weighted.
5. Evaluates Random 5-fold CV vs. Buffered Spatial Block 5-fold CV (variogram-sized + 5 km dead-zone buffer).
"""

from __future__ import annotations
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from src.gee_export import ALPHAEARTH_BANDS
from src.labels_and_leakage import assign_sample_roles, run_excavation_scar_leakage_probe
from src.models import (
    AlphaEarthEmbeddingKNN,
    DetectabilityCoupledSurveyPropensity,
    TabularNNPUClassifier,
    build_lightgbm_baseline,
    build_rf_orengo2020_baseline,
)
from src.validation import (
    compute_area_of_applicability,
    compute_recall_and_kvamme_gain_at_k,
    estimate_empirical_variogram_range_m,
    evaluate_stratified_by_relief_and_modality,
    generate_spatial_block_cv_splits,
)


def evaluate_benchmark_tracks(
    df: pd.DataFrame,
    s1_s2_dem_cols: List[str],
    dem_only_cols: List[str],
    embedding_cols: List[str] = ALPHAEARTH_BANDS,
    accessibility_cols: Tuple[str, ...] = ("dist_road_km", "dist_town_km"),
    prior_pi_p: float = 0.02,
    dead_zone_buffer_m: float = 5000.0,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, float | bool], pd.DataFrame]:
    """
    Execute 5-track benchmark comparing Random CV vs. Buffered Spatial Block CV,
    stratified by mound relief, discovery modality, protected site status, and unverified map mounds.
    """
    df = assign_sample_roles(df)

    coords_m = df[["x_m", "y_m"]].to_numpy(dtype=np.float64)
    X_s1s2_dem = df[s1_s2_dem_cols].to_numpy(dtype=np.float64)
    X_emb = df[embedding_cols].to_numpy(dtype=np.float64)
    X_emb_dem = np.hstack([X_emb, df[dem_only_cols].to_numpy(dtype=np.float64)])

    # Sample role masks
    is_train_pos = (df["sample_role"] == "train_positive").to_numpy()
    is_protected_pos = (df["sample_role"] == "eval_protected_positive").to_numpy()
    is_unverified_mound = (df["sample_role"] == "unverified_map_mound").to_numpy()
    is_unlabelled_bg = (df["sample_role"] == "unlabelled_background").to_numpy()

    # Binary training target: 1 for confirmed unexcavated sites, 0 for unlabelled background
    # Unverified map mounds and protected sites have target = -1 (ignored in training loss)
    y_train = np.full(len(df), -1, dtype=int)
    y_train[is_train_pos] = 1
    y_train[is_unlabelled_bg] = 0

    # Ground-truth evaluation target: 1 for any confirmed site (train + protected), 0 for background
    y_eval_confirmed = np.zeros(len(df), dtype=int)
    y_eval_confirmed[is_train_pos | is_protected_pos] = 1

    # 1. Run excavation-scar leakage audit on all confirmed sites
    confirmed_mask = y_eval_confirmed == 1
    scar_audit = run_excavation_scar_leakage_probe(
        X_positives=X_s1s2_dem[confirmed_mask],
        is_excavated_or_protected=is_protected_pos[confirmed_mask].astype(int),
        random_state=random_state,
    )

    # 2. Propensity score calculation (sensitivity proxy)
    propensity_model = DetectabilityCoupledSurveyPropensity(min_propensity_clip=0.05)
    prop_target = np.zeros(len(df), dtype=int)
    prop_target[is_train_pos | is_protected_pos] = 1
    propensity_model.fit(
        detectability_proxy=df["msrm"].to_numpy(dtype=np.float64),
        on_historical_map=df["on_soi_map"].to_numpy(dtype=np.float64) if "on_soi_map" in df.columns else np.zeros(len(df)),
        accessibility_covariates=df[list(accessibility_cols)].to_numpy(dtype=np.float64),
        target_labels=prop_target,
    )
    prop_scores = propensity_model.predict_propensity(
        detectability_proxy=df["msrm"].to_numpy(dtype=np.float64),
        on_historical_map=df["on_soi_map"].to_numpy(dtype=np.float64) if "on_soi_map" in df.columns else np.zeros(len(df)),
        accessibility_covariates=df[list(accessibility_cols)].to_numpy(dtype=np.float64),
    )

    # 3. Sizing spatial CV blocks via empirical variogram range
    vario_range_m = estimate_empirical_variogram_range_m(coords_m, X_s1s2_dem, random_state=random_state)
    block_size_m = max(25000.0, 1.25 * vario_range_m)

    spatial_splits = generate_spatial_block_cv_splits(
        coords_m=coords_m,
        block_size_m=block_size_m,
        dead_zone_buffer_m=dead_zone_buffer_m,
        n_folds=5,
        random_state=random_state,
    )

    # Random splits stratify on confirmed sites vs unlabelled
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    train_eligible_idx = np.where(y_train >= 0)[0]
    random_splits_raw = list(skf.split(train_eligible_idx, y_train[train_eligible_idx]))
    random_splits = []
    for tr_sub, te_sub in random_splits_raw:
        te_set = set(train_eligible_idx[te_sub])
        tr_set = set(train_eligible_idx[tr_sub])
        # Add unverified mounds and protected sites to test set for evaluation
        eval_only_idx = np.where(y_train == -1)[0]
        te_full = np.array(sorted(te_set | set(eval_only_idx)), dtype=int)
        tr_full = np.array(sorted(tr_set), dtype=int)
        random_splits.append((tr_full, te_full))

    # Tracks covering models and sensitivity variations
    tracks = [
        ("T1_RF_S1S2_FABDEM", "s1s2_dem", "rf", False),
        ("T2_LGBM_S1S2_FABDEM", "s1s2_dem", "lgbm", False),
        ("T3a_SAR_nnPU_S1S2_FABDEM_Unweighted", "s1s2_dem", "nnpu", False),
        ("T3b_SAR_nnPU_S1S2_FABDEM_PropensityWeighted", "s1s2_dem", "nnpu", True),
        ("T4_KNN_AlphaEarth_Only", "emb_only", "knn", False),
        ("T5a_SAR_nnPU_AlphaEarth_FABDEM_Unweighted", "emb_dem", "nnpu", False),
        ("T5b_SAR_nnPU_AlphaEarth_FABDEM_PropensityWeighted", "emb_dem", "nnpu", True),
    ]

    summary_rows: List[Dict] = []
    stratified_dfs: List[pd.DataFrame] = []
    weak_label_rows: List[Dict] = []

    for split_scheme, splits in [("Random_5Fold_CV", random_splits), ("Spatial_Block_Buffered_CV", spatial_splits)]:
        for track_name, feat_key, model_key, use_weights in tracks:
            X_mat = {"s1s2_dem": X_s1s2_dem, "emb_only": X_emb, "emb_dem": X_emb_dem}[feat_key]
            oof_scores = np.full(len(df), np.nan, dtype=np.float64)
            oof_aoa = np.zeros(len(df), dtype=bool)

            for tr_idx, te_idx in splits:
                # Filter training instances to strictly eligible training samples (train_positive & unlabelled_bg)
                tr_mask = y_train[tr_idx] >= 0
                actual_tr_idx = tr_idx[tr_mask]
                if np.sum(y_train[actual_tr_idx] == 1) < 2 or np.sum(y_train[actual_tr_idx] == 0) < 5:
                    continue

                _, aoa_mask, _ = compute_area_of_applicability(X_mat[actual_tr_idx], X_mat[te_idx])
                oof_aoa[te_idx] = aoa_mask

                if model_key == "rf":
                    clf = build_rf_orengo2020_baseline(random_state=random_state)
                    clf.fit(X_mat[actual_tr_idx], y_train[actual_tr_idx])
                    oof_scores[te_idx] = clf.predict_proba(X_mat[te_idx])[:, 1]
                elif model_key == "lgbm":
                    clf = build_lightgbm_baseline(random_state=random_state)
                    clf.fit(X_mat[actual_tr_idx], y_train[actual_tr_idx])
                    oof_scores[te_idx] = clf.predict_proba(X_mat[te_idx])[:, 1]
                elif model_key == "nnpu":
                    clf = TabularNNPUClassifier(prior_pi_p=prior_pi_p, max_iter=100, random_state=random_state)
                    w = prop_scores[actual_tr_idx] if use_weights else None
                    clf.fit(X_mat[actual_tr_idx], y_train[actual_tr_idx], propensity_scores=w)
                    oof_scores[te_idx] = clf.predict_proba(X_mat[te_idx])[:, 1]
                elif model_key == "knn":
                    # Unexcavated confirmed positives only
                    unexc_pos = actual_tr_idx[y_train[actual_tr_idx] == 1]
                    hard_neg = actual_tr_idx[
                        (y_train[actual_tr_idx] == 0)
                        & (df.loc[actual_tr_idx, "is_hard_negative"].to_numpy() == 1
                           if "is_hard_negative" in df.columns else False)
                    ]
                    knn = AlphaEarthEmbeddingKNN(k_positives=5, k_hard_negatives=5)
                    knn.fit(X_mat[unexc_pos], X_mat[hard_neg] if len(hard_neg) > 0 else None)
                    oof_scores[te_idx] = knn.score(X_mat[te_idx])

            # Evaluate on confirmed sites vs unlabelled background
            eval_mask = ~np.isnan(oof_scores) & (is_train_pos | is_protected_pos | is_unlabelled_bg)
            metrics = compute_recall_and_kvamme_gain_at_k(
                oof_scores[eval_mask], y_eval_confirmed[eval_mask], [1.0, 2.0, 5.0, 10.0]
            )
            metrics["track"] = track_name
            metrics["cv_scheme"] = split_scheme
            metrics["aoa_retention_pct"] = float(np.mean(oof_aoa[eval_mask]) * 100.0)
            metrics["block_size_km"] = block_size_m / 1000.0
            summary_rows.append(metrics)

            if split_scheme == "Spatial_Block_Buffered_CV":
                # Stratification by relief and modality
                valid_split = ~np.isnan(oof_scores) & eval_mask
                strat_df = evaluate_stratified_by_relief_and_modality(
                    scores=oof_scores[valid_split],
                    y_true=y_eval_confirmed[valid_split],
                    relief_class=df.loc[valid_split, "relief_class"].tolist(),
                    discovery_modality=df.loc[valid_split, "discovery_modality"].tolist(),
                    k_pct=5.0,
                )
                strat_df["track"] = track_name
                stratified_dfs.append(strat_df)

                # Separate evaluation of held-out protected/excavated stratum
                prot_subset = ~np.isnan(oof_scores) & (is_protected_pos | is_unlabelled_bg)
                if np.any(is_protected_pos):
                    prot_metrics = compute_recall_and_kvamme_gain_at_k(
                        oof_scores[prot_subset], is_protected_pos[prot_subset].astype(int), [5.0]
                    )
                    stratified_dfs.append(
                        pd.DataFrame(
                            [
                                {
                                    "stratum_type": "held_out_protected_status",
                                    "stratum_value": "protected_or_excavated",
                                    "n_positives": int(np.sum(is_protected_pos)),
                                    "recall_at_5pct": prot_metrics["recall_at_5pct"],
                                    "kvamme_gain_at_5pct": prot_metrics["kvamme_gain_at_5pct"],
                                    "track": track_name,
                                }
                            ]
                        )
                    )

                # Separate weak-label evaluation of unverified SOI map mounds
                if np.any(is_unverified_mound):
                    mound_subset = ~np.isnan(oof_scores) & (is_unverified_mound | is_unlabelled_bg)
                    mound_metrics = compute_recall_and_kvamme_gain_at_k(
                        oof_scores[mound_subset], is_unverified_mound[mound_subset].astype(int), [5.0]
                    )
                    weak_label_rows.append(
                        {
                            "track": track_name,
                            "n_unverified_mounds": int(np.sum(is_unverified_mound)),
                            "recall_at_5pct": mound_metrics["recall_at_5pct"],
                            "kvamme_gain_at_5pct": mound_metrics["kvamme_gain_at_5pct"],
                        }
                    )

    summary_df = pd.DataFrame(summary_rows)
    stratified_all = pd.concat(stratified_dfs, ignore_index=True) if stratified_dfs else pd.DataFrame()
    weak_label_df = pd.DataFrame(weak_label_rows) if weak_label_rows else pd.DataFrame()
    return summary_df, stratified_all, scar_audit, weak_label_df
