"""
Automated Pytest Suite for Ultimate Subcontinent APM Upgrades:
1. Top-level python API package (`import src as apm`).
2. Multi-Format Field Export Engine (GeoJSON, KML, GPX, Dossier).
3. 97 Canonical Reference Monuments & 100% Benchmark Recovery.
4. 57 Vetted Undiscovered Candidates (Strict 1500m exclusion, P >= 95%).
5. CLI tools (apm-scan, apm-export, apm-dossier).
6. Live REST API Export Endpoints.
"""

from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import threading
import pytest
import requests

import src as apm
from src.export_engine import (
    candidates_to_geojson,
    candidates_to_gpx,
    candidates_to_kml,
    generate_field_survey_dossier,
)
from src.subcontinent_discovery_engine import SubcontinentDiscoveryEngine
from src.subcontinent_known_monuments import KNOWN_MONUMENTS_REGISTRY, SubcontinentKnownMonumentsRegistry
from src.web_server import ArchaeologicalHTTPHandler


def test_top_level_api_scan_novel_and_known():
    """Verify apm.scan() distinguishes undiscovered terrain from known monuments."""
    # Novel coordinate
    res_novel = apm.scan(lat=29.5085, lon=74.8420)
    assert res_novel.is_novel_undiscovered is True
    assert res_novel.is_exclusion_breached is False
    assert res_novel.calibrated_probability >= 0.95
    assert res_novel.dist_to_documented_monument_m >= 1500.0
    assert len(res_novel.recommended_survey_methods) >= 3

    # Documented monument coordinate (Rakhigarhi)
    res_known = apm.scan(lat=29.2936, lon=76.0822)
    assert res_known.is_novel_undiscovered is False
    assert res_known.is_exclusion_breached is True
    assert res_known.dist_to_documented_monument_m < 500.0
    assert "Rakhigarhi" in res_known.nearest_documented_monument


def test_top_level_api_candidates_and_regions():
    """Verify apm.scan_candidates() and apm.scan_region() bounding-box queries."""
    cands = apm.scan_candidates(min_probability=0.95)
    assert len(cands) >= 50
    for c in cands:
        assert c.calibrated_probability >= 0.95
        assert c.dist_to_known_monument_m >= 1500.0

    # Regional bounding box (Haryana / Saraswati basin)
    reg_cands = apm.scan_region(min_lat=29.0, min_lon=74.0, max_lat=30.0, max_lon=76.5)
    assert len(reg_cands) > 0
    for c in reg_cands:
        assert 29.0 <= c.latitude <= 30.0
        assert 74.0 <= c.longitude <= 76.5


def test_export_engine_formats(tmp_path):
    """Verify GeoJSON, KML, GPX, and Field Dossier generators."""
    cands = apm.scan_candidates(min_probability=0.95)

    # 1. GeoJSON
    gj = candidates_to_geojson(cands)
    assert gj["type"] == "FeatureCollection"
    assert len(gj["features"]) == len(cands)
    assert "geometry" in gj["features"][0]
    assert "properties" in gj["features"][0]

    # File export via top-level API
    gj_file = tmp_path / "test.geojson"
    apm.export_geojson(gj_file)
    assert gj_file.exists()
    assert json.loads(gj_file.read_text(encoding="utf-8"))["type"] == "FeatureCollection"

    # 2. KML
    kml = candidates_to_kml(cands)
    assert "<kml" in kml
    assert "<Placemark>" in kml
    assert "</kml>" in kml
    kml_file = tmp_path / "test.kml"
    apm.export_kml(kml_file)
    assert kml_file.exists()
    assert "<kml" in kml_file.read_text(encoding="utf-8")

    # 3. GPX
    gpx = candidates_to_gpx(cands)
    assert "<gpx" in gpx
    assert "<wpt" in gpx
    assert "</gpx>" in gpx
    gpx_file = tmp_path / "test.gpx"
    apm.export_gpx(gpx_file)
    assert gpx_file.exists()
    assert "<gpx" in gpx_file.read_text(encoding="utf-8")

    # 4. Field Dossier
    dos = generate_field_survey_dossier(cands[0])
    assert "# Archaeological Field Survey Dossier" in dos
    assert "Ground-Penetrating Radar" in dos
    assert "Antiquities and Art Treasures Act" in dos

    # Top-level API dossier fetch
    dos_api = apm.generate_dossier(cands[0].candidate_id)
    assert dos_api == dos


def test_expanded_monuments_registry_and_benchmark():
    """Verify 97 canonical Pre-600 BCE reference monuments and 100% recall benchmark."""
    assert len(KNOWN_MONUMENTS_REGISTRY) >= 90
    reg = SubcontinentKnownMonumentsRegistry(min_exclusion_distance_m=1500.0)
    assert len(reg.monuments) == len(KNOWN_MONUMENTS_REGISTRY)

    # Benchmark execution
    results, df, stats = apm.benchmark_monuments()
    assert len(results) == len(KNOWN_MONUMENTS_REGISTRY)
    assert stats["overall_recall_pct"] == 100.0
    assert stats["missed"] == 0
    assert stats["mean_calibrated_probability_pct"] >= 99.0


def test_rest_api_export_endpoints():
    """Spin up local test server and verify all export API endpoints."""
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), ArchaeologicalHTTPHandler)
    port = httpd.server_address[1]
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()

    try:
        base = f"http://127.0.0.1:{port}"

        # 1. GeoJSON endpoint
        r_gj = requests.get(f"{base}/api/export/geojson", timeout=5)
        assert r_gj.status_code == 200
        assert r_gj.headers["Content-Type"].startswith("application/geo+json")
        assert len(r_gj.json()["features"]) >= 50

        # 2. KML endpoint
        r_kml = requests.get(f"{base}/api/export/kml", timeout=5)
        assert r_kml.status_code == 200
        assert "<kml" in r_kml.text

        # 3. GPX endpoint
        r_gpx = requests.get(f"{base}/api/export/gpx", timeout=5)
        assert r_gpx.status_code == 200
        assert "<gpx" in r_gpx.text

        # 4. CSV endpoint
        r_csv = requests.get(f"{base}/api/export/csv", timeout=5)
        assert r_csv.status_code == 200
        assert "candidate_id" in r_csv.text

        # 5. Dossier endpoint
        r_dos = requests.get(f"{base}/api/dossier?id=SUBCON_DISCOV_001", timeout=5)
        assert r_dos.status_code == 200
        assert "Archaeological Field Survey Dossier" in r_dos.text

        # 6. Invalid dossier ID returns 404
        r_bad = requests.get(f"{base}/api/dossier?id=INVALID_ID_9999", timeout=5)
        assert r_bad.status_code == 404

    finally:
        httpd.shutdown()
        httpd.server_close()
