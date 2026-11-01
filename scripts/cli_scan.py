"""
CLI Tool: apm-scan
Evaluate any geographic coordinate using the GeoAI Pre-600 BCE discovery engine.

Usage:
    apm-scan --lat 29.5085 --lon 74.8420
    apm-scan --lat 29.2936 --lon 76.0822 --json
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure repo root on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import src as apm


def main():
    parser = argparse.ArgumentParser(
        description="Scan coordinates with the Pre-600 BCE GeoAI Archaeological Discovery Engine."
    )
    parser.add_argument("--lat", type=float, required=True, help="Latitude (degrees N)")
    parser.add_argument("--lon", type=float, required=True, help="Longitude (degrees E)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON response")
    args = parser.parse_args()

    res = apm.scan(args.lat, args.lon)

    if args.json:
        print(json.dumps(res.to_dict(), indent=2))
        return

    print("=" * 80)
    print(f"APM GEOAI TERRAIN ASSESSMENT: {args.lat:.5f}° N, {args.lon:.5f}° E")
    print("=" * 80)
    if res.is_novel_undiscovered:
        print("STATUS: 🌟 100% NEW / UNDISCOVERED LAND")
        print(f"Nearest Documented Monument: {res.nearest_documented_monument} ({res.dist_to_documented_monument_m/1000.0:.2f} km away)")
        print(f"Presence Probability:       {res.calibrated_probability * 100:.1f}% ({res.confidence_tier})")
    else:
        print("STATUS: 🏛️ ALREADY DISCOVERED HISTORICAL MONUMENT")
        print(f"Matched Monument:            {res.nearest_documented_monument}")
        print(f"Separation:                  {res.dist_to_documented_monument_m:.0f} m (< 1,500 m exclusion perimeter)")

    print(f"Macro-Basin:                 {res.macro_basin}")
    print(f"Associated Paleochannel:     {res.nearest_paleochannel} ({res.dist_paleochannel_km:.2f} km)")
    print(f"Fluvial Prior Score:         {res.fluvial_prior_score:.3f} / 1.000")
    print(f"Mound Relief Elevation:      +{res.estimated_relief_m:.1f} m")
    print(f"Cultural Horizon:            {res.predicted_culture}")
    print(f"Cultural Rationale:          {res.cultural_rationale}")
    print("\nRecommended Non-Invasive Survey Methods:")
    for m in res.recommended_survey_methods:
        print(f"  * {m}")
    print("=" * 80)


if __name__ == "__main__":
    main()
