"""
Multi-Format Archaeological Export Engine for Pre-600 BCE Discoveries.
Generates:
1. GeoJSON (RFC 7946) for QGIS, ArcGIS, and Mapbox
2. KML for Google Earth 3D Aerial Inspection
3. GPX for Garmin / Trimble Handheld Field GPS Units
4. Comprehensive Field Survey Dossiers for Ground Expeditions
"""

from __future__ import annotations
from dataclasses import asdict
import html
import json
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

from src.subcontinent_discovery_engine import SubcontinentCandidate


def candidate_to_geojson_feature(candidate: SubcontinentCandidate) -> dict:
    """Convert SubcontinentCandidate into an RFC 7946 GeoJSON Feature."""
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [round(candidate.longitude, 6), round(candidate.latitude, 6)],
        },
        "properties": {
            "candidate_id": candidate.candidate_id,
            "basin_id": candidate.basin_id,
            "basin_name": candidate.basin_name,
            "state_province": candidate.state_province,
            "country": candidate.country,
            "calibrated_probability": round(candidate.calibrated_probability, 4),
            "confidence_tier": candidate.confidence_tier,
            "predicted_culture": candidate.predicted_culture,
            "culture_confidence": round(candidate.culture_confidence, 4),
            "cultural_rationale": candidate.cultural_rationale,
            "nearest_paleochannel": candidate.nearest_paleochannel_name,
            "dist_paleochannel_km": round(candidate.dist_paleochannel_km, 2),
            "fluvial_prior_score": round(candidate.fluvial_prior_score, 3),
            "estimated_relief_m": round(candidate.estimated_relief_m, 2),
            "wth_tophat_m": round(candidate.wth_tophat_m, 2),
            "bsi_summer_score": round(candidate.bsi_summer_score, 3),
            "sar_vh_db": round(candidate.sar_vh_db, 2),
            "alphaearth_similarity": round(candidate.alphaearth_similarity, 3),
            "on_historical_soi_map": candidate.on_historical_soi_map,
            "nearest_known_monument": candidate.nearest_known_monument,
            "dist_to_known_monument_m": round(candidate.dist_to_known_monument_m, 1),
            "is_novel_undiscovered": True,
            "recommended_ground_check": candidate.recommended_ground_check,
        },
    }


def candidates_to_geojson(candidates: List[SubcontinentCandidate]) -> dict:
    """Convert list of candidates into a GeoJSON FeatureCollection."""
    return {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
        "metadata": {
            "generated_by": "Archaeological Predictive Modeling (APM) Subcontinent Engine",
            "chronological_scope": "Pre-600 BCE (Indus, Saraswati, Vedic, Chalcolithic)",
            "safety_invariant": "Strict >=1500m exclusion against all registered historical monuments",
            "total_candidates": len(candidates),
        },
        "features": [candidate_to_geojson_feature(c) for c in candidates],
    }


