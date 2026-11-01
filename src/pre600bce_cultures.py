"""
Pre-600 BCE Archaeological Cultural Horizons Specification for the Indian Subcontinent.
Covers the 6 Macro-Basins: Indus Valley, Ghaggar-Hakra (Saraswati), Ganga-Yamuna Valleys,
Gujarat/Kutch/Saurashtra, Balochistan, and Central India / Northern Deccan.

Chronological horizons prior to 600 BCE (pre-Northern Black Polished Ware / pre-Mahajanapada era):
1. Hakra Ware & Early Harappan / Sothi-Siswal (~3800 - 2600 BCE)
2. Mature Harappan Civilisation (~2600 - 1900 BCE)
3. Late Harappan / Post-Urban Indus (~1900 - 1300 BCE)
4. Ochre Coloured Pottery (OCP) & Copper Hoard Culture (~2000 - 1500 BCE)
5. Painted Grey Ware (PGW) & Vedic Riverine Settlements (~1200 - 600 BCE)
6. Ahar-Banas Chalcolithic Culture (~3000 - 1500 BCE)
7. Malwa & Kayatha Chalcolithic Cultures (~2450 - 1400 BCE)
8. Jorwe Culture (~1400 - 700 BCE)
9. Gujarat Maritime & Estuarine Harappan (~2600 - 1600 BCE)
10. Balochistan Aceramic & Early Chalcolithic (~7000 - 2600 BCE)
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
    "ahar_banas": Pre600BCECulture(
        culture_id="ahar_banas",
        canonical_name="Ahar-Banas Chalcolithic Culture",
        period_start_bce=3000,
        period_end_bce=1500,
        primary_drainage="Banas River Basin & Berach/Kothari Tributaries (Mewar)",
        diagnostic_ceramics=["White-painted Black-and-Red Ware", "Tan Ware", "Incised red ware"],
        mound_morphology="Substantial tell mounds with mud-brick and schist stone masonry foundations, 3m to 12m relief",
        typical_area_ha=(1.5, 12.0),
        remote_sensing_signature={
            "relief": "Conical to flat-topped prominent tell mounds in MSRM and White Top-Hat",
            "bsi": "Bright mineral reflectance from exposed schist, quartz, and copper metallurgy slag",
            "sar": "High backscatter roughness due to stone wall footings and slag deposits",
            "paleochannel": "Situated on high elevated river terraces flanking the Banas drainage",
        },
        geographical_epicenter="Udaipur, Rajsamand, Bhilwara, and Chittorgarh (Mewar Plateau, SE Rajasthan)",
    ),
    "malwa_kayatha": Pre600BCECulture(
        culture_id="malwa_kayatha",
        canonical_name="Malwa & Kayatha Chalcolithic Cultures",
        period_start_bce=2450,
        period_end_bce=1400,
        primary_drainage="Narmada, Chambal, Betwa, and Choti Kali Sindh Valleys",
        diagnostic_ceramics=["Chocolate-slipped Kayatha Ware", "Buff-slipped Malwa Ware painted in dark brown/black"],
        mound_morphology="Medium to prominent settlement mounds on ancient river terraces (*dhaba*), 2.5m to 8m relief",
        typical_area_ha=(1.0, 10.0),
        remote_sensing_signature={
            "relief": "Distinct elevated mounds rising above basalt regur plains",
            "bsi": "High contrast between pale anthropogenic pottery debris and surrounding black cotton soil",
            "sar": "Strong dielectric anomaly during post-harvest dry season",
            "paleochannel": "Occupying perennial high-flood terraces of the Narmada and Chambal tributaries",
        },
        geographical_epicenter="Ujjain, Indore, Dhar, Khargone (Malwa Plateau & Narmada Basin, MP)",
    ),
    "jorwe_chalcolithic": Pre600BCECulture(
        culture_id="jorwe_chalcolithic",
        canonical_name="Jorwe Culture (Deccan Chalcolithic)",
        period_start_bce=1400,
        period_end_bce=700,
        primary_drainage="Pravara, Upper Godavari, and Ghod/Bhima River Basins",
        diagnostic_ceramics=["Matt-slipped Jorwe Ware with painted geometric patterns", "Spouted jars and carinated bowls"],
        mound_morphology="Compact nucleated village mounds with mud-plastered wattle-and-daub houses, 2.0m to 6.5m relief",
        typical_area_ha=(0.8, 8.0),
        remote_sensing_signature={
            "relief": "Clearly demarcated circular or oval tell mounds on river terraces",
            "bsi": "Dense ceramic sherd scatter visible in Sentinel-2 Zaid bare soil composites",
            "sar": "Cross-polarization VH contrast against surrounding Deccan trap vertisols",
            "paleochannel": "Perched immediately above seasonal high-flood margins of perennial rivers",
        },
        geographical_epicenter="Ahmednagar, Pune, Nashik, Aurangabad (Northern Maharashtra)",
    ),
    "gujarat_estuarine_harappan": Pre600BCECulture(
        culture_id="gujarat_estuarine_harappan",
        canonical_name="Gujarat Maritime & Estuarine Harappan (Anarta / Sorath)",
        period_start_bce=3000,
        period_end_bce=1600,
        primary_drainage="Relict Luni Delta, Bhadar, Sabarmati, and Rann Embayments",
        diagnostic_ceramics=["Anarta Tradition coarse ware", "Classical Harappan Black-on-Red", "Prabhas Ware"],
        mound_morphology="Fortified stone/mud-brick citadels on rocky bluffs (*bets*) or estuarine mounds, 2.0m to 14m relief",
        typical_area_ha=(1.5, 50.0),
        remote_sensing_signature={
            "relief": "Elevated insular or estuarine mounds clearly separated from saline tidal flats",
            "bsi": "Extremely high bare-soil and sandstone/limestone masonry reflectance",
            "sar": "Severe backscatter difference between dry mound surface and moist saline mudflats",
            "paleochannel": "Aligned along ancient navigable tidal creeks and relict estuarine channels",
        },
        geographical_epicenter="Kutch (Khadir, Pachham), Saurashtra, and Gulf of Khambhat littoral",
    ),
}


def infer_likely_pre600bce_culture(
    latitude: float,
    longitude: float,
    estimated_height_m: float,
    dist_paleochannel_km: float,
    bsi_score: float,
    is_multi_mound: bool = False,
    basin_id: Optional[str] = None,
) -> Tuple[str, float, str]:
    """
    Infer the most probable Pre-600 BCE cultural affiliation based on spatial-geomorphic parameters
    across the entire Indian Subcontinent.
    Returns: (culture_id, confidence_fraction, cultural_rationale).
    """
    # 1. Central India / Deccan Basins
    if basin_id == "central_india_deccan" or (18.0 <= latitude <= 25.5 and 73.0 <= longitude <= 79.5):
        # A. Northern Deccan (Maharashtra) -> Jorwe
        if latitude <= 20.8 and longitude <= 76.5:
            return (
                "jorwe_chalcolithic",
                0.90,
                f"Location in the Godavari-Pravara basin with {estimated_height_m:.1f}m mound relief "
                f"matches nucleated Jorwe Chalcolithic village settlements (~1400-700 BCE).",
            )
        # B. Mewar / SE Rajasthan (Banas basin) -> Ahar-Banas
        if 24.0 <= latitude <= 25.5 and 73.2 <= longitude <= 75.5:
            return (
                "ahar_banas",
                0.92,
                f"Mound height ({estimated_height_m:.1f}m) in the Banas river basin with stone masonry signature "
                f"corresponds to proto-urban Ahar-Banas Chalcolithic centers (~3000-1500 BCE).",
            )
        # C. Malwa Plateau / Narmada Valley -> Malwa & Kayatha
        return (
            "malwa_kayatha",
            0.89,
            f"Fluvial terrace mound ({estimated_height_m:.1f}m) in the Narmada/Chambal drainage "
            f"exhibiting ceramic scatter aligns with Malwa/Kayatha Chalcolithic settlements (~2450-1400 BCE).",
        )

    # 2. Gujarat / Kutch / Saurashtra Basin
    if basin_id == "gujarat_kutch_saurashtra" or (20.5 <= latitude <= 24.5 and 68.5 <= longitude <= 73.5):
        return (
            "gujarat_estuarine_harappan",
            0.93,
            f"Estuarine/littoral mound morphology ({estimated_height_m:.1f}m) near relict tidal waterway "
            f"({dist_paleochannel_km:.1f}km) is diagnostic of Gujarat Maritime/Anarta Harappan horizons.",
        )

    # 3. Lower Indus / Sindh / Balochistan
    if basin_id == "lower_indus_sindh_balochistan" or (longitude < 70.0 and latitude < 30.5):
        if estimated_height_m >= 4.0:
            return (
                "mature_harappan",
                0.94,
                f"Prominent tell mound ({estimated_height_m:.1f}m) in the Lower Indus/Nara floodplain "
                f"strongly indicates an urban Mature Harappan settlement.",
            )
        return (
            "hakra_early_harappan",
            0.88,
            f"Relict alluvial fan/delta mound ({estimated_height_m:.1f}m) in the Sindh-Balochistan borderland "
            f"corresponds to Early Chalcolithic/Amri-Nal pastoral settlements.",
        )

    # 4. Upper Indus & Punjab River Systems (Pakistan & India)
    if basin_id == "upper_indus_punjab" or (latitude >= 30.5 and longitude <= 75.0):
        if estimated_height_m >= 3.5:
            return (
                "mature_harappan",
                0.91,
                f"Elevated mound ({estimated_height_m:.1f}m) on the paleo-Ravi/Sutlej interfluve "
                f"indicates Harappan urban occupation.",
            )
        return (
            "late_harappan",
            0.86,
            f"Mound feature ({estimated_height_m:.1f}m) in the Punjab doab representing Late Harappan / Cemetery H horizon.",
        )

    # 5. Ganga-Yamuna Doab & Middle Ganga Basin
    if basin_id == "ganga_yamuna_doab" or (longitude >= 77.0 and 24.5 <= latitude <= 30.5):
        if 1.5 <= estimated_height_m <= 6.0 and bsi_score > 0.12:
            return (
                "painted_grey_ware_vedic",
                0.89,
                f"Compact settlement mound ({estimated_height_m:.1f}m) along Upper Ganga/Hindon relict meanders "
                f"matches Painted Grey Ware / Vedic riverine sites.",
            )
        return (
            "ocp_copper_hoard",
            0.86,
            f"Low-relief alluvial mound ({estimated_height_m:.1f}m) in the Yamuna-Ganga doab "
            f"characteristic of the Ochre Coloured Pottery / Copper Hoard horizon.",
        )

    # 6. Saraswati-Ghaggar-Hakra Basin (Haryana, N. Rajasthan, Cholistan)
    if estimated_height_m >= 4.0 and dist_paleochannel_km <= 2.5:
        return (
            "mature_harappan",
            0.92,
            f"Prominent mound height ({estimated_height_m:.1f}m) in close proximity to major Ghaggar/Chautang waterway "
            f"({dist_paleochannel_km:.1f}km) strongly matches Mature Harappan urban centers.",
        )

    if 1.5 <= estimated_height_m <= 6.0 and 75.4 <= longitude <= 77.5 and 28.8 <= latitude <= 30.2:
        return (
            "painted_grey_ware_vedic",
            0.89,
            f"Compact mound relief ({estimated_height_m:.1f}m) in the historical Vedic Saraswati-Drishadvati doab "
            f"with close riverine proximity ({dist_paleochannel_km:.1f}km) is characteristic of Painted Grey Ware settlements.",
        )

    if estimated_height_m < 2.5 and longitude <= 75.8 and dist_paleochannel_km <= 2.0:
        return (
            "hakra_early_harappan",
            0.87,
            f"Low-relief mound morphology ({estimated_height_m:.1f}m) along the lower Ghaggar paleolevee "
            f"corresponds to Hakra Ware / Early Harappan agro-pastoral settlements.",
        )

    return (
        "painted_grey_ware_vedic" if bsi_score > 0.1 else "late_harappan",
        0.82,
        f"Pre-600 BCE settlement candidate in the northern interfluve with {estimated_height_m:.1f}m elevation profile.",
    )
