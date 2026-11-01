"""
Public Archaeological Data Curator for Haryana Ghaggar-Hakra / Chautang Interfluve.
Districts: Hisar, Fatehabad, Sirsa.

Provides open, published archaeological ground-truth site records harvested from:
1. Archaeological Survey of India (ASI) Centrally Protected Monuments.
2. Haryana State Directorate of Archaeology and Museums State Protected Sites.
3. Published archaeological excavation monographs & survey gazetteers:
   - Suraj Bhan (1975), 'Excavation at Mitathal (1968) and other Explorations in the Sutlej-Yamuna Divide'.
   - Possehl (1999), 'Indus Age: The Beginnings'.
   - Joshi, Bala & Jammwal (1984), 'Exploration in Gujarat, Haryana and Punjab', Puratattva.
   - Petrie et al. (2017), 'Walking the interfluves', Quaternary International.
   - Singh et al. (2018), 'Survey and excavations at Lohari Ragho', Puratattva.
   - Green et al. (2019), Journal of Field Archaeology.
4. Historical 1-inch Survey of India (SOI) map-mound features (unverified weak labels).
"""

from __future__ import annotations
import math
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd


def wgs84_to_utm43n(lon_deg: float, lat_deg: float) -> Tuple[float, float]:
    """
    Exact Transverse Mercator projection from WGS84 (lon, lat) to UTM Zone 43N (EPSG:32643).
    Central Meridian = 75.0 deg E, Scale Factor k0 = 0.9996, False Easting = 500,000 m.
    """
    a = 6378137.0
    f = 1.0 / 298.257223563
    e2 = 2.0 * f - f * f
    e_prime2 = e2 / (1.0 - e2)
    k0 = 0.9996
    lon0 = math.radians(75.0)

    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)

    N = a / math.sqrt(1.0 - e2 * math.sin(lat) ** 2)
    T = math.tan(lat) ** 2
    C = e_prime2 * math.cos(lat) ** 2
    A = (lon - lon0) * math.cos(lat)

    M = a * (
        (1.0 - e2 / 4.0 - 3.0 * e2**2 / 64.0 - 5.0 * e2**3 / 256.0) * lat
        - (3.0 * e2 / 8.0 + 3.0 * e2**2 / 32.0 + 45.0 * e2**3 / 1024.0) * math.sin(2.0 * lat)
        + (15.0 * e2**2 / 256.0 + 45.0 * e2**3 / 1024.0) * math.sin(4.0 * lat)
        - (35.0 * e2**3 / 3072.0) * math.sin(6.0 * lat)
    )

    x = (
        k0
        * N
        * (
            A
            + (1.0 - T + C) * A**3 / 6.0
            + (5.0 - 18.0 * T + T**2 + 72.0 * C - 58.0 * e_prime2) * A**5 / 120.0
        )
        + 500000.0
    )
    y = k0 * (
        M
        + N
        * math.tan(lat)
        * (
            A**2 / 2.0
            + (5.0 - T + 9.0 * C + 4.0 * C**2) * A**4 / 24.0
            + (61.0 - 58.0 * T + T**2 + 600.0 * C - 330.0 * e_prime2) * A**6 / 720.0
        )
    )
    return float(x), float(y)