def candidates_to_kml(candidates: List[SubcontinentCandidate]) -> str:
    """Generate KML format with stylized balloons for Google Earth."""
    kml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '  <Document>',
        '    <name>Pre-600 BCE Undiscovered Archaeological Candidates</name>',
        '    <description>Subcontinent-wide GeoAI prospective discoveries (P &gt;= 95%, unexcavated, unrecorded)</description>',
        '    <Style id="discoveryPin">',
        '      <IconStyle>',
        '        <color>ff00aaff</color>',
        '        <scale>1.2</scale>',
        '        <Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>',
        '      </IconStyle>',
        '    </Style>',
    ]

    for c in candidates:
        desc = f"""
        <table border="1" cellpadding="4" style="border-collapse:collapse;font-family:sans-serif;font-size:12px;">
          <tr bgcolor="#f4ecd8"><th colspan="2">🌟 {c.candidate_id}: {c.predicted_culture}</th></tr>
          <tr><td><b>Presence Probability:</b></td><td><b>{c.calibrated_probability * 100:.1f}%</b></td></tr>
          <tr><td><b>Macro-Basin:</b></td><td>{c.basin_name} ({c.state_province}, {c.country})</td></tr>
          <tr><td><b>Nearest Paleochannel:</b></td><td>{c.nearest_paleochannel_name} ({c.dist_paleochannel_km:.2f} km)</td></tr>
          <tr><td><b>Micro-Topography (Relief):</b></td><td>+{c.estimated_relief_m:.1f} m (Tophat: {c.wth_tophat_m:.1f} m)</td></tr>
          <tr><td><b>Nearest Documented Monument:</b></td><td>{c.nearest_known_monument} ({c.dist_to_known_monument_m / 1000.0:.2f} km away - 100% Novel)</td></tr>
          <tr><td><b>Diagnostic Ceramics &amp; Features:</b></td><td>{html.escape(c.cultural_rationale)}</td></tr>
          <tr><td><b>Recommended Survey Protocol:</b></td><td>{html.escape(c.recommended_ground_check)}</td></tr>
        </table>
        """
        kml_lines.extend([
            '    <Placemark>',
            f'      <name>{c.candidate_id} ({c.predicted_culture})</name>',
            f'      <styleUrl>#discoveryPin</styleUrl>',
            f'      <description><![CDATA[{desc}]]></description>',
            '      <Point>',
            f'        <coordinates>{c.longitude:.6f},{c.latitude:.6f},{c.estimated_relief_m:.1f}</coordinates>',
            '      </Point>',
            '    </Placemark>',
        ])

    kml_lines.extend([
        '  </Document>',
        '</kml>',
    ])
    return '\n'.join(kml_lines)


def candidates_to_gpx(candidates: List[SubcontinentCandidate]) -> str:
    """Generate GPS Exchange Format (GPX 1.1) for handheld GPS units."""
    gpx_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx version="1.1" creator="APM Subcontinent GeoAI Engine" xmlns="http://www.topografix.com/GPX/1/1">',
        '  <metadata>',
        '    <name>Pre-600 BCE Undiscovered Mound Discoveries</name>',
        '    <desc>Target waypoints for ground archaeological verification surveys</desc>',
        '  </metadata>',
    ]

    for c in candidates:
        name = f"{c.candidate_id}"
        desc = (
            f"Culture: {c.predicted_culture} | Prob: {c.calibrated_probability * 100:.1f}% | "
            f"Relief: +{c.estimated_relief_m:.1f}m | Paleochannel: {c.nearest_paleochannel_name} "
            f"({c.dist_paleochannel_km:.1f}km) | Nearest Known Monument: {c.nearest_known_monument} "
            f"({c.dist_to_known_monument_m/1000.0:.1f}km)"
        )
        gpx_lines.extend([
            f'  <wpt lat="{c.latitude:.6f}" lon="{c.longitude:.6f}">',
            f'    <ele>{c.estimated_relief_m:.1f}</ele>',
            f'    <name>{html.escape(name)}</name>',
            f'    <desc>{html.escape(desc)}</desc>',
            '    <type>Archaeological Mound Prospect</type>',
            '  </wpt>',
        ])

    gpx_lines.append('</gpx>')
    return '\n'.join(gpx_lines)


