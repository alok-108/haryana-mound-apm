"""
Pan-Subcontinent Paleochannel Hydrology & Relict Drainage Architecture.
Models the relict riverine networks across the 6 Macro-Basins of the Indian Subcontinent:
1. Saraswati-Ghaggar-Hakra & Drishadvati (NW India & Cholistan)
2. Upper Indus, Sutlej & Punjab River Interfluves (Doabs)
3. Lower Indus, Eastern Nara & Balochistan Alluvial Fans (Mehrgarh / Kachi)
4. Gujarat Relict Estuaries (Luni, Paleo-Sabarmati, Bhogavo / Lothal)
5. Ganga-Yamuna Doab Relict Meander Belts (Hindon, Kali, Paleo-Ganga)
6. Central India & Northern Deccan Terraces (Banas, Narmada, Pravara)

Uses 3D spherical Cartesian projection for exact great-circle distance queries
across the entire subcontinent without coordinate distortion.
"""

from __future__ import annotations
import math
from typing import Dict, List, Tuple
import numpy as np
from scipy.spatial import cKDTree

EARTH_RADIUS_M = 6371000.0


def latlon_to_cartesian_3d(lat_deg: float | np.ndarray, lon_deg: float | np.ndarray) -> np.ndarray:
    """Convert WGS84 latitude and longitude in degrees to 3D Cartesian coordinates (X, Y, Z) in meters."""
    lat_rad = np.radians(lat_deg)
    lon_rad = np.radians(lon_deg)
    x = EARTH_RADIUS_M * np.cos(lat_rad) * np.cos(lon_rad)
    y = EARTH_RADIUS_M * np.cos(lat_rad) * np.sin(lon_rad)
    z = EARTH_RADIUS_M * np.sin(lat_rad)
    if isinstance(lat_deg, np.ndarray) or isinstance(lon_deg, np.ndarray):
        return np.column_stack([x, y, z])
    return np.array([x, y, z], dtype=np.float64)


def chord_distance_to_arc_distance_m(chord_dist_m: np.ndarray | float) -> np.ndarray | float:
    """Convert 3D Euclidean chord distance to great-circle surface distance in meters."""
    ratio = np.clip(chord_dist_m / (2.0 * EARTH_RADIUS_M), 0.0, 1.0)
    return 2.0 * EARTH_RADIUS_M * np.arcsin(ratio)


