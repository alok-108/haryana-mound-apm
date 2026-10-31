"""
Label Curation, Deduplication, Role Assignment, Palimpsest-Safe Target-Group Background (TGB),
and Excavation-Scar Diagnostic Auditing.

Key Design Rules (Phase 2 Revision):
1. Positives for training = ground-confirmed, unexcavated sites ONLY (`is_ground_confirmed == True` and `is_protected_or_excavated == False`).
2. Unverified Survey of India (SOI) map mounds (`is_ground_confirmed == False`) are EXCLUDED from both
   training positives and background sets; they are tracked exclusively as a separate weak-label evaluation set.
3. Protected / excavated sites (`is_protected_or_excavated == True`) are DROPPED from training positives and
   evaluated as a separate diagnostic stratum to verify that models do not cheat on modern fences, sheds, or trenches.
4. Target-Group Background (TGB) excludes co-located multi-period sites within 500 m.
"""

from __future__ import annotations
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Sequence, Tuple
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler


VALID_DISCOVERY_MODALITIES = {
    "pedestrian_transect",
    "toposheet_symbol",
    "satellite_visual",
    "chance_find_construction",
    "legacy_gazetteer",
}

DEFAULT_POSITIONAL_SIGMA_M: Dict[str, float] = {
    "rtk_dgps": 5.0,
    "handheld_gps": 25.0,
    "vhr_verified": 30.0,
    "toposheet_1inch": 90.0,
    "village_centroid": 1200.0,
    "arcmin_rounded": 1850.0,
}


def normalize_toponym(name: str) -> str:
    """Normalize transliteration variants across colonial and modern spellings in Haryana/NW India."""
    if not isinstance(name, str):
        return ""
    s = name.strip().lower()
    for src, dst in [("kheda", "khera"), ("kheri", "khera"), ("theri", "theh"), ("deeh", "dih"), ("kotla", "kot")]:
        s = s.replace(src, dst)
    for ch in ["-", "_", ".", ",", "(", ")", "1", "2", "3", "i", "ii", "iii"]:
        s = s.replace(ch, " ")
    return " ".join(s.split())


