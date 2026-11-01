"""
Interactive Web GIS Map Generator for Pre-600 BCE Discovery Candidates.
Builds a standalone Leaflet.js HTML map with:
1. High-resolution satellite imagery (ESRI World Imagery) and topographic terrain basemaps.
2. Mapped relict paleochannels (Saraswati/Ghaggar, Drishadvati/Chautang, Paleo-Yamuna/Ganga).
3. Known recorded reference sites (Rakhigarhi, Banawali, Agroha, Kunal, Siswal, etc.).
4. Prospective undiscovered site candidates categorized by confidence tiers:
   - Tier 1: 95%-100% (Ultra-High Certainty)
   - Tier 2: 85%-95% (High Priority)
   - Tier 3: 70%-85% (Ploughed/Low-Relief)

Usage:
    python -m scripts.generate_discovery_map --candidates results/candidates/undiscovered_pre600bce_candidates.csv
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd

from src.paleochannel_priors import PALEOCHANNELS_WGS84
from src.public_data_curator import build_canonical_sites_dataframe


def build_interactive_map_html(
    candidates_df: pd.DataFrame,
    output_html_path: Path,
) -> None:
    """Generate standalone self-contained Leaflet HTML map."""
    known_sites = build_canonical_sites_dataframe(include_unverified=False)

    cand_records = candidates_df.to_dict(orient="records")
    known_records = known_sites.to_dict(orient="records")

    # Serialize paleochannel lines as GeoJSON
    paleo_features = []
    for name, line_pts in PALEOCHANNELS_WGS84.items():
        paleo_features.append(
            {
                "type": "Feature",
                "properties": {"name": name.replace("_", " ").title()},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[pt[0], pt[1]] for pt in line_pts],
                },
            }
        )
    paleo_geojson = {"type": "FeatureCollection", "features": paleo_features}

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Pre-600 BCE Archaeological Discovery Map (Indus-Saraswati-Vedic Horizons)</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    body, html {{ margin: 0; padding: 0; height: 100%; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    #map {{ width: 100%; height: 100%; }}
    .info-panel {{
      position: absolute; top: 12px; right: 12px; z-index: 1000;
      background: rgba(255, 255, 255, 0.95); padding: 14px 18px; border-radius: 8px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.25); max-width: 320px; font-size: 13px;
    }}
    .info-panel h2 {{ margin: 0 0 6px 0; font-size: 16px; color: #1a202c; }}
    .badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-bottom: 4px; }}
    .badge-tier1 {{ background: #dc2626; color: white; }}
    .badge-tier2 {{ background: #ea580c; color: white; }}
    .badge-tier3 {{ background: #7c3aed; color: white; }}
    .badge-known {{ background: #2563eb; color: white; }}
    .legend-item {{ margin: 4px 0; display: flex; align-items: center; gap: 8px; font-size: 12px; }}
    .legend-color {{ width: 14px; height: 14px; border-radius: 50%; display: inline-block; }}
    .popup-title {{ font-size: 14px; font-weight: bold; margin-bottom: 4px; color: #111827; }}
    .popup-meta {{ font-size: 12px; line-height: 1.45; color: #374151; }}
  </style>
</head>
<body>
  <div id="map"></div>
  <div class="info-panel">
    <h2>Pre-600 BCE Discovery Map</h2>
    <div style="color: #4b5563; font-size: 12px; margin-bottom: 8px;">
      Prospective unrecorded sites in the Indus, Saraswati-Ghaggar & Ganga basins.
    </div>
    <div class="legend-item"><span class="legend-color" style="background: #dc2626;"></span> <strong>Tier 1 (95%-100%):</strong> Ultra-High Confidence</div>
    <div class="legend-item"><span class="legend-color" style="background: #ea580c;"></span> <strong>Tier 2 (85%-95%):</strong> High Priority Candidate</div>
    <div class="legend-item"><span class="legend-color" style="background: #7c3aed;"></span> <strong>Tier 3 (70%-85%):</strong> Ploughed/Low-Relief</div>
    <div class="legend-item"><span class="legend-color" style="background: #2563eb;"></span> <strong>Recorded Sites:</strong> Reference ground-truth</div>
    <div class="legend-item"><span style="width: 16px; height: 3px; background: #0284c7; display: inline-block;"></span> <strong>Relict Paleochannel:</strong> Saraswati/Chautang</div>
  </div>

  <script>
    const map = L.map('map').setView([29.40, 75.50], 9);

    // Basemaps
    const esriSat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
      maxZoom: 18,
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    }}).addTo(map);

    const osm = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }});

    const topo = L.tileLayer('https://{{s}}.tile.opentopomap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 17,
      attribution: 'Map data: &copy; OpenStreetMap contributors, SRTM | Map style: &copy; OpenTopoMap'
    }});

    const baseMaps = {{
      "Satellite (ESRI World Imagery)": esriSat,
      "OpenStreetMap": osm,
      "Topographic Terrain": topo
    }};

    // 1. Draw Paleochannels
    const paleoData = {json.dumps(paleo_geojson)};
    const paleoLayer = L.geoJSON(paleoData, {{
      style: {{
        color: '#38bdf8',
        weight: 3.5,
        dashArray: '6, 6',
        opacity: 0.85
      }},
      onEachFeature: function(feature, layer) {{
        layer.bindPopup('<strong>Relict Paleochannel:</strong><br>' + feature.properties.name);
      }}
    }}).addTo(map);

    // 2. Known Recorded Sites
    const knownSites = {json.dumps(known_records)};
    const knownLayer = L.layerGroup();
    knownSites.forEach(s => {{
      const marker = L.circleMarker([s.latitude, s.longitude], {{
        radius: 7,
        fillColor: '#2563eb',
        color: '#ffffff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.9
      }});
      marker.bindPopup(`
        <div class="popup-title">${{s.site_name}}</div>
        <span class="badge badge-known">Recorded Reference Site</span><br>
        <div class="popup-meta">
          <strong>District:</strong> ${{s.district}}<br>
          <strong>Relief:</strong> ${{s.relief_class}} (~${{s.estimated_height_m}}m)<br>
          <strong>Citation:</strong> ${{s.source_citation}}
        </div>
      `);
      knownLayer.addLayer(marker);
    }}).addTo(map);

    // 3. Prospective Discovery Candidates
    const candidates = {json.dumps(cand_records)};
    const tier1Layer = L.layerGroup();
    const tier2Layer = L.layerGroup();
    const tier3Layer = L.layerGroup();

    candidates.forEach(c => {{
      const probPct = (c.calibrated_probability * 100).toFixed(1);
      let color = '#7c3aed';
      let radius = 6;
      let targetLayer = tier3Layer;
      let badgeClass = 'badge-tier3';

      if (c.calibrated_probability >= 0.95) {{
        color = '#dc2626';
        radius = 10;
        targetLayer = tier1Layer;
        badgeClass = 'badge-tier1';
      }} else if (c.calibrated_probability >= 0.85) {{
        color = '#ea580c';
        radius = 8;
        targetLayer = tier2Layer;
        badgeClass = 'badge-tier2';
      }}

      const marker = L.circleMarker([c.latitude, c.longitude], {{
        radius: radius,
        fillColor: color,
        color: '#ffffff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.95
      }});

      marker.bindPopup(`
        <div class="popup-title">${{c.candidate_id}}</div>
        <span class="badge ${{badgeClass}}">${{c.confidence_tier}}</span><br>
        <div class="popup-meta">
          <strong>Calibrated Probability:</strong> <span style="font-size:14px;color:${{color}};font-weight:bold;">${{probPct}}%</span><br>
          <strong>GPS Coordinates:</strong> ${{c.latitude.toFixed(5)}}° N, ${{c.longitude.toFixed(5)}}° E<br>
          <strong>Predicted Culture:</strong> <strong>${{c.predicted_culture.toUpperCase()}}</strong><br>
          <strong>Estimated Mound Relief:</strong> ${{c.estimated_height_m.toFixed(1)}} meters<br>
          <strong>Paleochannel Distance:</strong> ${{c.dist_paleochannel_km.toFixed(2)}} km<br>
          <strong>Orthogonal Gates Passed:</strong> ${{c.evidence_gate_count}} of 7<br>
          <strong>Historical Map Feature:</strong> ${{c.on_historical_soi_map ? 'Yes (SOI toposheet)' : 'No'}}<br>
          <hr style="margin:4px 0;border:0;border-top:1px solid #e5e7eb;">
          <small>${{c.cultural_rationale}}</small>
        </div>
      `);
      targetLayer.addLayer(marker);
    }});

    tier1Layer.addTo(map);
    tier2Layer.addTo(map);
    tier3Layer.addTo(map);

    const overlayMaps = {{
      "Tier 1: 95%-100% Candidates": tier1Layer,
      "Tier 2: 85%-95% Candidates": tier2Layer,
      "Tier 3: 70%-85% Candidates": tier3Layer,
      "Known Reference Sites": knownLayer,
      "Relict Paleochannels": paleoLayer
    }};

    L.control.layers(baseMaps, overlayMaps, {{ collapsed: false }}).addTo(map);
  </script>
</body>
</html>
"""

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Interactive Pre-600 BCE Discovery Map")
    parser.add_argument(
        "--candidates",
        type=str,
        default="results/candidates/undiscovered_pre600bce_candidates.csv",
        help="Path to candidates CSV",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/candidates/interactive_discovery_map.html",
        help="Output HTML map path",
    )
    args = parser.parse_args()

    cand_path = Path(args.candidates)
    if not cand_path.exists():
        raise FileNotFoundError(f"Candidates file not found at: {cand_path}")

    df = pd.read_csv(cand_path)
    out_html = Path(args.output)
    out_html.parent.mkdir(parents=True, exist_ok=True)

    build_interactive_map_html(df, out_html)
    print(f"Interactive Discovery Map generated successfully: {out_html.resolve()}")


if __name__ == "__main__":
    main()
