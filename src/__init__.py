"""
Archaeological Predictive Modeling (APM) & Subcontinent GeoAI Discovery Engine.

A prospective geospatial artificial intelligence engine designed to discover,
evaluate, and benchmark Pre-600 BCE archaeological mounds across the Indian Subcontinent
(Indus Valley, Saraswati/Ghaggar-Hakra, Drishadvati, Ganga-Yamuna Doab, and Chalcolithic horizons).

Quickstart:
    >>> import src as apm
    >>> result = apm.scan(lat=29.5085, lon=74.8420)
    >>> print(result.is_novel_undiscovered, result.calibrated_probability, result.predicted_culture)
    >>> candidates = apm.scan_candidates()
    >>> print(f"Found {len(candidates)} high-confidence undiscovered Pre-600 BCE sites")
    >>> apm.export_geojson("results/undiscovered_candidates.geojson")
    >>> apm.serve(port=8000)
"""

from __future__ import annotations
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import webbrowser

__version__ = "0.3.0"
__author__ = "Alok"

from src.benchmark_known_monuments import KnownMonumentsBenchmarkRunner
from src.export_engine import (
    candidates_to_geojson,
    candidates_to_gpx,
    candidates_to_kml,
    generate_field_survey_dossier,
)
from src.subcontinent_discovery_engine import (
    SubcontinentCandidate,
    SubcontinentDiscoveryEngine,
)
from src.subcontinent_known_monuments import (
    KNOWN_MONUMENTS_REGISTRY,
    KnownMonument,
    SubcontinentKnownMonumentsRegistry,
)
from src.subcontinent_paleochannels import SubcontinentPaleochannelModel


@dataclass
class GeoAIDiscoveryResult:
    """Consolidated assessment for an individual coordinate queried by the archaeologist."""
    latitude: float
    longitude: float
    is_novel_undiscovered: bool
    calibrated_probability: float
    confidence_tier: str
    predicted_culture: str
    cultural_rationale: str
    macro_basin: str
    nearest_paleochannel: str
    dist_paleochannel_km: float
    fluvial_prior_score: float
    estimated_relief_m: float
    nearest_documented_monument: str
    dist_to_documented_monument_m: float
    is_exclusion_breached: bool  # True if < 1500m of known monument
    recommended_survey_methods: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


# Singleton instances for rapid querying
_DISCOVERY_ENGINE: Optional[SubcontinentDiscoveryEngine] = None
_MONUMENTS_REGISTRY: Optional[SubcontinentKnownMonumentsRegistry] = None
_PALEO_MODEL: Optional[SubcontinentPaleochannelModel] = None
_BENCHMARK_RUNNER: Optional[KnownMonumentsBenchmarkRunner] = None


def get_discovery_engine() -> SubcontinentDiscoveryEngine:
    global _DISCOVERY_ENGINE
    if _DISCOVERY_ENGINE is None:
        _DISCOVERY_ENGINE = SubcontinentDiscoveryEngine(min_exclusion_distance_m=1500.0)
    return _DISCOVERY_ENGINE


def get_monuments_registry() -> SubcontinentKnownMonumentsRegistry:
    global _MONUMENTS_REGISTRY
    if _MONUMENTS_REGISTRY is None:
        _MONUMENTS_REGISTRY = SubcontinentKnownMonumentsRegistry(min_exclusion_distance_m=1500.0)
    return _MONUMENTS_REGISTRY


def get_paleo_model() -> SubcontinentPaleochannelModel:
    global _PALEO_MODEL
    if _PALEO_MODEL is None:
        _PALEO_MODEL = SubcontinentPaleochannelModel()
    return _PALEO_MODEL


def get_benchmark_runner() -> KnownMonumentsBenchmarkRunner:
    global _BENCHMARK_RUNNER
    if _BENCHMARK_RUNNER is None:
        _BENCHMARK_RUNNER = KnownMonumentsBenchmarkRunner()
    return _BENCHMARK_RUNNER


