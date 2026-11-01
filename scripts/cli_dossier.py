"""
CLI Tool: apm-dossier
Generate and display or save an Archaeological Field Survey Dossier for a prospective candidate.

Usage:
    apm-dossier --id SUBCON_DISCOV_001
    apm-dossier --id SUBCON_DISCOV_001 --out dossier_001.md
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
        description="Generate Archaeological Field Survey Dossier for a Pre-600 BCE Candidate."
    )
    parser.add_argument(
        "--id",
        type=str,
        required=True,
        help="Candidate Identifier (e.g., SUBCON_DISCOV_001)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Optional output file path to save markdown dossier",
    )
    args = parser.parse_args()

    try:
        dossier = apm.generate_dossier(args.id)
    except KeyError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    if args.out:
        out_p = Path(args.out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(dossier)
        print(f"[OK] Dossier for {args.id} saved to: {out_p}")
    else:
        print(dossier)


if __name__ == "__main__":
    main()
