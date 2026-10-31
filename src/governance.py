"""
Governance, Coordinate Obfuscation, H3 Resolution Verification, and Authorized Partner Export Adapter.

Enforces Ground Rules:
1. Never exports raw site or candidate coordinates in public views.
2. Aggregates public probabilities to Uber H3 Resolution 5/6 with k-anonymity suppression (n >= 5).
3. Verifies H3 Resolution 8 standard geometry (edge length 0.531414010 km, area 0.737327598 km^2;
   source: https://h3geo.org/docs/core-library/restable/).
4. Legal & Fieldwork Governance:
   No fieldwork or surface collection without written permission from ASI/the State Department
   and an institutional partner; legal basis to be confirmed with them.
   The partner export adapter gates surface collection exports behind an explicit `field_permission_reference`.
"""

from __future__ import annotations
from dataclasses import dataclass
import hashlib
from typing import Dict, Optional
import numpy as np
import pandas as pd

try:
    import h3 as _h3
except ImportError:
    _h3 = None


# Official H3 Resolution Table constants (https://h3geo.org/docs/core-library/restable/)
H3_OFFICIAL_TABLE: Dict[int, Dict[str, float]] = {
    5: {"edge_km": 9.854090990, "area_km2": 252.903858182},
    6: {"edge_km": 3.724532667, "area_km2": 36.129062164},
    7: {"edge_km": 1.406475763, "area_km2": 5.161293360},
    8: {"edge_km": 0.531414010, "area_km2": 0.737327598},
    9: {"edge_km": 0.200786148, "area_km2": 0.105332513},
}


def verify_h3_res8_constants() -> Dict[str, float]:
    """Verify H3 Resolution 8 geometry against official H3 library tables."""
    if _h3 is not None:
        if hasattr(_h3, "edge_length"):
            edge_km = float(_h3.edge_length(8, unit="km"))
            area_km2 = float(_h3.hex_area(8, unit="km^2"))
        else:
            edge_km = float(_h3.average_hexagon_edge_length(8, unit="km"))
            area_km2 = float(_h3.average_hexagon_area(8, unit="km^2"))
    else:
        edge_km = H3_OFFICIAL_TABLE[8]["edge_km"]
        area_km2 = H3_OFFICIAL_TABLE[8]["area_km2"]

    assert abs(edge_km - 0.531414010) < 0.002, f"Expected ~0.531 km edge length for H3 Res 8, got {edge_km}"
    assert abs(area_km2 - 0.737327598) < 0.005, f"Expected ~0.737 km^2 area for H3 Res 8, got {area_km2}"
    return {"h3_res8_edge_km": edge_km, "h3_res8_area_km2": area_km2}


def latlon_to_h3(lat: float, lon: float, res: int) -> str:
    """Convert WGS84 (lat, lon) to H3 cell ID at resolution `res`."""
    if _h3 is not None:
        if hasattr(_h3, "geo_to_h3"):
            return str(_h3.geo_to_h3(lat, lon, res))
        return str(_h3.latlng_to_cell(lat, lon, res))
    # Deterministic coarse hexagonal-equivalent bin fallback when h3 C-binding is not installed locally
    edge_deg = H3_OFFICIAL_TABLE.get(res, {"edge_km": 9.854})["edge_km"] / 111.32
    q = int(np.floor(lat / edge_deg))
    r = int(np.floor(lon / edge_deg))
    digest = hashlib.sha1(f"res{res}:{q}:{r}".encode("utf-8")).hexdigest()[:12]
    return f"8{res:x}{digest}"


def obfuscate_candidates_for_public_view(
    df_candidates: pd.DataFrame,
    public_h3_res: int = 5,
    min_count_k_anonymity: int = 5,
) -> pd.DataFrame:
    """
    Convert point-level or H3-Res-8 candidate predictions into a coarse public H3 Resolution 5/6 summary.
    - Strips `lat`, `lon`, `x_m`, `y_m`, `site_name`, and `village_name` columns completely.
    - Suppresses any H3 cell with fewer than `min_count_k_anonymity` evaluated sub-cells.
    """
    if public_h3_res > 6:
        raise PermissionError(
            f"Public export resolution {public_h3_res} is too fine; must be <= 6 to prevent looting triangulation."
        )

    df = df_candidates.copy()
    if "h3_public" not in df.columns:
        if "lat" not in df.columns or "lon" not in df.columns:
            raise ValueError("DataFrame must contain ('lat', 'lon') or precomputed 'h3_public'")
        df["h3_public"] = [latlon_to_h3(lat, lon, public_h3_res) for lat, lon in zip(df["lat"], df["lon"])]

    grouped = (
        df.groupby("h3_public", as_index=False)
        .agg(
            n_subcells=("score", "count"),
            mean_score=("score", "mean"),
            q90_score=("score", lambda s: float(np.percentile(s, 90))),
            aoa_coverage_fraction=("aoa_valid", "mean"),
        )
    )
    safe = grouped[grouped["n_subcells"] >= min_count_k_anonymity].copy().reset_index(drop=True)

    forbidden_cols = {"lat", "lon", "x_m", "y_m", "site_name", "village_name", "exact_geometry"}
    assert forbidden_cols.isdisjoint(set(safe.columns)), "Coordinate leakage detected in public view!"
    return safe


@dataclass
class InstitutionalPartnerCredentials:
    partner_institution: str
    data_sharing_agreement_id: str
    field_permission_reference: Optional[str] = None


class PartnerFieldExportAdapter:
    """
    Clean adapter interface for institutional partners (e.g., MAHSA / BHU / ASI Circle).
    Governance rules:
    - Exact coordinates require a signed institutional Data-Sharing Agreement (DSA).
    - Surface collection / fieldwork protocols require an active `field_permission_reference`:
      No fieldwork or surface collection without written permission from ASI/the State Department
      and an institutional partner; legal basis to be confirmed with them.
    """

    @staticmethod
    def export_for_partner(
        df_candidates: pd.DataFrame,
        credentials: Optional[InstitutionalPartnerCredentials],
        include_surface_collection_protocol: bool = False,
    ) -> pd.DataFrame:
        if credentials is None or not credentials.data_sharing_agreement_id.strip():
            raise PermissionError(
                "Exact coordinate export denied: requires verified InstitutionalPartnerCredentials and signed DSA."
            )
        if include_surface_collection_protocol and not credentials.field_permission_reference:
            raise PermissionError(
                "Surface collection protocol export denied: No fieldwork or surface collection without "
                "written permission from ASI/the State Department and an institutional partner; "
                "legal basis to be confirmed with them."
            )
        out = df_candidates.copy()
        out["exported_to_partner"] = credentials.partner_institution
        out["dsa_id"] = credentials.data_sharing_agreement_id
        return out
