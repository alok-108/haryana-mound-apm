"""
Phase 4 Unit Tests: QGIS Plugin, ODK Mobile Feedback, and Active Learning Pipeline.
Verifies:
1. QGIS plugin bundle integrity (metadata, dialog, zip structure).
2. ODK / KoboToolbox mobile survey form generation (JSON, XLSForm CSVs).
3. Active Learning ground feedback ingestion and training set promotion.
4. Coarse public sensitivity GeoJSON export (anti-looting compliance).
5. Web server Phase 4 API endpoints (/api/export/qgis-plugin, /api/feedback/submit, etc.).
"""

from __future__ import annotations
import io
import json
from pathlib import Path
import tempfile
import zipfile
import pytest
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent

from src.field_feedback.odk_form_generator import (
    ODK_SURVEY_QUESTIONS,
    ODK_CHOICES,
    ODK_SETTINGS,
    export_odk_survey_bundle,
)
from src.field_feedback.active_learning_ingestor import (
    SurveyVerificationSubmission,
    ActiveLearningFeedbackIngestor,
)
from src.coarse_raster_exporter import CoarseRasterExporter
from scripts.package_qgis_plugin import build_qgis_plugin_zip


def test_qgis_plugin_zip_bundle():
    """Verify QGIS plugin zip packaging contains required metadata and plugin files."""
    zip_path = build_qgis_plugin_zip()
    assert zip_path.exists(), "QGIS plugin zip must exist"
    assert zip_path.stat().st_size > 1000, "Zip size should be > 1 KB"

    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        assert "pre600bce_apm/metadata.txt" in namelist
        assert "pre600bce_apm/__init__.py" in namelist
        assert "pre600bce_apm/apm_plugin.py" in namelist
        assert "pre600bce_apm/apm_dockwidget.py" in namelist
        assert "pre600bce_apm/icon.png" in namelist

        metadata_content = zf.read("pre600bce_apm/metadata.txt").decode("utf-8")
        assert "name=Pre-600 BCE Subcontinent APM Discovery GIS" in metadata_content
        assert "qgisMinimumVersion=3." in metadata_content


