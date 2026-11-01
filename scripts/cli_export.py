"""
CLI Tool: apm-export
Export high-confidence Pre-600 BCE candidate discoveries into standard geospatial formats:
GeoJSON, Google Earth KML, Handheld GPS GPX, or CSV.

Usage:
    apm-export --format geojson --out results/discoveries.geojson
    apm-export --format kml --out results/discoveries.kml
    apm-export --format gpx --out results/discoveries.gpx
    apm-export --format csv --out results/discoveries.csv
"""

import argparse
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
        description="Export Pre-600 BCE Archaeological Discoveries to Geospatial Formats."
    )
    parser.add_argument(
        "--format",
        choices=["geojson", "kml", "gpx", "csv"],
        default="geojson",
        help="Target export format (default: geojson)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output file path (defaults to results/subcontinent/undiscovered_candidates.<ext>)",
    )
    parser.add_argument(
        "--min-prob",
        type=float,
        default=0.95,
        help="Minimum calibrated probability threshold (default: 0.95)",
    )
    args = parser.parse_args()

    fmt = args.format.lower()
    default_names = {
        "geojson": "results/subcontinent/undiscovered_subcontinent_pre600bce_candidates.geojson",
        "kml": "results/subcontinent/undiscovered_subcontinent_pre600bce_candidates.kml",
        "gpx": "results/subcontinent/undiscovered_subcontinent_pre600bce_candidates.gpx",
        "csv": "results/subcontinent/undiscovered_subcontinent_pre600bce_candidates.csv",
    }
    out_path = Path(args.out) if args.out else Path(default_names[fmt])

    if fmt == "geojson":
        res_p = apm.export_geojson(out_path, min_probability=args.min_prob)
    elif fmt == "kml":
        res_p = apm.export_kml(out_path, min_probability=args.min_prob)
    elif fmt == "gpx":
        res_p = apm.export_gpx(out_path, min_probability=args.min_prob)
    elif fmt == "csv":
        cands = apm.scan_candidates(min_probability=args.min_prob)
        import pandas as pd
        from dataclasses import asdict
        df = pd.DataFrame([asdict(c) for c in cands])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)
        res_p = out_path

    print(f"[OK] Successfully exported {fmt.upper()} layer to: {res_p}")


if __name__ == "__main__":
    main()
