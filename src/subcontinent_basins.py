"""
Pan-Subcontinent Pre-600 BCE Macro-Basin Architecture.
Defines the 6 principal geographic and hydrological basins of the Indian Subcontinent
where Pre-600 BCE agricultural, proto-urban, and early historic civilizations developed.

The 6 Macro-Basins:
1. GHAGGAR_HAKRA_SARASWATI: Saraswati-Ghaggar-Hakra Basin & Drishadvati (NW India & Cholistan)
2. UPPER_INDUS_PUNJAB: Upper Indus & Punjab River Systems (Interfluves / Doabs)
3. LOWER_INDUS_SINDH_BALOCHISTAN: Lower Indus, Sindh & Balochistan (Kachi Plain & Makran)
4. GUJARAT_KUTCH_SAURASHTRA: Gujarat, Rann of Kutch & Saurashtra Peninsula
5. GANGA_YAMUNA_DOAB: Ganga-Yamuna Interfluve & Middle Ganga Valley (Vedic & OCP Core)
6. CENTRAL_INDIA_DECCAN: Mewar (Ahar-Banas), Malwa Plateau & Northern Deccan (Pravara/Godavari)

References:
- Possehl, G.L. (2002), 'The Indus Civilization: A Contemporary Perspective', AltaMira Press.
- Chakrabarti, D.K. (1999), 'India: An Archaeological History', Oxford University Press.
- Lal, B.B. (1997), 'The Earliest Civilization of South Asia', Aryan Books.
- Joshi, J.P. (1993), 'Excavation at Bhagwanpura 1977-78', Archaeological Survey of India.
- Dhavalikar, M.K. (1997), 'Indian Protohistory', Books & Books.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class MacroBasin:
    basin_id: str
    name: str
    regional_coverage: str
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    primary_drainage_systems: List[str]
    major_cultural_horizons: List[str]
    landscape_character: str
    remote_sensing_challenges: str


SUBCONTINENT_BASINS: Dict[str, MacroBasin] = {
    "ghaggar_hakra_saraswati": MacroBasin(
        basin_id="ghaggar_hakra_saraswati",
        name="Saraswati-Ghaggar-Hakra & Drishadvati Basin",
        regional_coverage="Haryana, Punjab (India), Northern Rajasthan, Cholistan Desert (Punjab, Pakistan)",
        lat_min=27.5,
        lat_max=31.5,
        lon_min=71.0,
        lon_max=77.5,
        primary_drainage_systems=["Relict Saraswati / Ghaggar Trunk", "Relict Drishadvati / Chautang", "Naiwal Channels"],
        major_cultural_horizons=[
            "Hakra Ware (~3800-3200 BCE)",
            "Early Harappan / Sothi-Siswal (~3300-2600 BCE)",
            "Mature Harappan (~2600-1900 BCE)",
            "Late Harappan / Bara (~1900-1300 BCE)",
            "Painted Grey Ware / Vedic (~1200-600 BCE)",
        ],
        landscape_character="Alluvial plain transitioning into active sand-dune belts (Thar desert margin); relict fluvial paleochannels with localized clay-silt depressions (dahars).",
        remote_sensing_challenges="Distinguishing low-relief anthropogenic mounds (<1.5m) from aeolian sand dunes; modern canal irrigation masking paleodrainage.",
    ),
    "upper_indus_punjab": MacroBasin(
        basin_id="upper_indus_punjab",
        name="Upper Indus & Punjab Interfluves (Doabs)",
        regional_coverage="Pakistani Punjab (Bari, Rechna, Jech, Chaj, Sindh Sagar doabs), Indian Punjab, NW Khyber Pakhtunkhwa",
        lat_min=29.5,
        lat_max=34.0,
        lon_min=70.0,
        lon_max=76.5,
        primary_drainage_systems=["Indus River", "Ravi River", "Chenab River", "Jhelum River", "Beas River", "Sutlej River"],
        major_cultural_horizons=[
            "Ravi Phase / Early Harappan (~3300-2800 BCE)",
            "Kot Diji Horizon (~2800-2600 BCE)",
            "Mature Harappan Urbanism (~2600-1900 BCE)",
            "Cemetery H / Late Harappan (~1900-1300 BCE)",
        ],
        landscape_character="Massive fertile quaternary alluvial interfluves (doabs); heavy fluvial sediment accumulation and active river channel migration.",
        remote_sensing_challenges="Intense multi-cropping agriculture and seasonal flood silting that buries shallow sites under 1-3m of recent silt.",
    ),
    "lower_indus_sindh_balochistan": MacroBasin(
        basin_id="lower_indus_sindh_balochistan",
        name="Lower Indus, Sindh Valley & Balochistan Highlands",
        regional_coverage="Sindh (Larkana, Sukkur, Dadu, Thatta), Balochistan (Kachi Plain, Bolan Pass, Lasbela, Makran)",
        lat_min=24.5,
        lat_max=30.5,
        lon_min=61.5,
        lon_max=70.0,
        primary_drainage_systems=["Lower Indus Trunk", "Eastern Nara (Relict Hakra)", "Bolan River", "Porali River", "Dasht River"],
        major_cultural_horizons=[
            "Mehrgarh Aceramic Neolithic & Chalcolithic (~7000-2600 BCE)",
            "Amri-Nal Culture (~3200-2400 BCE)",
            "Kulli Complex (~2500-2000 BCE)",
            "Mature Harappan Urbanism (~2600-1900 BCE)",
            "Jhukar Phase (~1900-1500 BCE)",
        ],
        landscape_character="Hyper-arid alluvial valley flanked by rugged folded calcareous ranges (Kirthar, Sulaiman, Makran); major tell mounds (*dambs*).",
        remote_sensing_challenges="Salinization crusts (kallar), high thermal reflection, and aeolian deflation of surface ceramics.",
    ),
    "gujarat_kutch_saurashtra": MacroBasin(
        basin_id="gujarat_kutch_saurashtra",
        name="Gujarat, Rann of Kutch & Saurashtra Peninsula",
        regional_coverage="Kutch (Khadir, Pachham, Bela islands), Saurashtra (Kathiawar), North Gujarat plains, Gulf of Khambhat",
        lat_min=20.5,
        lat_max=24.8,
        lon_min=68.5,
        lon_max=73.5,
        primary_drainage_systems=["Relict Luni Delta", "Sabarmati River", "Mahi River", "Bhadar River", "Bhogavo River", "Banashthali"],
        major_cultural_horizons=[
            "Anarta Tradition (~3950-2200 BCE)",
            "Pre-Prabhas Horizon (~3000-2600 BCE)",
            "Mature Classical Harappan (~2600-1900 BCE)",
            "Sorath Harappan & Rangpur IIB/C (~2000-1400 BCE)",
            "Lustrous Red Ware (~1400-1000 BCE)",
        ],
        landscape_character="Saline mudflats (Great & Little Rann), uplifted rocky islands (*bets*), semi-arid coastal plains, and basaltic tablelands.",
        remote_sensing_challenges="Extreme tidal and seasonal monsoon flooding in Rann; hypersaline salt encrustations affecting SAR backscatter.",
    ),
    "ganga_yamuna_doab": MacroBasin(
        basin_id="ganga_yamuna_doab",
        name="Ganga-Yamuna Interfluve & Middle Ganga Basin",
        regional_coverage="Western UP (Saharanpur, Meerut, Baghpat, Bulandshahr), Middle Doab (Aligarh, Mathura, Agra, Kannauj), Middle Ganga (Prayagraj, Varanasi)",
        lat_min=24.5,
        lat_max=30.5,
        lon_min=76.5,
        lon_max=84.5,
        primary_drainage_systems=["Paleo-Yamuna", "Paleo-Ganga", "Hindon River", "Kali Nadi East", "Krishni River", "Gomti River", "Ghaghara River"],
        major_cultural_horizons=[
            "Late Harappan / Bargaon Horizon (~1900-1500 BCE)",
            "Ochre Coloured Pottery (OCP) / Copper Hoard Culture (~2000-1500 BCE)",
            "Black-and-Red Ware (BRW) (~1450-1000 BCE)",
            "Painted Grey Ware (PGW) / Early Vedic & Epic Horizon (~1200-600 BCE)",
        ],
        landscape_character="Deep quaternary Gangetic alluvium; high-density agricultural settlement with relict meander scrolls, oxbow lakes (*tals*), and natural river levees.",
        remote_sensing_challenges="Extremely dense modern human settlement footprint; brick kilns in peri-urban zones; continuous canal-fed green vegetation cover.",
    ),
    "central_india_deccan": MacroBasin(
        basin_id="central_india_deccan",
        name="Central India & Northern Deccan (Mewar, Malwa & Pravara)",
        regional_coverage="SE Rajasthan (Mewar Plateau), Madhya Pradesh (Malwa Plateau, Narmada Valley), Maharashtra (Upper Godavari, Pravara, Ghod)",
        lat_min=18.0,
        lat_max=25.5,
        lon_min=73.0,
        lon_max=79.5,
        primary_drainage_systems=["Banas River", "Chambal River", "Narmada River", "Tapi River", "Pravara River", "Godavari River", "Ghod River"],
        major_cultural_horizons=[
            "Ahar-Banas Culture (~3000-1500 BCE)",
            "Kayatha Culture (~2450-2000 BCE)",
            "Malwa Culture (~1900-1400 BCE)",
            "Jorwe Culture (~1400-700 BCE)",
        ],
        landscape_character="Deccan volcanic trap basalt topography, black cotton soil (*regur*), elevated river terraces along deeply incised perennial river valleys.",
        remote_sensing_challenges="Black cotton soil cracking and swelling dynamics; basalt rock outcrop confusion with stone-walled tell mounds.",
    ),
}


def find_macro_basin_for_coordinates(lat: float, lon: float) -> MacroBasin | None:
    """Find the corresponding macro-basin for a given latitude and longitude."""
    for basin in SUBCONTINENT_BASINS.values():
        if basin.lat_min <= lat <= basin.lat_max and basin.lon_min <= lon <= basin.lon_max:
            return basin
    return None