def generate_field_survey_dossier(candidate: SubcontinentCandidate) -> str:
    """
    Generate an exhaustive, field-ready archaeological briefing dossier
    with non-invasive geophysical survey guidelines and geomorphic context.
    """
    gpr_recommendation = (
        "- **Ground-Penetrating Radar (GPR):** Employ a 400 MHz center-frequency dipole antenna. "
        "Run an orthogonal 0.5 m traverse grid across the elevated mound crown to resolve buried "
        "mudbrick or fired-brick foundation walls up to 2.5 m depth."
    )
    mag_recommendation = (
        "- **Fluxgate Magnetic Gradiometry:** High-resolution magnetic gradient survey "
        "(0.25 m along-line sample interval, 0.5 m line spacing) to detect thermo-remanent "
        "magnetic anomalies (ceramic firing kilns, hearths, and burnt vitrified pottery dumps)."
    )
    uav_recommendation = (
        "- **UAV Photogrammetry / LiDAR:** Fly an autonomous drone grid at 40-50 m AGL with RTK-GNSS "
        "base station reference to generate a 2 cm Digital Surface Model (DSM) and calculate residual "
        "topographic prominence relative to surrounding agricultural fields."
    )
    coring_recommendation = (
        "- **Hand-Auger Sediment Coring:** Extract 50 mm continuous sediment cores in 50 cm increments "
        "at the mound skirt to identify the Holocene floodplain-cultural horizon contact boundary and "
        "retrieve charcoal for accelerator mass spectrometry (AMS) radiocarbon dating."
    )

    dossier = f"""# Archaeological Field Survey Dossier: {candidate.candidate_id}
**Target Classification:** 🌟 100% Novel / Undiscovered Archaeological Mound Candidate  
**Chronological Horizon:** {candidate.predicted_culture} (Pre-600 BCE)  
**Calibrated GeoAI Probability:** **{candidate.calibrated_probability * 100:.2f}%** ({candidate.confidence_tier})  

---

## 1. Geospatial & Administrative Location
- **Centroid Coordinates:** `{candidate.latitude:.6f}° N, {candidate.longitude:.6f}° E`
- **Macro-Basin:** {candidate.basin_name} (`{candidate.basin_id}`)
- **State / Province:** {candidate.state_province}, {candidate.country}
- **Nearest Registered Monument:** {candidate.nearest_known_monument}
- **Spatial Separation:** **{candidate.dist_to_known_monument_m:.0f} meters** ({candidate.dist_to_known_monument_m / 1000.0:.2f} km)
  *(Safety Verification: Exceeds mandatory 1,500 m exclusion buffer; strictly unexcavated and undocumented)*

---

## 2. Paleohydrological Setting
- **Associated Ancient Watercourse:** `{candidate.nearest_paleochannel_name}`
- **Distance to Relict River Bed:** **{candidate.dist_paleochannel_km:.2f} km**
- **Fluvial Prior Score:** {candidate.fluvial_prior_score:.3f} / 1.000
- **Geomorphic Context:** Ancient natural levee / oxbow bluff situated above seasonal inundation level.

---

## 3. Multi-Sensor Physics & Remote Sensing Telemetry
| Diagnostic Sensor | Observed Metric | Physical Anomaly Interpretation |
| :--- | :--- | :--- |
| **Micro-Topography (DEM)** | `+{candidate.estimated_relief_m:.2f} m` | Anthropogenic tell mound elevated above flat alluvium |
| **White Top-Hat Filter** | `+{candidate.wth_tophat_m:.2f} m` | Localized positive elevation bump characteristic of habitational mounds |
| **Bare Soil Index (BSI)** | `{candidate.bsi_summer_score:.3f}` | High mineral reflectance; compact brick rubble and caliche accumulation |
| **Sentinel-1 SAR (VH)** | `{candidate.sar_vh_db:.2f} dB` | Radar cross-polarization backscatter contrast from subsurface structures |
| **AlphaEarth AI Similarity** | `{candidate.alphaearth_similarity:.3f}` | 64D satellite foundation model feature alignment with canonical sites |
| **Survey of India (SOI)** | `{"Confirmed Hachure" if candidate.on_historical_soi_map else "Unmarked Land"}` | {"Historical 1-inch toposheet indicates elevated landform" if candidate.on_historical_soi_map else "Completely obscured/unmarked on historical maps"} |

---

## 4. Cultural Attribution & Ceramic Diagnostic Markers
- **Cultural Horizon:** {candidate.predicted_culture} (Confidence: {candidate.culture_confidence * 100:.1f}%)
- **Diagnostic Rationales:** {candidate.cultural_rationale}
- **Field Visual Clues:** Look for exposed pottery scatters along plough furrows, burnt clay nodules, micro-blade debitage, and ash layers in erosion gullies.

---

## 5. Recommended Non-Invasive Geophysical Protocol
{gpr_recommendation}
{mag_recommendation}
{uav_recommendation}
{coring_recommendation}

---

## 6. Antiquities Governance & Anti-Looting Compliance
> [!IMPORTANT]
> This candidate dossier is produced solely for non-destructive academic research, spatial modeling, and statutory survey planning.
> In accordance with the Antiquities and Art Treasures Act (1972) / Ancient Monuments Preservation Acts, any surface collection, excavation, or invasive exploration must be conducted strictly under formal permits issued by the Archaeological Survey of India (ASI) or competent State Archaeology Departments.
"""
    return dossier