# Canonical polyline coordinates of major mapped paleochannels across the Subcontinent (lon, lat)
SUBCONTINENT_PALEOCHANNELS: Dict[str, Dict[str, object]] = {
    # 1. Saraswati-Ghaggar-Hakra Basin
    "saraswati_ghaggar_trunk": {
        "basin_id": "ghaggar_hakra_saraswati",
        "name": "Saraswati-Ghaggar-Hakra Relict Riverbed",
        "polyline": [
            (77.30, 30.45),  # Adi Badri / Shivalik foothills
            (76.85, 30.35),  # Pinjore / Ambala
            (76.50, 30.15),  # Pehowa
            (76.10, 29.95),  # Shatrana
            (75.70, 29.80),  # Tohana
            (75.35, 29.65),  # Banawali
            (75.05, 29.55),  # Sirsa
            (74.70, 29.45),  # Ellenabad
            (74.30, 29.58),  # Hanumangarh / Kalibangan
            (73.80, 29.35),  # Suratgarh
            (73.20, 29.15),  # Anupgarh
            (72.60, 28.95),  # Fort Abbas (Pakistan)
            (71.85, 28.58),  # Derawar Fort / Kudwala
            (71.12, 28.30),  # Ganweriwala Depression
        ],
    },
    "drishadvati_chautang_trunk": {
        "basin_id": "ghaggar_hakra_saraswati",
        "name": "Relict Drishadvati / Chautang Riverbed",
        "polyline": [
            (77.10, 30.15),  # Shivalik exit near Yamunanagar
            (76.75, 29.75),  # Kaithal south
            (76.35, 29.45),  # Jind
            (76.08, 29.30),  # Narnaund / Rakhigarhi
            (75.95, 29.10),  # Hansi
            (75.50, 29.15),  # Siswal
            (75.15, 29.10),  # Bhadra
            (74.75, 29.05),  # Nohar
            (74.35, 29.15),  # Rawatsar junction with Hakra
        ],
    },
    "naiwal_relict_channels": {
        "basin_id": "ghaggar_hakra_saraswati",
        "name": "Naiwal Relict Braided Channels",
        "polyline": [
            (75.60, 30.10),  # Patiala south
            (75.25, 29.95),  # Sunam
            (74.95, 29.80),  # Bhatinda south
            (74.55, 29.60),  # Rania / Sirsa west
        ],
    },
    # 2. Upper Indus & Punjab Basin
    "paleo_sutlej_diversion": {
        "basin_id": "upper_indus_punjab",
        "name": "Paleo-Sutlej Migration Channel (Pre-Capture)",
        "polyline": [
            (76.53, 30.97),  # Ropar
            (76.10, 30.80),  # Khanna south
            (75.60, 30.60),  # Nabha
            (75.10, 30.35),  # Barnala south
            (74.60, 30.10),  # Muktsar
            (74.10, 29.85),  # Fazilka
        ],
    },
    "paleo_ravi_interfluve": {
        "basin_id": "upper_indus_punjab",
        "name": "Paleo-Ravi Harappan Meander Belt",
        "polyline": [
            (74.85, 31.80),  # Gurdaspur / Batala
            (74.35, 31.55),  # Lahore north
            (73.65, 31.20),  # Balloki
            (72.87, 30.63),  # Harappa ancient oxbow
            (72.20, 30.35),  # Chichawatni / Mian Channu
            (71.80, 30.15),  # Khanewal
        ],
    },
    # 3. Lower Indus, Sindh & Balochistan Basin
    "eastern_nara_hakra_trunk": {
        "basin_id": "lower_indus_sindh_balochistan",
        "name": "Eastern Nara / Hakra Southern Outlet",
        "polyline": [
            (69.25, 28.00),  # Ghotki east
            (69.05, 27.60),  # Rohri east / Khairpur
            (68.95, 26.85),  # Kot Diji east
            (69.30, 25.55),  # Sanghar / Khipro east
            (69.45, 25.10),  # Mirpur Khas east
            (69.80, 24.50),  # Umarkot / Great Rann northern delta
        ],
    },
    "lower_indus_western_paleomeander": {
        "basin_id": "lower_indus_sindh_balochistan",
        "name": "Lower Indus Relict Western Oxbow & Meander",
        "polyline": [
            (68.55, 27.80),  # Shikarpur south
            (68.25, 27.55),  # Larkana
            (68.14, 27.33),  # Mohenjo-daro ancient channel
            (68.05, 27.08),  # Mehar / Dadu north
            (67.95, 26.70),  # Sehwan / Lake Manchar
        ],
    },
    "bolan_alluvial_fan_paleo": {
        "basin_id": "lower_indus_sindh_balochistan",
        "name": "Bolan River Relict Alluvial Fan (Kachi Plain)",
        "polyline": [
            (67.75, 29.60),  # Bolan Pass gorge
            (68.09, 29.39),  # Mehrgarh proto-alluvial terrace
            (68.22, 29.31),  # Sibi / Nausharo fan
            (68.50, 28.80),  # Jacobabad north
        ],
    },
    "porali_lasbela_paleochannel": {
        "basin_id": "lower_indus_sindh_balochistan",
        "name": "Porali Relict Riverine Corridor (Lasbela Plain)",
        "polyline": [
            (66.45, 26.30),  # Bela north
            (66.58, 25.72),  # Uthal / Lasbela
            (66.72, 25.48),  # Balakot ancient estuary
            (66.75, 25.20),  # Sonmiani Bay mouth
        ],
    },
    # 4. Gujarat, Kutch & Saurashtra Basin
    "paleo_luni_kutch_embayment": {
        "basin_id": "gujarat_kutch_saurashtra",
        "name": "Paleo-Luni & Great Rann Maritime Inflow",
        "polyline": [
            (71.50, 24.75),  # Sanchor (Rajasthan/Gujarat border)
            (71.30, 24.52),  # Tharad north
            (70.65, 24.05),  # Great Rann northern shore
            (70.52, 23.95),  # Bela Bet / Khadir margin
            (70.22, 23.89),  # Khadir Island / Dholavira embayment
            (69.60, 23.75),  # Pachham Island west
        ],
    },
    "paleo_bhogavo_sabarmati_lothal": {
        "basin_id": "gujarat_kutch_saurashtra",
        "name": "Paleo-Bhogavo & Sabarmati Lothal Estuary",
        "polyline": [
            (71.85, 22.85),  # Surendranagar
            (72.05, 22.70),  # Limbdi
            (72.25, 22.52),  # Lothal ancient dockyard estuary
            (72.45, 22.35),  # Dholka south
            (72.60, 22.10),  # Gulf of Khambhat mouth
        ],
    },
    "bhadar_saurashtra_paleochannel": {
        "basin_id": "gujarat_kutch_saurashtra",
        "name": "Bhadar Relict Riverine Corridor (Central Saurashtra)",
        "polyline": [
            (71.45, 22.15),  # Jasdan
            (71.21, 22.01),  # Gondal south
            (70.92, 21.87),  # Rojdi ancient riverbend
            (70.40, 21.65),  # Dhoraji
            (69.80, 21.60),  # Navibandar mouth
        ],
    },
    # 5. Ganga-Yamuna Doab & Middle Ganga Basin
    "paleo_yamuna_hindon_scrolls": {
        "basin_id": "ganga_yamuna_doab",
        "name": "Paleo-Yamuna & Hindon Meander System",
        "polyline": [
            (77.55, 30.30),  # Paonta / Hathnikund
            (77.40, 29.85),  # Saharanpur / Bargaon
            (77.30, 29.45),  # Shamli
            (77.21, 29.14),  # Sinauli / Baghpat
            (77.25, 28.70),  # Delhi / Loni
            (77.45, 28.40),  # Greater Noida / Dankaur
        ],
    },
    "kali_nadi_upper_ganga_scrolls": {
        "basin_id": "ganga_yamuna_doab",
        "name": "Kali Nadi & Upper Ganga Oxbow Belt",
        "polyline": [
            (77.75, 29.50),  # Muzaffarnagar / Mandi
            (77.85, 29.20),  # Meerut
            (77.99, 29.17),  # Hastinapur ancient river bend
            (78.35, 28.75),  # Bulandshahr / Anupshahr
            (78.68, 27.70),  # Atranjikhera / Etah
            (79.28, 27.62),  # Kampil / Farrukhabad
            (81.38, 25.33),  # Kausambi / Prayagraj confluence
        ],
    },
    # 6. Central India & Northern Deccan Basin
    "banas_relict_terraces": {
        "basin_id": "central_india_deccan",
        "name": "Banas River Relict Terraces (Ahar Culture Core)",
        "polyline": [
            (73.72, 24.58),  # Ahar / Udaipur valley
            (74.25, 25.02),  # Gilund
            (74.48, 25.21),  # Bhilwara south
            (74.65, 25.35),  # Mandal
            (75.30, 25.80),  # Tonk / Banasthali
        ],
    },
    "berach_relict_terraces": {
        "basin_id": "central_india_deccan",
        "name": "Berach River Relict Terraces (Mewar Southern Flank)",
        "polyline": [
            (73.75, 24.60),  # Udaipur east
            (73.98, 24.72),  # Balathal
            (74.12, 24.62),  # Vallabhnagar south
            (74.45, 24.85),  # Kapasan
            (74.62, 24.88),  # Chittorgarh confluence
        ],
    },
    "paleo_narmada_chambal_terraces": {
        "basin_id": "central_india_deccan",
        "name": "Narmada & Chambal Malwa Riverine Terraces",
        "polyline": [
            (75.40, 23.45),  # Nagda (Chambal)
            (75.82, 23.28),  # Tarana / Choti Kali Sindh
            (76.02, 23.13),  # Kayatha
            (75.80, 22.70),  # Indore south
            (75.58, 22.18),  # Maheshwar / Navdatoli (Narmada)
            (75.41, 22.12),  # Kasrawad / Narmada south bank
            (74.90, 22.05),  # Barwani (Lower Narmada)
        ],
    },
    "pravara_godavari_jorwe_terraces": {
        "basin_id": "central_india_deccan",
        "name": "Pravara-Godavari Jorwe Fluvial Belt",
        "polyline": [
            (74.35, 19.65),  # Sangamner
            (74.51, 19.58),  # Sangamner east
            (74.68, 19.52),  # Daimabad ancient levee
            (74.92, 19.55),  # Nevasa / Pravara-Godavari confluence
        ],
    },
    "ghod_river_jorwe_terraces": {
        "basin_id": "central_india_deccan",
        "name": "Ghod River Relict Terraces (Inamgaon Zone)",
        "polyline": [
            (74.10, 18.90),  # Khed
            (74.38, 18.71),  # Shirur west
            (74.52, 18.60),  # Inamgaon ancient terrace
            (74.80, 18.45),  # Daund confluence with Bhima
        ],
    },
}


