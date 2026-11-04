"""
ODK Collect & KoboToolbox Mobile Survey Form Generator for Field Archaeologists.
Generates:
1. Standard XLSForm structure (survey, choices, settings) exportable to CSV/JSON/XLSX.
2. Form fields for recording tell verification ground verdicts:
   - mound_confirmed (ancient tell verified on ground)
   - false_positive_dune (sand dune / natural knoll)
   - false_positive_canal (canal spoil bank / road ridge)
   - false_positive_brick_kiln (modern brick kiln)
   - ploughed_out_scatter (levelled surface sherd scatter)
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Optional


ODK_SURVEY_QUESTIONS: List[Dict[str, str]] = [
    {"type": "start", "name": "start_time", "label": "Start Time"},
    {"type": "end", "name": "end_time", "label": "End Time"},
    {"type": "deviceid", "name": "device_id", "label": "Device Identifier"},
    {"type": "text", "name": "surveyor_name", "label": "Surveyor Full Name", "required": "yes"},
    {"type": "select_one institution_type", "name": "institution", "label": "Affiliated Institution", "required": "yes"},
    {"type": "text", "name": "candidate_id", "label": "Target APM Candidate ID (e.g. SUBCON_DISCOV_001)", "required": "no"},
    {"type": "geopoint", "name": "ground_location", "label": "GPS Coordinate (Ensure < 5m GNSS accuracy)", "required": "yes"},
    {"type": "select_one ground_verdict_list", "name": "ground_verdict", "label": "Ground Archaeological Verdict", "required": "yes"},
    {"type": "decimal", "name": "observed_relief_m", "label": "Estimated Mound Relief Height Above Plain (m)", "relevant": "${ground_verdict} = 'mound_confirmed'"},
    {"type": "decimal", "name": "observed_diameter_m", "label": "Estimated Mound Footprint Diameter (m)", "relevant": "${ground_verdict} = 'mound_confirmed'"},
    {"type": "select_multiple pottery_types", "name": "observed_ceramics", "label": "Observed Diagnostic Ceramic Horizons", "relevant": "${ground_verdict} = 'mound_confirmed' or ${ground_verdict} = 'ploughed_out_scatter'"},
    {"type": "image", "name": "mound_photo", "label": "Photograph of Mound Profile or Ceramic Sherds"},
    {"type": "note", "name": "anti_looting_reminder", "label": "REMINDER: Do NOT remove diagnostic sherds or artifacts without statutory authorization from ASI / State Antiquities Directorate."},
    {"type": "text", "name": "field_notes", "label": "General Field Geomorphic & Cultural Notes"},
]

ODK_CHOICES: List[Dict[str, str]] = [
    # Institutions
    {"list_name": "institution_type", "name": "asi", "label": "Archaeological Survey of India (ASI)"},
    {"list_name": "institution_type", "name": "state_doam", "label": "State Directorate of Archaeology & Museums"},
    {"list_name": "institution_type", "name": "university", "label": "University / Academic Department"},
    {"list_name": "institution_type", "name": "consortium", "label": "International / Inter-Institutional Consortium"},
    {"list_name": "institution_type", "name": "independent", "label": "Accredited Independent Researcher"},

    # Ground Verdicts
    {"list_name": "ground_verdict_list", "name": "mound_confirmed", "label": "✅ Mound Confirmed (Ancient Archaeological Tell)"},
    {"list_name": "ground_verdict_list", "name": "false_positive_dune", "label": "❌ False Positive: Natural Sand Dune / Relict Ridge"},
    {"list_name": "ground_verdict_list", "name": "false_positive_canal", "label": "❌ False Positive: Modern Canal Spoil Bank / Bund"},
    {"list_name": "ground_verdict_list", "name": "false_positive_brick_kiln", "label": "❌ False Positive: Modern Brick Kiln / Debris Mound"},
    {"list_name": "ground_verdict_list", "name": "ploughed_out_scatter", "label": "⚠️ Levelled / Ploughed-out Pottery Scatter (Low Relief)"},

    # Pottery Horizons
    {"list_name": "pottery_types", "name": "hakra_ware", "label": "Hakra Ware (Incised / Mud-Applique)"},
    {"list_name": "pottery_types", "name": "early_harappan", "label": "Early Harappan (Sothi-Siswal / Kot Diji)"},
    {"list_name": "pottery_types", "name": "mature_harappan", "label": "Mature Harappan (Red Ware / Black-on-Red)"},
    {"list_name": "pottery_types", "name": "late_harappan_ocp", "label": "Late Harappan / Ochre Coloured Pottery (OCP)"},
    {"list_name": "pottery_types", "name": "pgw", "label": "Painted Grey Ware (PGW / Vedic Horizon)"},
    {"list_name": "pottery_types", "name": "brw", "label": "Black-and-Red Ware (BRW / Chalcolithic)"},
    {"list_name": "pottery_types", "name": "early_historic", "label": "Early Historic (NBPW / Red Polished Ware)"},
]

ODK_SETTINGS: Dict[str, str] = {
    "form_title": "Pre-600 BCE APM Ground Tell Verification Form",
    "form_id": "pre600bce_apm_field_verification_v1",
    "version": "20261104",
    "default_language": "en",
}


def export_odk_survey_bundle(output_dir: Path) -> Dict[str, Path]:
    """
    Export ODK Collect / KoboToolbox mobile survey definition files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. JSON Schema for Web / API integration
    bundle_json = {
        "settings": ODK_SETTINGS,
        "survey": ODK_SURVEY_QUESTIONS,
        "choices": ODK_CHOICES,
    }
    json_path = output_dir / "apm_field_survey_form.json"
    json_path.write_text(json.dumps(bundle_json, indent=2), encoding="utf-8")

    # 2. Standard CSV definition for KoboToolbox / ODK XLSForm import
    survey_csv = output_dir / "xlsform_survey.csv"
    survey_lines = ["type,name,label,required,relevant"]
    for q in ODK_SURVEY_QUESTIONS:
        req = q.get("required", "")
        rel = q.get("relevant", "")
        survey_lines.append(f'"{q["type"]}","{q["name"]}","{q["label"]}","{req}","{rel}"')
    survey_csv.write_text("\n".join(survey_lines), encoding="utf-8")

    choices_csv = output_dir / "xlsform_choices.csv"
    choices_lines = ["list_name,name,label"]
    for c in ODK_CHOICES:
        choices_lines.append(f'"{c["list_name"]}","{c["name"]}","{c["label"]}"')
    choices_csv.write_text("\n".join(choices_lines), encoding="utf-8")

    return {
        "json_form": json_path,
        "survey_csv": survey_csv,
        "choices_csv": choices_csv,
    }
