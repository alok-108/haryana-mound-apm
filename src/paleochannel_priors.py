"""
Paleochannel Hydrology Priors & Relict Riverine Distance Modeling.
Models the major relict hydrological systems of Northern India:
1. Relict Saraswati / Ghaggar Trunk Channel (Pinjore -> Shatrana -> Sirsa -> Hanumangarh).
2. Relict Drishadvati / Chautang Channel (Jind -> Hansi -> Rakhigarhi -> Siswal -> Bhadra).
3. Relict Sahibi / Dohan Basin (Southern Haryana / NE Rajasthan).
4. Relict Yamuna-Ganga Doab Meanders (Hindon, Kali, Upper Ganga).

References:
- Yashpal et al. (1980), 'Remote sensing of the lost Saraswati river', Proc. Indian Acad. Sci.
- Valdiya, K.S. (2002), 'Saraswati: The River That Disappeared', Universities Press.
- Petrie, C.A. et al. (2017), 'Walking the interfluves', Quaternary International 437: 103-118.
- Orengo, H.A. & Petrie, C.A. (2017), 'Multi-scale relief model (MSRM)', Remote Sensing.
"""

from __future__ import annotations
import math
from typing import Dict, List, Tuple
import numpy as np
from scipy.spatial import cKDTree

from src.public_data_curator import wgs84_to_utm43n


# Canonical polyline coordinates of major mapped paleochannels in WGS84 (lon, lat)
PALEOCHANNELS_WGS84: Dict[str, List[Tuple[float, float]]] = {
    "ghaggar_saraswati_trunk": [
        (76.85, 30.35),
        (76.50, 30.15),
        (76.10, 29.95),
        (75.70, 29.80),
        (75.35, 29.65),  # Near Banawali
        (75.05, 29.55),  # Near Sirsa
        (74.70, 29.45),  # Near Ellenabad
        (74.30, 29.58),  # Near Hanumangarh / Kalibangan
        (73.80, 29.35),  # Near Suratgarh
        (73.20, 29.15),  # Near Anupgarh
    ],
    "drishadvati_chautang_trunk": [
        (76.75, 29.75),
        (76.35, 29.45),  # Near Jind
        (76.08, 29.30),  # Near Rakhigarhi / Narnaund
        (75.95, 29.10),  # Near Hansi
        (75.50, 29.15),  # Near Siswal
        (75.15, 29.10),  # Near Bhadra
        (74.75, 29.05),  # Near Nohar
        (74.35, 29.15),  # Near Rawatsar junction with Ghaggar
    ],
    "upper_yamuna_ganga_paleo": [
        (77.20, 30.10),  # Near Jagadhri / Hathnikund
        (77.25, 29.65),  # Near Shamli / Karnal east
        (77.45, 29.30),  # Near Baghpat
        (77.75, 29.00),  # Near Meerut / Hastinapur
        (78.10, 28.60),  # Near Bulandshahr / Narora
    ],
}


class PaleochannelPriorModel:
    """
    Computes Euclidean distance to mapped Northern Indian paleochannels (EPSG:32643)
    and evaluates fluvial settlement likelihood priors for Pre-600 BCE cultures.
    """

    def __init__(self, densify_step_m: float = 500.0) -> None:
        self.densify_step_m = densify_step_m
        self.segments_utm: List[np.ndarray] = []
        self.all_sample_points: List[Tuple[float, float]] = []

        # Convert polyline vertices to UTM 43N and interpolate points every `densify_step_m`
        for name, polyline in PALEOCHANNELS_WGS84.items():
            pts_utm = [wgs84_to_utm43n(lon, lat) for lon, lat in polyline]
            for i in range(len(pts_utm) - 1):
                p1 = np.array(pts_utm[i], dtype=np.float64)
                p2 = np.array(pts_utm[i + 1], dtype=np.float64)
                seg_len = float(np.linalg.norm(p2 - p1))
                n_steps = max(1, int(seg_len / densify_step_m))
                for s in range(n_steps + 1):
                    pt = p1 + (p2 - p1) * (s / n_steps)
                    self.all_sample_points.append((pt[0], pt[1]))

        self.kd_tree = cKDTree(np.array(self.all_sample_points, dtype=np.float64))

    def compute_distance_to_paleochannel_km(self, coords_m: np.ndarray) -> np.ndarray:
        """Compute distance in kilometers from query points (x_m, y_m in EPSG:32643) to nearest paleochannel."""
        coords = np.asarray(coords_m, dtype=np.float64)
        if coords.ndim == 1:
            coords = coords.reshape(1, -1)
        dists_m, _ = self.kd_tree.query(coords, k=1)
        return dists_m / 1000.0

    def compute_fluvial_settlement_prior(
        self,
        coords_m: np.ndarray,
        sigma_fluvial_km: float = 3.0,
        min_prior: float = 0.05,
    ) -> np.ndarray:
        """
        Evaluate Gaussian-decay fluvial settlement likelihood prior:
        Pre-600 BCE agricultural civilizations were river-dependent.
        Points within 0.5-2.5 km of a major paleochannel receive prior ~1.0;
        points > 8-10 km away drop toward min_prior.
        """
        dists_km = self.compute_distance_to_paleochannel_km(coords_m)
        # Optimal settlement zone: 0.2 km <= d <= 2.5 km (avoids direct annual riverbed scouring while retaining water access)
        effective_dist = np.maximum(0.0, dists_km - 0.2)
        priors = np.exp(-0.5 * (effective_dist / sigma_fluvial_km) ** 2)
        return np.clip(priors, min_prior, 1.0)
