"""
Interactive Web GIS Map Generator for Pan-Subcontinent Pre-600 BCE Discoveries.
Builds a standalone Leaflet.js HTML map with:
1. High-resolution satellite basemaps (ESRI World Imagery + Labels, CartoDB Dark Matter).
2. 6 Macro-Basin boundary extents with contextual cultural metadata.
3. Mapped relict paleochannels across the Subcontinent (Saraswati, Drishadvati, Paleo-Sutlej, Eastern Nara, Bhogavo, Ganga-Yamuna, Banas, Pravara).
4. Authoritative known/excavated monuments with 1500m spatial exclusion buffer zones.
5. High-confidence undiscovered Pre-600 BCE site candidates (Tier 1: 95%-100% probability).
6. Client-side interactive filter controls by Basin and Cultural Horizon.
"""

from __future__ import annotations
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.pre600bce_cultures import CULTURE_PROFILES
from src.subcontinent_basins import SUBCONTINENT_BASINS
from src.subcontinent_known_monuments import KNOWN_MONUMENTS_REGISTRY
from src.subcontinent_paleochannels import SUBCONTINENT_PALEOCHANNELS


def generate_subcontinent_map_html(
    candidates_csv_path: Path,
    output_html_path: Path,
) -> None:
    df_cands = pd.read_csv(candidates_csv_path)
    cand_records = df_cands.to_dict(orient="records")

    # Serialize known monuments
    known_records = []
    for m in KNOWN_MONUMENTS_REGISTRY:
        known_records.append({
            "site_id": m.site_id,
            "name": m.canonical_name,
            "basin_id": m.basin_id,
            "state_province": m.state_province,
            "country": m.country,
            "lat": m.latitude,
            "lon": m.longitude,
            "culture": m.cultural_horizon,
            "excavation_status": m.excavation_status,
            "protection_status": m.protection_status,
            "citation": m.citation,
        })

    # Serialize paleochannels
    paleo_features = []
    for ch_id, ch_info in SUBCONTINENT_PALEOCHANNELS.items():
        polyline = ch_info["polyline"]
        paleo_features.append({
            "type": "Feature",
            "properties": {
                "channel_id": ch_id,
                "name": str(ch_info["name"]),
                "basin_id": str(ch_info["basin_id"]),
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[pt[0], pt[1]] for pt in polyline],
            },
        })
    paleo_geojson = {"type": "FeatureCollection", "features": paleo_features}

    # Serialize macro basins
    basin_features = []
    basin_colors = {
        "ghaggar_hakra_saraswati": "#06b6d4",       # Cyan
        "upper_indus_punjab": "#3b82f6",            # Blue
        "lower_indus_sindh_balochistan": "#f97316", # Orange
        "gujarat_kutch_saurashtra": "#14b8a6",      # Teal
        "ganga_yamuna_doab": "#10b981",             # Emerald Green
        "central_india_deccan": "#ec4899",          # Pink / Rose
    }

    for b_id, b in SUBCONTINENT_BASINS.items():
        # Bounding box polygon
        poly_coords = [
            [b.lon_min, b.lat_min],
            [b.lon_max, b.lat_min],
            [b.lon_max, b.lat_max],
            [b.lon_min, b.lat_max],
            [b.lon_min, b.lat_min],
        ]
        basin_features.append({
            "type": "Feature",
            "properties": {
                "basin_id": b_id,
                "name": b.name,
                "coverage": b.regional_coverage,
                "cultures": b.major_cultural_horizons,
                "color": basin_colors.get(b_id, "#64748b"),
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [poly_coords],
            },
        })
    basin_geojson = {"type": "FeatureCollection", "features": basin_features}

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Pan-Subcontinent Pre-600 BCE Archaeological Discovery Web GIS</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    body, html {{ margin: 0; padding: 0; height: 100%; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; }}
    #map {{ width: 100%; height: 100%; z-index: 1; }}

    /* Header Bar */
    .top-header {{
      position: absolute; top: 12px; left: 60px; z-index: 1000;
      background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(8px);
      padding: 10px 18px; border-radius: 8px; border: 1px solid rgba(148, 163, 184, 0.2);
      box-shadow: 0 8px 32px rgba(0,0,0,0.5); pointer-events: auto;
    }}
    .top-header h1 {{ margin: 0; font-size: 16px; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 8px; }}
    .top-header p {{ margin: 2px 0 0 0; font-size: 11px; color: #94a3b8; }}

    /* Floating Control Panel */
    .control-panel {{
      position: absolute; top: 12px; right: 12px; z-index: 1000;
      background: rgba(15, 23, 42, 0.94); backdrop-filter: blur(10px);
      padding: 16px; border-radius: 10px; border: 1px solid rgba(148, 163, 184, 0.25);
      box-shadow: 0 10px 40px rgba(0,0,0,0.6); max-width: 340px; font-size: 12px;
      max-height: 90vh; overflow-y: auto; pointer-events: auto;
    }}
    .panel-title {{ font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #38bdf8; margin-bottom: 8px; border-bottom: 1px solid rgba(148, 163, 184, 0.2); padding-bottom: 4px; }}
    .filter-group {{ margin-bottom: 12px; }}
    .filter-group label {{ display: block; font-weight: 600; margin-bottom: 4px; color: #cbd5e1; }}
    .filter-select {{
      width: 100%; padding: 6px 8px; background: #1e293b; color: #f8fafc;
      border: 1px solid #475569; border-radius: 6px; font-size: 11px; outline: none;
    }}
    .stat-badge {{
      display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 11px;
      font-weight: 700; background: #dc2626; color: white; margin-right: 4px;
    }}
    .legend-row {{ display: flex; align-items: center; gap: 8px; margin: 6px 0; font-size: 11px; }}
    .legend-dot {{ width: 12px; height: 12px; border-radius: 50%; display: inline-block; }}
    .legend-sq {{ width: 11px; height: 11px; border-radius: 2px; display: inline-block; }}
    .legend-line {{ width: 18px; height: 3px; display: inline-block; border-radius: 2px; }}

    /* Pulsing marker CSS */
    .pulse-target {{
      background: #ef4444; width: 14px; height: 14px; border-radius: 50%;
      border: 2px solid #ffffff; box-shadow: 0 0 12px #ef4444;
      animation: pulse 1.8s infinite;
    }}
    @keyframes pulse {{
      0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.8); }}
      70% {{ box-shadow: 0 0 0 12px rgba(239, 68, 68, 0); }}
      100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }}
    }}

    /* Popup card */
    .leaflet-popup-content-wrapper {{
      background: #0f172a; color: #f8fafc; border: 1px solid #38bdf8;
      border-radius: 8px; box-shadow: 0 12px 30px rgba(0,0,0,0.8);
    }}
    .leaflet-popup-tip {{ background: #0f172a; border: 1px solid #38bdf8; }}
    .popup-box {{ font-size: 12px; line-height: 1.45; }}
    .popup-hdr {{ font-size: 14px; font-weight: 700; color: #38bdf8; margin-bottom: 4px; border-bottom: 1px solid #334155; padding-bottom: 4px; }}
    .popup-row {{ margin: 4px 0; }}
    .metric-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; margin: 6px 0; background: #1e293b; padding: 6px; border-radius: 4px; font-size: 11px; }}
    .metric-item {{ color: #cbd5e1; }}
    .metric-item strong {{ color: #38bdf8; }}
    .prob-pill {{
      display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px;
      font-weight: 700; background: #15803d; color: #86efac; margin-bottom: 6px;
    }}
    .novelty-pill {{
      display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px;
      font-weight: 700; background: #0369a1; color: #bae6fd; margin-bottom: 6px;
    }}
  </style>
</head>
<body>
  <div class="top-header">
    <h1><span>🛰️</span> Pan-Subcontinent Pre-600 BCE Discovery Map</h1>
    <p>Predictive Spatial Gating Across 6 Macro-Basins &bull; ONLY Unexcavated/Undiscovered Lands Displayed</p>
  </div>

  <div class="control-panel">
    <div class="panel-title">Landscape Gating Controls</div>

    <div class="filter-group">
      <label for="basinSelect">Macro-Basin Filter:</label>
      <select id="basinSelect" class="filter-select" onchange="applyFilters()">
        <option value="ALL">All 6 Macro-Basins (Subcontinent Wide)</option>
        <option value="ghaggar_hakra_saraswati">1. Saraswati-Ghaggar-Hakra & Drishadvati</option>
        <option value="upper_indus_punjab">2. Upper Indus & Punjab Doabs</option>
        <option value="lower_indus_sindh_balochistan">3. Lower Indus, Sindh & Balochistan</option>
        <option value="gujarat_kutch_saurashtra">4. Gujarat, Kutch & Saurashtra</option>
        <option value="ganga_yamuna_doab">5. Ganga-Yamuna Doab & Middle Ganga</option>
        <option value="central_india_deccan">6. Central India & Northern Deccan</option>
      </select>
    </div>

    <div class="filter-group">
      <label for="cultureSelect">Cultural Horizon Filter:</label>
      <select id="cultureSelect" class="filter-select" onchange="applyFilters()">
        <option value="ALL">All Cultural Horizons (Pre-600 BCE)</option>
        <option value="mature_harappan">Mature Harappan Urbanism (~2600-1900 BCE)</option>
        <option value="hakra_early_harappan">Hakra Ware / Early Harappan (~3800-2600 BCE)</option>
        <option value="late_harappan">Late Harappan / Post-Urban (~1900-1300 BCE)</option>
        <option value="painted_grey_ware_vedic">Painted Grey Ware / Vedic (~1200-600 BCE)</option>
        <option value="ocp_copper_hoard">Ochre Coloured Pottery / Copper Hoard (~2000-1500 BCE)</option>
        <option value="ahar_banas">Ahar-Banas Culture (~3000-1500 BCE)</option>
        <option value="malwa_kayatha">Malwa & Kayatha Chalcolithic (~2450-1400 BCE)</option>
        <option value="jorwe_chalcolithic">Jorwe Culture (~1400-700 BCE)</option>
        <option value="gujarat_estuarine_harappan">Gujarat Maritime & Estuarine Harappan (~2600-1600 BCE)</option>
      </select>
    </div>

    <div class="filter-group">
      <label>
        <input type="checkbox" id="toggleBuffers" onchange="toggleExclusionBuffers()" checked />
        Show 1500 m Exclusion Buffers (Guarantees Novelty)
      </label>
    </div>

    <div style="margin: 10px 0; padding: 8px; background: #1e293b; border-radius: 6px;">
      <span class="stat-badge" id="candidateCountDisplay">28</span>
      <span style="font-weight: 600; color: #f1f5f9;">Undiscovered Candidates Visible</span>
    </div>

    <div class="panel-title" style="margin-top: 14px;">Map Legend</div>
    <div class="legend-row">
      <span class="legend-dot" style="background: #ef4444; box-shadow: 0 0 6px #ef4444;"></span>
      <strong>Undiscovered Candidate (Tier 1: 95%-100%)</strong>
    </div>
    <div class="legend-row">
      <span class="legend-sq" style="background: #3b82f6;"></span>
      <span>Known Excavated Monument (Strictly Excluded)</span>
    </div>
    <div class="legend-row">
      <span class="legend-dot" style="background: rgba(59, 130, 246, 0.2); border: 1px dashed #3b82f6;"></span>
      <span>1500 m Exclusion Safety Perimeter</span>
    </div>
    <div class="legend-row">
      <span class="legend-line" style="background: #38bdf8;"></span>
      <span>Relict Paleochannel / Ancient Waterway</span>
    </div>
    <div class="legend-row">
      <span class="legend-line" style="background: rgba(148, 163, 184, 0.4); height: 2px;"></span>
      <span>Macro-Basin Structural Extents</span>
    </div>
  </div>

  <div id="map"></div>

  <script>
    // Candidates and reference data injected from Python backend
    const rawCandidates = {json.dumps(cand_records)};
    const rawMonuments = {json.dumps(known_records)};
    const paleoGeoJSON = {json.dumps(paleo_geojson)};
    const basinGeoJSON = {json.dumps(basin_geojson)};

    // Map initialization centered on the Subcontinent
    const map = L.map('map', {{
      center: [26.8, 74.5],
      zoom: 6,
      zoomControl: false,
    }});
    L.control.zoom({{ position: 'bottomright' }}).addTo(map);

    // Basemaps
    const esriSat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
      maxZoom: 18,
      attribution: 'Esri, Maxar, Earthstar Geographics'
    }}).addTo(map);

    const esriLabels = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
      maxZoom: 18,
      opacity: 0.75
    }}).addTo(map);

    const darkBasemap = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
      subdomains: 'abcd',
      maxZoom: 19
    }});

    // Layer Groups
    const basinLayer = L.geoJSON(basinGeoJSON, {{
      style: function(feature) {{
        return {{
          color: feature.properties.color || '#64748b',
          weight: 1.5,
          dashArray: '4, 4',
          fillColor: feature.properties.color || '#64748b',
          fillOpacity: 0.05,
        }};
      }},
      onEachFeature: function(feature, layer) {{
        layer.bindTooltip("<strong>" + feature.properties.name + "</strong><br><small>" + feature.properties.coverage + "</small>", {{
          sticky: true,
          className: 'basin-tooltip'
        }});
      }}
    }}).addTo(map);

    const paleochannelLayer = L.geoJSON(paleoGeoJSON, {{
      style: {{
        color: '#0284c7',
        weight: 3.5,
        opacity: 0.85,
        dashArray: '6, 6',
      }},
      onEachFeature: function(feature, layer) {{
        layer.bindPopup("<div class='popup-box'><div class='popup-hdr'>Relict Paleochannel</div><strong>" + feature.properties.name + "</strong><br>Basin: " + feature.properties.basin_id + "</div>");
      }}
    }}).addTo(map);

    const bufferGroup = L.layerGroup().addTo(map);
    const monumentGroup = L.layerGroup().addTo(map);
    const candidateGroup = L.layerGroup().addTo(map);

    // Plot Known Monuments with 1500m Exclusion Buffers
    rawMonuments.forEach(m => {{
      // 1500m exclusion buffer circle
      const buffer = L.circle([m.lat, m.lon], {{
        radius: 1500,
        color: '#3b82f6',
        weight: 1,
        dashArray: '3, 3',
        fillColor: '#3b82f6',
        fillOpacity: 0.12,
      }});
      bufferGroup.addLayer(buffer);

      // Monument marker
      const sqIcon = L.divIcon({{
        className: 'custom-monument-icon',
        html: '<div style="background:#2563eb; width:10px; height:10px; border:2px solid #ffffff; border-radius:2px; box-shadow:0 0 6px #2563eb;"></div>',
        iconSize: [12, 12],
        iconAnchor: [6, 6]
      }});
      const marker = L.marker([m.lat, m.lon], {{ icon: sqIcon }});
      marker.bindPopup(
        "<div class='popup-box'>" +
        "<div class='popup-hdr'>Known Documented Monument</div>" +
        "<strong>" + m.name + "</strong><br>" +
        "<div class='popup-row'>📍 " + m.state_province + ", " + m.country + " (" + m.lat.toFixed(4) + "°N, " + m.lon.toFixed(4) + "°E)</div>" +
        "<div class='popup-row'>🏺 Culture: " + m.culture + "</div>" +
        "<div class='popup-row'>⛏️ Status: " + m.excavation_status + " (" + m.protection_status + ")</div>" +
        "<div class='popup-row' style='font-size:10px; color:#94a3b8;'>Citation: " + m.citation + "</div>" +
        "<div style='margin-top:4px; color:#ef4444; font-size:11px; font-weight:600;'>⛔ 1500 m Exclusion Buffer Active: Disallows any novel predictions within this zone!</div>" +
        "</div>"
      );
      monumentGroup.addLayer(marker);
    }});

    // Plot Undiscovered Candidates
    let activeCandidateMarkers = [];

    function renderCandidates(candidatesToRender) {{
      candidateGroup.clearLayers();
      activeCandidateMarkers = [];

      candidatesToRender.forEach(c => {{
        const pulseIcon = L.divIcon({{
          className: 'custom-pulse-marker',
          html: '<div class="pulse-target"></div>',
          iconSize: [14, 14],
          iconAnchor: [7, 7]
        }});

        const marker = L.marker([c.latitude, c.longitude], {{ icon: pulseIcon }});
        marker.bindPopup(
          "<div class='popup-box'>" +
          "<div class='popup-hdr'>Undiscovered Candidate " + c.candidate_id + "</div>" +
          "<span class='prob-pill'>P(Presence): " + (c.calibrated_probability * 100).toFixed(1) + "% (" + c.confidence_tier + ")</span> " +
          "<span class='novelty-pill'>Verified Novel & Unexcavated</span><br>" +
          "<div class='popup-row'><strong>Macro-Basin:</strong> " + c.basin_name + "</div>" +
          "<div class='popup-row'><strong>Location:</strong> " + c.state_province + ", " + c.country + " (" + c.latitude.toFixed(4) + "°N, " + c.longitude.toFixed(4) + "°E)</div>" +
          "<div class='popup-row'><strong>Predicted Culture:</strong> " + c.predicted_culture + " (" + (c.culture_confidence * 100).toFixed(0) + "% conf)</div>" +
          "<div class='popup-row'><strong>Nearest Paleochannel:</strong> " + c.nearest_paleochannel_name + " (" + c.dist_paleochannel_km + " km)</div>" +
          "<div class='popup-row'><strong>Nearest Known Monument:</strong> " + c.nearest_known_monument + " (" + (c.dist_to_known_monument_m / 1000).toFixed(1) + " km away)</div>" +
          "<div class='metric-grid'>" +
          "<div class='metric-item'>MSRM Relief: <strong>" + c.estimated_relief_m + " m</strong></div>" +
          "<div class='metric-item'>White Top-Hat: <strong>" + c.wth_tophat_m + " m</strong></div>" +
          "<div class='metric-item'>Summer BSI: <strong>" + c.bsi_summer_score + "</strong></div>" +
          "<div class='metric-item'>SAR VH: <strong>" + c.sar_vh_db + " dB</strong></div>" +
          "<div class='metric-item'>AlphaEarth Sim: <strong>" + c.alphaearth_similarity + "</strong></div>" +
          "<div class='metric-item'>Orthogonal Gates: <strong>" + c.evidence_gate_count + " / 7</strong></div>" +
          "</div>" +
          "<div class='popup-row' style='font-size:11px; color:#cbd5e1;'><strong>Rationale:</strong> " + c.cultural_rationale + "</div>" +
          "<div class='popup-row' style='font-size:11px; color:#38bdf8; margin-top:4px;'><strong>Field Protocol:</strong> " + c.recommended_ground_check + "</div>" +
          "</div>"
        );
        candidateGroup.addLayer(marker);
        activeCandidateMarkers.push({{ data: c, marker: marker }});
      }});

      document.getElementById('candidateCountDisplay').innerText = candidatesToRender.length;
    }}

    // Apply Client-Side Interactive Filters
    function applyFilters() {{
      const selBasin = document.getElementById('basinSelect').value;
      const selCulture = document.getElementById('cultureSelect').value;

      const filtered = rawCandidates.filter(c => {{
        const matchBasin = (selBasin === 'ALL' || c.basin_id === selBasin);
        const matchCulture = (selCulture === 'ALL' || c.predicted_culture === selCulture);
        return matchBasin && matchCulture;
      }});

      renderCandidates(filtered);
    }}

    // Toggle 1500m exclusion buffers
    function toggleExclusionBuffers() {{
      const chk = document.getElementById('toggleBuffers').checked;
      if (chk) {{
        map.addLayer(bufferGroup);
      }} else {{
        map.removeLayer(bufferGroup);
      }}
    }}

    // Initial render
    renderCandidates(rawCandidates);

    // Layer switcher
    const baseMaps = {{
      "ESRI Satellite (Imagery + Labels)": esriSat,
      "CartoDB Dark Matter (High Contrast)": darkBasemap
    }};
    const overlayMaps = {{
      "Undiscovered Candidates": candidateGroup,
      "Known Recorded Monuments": monumentGroup,
      "1500m Exclusion Buffers": bufferGroup,
      "Relict Paleochannels": paleochannelLayer,
      "Macro-Basins": basinLayer
    }};
    L.control.layers(baseMaps, overlayMaps, {{ position: 'bottomleft' }}).addTo(map);
  </script>
</body>
</html>
"""

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Generated Interactive Subcontinent Web GIS Map: {output_html_path}")


if __name__ == "__main__":
    candidates_csv = Path("results/subcontinent/undiscovered_subcontinent_pre600bce_candidates.csv")
    output_html = Path("results/subcontinent/subcontinent_discovery_map.html")
    generate_subcontinent_map_html(candidates_csv, output_html)