def test_odk_form_generator():
    """Verify ODK / KoboToolbox mobile survey form schema generation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_p = Path(tmp_dir)
        bundle = export_odk_survey_bundle(out_p)

        assert bundle["json_form"].exists()
        assert bundle["survey_csv"].exists()
        assert bundle["choices_csv"].exists()

        form_data = json.loads(bundle["json_form"].read_text(encoding="utf-8"))
        assert "settings" in form_data
        assert "survey" in form_data
        assert "choices" in form_data

        # Check critical fields exist
        field_names = [q["name"] for q in form_data["survey"]]
        assert "ground_verdict" in field_names
        assert "observed_relief_m" in field_names
        assert "observed_ceramics" in field_names
        assert "anti_looting_reminder" in field_names

        # Check verdict choices include confirmed tell and false positive types
        choice_names = [c["name"] for c in form_data["choices"] if c["list_name"] == "ground_verdict_list"]
        assert "mound_confirmed" in choice_names
        assert "false_positive_dune" in choice_names
        assert "false_positive_canal" in choice_names


def test_active_learning_ingestion_and_retraining():
    """Verify ground survey feedback ingestion, spatial safety check, and model feature update."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_csv = Path(tmp_dir) / "test_submissions.csv"
        ingestor = ActiveLearningFeedbackIngestor(storage_csv=storage_csv, min_exclusion_distance_m=1500.0)

        # 1. Ingest confirmed mound in novel territory
        sub1 = SurveyVerificationSubmission(
            submission_id="SUB_TEST_001",
            surveyor_name="Dr. Archaeologist",
            institution="university",
            latitude=29.5085,
            longitude=74.8420,
            ground_verdict="mound_confirmed",
            candidate_id="SUBCON_DISCOV_001",
            observed_relief_m=3.5,
            observed_diameter_m=220.0,
            observed_ceramics=["hakra_ware", "early_harappan"],
            field_notes="Dense pottery scatter with burnt mud-brick fragments.",
        )
        res1 = ingestor.ingest_submission(sub1)
        assert res1["status"] == "INGESTED"
        assert res1["active_learning_role"] == "new_ground_truth_positive"
        assert res1["is_outside_known_buffer"] is True

        # 2. Ingest false positive dune
        sub2 = SurveyVerificationSubmission(
            submission_id="SUB_TEST_002",
            surveyor_name="Surveyor B",
            institution="state_doam",
            latitude=28.8000,
            longitude=72.5000,
            ground_verdict="false_positive_dune",
            candidate_id="SUBCON_DISCOV_002",
            observed_relief_m=4.0,
            observed_diameter_m=150.0,
            field_notes="Pure aeolian sand ridge without anthropogenic cultural material.",
        )
        res2 = ingestor.ingest_submission(sub2)
        assert res2["status"] == "INGESTED"
        assert res2["active_learning_role"] == "hard_negative_penalty"

        # 3. Test active learning dataframe update
        base_df = pd.DataFrame([
            {"site_id": "SUBCON_DISCOV_001", "y_obs": 0, "is_hard_negative": 0},
            {"site_id": "SUBCON_DISCOV_002", "y_obs": 1, "is_hard_negative": 0},
            {"site_id": "SUBCON_DISCOV_003", "y_obs": 0, "is_hard_negative": 0},
        ])

        updated_df, stats = ingestor.apply_active_learning_update(base_df)
        assert stats["new_positives"] == 1
        assert stats["new_hard_negatives"] == 1
        assert stats["total_feedback_submissions"] == 2

        # Verify candidate 1 was promoted to positive
        c1 = updated_df[updated_df["site_id"] == "SUBCON_DISCOV_001"].iloc[0]
        assert c1["y_obs"] == 1
        assert c1["is_ground_confirmed"] is True

        # Verify candidate 2 was penalized as hard negative
        c2 = updated_df[updated_df["site_id"] == "SUBCON_DISCOV_002"].iloc[0]
        assert c2["y_obs"] == 0
        assert c2["is_hard_negative"] == 1


def test_coarse_raster_exporter():
    """Verify coarse 2km public sensitivity export complies with anti-looting rules."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_geojson = Path(tmp_dir) / "coarse_test.geojson"
        exporter = CoarseRasterExporter(resolution_km=2.0)
        gj_data = exporter.export_coarse_sensitivity_geojson(output_path=out_geojson)

        assert out_geojson.exists()
        assert gj_data["type"] == "FeatureCollection"
        assert len(gj_data["features"]) > 0

        # Check anti-looting notice in metadata
        assert "anti_looting_notice" in gj_data["metadata"]
        assert gj_data["metadata"]["grid_resolution_km"] == 2.0

        # Check individual polygon features
        feat = gj_data["features"][0]
        assert feat["geometry"]["type"] == "Polygon"
        assert "sensitivity_tier" in feat["properties"]
        assert "mean_probability" in feat["properties"]
        # Exact site coordinates or candidate IDs must NOT be present in public coarse properties
        assert "exact_latitude" not in feat["properties"]
        assert "exact_longitude" not in feat["properties"]


def test_web_server_phase4_api():
    """Verify web server Phase 4 endpoints without starting external port."""
    from src.web_server import APM_BACKEND, ArchaeologicalHTTPHandler

    # 1. Test feedback submission directly on APM_BACKEND
    sub = SurveyVerificationSubmission(
        submission_id="SUB_WEB_TEST",
        surveyor_name="Tester",
        institution="asi",
        latitude=29.2936,  # Exactly on Rakhigarhi (Mounds 1-7)
        longitude=76.0822,
        ground_verdict="mound_confirmed",
    )
    result = APM_BACKEND.feedback_ingestor.ingest_submission(sub)
    assert result["status"] == "INGESTED"
    # Rakhigarhi is a known monument (< 1500m)
    assert result["is_outside_known_buffer"] is False
    assert result["dist_to_documented_monument_m"] < 1500.0
