"""
Spatial Block Cross-Validation (with Dead-Zone Buffer), Area of Applicability (AoA),
Stratified Recall@k% & Kvamme's Gain, and Random-vs-Spatial CV Gap Evaluation.

References:
- Roberts et al. (2017, Ecography, doi:10.1111/ecog.02881)
- Valavi et al. (2019, MEE, doi:10.1111/2041-210X.13107)
- Meyer & Pebesma (2021, MEE, doi:10.1111/2041-210X.13650)
"""

from __future__ import annotations
from typing import Dict, Iterator, List, Optional, Sequence, Tuple
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist, pdist
from sklearn.model_selection import StratifiedKFold


def estimate_empirical_variogram_range_m(
    coords_m: np.ndarray,
    features: np.ndarray,
    n_bins: int = 15,
    max_sample: int = 1500,
    random_state: int = 42,
) -> float:
    """
    Estimate the effective spatial autocorrelation range (95% sill threshold)
    across standardized environmental/sensor features to size spatial CV blocks.
    """
    rng = np.random.default_rng(random_state)
    if len(coords_m) > max_sample:
        idx = rng.choice(len(coords_m), size=max_sample, replace=False)
        coords_m = coords_m[idx]
        features = features[idx]

    z = (features - np.nanmean(features, axis=0)) / (np.nanstd(features, axis=0) + 1e-8)
    dists = pdist(coords_m)
    semivars = 0.5 * pdist(z, metric="sqeuclidean") / z.shape[1]

    max_d = float(np.percentile(dists, 70))
    bins = np.linspace(0.0, max_d, n_bins + 1)
    bin_centers = 0.5 * (bins[:-1] + bins[1:])
    gamma = np.zeros(n_bins, dtype=np.float64)

    for b in range(n_bins):
        mask = (dists >= bins[b]) & (dists < bins[b + 1])
        gamma[b] = float(np.mean(semivars[mask])) if np.any(mask) else np.nan

    valid = ~np.isnan(gamma)
    if not np.any(valid):
        return 25000.0
    sill = float(np.nanpercentile(gamma[valid], 90))
    reached = np.where(gamma >= 0.95 * sill)[0]
    if len(reached) == 0:
        return float(bin_centers[valid][-1])
    return float(max(bin_centers[reached[0]], 5000.0))