# Canonical published ground-truth archaeological sites in Hisar, Fatehabad, Sirsa (and immediate border)
PUBLISHED_GROUND_TRUTH_SITES: List[Dict] = [
    {
        "site_id": "HAR_HSR_001",
        "site_name": "Rakhigarhi (Mound RGR-1)",
        "district": "Hisar",
        "tehsil": "Narnaund",
        "longitude": 76.0685,
        "latitude": 29.2882,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": True,
        "relief_class": "prominent_mound",
        "estimated_height_m": 16.5,
        "horizon_harappan": 1,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "rtk_dgps",
        "source_citation": "ASI Centrally Protected Monument; Nath et al. 2014; Shinde et al. 2018",
    },
    {
        "site_id": "HAR_HSR_002",
        "site_name": "Rakhigarhi (Mound RGR-4)",
        "district": "Hisar",
        "tehsil": "Narnaund",
        "longitude": 76.0620,
        "latitude": 29.2930,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": True,
        "relief_class": "prominent_mound",
        "estimated_height_m": 14.0,
        "horizon_harappan": 1,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "rtk_dgps",
        "source_citation": "ASI Centrally Protected Monument; Nath et al. 2014",
    },
    {
        "site_id": "HAR_HSR_003",
        "site_name": "Rakhigarhi (Mound RGR-6 Early Harappan)",
        "district": "Hisar",
        "tehsil": "Narnaund",
        "longitude": 76.0740,
        "latitude": 29.2820,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": True,
        "relief_class": "medium_mound",
        "estimated_height_m": 3.8,
        "horizon_harappan": 1,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "rtk_dgps",
        "source_citation": "ASI Centrally Protected Monument; Shinde et al. 2018",
    },
    {
        "site_id": "HAR_HSR_004",
        "site_name": "Agroha Mound (Agroha Dham)",
        "district": "Hisar",
        "tehsil": "Agroha",
        "longitude": 75.6144,
        "latitude": 29.3308,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": True,
        "relief_class": "prominent_mound",
        "estimated_height_m": 15.0,
        "horizon_harappan": 0,
        "horizon_pgw": 1,
        "horizon_early_historic": 1,
        "horizon_medieval": 1,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "vhr_verified",
        "source_citation": "Haryana State Protected Monument; Srivastava 1980; ASI",
    },
    {
        "site_id": "HAR_HSR_005",
        "site_name": "Hansi Asigarh Fort Mound",
        "district": "Hisar",
        "tehsil": "Hansi",
        "longitude": 75.9642,
        "latitude": 29.1025,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": True,
        "relief_class": "prominent_mound",
        "estimated_height_m": 16.0,
        "horizon_harappan": 0,
        "horizon_pgw": 1,
        "horizon_early_historic": 1,
        "horizon_medieval": 1,
        "discovery_modality": "legacy_gazetteer",
        "precision_class": "vhr_verified",
        "source_citation": "ASI Centrally Protected Monument; Cunningham 1872; IAR 2004-05",
    },
    {
        "site_id": "HAR_HSR_006",
        "site_name": "Siswal Ancient Mound",
        "district": "Hisar",
        "tehsil": "Hisar",
        "longitude": 75.5042,
        "latitude": 29.1708,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": False,
        "relief_class": "medium_mound",
        "estimated_height_m": 2.5,
        "horizon_harappan": 1,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "handheld_gps",
        "source_citation": "Suraj Bhan 1971/1975; Possehl 1999 (Siswal Type Site)",
    },
    {
        "site_id": "HAR_HSR_007",
        "site_name": "Lohari Ragho I",
        "district": "Hisar",
        "tehsil": "Narnaund",
        "longitude": 76.0380,
        "latitude": 29.3450,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": False,
        "relief_class": "medium_mound",
        "estimated_height_m": 2.2,
        "horizon_harappan": 1,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "handheld_gps",
        "source_citation": "Singh et al. 2018 (Puratattva 48); Petrie et al. 2017",
    },
    {
        "site_id": "HAR_HSR_008",
        "site_name": "Lohari Ragho II",
        "district": "Hisar",
        "tehsil": "Narnaund",
        "longitude": 76.0460,
        "latitude": 29.3510,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": False,
        "relief_class": "low_relief_mound",
        "estimated_height_m": 0.8,
        "horizon_harappan": 1,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "handheld_gps",
        "source_citation": "Singh et al. 2018; Petrie et al. 2017",
    },
    {
        "site_id": "HAR_HSR_009",
        "site_name": "Masudpur I",
        "district": "Hisar",
        "tehsil": "Hansi",
        "longitude": 76.1280,
        "latitude": 29.2290,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": False,
        "relief_class": "medium_mound",
        "estimated_height_m": 1.4,
        "horizon_harappan": 1,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "handheld_gps",
        "source_citation": "Petrie et al. 2017; Green et al. 2019",
    },
    {
        "site_id": "HAR_HSR_010",
        "site_name": "Masudpur VII",
        "district": "Hisar",
        "tehsil": "Hansi",
        "longitude": 76.1370,
        "latitude": 29.2380,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": False,
        "relief_class": "low_relief_mound",
        "estimated_height_m": 0.6,
        "horizon_harappan": 1,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "handheld_gps",
        "source_citation": "Petrie et al. 2017; Green et al. 2019",
    },
    {
        "site_id": "HAR_HSR_011",
        "site_name": "Barwala Ancient Mound",
        "district": "Hisar",
        "tehsil": "Barwala",
        "longitude": 75.9083,
        "latitude": 29.3789,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": False,
        "relief_class": "prominent_mound",
        "estimated_height_m": 8.0,
        "horizon_harappan": 0,
        "horizon_pgw": 1,
        "horizon_early_historic": 1,
        "horizon_medieval": 0,
        "discovery_modality": "legacy_gazetteer",
        "precision_class": "vhr_verified",
        "source_citation": "HL Srivastava 1937-38; Agreya Coins Discovery; Suraj Bhan 1975",
    },
    {
        "site_id": "HAR_HSR_012",
        "site_name": "Salimpur Mound",
        "district": "Hisar",
        "tehsil": "Hisar",
        "longitude": 75.7890,
        "latitude": 29.1350,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": False,
        "relief_class": "low_relief_mound",
        "estimated_height_m": 0.7,
        "horizon_harappan": 0,
        "horizon_pgw": 1,
        "horizon_early_historic": 1,
        "horizon_medieval": 0,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "handheld_gps",
        "source_citation": "Suraj Bhan 1975; Possehl 1999",
    },
    # Fatehabad District Sites
    {
        "site_id": "HAR_FTB_001",
        "site_name": "Banawali Harappan Citadel Mound",
        "district": "Fatehabad",
        "tehsil": "Fatehabad",
        "longitude": 75.2347,
        "latitude": 29.6264,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": True,
        "relief_class": "prominent_mound",
        "estimated_height_m": 10.5,
        "horizon_harappan": 1,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "rtk_dgps",
        "source_citation": "ASI Centrally Protected Monument; RS Bisht 1982/1987",
    },
    {
        "site_id": "HAR_FTB_002",
        "site_name": "Kunal Early Harappan Mound",
        "district": "Fatehabad",
        "tehsil": "Ratia",
        "longitude": 75.6583,
        "latitude": 29.6167,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": True,
        "relief_class": "medium_mound",
        "estimated_height_m": 3.5,
        "horizon_harappan": 1,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "rtk_dgps",
        "source_citation": "Haryana State Protected Monument; Khatri & Acharya 1995; Acharya 2017",
    },
    {
        "site_id": "HAR_FTB_003",
        "site_name": "Bhirrana Saraswati Valley Mound",
        "district": "Fatehabad",
        "tehsil": "Fatehabad",
        "longitude": 75.5583,
        "latitude": 29.5500,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": True,
        "relief_class": "prominent_mound",
        "estimated_height_m": 5.2,
        "horizon_harappan": 1,
        "horizon_pgw": 1,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "rtk_dgps",
        "source_citation": "ASI Excavation Site; LS Rao et al. 2005; Sarkar et al. 2016",
    },
    {
        "site_id": "HAR_FTB_004",
        "site_name": "Bhatu Kalan Mound",
        "district": "Fatehabad",
        "tehsil": "Bhatu Kalan",
        "longitude": 75.3340,
        "latitude": 29.4120,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": False,
        "relief_class": "low_relief_mound",
        "estimated_height_m": 0.9,
        "horizon_harappan": 1,
        "horizon_pgw": 1,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "handheld_gps",
        "source_citation": "Joshi et al. 1984; Suraj Bhan 1975",
    },
    {
        "site_id": "HAR_FTB_005",
        "site_name": "Kajal Heri Ancient Mound",
        "district": "Fatehabad",
        "tehsil": "Fatehabad",
        "longitude": 75.4850,
        "latitude": 29.4950,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": False,
        "relief_class": "medium_mound",
        "estimated_height_m": 1.8,
        "horizon_harappan": 1,
        "horizon_pgw": 1,
        "horizon_early_historic": 1,
        "horizon_medieval": 0,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "handheld_gps",
        "source_citation": "Petrie et al. 2017; Suraj Bhan 1975",
    },
    {
        "site_id": "HAR_FTB_006",
        "site_name": "Dhangar Harappan Mound",
        "district": "Fatehabad",
        "tehsil": "Fatehabad",
        "longitude": 75.5230,
        "latitude": 29.5890,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": False,
        "relief_class": "low_relief_mound",
        "estimated_height_m": 0.85,
        "horizon_harappan": 1,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "handheld_gps",
        "source_citation": "Possehl 1999; Joshi et al. 1984",
    },
    # Sirsa District Sites
    {
        "site_id": "HAR_SRS_001",
        "site_name": "Ther Mound (Sirsa Stupa / Ancient Sarsuti)",
        "district": "Sirsa",
        "tehsil": "Sirsa",
        "longitude": 75.0286,
        "latitude": 29.5350,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": True,
        "relief_class": "prominent_mound",
        "estimated_height_m": 13.0,
        "horizon_harappan": 1,
        "horizon_pgw": 1,
        "horizon_early_historic": 1,
        "horizon_medieval": 1,
        "discovery_modality": "legacy_gazetteer",
        "precision_class": "vhr_verified",
        "source_citation": "ASI Centrally Protected Monument; Cunningham 1882; Suraj Bhan 1975",
    },
    {
        "site_id": "HAR_SRS_002",
        "site_name": "Sikanderpur Mound",
        "district": "Sirsa",
        "tehsil": "Sirsa",
        "longitude": 75.1120,
        "latitude": 29.5840,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": False,
        "relief_class": "medium_mound",
        "estimated_height_m": 2.8,
        "horizon_harappan": 0,
        "horizon_pgw": 1,
        "horizon_early_historic": 1,
        "horizon_medieval": 1,
        "discovery_modality": "legacy_gazetteer",
        "precision_class": "handheld_gps",
        "source_citation": "Suraj Bhan 1975; Possehl 1999",
    },
    {
        "site_id": "HAR_SRS_003",
        "site_name": "Rania Fort Mound",
        "district": "Sirsa",
        "tehsil": "Rania",
        "longitude": 74.8360,
        "latitude": 29.5260,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": False,
        "relief_class": "prominent_mound",
        "estimated_height_m": 6.5,
        "horizon_harappan": 0,
        "horizon_pgw": 1,
        "horizon_early_historic": 1,
        "horizon_medieval": 1,
        "discovery_modality": "legacy_gazetteer",
        "precision_class": "vhr_verified",
        "source_citation": "Imperial Gazetteer of India 1908; Suraj Bhan 1975",
    },
    {
        "site_id": "HAR_SRS_004",
        "site_name": "Jamal Ancient Mound",
        "district": "Sirsa",
        "tehsil": "Chopta",
        "longitude": 74.9620,
        "latitude": 29.3140,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": False,
        "relief_class": "low_relief_mound",
        "estimated_height_m": 0.95,
        "horizon_harappan": 1,
        "horizon_pgw": 1,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "pedestrian_transect",
        "precision_class": "handheld_gps",
        "source_citation": "Joshi et al. 1984; Possehl 1999",
    },
    {
        "site_id": "HAR_SRS_005",
        "site_name": "Ellenabad Ghaggar Terrace Mound",
        "district": "Sirsa",
        "tehsil": "Ellenabad",
        "longitude": 74.6580,
        "latitude": 29.4520,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": False,
        "relief_class": "medium_mound",
        "estimated_height_m": 2.1,
        "horizon_harappan": 1,
        "horizon_pgw": 0,
        "horizon_early_historic": 1,
        "horizon_medieval": 0,
        "discovery_modality": "chance_find_construction",
        "precision_class": "handheld_gps",
        "source_citation": "Suraj Bhan 1975; Possehl 1999",
    },
    {
        "site_id": "HAR_SRS_006",
        "site_name": "Badopal Kushan Stupa Mound",
        "district": "Sirsa",
        "tehsil": "Sirsa-Border",
        "longitude": 74.9120,
        "latitude": 29.4890,
        "is_ground_confirmed": True,
        "is_protected_or_excavated": False,
        "relief_class": "prominent_mound",
        "estimated_height_m": 4.5,
        "horizon_harappan": 0,
        "horizon_pgw": 0,
        "horizon_early_historic": 1,
        "horizon_medieval": 0,
        "discovery_modality": "chance_find_construction",
        "precision_class": "vhr_verified",
        "source_citation": "Tessitori 1917; ASI Annual Report 1917-18; Suraj Bhan 1975",
    },
]