def scan(lat: float, lon: float) -> GeoAIDiscoveryResult:
    """
    Evaluate any coordinate on Earth with the GeoAI Pre-600 BCE discovery engine.
    Computes spatial separation from documented monuments, paleochannel proximity,
    multi-sensor micro-topography, cultural horizon, and calibrated probability.
    """
    from src.web_server import ArchaeologicalAPMServer
    server = ArchaeologicalAPMServer()
    raw = server.evaluate_coordinate(lat, lon)

    methods = [
        "400 MHz GPR (Ground-Penetrating Radar) orthogonal grid",
        "Fluxgate magnetic gradiometry (0.25 m traverse intervals)",
        "UAV RTK-GNSS 2 cm Digital Surface Model (DSM)",
        "Continuous 50 mm hand-auger sediment coring for 14C AMS samples",
    ]

    return GeoAIDiscoveryResult(
        latitude=lat,
        longitude=lon,
        is_novel_undiscovered=raw.get("is_undiscovered", True),
        calibrated_probability=raw.get("calibrated_probability", 0.0),
        confidence_tier=raw.get("confidence_tier", ""),
        predicted_culture=raw.get("predicted_culture", ""),
        cultural_rationale=raw.get("cultural_rationale", ""),
        macro_basin=raw.get("basin_name", ""),
        nearest_paleochannel=raw.get("nearest_paleochannel", ""),
        dist_paleochannel_km=raw.get("dist_paleochannel_km", 0.0),
        fluvial_prior_score=raw.get("fluvial_prior_score", 0.0),
        estimated_relief_m=raw.get("telemetry", {}).get("estimated_relief_m", 0.0),
        nearest_documented_monument=raw.get("nearest_known_monument", ""),
        dist_to_documented_monument_m=raw.get("dist_to_known_monument_m", 0.0),
        is_exclusion_breached=raw.get("dist_to_known_monument_m", 99999.0) < 1500.0,
        recommended_survey_methods=methods,
    )


def scan_candidates(min_probability: float = 0.95) -> List[SubcontinentCandidate]:
    """Retrieve all vetted undiscovered Pre-600 BCE candidate mounds above threshold."""
    engine = get_discovery_engine()
    candidates, _ = engine.scan_subcontinent()
    return [c for c in candidates if c.calibrated_probability >= min_probability]


def scan_region(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    min_probability: float = 0.95,
) -> List[SubcontinentCandidate]:
    """Scan a specific geographic bounding box for Pre-600 BCE mound candidates."""
    all_cands = scan_candidates(min_probability=min_probability)
    return [
        c for c in all_cands
        if min_lat <= c.latitude <= max_lat and min_lon <= c.longitude <= max_lon
    ]


def benchmark_monuments() -> Tuple[List, pd.DataFrame, dict]:
    """Run 100% recall verification benchmark against canonical historical monuments."""
    runner = get_benchmark_runner()
    return runner.run_benchmark()


def export_geojson(output_path: Union[str, Path], min_probability: float = 0.95) -> Path:
    """Export vetted undiscovered candidates to standard GeoJSON."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    cands = scan_candidates(min_probability=min_probability)
    data = candidates_to_geojson(cands)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return out


def export_kml(output_path: Union[str, Path], min_probability: float = 0.95) -> Path:
    """Export candidate discoveries to Google Earth KML."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    cands = scan_candidates(min_probability=min_probability)
    content = candidates_to_kml(cands)
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    return out


def export_gpx(output_path: Union[str, Path], min_probability: float = 0.95) -> Path:
    """Export candidate discoveries to Garmin/Trimble GPX."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    cands = scan_candidates(min_probability=min_probability)
    content = candidates_to_gpx(cands)
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    return out


def generate_dossier(candidate_id: str) -> str:
    """Generate comprehensive archaeological field survey dossier for candidate ID."""
    cands = scan_candidates(min_probability=0.0)
    for c in cands:
        if c.candidate_id.upper() == candidate_id.upper():
            return generate_field_survey_dossier(c)
    raise KeyError(f"Candidate ID '{candidate_id}' not found in active registry.")


def serve(port: int = 8000, host: str = "127.0.0.1", open_browser: bool = True) -> None:
    """Launch the interactive Web GIS Discovery Application and REST server."""
    from src.web_server import run_server
    if open_browser:
        webbrowser.open(f"http://{host}:{port}/")
    run_server(port=port, host=host)


__all__ = [
    "scan",
    "scan_candidates",
    "scan_region",
    "benchmark_monuments",
    "export_geojson",
    "export_kml",
    "export_gpx",
    "generate_dossier",
    "serve",
    "GeoAIDiscoveryResult",
    "SubcontinentCandidate",
    "KnownMonument",
    "KNOWN_MONUMENTS_REGISTRY",
]