def deduplicate_site_inventory(
    df: pd.DataFrame,
    max_spatial_distance_m: float = 350.0,
    min_name_similarity: float = 0.82,
) -> pd.DataFrame:
    """
    Probabilistic spatial + phonetic record linkage across ASI, IAR, MAHSA, and SOI map-mound tables.
    Expects metric coordinates `x_m`, `y_m` (EPSG:32643), `site_name`, `precision_class`,
    `discovery_modality`, `is_ground_confirmed`, and multi-label horizon columns `horizon_*`.
    """
    required = {"site_id", "site_name", "x_m", "y_m", "precision_class", "discovery_modality"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Inventory missing required columns: {missing}")

    df = df.copy().reset_index(drop=True)
    df["sigma_pos_m"] = df["precision_class"].map(DEFAULT_POSITIONAL_SIGMA_M).fillna(1000.0)
    df = df.sort_values("sigma_pos_m", ascending=True).reset_index(drop=True)

    coords = df[["x_m", "y_m"]].to_numpy(dtype=np.float64)
    norm_names = [normalize_toponym(n) for n in df["site_name"]]
    horizon_cols = [c for c in df.columns if c.startswith("horizon_")]

    assigned_cluster = np.full(len(df), -1, dtype=int)
    merged_rows: List[Dict] = []
    cluster_id = 0

    for i in range(len(df)):
        if assigned_cluster[i] != -1:
            continue
        assigned_cluster[i] = cluster_id
        members = [i]

        for j in range(i + 1, len(df)):
            if assigned_cluster[j] != -1:
                continue
            dist_m = float(np.linalg.norm(coords[i] - coords[j]))
            combined_sigma = float(np.hypot(df.loc[i, "sigma_pos_m"], df.loc[j, "sigma_pos_m"]))
            name_sim = SequenceMatcher(None, norm_names[i], norm_names[j]).ratio()

            if dist_m <= max_spatial_distance_m or (dist_m <= 1.5 * combined_sigma and name_sim >= min_name_similarity):
                assigned_cluster[j] = cluster_id
                members.append(j)

        sub = df.iloc[members]
        canonical = sub.iloc[0].to_dict()
        canonical["merged_count"] = len(members)
        canonical["merged_site_ids"] = ";".join(sub["site_id"].astype(str).tolist())
        for h_col in horizon_cols:
            canonical[h_col] = int(sub[h_col].max())
        if "is_ground_confirmed" in sub.columns:
            canonical["is_ground_confirmed"] = bool(sub["is_ground_confirmed"].max())
        if "is_protected_or_excavated" in sub.columns:
            canonical["is_protected_or_excavated"] = bool(sub["is_protected_or_excavated"].max())
        merged_rows.append(canonical)
        cluster_id += 1

    return pd.DataFrame(merged_rows)


def assign_sample_roles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enforce Rule 5 & Rule 7:
    - 'train_positive': confirmed archaeological sites that are NOT protected/excavated.
    - 'eval_protected_positive': confirmed sites with protection/excavation (held out from training).
    - 'unverified_map_mound': unverified historical map symbols (excluded from training positives & background).
    - 'unlabelled_background': background cells not intersecting known or unverified mounds.
    """
    df = df.copy()
    roles = []
    has_y_obs = "y_obs" in df.columns
    for _, row in df.iterrows():
        y = int(row["y_obs"]) if has_y_obs else 1
        confirmed = bool(row.get("is_ground_confirmed", False))
        protected = bool(row.get("is_protected_or_excavated", False))
        modality = str(row.get("discovery_modality", ""))

        if y == 1:
            if confirmed:
                if protected:
                    roles.append("eval_protected_positive")
                else:
                    roles.append("train_positive")
            else:
                roles.append("unverified_map_mound")
        else:
            if modality == "toposheet_symbol" and not confirmed:
                roles.append("unverified_map_mound")
            else:
                roles.append("unlabelled_background")

    df["sample_role"] = roles
    return df


def select_target_group_background(
    sites_df: pd.DataFrame,
    target_horizon_col: str,
    other_horizon_cols: Sequence[str],
    exclude_colocated_buffer_m: float = 500.0,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Select presence records and Target-Group Background (TGB; Phillips et al. 2009, doi:10.1890/07-2153.1)
    for `target_horizon_col` while strictly preventing multi-period palimpsest contamination.
    """
    df = assign_sample_roles(sites_df) if "sample_role" not in sites_df.columns else sites_df.copy()

    # Presences are confirmed, unexcavated sites where target_horizon == 1
    presences = df[
        (df[target_horizon_col] == 1) & (df["sample_role"] == "train_positive")
    ].copy().reset_index(drop=True)

    # TGB pseudo-absences: confirmed sites with target_horizon == 0, known other horizon == 1,
    # and strictly > exclude_colocated_buffer_m from any target_horizon site
    candidates = df[
        (df[target_horizon_col] == 0) & (df["is_ground_confirmed"] == True)
    ].copy()

    if other_horizon_cols:
        has_known_other_horizon = candidates[list(other_horizon_cols)].max(axis=1) > 0
        candidates = candidates[has_known_other_horizon].copy()

    if len(presences) > 0 and len(candidates) > 0:
        p_xy = presences[["x_m", "y_m"]].to_numpy(dtype=np.float64)
        c_xy = candidates[["x_m", "y_m"]].to_numpy(dtype=np.float64)
        min_dist_to_presence = cdist(c_xy, p_xy).min(axis=1)
        candidates = candidates[min_dist_to_presence > exclude_colocated_buffer_m].copy()

    return presences.reset_index(drop=True), candidates.reset_index(drop=True)


def extract_scar_masked_patch_features(
    patch: np.ndarray,
    pixel_size_m: float,
    is_protected_or_excavated: bool,
    inner_exclusion_radius_m: float = 75.0,
    outer_halo_radius_m: float = 250.0,
) -> np.ndarray:
    """
    Extract summary features from a (C, H, W) raster chip.
    If `is_protected_or_excavated` is True, masks out the central [0, inner_exclusion_radius_m]
    zone containing ASI fences, sheds, and excavation trenches, pooling from the unexcavated
    annular agricultural halo [inner_exclusion_radius_m, outer_halo_radius_m].
    """
    if patch.ndim != 3:
        raise ValueError(f"Expected (C, H, W) patch, got shape {patch.shape}")
    c, h, w = patch.shape
    yy, xx = np.ogrid[:h, :w]
    cy, cx = (h - 1) / 2.0, (w - 1) / 2.0
    dist_m = np.hypot(yy - cy, xx - cx) * pixel_size_m

    if is_protected_or_excavated:
        mask = (dist_m >= inner_exclusion_radius_m) & (dist_m <= outer_halo_radius_m)
        if not np.any(mask):
            mask = dist_m >= inner_exclusion_radius_m
    else:
        mask = dist_m <= inner_exclusion_radius_m
        if not np.any(mask):
            mask = np.ones((h, w), dtype=bool)

    pixels = patch[:, mask]
    mean_feat = np.nanmean(pixels, axis=1)
    std_feat = np.nanstd(pixels, axis=1)
    return np.concatenate([mean_feat, std_feat], axis=0)


def run_excavation_scar_leakage_probe(
    X_positives: np.ndarray,
    is_excavated_or_protected: np.ndarray,
    max_allowed_auc: float = 0.60,
    random_state: int = 42,
) -> Dict[str, float | bool]:
    """
    Diagnostic leakage audit:
    Trains an L2-regularised logistic probe on positive site features to test whether
    the feature representation can separate excavated/protected ASI monuments (1)
    from unexcavated agricultural mounds (0).
    If CV ROC-AUC > `max_allowed_auc`, flags an excavation-scar leakage violation.
    """
    y = np.asarray(is_excavated_or_protected, dtype=int)
    if len(np.unique(y)) < 2 or np.min(np.bincount(y)) < 3:
        return {"probe_auc": float("nan"), "passed": True, "n_excavated": int(np.sum(y == 1))}

    n_splits = min(5, int(np.min(np.bincount(y))))
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    oof_preds = np.zeros(len(y), dtype=np.float64)

    for train_idx, test_idx in skf.split(X_positives, y):
        scaler = StandardScaler()
        X_tr = scaler.fit_transform(X_positives[train_idx])
        X_te = scaler.transform(X_positives[test_idx])
        clf = LogisticRegression(C=0.5, max_iter=500, random_state=random_state)
        clf.fit(X_tr, y[train_idx])
        oof_preds[test_idx] = clf.predict_proba(X_te)[:, 1]

    auc = float(roc_auc_score(y, oof_preds))
    return {
        "probe_auc": auc,
        "passed": bool(auc <= max_allowed_auc),
        "n_excavated": int(np.sum(y == 1)),
        "n_unexcavated": int(np.sum(y == 0)),
    }