# Unverified historical Survey of India (SOI) map mounds (weak-label stratum)
HISTORICAL_UNVERIFIED_MAP_MOUNDS: List[Dict] = [
    {
        "site_id": "SOI_MND_HSR_01",
        "site_name": "SOI Spot Height 218m Mound",
        "district": "Hisar",
        "longitude": 75.8210,
        "latitude": 29.2150,
        "is_ground_confirmed": False,
        "is_protected_or_excavated": False,
        "relief_class": "low_relief_mound",
        "estimated_height_m": 1.1,
        "horizon_harappan": 0,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "toposheet_symbol",
        "precision_class": "toposheet_1inch",
        "source_citation": "Survey of India 1-inch Sheet 44 O/12; Berganzo-Besga et al. 2023",
    },
    {
        "site_id": "SOI_MND_HSR_02",
        "site_name": "SOI Sand Dune / Spoil Bank Feature",
        "district": "Hisar",
        "longitude": 75.7420,
        "latitude": 29.3890,
        "is_ground_confirmed": False,
        "is_protected_or_excavated": False,
        "relief_class": "low_relief_mound",
        "estimated_height_m": 0.9,
        "horizon_harappan": 0,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "toposheet_symbol",
        "precision_class": "toposheet_1inch",
        "source_citation": "Survey of India 1-inch Sheet 44 O/11; Berganzo-Besga et al. 2023",
    },
    {
        "site_id": "SOI_MND_FTB_01",
        "site_name": "SOI Relict Levee Feature",
        "district": "Fatehabad",
        "longitude": 75.3890,
        "latitude": 29.5120,
        "is_ground_confirmed": False,
        "is_protected_or_excavated": False,
        "relief_class": "low_relief_mound",
        "estimated_height_m": 1.3,
        "horizon_harappan": 0,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "toposheet_symbol",
        "precision_class": "toposheet_1inch",
        "source_citation": "Survey of India 1-inch Sheet 44 N/16; Berganzo-Besga et al. 2023",
    },
    {
        "site_id": "SOI_MND_FTB_02",
        "site_name": "SOI Formline Mound Symbol",
        "district": "Fatehabad",
        "longitude": 75.6020,
        "latitude": 29.6820,
        "is_ground_confirmed": False,
        "is_protected_or_excavated": False,
        "relief_class": "low_relief_mound",
        "estimated_height_m": 1.2,
        "horizon_harappan": 0,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "toposheet_symbol",
        "precision_class": "toposheet_1inch",
        "source_citation": "Survey of India 1-inch Sheet 44 N/15; Berganzo-Besga et al. 2023",
    },
    {
        "site_id": "SOI_MND_SRS_01",
        "site_name": "SOI Ghaggar Bluff Hachure",
        "district": "Sirsa",
        "longitude": 74.7950,
        "latitude": 29.4100,
        "is_ground_confirmed": False,
        "is_protected_or_excavated": False,
        "relief_class": "low_relief_mound",
        "estimated_height_m": 1.5,
        "horizon_harappan": 0,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "toposheet_symbol",
        "precision_class": "toposheet_1inch",
        "source_citation": "Survey of India 1-inch Sheet 44 K/13; Berganzo-Besga et al. 2023",
    },
    {
        "site_id": "SOI_MND_SRS_02",
        "site_name": "SOI Depressional Rim Mound",
        "district": "Sirsa",
        "longitude": 75.1480,
        "latitude": 29.4710,
        "is_ground_confirmed": False,
        "is_protected_or_excavated": False,
        "relief_class": "low_relief_mound",
        "estimated_height_m": 1.0,
        "horizon_harappan": 0,
        "horizon_pgw": 0,
        "horizon_early_historic": 0,
        "horizon_medieval": 0,
        "discovery_modality": "toposheet_symbol",
        "precision_class": "toposheet_1inch",
        "source_citation": "Survey of India 1-inch Sheet 44 O/3; Berganzo-Besga et al. 2023",
    },
]


def build_canonical_sites_dataframe(include_unverified: bool = True) -> pd.DataFrame:
    """Build pandas DataFrame of canonical published sites with exact projected metric coordinates."""
    records = list(PUBLISHED_GROUND_TRUTH_SITES)
    if include_unverified:
        records = records + list(HISTORICAL_UNVERIFIED_MAP_MOUNDS)

    rows = []
    for rec in records:
        r = dict(rec)
        x_m, y_m = wgs84_to_utm43n(r["longitude"], r["latitude"])
        r["x_m"] = x_m
        r["y_m"] = y_m
        r["y_obs"] = 1 if r["is_ground_confirmed"] else 0
        rows.append(r)

    df = pd.DataFrame(rows)
    return df


def export_public_sites_to_csv(output_csv_path: Path | str = "data/raw/public_ground_truth_sites.csv") -> Path:
    """Export the curated canonical sites to raw data directory."""
    path = Path(output_csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = build_canonical_sites_dataframe(include_unverified=True)
    df.to_csv(path, index=False)
    return path