def generate_spatial_block_cv_splits(
    coords_m: np.ndarray,
    block_size_m: float = 25000.0,
    dead_zone_buffer_m: float = 5000.0,
    n_folds: int = 5,
    random_state: int = 42,
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Assign points to spatial grid blocks of side `block_size_m`, partition blocks into `n_folds`,
    and purge any training point within `dead_zone_buffer_m` of any test point in that fold.
    """
    x_min, y_min = coords_m.min(axis=0)
    gx = np.floor((coords_m[:, 0] - x_min) / block_size_m).astype(int)
    gy = np.floor((coords_m[:, 1] - y_min) / block_size_m).astype(int)
    block_ids = gx * 100000 + gy

    unique_blocks = np.unique(block_ids)
    rng = np.random.default_rng(random_state)
    shuffled_blocks = rng.permutation(unique_blocks)
    block_to_fold = {b: (i % n_folds) for i, b in enumerate(shuffled_blocks)}
    point_folds = np.array([block_to_fold[b] for b in block_ids], dtype=int)

    splits: List[Tuple[np.ndarray, np.ndarray]] = []
    for fold in range(n_folds):
        test_idx = np.where(point_folds == fold)[0]
        candidate_train_idx = np.where(point_folds != fold)[0]

        if len(test_idx) == 0 or len(candidate_train_idx) == 0:
            continue

        if dead_zone_buffer_m > 0.0:
            d_mat = cdist(coords_m[candidate_train_idx], coords_m[test_idx])
            min_d_to_test = d_mat.min(axis=1)
            keep_mask = min_d_to_test >= dead_zone_buffer_m
            train_idx = candidate_train_idx[keep_mask]
        else:
            train_idx = candidate_train_idx

        splits.append((train_idx, test_idx))
    return splits


def compute_area_of_applicability(
    X_train: np.ndarray,
    X_query: np.ndarray,
    feature_weights: Optional[np.ndarray] = None,
    cv_train_folds: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Compute Meyer & Pebesma (2021, MEE, doi:10.1111/2041-210X.13650) Dissimilarity Index (DI)
    and binary Area of Applicability (AoA) mask.
    Returns (di_query, aoa_mask, threshold).
    """
    mean = np.nanmean(X_train, axis=0)
    std = np.nanstd(X_train, axis=0) + 1e-8
    Z_tr = (X_train - mean) / std
    Z_qu = (X_query - mean) / std

    if feature_weights is not None:
        w = np.asarray(feature_weights, dtype=np.float64)
        w = w / (np.sum(w) + 1e-8)
        Z_tr = Z_tr * w
        Z_qu = Z_qu * w

    pairwise_tr = pdist(Z_tr)
    d_bar = float(np.mean(pairwise_tr)) if len(pairwise_tr) > 0 else 1.0

    # Distance of each training point to its nearest training neighbour (or out-of-fold neighbour)
    d_tr_mat = cdist(Z_tr, Z_tr)
    np.fill_diagonal(d_tr_mat, np.inf)
    if cv_train_folds is not None:
        same_fold = cv_train_folds[:, None] == cv_train_folds[None, :]
        d_tr_mat[same_fold] = np.inf

    di_tr = d_tr_mat.min(axis=1) / d_bar
    q25, q75 = np.percentile(di_tr, [25, 75])
    iqr = q75 - q25
    threshold = float(q75 + 1.5 * iqr)

    d_qu_min = cdist(Z_qu, Z_tr).min(axis=1)
    di_query = d_qu_min / d_bar
    aoa_mask = di_query <= threshold
    return di_query, aoa_mask, threshold


def compute_recall_and_kvamme_gain_at_k(
    scores: np.ndarray,
    y_true: np.ndarray,
    k_percent_list: Sequence[float] = (1.0, 2.0, 5.0, 10.0),
) -> Dict[str, float]:
    """
    Compute Recall@k% area and Kvamme's Gain G = 1 - (%Area / %Sites)
    for k in k_percent_list.
    """
    scores = np.asarray(scores, dtype=np.float64)
    y_true = np.asarray(y_true, dtype=int)
    n_total = len(scores)
    n_pos = int(np.sum(y_true == 1))
    if n_total == 0 or n_pos == 0:
        return {f"recall_at_{k:g}pct": float("nan") for k in k_percent_list}

    order = np.argsort(-scores)
    y_sorted = y_true[order]

    metrics: Dict[str, float] = {}
    for k_pct in k_percent_list:
        n_top = max(1, int(np.ceil((k_pct / 100.0) * n_total)))
        hits = int(np.sum(y_sorted[:n_top] == 1))
        recall = hits / n_pos
        pct_area = (n_top / n_total) * 100.0
        pct_sites = recall * 100.0
        gain = float(1.0 - (pct_area / pct_sites)) if pct_sites > 0 else -np.inf
        metrics[f"recall_at_{k_pct:g}pct"] = float(recall)
        metrics[f"kvamme_gain_at_{k_pct:g}pct"] = gain
    return metrics


def evaluate_stratified_by_relief_and_modality(
    scores: np.ndarray,
    y_true: np.ndarray,
    relief_class: Sequence[str],
    discovery_modality: Sequence[str],
    k_pct: float = 5.0,
) -> pd.DataFrame:
    """
    Evaluate Recall@k% and Kvamme's Gain stratified separately by mound relief class
    (e.g., 'low_<1m' vs. 'high_>=1.5m') and discovery modality (e.g., 'pedestrian_transect' vs. 'toposheet_symbol').
    Background (y_true == 0) is shared across strata to preserve area threshold definitions.
    """
    scores = np.asarray(scores, dtype=np.float64)
    y_true = np.asarray(y_true, dtype=int)
    relief_arr = np.asarray(relief_class, dtype=str)
    mod_arr = np.asarray(discovery_modality, dtype=str)
    bg_mask = y_true == 0

    rows: List[Dict] = []
    for group_type, arr in [("relief_class", relief_arr), ("discovery_modality", mod_arr)]:
        for val in sorted(set(arr[y_true == 1])):
            pos_stratum = (y_true == 1) & (arr == val)
            subset_mask = bg_mask | pos_stratum
            res = compute_recall_and_kvamme_gain_at_k(scores[subset_mask], y_true[subset_mask], [k_pct])
            rows.append(
                {
                    "stratum_type": group_type,
                    "stratum_value": val,
                    "n_positives": int(np.sum(pos_stratum)),
                    f"recall_at_{k_pct:g}pct": res[f"recall_at_{k_pct:g}pct"],
                    f"kvamme_gain_at_{k_pct:g}pct": res[f"kvamme_gain_at_{k_pct:g}pct"],
                }
            )
    return pd.DataFrame(rows)
