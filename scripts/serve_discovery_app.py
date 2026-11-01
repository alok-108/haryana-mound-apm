"""
CLI Launcher: Start the Pan-Subcontinent Pre-600 BCE APM Discovery Server.
Runs the live Python REST backend and connects the Interactive Web GIS Map.

Usage:
    python scripts/serve_discovery_app.py [--port 8000] [--no-browser]
"""

from __future__ import annotations
import argparse
from pathlib import Path
import socket
import sys
import webbrowser

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.web_server import ArchaeologicalHTTPHandler, ThreadingHTTPServer


def find_available_port(starting_port: int = 8000, max_attempts: int = 20) -> int:
    """Find an available port starting from `starting_port`."""
    for p in range(starting_port, starting_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return starting_port


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the Live Archaeological APM Discovery Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open web browser automatically")
    args = parser.parse_args()

    port = find_available_port(args.port)
    server_address = ("0.0.0.0", port)

    print("=" * 85)
    print("🛰️  PAN-SUBCONTINENT PRE-600 BCE ARCHAEOLOGICAL DISCOVERY SERVER (LIVE APM BACKEND)")
    print("=" * 85)
    print(f"[*] Initializing in-memory spatial indexes (KDTree) & paleochannel networks...")
    print(f"[*] Server listening on:  http://localhost:{port}/")
    print(f"[*] Map Web GIS UI:       http://localhost:{port}/map")
    print(f"[*] REST API Endpoints:")
    print(f"    - GET http://localhost:{port}/api/status")
    print(f"    - GET http://localhost:{port}/api/scan?lat=<float>&lon=<float>")
    print(f"    - GET http://localhost:{port}/api/scan_viewport?min_lat=...&max_lat=...&min_lon=...&max_lon=...")
    print(f"    - GET http://localhost:{port}/api/benchmark")
    print(f"    - GET http://localhost:{port}/api/candidates")
    print("=" * 85)
    print("[*] Map is LIVE-CONNECTED to Python backend. Click anywhere on the map to trigger APM scan.")
    print("Press Ctrl+C to stop the server.\n")

    if not args.no_browser:
        webbrowser.open(f"http://localhost:{port}/")

    httpd = ThreadingHTTPServer(server_address, ArchaeologicalHTTPHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Shutting down server gracefully...")
        httpd.server_close()
        print("[OK] Server stopped.")


if __name__ == "__main__":
    main()
