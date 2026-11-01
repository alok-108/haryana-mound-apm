"""
Pre-600 BCE Archaeological Cultural Horizons Specification for Northern India.
Covers the Indus Valley, Ghaggar-Hakra (Saraswati), and Ganga-Yamuna Valleys.

Chronological horizons prior to 600 BCE (pre-Northern Black Polished Ware / pre-Mahajanapada era):
1. Hakra Ware & Early Harappan / Sothi-Siswal (~3300 - 2600 BCE)
2. Mature Harappan Civilisation (~2600 - 1900 BCE)
3. Late Harappan / Post-Urban Indus (~1900 - 1300 BCE)
4. Ochre Coloured Pottery (OCP) & Copper Hoard Culture (~2000 - 1500 BCE)
5. Painted Grey Ware (PGW) & Vedic Riverine Settlements (~1200 - 600 BCE)
6. Early Black-and-Red Ware (BRW) (~1300 - 700 BCE)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Pre600BCECulture:
    culture_id: str
    canonical_name: str
    period_start_bce: int
    period_end_bce: int
    primary_drainage: str
    diagnostic_ceramics: List[str]
    mound_morphology: str
    typical_area_ha: Tuple[float, float]
    remote_sensing_signature: Dict[str, str]
    geographical_epicenter: str


CULTURE_PROFILES: Dict[str, Pre600BCECulture] = {
    "hakra_early_harappan": Pre600BCECulture(
        culture_id="hakra_early_harappan",
        canonical_name="Hakra Ware / Early Harappan (Sothi-Siswal / Ravi)",
        period_start_bce=3300,
        period_end_bce=2600,
        primary_drainage="Ghaggar-Hakra & Relict Chautang (Drishadvati)",
        diagnostic_ceramics=["Mud-appliqué Hakra Ware", "Bichrome Sothi Ware", "Perforated jars"],
        mound_morphology="Low to medium circular/elliptical mounds, 0.8m to 3.5m relief, silty-clay matrix",
        typical_area_ha=(0.5, 4.0),
        remote_sensing_signature={
            "relief": "Low to medium prominence in MSRM (0.3 to 1.5), often eroded or ploughed",
            "bsi": "Elevated Zaid bare-soil reflectance from oxidized silty potsherds",
            "sar": "Moderate VH backscatter contrast against surrounding alluvial loam",
            "paleochannel": "Directly situated on natural levees or paleo-oxbow margins (<= 1500m)",
        },
        geographical_epicenter="Ghaggar-Hakra floodplain (Hisar, Fatehabad, Sirsa, Bahawalpur, Hanumangarh)",
    ),
    "mature_harappan": Pre600BCECulture(
        culture_id="mature_harappan",
        canonical_name="Mature Harappan Urban Civilization",
        period_start_bce=2600,
        period_end_bce=1900,
        primary_drainage="Ghaggar-Hakra, Drishadvati, Indus, and Relict Saraswati Systems",
        diagnostic_ceramics=["Red Ware with black painted geometric/faunal motifs", "Dish-on-stand", "Perforated jars"],
        mound_morphology="Massive multi-mound complexes, citadel and lower town bipartite layout, 4m to 17m relief",
        typical_area_ha=(2.0, 150.0),
        remote_sensing_signature={
            "relief": "Strong prominent White Top-Hat and MSRM (> 2.0 to 10.0+), visible elevated contours",
            "bsi": "Very high summer Bare Soil Index due to baked mud-brick and fired brick debris",
            "sar": "High dielectric C-band VH cross-polarization from structural brick rubble",
            "paleochannel": "Adjacent to major relict trunk waterways (<= 2500m)",
        },
        geographical_epicenter="Rakhigarhi, Banawali, Kalibangan, Mitathal, Harappa corridor",
    ),
    "late_harappan": Pre600BCECulture(
        culture_id="late_harappan",
        canonical_name="Late Harappan / Post-Urban (Cemetery H / Jhukar-related)",
        period_start_bce=1900,
        period_end_bce=1300,
        primary_drainage="Upper Ghaggar, Markanda, Chautang, and Western Yamuna doab",
        diagnostic_ceramics=["Lustrous Red Ware", "Black painted geometric bands", "Coarse red ware"],
        mound_morphology="Small dispersed rural settlement mounds, 0.5m to 2.5m relief",
        typical_area_ha=(0.3, 3.0),
        remote_sensing_signature={
            "relief": "Low relief, frequently partially levelled by modern tractor agriculture",
            "bsi": "Localized ceramic scatter signature detectable in post-harvest Sentinel-2 bare soil bands",
            "sar": "Subtle dielectric contrast in pre-monsoon dry soil",
            "paleochannel": "Shifted toward upper tributary streams and foothill alluvial fans",
        },
        geographical_epicenter="Eastern Haryana, Punjab foothills, and Upper Yamuna divide",
    ),
    "ocp_copper_hoard": Pre600BCECulture(
        culture_id="ocp_copper_hoard",
        canonical_name="Ochre Coloured Pottery (OCP) / Copper Hoard Horizon",
        period_start_bce=2000,
        period_end_bce=1500,
        primary_drainage="Yamuna-Ganga Doab, Hindon, and Relict Sahibi/Krishni",
        diagnostic_ceramics=["Ill-fired Ochre Coloured Pottery (rolled, waterlogged edges)", "Anthropomorphic copper axes"],
        mound_morphology="Often shallow low mounds or buried under 0.5m-2m of flood silt, 0.4m to 1.8m relief",
        typical_area_ha=(0.5, 3.5),
        remote_sensing_signature={
            "relief": "Very subtle MSRM elevation anomaly; requires multi-scale topographic top-hats",
            "bsi": "High ochre/iron oxide spectral absorption signature in Sentinel-2 B4 and B11",
            "sar": "Differential moisture retention along paleo-levees during dry pre-monsoon",
            "paleochannel": "Directly associated with secondary anastomosing meanders in Ganga-Yamuna alluvium",
        },
        geographical_epicenter="Western Uttar Pradesh (Baghpat, Meerut, Saharanpur) and SE Haryana",
    ),
    "painted_grey_ware_vedic": Pre600BCECulture(
        culture_id="painted_grey_ware_vedic",
        canonical_name="Painted Grey Ware (PGW) / Vedic Riverine Horizon",
        period_start_bce=1200,
        period_end_bce=600,
        primary_drainage="Saraswati, Drishadvati, Yamuna, and Upper Ganga (Kuru-Pancala Core)",
        diagnostic_ceramics=["Fine Painted Grey Ware with black painted geometric designs", "Black-and-Red Ware", "Fine Red Slipped Ware"],
        mound_morphology="Prominent compact settlement mounds (*khera* / *theh*), 2.0m to 10m relief, often underlying historic villages",
        typical_area_ha=(1.0, 8.0),
        remote_sensing_signature={
            "relief": "Clear compact elevation signature in MSRM and White Top-Hat (1.0 to 4.5)",
            "bsi": "Distinctive summer bare-soil contrast and dark organic anthropogenic soil (*anthrosol*)",
            "sar": "Strong C-band backscatter contrast against surrounding irrigated wheat fields",
            "paleochannel": "Strict alignment with perennial relict channels and sacred river bends",
        },
        geographical_epicenter="Kurukshetra, Kaithal, Karnal, Jind, Hisar, Rohtak, Panipat, Hastinapur",
    ),
}


def infer_likely_pre600bce_culture(
    latitude: float,
    longitude: float,
    estimated_height_m: float,
    dist_paleochannel_km: float,
    bsi_score: float,
    is_multi_mound: bool = False,
) -> Tuple[str, float, str]:
    """
    Infer the most probable Pre-600 BCE cultural affiliation based on spatial-geomorphic parameters.
    Returns: (culture_id, confidence_fraction, cultural_rationale).
    """
    # 1. Prominent multi-mound complexes on central Ghaggar/Chautang -> Mature Harappan
    if estimated_height_m >= 4.0 and dist_paleochannel_km <= 2.5 and longitude <= 76.2:
        return (
            "mature_harappan",
            0.92,
            f"Prominent mound height ({estimated_height_m:.1f}m) in close proximity to major Ghaggar/Chautang waterway "
            f"({dist_paleochannel_km:.1f}km) strongly matches Mature Harappan urban centers.",
        )

    # 2. Compact mounds in Saraswati/Drishadvati / Kurukshetra-Hisar corridor -> PGW / Vedic
    if 1.5 <= estimated_height_m <= 6.0 and 75.4 <= longitude <= 77.5 and 28.8 <= latitude <= 30.2:
        return (
            "painted_grey_ware_vedic",
            0.89,
            f"Compact mound relief ({estimated_height_m:.1f}m) in the historical Vedic Saraswati-Drishadvati doab "
            f"with close riverine proximity ({dist_paleochannel_km:.1f}km) is characteristic of Painted Grey Ware settlements.",
        )

    # 3. Low relief in western Ghaggar/Sirsa/Fatehabad alluvium -> Hakra / Early Harappan
    if estimated_height_m < 2.5 and longitude <= 75.8 and dist_paleochannel_km <= 2.0:
        return (
            "hakra_early_harappan",
            0.87,
            f"Low-relief mound morphology ({estimated_height_m:.1f}m) along the lower Ghaggar paleolevee "
            f"corresponds to Hakra Ware / Early Harappan agro-pastoral settlements.",
        )

    # 4. Eastern Yamuna-Ganga doab -> OCP / Copper Hoard
    if longitude >= 76.8:
        return (
            "ocp_copper_hoard",
            0.84,
            f"Geographic location in the Yamuna-Ganga divide with subtle relief profile ({estimated_height_m:.1f}m) "
            f"matches the Ochre Coloured Pottery / Copper Hoard horizon.",
        )

    # 5. Default Harappan-Vedic transition
    return (
        "painted_grey_ware_vedic" if bsi_score > 0.1 else "late_harappan",
        0.80,
        f"Pre-600 BCE settlement candidate in the northern interfluve with {estimated_height_m:.1f}m elevation profile.",
    )