class SubcontinentPaleochannelModel:
    """
    Computes exact spherical distances to mapped paleochannels across the entire Indian Subcontinent
    and evaluates fluvial settlement likelihood priors for Pre-600 BCE archaeological discovery.
    """

    def __init__(self, densify_step_m: float = 1000.0) -> None:
        self.densify_step_m = densify_step_m
        self.all_sample_points_3d: List[np.ndarray] = []
        self.sample_metadata: List[Tuple[str, str, str]] = []  # (channel_id, channel_name, basin_id)

        # Densify all polylines on the sphere
        for ch_id, ch_data in SUBCONTINENT_PALEOCHANNELS.items():
            polyline = ch_data["polyline"]
            ch_name = str(ch_data["name"])
            basin_id = str(ch_data["basin_id"])

            for i in range(len(polyline) - 1):
                lon1, lat1 = polyline[i]
                lon2, lat2 = polyline[i + 1]

                p1_3d = latlon_to_cartesian_3d(lat1, lon1)
                p2_3d = latlon_to_cartesian_3d(lat2, lon2)

                chord_len = float(np.linalg.norm(p2_3d - p1_3d))
                arc_len = float(chord_distance_to_arc_distance_m(chord_len))
                n_steps = max(1, int(arc_len / densify_step_m))

                for s in range(n_steps + 1):
                    # Linear chord interpolation, normalized to Earth surface
                    pt_3d = p1_3d + (p2_3d - p1_3d) * (s / n_steps)
                    pt_3d_norm = pt_3d * (EARTH_RADIUS_M / np.linalg.norm(pt_3d))
                    self.all_sample_points_3d.append(pt_3d_norm)
                    self.sample_metadata.append((ch_id, ch_name, basin_id))

        self.kd_tree_3d = cKDTree(np.array(self.all_sample_points_3d, dtype=np.float64))

    def query_nearest_paleochannel(
        self, lat: float, lon: float
    ) -> Tuple[float, str, str, str]:
        """
        Query nearest paleochannel from query coordinate (lat, lon in degrees).
        Returns: (distance_km, nearest_channel_id, nearest_channel_name, basin_id).
        """
        q_3d = latlon_to_cartesian_3d(lat, lon)
        chord_dist, idx = self.kd_tree_3d.query(q_3d, k=1)
        arc_dist_m = float(chord_distance_to_arc_distance_m(chord_dist))
        dist_km = arc_dist_m / 1000.0
        ch_id, ch_name, b_id = self.sample_metadata[idx]
        return dist_km, ch_id, ch_name, b_id

    def compute_fluvial_prior_score(
        self,
        dist_km: float,
        sigma_fluvial_km: float = 3.5,
        min_prior: float = 0.05,
    ) -> float:
        """
        Evaluate Gaussian-decay fluvial settlement likelihood prior:
        Pre-600 BCE agricultural communities required perennial water and fertile silt.
        """
        decay = math.exp(-0.5 * (dist_km / sigma_fluvial_km) ** 2)
        return float(np.clip(decay, min_prior, 1.0))
